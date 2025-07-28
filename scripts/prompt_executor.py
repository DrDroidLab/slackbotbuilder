import json
import sys
import logging
import re
from typing import Dict, List, Any, Optional
from openai import OpenAI
from slack_credentials_manager import credentials_manager
from mcp_servers.mcp_utils import send_jsonrpc, fetch_tools_list, execute_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_parameters_from_slack_message(message_text: str, api_key: str = None) -> Dict[str, Any]:
    """
    Extract relevant parameters from Slack message using LLM
    
    Args:
        message_text: The Slack message text
        api_key: OpenAI API key (optional, will be fetched if not provided)
        
    Returns:
        Dict containing extracted parameters
    """
    if not api_key:
        api_key = credentials_manager.get_openai_api_key()
    
    if not api_key:
        logger.warning("No OpenAI API key available, falling back to basic extraction")
        return extract_parameters_basic(message_text)
    
    try:
        client = OpenAI(api_key=api_key)
        
        system_prompt = """
You are a parameter extraction specialist. Extract relevant parameters from user messages for Grafana operations.

## Available Parameter Types:
- environment: "production", "staging", "development", "dev", "prod"
- dashboard_id: Numeric dashboard IDs (e.g., "12345", "67890")
- search_query: Search terms for finding dashboards
- operation_type: "status", "health", "connection", "dashboards", "search"
- time_range: Time periods like "last hour", "today", "this week"
- datasource: Specific datasource names or types
- folder: Dashboard folder names
- tags: Dashboard tags

## Extraction Rules:
1. Look for environment mentions (production, staging, dev, etc.)
2. Extract dashboard IDs when mentioned
3. Identify search queries after "search" or similar terms
4. Determine operation type based on user intent
5. Extract time ranges if specified
6. Identify datasource mentions
7. Extract folder names if mentioned
8. Look for tag specifications

## Response Format:
Return ONLY a valid JSON object with extracted parameters. Example:
{
  "environment": "production",
  "dashboard_id": "12345",
  "search_query": "cpu metrics",
  "operation_type": "dashboards"
}

If no relevant parameters found, return empty object: {}
"""
        
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract parameters from this message: {message_text}"}
            ],
            max_tokens=200,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        # Parse the LLM response
        llm_response = response.choices[0].message.content.strip()
        
        # Try to parse as JSON
        try:
            params = json.loads(llm_response)
            logger.info(f"LLM extracted parameters: {params}")
            return params
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"LLM response: {llm_response}")
            # Fall back to basic extraction
            return extract_parameters_basic(message_text)
            
    except Exception as e:
        logger.error(f"Error in LLM parameter extraction: {e}")
        # Fall back to basic extraction
        return extract_parameters_basic(message_text)


def extract_parameters_basic(message_text: str) -> Dict[str, Any]:
    """
    Basic parameter extraction as fallback (original hardcoded logic)
    
    Args:
        message_text: The Slack message text
        
    Returns:
        Dict containing extracted parameters
    """
    params = {}
    
    # Extract environment mentions
    if "production" in message_text.lower() or "prod" in message_text.lower():
        params["environment"] = "production"
    elif "staging" in message_text.lower():
        params["environment"] = "staging"
    elif "development" in message_text.lower() or "dev" in message_text.lower():
        params["environment"] = "development"
    
    # Extract dashboard IDs (e.g., "dashboard 12345")
    dashboard_match = re.search(r'dashboard\s+(\d+)', message_text, re.IGNORECASE)
    if dashboard_match:
        params["dashboard_id"] = dashboard_match.group(1)
    
    # Extract search terms
    if "search" in message_text.lower():
        search_match = re.search(r'search\s+(.+)', message_text, re.IGNORECASE)
        if search_match:
            params["search_query"] = search_match.group(1).strip()
    
    # Extract specific tool mentions
    if "connection" in message_text.lower() or "connect" in message_text.lower():
        params["check_connection"] = True
    
    if "dashboards" in message_text.lower() or "dashboard" in message_text.lower():
        params["fetch_dashboards"] = True
    
    return params


def get_available_tools(server_name: str = "grafana-mcp-server") -> List[Dict]:
    """
    Get available tools from MCP server
    
    Args:
        server_name: Name of the MCP server
        
    Returns:
        List of available tools
    """
    try:
        tools_list_resp = fetch_tools_list(server_name, "tools/list")
        if "error" in tools_list_resp or "result" not in tools_list_resp:
            logger.error(f"Failed to fetch tools: {tools_list_resp}")
            return []
        
        available_tools = tools_list_resp.get("result", {}).get("tools", [])
        logger.info(f"Available tools: {[tool.get('name') for tool in available_tools]}")
        return available_tools
    except Exception as e:
        logger.error(f"Error fetching tools: {e}")
        return []


