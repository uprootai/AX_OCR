"""분류 API (VLM 기반 도면 분류)

Phase 4: Vision-Language Model을 활용한 도면 자동 분류
- 도면 타입 분류 (기계 부품도, P&ID, 조립도 등)
- 영역 자동 검출 (표제란, 메인 뷰, BOM 등)
- 추천 프리셋 제공
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any, List
import base64

logger = logging.getLogger(__name__)

from schemas.classification import (
    ClassificationRequest,
    ClassificationResultSchema,
    ClassificationWithPresetResponse,
    PresetConfig,
    DetectedRegionSchema,
    DrawingType,
    RegionType,
)
from services.vlm_classifier import (
    vlm_classifier,
    get_preset_config,
    PRESET_PIPELINES,
)

router = APIRouter(prefix="/classification", tags=["Classification"])

# 서비스 인스턴스 (DI 패턴)
_session_service = None


def set_classification_services(session_service):
    """서비스 주입"""
    global _session_service
    _session_service = session_service


def get_session_service():
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


# ==================== Endpoints ====================

@router.post("/classify", response_model=ClassificationWithPresetResponse)
async def classify_drawing(request: ClassificationRequest) -> ClassificationWithPresetResponse:
    """
    도면 분류 실행

    VLM을 사용하여 도면 타입을 분류하고 추천 프리셋을 반환합니다.

    **지원 도면 타입:**
    - mechanical_part: 기계 부품도
    - pid: P&ID (배관계장도)
    - assembly: 조립도
    - electrical: 전기 회로도
    - architectural: 건축 도면

    **프로바이더:**
    - local: 로컬 VL API (기본)
    - openai: OpenAI GPT-4o
    - anthropic: Anthropic Claude Vision
    """
    if not request.image_base64 and not request.image_path:
        raise HTTPException(
            status_code=400,
            detail="image_base64 또는 image_path 중 하나가 필요합니다"
        )

    # VLM 분류 실행
    result = await vlm_classifier.classify_drawing(
        image_path=request.image_path,
        image_base64=request.image_base64,
        provider=request.provider
    )

    # 프리셋 조회
    preset_config = get_preset_config(result.suggested_preset)

    # 세션에 분류 결과 저장 (선택적)
    if request.session_id:
        try:
            session_service = get_session_service()
            session_service.update_session(request.session_id, {
                "classification": {
                    "drawing_type": result.drawing_type.value,
                    "confidence": result.confidence,
                    "suggested_preset": result.suggested_preset,
                    "provider": result.provider,
                    "regions": [
                        {
                            "region_type": r.region_type.value,
                            "bbox": r.bbox,
                            "confidence": r.confidence,
                            "description": r.description
                        }
                        for r in result.regions
                    ]
                }
            })
        except Exception as e:
            logger.warning(f"[Classification] 세션 저장 실패: {e}")

    # 응답 생성
    classification_schema = ClassificationResultSchema(
        drawing_type=result.drawing_type,
        confidence=result.confidence,
        suggested_preset=result.suggested_preset,
        regions=[
            DetectedRegionSchema(
                region_type=r.region_type,
                bbox=r.bbox,
                confidence=r.confidence,
                description=r.description
            )
            for r in result.regions
        ],
        analysis_notes=result.analysis_notes,
        provider=result.provider
    )

    preset_schema = PresetConfig(
        name=preset_config["name"],
        description=preset_config["description"],
        nodes=preset_config["nodes"],
        yolo_confidence=preset_config.get("yolo_confidence"),
        ocr_engine=preset_config.get("ocr_engine"),
        enable_tolerance_analysis=preset_config.get("enable_tolerance_analysis"),
        enable_connectivity=preset_config.get("enable_connectivity"),
        enable_bom=preset_config.get("enable_bom"),
        enable_part_matching=preset_config.get("enable_part_matching"),
        enable_circuit_analysis=preset_config.get("enable_circuit_analysis"),
        enable_floor_plan_analysis=preset_config.get("enable_floor_plan_analysis"),
    )

    return ClassificationWithPresetResponse(
        classification=classification_schema,
        preset=preset_schema,
        session_id=request.session_id
    )


@router.post("/classify-upload")
async def classify_drawing_upload(
    file: UploadFile = File(...),
    provider: str = Form("local"),
    session_id: Optional[str] = Form(None)
) -> ClassificationWithPresetResponse:
    """
    파일 업로드로 도면 분류

    multipart/form-data로 이미지를 업로드하여 분류합니다.
    """
    # 파일 읽기
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode("utf-8")

    # 분류 실행
    request = ClassificationRequest(
        image_base64=image_base64,
        provider=provider,
        session_id=session_id
    )

    return await classify_drawing(request)


@router.get("/presets")
async def get_presets() -> Dict[str, Any]:
    """
    사용 가능한 프리셋 목록 조회

    각 도면 타입에 최적화된 분석 파이프라인 프리셋을 반환합니다.
    """
    return {
        "presets": PRESET_PIPELINES,
        "drawing_types": [t.value for t in DrawingType],
        "region_types": [r.value for r in RegionType]
    }


@router.get("/presets/{preset_name}")
async def get_preset(preset_name: str) -> Dict[str, Any]:
    """특정 프리셋 조회"""
    config = get_preset_config(preset_name)
    if preset_name not in PRESET_PIPELINES:
        # 기본 프리셋 반환
        return {
            "preset_name": "general",
            "config": config,
            "note": f"'{preset_name}' 프리셋이 없어 'general' 프리셋을 반환합니다"
        }

    return {
        "preset_name": preset_name,
        "config": config
    }


@router.post("/apply-preset/{session_id}")
async def apply_preset_to_session(
    session_id: str,
    preset_name: str
) -> Dict[str, Any]:
    """
    세션에 프리셋 적용

    선택한 프리셋의 설정을 세션의 분석 옵션에 적용합니다.
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    config = get_preset_config(preset_name)

    # 세션 옵션 업데이트
    analysis_options = session.get("analysis_options", {})

    if config.get("yolo_confidence"):
        analysis_options["yolo_confidence"] = config["yolo_confidence"]

    if config.get("ocr_engine"):
        analysis_options["ocr_engine"] = config["ocr_engine"]

    analysis_options["preset_name"] = preset_name
    analysis_options["nodes"] = config.get("nodes", [])

    # features 배열 업데이트 (P&ID 분석 등 기능 활성화를 위해)
    features = config.get("features", [])

    session_service.update_session(session_id, {
        "analysis_options": analysis_options,
        "applied_preset": preset_name,
        "features": features  # 기능 목록 추가
    })

    return {
        "session_id": session_id,
        "applied_preset": preset_name,
        "config": config,
        "analysis_options": analysis_options,
        "features": features
    }


