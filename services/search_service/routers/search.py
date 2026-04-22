import logging
import httpx

from fastapi import APIRouter, Depends, Header, HTTPException
from qdrant_client.models import Filter

from core.config import settings
from core.processor import embed_query, deduplicate_results, refine_results
from database import AsyncSessionDep
from qdrant import QdrantDep
from repository.vector import query_collection, deep_search, build_filename_filter
from repository.postgres import save_search_request, save_search_results, get_requests_by_user
from schemas.search import SearchParams, SearchResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search(
    db:        AsyncSessionDep,
    qdrant:    QdrantDep,
    params:    SearchParams = Depends(),
    x_user_id: int = Header(...),
):
    # 1. Check the embedding model and document collection
    if params.model not in settings.COLLECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{params.model}'. Choose from: {list(settings.COLLECTIONS.keys())}",
        )

    collection = settings.COLLECTIONS[params.model]["collection"]

    # 2. Embed the search query
    try:
        query_vector = await embed_query(params.query, params.model)
    
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Model service error: {e}")

    # 3. Create the search filter for Qdrant
    search_filter: Filter | None = None
    
    if params.filenames:
        names = params.filenames.split(",")
        logger.info(f"Filtering to {len(names)} document(s)")
        search_filter = build_filename_filter(names)

    # 4. Search in Qdrant
    results = await query_collection(qdrant, collection, query_vector, params, search_filter)

    # 5. The Deep Search
    if params.deep:
        existing = {r.chunk_index for r in results}
        rescued  = await deep_search(qdrant, collection, query_vector, params, existing, search_filter)
        results  = deduplicate_results(results + rescued, params.top_k)

# 6. The search results refining
    if params.refine:
        results = await refine_results(results, params)
        results = deduplicate_results(results, params.top_k)
        
    # 7. Saving search request and results
    search_request_id = await save_search_request(db, x_user_id, params)
    
    await save_search_results(db, search_request_id, results)

    # 8. Return Search Responses 
    return SearchResponse(query=params.query, model=params.model, collection=collection, results=results)


@router.get("/history", response_model=list[SearchResponse])
async def search_history(
    db:        AsyncSessionDep,
    x_user_id: int = Header(...),
):
    return await get_requests_by_user(db, x_user_id)