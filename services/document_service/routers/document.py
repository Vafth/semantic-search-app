from fastapi import APIRouter, File, UploadFile, HTTPException, Header
from qdrant_client.models import Filter, FieldCondition, MatchValue
import asyncio

from core.config import settings
from core.processor import chunk_text, get_embeddings

from database import AsyncSessionDep
from qdrant import QdrantDep
from models.document import DocumentStatus
from schemas.document import DocumentRead, DocumentCreate
from repository.postgres import (
    create_document, 
    update_document_status,
    get_documents_by_user, 
    get_document_by_id,
    delete_document_by_id
)
from repository.vector import store_chunks, get_chunks_by_document

router = APIRouter()

# ── EndPoints ─────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload(
    db: AsyncSessionDep,
    qdrant: QdrantDep,
    x_user_id: int = Header(...),
    file: UploadFile = File(...)
):
    if not file.filename or not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported.")

    content = await file.read()

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    try:
        chunks = chunk_text(text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 1. Create entry in PostgreSQL
    doc_in = DocumentCreate(
        file_name    = file.filename,
        file_size    = len(content),
        content_type = file.content_type,
    )
    doc_record = await create_document(db, doc_in, x_user_id)

    # 2. Upload to Qdrant
    try:
        chunks = chunk_text(text)

        await asyncio.gather(*[
            store_chunks(
                qdrant,
                chunks,
                await get_embeddings(chunks, model_name),
                doc_record.id,
                file.filename,
                model_name,
                cfg,
            )
            for model_name, cfg in settings.COLLECTIONS.items()
        ])
            
        # 3. Update PostgreSQL to Ready
        await update_document_status(db, doc_record.id, DocumentStatus.ready, len(chunks))
        
        return {
            "message":      "Document indexed successfully.",
            "document_id":   doc_record.id,
            "chunks_stored": len(chunks)
        }
    except Exception as e:
        # Mark as failed if Qdrant fails
        await update_document_status(db, doc_record.id, DocumentStatus.failed)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/documents",response_model=list[DocumentRead])
async def list_documents(
    db:        AsyncSessionDep,
    x_user_id: int = Header(...)
):

    docs = await get_documents_by_user(db, x_user_id)
    return docs

@router.get("/document/{document_id}/text")
async def get_document_text(
    document_id: int,
    db:          AsyncSessionDep,
    qdrant:      QdrantDep,
    x_user_id:   int = Header(...)
):
    # 1. Ownership check in Postgres
    doc = await get_document_by_id(db, document_id)
    if not doc or doc.user_id != x_user_id:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 2. Reconstruct text using our core logic
    text = await get_chunks_by_document(qdrant, document_id)
    
    if not text:
        raise HTTPException(status_code=404, detail="Document content missing in vector store.")

    return {
        "document_id": document_id,
        "filename":    doc.file_name,
        "text":        text,
    }

@router.delete("/document/{document_id}")
async def delete_document(
    document_id: int,
    db:          AsyncSessionDep,
    qdrant:      QdrantDep,
    x_user_id:   int = Header(...)
):
    # 1. Verify ownership in Postgres
    doc = await get_document_by_id(db, document_id)
    if not doc or doc.user_id != x_user_id:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 2. Delete from Qdrant first (Vector DB Cleanup)
    failed = []
    for _, cfg in settings.COLLECTIONS.items():
        try:
            qdrant.delete(
                collection_name=cfg["collection"],
                points_selector=Filter(
                    must=[FieldCondition(
                        key   = "document_id",
                        match = MatchValue(value=document_id)
                    )]
                ),
            )
        except Exception:
            failed.append(cfg["collection"])

    if failed:
        raise HTTPException(status_code=500, detail="Qdrant deletion failed.")

    # 3. Delete from Postgres
    await delete_document_by_id(document_id, db)
    
    return {"message": "Document deleted successfully."}