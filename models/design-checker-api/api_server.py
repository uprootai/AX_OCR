"""
Design Checker API Server
도면 설계 오류 검출 및 규정 검증 API

포트: 5019

설계 검증 규칙:
- ISO 10628 (P&ID 표준)
- ISA 5.1 (계기 심볼 표준)
- TECHCROSS BWMS 체크리스트
"""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Schemas
from schemas import HealthResponse, ProcessResponse

# Constants
from constants import DESIGN_RULES

# BWMS Rules
from bwms_rules import bwms_checker

# Rule Loader (카테고리별 YAML 관리)
from rule_loader import rule_loader

# Routers
from routers import check_router, rules_router, checklist_router, ocr_check_router, pipeline_router

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("DESIGN_CHECKER_PORT", "5019"))


# =====================
# Lifespan (startup/shutdown)
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 생명주기 관리 (startup/shutdown)"""
    # Startup
    logger.info("Starting Design Checker API on port %d", API_PORT)
    logger.info("Total design rules: %d", len(DESIGN_RULES))

    # 카테고리별 YAML 규칙 자동 로드
    try:
        loaded_rules = rule_loader.load_all_rules()
        if loaded_rules:
            # bwms_checker에 동적 규칙으로 로드
            if not hasattr(bwms_checker, '_dynamic_rules'):
                bwms_checker._dynamic_rules = {}

            for rule_id, rule_dict in loaded_rules.items():
                bwms_checker._dynamic_rules[rule_id] = rule_dict

            logger.info(f"Auto-loaded {len(loaded_rules)} rules from YAML files")

    except Exception as e:
        logger.warning(f"Failed to auto-load rules: {e}")

    logger.info("Design Checker API started successfully")

    yield  # 여기서 앱 실행

    # Shutdown (필요시)
    logger.info("Shutting down Design Checker API")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Design Checker API",
    description="P&ID 도면 설계 오류 검출 및 규정 검증 API",
    version="1.0.0",
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

# Include Routers
app.include_router(check_router)
app.include_router(rules_router)
app.include_router(checklist_router)
app.include_router(ocr_check_router)
app.include_router(pipeline_router)


# =====================
# Health Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크"""
    return HealthResponse(
        status="healthy",
        service="design-checker-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스 체크 (v1)"""
    return await health_check()


@app.get("/api/v1/info")
async def get_info():
    """API 정보 조회"""
    # 동적 규칙 수
    dynamic_count = len(getattr(bwms_checker, '_dynamic_rules', {}))

    return ProcessResponse(
        success=True,
        data={
            "name": "Design Checker API",
            "version": "1.0.0",
            "description": "P&ID 도면 설계 오류 검출 및 규정 검증",
            "port": API_PORT,
            "rules": {
                "design_rules": len(DESIGN_RULES),
                "bwms_builtin": 7,
                "bwms_dynamic": dynamic_count,
                "total": len(DESIGN_RULES) + 7 + dynamic_count
            },
            "endpoints": {
                "health": "/health",
                "check": "/api/v1/check",
                "check_bwms": "/api/v1/check/bwms",
                "check_ocr": "/api/v1/check/ocr",
                "check_ocr_tags": "/api/v1/check/ocr/tags",
                "check_ocr_patterns": "/api/v1/check/ocr/patterns",
                "rules": "/api/v1/rules",
                "rules_bwms": "/api/v1/rules/bwms",
                "rules_status": "/api/v1/rules/status",
                "checklist_upload": "/api/v1/checklist/upload",
                "checklist_template": "/api/v1/checklist/template",
                "pipeline_detect": "/api/v1/pipeline/detect",
                "pipeline_ocr": "/api/v1/pipeline/ocr",
                "pipeline_validate": "/api/v1/pipeline/validate",
                "pipeline_export": "/api/v1/pipeline/validate/export",
            },
            "ocr_sources": ["paddleocr", "edocr2", "both"],
            "standards": [
                "ISO 10628 (P&ID)",
                "ISA 5.1 (계기 심볼)",
                "TECHCROSS BWMS"
            ]
        }
    )


# =====================
# Main Entry Point
# =====================

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=False,
        log_level="info"
    )
