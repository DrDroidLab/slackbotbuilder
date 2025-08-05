import json
import sys
import logging
import re
from mcp_servers.mcp_utils import execute_tool
from agents import log_analyser_agent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def k8s_5xx_errors_tool(slack_message_json):
    """Main function to investigate 5xx errors in Kubernetes namespaces"""
    
    # Extract namespace from Slack message using regex
    message_text = slack_message_json.get('text', '')
    namespace_match = re.search(r'namespace:\s*([a-zA-Z0-9_-]+)', message_text)
    
    if namespace_match:
        extracted_namespace = namespace_match.group(1)
        namespaces = [extracted_namespace]
        logger.info(f"Extracted namespace from message: {extracted_namespace}")
    else:
        # Fallback to default namespace if no match found
        namespaces = ["default"]
        logger.warning("No namespace found in message, using default namespace")
    
    # Use execute_tool to call kubernetes tool for 5xx error investigation
    # We'll use the available kubectl command tool to execute our investigation
    investigation_commands = []
    
    for namespace in namespaces:
        # Check for 5xx errors in ingress logs
        ingress_cmd = f"kubectl logs -l app.kubernetes.io/name=ingress-nginx -n {namespace} --tail=1000 2>&1 | grep ' 5[0-9][0-9] '"
        investigation_commands.append(f"# Ingress 5xx errors for {namespace}:")
        investigation_commands.append(ingress_cmd)
        
        # Check for 5xx errors in pod logs
        pod_cmd = f"kubectl logs -n {namespace} --tail=1000 --all-containers 2>&1 | grep ' 5[0-9][0-9] '"
        investigation_commands.append(f"# Pod 5xx errors for {namespace}:")
        investigation_commands.append(pod_cmd)
        
        # Get failing pods
        failing_cmd = f"kubectl get pods -n {namespace} --no-headers 2>&1"
        investigation_commands.append(f"# Failing pods for {namespace}:")
        investigation_commands.append(failing_cmd)
        
        # Get OOM/restarted pods
        oom_cmd = f"kubectl get pods -n {namespace} --no-headers"
        investigation_commands.append(f"# OOM/Restarted pods for {namespace}:")
        investigation_commands.append(oom_cmd)
        
        # Check probe failures
        probe_cmd = f"kubectl describe pods -n {namespace} 2>&1 | grep -A5 'Events:' | grep -iE 'Readiness probe failed|Liveness probe failed'"
        investigation_commands.append(f"# Probe failures for {namespace}:")
        investigation_commands.append(probe_cmd)
    
    # Execute all commands using the available kubectl tool
    investigation_data = []
    for cmd in investigation_commands:
        if cmd.startswith('#'):
            investigation_data.append(cmd)  # Add comment as header
        else:
            result = execute_tool("native_k8_connection_ode_command", {"command": cmd})
            investigation_data.append(f"Command: {cmd}")
            investigation_data.append(f"Result: {result}")
            investigation_data.append("---")
    
    # Create messages for AI analysis
    messages = []
    messages.append({"role": "system", "content": 'Analyse Kubernetes investigation data and make sure to search for 5xx errors and provide actionable recommendations.'})
    messages.append({"role": "user", "content": "This is the slack alert that I've received. Please analyse the Kubernetes investigation data in context of it." + str(slack_message_json)})
    
    ndjson_events = []
    ndjson_events.append({'type':'tool_result','tool_name':'kubectl_5xx_investigation','tool_config': {'namespaces': namespaces},'tool_result':investigation_data})
    
    agent_chat = log_analyser_agent(investigation_data, messages)
    return ndjson_events + agent_chat

#boilerplating
def main():
    """
    Main function to execute k8s 5xx errors investigation workflow
    """
    try:
        if len(sys.argv) < 2:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
        
    except Exception as e:
        logger.error(f"An unexpected error occurred in main: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}
    
    slack_message_json = json.loads(sys.argv[1])
    agent_chat_response = k8s_5xx_errors_tool(slack_message_json)
    
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
        "thread_ts": slack_message_json.get('thread_ts', slack_message_json.get('ts', ''))
    }    
    
    if file_content:
        slack_message_response['file_content'] = file_content
    
    return slack_message_response

if __name__ == "__main__":
    result = main()
    if result:
        print(json.dumps(result)) 