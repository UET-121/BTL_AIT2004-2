FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY shared_lib /app/shared_lib
COPY worker /app/worker

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN uv pip install --system -e /app/shared_lib
RUN uv pip install --system -r /app/worker/pyproject.toml

CMD ["python", "-m", "worker.src.consumer"]