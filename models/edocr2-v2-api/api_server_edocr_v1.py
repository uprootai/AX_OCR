"""
eDOCr v1 API Server
Engineering Drawing OCR microservice (eDOCr v1 implementation)

Port: 5001
Features: Dimension, GD&T, and text extraction from engineering drawings
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from edocr_v1 import init_directories, ocr_router, docs_router
from edocr_v1.services import ocr_service

# =====================
# Logging Setup
# =====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("=" * 70)
    logger.info("eDOCr v1 API Server Starting...")
    logger.info("=" * 70)

    # Initialize directories
    init_directories()

    # Configure GPU
    ocr_service.configure_gpu()

    # Load models
    if ocr_service.edocr_available:
        try:
            ocr_service.load_models()
            logger.info("eDOCr v1 models loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load eDOCr v1 models: {e}")
            raise
    else:
        logger.warning("eDOCr v1 not available - running in mock mode")

    yield

    # Shutdown
    logger.info("Shutting down eDOCr v1 API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="eDOCr v1 API",
    description="Engineering Drawing OCR Service (eDOCr v1)",
    version="1.0.0",
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
    allow_headers=["*"]
)

# Include routers
app.include_router(ocr_router)
app.include_router(docs_router)


# =====================
# Main Entry Point
# =====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
