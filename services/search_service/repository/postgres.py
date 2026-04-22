from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.search import SearchRequest, SearchResult
from schemas.search import SearchHit, SearchParams


async def save_search_request(
        db:        AsyncSession,
        user_id:   int,
        params:    SearchParams,
    ) -> int:

    obj = SearchRequest(
        user_id       = user_id,
        filenames     = params.filenames,
        query         = params.query,
        search_params = params.model_dump(exclude={"query", "filenames"})
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    assert obj.id is not None
    return obj.id



async def save_search_results(
    db:         AsyncSession,
    request_id: int,
    results:    list[SearchHit],
) -> None:
    
    for r in results:
        obj = SearchResult(
            request_id  = request_id,
            filename    = r.filename,
            chunk_text  = r.text,
            chunk_index = r.chunk_index,
            score       = r.score,
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