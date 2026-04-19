from enum import Enum
from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, Integer
from sqlmodel import Field, SQLModel


class DocumentStatus(str, Enum):
    processing = "processing"
    ready      = "ready"
    failed     = "failed"


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id:      Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_type=sa.Integer,
        nullable=False,
        index=True,
    )

    file_name:    str           = Field(max_length=512)
    file_size:    int           = Field()          # bytes
    content_type: str           = Field(max_length=128)  # e.g. application/pdf
    chunk_count:  int           = Field(default=0) # filled after vectorisation
    status:       DocumentStatus = Field(default=DocumentStatus.processing)

    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type = sa.DateTime(timezone=True), 
        nullable=False,
    )