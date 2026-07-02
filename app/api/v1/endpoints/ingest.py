from fastapi import APIRouter, UploadFile

from app.schemas.chat import IngestResponse
from app.services.ingestion import process_upload

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile):
    """Upload and ingest a PDF, TXT, or Markdown file into the knowledge base."""
    return await process_upload(file)

