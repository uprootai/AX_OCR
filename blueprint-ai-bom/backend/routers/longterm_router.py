"""Long-term Roadmap Router - 장기 로드맵 기능 API

기능 목록:
- 도면 영역 세분화 (Drawing Region Segmentation) ✅ 구현됨
- 노트/주석 추출 (Notes Extraction) ✅ 구현됨
- 리비전 비교 (Revision Comparison) ✅ 구현됨
- VLM 자동 분류 (VLM Auto Classification) ✅ 구현됨

분리 목적:
- analysis_router.py 크기 감소 (2,800+ lines → 모듈화)
- LLM 컨텍스트 효율성 향상
- 장기 로드맵 기능 독립 관리
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
import logging
import time
import uuid
import base64
import tempfile
from pathlib import Path

# VLM 분류 서비스
from services.vlm_classifier import vlm_classifier, get_preset_config

# 노트 추출 서비스
from services.notes_extractor import notes_extractor, NoteCategory

# 영역 세분화 서비스
from services.region_segmenter import RegionSegmenter
from schemas.region import RegionSegmentationConfig, RegionType

# 리비전 비교 서비스
from services.revision_comparator import revision_comparator

# 영역 세분화 싱글톤
_region_segmenter: Optional[RegionSegmenter] = None


def get_region_segmenter() -> RegionSegmenter:
    """영역 세분화 서비스 인스턴스 가져오기"""
    global _region_segmenter
    if _region_segmenter is None:
        _region_segmenter = RegionSegmenter()
    return _region_segmenter

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


# ============================================================
# 주석/노트 추출 (Notes Extraction)
# ============================================================

@router.post("/notes/{session_id}/extract")
async def extract_notes(
    session_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """도면 노트/주석 추출

    GPT-4o-mini (기본), GPT-4o, Claude Vision을 사용하여
    일반 노트, 재료 사양, 열처리, 표면 처리 등을 추출합니다.

    Config options:
    - provider: VLM 제공자 (openai, anthropic) - 기본: openai
    - use_ocr: 기존 OCR 결과 활용 여부 (기본: True)

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
    provider = config.get("provider", "openai")
    use_ocr = config.get("use_ocr", True)

    # 이미지 준비
    image_path = session.get("image_path")
    image_base64 = session.get("image_base64")

    if image_path and not image_base64:
        try:
            path = Path(image_path)
            if path.exists():
                with open(path, "rb") as f:
                    image_base64 = base64.b64encode(f.read()).decode("utf-8")
                logger.info(f"[Notes] 이미지 로드 완료: {image_path}")
        except Exception as e:
            logger.warning(f"[Notes] 이미지 로드 실패: {e}")

    # 기존 OCR 결과 가져오기
    ocr_texts = None
    if use_ocr:
        ocr_results = session.get("ocr_results", {})
        if ocr_results:
            ocr_texts = ocr_results.get("texts", [])

    # 노트 추출 실행
    notes = []
    materials: List[Dict[str, Any]] = []
    standards: List[str] = []
    tolerances: Dict[str, Any] = {}
    heat_treatments: List[Dict[str, Any]] = []
    surface_finishes: List[Dict[str, Any]] = []
    extraction_provider = "none"
    llm_model = None

    if image_base64:
        try:
            # 노트 추출기 호출
            extraction_result = await notes_extractor.extract_notes(
                image_base64=image_base64,
                ocr_texts=ocr_texts,
                provider=provider
            )

            # 결과 변환
            notes = [
                {
                    "id": n.id,
                    "category": n.category.value,
                    "text": n.text,
                    "confidence": n.confidence,
                    "bbox": n.bbox,
                    "source": n.source,
                    "verified": n.verified,
                    "parsed_data": n.parsed_data
                }
                for n in extraction_result.notes
            ]
            materials = extraction_result.materials
            standards = extraction_result.standards
            tolerances = extraction_result.tolerances
            heat_treatments = extraction_result.heat_treatments
            surface_finishes = extraction_result.surface_finishes
            extraction_provider = extraction_result.provider
            llm_model = notes_extractor.openai_model if extraction_provider == "openai" else None

            logger.info(f"[Notes] 추출 완료 - {len(notes)}개 노트, provider: {extraction_provider}")

        except Exception as e:
            logger.error(f"[Notes] 추출 실패: {e}")

            # OCR 결과가 있으면 규칙 기반 추출 시도
            if ocr_texts:
                try:
                    fallback_result = notes_extractor.extract_from_ocr_results(ocr_texts)
                    notes = [
                        {
                            "id": n.id,
                            "category": n.category.value,
                            "text": n.text,
                            "confidence": n.confidence,
                            "bbox": n.bbox,
                            "source": n.source,
                            "verified": n.verified
                        }
                        for n in fallback_result.notes
                    ]
                    materials = fallback_result.materials
                    standards = fallback_result.standards
                    tolerances = fallback_result.tolerances
                    extraction_provider = "regex"
                    logger.info(f"[Notes] 규칙 기반 폴백 - {len(notes)}개 노트")
                except Exception as e2:
                    logger.error(f"[Notes] 폴백도 실패: {e2}")
    else:
        logger.warning(f"[Notes] 세션 {session_id}에 이미지가 없습니다")

    # 카테고리별 집계
    by_category: Dict[str, int] = {}
    for note in notes:
        cat = note.get("category", "general")
        by_category[cat] = by_category.get(cat, 0) + 1

    processing_time = (time.time() - start_time) * 1000

    result = {
        "session_id": session_id,
        "notes": notes,
        "total_notes": len(notes),
        "by_category": by_category,
        "materials": materials,
        "standards": standards,
        "tolerances": tolerances,
        "heat_treatments": heat_treatments,
        "surface_finishes": surface_finishes,
        "extraction_provider": extraction_provider,
        "llm_model": llm_model,
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
        "heat_treatments": [],
        "surface_finishes": [],
        "extraction_provider": "none",
        "llm_model": None,
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

    이미지 기반 구조적 비교 (SSIM) + 세션 데이터 비교 + VLM 지능형 비교를 수행합니다.

    Request body:
    - session_id_old: 이전 리비전 세션 ID
    - session_id_new: 새 리비전 세션 ID
    - config: 비교 설정 (선택)
        - use_vlm: VLM 기반 비교 사용 (기본: False)
        - compare_dimensions: 치수 비교 (기본: True)
        - compare_symbols: 심볼 비교 (기본: True)
        - compare_notes: 노트 비교 (기본: True)

    환경변수:
    - OPENAI_API_KEY: VLM 비교 시 필요
    """
    start_time = time.time()

    session_id_old = request.get("session_id_old")
    session_id_new = request.get("session_id_new")
    config = request.get("config", {})

    if not session_id_old or not session_id_new:
        raise HTTPException(status_code=400, detail="session_id_old와 session_id_new가 필요합니다")

    session_service = get_session_service()

    session_old = session_service.get_session(session_id_old)
    session_new = session_service.get_session(session_id_new)

    if not session_old:
        raise HTTPException(status_code=404, detail="이전 리비전 세션을 찾을 수 없습니다")
    if not session_new:
        raise HTTPException(status_code=404, detail="새 리비전 세션을 찾을 수 없습니다")

    # 리비전 비교 실행
    try:
        comparison_result = await revision_comparator.compare_revisions(
            session_old=session_old,
            session_new=session_new,
            config=config
        )

        # 변경 사항을 직렬화 가능한 형태로 변환
        changes = [
            {
                "id": c.id,
                "change_type": c.change_type.value,
                "category": c.category.value,
                "description": c.description,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "bbox_old": c.bbox_old,
                "bbox_new": c.bbox_new,
                "confidence": c.confidence,
                "severity": c.severity.value,
                "item_id": c.item_id,
            }
            for c in comparison_result.changes
        ]

        logger.info(
            f"[Revision] 비교 완료 - {comparison_result.total_changes}개 변경점, "
            f"유사도: {comparison_result.similarity_score:.2%}"
        )

    except Exception as e:
        logger.error(f"[Revision] 비교 실패: {e}")
        changes = []
        comparison_result = None

    processing_time = (time.time() - start_time) * 1000

    if comparison_result:
        result = {
            "comparison_id": comparison_result.comparison_id,
            "session_id_old": session_id_old,
            "session_id_new": session_id_new,
            "changes": changes,
            "total_changes": comparison_result.total_changes,
            "by_type": comparison_result.by_type,
            "by_category": comparison_result.by_category,
            "added_count": comparison_result.added_count,
            "removed_count": comparison_result.removed_count,
            "modified_count": comparison_result.modified_count,
            "similarity_score": comparison_result.similarity_score,
            "alignment_score": comparison_result.alignment_score,
            "diff_image_base64": comparison_result.diff_image_base64,
            "comparison_provider": comparison_result.provider,
            "processing_time_ms": processing_time,
        }
    else:
        result = {
            "comparison_id": str(uuid.uuid4()),
            "session_id_old": session_id_old,
            "session_id_new": session_id_new,
            "changes": [],
            "total_changes": 0,
            "by_type": {},
            "by_category": {},
            "added_count": 0,
            "removed_count": 0,
            "modified_count": 0,
            "similarity_score": 0.0,
            "alignment_score": 0.0,
            "diff_image_base64": None,
            "comparison_provider": "error",
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
        "comparison_id": None,
        "session_id_old": None,
        "session_id_new": session_id,
        "changes": [],
        "total_changes": 0,
        "by_type": {},
        "by_category": {},
        "added_count": 0,
        "removed_count": 0,
        "modified_count": 0,
        "similarity_score": 0.0,
        "alignment_score": 0.0,
        "diff_image_base64": None,
        "comparison_provider": "none",
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
                "bom_generation"
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
