FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY shared_lib /app/shared_lib
COPY backend /app/backend

RUN uv pip install --system -e /app/shared_lib
RUN uv pip install --system -r /app/backend/pyproject.toml

EXPOSE 8000

CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]