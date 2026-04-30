from fastapi import APIRouter, File, UploadFile, HTTPException, Header

from core.config import settings
from core.processor import chunk_text

from database import AsyncSessionDep
from qdrant import QdrantDep
from models.document import DocumentStatus
from schemas.document import DocumentRead, DocumentCreate
from repository.postgres import (
    create_document, 
    update_document_status,
    get_documents_by_user, 
    get_document_by_name,
    delete_document_by_id
)
from repository.vector import get_chunks_by_document, delete_points_by_document
from core.processor import index_document

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

    existing = await get_document_by_name(db, x_user_id, file.filename)
    if existing:
        raise HTTPException(status_code=409, detail="Document with this name already exists")
    
    try:
        chunks = chunk_text(text)    
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 1. Create Document in PostgreSQL
    doc_in = DocumentCreate(
        filename    = file.filename,
        file_size    = len(content),
        content_type = file.content_type,
    )

    doc_record = await create_document(db, doc_in, x_user_id)

    try:
        # 2. Upload to Qdrant
        await index_document(qdrant, chunks, doc_record.id, file.filename)
            
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

@router.get("/document/{document_name}/text")
async def get_document_text(
    document_name: str,
    db:            AsyncSessionDep,
    qdrant:        QdrantDep,
    x_user_id:     int = Header(...)
):
    # 1. Find document in Postgres
    doc = await get_document_by_name(db, x_user_id, document_name)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 2. Reconstruct text
    text = await get_chunks_by_document(qdrant, doc.id)
    
    if not text:
        raise HTTPException(status_code=404, detail="Document content missing in vector store.")

    # 3. Return the document text
    return {
        "filename":    doc.filename,
        "text":        text,
    }

@router.delete("/document/{document_name}")
async def delete_document(
    document_name: str,
    db:            AsyncSessionDep,
    qdrant:        QdrantDep,
    x_user_id:     int = Header(...)
):
    # 1. Find document in Postgres
    doc = await get_document_by_name(db, x_user_id, document_name)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 2. Delete points from Qdrant
    failed = await delete_points_by_document(qdrant, doc.id)

    if failed:
        raise HTTPException(status_code=500, detail="Qdrant deletion failed.")

    # 3. Delete from Postgres
    await delete_document_by_id(db, doc.id)
    
    return {
        "message": "Document deleted successfully."
    }