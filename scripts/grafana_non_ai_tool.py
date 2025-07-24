import requests
import json
import sys
import logging

MCP_URL = "http://localhost:8000/mcp"  # Change if your server is running elsewhere

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_jsonrpc(method, params=None, request_id=1):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": request_id,
    }
    resp = requests.post(MCP_URL, json=payload)
    try:
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"HTTP error: {e}")
        logger.error(resp.text)
        return None
    return resp.json()

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
        init_resp = send_jsonrpc("initialize", init_params, request_id=1)
        
        # 2. List tools
        tools_resp = send_jsonrpc("tools/list", request_id=2)
        
        # 3. Call test_connection
        test_conn_resp = send_jsonrpc("tools/call", {"name": "test_connection", "arguments": {}}, request_id=3)
        
        # 4. Call fetch_dashboards
        dashboards_resp = send_jsonrpc("tools/call", {"name": "grafana_fetch_all_dashboards", "arguments": {}}, request_id=4)
        
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