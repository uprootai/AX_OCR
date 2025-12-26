"""Long-term Roadmap Router - 장기 로드맵 기능 API

기능 목록:
- 도면 영역 세분화 (Drawing Region Segmentation)
- 노트/주석 추출 (Notes Extraction)
- 리비전 비교 (Revision Comparison)
- VLM 자동 분류 (VLM Auto Classification)

분리 목적:
- analysis_router.py 크기 감소 (2,800+ lines → 모듈화)
- LLM 컨텍스트 효율성 향상
- 장기 로드맵 기능 독립 관리
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
import logging
import time
import uuid

# Session 서비스 의존성
_session_service = None


def get_session_service():
    """세션 서비스 인스턴스 가져오기 (지연 초기화)"""
    global _session_service
    if _session_service is None:
        from services.session_service import SessionService
        _session_service = SessionService()
    return _session_service


def set_session_service(service):
    """세션 서비스 주입 (테스트용)"""
    global _session_service
    _session_service = service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Long-term Features"])


# ============================================================
# 도면 영역 세분화 (Drawing Region Segmentation)
# ============================================================

@router.post("/drawing-regions/{session_id}/segment")
async def segment_drawing_regions(session_id: str) -> Dict[str, Any]:
    """도면 영역 세분화 실행

    정면도, 측면도, 단면도, 상세도, 표제란 등을 자동 구분합니다.
    SAM/U-Net 기반 세그멘테이션 모델이 필요합니다 (현재: 더미 구현).
    """
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # TODO: 실제 세그멘테이션 모델 구현
    # 현재는 더미 결과 반환
    regions = []

    # 표제란 영역 추정 (우하단 고정 위치)
    image_width = session.get("image_width", 1000)
    image_height = session.get("image_height", 1000)

    # 표제란이 있을 가능성이 높은 영역 추가
    title_block_region = {
        "id": f"region_{session_id[:8]}_title",
        "view_type": "title_block",
        "label": "표제란",
        "bbox": [image_width * 0.6, image_height * 0.85, image_width, image_height],
        "confidence": 0.7,
        "contains_dimensions": False,
        "contains_annotations": True,
    }

    # 메인 뷰 영역 (단순 추정)
    main_view_region = {
        "id": f"region_{session_id[:8]}_main",
        "view_type": "front",
        "label": "정면도",
        "bbox": [0, 0, image_width * 0.6, image_height * 0.85],
        "confidence": 0.5,
        "contains_dimensions": True,
        "contains_annotations": True,
    }

    regions = [title_block_region, main_view_region]

    processing_time = (time.time() - start_time) * 1000

    result = {
        "session_id": session_id,
        "regions": regions,
        "total_regions": len(regions),
        "by_view_type": {"title_block": 1, "front": 1},
        "has_title_block": True,
        "has_parts_list": False,
        "processing_time_ms": processing_time,
    }

    session_service.update_session(session_id, {"drawing_regions": result})
    return result


@router.get("/drawing-regions/{session_id}")
async def get_drawing_regions(session_id: str) -> Dict[str, Any]:
    """도면 영역 세분화 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return session.get("drawing_regions", {
        "session_id": session_id,
        "regions": [],
        "total_regions": 0,
        "by_view_type": {},
        "has_title_block": False,
        "has_parts_list": False,
        "processing_time_ms": 0,
    })


