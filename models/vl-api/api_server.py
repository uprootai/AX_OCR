"""
Vision Language Model API Server
Multimodal LLM 기반 도면 분석 마이크로서비스

포트: 5004
기능: Information Block 추출, 치수 추출, 제조 공정 추론, QC Checklist 생성
"""

import logging
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import torch

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_DIR = Path("/tmp/vl-api/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Import services and routers
from services import (
    get_available_models,
    set_model_state,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
)
from routers import analysis_router
from schemas import HealthResponse


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate API keys and load BLIP on startup, cleanup on shutdown"""
    # Startup
    logger.info("🚀 Starting VL API...")
    logger.info("🔑 Validating API keys...")

    missing_keys = []
    available_models = []

    # Check Anthropic API key
    if ANTHROPIC_API_KEY:
        logger.info("  ✅ ANTHROPIC_API_KEY is set")
        available_models.extend([
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307"
        ])
    else:
        logger.warning("  ⚠️  ANTHROPIC_API_KEY is NOT set")
        missing_keys.append("ANTHROPIC_API_KEY")

    # Check OpenAI API key
    if OPENAI_API_KEY:
        logger.info("  ✅ OPENAI_API_KEY is set")
        available_models.extend([
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4"
        ])
    else:
        logger.warning("  ⚠️  OPENAI_API_KEY is NOT set")
        missing_keys.append("OPENAI_API_KEY")

    # Load local VL model as fallback (always available)
    logger.info("🔄 Loading local VL model...")
    florence_model = None
    florence_processor = None
    florence_device = None

    try:
        florence_device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"  Using device: {florence_device}")

        # Try BLIP (smaller model with better compatibility)
        BLIP_MODEL_ID = "Salesforce/blip-image-captioning-base"
        from transformers import BlipProcessor, BlipForConditionalGeneration

        florence_processor = BlipProcessor.from_pretrained(BLIP_MODEL_ID)
        florence_model = BlipForConditionalGeneration.from_pretrained(
            BLIP_MODEL_ID,
            torch_dtype=torch.float16 if florence_device == "cuda" else torch.float32
        ).to(florence_device)

        florence_model.eval()
        available_models.append("blip-base")
        logger.info("  ✅ BLIP model loaded successfully")
    except Exception as e:
        logger.error(f"  ❌ Failed to load local model: {e}")
        logger.warning("  Local model will not be available")

    # Update global state via service layer
    set_model_state(available_models, florence_model, florence_processor, florence_device)

    # Log summary
    if missing_keys and not florence_model:
        logger.error("❌ No API keys and BLIP failed to load! VL API will not work.")
        logger.error("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variables")
    elif missing_keys:
        logger.warning(f"⚠️  Missing API keys: {', '.join(missing_keys)}")
        logger.info(f"✅ BLIP available as fallback")
    else:
        logger.info(f"✅ All API keys validated. Available models: {len(available_models)}")

    logger.info(f"✅ VL API ready. Available models: {available_models}")

    yield

    # Shutdown
    logger.info("👋 Shutting down VL API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Vision Language Model API",
    description="Multimodal LLM Service for Engineering Drawing Analysis",
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
app.include_router(analysis_router)


# =====================
# Health Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint / 헬스체크

    Returns the current health status and available VL models.
    """
    available_models = get_available_models()

    # Fallback: check if keys exist (for backward compatibility)
    if not available_models:
        if ANTHROPIC_API_KEY:
            available_models.extend([
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ])
        if OPENAI_API_KEY:
            available_models.extend([
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-4-vision-preview"
            ])

    return HealthResponse(
        status="healthy",
        service="vl-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        available_models=available_models
    )


# =====================
# Main
# =====================

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=5004,
        reload=True,
        log_level="info"
    )
