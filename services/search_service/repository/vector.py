import re
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny

from core.processor import _score_sentence
from schemas.search import SearchParams, SearchResult

logger = logging.getLogger(__name__)


async def query_collection(
    qdrant:        QdrantClient,
    collection:    str,
    query_vector:  list[float],
    params:        SearchParams,
    search_filter,
) -> list[SearchResult]:
    response = qdrant.query_points(
        collection_name = collection,
        query           = query_vector,
        query_filter    = search_filter,
        limit           = params.top_k,
        with_payload    = True,
        score_threshold = params.score,
    )
    return [
        SearchResult(
            text        = hit.payload["text"],
            score       = round(hit.score, 4),
            chunk_index = hit.payload["chunk_index"],
            document_id = hit.payload["document_id"],
            filename    = hit.payload["filename"],
        )
        for hit in response.points
    ]


async def deep_search(
    qdrant:        QdrantClient,
    collection:    str,
    vector:        list[float],
    params:        SearchParams,
    existing:      set[int],
    search_filter,
) -> list[SearchResult]:
    borderline = qdrant.query_points(
        collection_name = collection,
        query           = vector,
        query_filter    = search_filter,
        limit           = params.top_k * 3,
        with_payload    = True,
        score_threshold = params.deep_min,
    )

    rescued = []
    for hit in borderline.points:
        if hit.score >= params.score or hit.payload["chunk_index"] in existing:
            continue

        sentences  = [
            s.strip() for s in re.split(r'(?<=[.!?])\s+', hit.payload["text"])
            if len(s.strip()) > 10
        ]
        scores     = [await _score_sentence(params.query, s, params.model) for s in sentences]
        best_score = max(scores)

        if best_score >= params.score:
            logger.info(f"Deep search rescued chunk {hit.payload['chunk_index']} (score {best_score})")
            rescued.append(SearchResult(
                text        = sentences[scores.index(best_score)],
                score       = round(best_score, 4),
                chunk_index = hit.payload["chunk_index"],
                document_id = hit.payload["document_id"],
                filename    = hit.payload["filename"],
            ))

    return rescued