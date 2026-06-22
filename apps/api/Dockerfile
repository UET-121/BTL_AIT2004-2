FROM python:3.11-slim

# System deps for some Python packages (e.g., pillow, opencv, onnxruntime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
# Pre-install CPU-only PyTorch to bypass massive CUDA dependencies (>1.5GB) and speed up build
RUN pip install --no-cache-dir --default-timeout=100 torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --default-timeout=100 -r /app/requirements.txt

COPY . /app

RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
