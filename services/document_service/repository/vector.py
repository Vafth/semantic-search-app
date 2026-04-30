import uuid
from logging import getLogger

from fastapi import HTTPException
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct

from core.config import settings

logger = getLogger(__name__)

async def store_chunks(
    qdrant:     QdrantClient,
    chunks:     list[str],
    vectors:    list[list[float]],
    doc_id:     int,
    filename:   str,
    model_name: str,
    cfg:        dict,
) -> None:
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text":        chunk,
                "document_id": doc_id,
                "filename":    filename,
                "chunk_index": i,
                "model":       model_name,
            }
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    qdrant.upsert(collection_name=cfg["collection"], points=points)
    logger.info(f"Stored {len(points)} points in '{cfg['collection']}'")


async def get_chunks_by_document(qdrant: QdrantClient, document_id: int) -> str:
    collection = list(settings.COLLECTIONS.values())[0]["collection"]

    results, _ = qdrant.scroll(
        collection_name=collection,
        scroll_filter=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
        limit=1000,
        with_payload=True,
    )

    if not results:
        return ""

    # Sort by chunk_index to ensure the story makes sense
    valid = [p for p in results if p.payload is not None]
    valid.sort(key=lambda p: p.payload["chunk_index"] if p.payload else 0)

    step = settings.CHUNK_SIZE - settings.CHUNK_OVERLAP
    all_sentences = []

    for i, point in enumerate(valid):
        text = point.payload["text"] if point.payload else ""
        sentences = [s.strip() for s in text.split(". ") if s.strip()]

        if i < len(valid) - 1:
            all_sentences.extend(sentences[:step])
        else:
            all_sentences.extend(sentences)

    return ". ".join(all_sentences)

async def delete_points_by_document(qdrant: QdrantClient, doc_id: int) -> list[str]:
    failed = []
    for _, cfg in settings.COLLECTIONS.items():
        try:
            qdrant.delete(
                collection_name  = cfg["collection"],
                points_selector  = Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=doc_id))]
                ),
            )
        except Exception:
            failed.append(cfg["collection"])
    return failed