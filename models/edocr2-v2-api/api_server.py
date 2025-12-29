"""
eDOCr2 API Server
Engineering Drawing OCR Processing Microservice

Port: 5002
Features: Extract dimensions, GD&T, and text from engineering drawings
"""
import os

# CRITICAL: Force CPU-only mode for TensorFlow
# The GPU XLA/JIT compilation has libdevice issues causing Floor operations to fail
# Using CPU is more stable and the OCR model is small enough that CPU is sufficient
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Hide all GPUs from TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TF logging

import tensorflow as tf

# Verify no GPU is visible
print(f"TensorFlow GPUs visible: {tf.config.list_physical_devices('GPU')}")

# Force eager execution mode (no graph compilation)
tf.config.run_functions_eagerly(True)

import logging
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models.schemas import HealthResponse
from services.ocr_processor import load_models
from routers import ocr_router

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_DIR = Path("/tmp/edocr2/uploads")
RESULTS_DIR = Path("/tmp/edocr2/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup, cleanup on shutdown"""
    # Startup
    logger.info("Starting eDOCr2 API...")
    load_models()
    logger.info("eDOCr2 API ready")

    yield

    # Shutdown
    logger.info("Shutting down eDOCr2 API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="eDOCr2 v2 API",
    description="Engineering Drawing OCR Service",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ocr_router)


# =====================
# Health Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": "eDOCr2 v2 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/health", response_model=HealthResponse)
@app.get("/api/v2/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "eDOCr2 v2 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# =====================
# Main
# =====================

if __name__ == "__main__":
    port = int(os.getenv("EDOCR2_PORT", 5001))
    workers = int(os.getenv("EDOCR2_WORKERS", 4))

    logger.info(f"Starting eDOCr2 API on port {port} with {workers} workers")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