@router.get("/session/{session_id}")
async def get_session_classification(session_id: str) -> Dict[str, Any]:
    """세션의 분류 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    classification = session.get("classification")
    applied_preset = session.get("applied_preset")

    if not classification:
        return {
            "session_id": session_id,
            "has_classification": False,
            "message": "아직 분류가 수행되지 않았습니다"
        }

    return {
        "session_id": session_id,
        "has_classification": True,
        "classification": classification,
        "applied_preset": applied_preset
    }


@router.get("/providers")
async def get_available_providers() -> Dict[str, Any]:
    """
    사용 가능한 VLM 프로바이더 조회

    각 프로바이더의 상태와 필요한 설정을 반환합니다.
    """
    import os

    providers = {
        "local": {
            "name": "Local VL API",
            "description": "로컬 Vision-Language 모델 (Qwen-VL, LLaVA 등)",
            "endpoint": vlm_classifier.local_vl_url,
            "available": True,  # 헬스체크로 확인 필요
            "requires_api_key": False
        },
        "openai": {
            "name": "OpenAI GPT-4o",
            "description": "OpenAI의 GPT-4o 모델",
            "available": bool(vlm_classifier.openai_api_key),
            "requires_api_key": True,
            "env_var": "OPENAI_API_KEY"
        },
        "anthropic": {
            "name": "Anthropic Claude Vision",
            "description": "Anthropic의 Claude 3 Vision 모델",
            "available": bool(vlm_classifier.anthropic_api_key),
            "requires_api_key": True,
            "env_var": "ANTHROPIC_API_KEY"
        }
    }

    return {
        "providers": providers,
        "default_provider": vlm_classifier.default_provider
    }
