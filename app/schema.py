from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any

MemoryMode = Literal["temporary", "persistent"]

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="User/session thread ID")
    message: str = Field(..., description="User message")
    memory: MemoryMode = Field("persistent", description="Memory mode to use")
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    mode: MemoryMode
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    # You can add streaming support in the future if needed
