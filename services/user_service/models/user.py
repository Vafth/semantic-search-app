from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from common.schemas.internal import UserRole


class User(SQLModel, table=True):
    __tablename__ = "users"

    id:              Optional[int] = Field(default=None, primary_key=True)
    username:        str           = Field(index=True, unique=True, max_length=50)
    hashed_password: str

    role:      UserRole  = Field(default=UserRole.user)
    is_active: bool      = Field(default=True)

    created_at: datetime = Field(
        default_factory  = lambda: datetime.now(timezone.utc),
        sa_type          = sa.DateTime(timezone=True),
        nullable         = False,
    )
    updated_at: Optional[datetime] = Field(
        default          = None,
        sa_type          = sa.DateTime(timezone=True),
        sa_column_kwargs = {"onupdate": sa.func.now()},
        nullable         = True,
    )