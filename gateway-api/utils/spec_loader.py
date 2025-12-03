"""
API Spec Loader Utility
YAML 스펙 파일을 로드하고 /meta 엔드포인트를 위한 형식으로 변환

Usage:
    from utils.spec_loader import SpecLoader, add_meta_endpoint

    # Option 1: FastAPI 앱에 /meta 엔드포인트 자동 추가
    add_meta_endpoint(app, "yolo")

    # Option 2: 스펙 직접 로드
    spec = SpecLoader.load("yolo")
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

logger = logging.getLogger(__name__)

# 스펙 파일 디렉토리 경로
SPEC_DIR = Path(__file__).parent.parent / "api_specs"
# Docker 환경에서는 환경변수로 오버라이드 가능
if os.getenv("API_SPECS_DIR"):
    SPEC_DIR = Path(os.getenv("API_SPECS_DIR"))


class SpecLoader:
    """API 스펙 로더"""

    _cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def load(cls, api_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        API 스펙 로드

        Args:
            api_id: API ID (예: yolo, edocr2, skinmodel)
            use_cache: 캐시 사용 여부

        Returns:
            스펙 딕셔너리 또는 None
        """
        if use_cache and api_id in cls._cache:
            return cls._cache[api_id]

        spec_path = SPEC_DIR / f"{api_id}.yaml"

        if not spec_path.exists():
            logger.warning(f"Spec file not found: {spec_path}")
            return None

        try:
            with open(spec_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            if use_cache:
                cls._cache[api_id] = spec

            logger.info(f"Loaded API spec: {api_id}")
            return spec

        except Exception as e:
            logger.error(f"Failed to load spec {api_id}: {e}")
            return None

    @classmethod
    def load_all(cls) -> Dict[str, Dict[str, Any]]:
        """모든 API 스펙 로드"""
        specs = {}

        if not SPEC_DIR.exists():
            logger.warning(f"Spec directory not found: {SPEC_DIR}")
            return specs

        for spec_file in SPEC_DIR.glob("*.yaml"):
            api_id = spec_file.stem
            spec = cls.load(api_id)
            if spec:
                specs[api_id] = spec

        logger.info(f"Loaded {len(specs)} API specs")
        return specs

    @classmethod
    def get_blueprintflow_meta(cls, api_id: str) -> Optional[Dict[str, Any]]:
        """BlueprintFlow용 메타데이터 추출"""
        spec = cls.load(api_id)
        if not spec:
            return None

        metadata = spec.get("metadata", {})
        server = spec.get("server", {})
        blueprintflow = spec.get("blueprintflow", {})

        return {
            "id": metadata.get("id", api_id),
            "name": metadata.get("name", api_id),
            "version": metadata.get("version", "1.0.0"),
            "port": metadata.get("port"),
            "description": metadata.get("description", ""),
            "endpoint": server.get("endpoint", "/api/v1/process"),
            "method": server.get("method", "POST"),
            "contentType": server.get("contentType", "multipart/form-data"),
            "timeout": server.get("timeout", 60),
            "category": blueprintflow.get("category", "detection"),
            "color": blueprintflow.get("color", "#6366f1"),
            "icon": blueprintflow.get("icon", "Box"),
            "requiresImage": blueprintflow.get("requiresImage", True),
            "inputs": spec.get("inputs", []),
            "outputs": spec.get("outputs", []),
            "parameters": spec.get("parameters", []),
            "mappings": spec.get("mappings", {}),
            "i18n": spec.get("i18n", {})
        }

    @classmethod
    def clear_cache(cls):
        """캐시 초기화"""
        cls._cache.clear()
        logger.info("Spec cache cleared")


def add_meta_endpoint(app, api_id: str):
    """
    FastAPI 앱에 /meta 엔드포인트 추가

    Args:
        app: FastAPI 앱 인스턴스
        api_id: API ID
    """
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse

    @app.get("/meta")
    @app.get("/api/v1/meta")
    async def get_api_meta():
        """API 메타데이터 (BlueprintFlow 자동 통합용)"""
        spec = SpecLoader.load(api_id)

        if not spec:
            raise HTTPException(
                status_code=404,
                detail=f"Spec not found for API: {api_id}"
            )

        return JSONResponse(content=spec)

    @app.get("/meta/blueprintflow")
    @app.get("/api/v1/meta/blueprintflow")
    async def get_blueprintflow_meta():
        """BlueprintFlow 노드 메타데이터"""
        meta = SpecLoader.get_blueprintflow_meta(api_id)

        if not meta:
            raise HTTPException(
                status_code=404,
                detail=f"Spec not found for API: {api_id}"
            )

        return JSONResponse(content=meta)

    logger.info(f"Added /meta endpoint for API: {api_id}")


def get_api_registry() -> Dict[str, Dict[str, Any]]:
    """
    모든 API의 레지스트리 정보 반환
    Gateway에서 API 목록 조회용
    """
    specs = SpecLoader.load_all()

    registry = {}
    for api_id, spec in specs.items():
        metadata = spec.get("metadata", {})
        server = spec.get("server", {})

        registry[api_id] = {
            "id": api_id,
            "name": metadata.get("name", api_id),
            "version": metadata.get("version", "1.0.0"),
            "port": metadata.get("port"),
            "description": metadata.get("description", ""),
            "endpoint": server.get("endpoint"),
            "healthEndpoint": server.get("healthEndpoint", "/health"),
            "category": spec.get("blueprintflow", {}).get("category", "detection")
        }

    return registry


# 간편 함수
def load_spec(api_id: str) -> Optional[Dict[str, Any]]:
    """스펙 로드 단축 함수"""
    return SpecLoader.load(api_id)


def get_spec_parameter(api_id: str, param_name: str) -> Optional[Dict[str, Any]]:
    """특정 파라미터 정보 조회"""
    spec = SpecLoader.load(api_id)
    if not spec:
        return None

    for param in spec.get("parameters", []):
        if param.get("name") == param_name:
            return param

    return None
