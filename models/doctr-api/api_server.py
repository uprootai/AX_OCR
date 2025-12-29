"""
DocTR API Server
Document Text Recognition - 2-stage pipeline (Detection + Recognition)

Port: 5014
GitHub: https://github.com/mindee/doctr
"""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from schemas import HealthResponse
from services import load_doctr_model, is_gpu_available
from routers import ocr_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("DOCTR_PORT", "5014"))


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on server startup"""
    try:
        load_doctr_model()
    except Exception as e:
        logger.warning(f"Model pre-loading failed (will load on first request): {e}")
    yield
    logger.info("Shutting down DocTR API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="DocTR API",
    description="DocTR - Document Text Recognition, 2-stage pipeline",
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
        service="doctr-api",
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
    logger.info(f"Starting DocTR API on port {API_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
