import logging
from sentence_transformers import SentenceTransformer, util
from core.config import settings

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.models: dict[str, SentenceTransformer] = {}

    def load_all(self):
        logger.info("Loading IBM Granite models into RAM...")
        self.models["small_model"]        = SentenceTransformer(settings.SMALL_MODEL_ID)
        self.models["normal_model"]       = SentenceTransformer(settings.NORMAL_MODEL_ID)
        self.models["multilingual_model"] = SentenceTransformer(settings.MULTI_MODEL_ID)
        logger.info("All models loaded successfully.")

    def get_model(self, name: str) -> SentenceTransformer:
        if name not in self.models:
            raise ValueError(f"Model {name} is not loaded.")
        return self.models[name]

    def compute_similarity(self, model_name: str, text_a: str, text_b: str) -> float:
        model = self.get_model(model_name)
        vecs = model.encode([text_a, text_b], normalize_embeddings=True)
        score = float(util.cos_sim(vecs[0], vecs[1]).item())
        return round(max(0.0, min(1.0, score)), 4)

manager = ModelManager()