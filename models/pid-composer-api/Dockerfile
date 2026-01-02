# PID Composer API Dockerfile
# P&ID 도면 레이어 합성 및 시각화 서비스

FROM python:3.11-slim

WORKDIR /app

# System dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1
ENV PID_COMPOSER_PORT=5021

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5021/health || exit 1

# Expose port
EXPOSE 5021

# Run
CMD ["python", "api_server.py"]
