"""View Labels Router - 뷰 라벨 인식 API (장기 로드맵)

longterm_router.py에서 분리된 뷰 라벨 추출 기능:
- 뷰 라벨 추출 (POST /analysis/view-labels/{session_id})
- 뷰 라벨 결과 조회 (GET /analysis/view-labels/{session_id})
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging

from services.view_label_extractor import view_label_extractor, ViewType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["View Labels"])

# Session 서비스 의존성
_session_service = None


def set_viewlabels_services(session_service):
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


@router.post("/view-labels/{session_id}")
async def extract_view_labels(session_id: str) -> Dict[str, Any]:
    """뷰 라벨 추출 (SECTION A-A, DETAIL B 등)

    세션의 OCR 결과에서 뷰 라벨을 추출합니다.
    - SECTION: 단면도 (SECTION A-A, 단면 A-A)
    - DETAIL: 상세도 (DETAIL B, DETAIL C SCALE 2:1)
    - VIEW: 투영도 (VIEW A-A)
    - ENLARGED: 확대도 (ENLARGED VIEW)
    - 한국어: 정면도, 측면도, 평면도 등

    Returns:
        view_labels: 추출된 뷰 라벨 목록
        cutting_line_markers: 절단선 마커 (A, B 등)
        total_views: 총 뷰 개수
        by_type: 타입별 개수
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # OCR 결과 가져오기 (dimensions에서 텍스트 추출 또는 texts)
    ocr_results = []

    # 1. dimensions에서 텍스트 추출
    dimensions = session.get("dimensions", [])
    for dim in dimensions:
        if dim.get("text"):
            ocr_results.append({
                "text": dim.get("text"),
                "bbox": dim.get("bbox"),
                "confidence": dim.get("confidence", 0.5),
            })

    # 2. texts에서 추출
    texts = session.get("texts", [])
    for t in texts:
        if isinstance(t, dict):
            if t.get("full_text"):
                ocr_results.append({
                    "text": t.get("full_text"),
                    "bbox": t.get("bbox"),
                    "confidence": t.get("confidence", 0.5),
                })
            elif t.get("text"):
                ocr_results.append({
                    "text": t.get("text"),
                    "bbox": t.get("bbox"),
                    "confidence": t.get("confidence", 0.5),
                })
            # detections 내 개별 텍스트도 확인
            for det in t.get("detections", []):
                if det.get("text"):
                    ocr_results.append({
                        "text": det.get("text"),
                        "bbox": det.get("bbox"),
                        "confidence": det.get("confidence", 0.5),
                    })

    # 3. text_regions에서 추출
    text_regions = session.get("text_regions", [])
    for tr in text_regions:
        for det in tr.get("detections", []):
            if det.get("text"):
                ocr_results.append({
                    "text": det.get("text"),
                    "bbox": det.get("bbox"),
                    "confidence": det.get("confidence", 0.5),
                })

    # 이미지 크기 가져오기 (있으면)
    image_width = session.get("image_width")
    image_height = session.get("image_height")

    # 뷰 라벨 추출
    extraction_result = view_label_extractor.extract_view_labels(
        ocr_results=ocr_results,
        image_width=image_width,
        image_height=image_height,
    )

    # 결과 직렬화
    view_labels_data = []
    for vl in extraction_result.view_labels:
        view_labels_data.append({
            "id": vl.id,
            "view_type": vl.view_type.value,
            "identifier": vl.identifier,
            "scale": vl.scale,
            "full_text": vl.full_text,
            "bbox": vl.bbox,
            "confidence": vl.confidence,
            "source": vl.source,
            "cutting_line_markers": vl.cutting_line_markers,
        })

    result = {
        "session_id": session_id,
        "view_labels": view_labels_data,
        "cutting_line_markers": extraction_result.cutting_line_markers,
        "total_views": extraction_result.total_views,
        "by_type": extraction_result.by_type,
        "processing_time_ms": extraction_result.processing_time_ms,
    }

    # 세션에 저장
    session_service.update_session(session_id, {"view_labels": result})

    logger.info(
        f"뷰 라벨 추출 완료: {session_id} - "
        f"{extraction_result.total_views}개 뷰, "
        f"타입별: {extraction_result.by_type}"
    )

    return result


@router.get("/view-labels/{session_id}")
async def get_view_labels(session_id: str) -> Dict[str, Any]:
    """뷰 라벨 추출 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return session.get("view_labels", {
        "session_id": session_id,
        "view_labels": [],
        "cutting_line_markers": [],
        "total_views": 0,
        "by_type": {},
        "processing_time_ms": 0,
    })
