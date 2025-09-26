from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from langgraph.checkpoint.sqlite import SqliteSaver

from .schema import ChatRequest, ChatResponse
from .graph import build_graph
from .config import settings

# We'll create both graphs during app startup and keep the SQLite context open
graphs = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # temporary (RAM) graph
    graphs["temporary"] = build_graph()

    # persistent (SQLite) graph — OPEN the context manager and keep it alive
    with SqliteSaver.from_conn_string(settings.sqlite_path) as sqlite_saver:
        graphs["persistent"] = build_graph(checkpointer=sqlite_saver)
        yield
    # context closes automatically on shutdown

app = FastAPI(title="Chatbot Backend (LangChain+LangGraph)", lifespan=lifespan)

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    mode = req.memory
    if mode not in graphs:
        raise HTTPException(status_code=400, detail="memory must be 'temporary' or 'persistent'")

    config = {"configurable": {"thread_id": req.session_id}}
    result = graphs[mode].invoke({"user_input": req.message, "messages": []}, config=config)

    messages = result.get("messages", [])
    reply = messages[-1].content if messages else ""

    return JSONResponse(
        ChatResponse(
            session_id=req.session_id,
            reply=reply,
            mode=mode,
            tokens_input=None,
            tokens_output=None,
        ).model_dump()
    )