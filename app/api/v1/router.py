from fastapi import APIRouter

from app.api.v1.endpoints import chat, ingest

router = APIRouter(prefix="/api/v1")
router.include_router(ingest.router, tags=["Ingestion"])
router.include_router(chat.router, tags=["Chat"])
