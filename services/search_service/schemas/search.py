from datetime import datetime
from typing import Optional, List

from fastapi import Query
from pydantic import BaseModel


class SearchResultRead(BaseModel):
    id:          int
    filename: int
    chunk_text:  str
    chunk_index: int
    score:       float

    model_config = {"from_attributes": True}


class SearchRequestRead(BaseModel):
    id:            int
    user_id:       int
    document_id:   Optional[int] = None
    query:         str
    search_params: dict
    created_at:    datetime
    results:       List[SearchResultRead] = []

    model_config = {"from_attributes": True}


class SearchRequestCreate(BaseModel):
    query:           str
    search_params:   dict = {}
    document_name:   Optional[str] = None


class SearchParams(BaseModel):
    query:     str           = Query(...)
    model:     str           = Query(...)
    top_k:     int           = Query(5)
    score:     float         = Query(0.4)
    dif:       float         = Query(0.0)
    filenames: Optional[str] = Query(None)
    refine:    bool          = Query(False)
    deep:      bool          = Query(False)
    deep_min:  float         = Query(0.25)


class SearchHit(BaseModel):
    text:        str
    score:       float
    chunk_index: int
    filename:    str

class SearchResponse(BaseModel):
    query:      str
    model:      str
    collection: str
    results:    list[SearchHit]