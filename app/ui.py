import os
import uuid
import json
import requests
import streamlit as st
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, List, Tuple

# =========================
# Page setup
# =========================
st.set_page_config(page_title="LangGraph Chat UI", page_icon="💬", layout="wide")

# =========================
# Constants
# =========================
DEFAULT_API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
CHAT_ENDPOINT = "/chat"
BADGE_PERSISTENT = "🔒"
BADGE_TEMP = "⚡"
DATA_FILE = Path(__file__).resolve().parents[1] / ".data/ui_chats.json"
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

# =========================
# Helpers
# =========================
def now_iso() -> str:
    return datetime.now(UTC).isoformat()

def post_chat(api_base: str, session_id: str, memory_mode: str, message: str) -> Dict[str, Any]:
    url = api_base.rstrip("/") + CHAT_ENDPOINT
    payload = {"session_id": session_id, "message": message, "memory": memory_mode}
    resp = requests.post(url, json=payload, timeout=60)
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail")
        except Exception:
            detail = resp.text
        raise RuntimeError(f"{resp.status_code} — {detail}")
    return resp.json()

def badge(memory: str) -> str:
    return BADGE_PERSISTENT if memory == "persistent" else BADGE_TEMP

# --- Title helpers ---
def is_default_title(title: str) -> bool:
    t = (title or "").strip().lower()
    return (t == "new chat") or t.startswith("chat ")

def make_title_from_user(text: str, max_len: int = 40) -> str:
    """Heuristic title from first user message (no LLM)."""
    if not text:
        return "New chat"
    s = text.strip().splitlines()[0]
    for lead in ["hola", "buenas", "hello", "hi", "hey"]:
        if s.lower().startswith(lead + " "):
            s = s[len(lead)+1:].strip()
    s = s.strip().rstrip(".!?,;:")
    if len(s) > max_len:
        cut = s[:max_len]
        s = cut.rsplit(" ", 1)[0] + "…"
    return s[:1].upper() + s[1:]

def next_numbered_title() -> str:
    st.session_state.setdefault("chat_counter", 1)
    n = st.session_state["chat_counter"]
    st.session_state["chat_counter"] = n + 1
    return f"Chat {n}"

# =========================
# Persistence helpers
# =========================
def save_permanent_chats(chats: Dict[str, Dict[str, Any]]):
    """Write the whole permanent-chats dict to disk."""
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)

def load_permanent_chats() -> Dict[str, Dict[str, Any]]:
    """Read and normalize the saved dict from disk."""
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            if not isinstance(raw, dict):
                return {}
            changed = False
            for cid, chat in list(raw.items()):
                if not isinstance(chat, dict):
                    del raw[cid]; changed = True; continue
                if "title" not in chat:
                    chat["title"] = "Persistent chat"; changed = True
                if "session_id" not in chat:
                    chat["session_id"] = str(uuid.uuid4()); changed = True
                if "messages" not in chat or not isinstance(chat.get("messages"), list):
                    chat["messages"] = []; changed = True
                if "created_at" not in chat:
                    chat["created_at"] = now_iso(); changed = True
                if "updated_at" not in chat:
                    chat["updated_at"] = now_iso(); changed = True
            if changed:
                save_permanent_chats(raw)
            return raw
        except Exception:
            return {}
    return {}

# =========================
# State
# =========================
def init_state():
    ss = st.session_state
    ss.setdefault("api_base", DEFAULT_API_BASE)
    ss.setdefault("permanent_chats", load_permanent_chats())
    ss.setdefault("temp_chat", new_temp_chat_obj())
    ss.setdefault("active_is_temp", False)
    ss.setdefault("active_chat_id", None)
    ss.setdefault("chat_counter", 1)  # for numbered default titles

    # Choose initial active chat
    if ss["active_chat_id"] is None and not ss["active_is_temp"]:
        if ss["permanent_chats"]:
            pid = sorted(ss["permanent_chats"].items(), key=lambda kv: kv[1]["updated_at"], reverse=True)[0][0]
            ss["active_chat_id"] = pid
        else:
            create_permanent_chat()  # numbered default

def new_temp_chat_obj() -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "title": "Temporary chat",
        "session_id": str(uuid.uuid4()),
        "messages": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

