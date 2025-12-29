"""
TrOCR API Server
Microsoft TrOCR (Transformer-based OCR) - PPT Slide 11 [HOW-2] Multi-Engine Ensemble

eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%

TrOCR excels at Scene Text Recognition, useful for handwriting-style text in drawings
"""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from schemas import HealthResponse
from services import (
    load_model,
    set_processor,
    set_model,
    is_model_loaded,
    is_trocr_available,
    get_device,
    get_model_name,
)
from routers import ocr_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TROCR_API_PORT = int(os.getenv("TROCR_API_PORT", "5009"))


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on server startup"""
    logger.info("Starting TrOCR API...")

    processor, model = load_model()
    set_processor(processor)
    set_model(model)

    if model is not None:
        logger.info("TrOCR model loaded successfully")
    else:
        logger.warning("TrOCR model failed to load")

    yield

    logger.info("Shutting down TrOCR API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="TrOCR API",
    description="Microsoft TrOCR (Transformer OCR) API - Multi-Engine Ensemble Component",
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
        status="healthy" if is_model_loaded() else "degraded",
        service="TrOCR API",
        version="1.0.0",
        trocr_available=is_trocr_available(),
        model_loaded=is_model_loaded(),
        model_name=get_model_name(),
        device=get_device(),
        timestamp=datetime.now().isoformat()
    )


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting TrOCR API on port {TROCR_API_PORT}")
    logger.info(f"Model: {get_model_name()}, Device: {get_device()}")
    logger.info(f"TrOCR available: {is_trocr_available()}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=TROCR_API_PORT,
        log_level="info"
    )
