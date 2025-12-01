# ESRGAN API Dockerfile
# CPU 버전 - GPU 버전은 nvidia/cuda 베이스 이미지 사용

FROM python:3.10-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (CPU version)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: Install Real-ESRGAN for better quality
# Uncomment below for Real-ESRGAN support (requires more disk space)
# RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
# RUN pip install --no-cache-dir basicsr realesrgan

# Copy application
COPY . .

# Create weights directory
RUN mkdir -p /app/weights

# Expose port
EXPOSE 5010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5010/health || exit 1

# Run
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "5010"]
