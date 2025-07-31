import json
import sys
import logging
import time
from mcp_servers.mcp_utils import fetch_tools_list
from agents import agent_with_tools

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prompt_ai_agent(slack_message_json,history=[],tools = 'all'):
    system_prompt = f"""You are an AI assistant specialized in helping DevOps/SRE/On-call engineers in their day-to-day operations -- including debug production issues, proactive monitoring setup and more. 
                         Your primary goal is to provide and execute practical, actionable debugging guidance based *directly* on the user's problem/alert description.

CRITICAL INSTRUCTIONS:
- Analyze the user's message to understand their specific problem. You will receive instructions / notes from user or data sources for services. Prioritise these instructions over other information.
- You have access to multiple relevant tools. There will be tools that will help you get context and then there will be tools that will help you fetch actual data or take actions.
- Use the combination of both to help the user. Make sure to think logically as a software engineer would think who needs to figure out the issue and fix it. Use tools with right justifications.
- Text should be in Markdown format."""
    messages = []
    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": str(slack_message_json)})
    messages.extend(history)
    if tools == 'all':
        available_tools = fetch_tools_list()
        agent_chat = agent_with_tools(messages, available_tools)
    elif tools == 'none':
        available_tools = []
        #todo
    # add handling for approval flows
    return agent_chat

def agent_wrapper_fn(slack_message_json):
    """
    Main function to execute prompt-based workflow
    """
    try:
        if not slack_message_json:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
    except Exception as e:
        logger.error(f"An unexpected error occurred in main: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}
    print(slack_message_json)
    start_time = time.monotonic()
    agent_chat_response = prompt_ai_agent(slack_message_json)
    time_taken = time.monotonic() - start_time
    time_taken_str = f"\n\n_Time taken: {time_taken:.2f} seconds_"
    agent_chat_response.append({'type': 'time_taken','time_taken': time_taken_str})
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
    print("Test")
    

# prompt_ai_agent("prompts/sample_prompt.md","Error in Service, please fix it.")
