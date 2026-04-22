import re
import logging
import httpx

from core.config import settings
from schemas.search import SearchParams, SearchHit

logger = logging.getLogger(__name__)


async def embed_query(query: str, model_name: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        batch_size = 16 if model_name in ("normal_model", "multilingual_model") else 32
        response   = await client.post(
            f"{settings.MODEL_SERVICE_URL}/embed",
            json={"texts": [query], "model": model_name, "batch_size": batch_size},
        )
        response.raise_for_status()
        return response.json()["vectors"][0]


def deduplicate_results(results: list[SearchHit], top_k: int) -> list[SearchHit]:
    seen = {}
    for r in results:
        if r.text not in seen or r.score > seen[r.text].score:
            seen[r.text] = r
    return sorted(seen.values(), key=lambda r: r.score, reverse=True)[:top_k]


async def _score_sentence(query: str, sentence: str, model: str) -> float:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.MODEL_SERVICE_URL}/similarity",
            json={"model": model, "text_a": query, "text_b": sentence},
        )
        resp.raise_for_status()
        return resp.json()["score"]


async def _filter_chunk_to_relevant_sentences(
    query:      str,
    chunk_text: str,
    model_name: str,
    min_score:  float,
) -> str:
    sentences = [
        s.strip() for s in re.split(r'(?<=[.!?])\s+', chunk_text)
        if len(s.strip()) > 10
    ]
    if len(sentences) <= 1:
        return chunk_text

    async with httpx.AsyncClient(timeout=30.0) as client:
        scores = []
        for sentence in sentences:
            resp = await client.post(
                f"{settings.MODEL_SERVICE_URL}/similarity",
                json={"text_a": query, "text_b": sentence, "model": model_name},
            )
            resp.raise_for_status()
            scores.append(resp.json()["score"])

    logger.info(f"Sentence scores: {scores}")
    kept = [s for s, sc in zip(sentences, scores) if sc >= min_score]
    return " ".join(kept) if kept else sentences[scores.index(max(scores))]


async def refine_results(results: list[SearchHit], params: SearchParams) -> list[SearchHit]:
    refined: list[SearchHit] = []
    
    for r in results:
        filtered_text = await _filter_chunk_to_relevant_sentences(
            query      = params.query,
            chunk_text = r.text,
            model_name = params.model,
            min_score  = params.score + params.dif,
        )
        refined.append(r.model_copy(update={"text": filtered_text}))
    return refined