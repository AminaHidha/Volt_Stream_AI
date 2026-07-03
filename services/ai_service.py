import os
import requests
from dotenv import load_dotenv
from .rag_service import search_relevant_stations

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def ask_ai(message: str, history: list, stations: list = None, user: dict = None):

    print("=== ask_ai called ===")
    print("message:", message)

    # RAG Search
    try:
        rag_context = search_relevant_stations(message)
        print("rag_context length:", len(rag_context))
    except Exception as e:
        print("RAG ERROR:", e)
        rag_context = ""

    user_context = ""
    if user:
        user_context = f"Current user: {user.get('full_name', 'Driver')}"

    messages = [
        {
            "role": "system",
            "content": (
                "You are VoltStream AI. STRICT RULES: "
                "1. Maximum 2 sentences per response. "
                "2. Plain text only - no bullets, no markdown, no bold. "
                "3. Only answer EV charging questions. "
                "4. Be direct and short. "
                f"{user_context}\n\n"
                f"{rag_context}"
            )
        }
    ]

    recent_history = history[-4:] if len(history) > 4 else history
    messages.extend(recent_history)
    messages.append({"role": "user", "content": message})

    print("Calling OpenRouter API...")

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://voltstream.app",
                "X-Title": "VoltStream AI",
            },
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 60,
            },
            timeout=30,
        )

        print("OpenRouter status:", response.status_code)
        print("OpenRouter response:", response.text[:200])

        response.raise_for_status()
        result = response.json()
        ai_reply = result["choices"][0]["message"]["content"].strip()

        # Hard truncate
        sentences = [s.strip() for s in ai_reply.split('.') if s.strip()]
        if len(sentences) > 2:
            ai_reply = sentences[0] + '. ' + sentences[1] + '.'
        elif len(sentences) == 1:
            ai_reply = sentences[0] + '.'

        words = ai_reply.split()
        if len(words) > 40:
            ai_reply = ' '.join(words[:40]) + '.'

        print("Final reply:", ai_reply)
        return ai_reply

    except Exception as e:
        print("OPENROUTER ERROR:", str(e))
        return "Unable to connect to AI right now."