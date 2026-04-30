from unittest.mock import patch

# ── upload ────────────────────────────────────────────────────────────────────

async def test_upload_wrong_collection(client, mock_index_document):
    mock_index_document.side_effect = ValueError("collection not found")
    
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
        headers={"x-user-id": "1"}
    )
    
    assert response.status_code == 500
    assert "Processing failed" in response.json()["detail"]

async def test_upload_wrong_file(client):
    
    response = await client.post(
        "/upload",
        files={"file": ("test.pdf", b"Mars is a red planet.", "text/plain")},
        headers={"x-user-id": "1"}
    )
    
    assert response.status_code == 400
    assert "Only .txt files are supported." in response.json()["detail"]

async def test_upload_wrong_encoding(client):
    
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", "Mars is a red planet.".encode("utf-16"), "text/plain")},
        headers={"x-user-id": "1"}
    )
    
    assert response.status_code == 400
    assert "File must be UTF-8 encoded." in response.json()["detail"]

async def test_upload_file_exist(client_with_file):
    
    response = await client_with_file.post(
        "/upload",
        files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
        headers={"x-user-id": "1"}
    )
    
    assert response.status_code == 409
    assert "Document with this name already exists" in response.json()["detail"]

async def test_upload_empty_file(client):    
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", b"", "text/plain")},
        headers={"x-user-id": "1"}
    )
    
    assert response.status_code == 422
    assert "No sentences found in the uploaded file." in response.json()["detail"]

async def test_upload_qdrant_fails(client, mock_get_embeddings):
    with patch("routers.document.index_document", side_effect=Exception("qdrant connection failed")):
        response = await client.post(
            "/upload",
            files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
            headers={"x-user-id": "1"}
        )
    assert response.status_code == 500
    assert "Processing failed" in response.json()["detail"]

async def test_upload_success(client, mock_get_embeddings):
    with patch("routers.document.index_document"):
        response = await client.post(
            "/upload",
            files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
            headers={"x-user-id": "1"}
        )
    assert response.status_code == 200
    assert response.json()["message"] == "Document indexed successfully."
    assert response.json()["chunks_stored"] > 0


# ── documents ─────────────────────────────────────────────────────────────────

async def test_get_user_docs(client_with_file):
    
    response = await client_with_file.get(
        "/documents",
        headers={"x-user-id": "1"}
    )
    
    assert response.status_code == 200
    assert list(response.json())[0]["filename"] == "test.txt"


# ── document/{document_name}/text ─────────────────────────────────────────────

async def test_get_doc_text_text_missing(client_with_file):
    
    response = await client_with_file.get(
        "/document/test.txt/text",
        headers={"x-user-id": "1"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Document content missing in vector store."


async def test_get_doc_text_wrong_filename(client_with_file):
    
    response = await client_with_file.get(
        "/document/123/text",
        headers={"x-user-id": "1"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


# ── delete document ───────────────────────────────────────────────────────────

async def test_delete_doc_no_file(client):
    
    response = await client.delete(
        "/document/123",
        headers={"x-user-id": "1"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."

async def test_delete_doc_qdrant_fails(client_with_file):
    with patch("routers.document.delete_points_by_document", return_value=["small_model_collection"]):
        response = await client_with_file.delete(
            "/document/test.txt",
            headers={"x-user-id": "1"}
        )
    
    assert response.status_code == 500
    assert response.json()["detail"] == "Qdrant deletion failed."

async def test_delete_doc(client_with_file):
    
    response = await client_with_file.delete(
        "/document/test.txt",
        headers={"x-user-id": "1"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Document deleted successfully."