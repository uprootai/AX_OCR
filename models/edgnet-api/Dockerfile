FROM python:3.10-slim

LABEL maintainer="Uproot AI Team"
LABEL description="EDGNet API - Graph Neural Network Segmentation Service"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
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

# Copy EDGNet source code (included in image for reliability)
COPY edgnet_src/ ./edgnet/

# Copy GraphSAGE trained models to /trained_models
COPY trained_models/ /trained_models/

# Copy application code
COPY api_server.py .
COPY routers/ ./routers/
# models/ contains schemas.py and UNet models
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/
COPY config/ ./config/

# Create directories and clean pycache
RUN mkdir -p /tmp/edgnet/uploads /tmp/edgnet/results && \
    find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# Run API server
CMD ["python", "api_server.py"]
