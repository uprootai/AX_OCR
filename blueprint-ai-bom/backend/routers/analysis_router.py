"""Analysis Router - 분석 옵션 및 실행 API

기존 detection_router.py 패턴을 따름:
- 서비스 주입 패턴 사용
- prefix 패턴: /analysis
- session_service 연동
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
import logging

from schemas.analysis_options import (
    AnalysisOptions,
    AnalysisOptionsUpdate,
    AnalysisResult,
    PRESETS,
    apply_preset_to_options,
)
from schemas.dimension import (
    Dimension,
    DimensionResult,
    DimensionListResponse,
    DimensionUpdate,
    DimensionVerificationUpdate,
    BulkDimensionVerificationUpdate,
)
from schemas.session import SessionStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Analysis"])

# 서비스 주입을 위한 전역 변수 (detection_router.py 패턴 따름)
_dimension_service = None
_detection_service = None
_session_service = None
_relation_service = None

# 세션별 옵션 캐시 (메모리)
_session_options: Dict[str, AnalysisOptions] = {}


def set_analysis_services(dimension_service, detection_service, session_service, relation_service=None):
    """서비스 인스턴스 설정 (api_server.py에서 호출)"""
    global _dimension_service, _detection_service, _session_service, _relation_service
    _dimension_service = dimension_service
    _detection_service = detection_service
    _session_service = session_service
    _relation_service = relation_service


def get_relation_service():
    if _relation_service is None:
        raise HTTPException(status_code=500, detail="Relation service not initialized")
    return _relation_service


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

    # 세션 확인
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 캐시된 옵션 반환 또는 기본값
    if session_id in _session_options:
        return _session_options[session_id]

    # 기본 옵션 (electrical 프리셋 - 기존 동작 호환)
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

    # 현재 옵션 가져오기
    current = _session_options.get(session_id, AnalysisOptions())

    # 프리셋 적용
    if options_update.preset and options_update.preset in PRESETS:
        current = apply_preset_to_options(current, options_update.preset)
    else:
        # 개별 옵션 업데이트
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
    session_service = get_session_service()
    detection_service = get_detection_service()
    dimension_service = get_dimension_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    # 분석 옵션 가져오기
    options = _session_options.get(session_id, AnalysisOptions())

    # 결과 초기화
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

    # 1. 심볼 검출 (기존 DetectionService 사용)
    if options.enable_symbol_detection:
        try:
            session_service.update_status(session_id, SessionStatus.DETECTING)

            from schemas.detection import DetectionConfig
            config = DetectionConfig(
                confidence=options.confidence_threshold,
                model_id=options.symbol_model_type
            )

            detection_result = detection_service.detect(
                image_path=image_path,
                config=config
            )

            result.detections = detection_result.get("detections", [])
            total_time += detection_result.get("processing_time_ms", 0)

            # 세션에 검출 결과 저장
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

            # 세션에 치수 결과 저장
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
                visualize=False,  # 분석 시에는 시각화 생성 생략 가능 (성능 최적화)
            )

            line_result = line_detector_service.detect_lines(image_path, config)

            result.lines = line_result.get("lines", [])
            total_time += line_result.get("processing_time_ms", 0)

            # 세션에 선 검출 결과 저장
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

    # 4. 텍스트 추출 (TODO: Phase 2에서 구현)
    if options.enable_text_extraction:
        result.errors.append("텍스트 추출은 아직 구현되지 않았습니다 (Phase 2)")

    # ==================== 관계 분석 및 연결 (Post-Processing) ====================
    # 모든 개별 분석이 끝난 후, 가능한 연결 작업 수행
    
    # 세션 최신 상태 조회 (이전 단계에서 저장된 결과 포함)
    current_session = session_service.get_session(session_id)
    if current_session:
        dims = current_session.get("dimensions", [])
        syms = current_session.get("detections", [])
        lines_data = current_session.get("lines", [])
        
        # A. 치수선-치수 관계 분석 (치수와 선이 모두 있을 때)
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

        # B. 치수-심볼 연결 (치수와 심볼이 모두 있을 때)
        if dims and syms and (options.enable_dimension_ocr or options.enable_symbol_detection):
            try:
                line_detector_service = get_line_detector_service()
                from schemas.line import Line
                parsed_lines = [Line(**l) if isinstance(l, dict) else l for l in lines_data] if lines_data else None
                
                links = line_detector_service.link_dimensions_to_symbols(dims, syms, parsed_lines)
                
                # 링크 저장
                link_data = [link.model_dump() for link in links]
                session_service.update_session(session_id, {
                    "dimension_symbol_links": link_data,
                })
                
                # 치수에 링크 정보 업데이트
                link_map = {link.dimension_id: link.symbol_id for link in links if link.symbol_id}
                updated_dims = []
                for dim in dims:
                    dim_copy = dict(dim)
                    if dim.get("id") in link_map:
                        dim_copy["linked_to"] = link_map[dim.get("id")]
                    updated_dims.append(dim_copy)
                
                session_service.update_session(session_id, {"dimensions": updated_dims})
                
                # 결과에도 반영 (옵션)
                result.dimensions = updated_dims
                
                logger.info(f"치수-심볼 연결 완료: {len(link_data)}개")
            except Exception as e:
                logger.error(f"치수-심볼 연결 실패: {str(e)}")

        # C. Phase 2: 치수선 기반 관계 추출 (DimensionRelationService 사용)
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

                # 세션에 관계 저장
                session_service.update_session(session_id, {
                    "relations": relations
                })

                # 결과에 반영
                result.relations = relations

                rel_time = (time.time() - start_time) * 1000
                total_time += rel_time

                # 통계 로깅
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

    # 상태 업데이트
    if result.errors:
        session_service.update_status(session_id, SessionStatus.ERROR)
    else:
        session_service.update_status(session_id, SessionStatus.VERIFIED)

    return result


# ==================== 치수 관리 API ====================

@router.get("/dimensions/{session_id}")
async def get_dimensions(session_id: str) -> DimensionListResponse:
    """세션의 치수 목록 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    dimensions = session.get("dimensions", [])

    # 상태별 통계
    stats = {
        "pending": 0,
        "approved": 0,
        "rejected": 0,
        "modified": 0,
        "manual": 0,
    }
    for dim in dimensions:
        status = dim.get("verification_status", "pending")
        if status in stats:
            stats[status] += 1

    return DimensionListResponse(
        session_id=session_id,
        dimensions=dimensions,
        total=len(dimensions),
        stats=stats
    )


