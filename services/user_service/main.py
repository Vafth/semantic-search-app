import logging
import sys
from contextlib import asynccontextmanager
 
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
 
from database import create_db_and_tables
from routers.user import router as user_router
from routers.internal import router as internal_router


# ── Logger Init ───────────────────────────────────────────────────────────────
logger = logging.getLogger("user_service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PostgreSQL tables...")
    await create_db_and_tables()
    logger.info("User Service started.")
    yield
    logger.info("Shutting down User Service...")


app = FastAPI(
    title="User Service",
    version="0.1.0",
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
app.include_router(user_router)
app.include_router(internal_router)

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "user-service"}