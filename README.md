# VoltStream — AI Service

A FastAPI microservice powering the **VoltStream AI Chat Assistant** — a Retrieval-Augmented Generation (RAG) system that answers EV charging questions using real station data.

Part of the VoltStream platform:
- 🔧 [Backend (Django)](https://github.com/AminaHidha/Volt_stream_repo)
- 💻 [Frontend (React)](https://github.com/AminaHidha/Volt_stream_Frontend)

---

## Overview

This service exposes a `/chat` endpoint that:
1. Retrieves relevant charging station data from a **ChromaDB vector store** based on the user's question (RAG)
2. Fetches live station and user data from the Django backend
3. Sends the enriched context + conversation history to an LLM via **OpenRouter**
4. Returns a short, focused, EV-related answer
5. Persists chat history in **SQLite**

---

## Tech Stack

- **Framework:** FastAPI
- **RAG / Vector Store:** LangChain + ChromaDB
- **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)
- **LLM Provider:** OpenRouter (`anthropic/claude-3-haiku`)
- **Database:** SQLite (chat history) via SQLAlchemy
- **Server:** Uvicorn (ASGI)

---

## Getting Started

### Prerequisites
- Python 3.11+
- The [VoltStream backend](https://github.com/AminaHidha/Volt_stream_repo) running on `localhost:8000` (used to load station data into the vector store, and to fetch live user/station context)
- An [OpenRouter](https://openrouter.ai/) API key

### Installation

```bash
git clone https://github.com/AminaHidha/Volt_Stream_AI.git
cd Volt_Stream_AI

python -m venv ai_env
ai_env\Scripts\Activate.ps1      # Windows PowerShell
# source ai_env/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
```

See `.env.example` for reference.

### Run the service

```bash
uvicorn main:app --reload --port 8001
```

On startup, the service automatically fetches all charging stations from the Django backend (`GET /api/stations/list/`) and loads them into the local ChromaDB vector store for retrieval.

The service will be available at **http://localhost:8001**, with interactive API docs at **http://localhost:8001/docs**.

### Run with Docker (optional)

```bash
docker compose up -d --build
```

> ⚠️ If you run both Docker and a local `uvicorn --reload` process on port 8001 at the same time, only one will actually receive requests — make sure to stop one before starting the other.

---

## Project Structure

```
├── main.py                    # FastAPI app entrypoint, startup event loads RAG data
├── database/
│   ├── database.py             # SQLAlchemy engine/session setup
│   └── deps.py                  # DB dependency injection
├── models/
│   ├── chat_model.py            # ChatMessageDB (SQLAlchemy)
│   ├── schemas.py               # Pydantic request/response models
│   └── vehicle_model.py
├── routers/
│   └── chat.py                  # POST /chat endpoint
├── services/
│   ├── ai_service.py            # Builds prompt, calls OpenRouter, formats response
│   ├── rag_service.py           # ChromaDB loading + similarity search
│   └── ev_service.py            # EV range estimation helper
├── chroma_db/                   # Persisted vector store (gitignored)
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## API

### `POST /chat`

**Request body:**
```json
{
  "user_id": "1",
  "message": "What's the closest fast charger?"
}
```

**Response:**
```json
{
  "response": "The nearest fast charger is at Station X, currently active.",
  "history": [
    { "role": "user", "content": "What's the closest fast charger?" },
    { "role": "assistant", "content": "The nearest fast charger is at Station X, currently active." }
  ]
}
```

The assistant is restricted to short (max 2 sentence), plain-text, EV-related answers.

---

## Notes

- Chat history is scoped per `user_id` and persisted in `voltstream.db` (SQLite).
- The vector store is rebuilt from live station data every time the service starts.
- If the Django backend is unreachable, the AI service still runs — it falls back to whatever data was last loaded into ChromaDB, and skips live user personalization.

---

*VoltStream EV Platform — Bridgeon Solutions — Amina Hidha — 2026*