@router.put("/dimensions/{session_id}/{dimension_id}")
async def update_dimension(
    session_id: str,
    dimension_id: str,
    update: DimensionUpdate
) -> Dict[str, Any]:
    """치수 업데이트 (검증 포함)"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    dimensions = session.get("dimensions", [])

    # 치수 찾기
    dim_idx = None
    for idx, dim in enumerate(dimensions):
        if dim.get("id") == dimension_id:
            dim_idx = idx
            break

    if dim_idx is None:
        raise HTTPException(status_code=404, detail="치수를 찾을 수 없습니다")

    # 업데이트 적용
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            dimensions[dim_idx][key] = value

    # 세션 업데이트
    session_service.update_session(session_id, {"dimensions": dimensions})

    return {
        "session_id": session_id,
        "dimension_id": dimension_id,
        "updated": True,
        "dimension": dimensions[dim_idx]
    }


@router.put("/dimensions/{session_id}/verify/bulk")
async def bulk_verify_dimensions(
    session_id: str,
    updates: BulkDimensionVerificationUpdate
) -> Dict[str, Any]:
    """일괄 치수 검증"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    dimensions = session.get("dimensions", [])
    dim_map = {d.get("id"): idx for idx, d in enumerate(dimensions)}

    results = []
    for update in updates.updates:
        if update.dimension_id not in dim_map:
            results.append({
                "dimension_id": update.dimension_id,
                "status": "error",
                "message": "치수를 찾을 수 없습니다"
            })
            continue

        idx = dim_map[update.dimension_id]
        dimensions[idx]["verification_status"] = update.status.value

        if update.modified_value:
            dimensions[idx]["modified_value"] = update.modified_value
        if update.modified_bbox:
            dimensions[idx]["modified_bbox"] = update.modified_bbox.model_dump()

        results.append({
            "dimension_id": update.dimension_id,
            "status": "updated"
        })

    # 세션 업데이트
    session_service.update_session(session_id, {"dimensions": dimensions})

    # 통계 계산
    stats = {"pending": 0, "approved": 0, "rejected": 0, "modified": 0, "manual": 0}
    for dim in dimensions:
        status = dim.get("verification_status", "pending")
        if status in stats:
            stats[status] += 1

    return {
        "session_id": session_id,
        "results": results,
        "stats": stats
    }


