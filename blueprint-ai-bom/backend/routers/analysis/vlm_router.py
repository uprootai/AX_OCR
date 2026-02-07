"""VLM Router - VLM 자동 분류 API (장기 로드맵)

longterm_router.py에서 분리된 VLM 분류 기능:
- VLM 분류 실행 (POST /analysis/vlm-classify/{session_id})
- 분류 결과 조회 (GET /analysis/vlm-classify/{session_id})
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
import logging
import time
import base64
from pathlib import Path

from services.vlm_classifier import vlm_classifier, get_preset_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["VLM Classification"])

# Session 서비스 의존성
_session_service = None


def set_vlm_services(session_service):
    """세션 서비스 설정"""
    global _session_service
    _session_service = session_service


def get_session_service():
    """세션 서비스 인스턴스 가져오기 (지연 초기화)"""
    global _session_service
    if _session_service is None:
        from services.session_service import SessionService
        _session_service = SessionService()
    return _session_service


@router.post("/vlm-classify/{session_id}")
async def vlm_classify_drawing(
    session_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """VLM 기반 도면 자동 분류

    GPT-4o-mini (기본), GPT-4o, Claude Vision, 로컬 VL API를 사용하여
    도면 타입 및 특성을 분류합니다.

    Config options:
    - provider: VLM 제공자 (local, openai, anthropic) - 기본: openai
    - recommend_features: 기능 추천 포함 여부 (기본: True)
    - model: OpenAI 모델 선택 (gpt-4o-mini, gpt-4o) - 환경변수 우선

    환경변수:
    - OPENAI_API_KEY: OpenAI API 키 (필수)
    - OPENAI_MODEL: 사용할 모델 (기본: gpt-4o-mini)
    """
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 설정 파싱
    config = config or {}
    provider = config.get("provider", "openai")  # 기본값을 openai로 변경
    recommend_features = config.get("recommend_features", True)

    # 이미지 준비 (세션에서 이미지 경로 또는 base64 가져오기)
    image_path = session.get("image_path")
    image_base64 = session.get("image_base64")

    # 이미지 경로에서 base64 인코딩
    if image_path and not image_base64:
        try:
            path = Path(image_path)
            if path.exists():
                with open(path, "rb") as f:
                    image_base64 = base64.b64encode(f.read()).decode("utf-8")
                logger.info(f"[VLM] 이미지 로드 완료: {image_path}")
        except Exception as e:
            logger.warning(f"[VLM] 이미지 로드 실패: {e}")

    # VLM 분류 실행
    drawing_type = "unknown"
    confidence = 0.0
    regions = []
    analysis_notes = ""
    raw_response = None
    vlm_model = None

    if image_base64:
        try:
            # VLM 분류기 호출
            classification_result = await vlm_classifier.classify_drawing(
                image_base64=image_base64,
                provider=provider
            )

            drawing_type = classification_result.drawing_type.value
            confidence = classification_result.confidence
            regions = [
                {
                    "region_type": r.region_type.value,
                    "bbox": r.bbox,
                    "confidence": r.confidence,
                    "description": r.description
                }
                for r in classification_result.regions
            ]
            analysis_notes = classification_result.analysis_notes
            raw_response = classification_result.raw_response
            provider = classification_result.provider
            vlm_model = vlm_classifier.openai_model if provider == "openai" else None

            logger.info(f"[VLM] 분류 완료 - 타입: {drawing_type}, 신뢰도: {confidence:.2f}, provider: {provider}")

        except Exception as e:
            logger.error(f"[VLM] 분류 실패: {e}")
            analysis_notes = f"VLM 분류 실패: {str(e)}"
    else:
        analysis_notes = "이미지가 없어 분류를 수행할 수 없습니다. 이미지를 먼저 업로드하세요."
        logger.warning(f"[VLM] 세션 {session_id}에 이미지가 없습니다")

    # 추천 기능 계산
    recommended_features = []
    if recommend_features:
        feature_map = {
            "mechanical_part": [
                "symbol_detection", "dimension_ocr", "dimension_verification",
                "gdt_parsing", "surface_roughness_parsing", "welding_symbol_parsing",
                "bom_generation"
            ],
            "assembly": [
                "symbol_detection", "symbol_verification", "balloon_matching",
                "quantity_extraction", "bom_generation"
            ],
            "pid": [
                "symbol_detection", "line_detection", "pid_connectivity",
                "pid_valve_detection", "pid_equipment_detection", "pid_design_checklist",
                "pid_deviation_analysis", "bom_generation"
            ],
            "electrical": [
                "symbol_detection", "dimension_ocr", "bom_generation"
            ],
            "architectural": [
                "symbol_detection", "dimension_ocr", "notes_extraction"
            ],
        }
        recommended_features = feature_map.get(drawing_type, [
            "symbol_detection", "dimension_ocr", "bom_generation"
        ])

    processing_time = (time.time() - start_time) * 1000

    result = {
        "session_id": session_id,
        "drawing_type": drawing_type,
        "drawing_type_confidence": confidence,
        "industry_domain": "machinery" if drawing_type in ["mechanical_part", "assembly"] else "general",
        "industry_confidence": confidence * 0.8,
        "complexity": "moderate",
        "estimated_part_count": None,
        "has_dimensions": drawing_type in ["mechanical_part", "assembly"],
        "has_tolerances": drawing_type == "mechanical_part",
        "has_surface_finish": drawing_type == "mechanical_part",
        "has_welding_symbols": drawing_type in ["mechanical_part", "assembly"],
        "has_gdt": drawing_type == "mechanical_part",
        "has_bom": drawing_type in ["assembly", "pid"],
        "has_notes": True,
        "has_title_block": True,
        "regions": regions,
        "recommended_features": recommended_features,
        "analysis_summary": analysis_notes or f"도면 타입: {drawing_type}, 추천 기능 {len(recommended_features)}개",
        "raw_response": raw_response,
        "vlm_provider": provider,
        "vlm_model": vlm_model,
        "processing_time_ms": processing_time,
    }

    session_service.update_session(session_id, {"vlm_classification": result})
    return result


@router.get("/vlm-classify/{session_id}")
async def get_vlm_classification(session_id: str) -> Dict[str, Any]:
    """VLM 분류 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return session.get("vlm_classification", {
        "session_id": session_id,
        "drawing_type": "other",
        "drawing_type_confidence": 0.0,
        "industry_domain": "general",
        "industry_confidence": 0.0,
        "complexity": "moderate",
        "recommended_features": [],
        "processing_time_ms": 0,
    })
