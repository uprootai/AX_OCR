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

# Copy eDOCr2 source code (included in image for reliability)
COPY edocr2_src/ ./edocr2/

# Copy eDOCr2 models to /models directory
COPY edocr2_src/models/ /models/

# Copy application code
COPY api_server.py .
COPY routers/ ./routers/
COPY gpu_preprocessing.py .
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/

# Create directories
RUN mkdir -p /tmp/edocr2/uploads /tmp/edocr2/results

# Configure CUDA library path for CuPy
RUN echo '/usr/local/lib/python3.10/site-packages/nvidia/cuda_nvrtc/lib' > /etc/ld.so.conf.d/cuda-nvrtc.conf && \
    echo '/usr/local/lib/python3.10/site-packages/nvidia/cuda_runtime/lib' >> /etc/ld.so.conf.d/cuda-nvrtc.conf && \
    echo '/usr/local/lib/python3.10/site-packages/nvidia/cublas/lib' >> /etc/ld.so.conf.d/cuda-nvrtc.conf && \
    ldconfig

# Expose port (5002 for v2 API)
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/api/v2/health || exit 1

# Run API server
CMD ["python", "api_server.py"]
