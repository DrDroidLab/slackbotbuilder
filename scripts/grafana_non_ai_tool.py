import json
import sys
import logging
from mcp_servers.mcp_utils import send_jsonrpc, fetch_tools_list, execute_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def main():
    try:
        if len(sys.argv) < 2:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
        
        slack_message_json = sys.argv[1]
        slack_message = json.loads(slack_message_json)
        logger.info(f"Processing message: {slack_message.get('text', 'No text')}")
        
        channel_id = slack_message.get('channel', '')
        message_ts = slack_message.get('ts', '')
        
        # 1. Initialize
        init_params = {"protocolVersion": "2025-06-18"}
        init_resp = send_jsonrpc("sample_server_1", "initialize", init_params, request_id=1)
        
        # 2. List tools
        tools_resp = fetch_tools_list("sample_server_1", "tools/list", request_id=2)
        
        # 3. Call test_connection
        test_conn_resp = execute_tool("sample_server_1", "test_connection", {}, request_id=3)
        
        # 4. Call fetch_dashboards
        dashboards_resp = execute_tool("sample_server_1", "grafana_fetch_all_dashboards", {}, request_id=4)
        
        # Prepare a summary text for Slack
        dashboards_text = json.dumps(dashboards_resp, indent=2) if dashboards_resp else "No dashboards found."
        response_text = f"Grafana Dashboards:\n```\n{dashboards_text}\n```"
        
        response = {
            "text": response_text,
            "channel": channel_id,
            "thread_ts": message_ts,
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
    print(json.dumps(result))