def create_permanent_chat(title: str | None = None):
    if st.session_state.get("active_is_temp"):
        st.session_state["temp_chat"] = new_temp_chat_obj()
    st.session_state["active_is_temp"] = False

    if not title:
        title = next_numbered_title()  # numbered default

    cid = str(uuid.uuid4())
    st.session_state["permanent_chats"][cid] = {
        "title": title,
        "session_id": str(uuid.uuid4()),
        "messages": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    save_permanent_chats(st.session_state["permanent_chats"])
    st.session_state["active_chat_id"] = cid

def activate_permanent_chat(chat_id: str):
    if st.session_state.get("active_is_temp"):
        st.session_state["temp_chat"] = new_temp_chat_obj()
        st.session_state["active_is_temp"] = False
    st.session_state["active_chat_id"] = chat_id

def start_new_temporary_chat():
    st.session_state["temp_chat"] = new_temp_chat_obj()
    st.session_state["active_is_temp"] = True
    st.session_state["active_chat_id"] = None

def delete_permanent_chat(chat_id: str):
    chats = st.session_state["permanent_chats"]
    if chat_id in chats:
        del chats[chat_id]
        save_permanent_chats(chats)
        if chats:
            new_active = sorted(chats.items(), key=lambda kv: kv[1]["updated_at"], reverse=True)[0][0]
            st.session_state["active_chat_id"] = new_active
            st.session_state["active_is_temp"] = False
        else:
            start_new_temporary_chat()

# =========================
# Init
# =========================
init_state()

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown("### 💬 Chats")

    # Only "New permanent"
    if st.button("🔒 New permanent", use_container_width=True):
        create_permanent_chat()  # no fixed title

    st.markdown("---")

    # Ephemeral temp chat (optional quick access)
    t = st.session_state["temp_chat"]
    is_active_temp = st.session_state["active_is_temp"]
    if st.button(f"{BADGE_TEMP} {t['title']}", type=("primary" if is_active_temp else "secondary"), use_container_width=True):
        start_new_temporary_chat()

    st.markdown("---")
    st.caption("Saved (permanent)")
    chats = st.session_state["permanent_chats"]
    items: List[Tuple[str, Dict[str, Any]]] = sorted(chats.items(), key=lambda kv: kv[1]["updated_at"], reverse=True)
    if not items:
        st.write("No permanent chats yet.")
    for cid, chat in items:
        is_active = (not st.session_state["active_is_temp"]) and (st.session_state["active_chat_id"] == cid)
        label = f"{BADGE_PERSISTENT} {chat['title']}"
        if st.button(label, key=f"open_{cid}", type=("primary" if is_active else "secondary"), use_container_width=True):
            activate_permanent_chat(cid)

    st.markdown("---")
    if (not st.session_state["active_is_temp"]) and (st.session_state["active_chat_id"] in st.session_state["permanent_chats"]):
        active_id = st.session_state["active_chat_id"]
        if st.button("🗑️ Delete current chat", use_container_width=True):
            delete_permanent_chat(active_id)

# =========================
# Main chat window
# =========================
st.title("💬 LangGraph Chat UI")

if st.session_state["active_is_temp"]:
    chat = st.session_state["temp_chat"]
    mode = "temporary"
else:
    chat = st.session_state["permanent_chats"][st.session_state["active_chat_id"]]
    mode = "persistent"

st.caption(f"{badge(mode)} **{chat['title']}** · session_id: `{chat['session_id']}` · mode: **{mode}**")

# Render history (robust)
for m in chat.get("messages", []):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Input
if prompt := st.chat_input("Type your message..."):
    chat.setdefault("messages", []).append({"role": "user", "content": prompt})
    chat["updated_at"] = now_iso()
    with st.chat_message("user"):
        st.markdown(prompt)
    try:
        with st.spinner("Contacting backend..."):
            data = post_chat(
                api_base=st.session_state["api_base"],
                session_id=chat["session_id"],
                memory_mode=mode,
                message=prompt,
            )
        reply = data.get("reply", "")
        with st.chat_message("assistant"):
            st.markdown(reply or "(no reply)")
        chat.setdefault("messages", []).append({"role": "assistant", "content": reply})
        chat["updated_at"] = now_iso()

        # Persist changes
        if mode == "persistent":
            # Auto-rename the first time if the title is generic
            if is_default_title(chat.get("title", "")):
                chat["title"] = make_title_from_user(prompt)
            save_permanent_chats(st.session_state["permanent_chats"])

    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"Could not reach backend: {e}")