"""Core Analysis Router - 프리셋, 옵션, 분석 실행 API

분할된 analysis_router.py의 핵심 기능:
- 프리셋 목록 및 적용
- 분석 옵션 관리
- 통합 분석 실행
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging

from schemas.analysis_options import (
    AnalysisOptions,
    AnalysisOptionsUpdate,
    AnalysisResult,
    PRESETS,
    apply_preset_to_options,
)
from schemas.session import SessionStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Analysis Core"])

# 서비스 주입을 위한 전역 변수
_dimension_service = None
_detection_service = None
_session_service = None
_relation_service = None

# 세션별 옵션 캐시 (메모리) - 다른 라우터에서도 접근 필요
_session_options: Dict[str, AnalysisOptions] = {}


def set_core_services(dimension_service, detection_service, session_service, relation_service=None):
    """서비스 인스턴스 설정 (api_server.py에서 호출)"""
    global _dimension_service, _detection_service, _session_service, _relation_service
    _dimension_service = dimension_service
    _detection_service = detection_service
    _session_service = session_service
    _relation_service = relation_service


def get_dimension_service():
    if _dimension_service is None:
        raise HTTPException(status_code=500, detail="Dimension service not initialized")
    return _dimension_service


def get_detection_service():
    if _detection_service is None:
        raise HTTPException(status_code=500, detail="Detection service not initialized")
    return _detection_service


def get_session_service():
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


def get_relation_service():
    if _relation_service is None:
        raise HTTPException(status_code=500, detail="Relation service not initialized")
    return _relation_service


def get_session_options():
    """세션 옵션 딕셔너리 반환 (다른 라우터에서 접근용)"""
    return _session_options


# ==================== 프리셋 API ====================

@router.get("/presets")
async def list_presets():
    """사용 가능한 프리셋 목록"""
    presets_list = []
    for preset_id, preset_data in PRESETS.items():
        presets_list.append({
            "id": preset_id,
            "name": preset_data.get("name", preset_id),
            "description": preset_data.get("description", ""),
            "icon": preset_data.get("icon", "📋"),
        })
    return {"presets": presets_list}


# ==================== 분석 옵션 API ====================

@router.get("/options/{session_id}")
async def get_analysis_options(session_id: str) -> AnalysisOptions:
    """세션의 분석 옵션 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if session_id in _session_options:
        return _session_options[session_id]

    default_options = AnalysisOptions(preset="electrical")
    return apply_preset_to_options(default_options, "electrical")


@router.put("/options/{session_id}")
async def update_analysis_options(
    session_id: str,
    options_update: AnalysisOptionsUpdate
) -> AnalysisOptions:
    """세션의 분석 옵션 업데이트"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    current = _session_options.get(session_id, AnalysisOptions())

    if options_update.preset and options_update.preset in PRESETS:
        current = apply_preset_to_options(current, options_update.preset)
    else:
        update_data = options_update.model_dump(exclude_unset=True, exclude={'preset'})
        current_data = current.model_dump()
        for key, value in update_data.items():
            if value is not None:
                current_data[key] = value
        current = AnalysisOptions(**current_data)

    _session_options[session_id] = current
    return current


@router.post("/options/{session_id}/preset/{preset_name}")
async def apply_preset(session_id: str, preset_name: str) -> AnalysisOptions:
    """프리셋 적용"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if preset_name not in PRESETS:
        raise HTTPException(status_code=400, detail=f"Unknown preset: {preset_name}")

    options = apply_preset_to_options(AnalysisOptions(), preset_name)
    _session_options[session_id] = options

    return options


# ==================== 분석 실행 API ====================

