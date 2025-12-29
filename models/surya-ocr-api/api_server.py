"""
Surya OCR API Server
90+ language support, layout analysis, table recognition

Port: 5013
GitHub: https://github.com/datalab-to/surya
"""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from schemas import HealthResponse
from services import load_surya_models, is_gpu_available
from routers import ocr_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("SURYA_OCR_PORT", "5013"))


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on server startup"""
    try:
        load_surya_models()
    except Exception as e:
        logger.warning(f"Model pre-loading failed (will load on first request): {e}")
    yield
    logger.info("Shutting down Surya OCR API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Surya OCR API",
    description="Surya OCR - 90+ language support, layout analysis, table recognition",
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
        service="surya-ocr-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        gpu_available=is_gpu_available()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """Health check (v1 path)"""
    return await health_check()


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting Surya OCR API on port {API_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
