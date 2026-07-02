import tempfile
from pathlib import Path

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from fastembed import TextEmbedding

from app.config import settings

_embedder = TextEmbedding(model_name=settings.EMBEDDING_MODEL)
_chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
_collection = _chroma_client.get_or_create_collection(
    name="knowledge_base",
    metadata={"hnsw:space": "cosine"},
)
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP,
)


def _extract_text(file_path: Path, suffix: str) -> str:
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file_path.read_text(encoding="utf-8")


async def ingest_file(filename: str, content: bytes) -> int:
    """Ingest a document: load → chunk → embed → store. Returns chunk count."""
    suffix = Path(filename).suffix.lower()
    if suffix not in (".pdf", ".txt", ".md"):
        raise ValueError(f"Unsupported file type: {suffix}")

    # Write to temp file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        text = _extract_text(tmp_path, suffix)
    finally:
        tmp_path.unlink(missing_ok=True)

    chunks = _splitter.split_text(text)
    if not chunks:
        return 0

    embeddings = [e.tolist() for e in _embedder.embed(chunks)]
    ids = [f"{filename}_{i}" for i in range(len(chunks))]

    _collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=[{"source": filename, "chunk_index": i} for i in range(len(chunks))],
    )
    return len(chunks)


from fastapi import HTTPException, UploadFile
from app.schemas.chat import IngestResponse
import logging

logger = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


async def process_upload(file: UploadFile) -> IngestResponse:
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        chunks = await ingest_file(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Ingestion failed for '%s': %s", file.filename, e)
        raise HTTPException(status_code=500, detail="Failed to process document.")

    logger.info("Ingested '%s' → %d chunks", file.filename, chunks)
    return IngestResponse(filename=file.filename, chunks=chunks)

