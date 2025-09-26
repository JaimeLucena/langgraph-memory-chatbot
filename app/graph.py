from __future__ import annotations
from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.messages import trim_messages
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from .config import settings

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_input: str

def make_llm():
    return ChatOpenAI(model=settings.openai_model, temperature=0.2)

# token-aware trimming
trimmer = trim_messages(
    strategy="last",
    max_tokens=1200,
    token_counter=make_llm()  # ok to pass the llm; LC will use it for counting
)

@tool
def echo_upper(text: str) -> str:
    """Returns the text in UPPERCASE (demo tool)."""
    return text.upper()

def route_tools(state: ChatState):
    content = state["user_input"].strip()
    if content.startswith("/upper "):
        return "use_tools"
    return "respond"

def use_tools_node(state: ChatState):
    arg = state["user_input"].replace("/upper ", "", 1)
    result = echo_upper.invoke({"text": arg})
    return {"messages": [AIMessage(content=f"(tool: echo_upper) {result}")]}

def respond_node(state: ChatState):
    llm = make_llm()
    system = SystemMessage(content=settings.system_prompt)
    history = state.get("messages", [])

    trimmed = trimmer.invoke([system, *history])  # -> List[BaseMessage]

    messages_in = trimmed + [HumanMessage(state["user_input"])]

    ai_msg: AIMessage = llm.invoke(messages_in)

    return {"messages": [ai_msg]}

def build_graph(checkpointer=None):
    """
    If no checkpointer is provided, use in-memory MemorySaver (temporary).
    For persistent mode, pass a SqliteSaver instance (already entered).
    """
    graph = StateGraph(ChatState)
    graph.add_node("use_tools", use_tools_node)
    graph.add_node("respond", respond_node)
    graph.set_entry_point("respond")
    graph.add_conditional_edges("respond", route_tools, {"use_tools": "use_tools", "respond": END})
    graph.add_edge("use_tools", END)

    return graph.compile(checkpointer=checkpointer or MemorySaver())