#!/usr/bin/env python3
"""
PaddleOCR API Server
Engineering Drawing Text Recognition using PaddleOCR
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models.schemas import HealthResponse
from services.ocr import PaddleOCRService, set_ocr_service, get_ocr_service, is_service_ready
from routers import ocr_router

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PADDLEOCR_PORT", "5006"))
USE_GPU = os.getenv("USE_GPU", "false").lower() == "true"
LANG = os.getenv("OCR_LANG", "en")


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load PaddleOCR model on startup, cleanup on shutdown"""
    # Startup
    logger.info(f"Starting PaddleOCR API on port {PORT}")
    ocr_service = PaddleOCRService()
    ocr_service.load_model()
    set_ocr_service(ocr_service)

    yield

    # Shutdown
    logger.info("Shutting down PaddleOCR API Server")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="PaddleOCR API",
    description="Drawing Text Recognition using PaddleOCR",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
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

@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Supports both /health and /api/v1/health for compatibility
    """
    ocr_service = get_ocr_service()
    return HealthResponse(
        status="healthy" if is_service_ready() else "unhealthy",
        service="paddleocr-api",
        version="1.0.0",
        gpu_available=USE_GPU,
        model_loaded=is_service_ready(),
        lang=LANG
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "PaddleOCR API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/v1/health",
            "ocr": "/api/v1/ocr",
            "docs": "/docs"
        }
    }


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting PaddleOCR API server on port {PORT}")
    logger.info(f"GPU enabled: {USE_GPU}")
    logger.info(f"Language: {LANG}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
