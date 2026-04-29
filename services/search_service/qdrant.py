from typing import Annotated
from logging import Logger, getLogger

from fastapi import Depends
from qdrant_client import QdrantClient

from core.config import settings

logger: Logger = getLogger(__name__)
_client: QdrantClient | None = None

def connect_qdrant() -> None:
    global _client
    _client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT) # pragma: no cover
    logger.info("Connected to Qdrant") # pragma: no cover

def get_qdrant_client() -> QdrantClient:
    assert _client is not None, "Qdrant client not initialized — call connect_qdrant() first" # pragma: no cover
    return _client # pragma: no cover


QdrantDep = Annotated[QdrantClient, Depends(get_qdrant_client)]