# ESRGAN API Dockerfile
# GPU 버전 - PyTorch 공식 이미지 기반

FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Real-ESRGAN then force numpy downgrade for PyTorch 2.0 compatibility
RUN pip install --no-cache-dir basicsr==1.4.2 realesrgan==0.3.0 && \
    pip install --no-cache-dir --force-reinstall "numpy<2"

# Copy application
COPY api_server.py .
COPY schemas.py .
COPY routers/ ./routers/
COPY services/ ./services/

# Create weights directory
RUN mkdir -p /app/weights

# Expose port
EXPOSE 5010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5010/health || exit 1

# Run
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "5010"]
