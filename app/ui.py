import os
import uuid
import requests
import streamlit as st
from typing import List, Dict

# ---------------------------
# Page setup
# ---------------------------
st.set_page_config(page_title="LangGraph Chat UI", page_icon="💬", layout="centered")

# ---------------------------
# Helpers
# ---------------------------
DEFAULT_API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
CHAT_ENDPOINT = "/chat"

def _init_state():
    if "api_base" not in st.session_state:
        st.session_state.api_base = DEFAULT_API_BASE
    if "memory_mode" not in st.session_state:
        st.session_state.memory_mode = "temporary"  # or "persistent"
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages: List[Dict[str, str]] = []  # [{"role": "user"|"assistant", "content": str}]


def new_chat():
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())


def clear_history():
    st.session_state.messages = []


def post_chat(message: str) -> Dict:
    """POST to FastAPI backend and return JSON response or raise."""
    url = st.session_state.api_base.rstrip("/") + CHAT_ENDPOINT
    payload = {
        "session_id": st.session_state.session_id,
        "message": message,
        "memory": st.session_state.memory_mode,
    }
    resp = requests.post(url, json=payload, timeout=60)
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail")
        except Exception:
            detail = resp.text
        raise RuntimeError(f"{resp.status_code} — {detail}")
    return resp.json()


# ---------------------------
# Sidebar
# ---------------------------
_init_state()

with st.sidebar:
    st.markdown("## ⚙️ Settings")

    st.text_input(
        "API base URL",
        key="api_base",
        help="Base URL for your FastAPI service (e.g. http://localhost:8000)",
    )

    st.selectbox(
        "Memory mode",
        options=["temporary", "persistent"],
        key="memory_mode",
        help=(
            "'temporary' uses in-memory state per session; 'persistent' uses SQLite checkpoints "
            "(requires the backend to be started with SqliteSaver)."
        ),
    )

    st.text_input("Session ID", key="session_id", help="Thread identifier used by LangGraph.")

    col1, col2 = st.columns(2)
    with col1:
        st.button("🆕 New chat", on_click=new_chat, use_container_width=True)
    with col2:
        st.button("🧹 Clear history", on_click=clear_history, use_container_width=True)

    st.markdown("---")
    st.caption(
        "This UI posts to **POST /chat** with {session_id, message, memory}. "
        "The backend returns {reply, mode, session_id, tokens_input, tokens_output}."
    )

# ---------------------------
# Header
# ---------------------------
st.title("💬 LangGraph Chat UI")
sub = (
    "Chat with your LangChain+LangGraph backend. Use the sidebar to choose memory mode and manage the session ID."
)
st.caption(sub)

# ---------------------------
# Render existing history
# ---------------------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])  # basic markdown rendering

# ---------------------------
# Chat input & send
# ---------------------------
if prompt := st.chat_input("Escribe tu mensaje…"):
    # Echo user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    try:
        with st.spinner("Consultando el backend…"):
            data = post_chat(prompt)
        reply = data.get("reply", "")
        mode = data.get("mode")
        tokens_in = data.get("tokens_input")
        tokens_out = data.get("tokens_output")

        # Show assistant message
        with st.chat_message("assistant"):
            st.markdown(reply or "(sin respuesta)")
            meta = []
            if mode:
                meta.append(f"modo: **{mode}**")
            if tokens_in is not None:
                meta.append(f"tokens_in: {tokens_in}")
            if tokens_out is not None:
                meta.append(f"tokens_out: {tokens_out}")
            if meta:
                st.caption(" · ".join(meta))

        st.session_state.messages.append({"role": "assistant", "content": reply})

    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"No se pudo contactar con el backend: {e}")
