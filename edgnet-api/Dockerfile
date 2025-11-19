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

# Copy application code
COPY api_server.py .
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/

# Create directories
RUN mkdir -p /tmp/edgnet/uploads /tmp/edgnet/results /models

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/api/v1/health || exit 1

# Run API server
CMD ["python", "api_server.py"]