@router.post("/dimensions/{session_id}/manual")
async def add_manual_dimension(
    session_id: str,
    value: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float
) -> Dict[str, Any]:
    """수동 치수 추가"""
    dimension_service = get_dimension_service()
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 수동 치수 생성
    new_dimension = dimension_service.add_manual_dimension(
        value=value,
        bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    )

    # 세션에 추가
    dimensions = session.get("dimensions", [])
    dimensions.append(new_dimension)

    session_service.update_session(session_id, {
        "dimensions": dimensions,
        "dimension_count": len(dimensions)
    })

    return {
        "session_id": session_id,
        "dimension": new_dimension,
        "message": "수동 치수가 추가되었습니다"
    }


@router.delete("/dimensions/{session_id}/{dimension_id}")
async def delete_dimension(session_id: str, dimension_id: str) -> Dict[str, Any]:
    """치수 삭제"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    dimensions = session.get("dimensions", [])
    new_dimensions = [d for d in dimensions if d.get("id") != dimension_id]

    if len(new_dimensions) == len(dimensions):
        raise HTTPException(status_code=404, detail="치수를 찾을 수 없습니다")

    session_service.update_session(session_id, {
        "dimensions": new_dimensions,
        "dimension_count": len(new_dimensions)
    })

    return {
        "session_id": session_id,
        "dimension_id": dimension_id,
        "message": "치수가 삭제되었습니다"
    }


# ==================== 선 검출 API ====================

# 선 검출 서비스 전역 변수
_line_detector_service = None


def set_line_detector_service(line_service):
    """선 검출 서비스 설정 (api_server.py에서 호출)"""
    global _line_detector_service
    _line_detector_service = line_service


def get_line_detector_service():
    if _line_detector_service is None:
        raise HTTPException(status_code=500, detail="Line detector service not initialized")
    return _line_detector_service


@router.post("/lines/{session_id}")
async def detect_lines(session_id: str) -> Dict[str, Any]:
    """
    선 검출 실행

    이미지에서 선을 검출하고 세션에 저장
    """
    session_service = get_session_service()
    line_service = get_line_detector_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    # 분석 옵션 가져오기
    options = _session_options.get(session_id, AnalysisOptions())

    try:
        # 선 검출 실행
        from schemas.line import LineDetectionConfig
        config = LineDetectionConfig(
            method="lsd",
            classify_types=True,
            classify_colors=True,
            find_intersections=True,
            visualize=True,
        )

        result = line_service.detect_lines(image_path, config)

        # 세션에 선 검출 결과 저장
        session_service.update_session(session_id, {
            "lines": result.get("lines", []),
            "intersections": result.get("intersections", []),
            "line_statistics": result.get("statistics", {}),
            "line_count": len(result.get("lines", [])),
        })

        logger.info(f"선 검출 완료: {len(result.get('lines', []))}개 선, {len(result.get('intersections', []))}개 교차점")

        return {
            "session_id": session_id,
            "lines": result.get("lines", []),
            "intersections": result.get("intersections", []),
            "statistics": result.get("statistics", {}),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "visualization_base64": result.get("visualization_base64"),
        }

    except Exception as e:
        logger.error(f"선 검출 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"선 검출 실패: {str(e)}")


@router.get("/lines/{session_id}")
async def get_lines(session_id: str) -> Dict[str, Any]:
    """세션의 선 검출 결과 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return {
        "session_id": session_id,
        "lines": session.get("lines", []),
        "intersections": session.get("intersections", []),
        "statistics": session.get("line_statistics", {}),
        "total": session.get("line_count", 0),
    }


