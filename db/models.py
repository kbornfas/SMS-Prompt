from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json
from typing import Optional, List, Dict, Any

Base = declarative_base()


class SMSLog(Base):
    """Track all SMS sent"""
    __tablename__ = 'sms_logs'
    
    id = Column(Integer, primary_key=True)
    recipient = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    template_name = Column(String, index=True)
    variables = Column(Text)  # JSON string
    message_sid = Column(String)
    status = Column(String, index=True)
    segments = Column(Integer)
    cost = Column(Float)
    success = Column(Boolean, default=True, index=True)
    error = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'recipient': self.recipient,
            'message': self.message,
            'template': self.template_name,
            'variables': json.loads(self.variables) if self.variables else None,
            'message_sid': self.message_sid,
            'status': self.status,
            'segments': self.segments,
            'cost': self.cost,
            'success': self.success,
            'error': self.error,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }


class Template(Base):
    """Store templates in database (optional, for database-backed templates)"""
    __tablename__ = 'templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Database:
    """Database manager for SMS history"""
    
    def __init__(self, db_path: str):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def log_sms(self, recipient: str, message: str, template_name: Optional[str], 
                variables: Optional[Dict], result: Dict) -> SMSLog:
        """Log an SMS send attempt"""
        log = SMSLog(
            recipient=recipient,
            message=message,
            template_name=template_name,
            variables=json.dumps(variables) if variables else None,
            message_sid=result.get('message_sid'),
            status=result.get('status'),
            segments=result.get('segments'),
            cost=float(result.get('price', 0)) if result.get('price') else None,
            success=result.get('success', False),
            error=result.get('error')
        )
        self.session.add(log)
        self.session.commit()
        return log
    
    def get_history(self, limit: int = 10, recipient: Optional[str] = None, 
                    template: Optional[str] = None, success_only: Optional[bool] = None,
                    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[SMSLog]:
        """Get SMS history with filters"""
        query = self.session.query(SMSLog)
        
        if recipient:
            query = query.filter(SMSLog.recipient == recipient)
        if template:
            query = query.filter(SMSLog.template_name == template)
        if success_only is not None:
            query = query.filter(SMSLog.success == success_only)
        if start_date:
            query = query.filter(SMSLog.sent_at >= start_date)
        if end_date:
            query = query.filter(SMSLog.sent_at <= end_date)
        
        return query.order_by(SMSLog.sent_at.desc()).limit(limit).all()
    
    def get_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get sending statistics for the specified period"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total = self.session.query(SMSLog).filter(SMSLog.sent_at >= start_date).count()
        successful = self.session.query(SMSLog).filter(
            SMSLog.success == True,
            SMSLog.sent_at >= start_date
        ).count()
        failed = total - successful
        
        total_cost = self.session.query(func.sum(SMSLog.cost)).filter(
            SMSLog.sent_at >= start_date
        ).scalar() or 0
        
        total_segments = self.session.query(func.sum(SMSLog.segments)).filter(
            SMSLog.sent_at >= start_date
        ).scalar() or 0
        
        # Get top templates
        template_stats = self.session.query(
            SMSLog.template_name,
            func.count(SMSLog.id).label('count')
        ).filter(
            SMSLog.sent_at >= start_date,
            SMSLog.template_name.isnot(None)
        ).group_by(SMSLog.template_name).order_by(func.count(SMSLog.id).desc()).limit(5).all()
        
        # Get daily breakdown
        daily_stats = self.session.query(
            func.date(SMSLog.sent_at).label('date'),
            func.count(SMSLog.id).label('count'),
            func.sum(SMSLog.cost).label('cost')
        ).filter(
            SMSLog.sent_at >= start_date
        ).group_by(func.date(SMSLog.sent_at)).order_by(func.date(SMSLog.sent_at)).all()
        
        return {
            'period_days': days,
            'total_sent': total,
            'successful': successful,
            'failed': failed,
            'total_cost': float(total_cost),
            'total_segments': int(total_segments) if total_segments else 0,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'top_templates': [{'name': t[0], 'count': t[1]} for t in template_stats],
            'daily_breakdown': [
                {'date': str(d[0]), 'count': d[1], 'cost': float(d[2]) if d[2] else 0}
                for d in daily_stats
            ]
        }
    
    def get_recipient_history(self, recipient: str) -> Dict[str, Any]:
        """Get detailed history for a specific recipient"""
        messages = self.session.query(SMSLog).filter(
            SMSLog.recipient == recipient
        ).order_by(SMSLog.sent_at.desc()).all()
        
        total = len(messages)
        successful = sum(1 for m in messages if m.success)
        total_cost = sum(m.cost or 0 for m in messages)
        
        return {
            'recipient': recipient,
            'total_messages': total,
            'successful': successful,
            'failed': total - successful,
            'total_cost': total_cost,
            'first_message': messages[-1].sent_at.isoformat() if messages else None,
            'last_message': messages[0].sent_at.isoformat() if messages else None,
            'messages': [m.to_dict() for m in messages[:10]]  # Last 10 messages
        }
    
    def search_messages(self, query: str, limit: int = 20) -> List[SMSLog]:
        """Search messages by content"""
        return self.session.query(SMSLog).filter(
            SMSLog.message.like(f'%{query}%')
        ).order_by(SMSLog.sent_at.desc()).limit(limit).all()
    
    def delete_old_logs(self, days: int = 90) -> int:
        """Delete logs older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = self.session.query(SMSLog).filter(
            SMSLog.sent_at < cutoff_date
        ).delete()
        self.session.commit()
        return deleted
    
    def export_logs(self, format: str = 'dict', limit: int = 1000) -> Any:
        """Export logs in various formats"""
        logs = self.session.query(SMSLog).order_by(SMSLog.sent_at.desc()).limit(limit).all()
        
        if format == 'dict':
            return [log.to_dict() for log in logs]
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].to_dict().keys())
                writer.writeheader()
                for log in logs:
                    writer.writerow(log.to_dict())
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def close(self):
        """Close database session"""
        self.session.close()
