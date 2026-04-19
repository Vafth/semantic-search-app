import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers.embed import router
from core.processor import manager

logger = logging.getLogger("model_service")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    stream=sys.stdout
)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    logger.info("Starting Model Service...")
    manager.load_all()
    
    yield
    logger.info("Shutting down Model Service...")
    manager.models.clear()


app = FastAPI(title="Model Service", lifespan=lifespan)

app.include_router(router)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "model-service", "models_loaded": list(manager.models.keys())}