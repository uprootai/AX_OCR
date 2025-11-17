FROM python:3.10-slim

LABEL maintainer="Uproot AI Team"
LABEL description="eDOCr2 API - Engineering Drawing OCR Service"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-nor \
    tesseract-ocr-swe \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api_server.py .
COPY gpu_preprocessing.py .

# Create directories
RUN mkdir -p /tmp/edocr2/uploads /tmp/edocr2/results /models

# Configure CUDA library path for CuPy
RUN echo '/usr/local/lib/python3.10/site-packages/nvidia/cuda_nvrtc/lib' > /etc/ld.so.conf.d/cuda-nvrtc.conf && \
    echo '/usr/local/lib/python3.10/site-packages/nvidia/cuda_runtime/lib' >> /etc/ld.so.conf.d/cuda-nvrtc.conf && \
    echo '/usr/local/lib/python3.10/site-packages/nvidia/cublas/lib' >> /etc/ld.so.conf.d/cuda-nvrtc.conf && \
    ldconfig

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5001/api/v1/health || exit 1

# Run API server
CMD ["python", "api_server.py"]
