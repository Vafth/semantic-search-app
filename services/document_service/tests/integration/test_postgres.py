from repository.postgres import create_document, update_document_status, _get_document_by_id, get_document_by_name, delete_document_by_name, delete_document_by_id, get_documents_by_user

from models.document import DocumentStatus

async def test_document_interactions(session_with_document):
    db_document = await _get_document_by_id(session_with_document, 1)
    assert db_document

    await update_document_status(session_with_document, db_document.id, DocumentStatus.ready, 2)

    db_updated_document = await get_document_by_name(session_with_document, 1, db_document.filename)

    assert db_updated_document and db_updated_document.status == "ready"

    user_docs = await get_documents_by_user(session_with_document, 1)
    assert len(user_docs) == 1

    result = await delete_document_by_name(session_with_document, 1, db_document.filename)    
    assert result == True

async def test_fault_doc_delete(db_session):
    result = await delete_document_by_name(db_session, 1, "123")    
    assert result == False

async def test_doc_delete_by_id(session_with_document):
    await delete_document_by_id(session_with_document, 1)    

    db_new_document = await _get_document_by_id(session_with_document, 1)
    assert db_new_document == None