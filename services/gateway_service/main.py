from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

import httpx
import os

DOC_URL    = os.getenv("DOC_SERVICE_URL",    "http://document-service:8001")
SEARCH_URL = os.getenv("SEARCH_SERVICE_URL", "http://search-service:8002")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"},
    )


# -- Endpoints ----
# -- Frontend endpoint ----

@app.get("/")
async def frontend():
    return FileResponse("/app/index.html")

# -- Search service endpoints ----

@app.get("/api/search")
async def search(request: Request):
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.get(
            f"{SEARCH_URL}/search",
            params=dict(request.query_params),
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    
# -- Document service endpoints ----

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    
    content = await file.read()
    
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(
            f"{DOC_URL}/upload",
            files={"file": (file.filename, content, file.content_type)},
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.get("/api/documents")
async def list_documents():
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{DOC_URL}/documents")
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    
@app.get("/api/document/{document_id}/text")
async def get_document_text(document_id: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{DOC_URL}/document/{document_id}/text")
        return JSONResponse(status_code=response.status_code, content=response.json())
    
@app.delete("/api/document/{id}")
async def delete_document(id: str):
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.delete(f"{DOC_URL}/document/{id}")
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.get("/health")
def health():
    return {"status": "ok", "service": "search-service"}