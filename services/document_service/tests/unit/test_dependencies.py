from common.dependencies import get_internal_user
from common.schemas.internal import InternalUser


async def test_get_internal_user_returns_internal_user():
    result = await get_internal_user(x_user_id=1, x_user_role="user")
    assert isinstance(result, InternalUser)
    assert result.id == 1
    assert result.role == "user"


async def test_get_internal_user_admin_role():
    result = await get_internal_user(x_user_id=42, x_user_role="admin")
    assert result.id == 42
    assert result.role == "admin"