def create_system_prompt(runbook_content: str, available_tools: List[Dict], extracted_params: Dict[str, Any]) -> str:
    """
    Create a system prompt for the LLM with runbook instructions and context
    
    Args:
        runbook_content: Content of the runbook file
        available_tools: List of available MCP tools
        extracted_params: Parameters extracted from Slack message
        
    Returns:
        System prompt string
    """
    tools_info = "\n".join([f"- {tool.get('name')}: {tool.get('description', 'No description')}" 
                           for tool in available_tools])
    
    params_info = "\n".join([f"- {key}: {value}" for key, value in extracted_params.items()]) if extracted_params else "None"
    
    system_prompt = f"""
You are a runbook executor that follows instructions to execute tools.

## Available Tools:
{tools_info}

## Extracted Parameters from User Message:
{params_info}

## Runbook Instructions:
{runbook_content}

## Execution Rules:
1. Always start by testing the connection if the tool is available
2. Based on the user's request and extracted parameters, determine which tools to call
3. Use the extracted parameters to customize tool calls when relevant
4. If user mentions specific dashboards, search for them
5. If user wants all dashboards, fetch them all
6. Provide a clear summary of findings
7. Handle errors gracefully and report them clearly

## Response Format:
Return a JSON object with:
- "text": The response message for Slack
- "channel": The channel ID
- "thread_ts": The thread timestamp
- "tool_calls": List of tools that were called
- "errors": List of any errors encountered

## Error Handling:
- If connection fails, report the error and stop
- If tool calls fail, log the error and continue if possible
- Always provide clear error messages to the user
"""
    return system_prompt


def execute_tool_with_llm_guidance(tool_name: str, arguments: Dict, server_name: str = "grafana-mcp-server") -> Dict:
    """
    Execute a tool with error handling
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments for the tool
        server_name: MCP server name
        
    Returns:
        Dict containing result or error
    """
    try:
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")
        result = execute_tool(server_name, tool_name, arguments)
        
        if "error" in result:
            logger.error(f"Tool {tool_name} failed: {result['error']}")
            return {"success": False, "error": result["error"], "tool": tool_name}
        else:
            logger.info(f"Tool {tool_name} executed successfully")
            return {"success": True, "result": result.get("result"), "tool": tool_name}
            
    except Exception as e:
        logger.error(f"Exception executing tool {tool_name}: {e}")
        return {"success": False, "error": str(e), "tool": tool_name}


def get_llm_decision(messages: List[Dict], available_tools: List[Dict], api_key: str) -> Optional[Dict]:
    """
    Get decision from LLM on which tools to call
    
    Args:
        messages: List of conversation messages (system, user, assistant, tool)
        available_tools: List of available tools
        api_key: OpenAI API key
        
    Returns:
        LLM response or None if failed
    """
    try:
        client = OpenAI(api_key=api_key)
        
        # Format tools for OpenAI API
        openai_tools = [{"type": "function", "function": tool} for tool in available_tools]
        
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto",
            max_tokens=4000,
            temperature=0.1
        )
        
        return response.choices[0].message
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
        return None


