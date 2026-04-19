import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import create_db_and_tables
from qdrant import init_qdrant, get_qdrant_client
from routers import document


# ── Logger Init ───────────────────────────────────────────────────────────────
logger = logging.getLogger("document_service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting Document Service...")
    
    logger.info("Initializing PostgreSQL...")
    await create_db_and_tables()

    logger.info("Initializing Qdrant...")
    init_qdrant()

    yield

    logger.info("Shutting down Document Service...")
    get_qdrant_client().close()


app = FastAPI(
    title="Document Service",
    version="0.2.0",
    lifespan=lifespan
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handling ────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(document.router)

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "document-service"}