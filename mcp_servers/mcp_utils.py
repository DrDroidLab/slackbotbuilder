import requests
import logging
import json
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# load mcp.json
with open('mcp_servers/mcp.json', 'r') as f:
    mcp_servers = json.load(f)

# MCP URL configuration

def send_jsonrpc(server_name, method, params=None, request_id=1):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": request_id,
    }
    resp = requests.post(mcp_servers[server_name]['url'], json=payload)
    try:
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"HTTP error: {e}")
        logger.error(resp.text)
        return None
    return resp.json()

def fetch_tools_list(server_name, params=None, request_id=1):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": params or {},
        "id": request_id,
    }
    resp = requests.post(mcp_servers[server_name]['url'], json=payload)
    try:
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"HTTP error: {e}")
        logger.error(resp.text)
        return None
    return resp.json()

def execute_tool(server_name, tool_name, arguments, request_id=1):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": request_id,
    }
    resp = requests.post(mcp_servers[server_name]['url'], json=payload)
    try:
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"HTTP error: {e}")
        logger.error(resp.text)
        return None
    return resp.json()
