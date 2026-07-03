from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import requests
import os

from models.schemas import ChatRequest, ChatResponse, ChatMessage
from models.chat_model import ChatMessageDB
from database.deps import get_db
from services.ai_service import ask_ai

router = APIRouter()


def get_stations():
    """Fetch stations from Django backend"""
    try:
        response = requests.get(
            "http://localhost:8000/api/stations/",
            timeout=5
        )
        print(f"Stations response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # Handle both paginated and non-paginated responses
            if isinstance(data, dict) and "results" in data:
                return data["results"]
            return data
        return []
    except Exception as e:
        print(f"Stations fetch error: {e}")
        return []


def get_user(user_id: str):
    """Fetch user from Django backend"""
    try:
        response = requests.get(
            f"http://localhost:8000/api/users/{user_id}/",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        print(f"User fetch error: {e}")
        return {}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):

    print(f"=== Chat request from user {request.user_id} ===")
    print(f"Message: {request.message}")

    # 1. Get history from DB
    history_db = db.query(ChatMessageDB)\
        .filter(ChatMessageDB.user_id == request.user_id)\
        .all()

    history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_db
    ]

    print(f"History length: {len(history)}")

    # 2. Get real stations and user data
    stations = get_stations()
    user = get_user(request.user_id)

    print(f"Stations fetched: {len(stations)}")

    # 3. Get AI response with real data
    response = ask_ai(request.message, history, stations=stations, user=user)

    print(f"AI response: {response}")

    # 4. Save user message
    db.add(ChatMessageDB(
        user_id=request.user_id,
        role="user",
        content=request.message
    ))

    # 5. Save assistant message
    db.add(ChatMessageDB(
        user_id=request.user_id,
        role="assistant",
        content=response
    ))

    db.commit()

    # 6. Return response + history
    updated_history = history + [
        {"role": "user", "content": request.message},
        {"role": "assistant", "content": response}
    ]

    return ChatResponse(
        response=response,
        history=[ChatMessage(**msg) for msg in updated_history]
    )