"""
OCR Ensemble API Server
PPT Slide 11 [HOW-2] Multi-engine Ensemble Weighted Voting System

eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%

Merges OCR results from multiple engines using weighted voting
"""
import os
import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from schemas import HealthResponse
from services import get_engine_urls
from routers import ocr_router
from routers.ocr_router import health_check_all_engines

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ENSEMBLE_API_PORT = int(os.getenv("ENSEMBLE_API_PORT", "5011"))

# Default weights (from PPT specification)
DEFAULT_WEIGHTS = {
    "edocr2": 0.40,
    "paddleocr": 0.35,
    "tesseract": 0.15,
    "trocr": 0.10
}


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="OCR Ensemble API",
    description="Multi-engine Ensemble OCR - 4 OCR engines with weighted voting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    status, engines = await health_check_all_engines()

    return HealthResponse(
        status=status,
        service="OCR Ensemble API",
        version="1.0.0",
        engines=engines,
        timestamp=datetime.now().isoformat()
    )


# =====================
# Main
# =====================

if __name__ == "__main__":
    engine_urls = get_engine_urls()

    logger.info(f"Starting OCR Ensemble API on port {ENSEMBLE_API_PORT}")
    logger.info(f"Default weights: {DEFAULT_WEIGHTS}")
    logger.info("Engine URLs:")
    for name, url in engine_urls.items():
        logger.info(f"  - {name}: {url}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=ENSEMBLE_API_PORT,
        log_level="info"
    )
