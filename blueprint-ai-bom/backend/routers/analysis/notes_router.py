"""Notes Router - 노트/주석 추출 API (장기 로드맵)

longterm_router.py에서 분리된 노트 추출 기능:
- 노트 추출 실행 (POST /analysis/notes/{session_id}/extract)
- 노트 결과 조회 (GET /analysis/notes/{session_id})
- 노트 정보 수정 (PUT /analysis/notes/{session_id}/{note_id})
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
import logging
import time
import base64
from pathlib import Path

from services.notes_extractor import notes_extractor, NoteCategory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Notes Extraction"])

# Session 서비스 의존성
_session_service = None


def set_notes_services(session_service):
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
