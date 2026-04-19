FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

RUN uv pip install --system --no-cache \
    torch==2.6.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

RUN uv pip install --system --no-cache sentence-transformers

COPY services/common ./services/common

COPY services/model_service/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

RUN python -c "\
from sentence_transformers import SentenceTransformer; \
print('Loading small-r2...'); SentenceTransformer('ibm-granite/granite-embedding-small-english-r2'); \
print('Loading english-r2...'); SentenceTransformer('ibm-granite/granite-embedding-english-r2'); \
print('Loading multilingual...'); SentenceTransformer('ibm-granite/granite-embedding-278m-multilingual'); \
print('All models cached.')"

COPY services/model_service/ .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]