import json
import sys
import logging
from mcp_servers.mcp_utils import send_jsonrpc, fetch_tools_list, execute_tool
from agents.agents import log_analyser_agent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#TODO -- create the function with the same name as your file.
def grafana_non_ai_tool(slack_message_json):
    params = {"datasource":"loki", "query":'{app="recommendationservice"} |= ``'}
    logs_data = execute_tool("grafana_datasource_query_execution", str(params))
    messages = []
    messages.append({"role": "system", "content": 'Analyse logs and make sure to search for errors.'})
    messages.append({"role": "user", "content": "This is the slack alert that I've received. Please analyse logs in context of it." + str(slack_message_json)})
    ndjson_events = []
    ndjson_events.append({'type':'tool_result','tool_name':'log_analyser','tool_config': str(params),'tool_result':logs_data})
    agent_chat = log_analyser_agent(logs_data, messages)
    return ndjson_events + agent_chat

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
    agent_chat_response = grafana_non_ai_tool(slack_message_json)
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
