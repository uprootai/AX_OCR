"""
EDGNet API Server
그래프 신경망 기반 도면 세그멘테이션 마이크로서비스

포트: 5012
기능: 도면을 Contour/Text/Dimension 컴포넌트로 분류
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import torch

from models.schemas import HealthResponse
from services import (
    EDGNetInferenceService,
    UNetInferenceService,
    check_edgnet_availability,
    check_model_exists,
    check_unet_model_exists,
    set_services
)
from routers import segment_router

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================
# Configuration
# =====================

UPLOAD_DIR = Path("/tmp/edgnet/uploads")
RESULTS_DIR = Path("/tmp/edgnet/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Model paths
GRAPHSAGE_MODEL_PATH = Path("/trained_models/graphsage_dimension_classifier.pth")
UNET_MODEL_PATH = Path("/app/models/edgnet_large.pth")


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate EDGNet pipeline and UNet model on startup"""
    logger.info("Starting EDGNet API...")

    # Auto-detect GPU availability
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")
    if device == 'cuda':
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    edgnet_service = None
    unet_service = None

    # ====== EDGNet (GraphSAGE) Initialization ======
    logger.info("Validating EDGNet pipeline...")
    edgnet_available = check_edgnet_availability()
    graphsage_exists = check_model_exists(str(GRAPHSAGE_MODEL_PATH))

    if not edgnet_available:
        logger.error("EDGNet pipeline NOT available")
    else:
        logger.info("EDGNet pipeline available")

        if not graphsage_exists:
            logger.error(f"GraphSAGE model NOT found: {GRAPHSAGE_MODEL_PATH}")
        else:
            logger.info(f"GraphSAGE model found: {GRAPHSAGE_MODEL_PATH}")

            # Initialize EDGNet service
            edgnet_service = EDGNetInferenceService(
                model_path=str(GRAPHSAGE_MODEL_PATH),
                device=device
            )

            try:
                edgnet_service.load_model()
                logger.info("✅ EDGNet GraphSAGE model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load EDGNet model: {e}")
                edgnet_service = None

    # ====== UNet Initialization ======
    logger.info("Validating UNet model...")
    unet_exists = check_unet_model_exists(str(UNET_MODEL_PATH))

    if not unet_exists:
        logger.warning(f"UNet model NOT found: {UNET_MODEL_PATH}")
    else:
        logger.info(f"UNet model found: {UNET_MODEL_PATH}")

        # Initialize UNet service
        unet_service = UNetInferenceService(
            model_path=str(UNET_MODEL_PATH),
            device=device,
            image_size=512
        )

        try:
            unet_service.load_model()
            logger.info("✅ UNet model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load UNet model: {e}")
            unet_service = None

    # Set global state
    set_services(edgnet_service, unet_service)

    logger.info("EDGNet API startup complete")

    yield  # Application runs here

    # Shutdown
    logger.info("Shutting down EDGNet API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="EDGNet API",
    description="Engineering Drawing Graph Neural Network Segmentation Service",
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
app.include_router(segment_router)


# =====================
# Health & Root Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": "EDGNet API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns the current health status of the EDGNet API service.
    Checks both GraphSAGE and UNet models availability.
    """
    graphsage_ready = check_edgnet_availability() and check_model_exists(str(GRAPHSAGE_MODEL_PATH))
    unet_ready = check_unet_model_exists(str(UNET_MODEL_PATH))

    # Service is healthy if at least one model is available
    is_ready = graphsage_ready or unet_ready
    status = "healthy" if is_ready else "degraded"

    return {
        "status": status,
        "service": "EDGNet API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# =====================
# Main
# =====================

if __name__ == "__main__":
    port = int(os.getenv("EDGNET_PORT", 5012))

    logger.info(f"Starting EDGNet API on port {port}")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )
