# 💬 LangGraph Memory Chatbot

A production-ready conversational AI backend built with **LangChain**, **LangGraph**, and **FastAPI**. Features dual memory modes (temporary/persistent), tool integration, and a beautiful Streamlit UI.

## ✨ Features

- 🔄 **Dual Memory Modes**
  - **Temporary**: In-memory conversations (MemorySaver)
  - **Persistent**: SQLite-backed conversation history
- 🛠️ **Tool Integration**
  - Wikipedia summaries (`/wiki <topic>`)
  - Weather information (`/weather <city>`)
- 🎯 **Smart Context Management**
  - Automatic message trimming (1200 tokens)
  - Prevents context overflow
- 🚀 **FastAPI Backend**
  - RESTful API with Pydantic validation
  - Session-based conversation management
- 🎨 **Streamlit UI**
  - Clean, intuitive chat interface
  - Real-time configuration
  - Session management controls

## 🏗️ Architecture

```
┌─────────────┐
│ Streamlit UI│
└──────┬──────┘
       │ HTTP POST
       ▼
┌─────────────┐
│  FastAPI    │
│   Backend   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│      LangGraph          │
│  ┌─────────────────┐    │
│  │   respond_node  │    │
│  └────────┬────────┘    │
│           │             │
│    ┌──────▼──────┐      │
│    │ needs_tools?│      │
│    └──────┬──────┘      │
│           │             │
│    ┌──────▼──────┐      │
│    │ tools_node  │      │
│    └─────────────┘      │
└─────────────────────────┘
       │
       ▼
┌─────────────┐
│  OpenAI API │
└─────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.9+
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/JaimeLucena/langgraph-memory-chatbot.git
   cd langgraph-memory-chatbot
   ```

2. **Create virtual environment (if you are not using uv)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Configure environment**
   
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   SQLITE_PATH=data/memory.sqlite
   SYSTEM_PROMPT=You are a helpful and concise assistant.
   ```

5. **Create data directory**
   ```bash
   mkdir -p data
   ```

## 🚀 Usage

### Start the Backend

```bash
uv run uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Start the UI

In a separate terminal:

```bash
uv run streamlit run app/ui.py
```

The UI will open automatically in your browser at `http://localhost:8501`

## 🔧 API Reference

### POST `/chat`

Send a message and receive a response.

**Request Body:**
```json
{
  "session_id": "unique-session-identifier",
  "message": "Hello, how are you?",
  "memory": "persistent",
  "metadata": {}
}
```

**Response:**
```json
{
  "session_id": "unique-session-identifier",
  "reply": "I'm doing well, thank you! How can I help you today?",
  "mode": "persistent",
  "tokens_input": null,
  "tokens_output": null
}
```

### Tool Commands

Activate tools by using slash commands:

- **Wikipedia**: `/wiki Python programming`
- **Weather**: `/weather Madrid`

## 📁 Project Structure

```
langgraph-memory-chatbot/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration & environment variables
│   ├── schema.py          # Pydantic models
│   ├── graph.py           # LangGraph workflow definition
│   ├── main.py            # FastAPI application
│   └── ui.py              # Streamlit interface
├── data/                  # Data directory (created automatically)
│   └── memory.sqlite      # Persistent conversation storage
├── venv/                  # Virtual environment (not in git)
├── .env                   # Environment variables (not in git)
├── .gitignore
├── pyproject.toml         # Project configuration
├── README.md
└── uv.lock                # Dependency lock file
```

## 🛠️ Configuration

All configuration is managed through environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_MODEL` | Model to use | `gpt-4o-mini` |
| `SQLITE_PATH` | Path to SQLite database | `data/memory.sqlite` |
| `SYSTEM_PROMPT` | System prompt for the AI | Default assistant prompt |

## 🧪 Testing

### Test the API directly

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "message": "Hello!",
    "memory": "temporary"
  }'
```

### Test Wikipedia tool

In the UI or via API:
```
/wiki Albert Einstein
```

### Test Weather tool

```
/weather London
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - Framework for LLM applications
- [LangGraph](https://github.com/langchain-ai/langgraph) - Graph-based orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Streamlit](https://streamlit.io/) - App framework for ML/AI

## 📧 Contact

Jaime Lucena - jaimelucena93@gmail.com

Project Link: [https://github.com/JaimeLucena/langgraph-memory-chatbot](https://github.com/JaimeLucena/langgraph-memory-chatbot)

---

⭐ If you find this project useful, please consider giving it a star!