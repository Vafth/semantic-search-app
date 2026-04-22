from fastapi import APIRouter, Request, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
import httpx

from core.config import settings
from core.security import ClaimsDep, build_internal_headers

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _json_response(response: httpx.Response) -> JSONResponse:
    return JSONResponse(
        status_code = response.status_code,
        content     = response.json(),
    )

async def _verify_user(claims: ClaimsDep, client: httpx.AsyncClient) -> None:
    """
    Calls user_service internal endpoint to confirm user exists and is active.
    """
    resp = await client.get(
        f"{settings.USER_SERVICE_URL}/internal/verify/{claims.sub}",
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "User verification failed",
        )


# ── Frontend ──────────────────────────────────────────────────────────────────

@router.get("/")
async def frontend():
    return FileResponse("/app/index.html")


# ── Auth passthrough ──────────────────────────────────────────────────────────

@router.post("/auth/login")
@router.post("/auth/register")
async def auth_passthrough(request: Request):
    
    path = request.url.path.removeprefix("/auth")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.request(
            method  = request.method,
            url     = f"{settings.USER_SERVICE_URL}{path}",
            content = await request.body(),
            headers = {"Content-Type": request.headers.get("Content-Type", "application/json")},
        )
    return _json_response(resp)


# ── User service (authenticated) ─────────────────────────────────────────────

@router.get("/auth/me")
async def me(claims: ClaimsDep):
    
    internal_headers = build_internal_headers(claims)
    async with httpx.AsyncClient(timeout=10.0) as client:
        await _verify_user(claims, client)
        
        resp = await client.get(
            f"{settings.USER_SERVICE_URL}/me",
            headers = internal_headers,
        )
    
    return _json_response(resp)


@router.get("/admin/users")
async def list_users(claims: ClaimsDep):
    
    internal_headers = build_internal_headers(claims)
    async with httpx.AsyncClient(timeout=10.0) as client:
        await _verify_user(claims, client)
    
        resp = await client.get(
            f"{settings.USER_SERVICE_URL}/users",
            headers = internal_headers,
        )
    
    return _json_response(resp)


@router.patch("/admin/users/{user_id}")
async def update_user(user_id: int, request: Request, claims: ClaimsDep):
    
    internal_headers = build_internal_headers(claims)
    async with httpx.AsyncClient(timeout=10.0) as client:
        await _verify_user(claims, client)
    
        resp = await client.patch(
            f"{settings.USER_SERVICE_URL}/users/{user_id}",
            content = await request.body(),
            headers = {**internal_headers, "Content-Type": "application/json"},
        )
    
    return _json_response(resp)


# ── Document service ──────────────────────────────────────────────────────────

@router.post("/api/upload")
async def upload(claims: ClaimsDep, file: UploadFile = File(...)):
    
    internal_headers = build_internal_headers(claims)
    content = await file.read()

    async with httpx.AsyncClient(timeout=None) as client:
        await _verify_user(claims, client)
    
        resp = await client.post(
            f"{settings.DOCUMENT_SERVICE_URL}/upload",
            files   = {"file": (file.filename, content, file.content_type)},
            headers = internal_headers,
        )
    
    return _json_response(resp)


@router.get("/api/documents")
async def list_documents(claims: ClaimsDep):
    
    internal_headers = build_internal_headers(claims)
    async with httpx.AsyncClient(timeout=10.0) as client:
        await _verify_user(claims, client)
    
        resp = await client.get(
            f"{settings.DOCUMENT_SERVICE_URL}/documents",
            headers = internal_headers,
        )
    
    return _json_response(resp)


@router.get("/api/document/{filename}/text")
async def get_document_text(filename: str, claims: ClaimsDep):
        
    internal_headers = build_internal_headers(claims)
    async with httpx.AsyncClient(timeout=10.0) as client:
        await _verify_user(claims, client)
    
        resp = await client.get(
            f"{settings.DOCUMENT_SERVICE_URL}/document/{filename}/text",
            headers = internal_headers,
        )
    
    return _json_response(resp)


@router.delete("/api/document/{filename}")
async def delete_document(filename: str, claims: ClaimsDep):
    
    internal_headers = build_internal_headers(claims)
    async with httpx.AsyncClient(timeout=300.0) as client:
        await _verify_user(claims, client)
    
        resp = await client.delete(
            f"{settings.DOCUMENT_SERVICE_URL}/document/{filename}",
            headers = internal_headers,
        )
    
    return _json_response(resp)


# ── Search service ────────────────────────────────────────────────────────────

@router.get("/api/search")
async def search(request: Request, claims: ClaimsDep):
    
    internal_headers = build_internal_headers(claims)
    async with httpx.AsyncClient(timeout=300.0) as client:
        await _verify_user(claims, client)
        
        resp = await client.get(
            f"{settings.SEARCH_SERVICE_URL}/search",
            params  = dict(request.query_params),
            headers = internal_headers,
        )
    
    return _json_response(resp)