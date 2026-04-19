import logging
import httpx

from fastapi import APIRouter, Depends, Header, HTTPException
from qdrant_client.models import Filter, FieldCondition, MatchAny

from core.config import settings
from core.processor import embed_query, deduplicate_results, refine_results
from database import AsyncSessionDep
from qdrant import QdrantDep
from repository.vector import query_collection, deep_search
from repository.postgres import create_search_request, save_search_results, get_requests_by_user
from schemas.search import SearchParams, SearchResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search(
    db:       AsyncSessionDep,
    qdrant:   QdrantDep,
    params:   SearchParams = Depends(),
    x_user_id: int = Header(...),
):
    if params.model not in settings.COLLECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{params.model}'. Choose from: {list(settings.COLLECTIONS.keys())}",
        )

    collection = settings.COLLECTIONS[params.model]["collection"]

    try:
        query_vector = await embed_query(params.query, params.model)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Model service error: {e}")

    search_filter = None
    if params.document_ids:
        ids = params.document_ids.split(",")
        logger.info(f"Filtering to {len(ids)} document(s)")
        search_filter = Filter(
            must=[FieldCondition(key="document_id", match=MatchAny(any=ids))]
        )

    results = await query_collection(qdrant, collection, query_vector, params, search_filter)

    if params.deep:
        existing = {r.chunk_index for r in results}
        rescued  = await deep_search(qdrant, collection, query_vector, params, existing, search_filter)
        results  = deduplicate_results(results + rescued, params.top_k)

    if params.refine:
        results = await refine_results(results, params)

    search_request = await create_search_request(db, user_id=x_user_id, query=params.query, params=params.model_dump(exclude={"query"}))
    await save_search_results(db, request_id=search_request.id, results=[r.model_dump() for r in results])

    return SearchResponse(query=params.query, model=params.model, collection=collection, results=results)


@router.get("/history")
async def search_history(
    db:        AsyncSessionDep,
    x_user_id: int = Header(...),
):
    return await get_requests_by_user(db, x_user_id)