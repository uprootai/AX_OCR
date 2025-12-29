"""
Skin Model API Server
Geometric Tolerance Prediction and Manufacturability Analysis Microservice

Port: 5003
Features: FEM-based tolerance prediction, GD&T validation, assemblability assessment
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import models
from models.schemas import HealthResponse

# Import routers
from routers import tolerance_router


# Logging setup
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
    """Server startup and shutdown lifecycle"""
    logger.info("Starting Skin Model API...")
    logger.info("Tolerance prediction service initialized")
    yield
    logger.info("Shutting down Skin Model API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Skin Model API",
    description="Geometric Tolerance Prediction and Manufacturability Analysis Service",
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
app.include_router(tolerance_router)


# =====================
# Health Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": "Skin Model API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns the current health status of the Skin Model API service.
    """
    return {
        "status": "healthy",
        "service": "Skin Model API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# =====================
# Main
# =====================

if __name__ == "__main__":
    port = int(os.getenv("SKINMODEL_PORT", 5003))
    workers = int(os.getenv("SKINMODEL_WORKERS", 2))

    logger.info(f"Starting Skin Model API on port {port} with {workers} workers")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
