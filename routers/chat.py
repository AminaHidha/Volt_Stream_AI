from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse, ChatMessage
from services.ai_service import ask_ai

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        print(f"=== Chat request ===")
        print(f"User: {request.user_id}, Message: {request.message}")

        # Simple history — no DB for now
        history = []

        # Get AI response
        response = ask_ai(request.message, history)

        print(f"AI response: {response}")

        return ChatResponse(
            response=response,
            history=[
                ChatMessage(role="user", content=request.message),
                ChatMessage(role="assistant", content=response)
            ]
        )

    except Exception as e:
        import traceback
        print("=== ERROR ===")
        print(traceback.format_exc())
        raise