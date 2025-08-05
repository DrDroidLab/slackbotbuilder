import json
import sys
import logging
import re
from mcp_servers.mcp_utils import execute_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration variables
TOOL_NAME = "native_k8_connection_ode_command"
DEFAULT_NAMESPACE = "default"
DEFAULT_DEPLOYMENT = "app"

def extract_restart_params(slack_message_json):
    """Extract restart parameters from Slack message using regex"""
    
    message_text = slack_message_json.get('text', '')
    
    # Extract namespace
    namespace_match = re.search(r'namespace:\s*([a-zA-Z0-9_-]+)', message_text)
    namespace = namespace_match.group(1) if namespace_match else DEFAULT_NAMESPACE
    
    # Extract deployment/pod name
    deployment_match = re.search(r'(?:deployment|pod):\s*([a-zA-Z0-9_-]+)', message_text)
    deployment = deployment_match.group(1) if deployment_match else DEFAULT_DEPLOYMENT
    
    # Extract restart type (deployment, pod, or all)
    restart_type = "deployment"
    if "pod" in message_text.lower():
        restart_type = "pod"
    elif "all" in message_text.lower():
        restart_type = "all"
    
    logger.info(f"Extracted params - Namespace: {namespace}, Deployment: {deployment}, Type: {restart_type}")
    
    return {
        "namespace": namespace,
        "deployment": deployment,
        "restart_type": restart_type
    }

def k8s_auto_restart_tool(slack_message_json):
    """Main function to perform Kubernetes auto-restart"""
    
    # Extract parameters from Slack message
    params = extract_restart_params(slack_message_json)
    namespace = params["namespace"]
    deployment = params["deployment"]
    restart_type = params["restart_type"]
    
    # Define restart commands based on type
    restart_commands = []
    
    if restart_type == "deployment":
        # Restart deployment by scaling down and up
        restart_commands.extend([
            f"kubectl get deployment {deployment} -n {namespace}",
            f"kubectl scale deployment {deployment} --replicas=0 -n {namespace}",
            f"kubectl scale deployment {deployment} --replicas=1 -n {namespace}",
            f"kubectl get deployment {deployment} -n {namespace}"
        ])
    elif restart_type == "pod":
        # Delete specific pod (it will be recreated by deployment)
        restart_commands.extend([
            f"kubectl get pods -n {namespace} | grep {deployment}",
            f"kubectl delete pod -l app={deployment} -n {namespace}",
            f"kubectl get pods -n {namespace} | grep {deployment}"
        ])
    else:  # all
        # Restart all deployments in namespace
        restart_commands.extend([
            f"kubectl get deployments -n {namespace}",
            f"kubectl get deployments -n {namespace} -o name | xargs -I {{}} kubectl scale {{}} --replicas=0 -n {namespace}",
            f"kubectl get deployments -n {namespace} -o name | xargs -I {{}} kubectl scale {{}} --replicas=1 -n {namespace}",
            f"kubectl get deployments -n {namespace}"
        ])
    
    # Execute restart commands
    results = []
    for i, command in enumerate(restart_commands):
        logger.info(f"Executing command {i+1}/{len(restart_commands)}: {command}")
        result = execute_tool(TOOL_NAME, {"command": command})
        results.append({
            "step": i + 1,
            "command": command,
            "result": result
        })
    
    # Create response
    ndjson_events = []
    ndjson_events.append({
        'type': 'tool_result',
        'tool_name': 'k8s_auto_restart',
        'tool_config': {
            'namespace': namespace,
            'deployment': deployment,
            'restart_type': restart_type,
            'commands_executed': len(restart_commands)
        },
        'tool_result': results
    })
    
    return ndjson_events

#boilerplating
def main():
    """
    Main function to execute k8s auto-restart workflow
    """
    try:
        if len(sys.argv) < 2:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
        
    except Exception as e:
        logger.error(f"An unexpected error occurred in main: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}
    
    slack_message_json = json.loads(sys.argv[1])
    tool_response = k8s_auto_restart_tool(slack_message_json)
    
    text = ''
    file_content = ""
    for response in tool_response:
        if response['type'] == 'tool_result':
            config = response['tool_config']
            text = text + (f"\n\nK8s Auto-Restart executed for {config['restart_type']} in namespace: {config['namespace']}\nDeployment: {config['deployment']}\nCommands executed: {config['commands_executed']}\nResult: in attached .txt file")
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