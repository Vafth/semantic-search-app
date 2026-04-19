from fastapi import Header
from .schemas.internal import InternalUser, UserRole

async def get_internal_user(
    x_user_id:   int      = Header(...),
    x_user_role: UserRole = Header(...),
) -> InternalUser:
    return InternalUser(id=x_user_id, role=x_user_role)