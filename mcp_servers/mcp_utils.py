import requests
import logging
import json
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load MCP server configuration from mcp.json
mcp_servers = {}

try:
    with open('mcp_servers/mcp.json', 'r') as f:
        external_config = json.load(f)
        # Handle the new format with mcpServers wrapper
        if "mcpServers" in external_config:
            # Convert the new format to the expected format
            for server_name, server_config in external_config["mcpServers"].items():
                mcp_servers[server_name] = server_config
        else:
            # Fallback to old format
            mcp_servers.update(external_config)
        logger.info("Loaded MCP configuration successfully")
except FileNotFoundError:
    logger.error("mcp.json file not found. Please create mcp_servers/mcp.json with your MCP server configuration.")
    raise
except Exception as e:
    logger.error(f"Error loading MCP configuration: {e}")
    raise

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
