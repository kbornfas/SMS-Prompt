from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import time
from typing import Optional, Dict, List, Any


class SMSGateway:
    """Handle SMS sending through various providers"""
    
    def __init__(self, provider: str = 'twilio', **credentials):
        self.provider = provider
        self.client = None
        self.from_number = None
        self.sms = None
        self.sender_id = None
        
        if provider == 'twilio':
            self.client = Client(
                credentials.get('account_sid'),
                credentials.get('auth_token')
            )
            self.from_number = credentials.get('phone_number')
        elif provider == 'africas_talking':
            # Africa's Talking implementation
            try:
                import africastalking  # type: ignore
                africastalking.initialize(
                    credentials.get('username'),
                    credentials.get('api_key')
                )
                self.sms = africastalking.SMS
                self.sender_id = credentials.get('sender_id')
            except ImportError:
                raise ImportError("africastalking package is not installed. Run: pip install africastalking")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def send(self, to_number: str, message: str, from_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Send SMS to a single recipient
        
        Args:
            to_number: Recipient phone number (E.164 format)
            message: Message content
            from_number: Optional override for sender number
        
        Returns:
            Dictionary with sending result
        """
        try:
            if self.provider == 'twilio':
                return self._send_twilio(to_number, message, from_number)
            elif self.provider == 'africas_talking':
                return self._send_africas_talking(to_number, message)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'to': to_number
            }
    
    def _send_twilio(self, to_number: str, message: str, from_number: Optional[str] = None) -> Dict[str, Any]:
        """Send via Twilio"""
        try:
            msg = self.client.messages.create(
                to=to_number,
                from_=from_number or self.from_number,
                body=message
            )
            
            return {
                'success': True,
                'message_sid': msg.sid,
                'status': msg.status,
                'to': to_number,
                'from': msg.from_,
                'segments': msg.num_segments,
                'price': msg.price,
                'price_unit': msg.price_unit
            }
        except TwilioRestException as e:
            return {
                'success': False,
                'error': e.msg,
                'error_code': e.code,
                'to': to_number
            }
    
    def _send_africas_talking(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send via Africa's Talking"""
        try:
            response = self.sms.send(
                message,
                [to_number],
                self.sender_id
            )
            
            if response['SMSMessageData']['Recipients']:
                recipient = response['SMSMessageData']['Recipients'][0]
                return {
                    'success': recipient['status'] == 'Success',
                    'message_id': recipient.get('messageId'),
                    'status': recipient['status'],
                    'to': to_number,
                    'cost': recipient.get('cost')
                }
            return {
                'success': False,
                'error': 'No recipients in response',
                'to': to_number
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'to': to_number
            }
    
    def send_bulk(self, recipients: List[str], message: str, rate_limit: int = 10) -> List[Dict[str, Any]]:
        """
        Send SMS to multiple recipients with rate limiting
        
        Args:
            recipients: List of phone numbers
            message: Message content (same for all)
            rate_limit: Messages per second
        
        Returns:
            List of results for each recipient
        """
        results = []
        delay = 1.0 / rate_limit if rate_limit > 0 else 0
        
        for recipient in recipients:
            result = self.send(recipient, message)
            results.append(result)
            
            if delay > 0:
                time.sleep(delay)
        
        return results
    
    def send_bulk_personalized(self, recipients_data: List[Dict], message_callback, rate_limit: int = 10) -> List[Dict[str, Any]]:
        """
        Send personalized SMS to multiple recipients with rate limiting
        
        Args:
            recipients_data: List of dicts with 'phone' and other fields
            message_callback: Function that takes recipient data and returns message
            rate_limit: Messages per second
        
        Returns:
            List of results for each recipient
        """
        results = []
        delay = 1.0 / rate_limit if rate_limit > 0 else 0
        
        for recipient_data in recipients_data:
            phone = recipient_data.get('phone')
            message = message_callback(recipient_data)
            result = self.send(phone, message)
            results.append(result)
            
            if delay > 0:
                time.sleep(delay)
        
        return results
    
    def get_cost_estimate(self, segments: int, recipient_count: int, provider: str = 'twilio') -> Dict[str, Any]:
        """Estimate cost for sending messages"""
        # Pricing approximations (actual prices vary by country and volume)
        pricing = {
            'twilio': 0.0079,  # $0.0079 per SMS segment (US)
            'africas_talking': 0.008,  # Approximate for Africa
        }
        
        cost_per_segment = pricing.get(provider, 0.0079)
        total_cost = segments * recipient_count * cost_per_segment
        
        return {
            'segments': segments,
            'recipients': recipient_count,
            'cost_per_segment': cost_per_segment,
            'total_cost': total_cost,
            'currency': 'USD'
        }
    
    def validate_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """Validate phone number format"""
        try:
            import phonenumbers
            parsed = phonenumbers.parse(phone_number, None)
            is_valid = phonenumbers.is_valid_number(parsed)
            
            return {
                'valid': is_valid,
                'formatted': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164) if is_valid else None,
                'country': phonenumbers.region_code_for_number(parsed) if is_valid else None
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
