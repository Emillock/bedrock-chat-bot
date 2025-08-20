import traceback

import requests
import streamlit as st

# from utils.ai_prompts import make_system_prompt, make_main_prompt
import ui_components.sidebar_components as sd_compents
from services.chat_service import _append_message_to_session, get_current_chat
from ui_components.main_components import display_tool_executions


def request_stream(prompt: str, modelName: str, api_url: str):
    """Send the raw uploaded file to FastAPI /predict."""
    try:
        data = {"prompt": prompt, "modelName": modelName}
        print(f"Sending request to API: {api_url} with data: {data}", flush=True)
        with requests.post(api_url, json=data, stream=True) as resp:
            # resp.iter_lines() yields chunks as they arrive
            for line in resp:
                if line.decode(encoding="utf-8", errors="ignore"):
                    # line is already a string if decode_unicode=True
                    # print(line)
                    yield line.decode(encoding="utf-8", errors="ignore")
        # FastAPI: 200 OK on success; 4xx/5xx otherwise with JSON detail
        # if resp.headers.get("content-type", "").startswith("application/json"):
        #     data = resp.json()
        # else:
        #     st.error(
        #         f"Unexpected response from API (status {resp.status_code}): {resp.text[:400]}"
        #     )
        #     return None

        if resp.status_code == 200:
            return data
        # Error path from FastAPI (HTTPException)
        detail = data.get("detail") if isinstance(data, dict) else None
        st.error(f"API Error {resp.status_code}: {detail or data}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error while calling API: {e}")
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
    if st.session_state.get("current_chat_id"):
        st.session_state["messages"] = get_current_chat(
            st.session_state["current_chat_id"]
        )
        for m in st.session_state["messages"]:
            with messages_container.chat_message(m["role"]):
                if "tool" in m and m["tool"]:
                    st.code(m["tool"], language="yaml")
                if "content" in m and m["content"]:
                    st.markdown(m["content"])

    # ------------------------------------------------------------------ Chat input
    user_text = st.chat_input(
        "Ask a question about Azercell.",
    )

    # ------------------------------------------------------------------ SideBar widgets
    # Main sidebar widgets
    sd_compents.create_sidebar_chat_buttons()
    sd_compents.create_provider_select_widget()

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
            print(
                "Running agent with user input:",
                user_text,
                "and model: ",
                st.session_state["params"]["model_id"],
                flush=True,
            )
            # system_prompt = make_system_prompt()
            # send_to_api(
            #     prompt=user_text,
            #     modelName=st.session_state['params']['model_id'],
            #     api_url=api_url
            # )
            # main_prompt = make_main_prompt(user_text)
            try:
                print(
                    "temperature:",
                    st.session_state["params"].get("temperature"),
                    flush=True,
                )
                print(
                    "max_tokens:",
                    st.session_state["params"].get("max_tokens"),
                    flush=True,
                )
                # If agent is available, use it

                response_stream = request_stream(
                    prompt=user_text,
                    modelName=st.session_state["params"]["model_name"],
                    api_url=api_url,
                )
                print("Response stream received:", response_stream, flush=True)
                with messages_container.chat_message("assistant"):
                    response = st.write_stream(response_stream)
                    response_dct = {"role": "assistant", "content": response}
            except Exception as e:
                response = f"⚠️ Something went wrong: {str(e)}"
                st.error(response)
                st.code(traceback.format_exc(), language="python")
                st.stop()
        # Add assistant message to chat history
        _append_message_to_session(response_dct)

    display_tool_executions()
