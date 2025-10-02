from __future__ import annotations
from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.messages import trim_messages
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from .config import settings
import requests
from urllib.parse import quote_plus
from langchain_core.messages import ToolMessage

# ---------- State ----------

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_input: str


# ---------- LLM factory ----------

def make_llm():
    return ChatOpenAI(model=settings.openai_model, temperature=0.2)

# ---------- Token-aware trimming ----------

trimmer = trim_messages(
    strategy="last",
    max_tokens=1200,
    token_counter=make_llm()  # model is used to count tokens accurately
)

# ---------- Tools ----------

@tool
def wiki_summary(topic: str, lang: str = "en") -> dict:
    """Get a short summary from Wikipedia for a topic (default lang=en)."""
    try:
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote_plus(topic)}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {"title": topic, "extract": "No summary found.", "url": ""}
        data = r.json()
        return {
            "title": data.get("title", topic),
            "extract": data.get("extract", ""),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
        }
    except Exception as e:
        return {"title": topic, "extract": f"Error: {e}", "url": ""}


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city using wttr.in ."""
    try:
        url = f"https://wttr.in/{quote_plus(city)}?format=3"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text.strip()
        return f"Could not fetch weather for {city}."
    except Exception as e:
        return f"Error: {e}"

TOOLS = [wiki_summary, get_weather]
TOOLS_NODE = ToolNode(TOOLS)  # Executes whichever tool the LLM requests

# ---------- Helper ----------

def user_requested_tools(text: str) -> bool:
    """Enable tools only via slash-commands: '/wiki ...' or '/weather ...'."""
    if not text:
        return False
    t = text.strip().lower()
    return t.startswith("/wiki") or t.startswith("/weather")

def should_append_user(history: List[BaseMessage], user_input: str) -> bool:
    """Append HumanMessage only on the first pass of the turn (avoid duplicates)."""
    if not history:
        return True
    last = history[-1]
    return not (isinstance(last, HumanMessage) and getattr(last, "content", None) == user_input)

def last_message_is_tool(history: List[BaseMessage]) -> bool:
    """True if we just ran a tool in this turn (prevents immediate re-binding)."""
    return bool(history) and isinstance(history[-1], ToolMessage)


# ---------- Nodes ----------

def respond_node(state: ChatState):
    # 1) Build the base prompt + trimmed conversation history
    system = SystemMessage(content=(settings.system_prompt or ""))
    history = state.get("messages", [])
    trimmed = trimmer.invoke([system, *history])

    # 2) Decide tool usage for THIS turn (avoid loops)
    wants_tools = user_requested_tools(state["user_input"])
    just_ran_tool = last_message_is_tool(history)

    # Allow tools only if the user asked AND we have NOT just run a tool
    if wants_tools and not just_ran_tool:
        llm = make_llm().bind_tools(TOOLS, tool_choice="auto")
    else:
        llm = make_llm()  # disable tools to force the model to produce a final answer

    # 3) Build messages_in:
    #    - append the HumanMessage only on the first pass of this turn
    msgs_in = trimmed[:]
    append_user = should_append_user(history, state["user_input"])
    if append_user:
        user_msg = HumanMessage(state["user_input"])
        msgs_in.append(user_msg)
    else:
        user_msg = None  # we won't persist it again

    # 4) Invoke the model
    ai_msg: AIMessage = llm.invoke(msgs_in)

    # 5) Persist messages:
    #    - persist HumanMessage only if we appended it this pass
    out = []
    if user_msg is not None:
        out.append(user_msg)
    out.append(ai_msg)
    return {"messages": out}

# ---------- Routing (guards/conditions) ----------

def needs_tools(state: ChatState) -> str:
    """
    Decide next hop after `respond`:
      - If the last AIMessage contains tool_calls -> go to "tools"
      - Otherwise -> finish (END)
    """
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, AIMessage):
            if getattr(msg, "tool_calls", None):
                return "tools"
            break
    return "end"

# ---------- Graph ----------

def build_graph(checkpointer=None):
    """
    If no checkpointer is provided, use in-memory MemorySaver (temporary).
    For persistent mode, pass a SqliteSaver instance (already entered).
    """
    graph = StateGraph(ChatState)

    # Nodes
    graph.add_node("respond", respond_node)
    graph.add_node("tools", TOOLS_NODE)

    # Define the initial node: conversations will start with 'respond'
    graph.set_entry_point("respond")

    # Conditional edges:
    # respond -> tools | END (based on whether the model asked to call a tool)
    graph.add_conditional_edges("respond", needs_tools, {"tools": "tools", "end": END}) # Dict: string returned from function needs_tools and its value (tools node or END)

    # After running a tool, return to 'respond' so the LLM can read the tool result
    # and craft the final answer.
    graph.add_edge("tools", "respond")

    # Default to in-memory temporary memory unless a checkpointer is provided
    return graph.compile(checkpointer=checkpointer or MemorySaver())