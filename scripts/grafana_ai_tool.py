import json
import sys
import logging
from openai import OpenAI
from slack_utils.slack_credentials_manager import credentials_manager
from mcp_servers.mcp_utils import fetch_tools_list
from agents.agents import agent_with_tools
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

## core code
def grafana_ai_tool(slack_message):
    api_key = credentials_manager.get_openai_api_key()

    system_prompt = f"""Investigate this alert and provide a summary by analysing metrics and dashboards."""
    messages = []
    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": str(slack_message)})
    agent_chat = []
    client = OpenAI(api_key=api_key)
    available_tools = fetch_tools_list()
    agent_chat = agent_with_tools(messages, available_tools)
    return agent_chat

#boilerplating
def main():
    """
    Main function to execute prompt-based workflow
    """
    try:
        if len(sys.argv) < 2:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
        
    except Exception as e:
        logger.error(f"An unexpected error occurred in main: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}
    slack_message_json = json.loads(sys.argv[1])
    agent_chat_response = grafana_ai_tool(slack_message_json)
    text = ''
    file_content = ""
    for response in agent_chat_response:
        if response['type'] == 'chat_text':
            text = text + (response['content'])
        # add tool result to a .txt file
        elif response['type'] == 'tool_result':
            text = text + ("\n\nTool Call: " + response['tool_name'] + " Tool Arguments: " + str(response['tool_config']) + " result: in attached .txt file")
            file_content = file_content + ("\n\nTool Call:" + response['tool_name'] + " Tool Arguments: " + str(response['tool_config']) + " result: " + str(response['tool_result']))
        elif response['type'] == 'time_taken':
            text = text + (response['time_taken'])
    slack_message_response = {
        "text": text,
        "channel": slack_message_json.get('channel'),
        "thread_ts": slack_message_json.get('thread_ts',slack_message_json.get('ts',''))
    }    
    if file_content:
        slack_message_response['file_content'] = file_content
    return slack_message_response

if __name__ == "__main__":
    result = main()
    if result:
        print(json.dumps(result))

# prompt_ai_agent("prompts/sample_prompt.md","Error in Service, please fix it.")
