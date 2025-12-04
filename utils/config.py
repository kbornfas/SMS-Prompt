import os
import yaml
from pathlib import Path


class Config:
    """Manage configuration for SMS prompt tool"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.sms-prompt'
        self.config_file = self.config_dir / 'config.yaml'
        self.templates_dir = self.config_dir / 'templates'
        self.db_file = self.config_dir / 'sms_history.db'
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """Create config directory and default config if not exists"""
        self.config_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        if not self.config_file.exists():
            default_config = {
                'sms_provider': 'twilio',  # twilio, africas_talking, vonage
                'twilio': {
                    'account_sid': '',
                    'auth_token': '',
                    'phone_number': ''
                },
                'africas_talking': {
                    'username': '',
                    'api_key': '',
                    'sender_id': ''
                },
                'defaults': {
                    'sender_name': 'YourApp',
                    'confirm_before_send': True,
                    'show_preview': True,
                    'save_to_history': True
                },
                'rate_limits': {
                    'messages_per_second': 10,
                    'messages_per_hour': 1000
                }
            }
            self.save_config(default_config)
            
            # Create sample templates
            self._create_sample_templates()
    
    def _create_sample_templates(self):
        """Create sample template files"""
        samples = {
            'welcome.txt': 'Hi {{name}}! 👋 Welcome to {{company}}. Your account is now active.',
            'reminder.txt': 'Hi {{name}}, this is a reminder about {{event}} on {{date}} at {{time}}.',
            'promo.txt': '🎉 Hey {{name}}! Special offer: {{discount}}% off. Use code: {{code}}. Valid until {{expiry}}.'
        }
        
        for filename, content in samples.items():
            template_path = self.templates_dir / filename
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def load_config(self):
        """Load configuration from YAML file"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def save_config(self, config):
        """Save configuration to YAML file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def set_value(self, key_path, value):
        """Set a configuration value using dot notation (e.g., twilio.account_sid)"""
        config = self.load_config()
        keys = key_path.split('.')
        
        current = config
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        
        current[keys[-1]] = value
        self.save_config(config)
        return True
    
    def get_value(self, key_path, default=None):
        """Get a configuration value using dot notation"""
        config = self.load_config()
        keys = key_path.split('.')
        
        current = config
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return default
            else:
                return default
        
        return current
