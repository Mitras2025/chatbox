import os
import json
import time
from typing import List, Dict, Any, Optional

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOLS_REGISTRY, TOOLS_SPEC

load_dotenv()
st.set_page_config(page_title="Local ChatGPT", page_icon="💬", layout="wide")

# ---- Sidebar Controls ----
with st.sidebar:
    st.title("⚙️ Settings")
    env_api_key = os.getenv("OPENAI_API_KEY", "")
    if env_api_key:
        api_key = env_api_key
        st.success("Using API key from environment")
    else:
        api_key = st.text_input("OpenAI API Key", type="password")
    model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"])  # adjust to your access
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    streaming = st.toggle("Stream responses", value=True)
    system_prompt = st.text_area("System Prompt", value="You are a helpful, concise assistant.", height=120)
    st.markdown("---")
    st.caption("Upload a .txt or .md file to add context:")
    up = st.file_uploader("Context file", type=["txt", "md"], accept_multiple_files=False)
    extra_context = ""
    if up is not None:
        extra_context = up.read().decode("utf-8", errors="ignore")
        st.success("Context loaded.")

# ---- Init client ----
if not api_key:
    st.info("Enter your OpenAI API key in the sidebar to start.")
client = OpenAI(api_key=api_key) if api_key else None

# ---- Session State ----
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, Any]] = []
if "tool_messages" not in st.session_state:
    st.session_state.tool_messages: List[Dict[str, Any]] = []  # internal tool call chain

def reset_chat():
    st.session_state.messages = []
    st.session_state.tool_messages = []

# Header
col1, col2 = st.columns([1,4])
with col1:
    st.title("💬 Local ChatGPT")
with col2:
    if st.button("New Chat", use_container_width=True):
        reset_chat()
        st.experimental_rerun()

# ---- Chat render ----
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---- User input ----
user_input = st.chat_input("Type your message...")

def build_messages(user_text: str) -> List[Dict[str, str]]:
    msgs: List[Dict[str, str]] = []
    if system_prompt.strip():
        msgs.append({"role": "system", "content": system_prompt})
    if extra_context.strip():
        msgs.append({"role": "system", "content": f"Extra context from file:\n\n{extra_context[:6000]}"})
    msgs.extend(st.session_state.messages)
    msgs.append({"role": "user", "content": user_text})
    return msgs

def call_with_tools(msgs: List[Dict[str, str]]) -> Dict[str, Any]:
    """Handles a single round of tool-calling if present."""
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        tools=TOOLS_SPEC,
        tool_choice="auto",
        messages=msgs
    )
    choice = resp.choices[0]
    message = choice.message
    # If tool calls exist, run them and return tool_outputs + second model response
    if message.tool_calls:
        tool_responses = []
        # record the assistant tool_calls message
        msgs.append({"role": "assistant", "content": message.content or "", "tool_calls": [tc.model_dump() for tc in message.tool_calls]})
        for tc in message.tool_calls:
            name = tc.function.name
            args_json = tc.function.arguments
            try:
                args = json.loads(args_json) if args_json else {}
            except Exception:
                args = {"_raw": args_json}
            func = TOOLS_REGISTRY.get(name)
            if not func:
                result = json.dumps({"error": f"Tool '{name}' not implemented."})
            else:
                try:
                    result = func(**args)
                except TypeError as te:
                    result = json.dumps({"error": f"Bad args for {name}: {str(te)}"})
                except Exception as e:
                    result = json.dumps({"error": str(e)})
            # append tool result for follow-up
            msgs.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": name,
                "content": result
            })
            tool_responses.append((name, result))

        # second call: model sees tool outputs
        final = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=msgs
        )
        return {"message": final.choices[0].message, "tool_responses": tool_responses}
    else:
        return {"message": message, "tool_responses": []}

if user_input and client:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build and send to model
    msgs = build_messages(user_input)

    with st.chat_message("assistant"):
        if streaming:
            # Stream without tool-calls (streaming and tools together are more complex).
            # We'll do a quick attempt: if tools are needed, fall back to non-streaming path.
            tmp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                tools=TOOLS_SPEC,
                tool_choice="auto",
                messages=msgs,
                stream=True
            )
            collected = []
            need_tools = False
            placeholder = st.empty()
            text = ""
            for chunk in tmp:
                delta = chunk.choices[0].delta
                if delta.tool_calls:
                    # tools requested -> switch to non-streaming tool flow
                    need_tools = True
                    break
                if delta.content:
                    text += delta.content
                    placeholder.markdown(text)
            if need_tools:
                # fall back
                result = call_with_tools(msgs)
                final_msg = result["message"].content or "(no content)"
                st.markdown(final_msg)
                st.session_state.messages.append({"role": "assistant", "content": final_msg})
            else:
                st.session_state.messages.append({"role": "assistant", "content": text})
        else:
            result = call_with_tools(msgs)
            final_msg = result["message"].content or "(no content)"
            st.markdown(final_msg)
            st.session_state.messages.append({"role": "assistant", "content": final_msg})
