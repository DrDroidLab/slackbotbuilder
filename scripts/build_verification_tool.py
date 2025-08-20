import json
import sys
import logging
import re
from mcp_servers.mcp_utils import execute_tool
from agents.agents import agent_with_tools

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration variables
TOOL_NAME = "bash"
DEFAULT_ORIGIN = "https://origin.example.com"
DEFAULT_P3_HOST = "https://p3.example.com"
DEFAULT_PATH = "/api/health"
DEFAULT_DOMAINS = "example.com"

def extract_variables_with_ai(slack_message_json):
    """Use AI to extract variables from Slack message"""
    
    # Create messages for AI analysis
    messages = []
    messages.append({
        "role": "system", 
        "content": """You are a variable extraction expert. Extract the following variables from the user's message:
- domain: The domain(s) to check (comma-separated if multiple)
- path: The API path to check
- origin: The origin server URL
- p3-host: The P3 host server URL

Return ONLY a JSON object with these exact keys: {"domain": "...", "path": "...", "origin": "...", "p3-host": "..."}
If any variable is not found, use placeholder values."""
    })
    
    messages.append({
        "role": "user", 
        "content": f"Extract variables from this message: {slack_message_json.get('text', '')}"
    })
    
    # Use AI to extract variables
    try:
        # Get available tools (empty list since we don't need external tools for extraction)
        available_tools = []
        ai_response = agent_with_tools(messages, available_tools)
        
        # Extract the AI response text
        ai_text = ""
        for response in ai_response:
            if response['type'] == 'chat_text':
                ai_text += response['content']
        
        # Try to parse JSON from AI response
        import re
        json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        if json_match:
            extracted_vars = json.loads(json_match.group())
            logger.info(f"AI extracted variables: {extracted_vars}")
            return extracted_vars
        else:
            logger.warning("Could not parse JSON from AI response, using defaults")
            return {
                "domain": DEFAULT_DOMAINS,
                "path": DEFAULT_PATH,
                "origin": DEFAULT_ORIGIN,
                "p3-host": DEFAULT_P3_HOST
            }
            
    except Exception as e:
        logger.error(f"Error in AI variable extraction: {e}")
        return {
            "domain": DEFAULT_DOMAINS,
            "path": DEFAULT_PATH,
            "origin": DEFAULT_ORIGIN,
            "p3-host": DEFAULT_P3_HOST
        }

def build_verification_tool(slack_message_json):
    """Main function to verify build numbers"""
    
    # Extract variables using AI
    variables = extract_variables_with_ai(slack_message_json)
    
    domain = variables.get('domain', DEFAULT_DOMAINS)
    path = variables.get('path', DEFAULT_PATH)
    origin = variables.get('origin', DEFAULT_ORIGIN)
    p3_host = variables.get('p3-host', DEFAULT_P3_HOST)
    
    logger.info(f"Using variables - Domain: {domain}, Path: {path}, Origin: {origin}, P3-Host: {p3_host}")
    
    # Create the bash script with placeholders
    verification_script = f"""#!/bin/bash

# Define the origin and path
ORIGIN="{origin}"
P3HOST="{p3_host}"
PATH_TO_CHECK="{path}"
DOMAINS="{domain}"

echo "==================================================================="
# Instead of using an array, we'll iterate directly over the domains using a while loop
IFS=','  # Set input field separator to comma
for domain in $DOMAINS; do
	# Perform the curl request and grep for the BUILD_NUMBER
	ORIGIN_OUTPUT=$(curl -X GET "${{ORIGIN}}${{PATH_TO_CHECK}}" -H "Host: ${{domain}}" -k --compressed)
	P3_OUTPUT=$(curl -i -X GET "${{P3HOST}}${{PATH_TO_CHECK}}" -H "X-<service>-V-Host: ${{domain}}" -H "X-<service>-V-Bot: false" -k --compressed)

	ORIGIN_BUILD_NUMBER=$(echo "${{ORIGIN_OUTPUT}}" | grep -o '"BUILD_NUMBER":"[0-9]\+"')
	ORIGIN_BUILD_DATE=$(echo "${{ORIGIN_OUTPUT}}" | grep -o '"BUILD_DATE":"[0-9]\\{{4\\}}-[0-9]\\{{2\\}}-[0-9]\\{{2\\}}T[0-9]\\{{2\\}}:[0-9]\\{{2\\}}:[0-9]\\{{2\\}}\\.[0-9]\\{{3\\}}Z"')

	P3_BUILD_NUMBER=$(echo "${{P3_OUTPUT}}" | grep -o '"BUILD_NUMBER":"[0-9]\+"')
	P3_BUILD_DATE=$(echo "${{P3_OUTPUT}}" | grep -o '"BUILD_DATE":"[0-9]\\{{4\\}}-[0-9]\\{{2\\}}-[0-9]\\{{2\\}}T[0-9]\\{{2\\}}:[0-9]\\{{2\\}}:[0-9]\\{{2\\}}\\.[0-9]\\{{3\\}}Z"')
	P3_OPTIMIZED_PAGE=$(echo "${{P3_OUTPUT}}" | grep -o 'x-<service>-p3-optimized: [0-1]')

	ORIGIN_BUILD="$ORIGIN_BUILD_NUMBER | $ORIGIN_BUILD_DATE"
	P3_BUILD="$P3_BUILD_NUMBER | $P3_BUILD_DATE"

	echo "\\n\\nDOMAIN:\\t${{domain}}\\nORIGIN:\\t$ORIGIN_BUILD\\nP3:\\t$P3_BUILD\\n\\n"

	if [ "$ORIGIN_BUILD" != "$P3_BUILD" ]; then
		echo "[FAILED]: Origin build is not same as the P3 build for domain '${{domain}}'"
		exit 1
	fi
	echo "[PASSED]: Origin build is same as the P3 build for domain '${{domain}}'"
	
	if [ "$P3_OPTIMIZED_PAGE" = "x-<service>-p3-optimized: 0" ]; then
		echo "[FAILED]: P3 page is not optimized for domain '${{domain}}': $P3_OPTIMIZED_PAGE \\n"
	else
		echo "[PASSED]: P3 page is optimized for domain '${{domain}}': $P3_OPTIMIZED_PAGE \\n"
	fi

	echo "==================================================================="
done"""
    
    # Execute the verification script using the available tool
    logger.info("Executing build verification script")
    result = execute_tool(TOOL_NAME, {"command": verification_script})
    
    # Create response
    ndjson_events = []
    ndjson_events.append({
        'type': 'tool_result',
        'tool_name': 'build_verification',
        'tool_config': {
            'domain': domain,
            'path': path,
            'origin': origin,
            'p3-host': p3_host
        },
        'tool_result': result
    })
    
    return ndjson_events

#boilerplating
def main():
    """
    Main function to execute build verification workflow
    """
    try:
        if len(sys.argv) < 2:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
        
    except Exception as e:
        logger.error(f"An unexpected error occurred in main: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}
    
    slack_message_json = json.loads(sys.argv[1])
    tool_response = build_verification_tool(slack_message_json)
    
    text = ''
    file_content = ""
    for response in tool_response:
        if response['type'] == 'tool_result':
            config = response['tool_config']
            text = text + (f"\n\nBuild Verification executed for domain: {config['domain']}\nPath: {config['path']}\nResult: in attached .txt file")
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