from fastapi import APIRouter, HTTPException, status, Query

from db.deps import AsyncSessionDep
from repository.user import get_user_by_id, increment_storage_used

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/verify/{user_id}", status_code=status.HTTP_200_OK)
async def verify_user(user_id: int, session: AsyncSessionDep):
    """Called by gateway to confirm user exists and is active."""
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return {"ok": True}


@router.get("/storage/{user_id}")
async def get_storage(user_id: int, db: AsyncSessionDep) -> dict:

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404)
    return {"storage_used": user.storage_used}


@router.patch("/storage/{user_id}")
async def update_storage(user_id: int, delta: int = Query(...), db: AsyncSessionDep = None) -> None:
    await increment_storage_used(db, user_id, delta)