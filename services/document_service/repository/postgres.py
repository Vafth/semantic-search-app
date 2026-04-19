from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.document import Document, DocumentStatus
from schemas.document import DocumentCreate

async def create_document(db: AsyncSession, doc_in: DocumentCreate, user_id: int) -> Document:
    db_obj = Document(**doc_in.model_dump(), user_id=user_id)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_document_status(
    db: AsyncSession, 
    doc_id: int, 
    status: DocumentStatus, 
    chunk_count: int = 0
) -> None:
    doc = await get_document_by_id(db, doc_id)
    if doc:
        doc.status = status
        if chunk_count > 0:
            doc.chunk_count = chunk_count
        await db.commit()

async def get_documents_by_user(db: AsyncSession, user_id: int) -> list[Document]:
    result = await db.execute(select(Document).where(Document.user_id == user_id))
    return list(result.scalars().all())

async def get_document_by_id(db: AsyncSession, doc_id: int) -> Document | None:
    return await db.get(Document, doc_id)

async def delete_document_by_id(db: AsyncSession, doc_id: int) -> None:
    doc = await get_document_by_id(db, doc_id)
    if doc:
        await db.delete(doc)
        await db.commit()