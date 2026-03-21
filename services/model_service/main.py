from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
from typing import List, Literal
import torch

import logging
import sys

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


app = FastAPI()

loaded = {
    "small_model":        {"model": SentenceTransformer, "vector_size": 384},
    "normal_model":       {"model": SentenceTransformer, "vector_size": 768},
    "multilingual_model": {"model": SentenceTransformer, "vector_size": 768},
}

@app.on_event("startup")
def startup():
    global loaded

    loaded["small_model"]["model"]        = SentenceTransformer("ibm-granite/granite-embedding-small-english-r2")
    loaded["normal_model"]["model"]       = SentenceTransformer("ibm-granite/granite-embedding-english-r2")
    loaded["multilingual_model"]["model"] = SentenceTransformer("ibm-granite/granite-embedding-278m-multilingual")
        
    logger.info("Models loaded and ready.")


class EmbedRequest(BaseModel):
    model: Literal["small_model", "normal_model", "multilingual_model"]
    texts: List[str]
    batch_size: int

class EmbedResponse(BaseModel):
    vectors: List[List[float]]

class SimilarityRequest(BaseModel):
    model: Literal["small_model", "normal_model", "multilingual_model"]
    text_a: str
    text_b: str

class SimilarityResponse(BaseModel):
    score: float


@app.post("/similarity")
def similarity(request: SimilarityRequest):
    if request.model not in loaded:
        raise HTTPException(
            status_code=503,
            detail=f"Model '{request.model}' is not yet loaded."
        )

    m    = loaded[request.model]["model"]
    vecs = m.encode(
        [request.text_a, request.text_b],
        normalize_embeddings=True,
    )

    score = float(util.cos_sim(vecs[0], vecs[1]).item())
    score = round(max(0.0, min(1.0, score)), 4)

    return SimilarityResponse(score=score)

@app.post("/embed")
def embed(request: EmbedRequest):
    if request.model not in loaded:
        raise HTTPException(
            status_code=503,
            detail=f"Model '{request.model}' is defined but not yet loaded."
        )

    m = loaded[request.model]["model"]

    all_vectors = []
    for i in range(0, len(request.texts), request.batch_size):
        batch = request.texts[i : i + request.batch_size]
        vecs  = m.encode(batch, normalize_embeddings=True)
        all_vectors.extend(vecs.tolist())

    return EmbedResponse(vectors=all_vectors)

@app.get("/health")
def health():
    return {"status": "ok", "service": "model-service"}