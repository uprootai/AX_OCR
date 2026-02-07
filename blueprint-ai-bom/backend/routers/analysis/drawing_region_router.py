"""Drawing Region Router - 도면 영역 세분화 API (장기 로드맵)

longterm_router.py에서 분리된 도면 영역 세분화 기능:
- 도면 영역 세분화 실행 (POST /analysis/drawing-regions/{session_id}/segment)
- 세분화 결과 조회 (GET /analysis/drawing-regions/{session_id})
- 영역 정보 수정 (PUT /analysis/drawing-regions/{session_id}/{region_id})
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
import logging
import time
import base64
from pathlib import Path

from services.region_segmenter import RegionSegmenter
from schemas.region import RegionSegmentationConfig, RegionType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Drawing Regions"])

# 영역 세분화 싱글톤
_region_segmenter: Optional[RegionSegmenter] = None

# Session 서비스 의존성
_session_service = None


def set_drawing_region_services(session_service):
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


def get_region_segmenter() -> RegionSegmenter:
    """영역 세분화 서비스 인스턴스 가져오기"""
    global _region_segmenter
    if _region_segmenter is None:
        _region_segmenter = RegionSegmenter()
    return _region_segmenter


def _get_region_label(region_type: RegionType) -> str:
    """영역 타입에 대한 한글 레이블 반환"""
    labels = {
        RegionType.TITLE_BLOCK: "표제란",
        RegionType.MAIN_VIEW: "메인 뷰",
        RegionType.BOM_TABLE: "BOM 테이블",
        RegionType.NOTES: "노트/주석",
        RegionType.DETAIL_VIEW: "상세도",
        RegionType.SECTION_VIEW: "단면도",
        RegionType.DIMENSION_AREA: "치수 영역",
        RegionType.LEGEND: "범례",
        RegionType.REVISION_BLOCK: "개정 이력",
        RegionType.PARTS_LIST: "부품 목록",
        RegionType.UNKNOWN: "미분류",
    }
    return labels.get(region_type, "알 수 없음")


def _get_fallback_regions(
    session_id: str,
    image_width: int,
    image_height: int
) -> List[Dict[str, Any]]:
    """폴백용 기본 영역 반환"""
    return [
        {
            "id": f"region_{session_id[:8]}_title",
            "view_type": "title_block",
            "label": "표제란",
            "bbox": [image_width * 0.6, image_height * 0.85, image_width, image_height],
            "bbox_normalized": [0.6, 0.85, 1.0, 1.0],
            "confidence": 0.7,
            "processing_strategy": "metadata_extract",
            "verification_status": "pending",
            "contains_dimensions": False,
            "contains_annotations": True,
        },
        {
            "id": f"region_{session_id[:8]}_main",
            "view_type": "main_view",
            "label": "메인 뷰",
            "bbox": [0, 0, image_width * 0.6, image_height * 0.85],
            "bbox_normalized": [0.0, 0.0, 0.6, 0.85],
            "confidence": 0.5,
            "processing_strategy": "yolo_ocr",
            "verification_status": "pending",
            "contains_dimensions": True,
            "contains_annotations": True,
        },
    ]


@router.post("/drawing-regions/{session_id}/segment")
async def segment_drawing_regions(
    session_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """도면 영역 세분화 실행

    휴리스틱 기반 + VLM 기반 영역 분석을 수행합니다.
    정면도, 측면도, 단면도, 상세도, 표제란, BOM 테이블 등을 자동 구분합니다.

    Config options:
    - use_vlm: VLM 기반 영역 분석 사용 (기본: True)
    - detect_title_block: 표제란 검출 (기본: True)
    - detect_bom_table: BOM 테이블 검출 (기본: True)
    - detect_notes: 노트 영역 검출 (기본: True)
    - detect_legend: 범례 검출 (기본: False)
    - min_region_area: 최소 영역 비율 (기본: 0.01)
    - confidence_threshold: 신뢰도 임계값 (기본: 0.3)
    - merge_overlapping: 겹치는 영역 병합 (기본: True)

    환경변수:
    - OPENAI_API_KEY: VLM 분석 시 필요
    """
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 설정 파싱
    config = config or {}
    use_vlm = config.get("use_vlm", True)

    # 이미지 경로 확인
    image_path = session.get("image_path")
    image_base64 = session.get("image_base64")
    temp_file_path = None

    # base64 이미지인 경우 임시 파일로 저장
    if not image_path and image_base64:
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                f.write(base64.b64decode(image_base64))
                temp_file_path = f.name
                image_path = temp_file_path
            logger.info(f"[Region] 임시 파일 생성: {temp_file_path}")
        except Exception as e:
            logger.warning(f"[Region] 임시 파일 생성 실패: {e}")

    # 영역 세분화 실행
    regions = []
    region_stats: Dict[str, int] = {}
    image_width = session.get("image_width", 1000)
    image_height = session.get("image_height", 1000)
    segmenter_result = None

    if image_path and Path(image_path).exists():
        try:
            # RegionSegmenter 설정 생성
            seg_config = RegionSegmentationConfig(
                min_region_area=config.get("min_region_area", 0.01),
                confidence_threshold=config.get("confidence_threshold", 0.3),
                merge_overlapping=config.get("merge_overlapping", True),
                detect_title_block=config.get("detect_title_block", True),
                detect_bom_table=config.get("detect_bom_table", True),
                detect_notes=config.get("detect_notes", True),
                detect_legend=config.get("detect_legend", False),
                auto_assign_strategy=True,
            )

            # 영역 세분화 실행
            segmenter = get_region_segmenter()
            segmenter_result = await segmenter.segment(
                session_id=session_id,
                image_path=image_path,
                config=seg_config,
                use_vlm=use_vlm
            )

            # 결과 변환
            regions = [
                {
                    "id": r.id,
                    "view_type": r.region_type.value,
                    "label": _get_region_label(r.region_type),
                    "bbox": [r.bbox.x1, r.bbox.y1, r.bbox.x2, r.bbox.y2],
                    "bbox_normalized": r.bbox_normalized,
                    "confidence": r.confidence,
                    "processing_strategy": r.processing_strategy.value,
                    "verification_status": r.verification_status.value,
                    "contains_dimensions": r.region_type in [
                        RegionType.MAIN_VIEW, RegionType.DETAIL_VIEW,
                        RegionType.SECTION_VIEW, RegionType.DIMENSION_AREA
                    ],
                    "contains_annotations": r.region_type in [
                        RegionType.NOTES, RegionType.TITLE_BLOCK
                    ],
                }
                for r in segmenter_result.regions
            ]

            image_width = segmenter_result.image_width
            image_height = segmenter_result.image_height
            region_stats = segmenter_result.region_stats

            logger.info(f"[Region] 세분화 완료 - {len(regions)}개 영역, VLM: {use_vlm}")

        except Exception as e:
            logger.error(f"[Region] 세분화 실패: {e}")
            # 폴백: 기본 휴리스틱 결과
            regions = _get_fallback_regions(session_id, image_width, image_height)
            region_stats = {"title_block": 1, "main_view": 1}
    else:
        # 이미지가 없으면 기본 휴리스틱 결과
        logger.warning(f"[Region] 세션 {session_id}에 이미지가 없습니다")
        regions = _get_fallback_regions(session_id, image_width, image_height)
        region_stats = {"title_block": 1, "main_view": 1}

    # 임시 파일 정리
    if temp_file_path:
        try:
            import os
            os.unlink(temp_file_path)
        except Exception:
            pass

    processing_time = (time.time() - start_time) * 1000

    result = {
        "session_id": session_id,
        "regions": regions,
        "total_regions": len(regions),
        "by_view_type": region_stats,
        "has_title_block": "title_block" in region_stats,
        "has_parts_list": "parts_list" in region_stats or "bom_table" in region_stats,
        "has_notes": "notes" in region_stats,
        "has_legend": "legend" in region_stats,
        "image_width": image_width,
        "image_height": image_height,
        "use_vlm": use_vlm,
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
        "has_notes": False,
        "has_legend": False,
        "image_width": 0,
        "image_height": 0,
        "use_vlm": False,
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
