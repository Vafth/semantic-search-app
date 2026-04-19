import re
import httpx

from core.config import settings

def clean_text(text: str) -> str:
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[citation needed\]', '', text)
    text = re.sub(r'\[c\]', '', text)
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
    text = re.sub(r'\n([A-Z][^\n]{3,80})\n', r'. \1. ', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n+', ' ', text)
    return text.strip()

def split_into_sentences(text: str) -> list[str]:
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if len(s.strip()) > 10]

def chunk_text(text: str) -> list[str]:
    text = clean_text(text)
    sentences = split_into_sentences(text)
    if not sentences:
        raise ValueError("No sentences found in the uploaded file.")
    
    chunks = []
    step = settings.CHUNK_SIZE - settings.CHUNK_OVERLAP
    for i in range(0, len(sentences), step):
        chunk = " ".join(sentences[i : i + settings.CHUNK_SIZE])
        if chunk:
            chunks.append(chunk)
    return chunks

async def get_embeddings(texts: list[str], model: str) -> list[list[float]]:
    batch_size = 16 if model in ("normal_model", "multilingual_model") else 32
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(
            f"{settings.MODEL_SERVICE_URL}/embed",
            json={"texts": texts, "model": model, "batch_size": batch_size},
        )
        response.raise_for_status()
        return response.json()["vectors"]