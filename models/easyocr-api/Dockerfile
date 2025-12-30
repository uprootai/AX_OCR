FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY api_server.py .
COPY routers/ ./routers/
COPY services/ ./services/

# Environment
ENV PYTHONPATH=/app
ENV EASYOCR_PORT=5015
ENV EASYOCR_GPU=false

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:5015/health || exit 1

EXPOSE 5015

CMD ["python", "api_server.py"]
