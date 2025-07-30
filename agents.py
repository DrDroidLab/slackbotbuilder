from openai import OpenAI
from slack_credentials_manager import credentials_manager
import json
from mcp_servers.mcp_utils import execute_tool
import tiktoken
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def count_tokens(text, model="gpt-4"):  # Helper function for token count
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception as e:
        logger.error(f"[TokenCount] Error: {e}")
        return -1

def agent_with_tools(messages, available_tools):
    agent_chat = []
    ndjson_events = []
    client = OpenAI(api_key=credentials_manager.get_openai_api_key())
    openai_tools = [{"type": "function", "function": tool} for tool in available_tools]
    # Non-streaming OpenAI call
    if len(openai_tools) > 0:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )
    else:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages
        )

    choice = response.choices[0]
    message = choice.message
    assistant_response_content = message.content or ""
    tool_calls = message.tool_calls or []

    # Emit assistant text
    if tool_calls:
        assistant_msg = {"role": "assistant","content": assistant_response_content,"tool_calls": tool_calls}
        ndjson_events.append({'type': 'chat_text','content': assistant_response_content})
        messages.append(assistant_msg)
        for index, tool_call in enumerate(tool_calls):
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments
            tool_call_id = tool_call.id

            if type(tool_args) == str:
                try:
                    tool_args = json.loads(tool_args)
                except:
                    tool_args = {}
            result_content = execute_tool(tool_name, tool_args)
            tool_msg = {"role": "tool","content": "Tool " + tool_name + " Tool Arguments: " + str(tool_args) + " result: " + str(result_content),"tool_call_id": tool_call_id}
            messages.append(tool_msg)
            ndjson_events.append({'type': 'tool_result','tool_name': tool_name,'tool_config': tool_args,'tool_result': result_content,'tool_call_id': tool_call_id})
        return ndjson_events + agent_with_tools(messages, available_tools)
    else:
        ndjson_events.append({'type': 'chat_text','content': assistant_response_content})
    return ndjson_events

def log_analyser_agent(logs_data,messages):
    logger.info("logs are short. Giving agent logs directly.")
    count_logs_tokens = count_tokens(str(logs_data))
    if count_logs_tokens>20000:
        # truncate and send
        truncated_logs_data = str(logs_data)[:20000]
        messages.append({"role": "user", "content": "Logs start here\n\n" + str(truncated_logs_data)})
    else:
        messages.append({"role": "user", "content": "Logs start here\n\n" + str(logs_data)})
    agent_chat = agent_with_tools(messages,[])
    return agent_chat
    #TODO -- add tool functions to analyse logs
    # count_logs_tokens = count_tokens(logs_data)
    # if len(count_logs_tokens)>20000:
    #     print("logs too long. Giving agent functions to analyse logs.")
        
    #     # logs are too long, give agent functions to 
    #     # (a) eyeball_logs(order_by=['desc','random'],limit=1000) 
    #     # (b) filter_logs(type=['grep','regex'],query,limit=1000)
    #     # (c) see_in_context(query,limit=1000)
    #     # (d) aggregate_counts()

    # else:

    
#async def agent_with_manual_approval_tools(messages, available_tools):
# todo