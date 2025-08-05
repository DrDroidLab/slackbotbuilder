import hmac
import hashlib
import time
import logging
from fastapi import Request, BackgroundTasks
import requests
from slack_credentials_manager import credentials_manager
from workflow_manager import workflow_manager
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from markdown_to_mrkdwn import SlackMarkdownConverter

logger = logging.getLogger(__name__)

class SlackEventHandler:
    def __init__(self):
        self.slack_api_base = "https://slack.com/api"
        self.processed_messages = set()  # Track processed message IDs
        self.max_processed_messages = 1000  # Limit to prevent memory bloat
    
    def cleanup_processed_messages(self):
        """Cleanup old processed messages to prevent memory bloat"""
        if len(self.processed_messages) > self.max_processed_messages:
            # Keep only the most recent 500 messages
            self.processed_messages = set(list(self.processed_messages)[-500:])
            print(f"🧹 CLEANUP: Reduced processed messages to 500")

    def verify_signature(self, request_body, signature, timestamp):
        """Verify Slack request signature"""
        try:
            # Get the signing secret from credentials
            signing_secret = credentials_manager.get_signing_secret()
            
            if not signing_secret:
                logger.error(f"No signing secret available")
                return False
            
            # Create the signature base string
            sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}"
            
            # Create the expected signature
            expected_signature = f"v0={hmac.new(signing_secret.encode('utf-8'), sig_basestring.encode('utf-8'), hashlib.sha256).hexdigest()}"
                        
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    async def handle_message_event_async(self, event_data):
        """Handle incoming message events (asynchronous)"""
        try:
            event_type = event_data.get('type')
            event_subtype = event_data.get('subtype')
                        
            # Skip bot messages and message edits/deletions for now
            if event_subtype in ['message_changed', 'message_deleted']:
                logger.info(f"Ignoring message with subtype: {event_subtype}")
                return
            
            # Extract message data
            message_id = event_data.get('ts')
            channel_id = event_data.get('channel')
            user_id = event_data.get('user')
            message_text = event_data.get('text', '')
            event_type = event_data.get('type')
            thread_timestamp = event_data.get('thread_ts')
            parent_message_id = event_data.get('parent_user_id')
            
            # Deduplication: Skip if we've already processed this message
            message_key = f"{message_id}_{channel_id}_{user_id}_{event_type}"
            if message_key in self.processed_messages:
                print(f"🔄 SKIPPING: Already processed message: {message_key}")
                return
            
            # Mark this message as processed
            self.processed_messages.add(message_key)
            print(f"✅ PROCESSING: New message: {message_key}")
            
            # Debug: Log the full event data to see what we're getting
            print(f"🔍 DEBUG: Full event data: {event_data}")
            
            # Get app configuration from credentials
            app_config = credentials_manager.get_app_config()
            if not app_config:
                logger.error(f"App configuration not found")
                return
            
            # Skip messages sent by the bot itself
            bot_user_id = self.get_bot_user_id(app_config['bot_token'])
            print(f"🔍 DEBUG: Message from user_id: {user_id}, bot_user_id: {bot_user_id}")
            if user_id == bot_user_id:
                print(f"🚫 IGNORING: Message from bot itself: {message_id}")
                return
            
            # Additional check: Skip if message has bot_id field (indicates bot message)
            if event_data.get('bot_id'):
                print(f"🚫 IGNORING: Message with bot_id: {event_data.get('bot_id')}")
                return
            
            
            # Get user information
            user_info = self.get_user_info(user_id, app_config['bot_token'])
            user_name = user_info.get('name', 'unknown')
            user_display_name = user_info.get('real_name', user_name)
            
            # Get channel name
            channel_name = self.get_channel_name(channel_id, app_config['bot_token'])

            is_bot_mentioned = False
            # Determine message type
            message_type = 'message'
            if event_type == 'app_mention':
                message_type = 'app_mention'
                is_bot_mentioned = True
                            
            # Log message processing (instead of storing in database)
            logger.info(f"Processing message {message_id} from user {user_name} in channel {channel_name} ({channel_id})")
            logger.info(f"Message text: {message_text}")
            logger.info(f"Bot mentioned: {is_bot_mentioned}")
                        
            # Process message through workflow system
            workflow_response = workflow_manager.process_message(event_data, channel_name, user_display_name, is_bot_mentioned)
                            
            # Send workflow response if available
            if workflow_response:
                self.send_workflow_response(workflow_response, app_config['bot_token'])
                            
            logger.info(f"Processed message {message_id} from user {user_name}")
            
        except Exception as e:
            logger.error(f"Error processing message event: {e}")
    
    def get_user_info(self, user_id, bot_token):
        """Get user information from Slack API"""
        try:
            response = requests.get(
                f"{self.slack_api_base}/users.info",
                params={"user": user_id},
                headers={"Authorization": f"Bearer {bot_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    user = data.get('user', {})
                    return {
                        'name': user.get('name', 'unknown'),
                        'real_name': user.get('real_name', 'unknown'),
                        'email': user.get('profile', {}).get('email', '')
                    }
            
            return {'name': 'unknown', 'real_name': 'unknown'}
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {'name': 'unknown', 'real_name': 'unknown'}
    
    def get_bot_user_id(self, bot_token):
        """Get bot user ID from Slack API"""
        try:
            response = requests.get(
                f"{self.slack_api_base}/auth.test",
                headers={"Authorization": f"Bearer {bot_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('user_id')
            return None
            
        except Exception as e:
            logger.error(f"Error getting bot user ID: {e}")
            return None
    
    def process_bot_mention(self, event_data, app_config):
        """Process bot mention and generate response"""
        try:
            message_text = event_data.get('text', '')
            channel_id = event_data.get('channel')
            message_id = event_data.get('ts')
            
            # Remove bot mention from message
            bot_user_id = self.get_bot_user_id(app_config['bot_token'])
            if bot_user_id:
                message_text = message_text.replace(f"<@{bot_user_id}>", "").strip()
            
            # Generate response (placeholder for now)
            response_text = f"I received your message: '{message_text}'. This is a placeholder response."
            
            # Send response to Slack
            response_message_id = self.send_message(channel_id, response_text, app_config['bot_token'])
            
            # Log bot response (instead of storing in database)
            if response_message_id:
                logger.info(f"Bot response sent: {response_message_id}")
                logger.info(f"Response text: {response_text}")
                logger.info(f"Channel: {channel_id}")
            else:
                logger.error("Failed to send bot response")
            
            logger.info(f"Processed bot mention in channel {channel_id}")
            
        except Exception as e:
            logger.error(f"Error processing bot mention: {e}")
    
    def send_message(self, channel_id, text, bot_token):
        """Send message to Slack channel"""
        try:
            response = requests.post(
                f"{self.slack_api_base}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {bot_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "channel": channel_id,
                    "text": text
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('ts')
            
            logger.error(f"Failed to send message: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    

    def send_workflow_response(self, workflow_response, bot_token):
        """Send workflow response to Slack"""
        try:
            # Extract response details
            text = workflow_response.get('text', '')
            channel = workflow_response.get('channel', '')
            thread_ts = workflow_response.get('thread_ts')
            file_content = workflow_response.get('file_content', '')
            converter = SlackMarkdownConverter()
            text = converter.convert(text)

            if file_content:
                try:
                    file_upload_slack_client = WebClient(token=bot_token)
                # Upload the text file to Slack
                    response = file_upload_slack_client.files_upload_v2(
                        title="DroidAgent Tool Result",
                        filename="droidagent_tool_result.txt",
                        content=file_content,
                    )
                    
                    # The response contains the uploaded file information
                    uploaded_file_url = response.get("file").get("permalink")
                    print(f"File uploaded successfully! File ID: {uploaded_file_url}")
                    if uploaded_file_url:
                        text = text + (f"\n\n<{uploaded_file_url}|Tool Results>")


                except SlackApiError as e:
                    print(f"Error uploading file: {e.response['error']}") 
                    text = text + (f"\n\nError uploading file.")
                        
            if not text or not channel:
                logger.error("Invalid workflow response: missing text or channel")
                return None
            # split into blocks of 2000 characters
            blocks = []
            for i in range(0, len(text), 2000):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text[i:i+2000]
                    }
                })
            # Prepare message payload
            message_payload = {
                "channel": channel,
                "blocks": blocks
                }
            if thread_ts:
                message_payload["thread_ts"] = thread_ts
            response = requests.post(
                f"{self.slack_api_base}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {bot_token}",
                    "Content-Type": "application/json"
                },
                json=message_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    logger.info(f"Workflow response sent successfully")
                    return data.get('ts')
                else:
                    logger.error(f"Slack API error: {data.get('error', 'Unknown error')}")
            else:
                logger.error(f"Failed to send workflow response: {response.text}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending workflow response: {e}")
            return None
    
    def handle_app_installed_event(self, event_data):
        """Handle app_installed event - when app is added to a workspace"""
        try:
            logger.info(f"App installed event received")
            # Extract workspace information
            team_id = event_data.get('team_id')
            team_name = event_data.get('team_name', '')
            team_domain = event_data.get('team_domain', '')
            
            # Log installation event
            logger.info(f"App installed in workspace: {team_name} ({team_id})")
            return {"status": "success", "message": "App installation recorded"}
            
        except Exception as e:
            logger.error(f"Error handling app installed event: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_app_installed_event_async(self, event_data):
        """Handle app_installed event - when app is added to a workspace (asynchronous)"""
        try:
            logger.info(f"App installed event received")
            
            # Extract workspace information
            team_id = event_data.get('team_id')
            team_name = event_data.get('team_name', '')
            team_domain = event_data.get('team_domain', '')
            
            # Log installation event
            logger.info(f"App installed in workspace: {team_name} ({team_id})")
            
        except Exception as e:
            logger.error(f"Error handling app installed event: {e}")
    
    def handle_app_uninstalled_event(self, event_data):
        """Handle app_uninstalled event - when app is removed from a workspace"""
        try:
            logger.info(f"App uninstalled event received")
            
            # Extract workspace information
            team_id = event_data.get('team_id')
            
            # Log uninstallation event
            logger.info(f"App uninstalled from workspace: {team_id}")
            return {"status": "success", "message": "App uninstallation recorded"}
            
        except Exception as e:
            logger.error(f"Error handling app uninstalled event: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_app_uninstalled_event_async(self, event_data):
        """Handle app_uninstalled event - when app is removed from a workspace (asynchronous)"""
        try:
            logger.info(f"App uninstalled event received")
            
            # Extract workspace information
            team_id = event_data.get('team_id')
            
            # Log uninstallation event
            logger.info(f"App uninstalled from workspace: {team_id}")
            
        except Exception as e:
            logger.error(f"Error handling app uninstalled event: {e}")
    
    def handle_channel_created_event(self, event_data):
        """Handle channel_created event - when a new channel is created"""
        try:
            logger.info(f"Channel created event received")
            
            # Extract channel information
            channel_id = event_data.get('channel', {}).get('id')
            channel_name = event_data.get('channel', {}).get('name', '')
            channel_type = 'public'  # New channels are typically public
            creator_id = event_data.get('channel', {}).get('creator')
            
            if channel_id and channel_name:
                # Log channel creation
                logger.info(f"Channel created: {channel_name} ({channel_id}) by user {creator_id}")
                return {"status": "success", "message": "Channel created"}
            else:
                logger.error("Missing channel information in event")
                return {"status": "error", "message": "Missing channel information"}
            
        except Exception as e:
            logger.error(f"Error handling channel created event: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_channel_created_event_async(self, event_data):
        """Handle channel_created event - when a new channel is created (asynchronous)"""
        try:
            logger.info(f"Channel created event received")
            
            # Extract channel information
            channel_id = event_data.get('channel', {}).get('id')
            channel_name = event_data.get('channel', {}).get('name', '')
            creator_id = event_data.get('channel', {}).get('creator')
            
            if channel_id and channel_name:
                # Log channel creation
                logger.info(f"Channel created: {channel_name} ({channel_id}) by user {creator_id}")
            else:
                logger.error("Missing channel information in event")
            
        except Exception as e:
            logger.error(f"Error handling channel created event: {e}")

    async def handle_channel_deleted_event_async(self, event_data):
        """Handle channel_deleted event - when a channel is deleted (asynchronous)"""
        try:
            logger.info(f"Channel deleted event received")
            channel_id = event_data.get('channel')
            if channel_id:
                logger.info(f"Channel deleted: {channel_id}")
            else:
                logger.error("Missing channel ID in event")
        except Exception as e:
            logger.error(f"Error handling channel deleted event: {e}")

    async def handle_member_joined_channel_event_async(self, event_data):
        """Handle member_joined_channel event (asynchronous)"""
        try:
            logger.info(f"Member joined channel event received")
            channel_id = event_data.get('channel')
            user_id = event_data.get('user')
            logger.info(f"User {user_id} joined channel {channel_id}")
        except Exception as e:
            logger.error(f"Error handling member joined channel event: {e}")

    async def handle_member_left_channel_event_async(self, event_data):
        """Handle member_left_channel event (asynchronous)"""
        try:
            logger.info(f"Member left channel event received")
            channel_id = event_data.get('channel')
            user_id = event_data.get('user')
            logger.info(f"User {user_id} left channel {channel_id}")
        except Exception as e:
            logger.error(f"Error handling member left channel event: {e}")
    
    def handle_channel_deleted_event(self, event_data):
        """Handle channel_deleted event - when a channel is deleted"""
        try:
            logger.info(f"Channel deleted event received")
            
            # Extract channel information
            channel_id = event_data.get('channel')
            
            if channel_id:
                # Log channel deletion
                logger.info(f"Channel deleted: {channel_id}")
                return {"status": "success", "message": "Channel deleted"}
            else:
                logger.error("Missing channel ID in event")
                return {"status": "error", "message": "Missing channel ID"}
            
        except Exception as e:
            logger.error(f"Error handling channel deleted event: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_member_joined_channel_event(self, event_data):
        """Handle member_joined_channel event - when a member (including bot) joins a channel"""
        try:
            logger.info(f"Member joined channel event received")
            
            # Extract event information
            channel_id = event_data.get('channel')
            user_id = event_data.get('user')
            team_id = event_data.get('team')
            
            # Get app configuration to check if this is our bot
            app_config = credentials_manager.get_app_config()
            if not app_config:
                logger.error(f"App configuration not found")
                return {"status": "error", "message": "App not configured"}
            
            # Get bot user ID
            bot_user_id = self.get_bot_user_id(app_config['bot_token'])
            
            # Check if the joining member is our bot
            if user_id == bot_user_id:
                logger.info(f"Bot joined channel: {channel_id}")
                
                # Get channel info from Slack API
                channel_info = self.get_channel_info(channel_id, app_config['bot_token'])
                if channel_info:
                    channel_name = channel_info.get('name', f"channel-{channel_id}")
                    channel_type = 'private' if channel_info.get('is_private', False) else 'public'
                    member_count = channel_info.get('num_members', 0)
                    
                    logger.info(f"Channel {channel_name} - Bot installed, {member_count} members")
                else:
                    logger.warning(f"Could not get channel info for {channel_id}")
                
                return {"status": "success", "message": "Bot added to channel"}
            else:
                # Regular user joined - log the event
                logger.info(f"User {user_id} joined channel {channel_id}")
                return {"status": "success", "message": "Member joined channel"}
            
        except Exception as e:
            logger.error(f"Error handling member joined channel event: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_member_left_channel_event(self, event_data):
        """Handle member_left_channel event - when a member (including bot) leaves a channel"""
        try:
            logger.info(f"Member left channel event received")
            
            # Extract event information
            channel_id = event_data.get('channel')
            user_id = event_data.get('user')
            team_id = event_data.get('team')
            
            # Get app configuration to check if this is our bot
            app_config = credentials_manager.get_app_config()
            if not app_config:
                logger.error(f"App configuration not found")
                return {"status": "error", "message": "App not configured"}
            
            # Get bot user ID
            bot_user_id = self.get_bot_user_id(app_config['bot_token'])
            
            # Check if the leaving member is our bot
            if user_id == bot_user_id:
                logger.info(f"Bot left channel: {channel_id}")
                return {"status": "success", "message": "Bot removed from channel"}
            else:
                # Regular user left - log the event
                logger.info(f"User {user_id} left channel {channel_id}")
                return {"status": "success", "message": "Member left channel"}
            
        except Exception as e:
            logger.error(f"Error handling member left channel event: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_channel_info(self, channel_id, bot_token):
        """Get channel information from Slack API"""
        try:
            response = requests.get(
                f"{self.slack_api_base}/conversations.info",
                headers={
                    "Authorization": f"Bearer {bot_token}",
                    "Content-Type": "application/json"
                },
                params={"channel": channel_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('channel', {})
            
            logger.error(f"Failed to get channel info: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None
    
    def get_channel_name(self, channel_id, bot_token):
        """Get channel name from channel ID"""
        try:
            channel_info = self.get_channel_info(channel_id, bot_token)
            if channel_info:
                return channel_info.get('name', '')
            return ''
        except Exception as e:
            logger.error(f"Error getting channel name: {e}")
            return ''
    
    async def handle_event_async(self, request_data, request: Request = None):
        """Main event handler (asynchronous processing)"""
        try:
            # Verify request signature
            signature = request.headers.get('X-Slack-Signature') if request else None
            timestamp = request.headers.get('X-Slack-Request-Timestamp') if request else None
            
            if not signature or not timestamp:
                logger.error("Missing signature or timestamp")
                return
            
            # Check if request is too old (replay attack protection)
            if abs(time.time() - int(timestamp)) > 60 * 5:  # 5 minutes
                logger.error("Request timestamp too old")
                return
            
            # Get request body for signature verification
            request_body = await request.body() if request else b""
            
            # Verify signature using app
            if not self.verify_signature(request_body, signature, timestamp):
                logger.error("Invalid signature")
                return
            
            # Handle URL verification
            if request_data.get('type') == 'url_verification':
                logger.info(f"Event Type URL verification already handled in calling function")
                return
            
            # Handle events
            event = request_data.get('event', {})
            event_type = event.get('type')
            
            if event_type in ['message', 'app_mention']:
                await self.handle_message_event_async(event)
            elif event_type == 'app_installed':
                await self.handle_app_installed_event_async(event)
            elif event_type == 'app_uninstalled':
                await self.handle_app_uninstalled_event_async(event)
            elif event_type == 'channel_created':
                await self.handle_channel_created_event_async(event)
            elif event_type == 'channel_deleted':
                await self.handle_channel_deleted_event_async(event)
            elif event_type == 'member_joined_channel':
                await self.handle_member_joined_channel_event_async(event)
            elif event_type == 'member_left_channel':
                await self.handle_member_left_channel_event_async(event)
            else:
                logger.info(f"Unhandled event type: {event_type}")
            
        except Exception as e:
            logger.error(f"Error handling event: {e}")

# Initialize event handler
slack_event_handler = SlackEventHandler() 