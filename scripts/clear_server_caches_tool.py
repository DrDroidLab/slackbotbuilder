import json
import sys
import logging
import re
from mcp_servers.mcp_utils import execute_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration variables
TOOL_NAME = "bash"
DEFAULT_SERVER = "localhost"
SERVER_REGEX_PATTERN = r'remote_server:\s*([a-zA-Z0-9._-]+)'

# Cache clearing command template
CACHE_CLEAR_COMMAND = """echo "===== MEMORY PROFILE BEFORE DROP_CACHES ====="
echo "### Free Memory Report ###"
free -h

echo -e "\\n### Dirty Memory (before) ###"
cat /proc/meminfo | grep -E 'Dirty|Writeback'

echo -e "\\nDropping caches..."
sudo sync; 
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

echo -e "\\n===== MEMORY PROFILE AFTER DROP_CACHES ====="
echo "### Free Memory Report ###"
free -h

echo -e "\\n### Dirty Memory (after) ###"
cat /proc/meminfo | grep -E 'Dirty|Writeback'

echo -e "\\n### Slab Memory (after) ###"
cat /proc/meminfo | grep -E 'Slab|SReclaimable|SUnreclaim'"""

def clear_server_caches_tool(slack_message_json):
    """Main function to clear caches on a remote server"""
    
    # Extract remote server from Slack message using regex
    message_text = slack_message_json.get('text', '')
    server_match = re.search(SERVER_REGEX_PATTERN, message_text)
    
    if server_match:
        extracted_server = server_match.group(1)
        logger.info(f"Extracted server from message: {extracted_server}")
    else:
        # Fallback to default server if no server specified
        extracted_server = DEFAULT_SERVER
        logger.warning(f"No server found in message, using {DEFAULT_SERVER}")
    
    # Use the cache clearing command template
    cache_clear_command = CACHE_CLEAR_COMMAND
    
    # Execute the bash command using the available tool
    logger.info(f"Executing cache clear command on server: {extracted_server}")
    result = execute_tool(TOOL_NAME, {"command": cache_clear_command})
    
    # Create response
    ndjson_events = []
    ndjson_events.append({
        'type': 'tool_result',
        'tool_name': 'cache_clear_command',
        'tool_config': {'server': extracted_server},
        'tool_result': result
    })
    
    # Return simple response without AI analysis (non-ai tool-call + non-ai analysis)
    return ndjson_events

#boilerplating
def main():
    """
    Main function to execute cache clearing workflow
    """
    try:
        if len(sys.argv) < 2:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
        
    except Exception as e:
        logger.error(f"An unexpected error occurred in main: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}
    
    slack_message_json = json.loads(sys.argv[1])
    tool_response = clear_server_caches_tool(slack_message_json)
    
    text = ''
    file_content = ""
    for response in tool_response:
        if response['type'] == 'tool_result':
            text = text + ("\n\nCache Clear Command executed on server: " + response['tool_config']['server'] + "\nResult: in attached .txt file")
            file_content = file_content + ("\n\nTool Call:" + response['tool_name'] + " Tool Arguments: " + str(response['tool_config']) + " result: " + str(response['tool_result']))
    
    slack_message_response = {
        "text": text,
        "channel": slack_message_json.get('channel'),
        "thread_ts": slack_message_json.get('thread_ts', slack_message_json.get('ts', ''))
    }    
    
    if file_content:
        slack_message_response['file_content'] = file_content
    
    return slack_message_response

if __name__ == "__main__":
    result = main()
    if result:
        print(json.dumps(result)) 