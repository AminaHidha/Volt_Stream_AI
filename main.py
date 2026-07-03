from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from routers.chat import router as chat_router
from database.database import Base, engine
from models.chat_model import ChatMessageDB
from services.rag_service import load_stations_to_vectordb

app = FastAPI(
    title="VoltStream AI Service",
    description="AI Chat microservice for VoltStream EV platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Load stations into ChromaDB on startup"""
    print("Loading stations into RAG vector database...")
    load_stations_to_vectordb()

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")

app.include_router(chat_router)
Base.metadata.create_all(bind=engine)