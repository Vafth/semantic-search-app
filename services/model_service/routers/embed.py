from fastapi import APIRouter, HTTPException
from typing import List, Literal
from pydantic import BaseModel
from core.processor import manager

router = APIRouter()

class EmbedRequest(BaseModel):
    model: Literal["small_model", "normal_model", "multilingual_model"]
    texts: List[str]
    batch_size: int = 32

class EmbedResponse(BaseModel):
    vectors: List[List[float]]

class SimilarityRequest(BaseModel):
    model: Literal["small_model", "normal_model", "multilingual_model"]
    text_a: str
    text_b: str

@router.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    try:
        model = manager.get_model(request.model)
        vectors = model.encode(
            request.texts, 
            batch_size=request.batch_size, 
            normalize_embeddings=True
        )
        return EmbedResponse(vectors=vectors.tolist())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/similarity")
async def similarity(request: SimilarityRequest):
    try:
        score = manager.compute_similarity(request.model, request.text_a, request.text_b)
        return {"score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))