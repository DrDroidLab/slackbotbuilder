import yaml
import os
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class SlackCredentialsManager:
    def __init__(self, credentials_file: str = "credentials.yaml"):
        self.credentials_file = credentials_file
        self.credentials = None
        self.load_credentials()
    
    def load_credentials(self) -> bool:
        try:
            if not os.path.exists(self.credentials_file):
                logger.error(f"Credentials file not found: {self.credentials_file}")
                return False
            
            with open(self.credentials_file, 'r') as file:
                self.credentials = yaml.safe_load(file)
            
            logger.info(f"Credentials loaded from {self.credentials_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return False
    
    def reload_credentials(self) -> bool:
        return self.load_credentials()
    
    def get_app_config(self) -> Optional[Dict]:
        # First try to get from environment variables
        env_config = self._get_app_config_from_env()
        if env_config:
            logger.info("Using Slack configuration from environment variables")
            return env_config
        
        # Fallback to credentials file
        if not self.credentials:
            logger.error("No credentials loaded from file")
            return None
        
        slack_config = self.credentials.get('slack', {})
        
        if not slack_config:
            logger.error("Slack configuration not found in credentials file")
            return None
        
        # Validate required fields
        required_fields = ['app_id', 'signing_secret', 'bot_token']
        for field in required_fields:
            if not slack_config.get(field):
                logger.error(f"Missing required field '{field}' in slack config")
                return None
        
        logger.info("Using Slack configuration from credentials file")
        return slack_config
    
    def _get_app_config_from_env(self) -> Optional[Dict]:
        """Get Slack configuration from environment variables"""
        try:
            app_id = os.getenv('SLACK_APP_ID')
            signing_secret = os.getenv('SLACK_SIGNING_SECRET')
            bot_token = os.getenv('SLACK_BOT_TOKEN')
            app_name = os.getenv('SLACK_APP_NAME', 'slack_ai_bot')
            
            # Check if all required fields are present
            if app_id and signing_secret and bot_token:
                return {
                    'app_id': app_id,
                    'signing_secret': signing_secret,
                    'bot_token': bot_token,
                    'app_name': app_name
                }
            else:
                missing_fields = []
                if not app_id:
                    missing_fields.append('SLACK_APP_ID')
                if not signing_secret:
                    missing_fields.append('SLACK_SIGNING_SECRET')
                if not bot_token:
                    missing_fields.append('SLACK_BOT_TOKEN')
                
                logger.debug(f"Missing environment variables: {', '.join(missing_fields)}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting app config from environment: {e}")
            return None
    
    def get_all_apps(self) -> List[Dict]:
        if not self.credentials:
            return []
        
        slack_config = self.credentials.get('slack', {})
        return [slack_config]
        
    def get_events_config(self) -> Dict:
        """
        Get events configuration
        
        Returns:
            Dict: Events configuration
        """
        if not self.credentials:
            return {}
        
        return self.credentials.get('events', {})
    
    def get_webhooks_config(self) -> Dict:
        """
        Get webhooks configuration
        
        Returns:
            Dict: Webhooks configuration
        """
        if not self.credentials:
            return {}
        
        return self.credentials.get('webhooks', {})
    
    def get_bot_config(self) -> Dict:
        """
        Get bot configuration
        
        Returns:
            Dict: Bot configuration
        """
        if not self.credentials:
            return {}
        
        return self.credentials.get('bot', {})
    
    def get_signing_secret(self) -> Optional[str]:
        # First try environment variable
        signing_secret = os.getenv('SLACK_SIGNING_SECRET')
        if signing_secret:
            return signing_secret
        
        # Fallback to app config
        app_config = self.get_app_config()
        return app_config.get('signing_secret') if app_config else None
    
    def get_bot_token(self) -> Optional[str]:
        # First try environment variable
        bot_token = os.getenv('SLACK_BOT_TOKEN')
        if bot_token:
            return bot_token
        
        # Fallback to app config
        app_config = self.get_app_config()
        return app_config.get('bot_token') if app_config else None
    
    def get_app_id(self) -> Optional[str]:
        # First try environment variable
        app_id = os.getenv('SLACK_APP_ID')
        if app_id:
            return app_id
        
        # Fallback to app config
        app_config = self.get_app_config()
        return app_config.get('app_id') if app_config else None
    
    def get_openai_api_key(self) -> Optional[str]:
        """
        Get OpenAI API key from environment variables first, then fallback to credentials file
        
        Returns:
            str: OpenAI API key or None if not found
        """
        # First try environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            logger.info("Using OpenAI API key from environment variable")
            return api_key
        
        # Fallback to credentials file
        if not self.credentials:
            logger.error("No credentials loaded from file")
            return None
        
        api_key = self.credentials.get('openai', {}).get('api_key')
        if api_key:
            logger.info("Using OpenAI API key from credentials file")
        
        return api_key

    def validate_credentials(self) -> bool:
        """
        Validate that all required credentials are present
        
        Returns:
            bool: True if valid, False otherwise
        """
        app_config = self.get_app_config()
        if not app_config:
            return False
        
        # Check for placeholder values
        placeholder_values = [
            "YOUR_APP_ID_HERE",
            "YOUR_SIGNING_SECRET_HERE", 
            "xoxb-YOUR_BOT_TOKEN_HERE"
        ]
        
        for field, value in app_config.items():
            if value in placeholder_values:
                logger.error(f"Placeholder value found in {field}: {value}")
                return False
        
        return True
    
    def get_credentials_summary(self) -> Dict:
        """
        Get a summary of loaded credentials (without sensitive data)
        
        Returns:
            Dict: Summary of credentials
        """
        if not self.credentials:
            return {"error": "No credentials loaded"}
        
        summary = {
            "apps_configured": 1 if self.credentials.get('slack') else 0,
            "active_apps": len(self.get_all_apps()),
            "api_configured": bool(self.credentials.get('api')),
            "slack_configured": bool(self.credentials.get('slack'))
        }
        return summary

# Global instance
credentials_manager = SlackCredentialsManager() 