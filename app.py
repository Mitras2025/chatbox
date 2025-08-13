import os
from openai import OpenAI
import streamlit as st

# ---- Page config ----
st.set_page_config(page_title="Local ChatGPT", page_icon="🤖", layout="wide")

# ---- Sidebar ----
st.sidebar.title("⚙️ Settings")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

client = OpenAI(api_key=api_key) if api_key else None

# ---- Session state initialization ----
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---- Helper: Reset chat ----


def reset_chat():
    st.session_state.messages = []


# ---- Header with buttons ----
col1, col2 = st.columns([0.85, 0.15])

with col1:
    st.title("💬 Local ChatGPT")

with col2:
    if st.button("New Chat", use_container_width=True):
        reset_chat()
        st.rerun()

# ---- Chat render ----
for m in st.session_state.messages:
    role = m.get("role", "user")
    content = m.get("content", "")
    if role not in ("user", "assistant", "system"):
        role = "user"
    with st.chat_message(role):
        st.markdown(content)

# ---- User input ----
if prompt := st.chat_input("Type your message"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not client:
        st.warning("Please enter your OpenAI API key in the sidebar.")
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ API Error: {e}"

        st.session_state.messages.append(
            {"role": "assistant", "content": reply})
    st.rerun()
