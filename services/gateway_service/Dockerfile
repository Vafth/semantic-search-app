FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gettext && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY services/common ./services/common

COPY services/gateway_service/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY services/gateway_service/ .
COPY frontend/index.html /app/index.html.template


EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["/bin/sh", "-c", "envsubst '${GATEWAY_URL}' < /app/index.html.template > /app/index.html && uvicorn main:app --host 0.0.0.0 --port 8080"]