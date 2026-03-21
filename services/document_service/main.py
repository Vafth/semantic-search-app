from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, 
    Filter, FieldCondition, MatchValue
)

import httpx
import re
import os
import uuid
import logging
import sys
import asyncio

logger  = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s'
))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

MODEL_URL     = os.getenv("MODEL_SERVICE_URL", "http://localhost:8000")
DB_HOST       = os.getenv("DB_HOST", "localhost")
DB_PORT       = int(os.getenv("DB_PORT", 6333))
VECTOR_SIZE   = 768
CHUNK_SIZE    = 3
CHUNK_OVERLAP = 1

COLLECTIONS = {
    "small_model":        {"collection": "docs_small_r2",     "vector_size": 384},
    "normal_model":       {"collection": "docs_english_r2",   "vector_size": 768},
    "multilingual_model": {"collection": "docs_multilingual", "vector_size": 768},
}

# -- DataClasses ----

class UploadResponse(BaseModel):
    message:       str
    document_id:   str
    chunks_stored: int

class DocumentInfo(BaseModel):
    document_id: str
    filename:    str
    chunks:      int

# -- apps ----

app = FastAPI()
db_client: QdrantClient = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    global db_client
    db_client = QdrantClient(host=DB_HOST, port=DB_PORT)
    _ensure_collections()

    logger.info("Document Service started. Qdrant connected.")


def _ensure_collections():
    existing = [c.name for c in db_client.get_collections().collections]
 
    for model_name, cfg in COLLECTIONS.items():
        col  = cfg["collection"]
        size = cfg["vector_size"]
 
        if col not in existing:
            db_client.create_collection(
                collection_name=col,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE),
            )
            logger.info(f"Created collection '{col}' (size={size}) for model '{model_name}'")
        else:
            logger.info(f"Collection '{col}' already exists")

# -- Help functions ----

def generate_id() -> str:

    return str(uuid.uuid4())

def split_into_sentences(text: str) -> list[str]:
    raw = re.split(r'(?<=[.!?])\s+', text.strip())

    return [s.strip() for s in raw if len(s.strip()) > 10]

def clean_text(text: str) -> str:

    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[citation needed\]', '', text)
    text = re.sub(r'\[c\]', '', text)
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
    text = re.sub(r'\n([A-Z][^\n]{3,80})\n', r'. \1. ', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n+', ' ', text)

    return text.strip()

def chunk_sentences(sentences: list[str], size: int, overlap: int) -> list[str]:
    
    chunks = []
    step = size - overlap  # how many sentences to advance each iteration

    for i in range(0, len(sentences), step):
        chunk = " ".join(sentences[i : i + size])
        if chunk:
            chunks.append(chunk)
    
    return chunks

def chunk_text(text: str) -> list[str]:
    
    text = clean_text(text)
    sentences = split_into_sentences(text)
    
    if not sentences:
        raise ValueError("No sentences found in the uploaded file.")
    
    return chunk_sentences(sentences, CHUNK_SIZE, CHUNK_OVERLAP)

async def get_embeddings(texts: list[str], model: str) -> list[list[float]]:
    
    batch_size = 16 if model in ("normal_model", "multilingual_model") else 32

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(
            f"{MODEL_URL}/embed",
            json={"texts": texts, "model": model, "batch_size": batch_size},
        )
        response.raise_for_status()
        return response.json()["vectors"]

async def embed_and_store(chunks, document_id, filename, model_name, cfg):
    vectors = await get_embeddings(chunks, model_name)
    points = [
        PointStruct(
            id      = str(uuid.uuid4()),
            vector  = vector,
            payload = {
                "text":        chunk,
                "document_id": document_id,
                "filename":    filename,
                "chunk_index": i,
                "model":       model_name,
            }
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    db_client.upsert(collection_name=cfg["collection"], points=points)
    logger.info(f"Stored {len(points)} points in '{cfg['collection']}'")

# -- Endpoints ----

@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):

    if not file.filename.endswith((".txt")):
        raise HTTPException(status_code=400, detail="Only .txt files are supported.")
 
    raw_bytes = await file.read()
    
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")
 
    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
 
    try:
        chunks = chunk_text(text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
 
    logger.info(f"File '{file.filename}' splits into {len(chunks)} chunks.")

    document_id = str(uuid.uuid4())
 
    await asyncio.gather(*[
        embed_and_store(chunks, document_id, file.filename, model_name, cfg)
        for model_name, cfg in COLLECTIONS.items()
    ]) 
  
    return UploadResponse(
        message       = "Document indexed in all models successfully.",
        document_id   = document_id,
        chunks_stored = len(chunks),
    )

@app.get("/documents", response_model=list[DocumentInfo])
def list_documents():

    collection = list(COLLECTIONS.values())[0]["collection"]

    seen: dict[DocumentInfo] = {}
    offset    = None
    page_size = 100

    while True:
        results, next_offset = db_client.scroll(
            collection_name = collection,
            limit           = page_size,
            offset          = offset,
            with_payload    = True,
            with_vectors    = False, 
        )

        for point in results:
            doc_id   = point.payload["document_id"]
            filename = point.payload["filename"]

            if doc_id not in seen:
                seen[doc_id] = DocumentInfo(
                    document_id = doc_id,
                    filename    = filename,
                    chunks      = 1,
                )
            else:
                seen[doc_id].chunks += 1

        if next_offset is None:
            break

        offset = next_offset

    return list(seen.values())

@app.get("/document/{document_id}/text")
def get_document_text(document_id: str):
    
    collection = list(COLLECTIONS.values())[0]["collection"]
    
    results, _ = db_client.scroll(
        collection_name = collection,
        scroll_filter   = Filter(
            must = [
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            ]),
        limit           = 1000,
        with_payload    = True,
        with_vectors    = False,
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    results.sort(key=lambda p: p.payload["chunk_index"])

    step = CHUNK_SIZE - CHUNK_OVERLAP

    all_sentences = []
    for i, point in enumerate(results):
        sentences = [s.strip() for s in point.payload["text"].split(". ") if s.strip()]
        if i < len(results) - 1:
            all_sentences.extend(sentences[:step])
        else:
            all_sentences.extend(sentences)

    return {
        "document_id": document_id,
        "filename":    results[0].payload["filename"],
        "text":        ". ".join(all_sentences),
    }

@app.delete("/document/{document_id}")
def delete_document(document_id: str):
    
    failed: list[str] = []

    for _, cfg in COLLECTIONS.items():
        try:
            db_client.delete(
                collection_name=cfg["collection"],
                points_selector=Filter(
                    must=[FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )]
                ),
            )
            logger.info(f"Deleted '{document_id}' from '{cfg['collection']}'")

        except Exception as e:
            failed.append(cfg["collection"])
            logger.error(f"Failed to delete from '{cfg['collection']}': {e}")

    if failed:
        raise HTTPException(
            status_code=500,
            detail=f"Deletion failed for collections: {failed}"
        )

    return {"message": f"Document {document_id} deleted from all collections."}

@app.get("/health")
def health():
    return {"status": "ok", "service": "document-service"}