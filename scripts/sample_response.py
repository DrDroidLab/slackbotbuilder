#!/usr/bin/env python3
"""
Sample action script: Hello Response
This script responds with "hi" when triggered by a workflow.
"""

import json
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Main function that processes the Slack message and returns a response.
    
    Args:
        sys.argv[1]: JSON string of the Slack message event
        
    Returns:
        dict: Response to send back to Slack
    """
    try:
        # Get the Slack message JSON from command line argument
        if len(sys.argv) < 2:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
        
        # Parse the Slack message
        slack_message_json = sys.argv[1]
        slack_message = json.loads(slack_message_json)
        
        logger.info(f"Processing message: {slack_message.get('text', 'No text')}")
        
        # Extract message details
        message_text = slack_message.get('text', '')
        channel_id = slack_message.get('channel', '')
        user_id = slack_message.get('user', '')
        message_ts = slack_message.get('ts', '')
        
        # Create response
        response = {
            "text": "👋 This is a sample response from your Slack bot.",
            "channel": channel_id,
            "thread_ts": message_ts,  # Reply in thread
            "response_type": "in_channel"
        }
        
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
    # Print result as JSON for the calling process to capture
    print(json.dumps(result)) 