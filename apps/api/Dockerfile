FROM python:3.11-slim

# System deps for some Python packages (e.g., pillow, opencv, onnxruntime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CACHE OPTIMIZATION: Install heavy ML dependencies FIRST.
# This creates a cached layer for the 4GB of downloads, preventing it from
# being rebuilt every time requirements.txt is modified.
# Cài đặt PyTorch với CUDA 12.4 để tương thích với GPU Driver hiện tại
RUN pip install --no-cache-dir --default-timeout=1000 torch torchvision --index-url https://download.pytorch.org/whl/cu124
RUN pip install --no-cache-dir --default-timeout=1000 onnxruntime-gpu

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --default-timeout=1000 -r /app/requirements.txt

COPY . /app

RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