@router.post("/lines/{session_id}/link-dimensions")
async def link_dimensions_to_symbols(session_id: str) -> Dict[str, Any]:
    """
    치수를 심볼에 연결

    치수 OCR 결과와 심볼 검출 결과를 기반으로
    각 치수를 가장 가까운 심볼에 자동 연결
    """
    session_service = get_session_service()
    line_service = get_line_detector_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    dimensions = session.get("dimensions", [])
    detections = session.get("detections", [])
    lines = session.get("lines", [])

    if not dimensions:
        return {
            "session_id": session_id,
            "links": [],
            "message": "치수가 없습니다"
        }

    if not detections:
        return {
            "session_id": session_id,
            "links": [],
            "message": "심볼이 없습니다"
        }

    # 치수-심볼 연결
    from schemas.line import Line
    parsed_lines = [Line(**l) if isinstance(l, dict) else l for l in lines]
    links = line_service.link_dimensions_to_symbols(dimensions, detections, parsed_lines)

    # 연결 정보를 세션에 저장
    link_data = [link.model_dump() for link in links]
    session_service.update_session(session_id, {
        "dimension_symbol_links": link_data,
    })

    # 치수에 연결 정보 업데이트
    link_map = {link.dimension_id: link.symbol_id for link in links if link.symbol_id}
    updated_dimensions = []
    for dim in dimensions:
        dim_copy = dict(dim)
        if dim.get("id") in link_map:
            dim_copy["linked_to"] = link_map[dim.get("id")]
        updated_dimensions.append(dim_copy)

    session_service.update_session(session_id, {"dimensions": updated_dimensions})

    return {
        "session_id": session_id,
        "links": link_data,
        "linked_count": sum(1 for link in links if link.symbol_id),
        "total_dimensions": len(dimensions),
    }


@router.post("/lines/{session_id}/find-dimension-relations")
async def find_dimension_relations(session_id: str) -> Dict[str, Any]:
    """
    치수선과 치수 간의 관계 분석

    검출된 선 중에서 치수선을 찾고,
    각 치수와의 관계(방향, 거리 등)를 분석
    """
    session_service = get_session_service()
    line_service = get_line_detector_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    lines = session.get("lines", [])
    dimensions = session.get("dimensions", [])

    if not lines:
        return {
            "session_id": session_id,
            "relations": [],
            "message": "선 검출 결과가 없습니다. 먼저 선 검출을 실행하세요."
        }

    if not dimensions:
        return {
            "session_id": session_id,
            "relations": [],
            "message": "치수가 없습니다"
        }

    # 선을 Line 객체로 변환
    from schemas.line import Line
    parsed_lines = [Line(**l) if isinstance(l, dict) else l for l in lines]

    # 치수선-치수 관계 분석
    relations = line_service.find_dimension_lines(parsed_lines, dimensions)

    # 세션에 저장
    relation_data = [rel.model_dump() for rel in relations]
    session_service.update_session(session_id, {
        "dimension_line_relations": relation_data,
    })

    return {
        "session_id": session_id,
        "relations": relation_data,
        "total": len(relations),
    }


@router.get("/lines/health")
async def check_line_detector_health() -> Dict[str, Any]:
    """Line Detector API 상태 확인"""
    try:
        line_service = get_line_detector_service()
        is_healthy = line_service.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "line-detector",
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "line-detector",
            "error": str(e),
        }
