"""
Gateway API Server
Integrated orchestration and workflow management microservice

Port: 8000
Features: Pipeline integration, quote generation, workflow management

Refactored: 2025-12-31
- Moved endpoints to dedicated routers (process, quote, download)
- Removed duplicate function definitions (already in utils/services)
- Lines: 2044 -> ~350
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models import (
    HealthResponse, ProcessData,
    YOLOResults, OCRResults, SegmentationResults, ToleranceResult,
    QuoteData, CostBreakdown,
    DetectionResult, DimensionData, ComponentData
)
from api_registry import get_api_registry
from routers import (
    admin_router, api_key_router, gpu_config_router, docker_router, results_router,
    container_router, spec_router, registry_router, workflow_router, config_router,
    process_router, quote_router, download_router
)
from routers.admin_router import set_api_registry
from constants import init_directories

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =====================
# Configuration
# =====================

EDOCR_V2_URL = os.getenv("EDOCR_V2_URL", "http://edocr2-v2-api:5002")
EDOCR2_URL = os.getenv("EDOCR2_URL", EDOCR_V2_URL)
EDGNET_URL = os.getenv("EDGNET_URL", "http://edgnet-api:5002")
SKINMODEL_URL = os.getenv("SKINMODEL_URL", "http://skinmodel-api:5003")
KNOWLEDGE_API_URL = os.getenv("KNOWLEDGE_API_URL", "http://knowledge-api:5007")

# Directory initialization (SSOT: constants/directories.py)
init_directories()


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("=" * 70)
    logger.info("Gateway API Starting")
    logger.info("=" * 70)

    registry = get_api_registry()
    set_api_registry(registry)

    # API auto-discovery
    logger.info("API auto-discovery starting...")

    docker_hosts = [
        "yolo-api",
        "paddleocr-api",
        "edocr2-v2-api",
        "edgnet-api",
        "skinmodel-api",
    ]

    await registry.discover_apis(host="localhost")

    for host in docker_hosts:
        try:
            apis = await registry.discover_apis(host=host)
            if apis:
                logger.info(f"{host}: {len(apis)} APIs found")
        except Exception as e:
            logger.debug(f"{host} discovery failed: {e}")

    registry.start_health_check_background()

    # Start result cleanup scheduler
    try:
        from utils.result_manager import start_cleanup_scheduler
        start_cleanup_scheduler()
    except ImportError:
        logger.warning("Result cleanup feature not available")

    logger.info("=" * 70)
    logger.info(f"Gateway API Ready (APIs: {len(registry.get_all_apis())})")
    logger.info("=" * 70)

    yield

    # Shutdown
    logger.info("Gateway API Stopping")
    try:
        from utils.result_manager import stop_cleanup_scheduler
        stop_cleanup_scheduler()
    except ImportError:
        pass


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Gateway API",
    description="Integrated Orchestration Service for Engineering Drawing Processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(admin_router)
app.include_router(api_key_router)
app.include_router(gpu_config_router)
app.include_router(docker_router)
app.include_router(results_router)
app.include_router(container_router)
app.include_router(spec_router)
app.include_router(registry_router)
app.include_router(workflow_router)
app.include_router(config_router)
app.include_router(process_router)
app.include_router(quote_router)
app.include_router(download_router)


# =====================
# Custom OpenAPI Schema
# =====================

def custom_openapi():
    """Custom OpenAPI schema with nested models"""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    nested_models = {
        "DetectionResult": DetectionResult,
        "YOLOResults": YOLOResults,
        "DimensionData": DimensionData,
        "OCRResults": OCRResults,
        "ComponentData": ComponentData,
        "SegmentationResults": SegmentationResults,
        "ToleranceResult": ToleranceResult,
        "ProcessData": ProcessData,
        "CostBreakdown": CostBreakdown,
        "QuoteData": QuoteData,
    }

    for model_name, model_class in nested_models.items():
        if model_name not in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"][model_name] = model_class.model_json_schema()

    if "ProcessResponse" in openapi_schema["components"]["schemas"]:
        openapi_schema["components"]["schemas"]["ProcessResponse"]["properties"]["data"] = {
            "$ref": "#/components/schemas/ProcessData"
        }

    if "QuoteResponse" in openapi_schema["components"]["schemas"]:
        openapi_schema["components"]["schemas"]["QuoteResponse"]["properties"]["data"] = {
            "$ref": "#/components/schemas/QuoteData"
        }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# =====================
# Helper Functions
# =====================

async def check_service_health(url: str, service_name: str) -> str:
    """Service health check (2s timeout)"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            if "edocr2-v2-api" in url:
                health_endpoint = f"{url}/api/v2/health"
            else:
                health_endpoint = f"{url}/api/v1/health"

            response = await client.get(health_endpoint)
            if response.status_code == 200:
                return "healthy"
            else:
                return f"unhealthy (status={response.status_code})"
    except Exception as e:
        logger.warning(f"{service_name} health check failed: {e}")
        return f"unreachable ({str(e)})"


# =====================
# API Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    services = {
        "edocr2": await check_service_health(EDOCR2_URL, "eDOCr2"),
        "edgnet": await check_service_health(EDGNET_URL, "EDGNet"),
        "skinmodel": await check_service_health(SKINMODEL_URL, "Skin Model"),
        "knowledge": await check_service_health(KNOWLEDGE_API_URL, "Knowledge API")
    }

    all_healthy = all(status == "healthy" for status in services.values())

    return {
        "status": "online" if all_healthy else "degraded",
        "service": "Gateway API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": services
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check (parallel execution, max 2s)"""
    results = await asyncio.gather(
        check_service_health(EDOCR2_URL, "eDOCr2"),
        check_service_health(EDGNET_URL, "EDGNet"),
        check_service_health(SKINMODEL_URL, "Skin Model"),
        check_service_health(KNOWLEDGE_API_URL, "Knowledge API"),
        return_exceptions=True
    )

    service_names = ["edocr2", "edgnet", "skinmodel", "knowledge"]
    services = {}
    for name, result in zip(service_names, results):
        if isinstance(result, Exception):
            services[name] = f"error ({str(result)})"
        else:
            services[name] = result

    all_healthy = all(status == "healthy" for status in services.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "Gateway API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": services
    }


@app.get("/api/v1/sample-image")
async def get_sample_image(path: str):
    """Serve sample image files"""
    try:
        allowed_paths = [
            "/datasets/combined/images/test/synthetic_random_synthetic_test_000003.jpg",
            "/datasets/combined/images/test/synthetic_random_synthetic_test_000001.jpg",
            "/datasets/combined/images/test/synthetic_random_synthetic_test_000002.jpg"
        ]

        if path not in allowed_paths:
            raise HTTPException(status_code=403, detail="Access to this path is not allowed")

        file_path = Path(path)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Image not found: {path}")

        return FileResponse(
            path=str(file_path),
            media_type="image/jpeg",
            filename=file_path.name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving sample image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Main
# =====================

if __name__ == "__main__":
    port = int(os.getenv("GATEWAY_PORT", 8000))
    workers = int(os.getenv("GATEWAY_WORKERS", 1))

    logger.info(f"Starting Gateway API on port {port} with {workers} workers")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
