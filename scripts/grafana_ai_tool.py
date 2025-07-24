import requests
import json
import sys
import logging
from openai import OpenAI
from slack_credentials_manager import credentials_manager

MCP_URL = "http://localhost:8000/mcp"  # Change if your server is running elsewhere

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_jsonrpc(method, params=None, request_id=1):
    """Sends a JSON-RPC request to the MCP server."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": request_id,
    }
    try:
        resp = requests.post(MCP_URL, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.Timeout:
        logger.error("Request to MCP server timed out.")
        return {"error": {"message": "Request timed out"}}
    except requests.RequestException as e:
        logger.error(f"HTTP error: {e}")
        return {"error": {"message": str(e)}}

def get_llm_decision(prompt, tools, api_key):
    """Gets a decision from the LLM on whether to call a tool."""
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[{"role": "user", "content": prompt}],
            tools=tools,
            tool_choice="auto",
        )
        return response.choices[0].message
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
        return None

def main():
    """Processes the Slack message, uses an LLM to decide on a tool, and interacts with the MCP server."""
    try:
        if len(sys.argv) < 2:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
        
        slack_message = json.loads(sys.argv[1])
        logger.info(f"Processing message: {slack_message.get('text', 'No text')}")

        channel_id = slack_message.get('channel')
        message_ts = slack_message.get('ts')
        prompt = slack_message.get('text', '').strip()

        if not prompt:
            return {"text": "Please provide a prompt.", "channel": channel_id, "thread_ts": message_ts}

        # 1. Get tools from MCP server
        tools_list_resp = send_jsonrpc("tools/list")
        if "error" in tools_list_resp or "result" not in tools_list_resp:
            return {"text": "Error: Could not retrieve tools from the MCP server.", "channel": channel_id, "thread_ts": message_ts}
        
        available_tools = tools_list_resp.get("result", {}).get("tools", [])
        if not available_tools:
            return {"text": "Error: No tools available from the MCP server.", "channel": channel_id, "thread_ts": message_ts}
        
        # Format tools for OpenAI API
        openai_tools = [{"type": "function", "function": tool} for tool in available_tools]

        # 2. Get LLM decision
        api_key = credentials_manager.get_openai_api_key()
        if not api_key:
            return {"text": "Error: OpenAI API key not found.", "channel": channel_id, "thread_ts": message_ts}

        llm_message = get_llm_decision(prompt, openai_tools, api_key)

        # 3. Execute tool call if decided by LLM
        if llm_message and llm_message.tool_calls:
            tool_call = llm_message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"LLM decided to call tool '{tool_name}' with args: {tool_args}")
            
            tool_response = send_jsonrpc("tools/call", {"name": tool_name, "arguments": tool_args})
            
            if "error" in tool_response:
                response_text = f"Error executing tool '{tool_name}': {tool_response['error']['message']}"
            else:
                result_text = json.dumps(tool_response.get("result", "No result"), indent=2)
                response_text = f"Result from `{tool_name}`:\n```\n{result_text}\n```"
        else:
            # Fallback to text response if no tool is called
            response_text = llm_message.content if llm_message else "I was unable to process your request."

        return {
            "text": response_text,
            "channel": channel_id,
            "thread_ts": message_ts,
        }

    except Exception as e:
        logger.error(f"An unexpected error occurred in main: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}

if __name__ == "__main__":
    result = main()
    if result:
        print(json.dumps(result)) 