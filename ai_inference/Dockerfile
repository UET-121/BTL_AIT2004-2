FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update && apt-get install -y \
    fontconfig \
    libfontconfig1 \
    fonts-dejavu-core \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN uv pip install --system "setuptools<82"
RUN uv pip install --system -r /app/pyproject.toml

COPY engine/ ./engine/
COPY streaming/ ./streaming/
COPY Main.py ./

CMD ["python", "Main.py"]
