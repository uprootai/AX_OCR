"""
Tesseract OCR API Server
PPT Slide 11 [HOW-2] Multi-Engine Ensemble Tesseract Engine

eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%
"""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from schemas import HealthResponse
from services import is_tesseract_available, get_tesseract_version
from routers import ocr_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TESSERACT_API_PORT = int(os.getenv("TESSERACT_API_PORT", "5008"))


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Server startup and shutdown lifecycle"""
    logger.info("Starting Tesseract OCR API...")

    if is_tesseract_available():
        version = get_tesseract_version()
        logger.info(f"Tesseract version: {version}")
    else:
        logger.warning("Tesseract is not available")

    yield

    logger.info("Shutting down Tesseract OCR API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Tesseract OCR API",
    description="Tesseract based OCR API - Multi-Engine Ensemble Component",
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
    allow_headers=["*"],
)

# Include routers
app.include_router(ocr_router)


# =====================
# Health Endpoint
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    return HealthResponse(
        status="healthy" if is_tesseract_available() else "degraded",
        service="Tesseract OCR API",
        version="1.0.0",
        tesseract_available=is_tesseract_available(),
        tesseract_version=get_tesseract_version(),
        timestamp=datetime.now().isoformat()
    )


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting Tesseract OCR API on port {TESSERACT_API_PORT}")
    logger.info(f"Tesseract available: {is_tesseract_available()}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=TESSERACT_API_PORT,
        log_level="info"
    )
