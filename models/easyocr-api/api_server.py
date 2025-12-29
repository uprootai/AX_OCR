"""
EasyOCR API Server
80+ language support, easy to use, CPU/GPU support

Port: 5015
GitHub: https://github.com/JaidedAI/EasyOCR
"""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from schemas import HealthResponse
from services import get_easyocr_reader, is_gpu_available, get_use_gpu
from routers import ocr_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("EASYOCR_PORT", "5015"))


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load default language model on startup"""
    try:
        # Pre-load Korean+English model
        get_easyocr_reader(["ko", "en"], gpu=get_use_gpu())
    except Exception as e:
        logger.warning(f"Default model pre-loading failed: {e}")
    yield
    logger.info("Shutting down EasyOCR API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="EasyOCR API",
    description="EasyOCR - 80+ language support, easy to use",
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
# Health Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    return HealthResponse(
        status="healthy",
        service="easyocr-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        gpu_available=is_gpu_available(),
        gpu_enabled=get_use_gpu()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """Health check (v1 path)"""
    return await health_check()


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting EasyOCR API on port {API_PORT}, GPU: {get_use_gpu()}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