@router.post("/run/{session_id}")
async def run_analysis(session_id: str) -> AnalysisResult:
    """
    분석 실행

    설정된 옵션에 따라 해당 분석 실행.
    - enable_symbol_detection: YOLO 심볼 검출
    - enable_dimension_ocr: eDOCr2 치수 인식
    """
    # 지연 임포트 (순환 참조 방지)
    from .line_router import get_line_detector_service

    session_service = get_session_service()
    detection_service = get_detection_service()
    dimension_service = get_dimension_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    options = _session_options.get(session_id, AnalysisOptions())

    result = AnalysisResult(
        session_id=session_id,
        options=options,
        detections=[],
        dimensions=[],
        lines=[],
        texts=[],
        relations=[],
        processing_time_ms=0.0,
        errors=[]
    )

    total_time = 0.0

    # 1. 심볼 검출
    if options.enable_symbol_detection:
        try:
            session_service.update_status(session_id, SessionStatus.DETECTING)

            from schemas.detection import DetectionConfig
            config = DetectionConfig(
                confidence=options.confidence_threshold,
                model_type=options.symbol_model_type  # panasia 모델 사용
            )

            detection_result = detection_service.detect(
                image_path=image_path,
                config=config
            )

            result.detections = detection_result.get("detections", [])
            total_time += detection_result.get("processing_time_ms", 0)

            session_service.set_detections(
                session_id=session_id,
                detections=detection_result["detections"],
                image_width=detection_result["image_width"],
                image_height=detection_result["image_height"]
            )

            logger.info(f"심볼 검출 완료: {len(result.detections)}개")

        except Exception as e:
            error_msg = f"심볼 검출 실패: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    # 2. 치수 OCR
    if options.enable_dimension_ocr:
        try:
            dimension_result = dimension_service.extract_dimensions(
                image_path=image_path,
                confidence_threshold=options.confidence_threshold
            )

            result.dimensions = dimension_result.get("dimensions", [])
            total_time += dimension_result.get("processing_time_ms", 0)

            session_service.update_session(session_id, {
                "dimensions": result.dimensions,
                "dimension_count": len(result.dimensions),
            })

            logger.info(f"치수 OCR 완료: {len(result.dimensions)}개")

        except Exception as e:
            error_msg = f"치수 OCR 실패: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    # 3. 선 검출
    if options.enable_line_detection:
        try:
            line_detector_service = get_line_detector_service()

            from schemas.line import LineDetectionConfig
            config = LineDetectionConfig(
                method="lsd",
                classify_types=True,
                classify_colors=True,
                find_intersections=True,
                visualize=False,
            )

            line_result = line_detector_service.detect_lines(image_path, config)

            result.lines = line_result.get("lines", [])
            total_time += line_result.get("processing_time_ms", 0)

            session_service.update_session(session_id, {
                "lines": result.lines,
                "intersections": line_result.get("intersections", []),
                "line_statistics": line_result.get("statistics", {}),
                "line_count": len(result.lines),
            })

            logger.info(f"선 검출 완료: {len(result.lines)}개")

        except Exception as e:
            error_msg = f"선 검출 실패: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    # 4. 텍스트 추출 (TODO)
    if options.enable_text_extraction:
        result.errors.append("텍스트 추출은 아직 구현되지 않았습니다 (Phase 2)")

    # ==================== 관계 분석 (Post-Processing) ====================
    current_session = session_service.get_session(session_id)
    if current_session:
        dims = current_session.get("dimensions", [])
        syms = current_session.get("detections", [])
        lines_data = current_session.get("lines", [])

        # A. 치수선-치수 관계 분석
        if dims and lines_data and options.enable_line_detection:
            try:
                line_detector_service = get_line_detector_service()
                from schemas.line import Line
                parsed_lines = [Line(**l) if isinstance(l, dict) else l for l in lines_data]

                relations = line_detector_service.find_dimension_lines(parsed_lines, dims)

                session_service.update_session(session_id, {
                    "dimension_line_relations": [rel.model_dump() for rel in relations],
                })
                logger.info(f"치수선 관계 분석 완료: {len(relations)}개")
            except Exception as e:
                logger.error(f"치수선 관계 분석 실패: {str(e)}")

        # B. 치수-심볼 연결
        if dims and syms and (options.enable_dimension_ocr or options.enable_symbol_detection):
            try:
                line_detector_service = get_line_detector_service()
                from schemas.line import Line
                parsed_lines = [Line(**l) if isinstance(l, dict) else l for l in lines_data] if lines_data else None

                links = line_detector_service.link_dimensions_to_symbols(dims, syms, parsed_lines)

                link_data = [link.model_dump() for link in links]
                session_service.update_session(session_id, {
                    "dimension_symbol_links": link_data,
                })

                link_map = {link.dimension_id: link.symbol_id for link in links if link.symbol_id}
                updated_dims = []
                for dim in dims:
                    dim_copy = dict(dim)
                    if dim.get("id") in link_map:
                        dim_copy["linked_to"] = link_map[dim.get("id")]
                    updated_dims.append(dim_copy)

                session_service.update_session(session_id, {"dimensions": updated_dims})
                result.dimensions = updated_dims

                logger.info(f"치수-심볼 연결 완료: {len(link_data)}개")
            except Exception as e:
                logger.error(f"치수-심볼 연결 실패: {str(e)}")

        # C. 치수선 기반 관계 추출
        if dims and options.enable_relation_extraction:
            try:
                import time
                start_time = time.time()

                relation_service = get_relation_service()
                relations = relation_service.extract_relations(
                    dimensions=dims,
                    symbols=syms,
                    lines=lines_data
                )

                session_service.update_session(session_id, {
                    "relations": relations
                })

                result.relations = relations

                rel_time = (time.time() - start_time) * 1000
                total_time += rel_time

                method_counts = {}
                for rel in relations:
                    method = rel.get("method", "proximity")
                    method_counts[method] = method_counts.get(method, 0) + 1

                logger.info(f"치수선 기반 관계 추출 완료: {len(relations)}개 (방법별: {method_counts})")

            except Exception as e:
                error_msg = f"관계 추출 실패: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)

    result.processing_time_ms = total_time

    if result.errors:
        session_service.update_status(session_id, SessionStatus.ERROR)
    else:
        session_service.update_status(session_id, SessionStatus.VERIFIED)

    return result
