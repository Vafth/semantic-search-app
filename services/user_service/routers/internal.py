from fastapi import APIRouter, HTTPException, status

from database import AsyncSessionDep
from repository.user import get_user_by_id

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