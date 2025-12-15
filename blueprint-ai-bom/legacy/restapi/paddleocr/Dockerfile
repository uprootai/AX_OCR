FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for PaddleOCR
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgtk-3-0 \
    wget \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install base dependencies first
RUN pip install --no-cache-dir --upgrade pip

# Install core dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    python-multipart==0.0.6 \
    numpy==1.24.3 \
    opencv-python-headless==4.8.1.78 \
    Pillow==10.0.0

# Install PaddleOCR with proper dependencies
RUN pip install --no-cache-dir \
    paddlepaddle==3.2.0 \
    paddleocr

# Copy application
COPY app.py .

# Expose port
EXPOSE 8001

# Run application
CMD ["python", "app.py"]