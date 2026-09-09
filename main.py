from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from routers.chat import router as chat_router
from routers.booking_agent import router as booking_agent_router
from routers.trip_agent import router as trip_agent_router          # ADD THIS
from database.database import Base, engine
from models.chat_model import ChatMessageDB

app = FastAPI(
    title="VoltStream AI Service",
    description="AI Chat microservice for VoltStream EV platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")

app.include_router(chat_router)
app.include_router(booking_agent_router)
app.include_router(trip_agent_router)                                # ADD THIS
Base.metadata.create_all(bind=engine)