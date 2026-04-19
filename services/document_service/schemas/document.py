from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id:           int
    user_id:      int
    file_name:    str
    file_size:    int
    content_type: str
    chunk_count:  int
    status:       str
    uploaded_at:  datetime

    model_config = {"from_attributes": True}


class DocumentCreate(BaseModel):
    """Used when client uploads a file"""
    file_name:    str
    file_size:    int
    content_type: str