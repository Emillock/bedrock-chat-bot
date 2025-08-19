import os
import datetime
import requests
import streamlit as st
from langchain_core.messages import HumanMessage, ToolMessage
from services.ai_service import get_response_stream
from services.mcp_service import run_agent
from services.chat_service import get_current_chat, _append_message_to_session
from utils.async_helpers import run_async
from utils.ai_prompts import make_system_prompt, make_main_prompt
import ui_components.sidebar_components as sd_compents
from ui_components.main_components import display_tool_executions
from config import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE
import traceback


def send_to_api(prompt: str, modelName: str, api_url: str) -> dict | None:
    """Send the raw uploaded file to FastAPI /predict."""
    try:
        data={"prompt": prompt, "modelName": modelName}
        print(f"Sending request to API: {api_url} with data: {data}", flush=True)
        resp = requests.post(
            api_url, json=data, timeout=60)
        # FastAPI: 200 OK on success; 4xx/5xx otherwise with JSON detail
        if resp.headers.get("content-type", "").startswith("application/json"):
            data = resp.json()
        else:
            st.error(
                f"Unexpected response from API (status {resp.status_code}): {resp.text[:400]}"
            )
            return None

        if resp.status_code == 200:
            return data
        # Error path from FastAPI (HTTPException)
        detail = data.get("detail") if isinstance(data, dict) else None
        st.error(f"API Error {resp.status_code}: {detail or data}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error while calling API: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def main():
    with st.sidebar:
        st.subheader("Chat History")
    sd_compents.create_history_chat_container()

# ------------------------------------------------------------------ Chat Part
    # Main chat interface
    st.header("Chat with Agent")
    messages_container = st.container(border=True, height=600)
# ------------------------------------------------------------------ Chat history
    # Re-render previous messages
    if st.session_state.get('current_chat_id'):
        st.session_state["messages"] = get_current_chat(
            st.session_state['current_chat_id'])
        for m in st.session_state["messages"]:
            with messages_container.chat_message(m["role"]):
                if "tool" in m and m["tool"]:
                    st.code(m["tool"], language='yaml')
                if "content" in m and m["content"]:
                    st.markdown(m["content"])

# ------------------------------------------------------------------ Chat input
    user_text = st.chat_input("Ask a question or explore available MCP tools")

# ------------------------------------------------------------------ SideBar widgets
    # Main sidebar widgets
    sd_compents.create_sidebar_chat_buttons()
    sd_compents.create_provider_select_widget()
    sd_compents.create_advanced_configuration_widget()
    sd_compents.create_mcp_connection_widget()
    sd_compents.create_mcp_tools_widget()

# ------------------------------------------------------------------ Main Logic
    if user_text is None:  # nothing submitted yet
        st.stop()


# ------------------------------------------------------------------ handle question (if any text)
    api_url = "http://backend:8000/generate"
    if user_text:
        user_text_dct = {"role": "user", "content": user_text}
        _append_message_to_session(user_text_dct)
        with messages_container.chat_message("user"):
            st.markdown(user_text)

        with st.spinner("Thinking…", show_time=True):
            print("Running agent with user input:", user_text, "and model: ",
                  st.session_state['params']['model_id'], flush=True)
            system_prompt = make_system_prompt()
            send_to_api(
                prompt=user_text,
                modelName=st.session_state['params']['model_id'],
                api_url=api_url
            )
            main_prompt = make_main_prompt(user_text)
            try:
                # If agent is available, use it
                if st.session_state.agent:
                    response = run_async(
                        run_agent(st.session_state.agent, user_text))
                    tool_output = None
                    # Extract tool executions if available
                    if "messages" in response:
                        for msg in response["messages"]:
                            # Look for AIMessage with tool calls
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    # Find corresponding ToolMessage
                                    tool_output = next(
                                        (m.content for m in response["messages"]
                                            if isinstance(m, ToolMessage) and
                                            m.tool_call_id == tool_call['id']),
                                        None
                                    )
                                    if tool_output:
                                        st.session_state.tool_executions.append({
                                            "tool_name": tool_call['name'],
                                            "input": tool_call['args'],
                                            "output": tool_output,
                                            "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        })
                    # Extract and display the response
                    output = ""
                    tool_count = 0
                    if "messages" in response:
                        for msg in response["messages"]:
                            if isinstance(msg, HumanMessage):
                                continue  # Skip human messages
                            elif hasattr(msg, 'name') and msg.name:  # ToolMessage
                                tool_count += 1
                                with messages_container.chat_message("assistant"):
                                    tool_message = f"**ToolMessage - {tool_count} ({msg.name}):** \n" + \
                                        msg.content
                                    st.code(tool_message, language='yaml')
                                    _append_message_to_session(
                                        {'role': 'assistant', 'tool': tool_message, })
                            else:  # AIMessage
                                if hasattr(msg, "content") and msg.content:
                                    with messages_container.chat_message("assistant"):
                                        output = str(msg.content)
                                        st.markdown(output)
                    response_dct = {"role": "assistant", "content": output}
                # Fall back to regular stream response if agent not available
                else:
                    st.warning("You are not connect to MCP servers!")
                    response_stream = get_response_stream(
                        main_prompt,
                        llm_provider=st.session_state['params']['model_id'],
                        system=system_prompt,
                        temperature=st.session_state['params'].get(
                            'temperature', DEFAULT_TEMPERATURE),
                        max_tokens=st.session_state['params'].get(
                            'max_tokens', DEFAULT_MAX_TOKENS),
                    )
                    with messages_container.chat_message("assistant"):
                        response = st.write_stream(response_stream)
                        response_dct = {
                            "role": "assistant", "content": response}
            except Exception as e:
                response = f"⚠️ Something went wrong: {str(e)}"
                st.error(response)
                st.code(traceback.format_exc(), language="python")
                st.stop()
        # Add assistant message to chat history
        _append_message_to_session(response_dct)

    display_tool_executions()
