from unittest.mock import patch


# ── upload ────────────────────────────────────────────────────────────────────

async def test_upload_wrong_collection(client):
    with patch("routers.document.index_document", side_effect=ValueError("collection not found")):
        response = await client.post(
            "/upload",
            files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
            headers={"x-user-id": "1", "x-user-role": "user"}
        )
    
    assert response.status_code == 500
    assert "Processing failed" in response.json()["detail"]


async def test_upload_wrong_file(client):
    response = await client.post(
        "/upload",
        files={"file": ("test.pdf", b"Mars is a red planet.", "text/plain")},
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    
    assert response.status_code == 400
    assert "Only .txt files are supported." in response.json()["detail"]


async def test_upload_wrong_encoding(client):
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", "Mars is a red planet.".encode("utf-16"), "text/plain")},
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    
    assert response.status_code == 400
    assert "File must be UTF-8 encoded." in response.json()["detail"]


async def test_upload_file_exist(client_with_file):
    response = await client_with_file.post(
        "/upload",
        files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    
    assert response.status_code == 409
    assert "Document with this name already exists" in response.json()["detail"]


async def test_upload_empty_file(client):    
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", b"", "text/plain")},
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    
    assert response.status_code == 422
    assert "No sentences found in the uploaded file." in response.json()["detail"]


async def test_upload_qdrant_fails(client):
    with patch("routers.document.index_document", side_effect=Exception("qdrant connection failed")):
        response = await client.post(
            "/upload",
            files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
            headers={"x-user-id": "1", "x-user-role": "user"}
        )
    assert response.status_code == 500
    assert "Processing failed" in response.json()["detail"]


async def test_upload_success(client):
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Document indexed successfully."
    assert response.json()["chunks_stored"] > 0


# ── documents ─────────────────────────────────────────────────────────────────

async def test_get_user_docs(client_with_file):
    response = await client_with_file.get(
        "/documents",
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    
    assert response.status_code == 200

    data = response.json()
    docs = data if isinstance(data, list) else data.get("documents", [])
    assert docs[0]["filename"] == "test.txt"


# ── document/{document_name}/text ─────────────────────────────────────────────

async def test_get_doc_text_text_missing(client):
    # Upload but skip indexing → Postgres has doc, Qdrant doesn't
    with patch("routers.document.index_document"):
        await client.post(
            "/upload",
            files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
            headers={"x-user-id": "1", "x-user-role": "user"}
        )

    response = await client.get(
        "/document/test.txt/text",
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Document content missing in vector store."


async def test_get_doc_text_wrong_filename(client_with_file):
    response = await client_with_file.get(
        "/document/123/text",
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


# ── delete document ───────────────────────────────────────────────────────────

async def test_delete_doc_no_file(client):
    response = await client.delete(
        "/document/123",
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


async def test_delete_doc_qdrant_fails(client_with_file):
    with patch("routers.document.delete_points_by_document", return_value=["small_model_collection"]):
        response = await client_with_file.delete(
            "/document/test.txt",
            headers={"x-user-id": "1", "x-user-role": "user"}
        )
    
    assert response.status_code == 500
    assert response.json()["detail"] == "Qdrant deletion failed."


async def test_delete_doc(client_with_file):
    response = await client_with_file.delete(
        "/document/test.txt",
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Document deleted successfully."


# ── Storage limit checks ──────────────────────────────────────────────────────

async def test_upload_owner_role_skips_storage_check(client):
    # owner → limit = -1 → skips GET /internal/storage entirely
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
        headers={"x-user-id": "1", "x-user-role": "owner"}
    )
    assert response.status_code == 200


async def test_upload_storage_service_unavailable(client):
    # user 998 → WireMock returns 503 → raises 503
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
        headers={"x-user-id": "998", "x-user-role": "user"}
    )
    assert response.status_code == 503
    assert "Could not verify storage usage" in response.json()["detail"]


async def test_upload_storage_limit_exceeded(client):
    # user 999 → WireMock returns storage_used: 999999999 → 413
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
        headers={"x-user-id": "999", "x-user-role": "user"}
    )
    assert response.status_code == 413
    body = response.json()["detail"]
    assert body["code"] == "storage_limit_exceeded"
    assert "storage_used" in body
    assert "storage_limit" in body
    assert "file_size" in body


# ── Success path with storage update ──────────────────────────────────────────

async def test_upload_success_patches_storage(client):
    response = await client.post(
        "/upload",
        files={"file": ("test.txt", b"Mars is a red planet.", "text/plain")},
        headers={"x-user-id": "1", "x-user-role": "user"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Document indexed successfully."
    assert isinstance(body["document_id"], int)
    assert body["chunks_stored"] > 0


# ── get_document_text success ─────────────────────────────────────────────────

async def test_get_doc_text_success(client_with_file):
    response = await client_with_file.get(
        "/document/test.txt/text",
        headers={"x-user-id": "1"}
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"
    assert response.json()["text"] != ""


# ── delete success with storage update ────────────────────────────────────────

async def test_delete_doc_success_patches_storage(client_with_file):
    response = await client_with_file.delete(
        "/document/test.txt",
        headers={"x-user-id": "1"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Document deleted successfully."

    # verify removed from postgres
    list_response = await client_with_file.get(
        "/documents",
        headers={"x-user-id": "1"}
    )
    assert len(list_response.json()) == 0