def main():
    """
    Main function to execute prompt-based workflow
    """
    try:
        if len(sys.argv) < 2:
            logger.error("No Slack message provided")
            return {"error": "No message provided"}
        
        slack_message = json.loads(sys.argv[1])
        logger.info(f"Processing message: {slack_message.get('text', 'No text')}")
        
        channel_id = slack_message.get('channel')
        message_ts = slack_message.get('ts')
        user_message = slack_message.get('text', '').strip()
        
        if not user_message:
            return {"text": "Please provide a message.", "channel": channel_id, "thread_ts": message_ts}
        
        # Get OpenAI API key first (needed for parameter extraction)
        api_key = credentials_manager.get_openai_api_key()
        if not api_key:
            return {"text": "Error: OpenAI API key not found.", "channel": channel_id, "thread_ts": message_ts}
        
        # Extract parameters from user message using LLM
        extracted_params = extract_parameters_from_slack_message(user_message, api_key)
        logger.info(f"Extracted parameters: {extracted_params}")
        
        # Get available tools from MCP server
        available_tools = get_available_tools()
        if not available_tools:
            return {
                "text": "Error: Could not retrieve tools from the MCP server.", 
                "channel": channel_id, 
                "thread_ts": message_ts
            }
        

        
        # Read the runbook content from the enhanced message
        runbook_content = slack_message.get('prompt_content', '')
        if not runbook_content:
            logger.warning("No prompt content provided, using default runbook")
        
        # Prepare tools and parameters info
        tools_info = "\n".join([f"- {tool.get('name')}: {tool.get('description', 'No description')}" 
                               for tool in available_tools])
        
        params_info = "\n".join([f"- {key}: {value}" for key, value in extracted_params.items()]) if extracted_params else "None"
        
        # Create comprehensive system prompt for multi-tool execution
        system_prompt = f"""
You are an AI assistant that executes user instructions using available tools via MCP server.

## Available Tools:
{tools_info}

## User's Request:
{runbook_content}

## Extracted Parameters:
{params_info}

## CRITICAL INSTRUCTIONS:
You MUST execute MULTIPLE tool calls for multiple instructions. For each instruction in the user's request, make a separate tool call.

## Step-by-Step Process:
1. Parse the user's request line by line
2. For EACH instruction, determine which tool is needed
3. Make a tool call for EACH instruction
4. If an instruction requires finding something first (like a dashboard), make TWO tool calls:
   - First: Find the item (e.g., grafana_fetch_all_dashboards)
   - Second: Get the specific item (e.g., grafana_fetch_dashboard_by_id with the found UID)

## Available Tools for Grafana Operations:
- test_connection: Check Grafana connectivity
- grafana_fetch_all_dashboards: Get all dashboards
- grafana_fetch_dashboard_by_id: Get specific dashboard by UID
- grafana_get_dashboard_config: Get dashboard configuration
- grafana_fetch_datasources: Get all datasources
- grafana_fetch_folders: Get all folders

## CRITICAL INSTRUCTIONS:
You MUST execute MULTIPLE tool calls for multiple instructions in a single response.

## EXECUTION STRATEGY:
For multiple instructions, you MUST make multiple tool calls in a single response.

## EXAMPLE:
User: "Get me a list of all the grafana dashboards. get me data from the kubernetes / api server dashboard"

You MUST make TWO tool calls in a single response:
1. Call grafana_fetch_all_dashboards (to get all dashboards)
2. Call grafana_fetch_dashboard_by_id with the UID found from the first call (search for "Kubernetes / API server" in the results and use its UID)

## IMPORTANT:
- Make ALL necessary tool calls in a single response
- Execute tools in logical order (find first, then get specific)
- Use the exact tool names and parameters needed
- For the second instruction, find the dashboard UID from the first tool call results
- Search for the dashboard title in the results and extract its UID dynamically
"""
        
        # Smart single-shot execution with result analysis
        tool_calls = []
        errors = []
        results = []
        
        # Create initial messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Execute the runbook based on the available tools and extracted parameters."}
        ]
        
        logger.info("Creating LLM request for tool execution...")
        
        # Get LLM decision with potential multiple tool calls
        llm_message = get_llm_decision(messages, available_tools, api_key)
        
        if not llm_message:
            errors.append("❌ Failed to get LLM decision")
        else:
            logger.info(f"LLM response content: {llm_message.content}")
            logger.info(f"LLM tool calls: {llm_message.tool_calls}")
            
            # Execute tool calls if any
            if llm_message.tool_calls:
                logger.info(f"LLM requested {len(llm_message.tool_calls)} tool calls")
                
                # Execute tools sequentially
                for tool_call in llm_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")
                    
                    # Execute the tool
                    tool_result = execute_tool_with_llm_guidance(tool_name, tool_args)
                    tool_calls.append(tool_result)
                    
                    if tool_result["success"]:
                        result_text = f"✅ {tool_name}: {tool_result['result']}"
                        results.append(result_text)
                    else:
                        error_text = f"❌ {tool_name}: {tool_result['error']}"
                        errors.append(error_text)
            else:
                logger.info("No tool calls requested by LLM")
        
        # Prepare final response
        if results:
            response_text = f"**Runbook Execution Results:**\n\n" + "\n\n".join(results)
        else:
            response_text = "No tools were executed."
        
        if errors:
            response_text += f"\n\n**Errors:**\n" + "\n".join(errors)
        
        return {
            "text": response_text,
            "channel": channel_id,
            "thread_ts": message_ts,
            "tool_calls": tool_calls,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"An unexpected error occurred in main: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}


if __name__ == "__main__":
    result = main()
    if result:
        print(json.dumps(result)) 