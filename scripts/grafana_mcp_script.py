import requests
import json

MCP_URL = "http://localhost:8000/mcp"  # Change if your server is running elsewhere

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
        print(f"HTTP error: {e}")
        print(resp.text)
        return None
    return resp.json()

def pretty_print(title, data):
    print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    # 1. Initialize
    init_params = {"protocolVersion": "2025-06-18"}
    init_resp = send_jsonrpc("initialize", init_params, request_id=1)
    pretty_print("Initialize", init_resp)

    # 2. List tools
    tools_resp = send_jsonrpc("tools/list", request_id=2)
    pretty_print("List Tools", tools_resp)

    # 3. Call test_connection
    test_conn_resp = send_jsonrpc("tools/call", {"name": "test_connection", "arguments": {}}, request_id=3)
    pretty_print("Test Connection", test_conn_resp)

    # 4. Call fetch_dashboards
    dashboards_resp = send_jsonrpc("tools/call", {"name": "grafana_fetch_all_dashboards", "arguments": {}}, request_id=4)
    pretty_print("Fetch Dashboards", dashboards_resp)