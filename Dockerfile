# Stage 1: Build SvelteKit static frontend
FROM node:22-slim AS frontend-builder
WORKDIR /app/frontend
COPY ["Chat Interface/package.json", "Chat Interface/package-lock.json", "./"]
RUN npm ci --engine-strict=false
COPY ["Chat Interface/", "./"]
RUN npm run build

# Stage 2: Python FastAPI + LangGraph + Mem0 runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    MEM0_TELEMETRY=false

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Pre-cache embedding model so container startup does not wait on HuggingFace Hub
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY config.yaml run.py ./
COPY src/ ./src/
COPY knowledge-base/ ./knowledge-base/
COPY --from=frontend-builder ["/app/frontend/build", "./Chat Interface/build"]

RUN mkdir -p /app/data /app/logs && python run.py --check

EXPOSE 8000

CMD ["python", "run.py", "--mode", "server"]
