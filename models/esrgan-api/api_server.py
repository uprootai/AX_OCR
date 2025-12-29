"""
ESRGAN (Real-ESRGAN) API Server
PPT Slide 9 [HOW-1] Preprocessing Enhancement ESRGAN Upscaling

Upscale low-resolution/low-quality scanned drawings by 4x to improve OCR accuracy
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
    set_upsampler,
    is_model_loaded,
    is_realesrgan_available,
    get_device
)
from routers import upscale_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ESRGAN_API_PORT = int(os.getenv("ESRGAN_API_PORT", "5010"))


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on server startup"""
    logger.info("Starting ESRGAN API...")

    upsampler = load_model()
    set_upsampler(upsampler)

    if upsampler:
        logger.info("✅ Real-ESRGAN model loaded")
    else:
        logger.warning("⚠️ Using fallback upscaling (Lanczos4)")

    yield

    logger.info("Shutting down ESRGAN API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="ESRGAN API",
    description="Real-ESRGAN based image upscaling API - preprocessing for low-quality drawings",
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
app.include_router(upscale_router)


# =====================
# Health Endpoint
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    return HealthResponse(
        status="healthy",
        service="ESRGAN API",
        version="1.0.0",
        realesrgan_available=is_realesrgan_available(),
        model_loaded=is_model_loaded(),
        device=get_device(),
        timestamp=datetime.now().isoformat()
    )


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting ESRGAN API on port {ESRGAN_API_PORT}")
    logger.info(f"Device: {get_device()}")
    logger.info(f"Real-ESRGAN available: {is_realesrgan_available()}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=ESRGAN_API_PORT,
        log_level="info"
    )
