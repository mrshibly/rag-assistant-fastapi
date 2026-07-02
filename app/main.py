from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.api.v1.router import router as v1_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load ML models on startup to avoid cold-start latency."""
    logger.info("Loading embedding model...")
    from app.services.ingestion import _embedder  # noqa: F401
    logger.info("Embedding model ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Mini AI Assistant",
    description="AI Assistant with knowledge ingestion, RAG chat, context memory, and tool calling.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )


app.include_router(v1_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
