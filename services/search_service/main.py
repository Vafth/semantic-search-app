from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient, models
from qdrant_client.models import Filter, FieldCondition

from typing import Optional
import httpx
import os
import re
import logging
import sys

# -- Logger ----

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s'
))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

MODEL_URL     = os.getenv("MODEL_SERVICE_URL", "http://localhost:8000")
DB_HOST       = os.getenv("DB_HOST", "localhost")
DB_PORT       = int(os.getenv("DB_PORT", 6333))
DEF_TOP_K     = 5
DEF_MIN_SCORE = 0.4
DEF_MIN_DIF   = 0.05

COLLECTIONS = {
    "small_model":        "docs_small_r2",
    "normal_model":       "docs_english_r2",
    "multilingual_model": "docs_multilingual",
}

app = FastAPI(title="Search Service", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

qdrant: QdrantClient = None

@app.on_event("startup")
def startup():
    global qdrant
    qdrant = QdrantClient(host=DB_HOST, port=DB_PORT)
    logger.info("Search Service started. Qdrant connected.")

# -- Data classes ----

class SearchParams(BaseModel):
    query:        str   = Query(...)
    model:        str   = Query("small_model")
    top_k:        int   = Query(5)
    score:        float = Query(0.4)
    dif:          float = Query(0)
    document_ids: Optional[str] = Query(None)
    refine:       bool  = Query(False)
    deep:         bool  = Query(False)
    deep_min:     float = Query(0.25)

class SearchResult(BaseModel):
    text:        str
    score:       float
    chunk_index: int
    document_id: str
    filename:    str

class SearchResponse(BaseModel):
    query:      str
    model:      str
    collection: str
    results:    list[SearchResult]

# -- Help functions ----

def deduplicate_results(results: list[SearchResult], top_k: int) -> list[SearchResult]:
    
    seen = {}
    for r in results:
        if r.text not in seen or r.score > seen[r.text].score:
            seen[r.text] = r
    
    return sorted(seen.values(), key=lambda r: r.score, reverse=True)[:top_k]

async def refine_results(results: list[SearchResult], params: SearchParams) -> list[SearchResult]:
    
    refined = []
    for r in results:
        filtered_text = await filter_chunk_to_relevant_sentences(
            query      = params.query,
            chunk_text = r.text,
            model_name = params.model,
            min_score  = params.score + params.dif,
        )
        refined.append(r.model_copy(update={"text": filtered_text}))
    
    return refined

async def score_sentence(query: str, sentence: str, model: str) -> float:
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{MODEL_URL}/similarity",
            json={"model": model, "text_a": query, "text_b": sentence}
        )
        resp.raise_for_status()
    
        return resp.json()["score"]

async def deep_search(
    collection:  str,
    vector:      list[float],
    params:      SearchParams,
    existing:    set[int],
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
        if hit.score >= params.score:
            continue
        if hit.payload["chunk_index"] in existing:
            continue

        sentences = [
            s.strip() for s in
            re.split(r'(?<=[.!?])\s+', hit.payload["text"])
            if len(s.strip()) > 10
        ]

        scores = [await score_sentence(params.query, s, params.model) for s in sentences]
        best_score = max(scores)
        best_sentence = sentences[scores.index(best_score)]

        if best_score >= params.score:
            logger.info(f"Deep search rescued sentence (chunk {hit.payload['chunk_index']}, score {best_score})")
            rescued.append(SearchResult(
                text        = best_sentence,
                score       = round(best_score, 4),
                chunk_index = hit.payload["chunk_index"],
                document_id = hit.payload["document_id"],
                filename    = hit.payload["filename"],
            ))

    return rescued

async def embed_query(query: str, model_name: str) -> list[float]:

    async with httpx.AsyncClient(timeout=60.0) as client:
        batch_size = 16 if model_name in ("normal_model", "multilingual_model") else 32
        
        response = await client.post(
            f"{MODEL_URL}/embed",
            json={"texts": [query], "model": model_name, "batch_size": batch_size},
        )
        response.raise_for_status()
        return response.json()["vectors"][0]

async def filter_chunk_to_relevant_sentences(
    query:      str,
    chunk_text: str,
    model_name: str,
    min_score:  float = DEF_MIN_SCORE + DEF_MIN_DIF,
) -> str:
    
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', chunk_text) if len(s.strip()) > 10]

    logger.info(f"Raw filtered sentence: {sentences}")
    if len(sentences) <= 1:
        return chunk_text

    async with httpx.AsyncClient(timeout=30.0) as client:
        scores = []
        for sentence in sentences:
            resp = await client.post(
                f"{MODEL_URL}/similarity",
                json={"text_a": query, "text_b": sentence, "model": model_name}
            )
            resp.raise_for_status()
            scores.append(resp.json()["score"])

    kept = [s for s, sc in zip(sentences, scores) if sc >= min_score]
    
    logger.info(f"Scores for each sentence: {scores}")
    
    if not kept:
        best = sentences[scores.index(max(scores))]
        return best

    return " ".join(kept)

# -- Endpoints ----

@app.get("/search", response_model=SearchResponse)
async def search(params: SearchParams = Depends()):

    if params.model not in COLLECTIONS:
        raise HTTPException(
            status_code = 400,
            detail      = f"Unknown model '{params.model}'. Choose from: {list(COLLECTIONS.keys())}"
        )

    collection = COLLECTIONS[params.model]

    try:
        query_vector = await embed_query(params.query, params.model)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Model Service error: {e}")
    

    logger.info(f"Searching '{collection}' for: '{params.query}' | top_k={params.top_k} | score>={params.score} with {params.model}")

    search_filter = None
    if params.document_ids:
        ids = params.document_ids.split(",") if params.document_ids else None
        logger.info(f"Amount of involved documents: {len(ids)}")
        search_filter = Filter(
            must=[FieldCondition(
                key="document_id",
                match=models.MatchAny(any=ids)
            )]
        )

    response = qdrant.query_points(
        collection_name = collection,
        query           = query_vector,
        query_filter    = search_filter,
        limit           = params.top_k,
        with_payload    = True,
        score_threshold = params.score,
    )

    results = [
        SearchResult(
            text        = hit.payload["text"],
            score       = round(hit.score, 4),
            chunk_index = hit.payload["chunk_index"],
            document_id = hit.payload["document_id"],
            filename    = hit.payload["filename"],
        )
        for hit in response.points
    ]

    if params.deep:
        existing = {r.chunk_index for r in results}
        deep     = await deep_search(collection, query_vector, params, existing, search_filter)
        results  = deduplicate_results(results + deep, params.top_k)

    logger.info(f"Found {len(results)} results in '{collection}'")

    if params.refine:
        results = await refine_results(results, params)

    return SearchResponse(
        query      = params.query,
        model      = params.model,
        collection = collection,
        results    = results,
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "search-service"}