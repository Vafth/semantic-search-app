from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Integer


class SearchRequest(SQLModel, table=True):
    __tablename__ = "search_requests"

    id:          Optional[int] = Field(default=None, primary_key=True)
    user_id:     int           = Field(sa_column=Column(Integer, nullable=False, index=True))
    document_id: Optional[int] = Field(sa_column=Column(Integer, nullable=True))

    query:         str  = Field()
    search_params: dict = Field(
        default_factory=dict,
        sa_type = sa.JSON, 
        nullable=False,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type = sa.DateTime(timezone=True), 
        nullable=False,
    )

    results: list["SearchResult"] = Relationship(back_populates="request", cascade_delete=True)


class SearchResult(SQLModel, table=True):
    __tablename__ = "search_results"

    id:          Optional[int] = Field(default=None, primary_key=True)
    request_id:  int           = Field(foreign_key="search_requests.id", index=True)

    chunk_text:  str   = Field()
    chunk_index: int   = Field()   # position inside the source document
    score:       float = Field()

    request: SearchRequest = Relationship(back_populates="results")