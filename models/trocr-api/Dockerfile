FROM python:3.10-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download model (optional - uncomment to include in image)
# RUN python -c "from transformers import TrOCRProcessor, VisionEncoderDecoderModel; \
#     TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed'); \
#     VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')"

# Copy application
COPY api_server.py .
COPY schemas.py .
COPY routers/ ./routers/
COPY services/ ./services/

# Create cache directory for models
RUN mkdir -p /root/.cache/huggingface

# Expose port
EXPOSE 5009

# Health check
HEALTHCHECK --interval=30s --timeout=30s --retries=3 \
    CMD curl -f http://localhost:5009/health || exit 1

# Run
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "5009"]
