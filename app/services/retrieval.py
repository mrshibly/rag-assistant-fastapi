from sentence_transformers import SentenceTransformer

from app.config import settings
from app.services.ingestion import _collection

_embedder = SentenceTransformer(settings.EMBEDDING_MODEL)


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """Query ChromaDB and return top-k relevant chunks."""
    if _collection.count() == 0:
        return []

    query_embedding = _embedder.encode([query]).tolist()
    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, _collection.count()),
    )

    return [
        {"text": doc, "source": meta["source"]}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]
