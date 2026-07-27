from fastapi import Header
from .schemas.internal import InternalUser, UserRole
from .core.config import _setting

async def get_internal_user(
        x_user_id:   int      = Header(...),
        x_user_role: UserRole = Header(...),
    ) -> InternalUser:

    return InternalUser(id=x_user_id, role=x_user_role)


def storage_limit_for_role(role: str) -> int:
    return {
        "user":  _setting.STORAGE_LIMIT_USER,
        "admin": _setting.STORAGE_LIMIT_ADMIN,
        "owner": -1,
    }.get(role, _setting.STORAGE_LIMIT_USER)

