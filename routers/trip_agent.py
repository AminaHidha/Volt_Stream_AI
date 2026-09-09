from datetime import date
from fastapi import APIRouter, Header, HTTPException
from models.schemas import AgentBookingRequest, AgentBookingResponse
from services.trip_agent_service import run_trip_agent

router = APIRouter()


@router.post("/agent/trip", response_model=AgentBookingResponse)
def agent_trip(request: AgentBookingRequest, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    today_str = date.today().isoformat()

    reply_text, booking_result = run_trip_agent(
        user_message=request.message,
        token=authorization,
        today_date=today_str,
        history=request.history,
    )

    booking_id = None
    payment = None
    if booking_result:
        booking_data = booking_result.get("booking", {})
        booking_id = booking_data.get("booking_id") or booking_data.get("id")
        payment = booking_result.get("payment")

    return AgentBookingResponse(response=reply_text, booking_id=booking_id, payment=payment)