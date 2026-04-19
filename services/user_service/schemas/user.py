from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from common.schemas.internal import UserRole


class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, digits, - and _")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v


class UserRead(BaseModel):
    id:         int
    username:   str
    role:       UserRole
    is_active:  bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Admin-only patch payload."""
    role:      Optional[UserRole] = None
    is_active: Optional[bool]     = None


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"