FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN uv pip install --system --no-cache \
    torch==2.6.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

RUN uv pip install --system --no-cache sentence-transformers

COPY requirements.txt .
RUN uv pip install --system --no-cache --require-hashes -r requirements.txt

RUN python -c "\
from sentence_transformers import SentenceTransformer; \
print('Loading small-r2...'); SentenceTransformer('ibm-granite/granite-embedding-small-english-r2'); \
print('Loading english-r2...'); SentenceTransformer('ibm-granite/granite-embedding-english-r2'); \
print('Loading multilingual...'); SentenceTransformer('ibm-granite/granite-embedding-278m-multilingual'); \
print('All models cached.')"

COPY main.py .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]