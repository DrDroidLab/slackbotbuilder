import json
import sys
import logging
from openai import OpenAI
from slack_credentials_manager import credentials_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_chatbot_response(prompt, api_key, instructions="You are a coding assistant that talks like a pirate.", model="gpt-4o"):
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return None

def main():
    try:
        if len(sys.argv) < 2:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
        
        slack_message_json = sys.argv[1]
        slack_message = json.loads(slack_message_json)
        
        
        # Ignore messages from bots to prevent loops
        if 'bot_id' in slack_message:
            logger.info("Ignoring message from bot to prevent loops.")
            return None

        logger.info(f"Processing message: {slack_message.get('text', 'No text')}")
        
        prompt = slack_message.get('text', '').strip()
        channel_id = slack_message.get('channel', '')
        message_ts = slack_message.get('ts', '')

        logger.info(f"Slack message: {slack_message}")
        
        if not prompt:
            response = {
                "text": "Please provide a prompt after the 'chatbot' keyword.",
                "channel": channel_id,
                "thread_ts": message_ts,
                "response_type": "in_channel"
            }
            logger.info(f"Generated response for empty prompt: {response}")
            return response

        # Get OpenAI API key from credentials
        api_key = credentials_manager.get_openai_api_key()
        if not api_key:
            return {"error": "OpenAI API key not found in credentials.yaml"}
            
        # Get chatbot response
        chatbot_response = get_chatbot_response(prompt, api_key)
        
        if chatbot_response:
            response = {
                "text": chatbot_response,
                "channel": channel_id,
                "thread_ts": message_ts,
                "response_type": "in_channel"
            }
        else:
            response = {"error": "Failed to get response from chatbot"}
            
        logger.info(f"Generated response: {response}")
        return response
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON provided: {e}")
        return {"error": "Invalid message format"}
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {"error": f"Processing error: {str(e)}"}

if __name__ == "__main__":
    result = main()
    print(json.dumps(result)) 