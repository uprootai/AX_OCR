FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api_server.py .
COPY config/ ./config/
COPY models/ ./models/
COPY services/ ./services/
COPY routers/ ./routers/
COPY utils/ ./utils/

# Create directories
RUN mkdir -p /tmp/yolo-api/uploads /tmp/yolo-api/results /app/models

# Download YOLOv11n as default model (for prototype)
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"

# Copy GPU auto-detection entrypoint script (if exists)
# 참조: scripts/docker-gpu-entrypoint.sh를 빌드 전에 복사하거나 volume mount
COPY docker-gpu-entrypoint.sh /usr/local/bin/docker-gpu-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-gpu-entrypoint.sh

# Environment: USE_GPU=auto|true|false (default: auto)
ENV USE_GPU=auto

# Expose port
EXPOSE 5005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5005/api/v1/health || exit 1

# Use GPU entrypoint with fallback
ENTRYPOINT ["/bin/bash", "-c", "if [ -x /usr/local/bin/docker-gpu-entrypoint.sh ]; then exec /usr/local/bin/docker-gpu-entrypoint.sh \"$@\"; else exec \"$@\"; fi", "--"]
CMD ["python", "api_server.py"]
