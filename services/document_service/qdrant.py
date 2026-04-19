from typing import Annotated
from logging import getLogger

from fastapi import Depends
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from core.config import settings

logger = getLogger(__name__)

_client: QdrantClient | None = None

def init_qdrant() -> None:
    global _client
    _client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    existing = [c.name for c in _client.get_collections().collections]

    for model_name, cfg in settings.COLLECTIONS.items():
        col  = cfg["collection"]
        size = cfg["vector_size"]

        if col not in existing:
            _client.create_collection(
                collection_name=col,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE),
            )
            logger.info(f"Created collection '{col}' (size={size}) for model '{model_name}'")
        else:
            logger.info(f"Collection '{col}' already exists")


def get_qdrant_client() -> QdrantClient:
    assert _client is not None, "Qdrant client not initialized"
    return _client


QdrantDep = Annotated[QdrantClient, Depends(get_qdrant_client)]