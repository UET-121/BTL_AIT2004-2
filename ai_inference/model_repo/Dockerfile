
FROM nvcr.io/nvidia/tensorrt:24.03-py3

WORKDIR /app

RUN pip install --no-cache-dir onnx

COPY . /app/

# Chạy luồng tự động build
CMD ["bash", "scripts/auto_build.sh"]