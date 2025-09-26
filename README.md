# Chatbot Backend — LangChain v0.3 + LCEL + LangGraph (Temporary & Persistent Memory)

This backend provides a **FastAPI** service implementing a chatbot with:

- **LCEL** for composable chains.  
- **LangGraph** for orchestration.  
- **Temporary memory** (`MemorySaver`) and **persistent memory** (`SqliteSaver`).  
- **Message trimming** with `trim_messages` to keep context window under control.  

---

## Requirements

- Python 3.10+  
- One of the following package managers:  
  - [`uv`](https://docs.astral.sh/uv/) (recommended, fastest)  
  - [Poetry](https://python-poetry.org/)  
  - Standard `pip`  

- An API key for your preferred LLM provider (e.g., OpenAI).  
- (Optional) A `.data/` directory for SQLite persistence.

---

## Installation

### Option 1 — Using **uv** (recommended)

# Clone the project
git clone https://github.com/your-org/chatbot-backend.git
cd chatbot-backend

# Install all dependencies (creates and manages virtualenv automatically)
uv sync

# Prepare environment variables and SQLite folder
cp .env.example .env
mkdir -p .data 

### Option 2 — Using **poetry**
git clone https://github.com/your-org/chatbot-backend.git
cd chatbot-backend

poetry install
cp .env.example .env
mkdir -p .data

### Option 3 — Using pip (classic)
git clone https://github.com/your-org/chatbot-backend.git
cd chatbot-backend

python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
cp .env.example .env
mkdir -p .data

## Architecture Notes
•	Persistence (recommended):
        Current LangChain docs suggest using LangGraph checkpointers (e.g. SqliteSaver, PostgresSaver) for memory, instead of older memory APIs.
•	Temporary vs Persistent:
•	MemorySaver: in-memory (RAM), volatile, resets on restart.
•	SqliteSaver: saves to SQLite for durability across restarts.
•	Scalability:
        For distributed or production deployments, prefer langgraph-checkpoint-postgres for persistence.
•	Context control:
        trim_messages ensures that only the relevant portion of the conversation is sent to the LLM.

## Execution
uv run uvicorn app.main:app --reload --port 8000
poetry run uvicorn app.main:app --reload --port 8000
uvicorn app.main:app --reload --port 8000