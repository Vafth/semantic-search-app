from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.search import SearchRequest, SearchResult


async def create_search_request(
    db:      AsyncSession,
    user_id: int,
    query:   str,
    params:  dict,
) -> SearchRequest:
    obj = SearchRequest(
        user_id       = user_id,
        query         = query,
        search_params = params,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def save_search_results(
    db:         AsyncSession,
    request_id: int,
    results:    list[dict],
) -> None:
    for r in results:
        obj = SearchResult(
            request_id  = request_id,
            document_id = r["document_id"],
            chunk_text  = r["text"],
            chunk_index = r["chunk_index"],
            score       = r["score"],
        )
        db.add(obj)
    await db.commit()


async def get_requests_by_user(
    db:      AsyncSession,
    user_id: int,
) -> list[SearchRequest]:
    result = await db.execute(
        select(SearchRequest).where(SearchRequest.user_id == user_id)
    )
    return list(result.scalars().all())


async def get_results_by_request(
    db:         AsyncSession,
    request_id: int,
) -> list[SearchResult]:
    result = await db.execute(
        select(SearchResult).where(SearchResult.request_id == request_id)
    )
    return list(result.scalars().all())