@router.put("/drawing-regions/{session_id}/{region_id}")
async def update_drawing_region(
    session_id: str,
    region_id: str,
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """도면 영역 정보 수정"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("drawing_regions", {})
    regions = result.get("regions", [])

    updated_region = None
    for i, r in enumerate(regions):
        if r.get("id") == region_id:
            regions[i].update(update)
            updated_region = regions[i]
            break

    if not updated_region:
        raise HTTPException(status_code=404, detail="영역을 찾을 수 없습니다")

    result["regions"] = regions
    session_service.update_session(session_id, {"drawing_regions": result})

    return {"success": True, "region": updated_region}


# ============================================================
# 주석/노트 추출 (Notes Extraction)
# ============================================================

@router.post("/notes/{session_id}/extract")
async def extract_notes(session_id: str) -> Dict[str, Any]:
    """도면 노트/주석 추출

    일반 노트, 재료 사양, 열처리, 표면 처리 등을 추출합니다.
    LLM 기반 분류가 필요합니다 (현재: 더미 구현).
    """
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # TODO: 실제 노트 추출 구현
    # 현재는 더미 결과 반환
    notes = []
    materials = []
    standards = []
    tolerances = {}

    processing_time = (time.time() - start_time) * 1000

    result = {
        "session_id": session_id,
        "notes": notes,
        "total_notes": len(notes),
        "by_category": {},
        "materials": materials,
        "standards": standards,
        "tolerances": tolerances,
        "processing_time_ms": processing_time,
    }

    session_service.update_session(session_id, {"notes_extraction": result})
    return result


@router.get("/notes/{session_id}")
async def get_notes(session_id: str) -> Dict[str, Any]:
    """노트 추출 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return session.get("notes_extraction", {
        "session_id": session_id,
        "notes": [],
        "total_notes": 0,
        "by_category": {},
        "materials": [],
        "standards": [],
        "tolerances": {},
        "processing_time_ms": 0,
    })


@router.put("/notes/{session_id}/{note_id}")
async def update_note(
    session_id: str,
    note_id: str,
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """노트 정보 수정"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("notes_extraction", {})
    notes = result.get("notes", [])

    updated_note = None
    for i, n in enumerate(notes):
        if n.get("id") == note_id:
            notes[i].update(update)
            updated_note = notes[i]
            break

    if not updated_note:
        raise HTTPException(status_code=404, detail="노트를 찾을 수 없습니다")

    result["notes"] = notes
    session_service.update_session(session_id, {"notes_extraction": result})

    return {"success": True, "note": updated_note}


# ============================================================
# 리비전 비교 (Revision Comparison)
# ============================================================

@router.post("/revision/compare")
async def compare_revisions(request: Dict[str, Any]) -> Dict[str, Any]:
    """두 도면 리비전 비교

    이미지 정합 및 변경점 감지를 수행합니다.
    SIFT/ORB 기반 정합 알고리즘이 필요합니다 (현재: 더미 구현).

    Request body:
    - session_id_old: 이전 리비전 세션 ID
    - session_id_new: 새 리비전 세션 ID
    - config: 비교 설정 (선택)
    """
    start_time = time.time()

    session_id_old = request.get("session_id_old")
    session_id_new = request.get("session_id_new")

    if not session_id_old or not session_id_new:
        raise HTTPException(status_code=400, detail="session_id_old와 session_id_new가 필요합니다")

    session_service = get_session_service()

    session_old = session_service.get_session(session_id_old)
    session_new = session_service.get_session(session_id_new)

    if not session_old:
        raise HTTPException(status_code=404, detail="이전 리비전 세션을 찾을 수 없습니다")
    if not session_new:
        raise HTTPException(status_code=404, detail="새 리비전 세션을 찾을 수 없습니다")

    # TODO: 실제 리비전 비교 구현
    # 현재는 더미 결과 반환
    changes = []
    comparison_id = str(uuid.uuid4())

    processing_time = (time.time() - start_time) * 1000

    result = {
        "comparison_id": comparison_id,
        "session_id_old": session_id_old,
        "session_id_new": session_id_new,
        "changes": changes,
        "total_changes": len(changes),
        "by_type": {},
        "by_category": {},
        "added_count": 0,
        "removed_count": 0,
        "modified_count": 0,
        "diff_image_url": None,
        "overlay_image_url": None,
        "alignment_score": 0.0,
        "processing_time_ms": processing_time,
    }

    # 새 세션에 비교 결과 저장
    session_service.update_session(session_id_new, {"revision_comparison": result})

    return result


@router.get("/revision/{session_id}")
async def get_revision_comparison(session_id: str) -> Dict[str, Any]:
    """리비전 비교 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return session.get("revision_comparison", {
        "session_id_old": None,
        "session_id_new": session_id,
        "changes": [],
        "total_changes": 0,
        "by_type": {},
        "by_category": {},
        "added_count": 0,
        "removed_count": 0,
        "modified_count": 0,
        "processing_time_ms": 0,
    })


# ============================================================
# VLM 자동 분류 (VLM Auto Classification)
# ============================================================

@router.post("/vlm-classify/{session_id}")
async def vlm_classify_drawing(
    session_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """VLM 기반 도면 자동 분류

    GPT-4V, Claude Vision 등을 사용하여 도면 타입 및 특성을 분류합니다.
    현재는 Local VL API를 사용합니다 (더미 구현).

    Config options:
    - provider: VLM 제공자 (local, openai, anthropic, google)
    - recommend_features: 기능 추천 포함 여부
    - detailed_analysis: 상세 분석 포함 여부
    """
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    provider = (config or {}).get("provider", "local")
    recommend_features = (config or {}).get("recommend_features", True)

    # TODO: 실제 VLM API 호출 구현
    # 현재는 세션의 기존 분류 정보 사용 또는 기본값 반환

    # 기존 분류 정보가 있으면 활용
    existing_type = session.get("drawing_type", "auto")
    confidence = session.get("drawing_type_confidence", 0.0)

    # 도면 타입 매핑
    type_mapping = {
        "mechanical_part": "mechanical_part",
        "assembly": "assembly",
        "pid": "pid",
        "electrical": "electrical",
        "dimension": "mechanical_part",
        "electrical_panel": "electrical",
        "auto": "other",
    }

    drawing_type = type_mapping.get(existing_type, "other")

    # 추천 기능 계산
    recommended_features = []
    if recommend_features:
        if drawing_type == "mechanical_part":
            recommended_features = [
                "dimension_ocr", "dimension_verification", "gdt_parsing",
                "surface_roughness_parsing", "welding_symbol_parsing"
            ]
        elif drawing_type == "assembly":
            recommended_features = [
                "symbol_detection", "balloon_matching", "quantity_extraction",
                "bom_generation"
            ]
        elif drawing_type == "pid":
            recommended_features = [
                "symbol_detection", "line_detection", "pid_connectivity",
                "bom_generation"
            ]
        elif drawing_type == "electrical":
            recommended_features = [
                "symbol_detection", "bom_generation"
            ]

    processing_time = (time.time() - start_time) * 1000

    result = {
        "session_id": session_id,
        "drawing_type": drawing_type,
        "drawing_type_confidence": confidence or 0.7,
        "industry_domain": "machinery",
        "industry_confidence": 0.6,
        "complexity": "moderate",
        "estimated_part_count": None,
        "has_dimensions": True,
        "has_tolerances": drawing_type == "mechanical_part",
        "has_surface_finish": drawing_type == "mechanical_part",
        "has_welding_symbols": drawing_type in ["mechanical_part", "assembly"],
        "has_gdt": drawing_type == "mechanical_part",
        "has_bom": drawing_type in ["assembly", "pid"],
        "has_notes": True,
        "has_title_block": True,
        "recommended_features": recommended_features,
        "analysis_summary": f"도면 타입: {drawing_type}, 추천 기능 {len(recommended_features)}개",
        "raw_response": None,
        "vlm_provider": provider,
        "vlm_model": "local-vl" if provider == "local" else None,
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
