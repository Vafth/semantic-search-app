from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, BigInteger, DateTime, func

from common.schemas.internal import UserRole


class User(SQLModel, table=True):
    __tablename__ = "users"

    id:              Optional[int] = Field(default = None, primary_key = True)
    username:        str           = Field(index   = True, unique      = True, max_length = 50)
    hashed_password: str

    role:         UserRole  = Field(default = UserRole.user)
    is_active:    bool      = Field(default = True)
    storage_used: int       = Field(default = 0, sa_column = Column(BigInteger, nullable = False, server_default = "0"))


    created_at: datetime = Field(
        default_factory  = lambda: datetime.now(timezone.utc),
        sa_type          = DateTime(timezone=True),
        nullable         = False,
    )
    updated_at: Optional[datetime] = Field(
        default          = None,
        sa_type          = DateTime(timezone=True),
        sa_column_kwargs = {"onupdate": func.now()},
        nullable         = True,
    )