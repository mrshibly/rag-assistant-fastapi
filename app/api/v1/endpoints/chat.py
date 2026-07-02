from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import process_chat
from app.services.memory import memory_service

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get a response with RAG, tool calling, and memory."""
    return await process_chat(request)


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation memory for a session."""
    memory_service.clear(session_id)
    return {"detail": f"Session '{session_id}' cleared."}

