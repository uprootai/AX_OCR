FROM python:3.10-slim

LABEL maintainer="Uproot AI Team"
LABEL description="Gateway API - Orchestration Service"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api_server.py cost_estimator.py pdf_generator.py advanced_features.py .

# Copy refactored modules
COPY models/ ./models/
COPY utils/ ./utils/
COPY services/ ./services/

# Create directories
RUN mkdir -p /tmp/gateway/uploads /tmp/gateway/results

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run API server
CMD ["python", "api_server.py"]
