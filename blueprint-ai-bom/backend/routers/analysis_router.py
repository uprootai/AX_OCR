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
    BulkDimensionImport,
    BulkDimensionImportResponse,
)
from schemas.session import SessionStatus
from schemas.region import (
    Region,
    RegionSegmentationConfig,
    RegionSegmentationRequest,
    RegionSegmentationResult,
    RegionUpdate,
    BulkRegionUpdate,
    ManualRegion,
    RegionProcessingResult,
    RegionListResponse,
    TitleBlockData,
    RegionType,
)
from schemas.gdt import (
    GeometricCharacteristic,
    MaterialCondition,
    GDTCategory,
    FeatureControlFrame,
    DatumFeature,
    GDTParsingConfig,
    GDTParsingResult,
    FCFUpdate,
    BulkFCFUpdate,
    ManualFCF,
    ManualDatum,
    GDTListResponse,
    GDTSummary,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Analysis"])

# 서비스 주입을 위한 전역 변수 (detection_router.py 패턴 따름)
_dimension_service = None
_detection_service = None
_session_service = None
_relation_service = None
_region_segmenter = None
_gdt_parser = None

# 세션별 옵션 캐시 (메모리)
_session_options: Dict[str, AnalysisOptions] = {}


def set_analysis_services(dimension_service, detection_service, session_service, relation_service=None, region_segmenter=None):
    """서비스 인스턴스 설정 (api_server.py에서 호출)"""
    global _dimension_service, _detection_service, _session_service, _relation_service, _region_segmenter
    _dimension_service = dimension_service
    _detection_service = detection_service
    _session_service = session_service
    _relation_service = relation_service
    _region_segmenter = region_segmenter


def set_region_segmenter(region_segmenter):
    """영역 분할 서비스 설정"""
    global _region_segmenter
    _region_segmenter = region_segmenter


def set_gdt_parser(gdt_parser):
    """GD&T 파서 서비스 설정"""
    global _gdt_parser
    _gdt_parser = gdt_parser


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


def get_region_segmenter():
    if _region_segmenter is None:
        raise HTTPException(status_code=500, detail="Region segmenter not initialized")
    return _region_segmenter


def get_gdt_parser():
    if _gdt_parser is None:
        raise HTTPException(status_code=500, detail="GDT parser not initialized")
    return _gdt_parser


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


@router.post("/dimensions/{session_id}/import-bulk", response_model=BulkDimensionImportResponse)
async def import_dimensions_bulk(
    session_id: str,
    request: BulkDimensionImport
) -> BulkDimensionImportResponse:
    """eDOCr2 치수 결과 일괄 가져오기

    BlueprintFlow 파이프라인에서 eDOCr2 노드의 결과를
    Blueprint AI BOM 세션에 저장합니다.

    Args:
        session_id: 세션 ID
        request: eDOCr2 치수 목록 및 설정

    Returns:
        가져온 치수 정보 및 통계
    """
    import uuid
    from schemas.detection import VerificationStatus

    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    existing_dimensions = session.get("dimensions", [])
    imported_dimensions = []
    auto_approved_count = 0

    # eDOCr2 → DimensionType 매핑
    EDOCR2_TYPE_MAPPING = {
        "linear": "length",
        "diameter": "diameter",
        "radius": "radius",
        "angle": "angle",
        "tolerance": "tolerance",
        "surface_finish": "surface_finish",
        "text_dimension": "unknown",
        "text": "unknown",
        "unknown": "unknown",
    }

    for idx, dim_data in enumerate(request.dimensions):
        try:
            # eDOCr2 형식에서 Blueprint AI BOM 형식으로 변환
            # eDOCr2 출력: {text, bbox: {x1, y1, x2, y2}, confidence, ...}
            dim_id = f"dim_{uuid.uuid4().hex[:8]}"

            # bbox 정규화 (eDOCr2는 여러 형식 지원)
            bbox_raw = dim_data.get("bbox", {})
            if isinstance(bbox_raw, dict):
                bbox = {
                    "x1": int(bbox_raw.get("x1", bbox_raw.get("x", 0))),
                    "y1": int(bbox_raw.get("y1", bbox_raw.get("y", 0))),
                    "x2": int(bbox_raw.get("x2", bbox_raw.get("x", 0) + bbox_raw.get("width", 0))),
                    "y2": int(bbox_raw.get("y2", bbox_raw.get("y", 0) + bbox_raw.get("height", 0))),
                }
            elif isinstance(bbox_raw, list) and len(bbox_raw) >= 4:
                bbox = {
                    "x1": int(bbox_raw[0]),
                    "y1": int(bbox_raw[1]),
                    "x2": int(bbox_raw[2]),
                    "y2": int(bbox_raw[3]),
                }
            else:
                logger.warning(f"알 수 없는 bbox 형식: {bbox_raw}")
                continue

            # 신뢰도 추출
            confidence = float(dim_data.get("confidence", 0.5))

            # 자동 승인 처리
            verification_status = "pending"
            if request.auto_approve_threshold and confidence >= request.auto_approve_threshold:
                verification_status = "approved"
                auto_approved_count += 1

            # 치수 값 추출 (text 또는 value 필드)
            value = dim_data.get("value") or dim_data.get("text", "")

            # eDOCr2 타입을 DimensionType으로 변환
            raw_type = dim_data.get("type", dim_data.get("dimension_type", "unknown"))
            mapped_type = EDOCR2_TYPE_MAPPING.get(raw_type, "unknown")

            dimension = Dimension(
                id=dim_id,
                bbox=bbox,
                value=value,
                raw_text=dim_data.get("raw_text", value),
                unit=dim_data.get("unit"),
                tolerance=dim_data.get("tolerance"),
                dimension_type=mapped_type,
                confidence=confidence,
                model_id=request.source,
                verification_status=verification_status,
            )

            imported_dimensions.append(dimension.model_dump())

        except Exception as e:
            logger.warning(f"치수 변환 중 오류 (인덱스 {idx}): {e}")
            continue

    # 기존 치수에 추가
    all_dimensions = existing_dimensions + imported_dimensions

    # 세션 업데이트
    session_service.update_session(session_id, {
        "dimensions": all_dimensions,
        "dimension_count": len(all_dimensions)
    })

    logger.info(f"세션 {session_id}: {len(imported_dimensions)}개 치수 가져옴 (자동 승인: {auto_approved_count})")

    return BulkDimensionImportResponse(
        session_id=session_id,
        imported_count=len(imported_dimensions),
        auto_approved_count=auto_approved_count,
        dimensions=imported_dimensions,
        message=f"{len(imported_dimensions)}개 치수를 가져왔습니다"
    )


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


# ==================== 연결성 분석 API ====================

# 연결성 분석 서비스 전역 변수
_connectivity_analyzer = None


def set_connectivity_analyzer(analyzer):
    """연결성 분석 서비스 설정 (api_server.py에서 호출)"""
    global _connectivity_analyzer
    _connectivity_analyzer = analyzer


def get_connectivity_analyzer():
    if _connectivity_analyzer is None:
        raise HTTPException(status_code=500, detail="Connectivity analyzer not initialized")
    return _connectivity_analyzer


@router.post("/connectivity/{session_id}")
async def analyze_connectivity(session_id: str) -> Dict[str, Any]:
    """
    심볼 연결성 분석

    심볼 검출 결과와 선 검출 결과를 기반으로
    심볼 간의 연결 관계를 분석합니다.
    """
    session_service = get_session_service()
    analyzer = get_connectivity_analyzer()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    detections = session.get("detections", [])
    if not detections:
        return {
            "session_id": session_id,
            "nodes": {},
            "connections": [],
            "statistics": {"total_symbols": 0},
            "message": "심볼이 없습니다. 먼저 심볼 검출을 실행하세요."
        }

    # 선 검출 결과 (있는 경우)
    lines = session.get("lines", [])
    intersections = session.get("intersections", [])

    # 연결성 분석 실행
    result = analyzer.analyze(
        symbols=detections,
        lines=lines if lines else None,
        intersections=intersections if intersections else None,
    )

    # 세션에 저장
    session_service.update_session(session_id, {
        "connectivity_graph": result,
        "connectivity_analyzed": True,
    })

    logger.info(
        f"연결성 분석 완료: {result['statistics']['total_symbols']}개 심볼, "
        f"{result['statistics']['total_connections']}개 연결"
    )

    return {
        "session_id": session_id,
        **result,
    }


@router.get("/connectivity/{session_id}")
async def get_connectivity(session_id: str) -> Dict[str, Any]:
    """세션의 연결성 분석 결과 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    graph = session.get("connectivity_graph", {})
    if not graph:
        return {
            "session_id": session_id,
            "analyzed": False,
            "message": "연결성 분석이 수행되지 않았습니다. POST /analysis/connectivity/{session_id}를 호출하세요."
        }

    return {
        "session_id": session_id,
        "analyzed": True,
        **graph,
    }


@router.get("/connectivity/{session_id}/path")
async def find_connection_path(
    session_id: str,
    source_id: str,
    target_id: str,
) -> Dict[str, Any]:
    """
    두 심볼 사이의 연결 경로 찾기

    Args:
        session_id: 세션 ID
        source_id: 시작 심볼 ID
        target_id: 목표 심볼 ID
    """
    session_service = get_session_service()
    analyzer = get_connectivity_analyzer()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    graph = session.get("connectivity_graph", {})
    if not graph:
        raise HTTPException(
            status_code=400,
            detail="연결성 분석이 수행되지 않았습니다"
        )

    path = analyzer.find_path(graph, source_id, target_id)

    if path is None:
        return {
            "session_id": session_id,
            "source_id": source_id,
            "target_id": target_id,
            "path": None,
            "connected": False,
            "message": "연결 경로를 찾을 수 없습니다"
        }

    return {
        "session_id": session_id,
        "source_id": source_id,
        "target_id": target_id,
        "path": path,
        "path_length": len(path),
        "connected": True,
    }


@router.get("/connectivity/{session_id}/component/{symbol_id}")
async def get_connected_component(
    session_id: str,
    symbol_id: str,
) -> Dict[str, Any]:
    """
    심볼이 속한 연결 컴포넌트 조회

    Args:
        session_id: 세션 ID
        symbol_id: 심볼 ID
    """
    session_service = get_session_service()
    analyzer = get_connectivity_analyzer()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    graph = session.get("connectivity_graph", {})
    if not graph:
        raise HTTPException(
            status_code=400,
            detail="연결성 분석이 수행되지 않았습니다"
        )

    component = analyzer.get_connected_component(graph, symbol_id)

    return {
        "session_id": session_id,
        "symbol_id": symbol_id,
        "component": component,
        "size": len(component),
    }


# ==================== 영역 분할 API (Phase 5) ====================

@router.post("/regions/{session_id}/segment", response_model=RegionSegmentationResult)
async def segment_regions(
    session_id: str,
    config: Optional[RegionSegmentationConfig] = None,
    use_vlm: bool = False,
) -> RegionSegmentationResult:
    """
    도면 영역 분할 실행

    도면을 다음 영역으로 분할:
    - 표제란 (Title Block): 메타데이터 추출
    - 메인 뷰 (Main View): YOLO + OCR 적용
    - BOM 테이블: 테이블 파싱
    - 범례 (Legend): 심볼 매칭
    - 노트/주석 영역: OCR 적용

    Args:
        session_id: 세션 ID
        config: 분할 설정 (선택)
        use_vlm: VLM 영역 검출 활성화 (Phase 4 연동)
    """
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    try:
        result = await segmenter.segment(
            session_id=session_id,
            image_path=image_path,
            config=config,
            use_vlm=use_vlm,
        )

        # 세션에 영역 정보 저장
        session_service.update_session(session_id, {
            "regions": [r.model_dump() for r in result.regions],
            "region_stats": result.region_stats,
        })

        return result

    except Exception as e:
        logger.error(f"영역 분할 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regions/{session_id}", response_model=RegionListResponse)
async def get_regions(session_id: str) -> RegionListResponse:
    """세션의 영역 목록 조회"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    regions = segmenter.get_regions(session_id)

    return RegionListResponse(
        session_id=session_id,
        regions=regions,
        total=len(regions),
    )


@router.get("/regions/{session_id}/{region_id}", response_model=Region)
async def get_region(session_id: str, region_id: str) -> Region:
    """특정 영역 조회"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    region = segmenter.get_region(session_id, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="영역을 찾을 수 없습니다")

    return region


@router.put("/regions/{session_id}/{region_id}", response_model=Region)
async def update_region(
    session_id: str,
    region_id: str,
    update: RegionUpdate,
) -> Region:
    """영역 업데이트"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # region_id 설정
    update.region_id = region_id

    updated = segmenter.update_region(session_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="영역을 찾을 수 없습니다")

    return updated


@router.put("/regions/{session_id}/bulk", response_model=List[Region])
async def bulk_update_regions(
    session_id: str,
    bulk_update: BulkRegionUpdate,
) -> List[Region]:
    """일괄 영역 업데이트"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    results = []
    for update in bulk_update.updates:
        updated = segmenter.update_region(session_id, update)
        if updated:
            results.append(updated)

    return results


@router.post("/regions/{session_id}/add", response_model=Region)
async def add_manual_region(
    session_id: str,
    manual_region: ManualRegion,
) -> Region:
    """수동 영역 추가"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 이미지 크기 가져오기 (없으면 파일에서 로드)
    image_width = session.get("image_width")
    image_height = session.get("image_height")

    if not image_width or not image_height:
        # 파일에서 이미지 크기 로드
        from PIL import Image
        file_path = session.get("file_path")
        if file_path:
            try:
                with Image.open(file_path) as img:
                    image_width, image_height = img.size
                    # 세션에 저장
                    session_service.update_session(session_id, {
                        "image_width": image_width,
                        "image_height": image_height,
                    })
            except Exception:
                # 기본값 사용
                image_width = 1000
                image_height = 1000
        else:
            image_width = 1000
            image_height = 1000

    region = segmenter.add_region(
        session_id=session_id,
        manual_region=manual_region,
        image_width=image_width,
        image_height=image_height,
    )

    return region


@router.delete("/regions/{session_id}/{region_id}")
async def delete_region(session_id: str, region_id: str) -> Dict[str, Any]:
    """영역 삭제"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    deleted = segmenter.delete_region(session_id, region_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="영역을 찾을 수 없습니다")

    return {"deleted": True, "region_id": region_id}


@router.post("/regions/{session_id}/{region_id}/process", response_model=RegionProcessingResult)
async def process_region(
    session_id: str,
    region_id: str,
) -> RegionProcessingResult:
    """
    단일 영역 처리

    영역 타입과 처리 전략에 따라 적절한 처리 수행:
    - YOLO_OCR: YOLO 검출 + OCR
    - OCR_ONLY: OCR만 적용
    - TABLE_PARSE: 테이블 파싱
    - METADATA_EXTRACT: 메타데이터 추출 (표제란)
    - SYMBOL_MATCH: 심볼 매칭 (범례)
    """
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    result = await segmenter.process_region(session_id, region_id, image_path)
    if not result:
        raise HTTPException(status_code=404, detail="영역을 찾을 수 없습니다")

    return result


@router.post("/regions/{session_id}/process-all")
async def process_all_regions(session_id: str) -> Dict[str, Any]:
    """모든 영역 처리"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    regions = segmenter.get_regions(session_id)
    results = []
    success_count = 0
    error_count = 0

    for region in regions:
        result = await segmenter.process_region(session_id, region.id, image_path)
        if result:
            results.append(result.model_dump())
            if result.success:
                success_count += 1
            else:
                error_count += 1

    return {
        "session_id": session_id,
        "total_regions": len(regions),
        "processed": success_count + error_count,
        "success": success_count,
        "errors": error_count,
        "results": results,
    }


# ==================== GD&T 파싱 API (Phase 7) ====================

@router.post("/gdt/{session_id}/parse", response_model=GDTParsingResult)
async def parse_gdt(
    session_id: str,
    config: Optional[GDTParsingConfig] = None,
) -> GDTParsingResult:
    """
    GD&T (기하공차) 파싱 실행

    도면에서 다음 요소를 검출:
    - Feature Control Frame (FCF): 기하공차 프레임
    - 14가지 기하 특성 (직진도, 평면도, 원통도 등)
    - 데이텀 참조 (A, B, C 등)
    - 재료 조건 수정자 (MMC, LMC, RFS)

    Args:
        session_id: 세션 ID
        config: GD&T 파싱 설정 (선택)
    """
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    # 기존 OCR 결과 가져오기 (있으면 재사용, 없으면 새로 실행)
    ocr_results = session.get("ocr_results")  # None이면 OCR 새로 실행

    try:
        result = await gdt_parser.parse(
            session_id=session_id,
            image_path=image_path,
            config=config,
            ocr_results=ocr_results,
        )

        # 세션에 GD&T 정보 저장
        session_service.update_session(session_id, {
            "gdt_fcf_list": [fcf.model_dump() for fcf in result.fcf_list],
            "gdt_datums": [d.model_dump() for d in result.datums],
            "gdt_fcf_count": result.total_fcf,
            "gdt_datum_count": result.total_datums,
        })

        return result

    except Exception as e:
        logger.error(f"GD&T 파싱 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gdt/{session_id}", response_model=GDTListResponse)
async def get_gdt(session_id: str) -> GDTListResponse:
    """세션의 GD&T 결과 조회"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    fcf_list = gdt_parser.get_fcf_list(session_id)
    datums = gdt_parser.get_datums(session_id)

    return GDTListResponse(
        session_id=session_id,
        fcf_list=fcf_list,
        datums=datums,
        total_fcf=len(fcf_list),
        total_datums=len(datums),
    )


@router.get("/gdt/{session_id}/fcf/{fcf_id}", response_model=FeatureControlFrame)
async def get_fcf(session_id: str, fcf_id: str) -> FeatureControlFrame:
    """특정 FCF 조회"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    fcf = gdt_parser.get_fcf(session_id, fcf_id)
    if not fcf:
        raise HTTPException(status_code=404, detail="FCF를 찾을 수 없습니다")

    return fcf


@router.put("/gdt/{session_id}/fcf/{fcf_id}", response_model=FeatureControlFrame)
async def update_fcf(
    session_id: str,
    fcf_id: str,
    update: FCFUpdate,
) -> FeatureControlFrame:
    """FCF 업데이트"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # fcf_id 설정
    update.fcf_id = fcf_id

    updated = gdt_parser.update_fcf(session_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="FCF를 찾을 수 없습니다")

    return updated


@router.put("/gdt/{session_id}/fcf/bulk")
async def bulk_update_fcf(
    session_id: str,
    bulk_update: BulkFCFUpdate,
) -> Dict[str, Any]:
    """일괄 FCF 업데이트"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    results = []
    for update in bulk_update.updates:
        updated = gdt_parser.update_fcf(session_id, update)
        results.append({
            "fcf_id": update.fcf_id,
            "updated": updated is not None,
        })

    return {
        "session_id": session_id,
        "results": results,
        "updated_count": sum(1 for r in results if r["updated"]),
    }


@router.post("/gdt/{session_id}/fcf/add", response_model=FeatureControlFrame)
async def add_manual_fcf(
    session_id: str,
    manual_fcf: ManualFCF,
) -> FeatureControlFrame:
    """수동 FCF 추가"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 이미지 크기 가져오기 (없으면 파일에서 로드)
    image_width = session.get("image_width")
    image_height = session.get("image_height")

    if not image_width or not image_height:
        from PIL import Image
        file_path = session.get("file_path")
        if file_path:
            try:
                with Image.open(file_path) as img:
                    image_width, image_height = img.size
                    session_service.update_session(session_id, {
                        "image_width": image_width,
                        "image_height": image_height,
                    })
            except Exception:
                image_width = 1000
                image_height = 1000
        else:
            image_width = 1000
            image_height = 1000

    fcf = gdt_parser.add_fcf(
        session_id=session_id,
        manual_fcf=manual_fcf,
        image_width=image_width,
        image_height=image_height,
    )

    return fcf


@router.delete("/gdt/{session_id}/fcf/{fcf_id}")
async def delete_fcf(session_id: str, fcf_id: str) -> Dict[str, Any]:
    """FCF 삭제"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    deleted = gdt_parser.delete_fcf(session_id, fcf_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="FCF를 찾을 수 없습니다")

    return {"deleted": True, "fcf_id": fcf_id}


@router.post("/gdt/{session_id}/datum/add", response_model=DatumFeature)
async def add_manual_datum(
    session_id: str,
    manual_datum: ManualDatum,
) -> DatumFeature:
    """수동 데이텀 추가"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 이미지 크기 가져오기 (없으면 파일에서 로드)
    image_width = session.get("image_width")
    image_height = session.get("image_height")

    if not image_width or not image_height:
        from PIL import Image
        file_path = session.get("file_path")
        if file_path:
            try:
                with Image.open(file_path) as img:
                    image_width, image_height = img.size
                    session_service.update_session(session_id, {
                        "image_width": image_width,
                        "image_height": image_height,
                    })
            except Exception:
                image_width = 1000
                image_height = 1000
        else:
            image_width = 1000
            image_height = 1000

    datum = gdt_parser.add_datum(
        session_id=session_id,
        manual_datum=manual_datum,
        image_width=image_width,
        image_height=image_height,
    )

    return datum


@router.delete("/gdt/{session_id}/datum/{datum_id}")
async def delete_datum(session_id: str, datum_id: str) -> Dict[str, Any]:
    """데이텀 삭제"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    deleted = gdt_parser.delete_datum(session_id, datum_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="데이텀을 찾을 수 없습니다")

    return {"deleted": True, "datum_id": datum_id}


@router.get("/gdt/{session_id}/summary", response_model=GDTSummary)
async def get_gdt_summary(session_id: str) -> GDTSummary:
    """GD&T 요약 정보 조회"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    summary = gdt_parser.get_summary(session_id)
    return summary


# ==================== 표제란 OCR API (2025-12-24) ====================

@router.post("/title-block/{session_id}/extract")
async def extract_title_block(session_id: str) -> Dict[str, Any]:
    """
    표제란 OCR 실행
    
    도면의 우하단 표제란 영역을 검출하고 메타데이터를 추출합니다:
    - 도면번호, 리비전, 재질, 작성자, 작성일, 스케일 등
    
    Args:
        session_id: 세션 ID
    
    Returns:
        title_block: TitleBlockData 형태의 표제란 정보
    """
    session_service = get_session_service()
    segmenter = get_region_segmenter()
    
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")
    
    try:
        # 1. 영역 분할 실행 (표제란만)
        config = RegionSegmentationConfig(
            detect_title_block=True,
            detect_bom_table=False,
            detect_legend=False,
            detect_notes=False,
            detect_detail_views=False,
        )
        
        seg_result = await segmenter.segment(
            session_id=session_id,
            image_path=image_path,
            config=config,
        )
        
        # 2. 표제란 영역 찾기
        title_block_region = None
        for region in seg_result.regions:
            if region.region_type == RegionType.TITLE_BLOCK:
                title_block_region = region
                break
        
        if not title_block_region:
            return {
                "success": False,
                "message": "표제란을 찾을 수 없습니다",
                "title_block": None,
            }
        
        # 3. 표제란 영역 처리 (OCR + 파싱)
        process_result = await segmenter.process_region(
            session_id=session_id,
            region_id=title_block_region.id,
            image_path=image_path,
        )
        
        # 4. 결과 추출
        title_block_data = TitleBlockData(
            raw_text=process_result.ocr_text,
            **(process_result.metadata or {})
        )
        
        # 5. 세션에 저장
        session_service.update_session(session_id, {
            "title_block": title_block_data.model_dump(),
            "title_block_region_id": title_block_region.id,
        })
        
        return {
            "success": True,
            "message": "표제란 추출 완료",
            "title_block": title_block_data.model_dump(),
            "region": title_block_region.model_dump(),
        }
        
    except Exception as e:
        logger.error(f"표제란 OCR 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"표제란 OCR 실패: {str(e)}")


@router.get("/title-block/{session_id}")
async def get_title_block(session_id: str) -> Dict[str, Any]:
    """표제란 정보 조회"""
    session_service = get_session_service()
    
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    title_block = session.get("title_block")
    if not title_block:
        return {
            "success": False,
            "message": "표제란 정보가 없습니다. 먼저 추출을 실행하세요.",
            "title_block": None,
        }
    
    return {
        "success": True,
        "title_block": title_block,
    }


@router.put("/title-block/{session_id}")
async def update_title_block(session_id: str, update: Dict[str, Any]) -> Dict[str, Any]:
    """표제란 정보 수동 수정"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    current = session.get("title_block", {})
    updated = {**current, **update}

    session_service.update_session(session_id, {"title_block": updated})

    return {
        "success": True,
        "title_block": updated,
    }


# ============================================================
# 중기 로드맵 기능 (2025-12-24)
# ============================================================

# ------------------------------------------------------------
# 용접 기호 파싱 (Welding Symbol Parsing)
# ------------------------------------------------------------

@router.post("/welding-symbols/{session_id}/parse")
async def parse_welding_symbols(session_id: str) -> Dict[str, Any]:
    """
    용접 기호 파싱

    - 도면에서 용접 기호 검출
    - 용접 타입, 크기, 깊이 등 파싱
    - ISO 2553 표준 기반
    """
    import time
    import uuid
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # TODO: 실제 용접 기호 검출 로직 (YOLO 학습 필요)
    # 현재는 더미 데이터 반환
    welding_symbols = []

    # 검출된 심볼에서 용접 기호 찾기 (데모용)
    detections = session.get("detections", [])
    for det in detections:
        class_name = det.get("class_name", "").lower()
        if "weld" in class_name or "용접" in class_name:
            welding_symbols.append({
                "id": str(uuid.uuid4()),
                "welding_type": "fillet",
                "location": "arrow_side",
                "size": None,
                "length": None,
                "field_weld": False,
                "all_around": False,
                "bbox": det.get("bbox"),
                "confidence": det.get("confidence", 0.0),
                "raw_text": det.get("class_name"),
            })

    processing_time = (time.time() - start_time) * 1000

    result = {
        "session_id": session_id,
        "welding_symbols": welding_symbols,
        "total_count": len(welding_symbols),
        "by_type": {},
        "processing_time_ms": processing_time,
    }

    # 세션에 저장
    session_service.update_session(session_id, {"welding_symbols": result})

    return result


@router.get("/welding-symbols/{session_id}")
async def get_welding_symbols(session_id: str) -> Dict[str, Any]:
    """용접 기호 파싱 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("welding_symbols")
    if not result:
        return {
            "session_id": session_id,
            "welding_symbols": [],
            "total_count": 0,
            "message": "용접 기호 파싱을 먼저 실행하세요.",
        }

    return result


@router.put("/welding-symbols/{session_id}/{symbol_id}")
async def update_welding_symbol(
    session_id: str,
    symbol_id: str,
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """용접 기호 정보 수정"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("welding_symbols", {})
    symbols = result.get("welding_symbols", [])

    for i, sym in enumerate(symbols):
        if sym.get("id") == symbol_id:
            symbols[i] = {**sym, **update}
            break

    result["welding_symbols"] = symbols
    session_service.update_session(session_id, {"welding_symbols": result})

    return {"success": True, "symbol": symbols[i] if i < len(symbols) else None}


# ------------------------------------------------------------
# 표면 거칠기 파싱 (Surface Roughness Parsing)
# ------------------------------------------------------------

@router.post("/surface-roughness/{session_id}/parse")
async def parse_surface_roughness(session_id: str) -> Dict[str, Any]:
    """
    표면 거칠기 기호 파싱

    - Ra, Rz, Rmax 값 추출
    - 가공 방법 및 방향 인식
    - ISO 1302 표준 기반
    """
    import time
    import uuid
    import re
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    roughness_symbols = []

    # 치수 텍스트에서 거칠기 값 찾기
    dimensions = session.get("dimensions", [])
    roughness_pattern = re.compile(r'(Ra|Rz|Rmax)\s*(\d+\.?\d*)', re.IGNORECASE)

    for dim in dimensions:
        text = dim.get("text", "") or dim.get("value", "")
        matches = roughness_pattern.findall(str(text))
        for match in matches:
            roughness_type, value = match
            roughness_symbols.append({
                "id": str(uuid.uuid4()),
                "roughness_type": roughness_type.capitalize(),
                "value": float(value),
                "unit": "μm",
                "machining_method": "unknown",
                "lay_direction": "unknown",
                "bbox": dim.get("bbox"),
                "confidence": 0.8,
                "raw_text": f"{roughness_type} {value}",
            })

    processing_time = (time.time() - start_time) * 1000

    # 타입별 집계
    by_type = {}
    for sym in roughness_symbols:
        rt = sym.get("roughness_type", "unknown")
        by_type[rt] = by_type.get(rt, 0) + 1

    result = {
        "session_id": session_id,
        "roughness_symbols": roughness_symbols,
        "total_count": len(roughness_symbols),
        "by_type": by_type,
        "processing_time_ms": processing_time,
    }

    session_service.update_session(session_id, {"surface_roughness": result})

    return result


@router.get("/surface-roughness/{session_id}")
async def get_surface_roughness(session_id: str) -> Dict[str, Any]:
    """표면 거칠기 파싱 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("surface_roughness")
    if not result:
        return {
            "session_id": session_id,
            "roughness_symbols": [],
            "total_count": 0,
            "message": "표면 거칠기 파싱을 먼저 실행하세요.",
        }

    return result


@router.put("/surface-roughness/{session_id}/{symbol_id}")
async def update_surface_roughness(
    session_id: str,
    symbol_id: str,
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """표면 거칠기 정보 수정"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("surface_roughness", {})
    symbols = result.get("roughness_symbols", [])

    updated_symbol = None
    for i, sym in enumerate(symbols):
        if sym.get("id") == symbol_id:
            symbols[i] = {**sym, **update}
            updated_symbol = symbols[i]
            break

    result["roughness_symbols"] = symbols
    session_service.update_session(session_id, {"surface_roughness": result})

    return {"success": True, "symbol": updated_symbol}


# ------------------------------------------------------------
# 수량 추출 (Quantity Extraction)
# ------------------------------------------------------------

@router.post("/quantity/{session_id}/extract")
async def extract_quantities(session_id: str) -> Dict[str, Any]:
    """
    수량 정보 추출

    - QTY, 수량, EA, SET 등 패턴 인식
    - 벌룬 옆, 테이블, 노트에서 추출
    """
    import time
    import uuid
    import re
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    quantities = []

    # 수량 패턴 정의
    patterns = [
        (r'QTY[:\s]*(\d+)', 'inline'),
        (r'수량[:\s]*(\d+)', 'inline'),
        (r'(\d+)\s*EA', 'inline'),
        (r'(\d+)\s*SET', 'inline'),
        (r'(\d+)\s*OFF', 'inline'),
        (r"REQ'?D[:\s]*(\d+)", 'inline'),
        (r'×(\d+)', 'balloon'),
        (r'\((\d+)\)', 'balloon'),
    ]

    # 치수에서 수량 찾기
    dimensions = session.get("dimensions", [])
    for dim in dimensions:
        text = str(dim.get("text", "") or dim.get("value", ""))
        for pattern, source in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                qty = int(match) if match.isdigit() else int(match)
                if 1 <= qty <= 1000:  # 합리적인 수량 범위
                    quantities.append({
                        "id": str(uuid.uuid4()),
                        "quantity": qty,
                        "unit": "EA",
                        "source": source,
                        "pattern_matched": pattern,
                        "bbox": dim.get("bbox"),
                        "confidence": 0.85,
                        "raw_text": text,
                    })

    # 검출 결과에서도 찾기
    detections = session.get("detections", [])
    for det in detections:
        class_name = str(det.get("class_name", ""))
        for pattern, source in patterns:
            matches = re.findall(pattern, class_name, re.IGNORECASE)
            for match in matches:
                qty = int(match)
                if 1 <= qty <= 1000:
                    quantities.append({
                        "id": str(uuid.uuid4()),
                        "quantity": qty,
                        "unit": "EA",
                        "source": source,
                        "pattern_matched": pattern,
                        "bbox": det.get("bbox"),
                        "confidence": det.get("confidence", 0.5),
                        "raw_text": class_name,
                    })

    processing_time = (time.time() - start_time) * 1000

    # 출처별 집계
    by_source = {}
    total_quantity = 0
    for q in quantities:
        src = q.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
        total_quantity += q.get("quantity", 0)

    result = {
        "session_id": session_id,
        "quantities": quantities,
        "total_items": len(quantities),
        "total_quantity": total_quantity,
        "by_source": by_source,
        "processing_time_ms": processing_time,
    }

    session_service.update_session(session_id, {"quantities": result})

    return result


@router.get("/quantity/{session_id}")
async def get_quantities(session_id: str) -> Dict[str, Any]:
    """수량 추출 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("quantities")
    if not result:
        return {
            "session_id": session_id,
            "quantities": [],
            "total_items": 0,
            "message": "수량 추출을 먼저 실행하세요.",
        }

    return result


@router.put("/quantity/{session_id}/{quantity_id}")
async def update_quantity(
    session_id: str,
    quantity_id: str,
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """수량 정보 수정"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("quantities", {})
    quantities = result.get("quantities", [])

    updated_item = None
    for i, q in enumerate(quantities):
        if q.get("id") == quantity_id:
            quantities[i] = {**q, **update}
            updated_item = quantities[i]
            break

    result["quantities"] = quantities
    session_service.update_session(session_id, {"quantities": result})

    return {"success": True, "quantity": updated_item}


# ------------------------------------------------------------
# 벌룬 번호 매칭 (Balloon Matching)
# ------------------------------------------------------------

@router.post("/balloon/{session_id}/match")
async def match_balloons(session_id: str) -> Dict[str, Any]:
    """
    벌룬 번호 매칭

    - 벌룬 검출 및 번호 OCR
    - 지시선 추적하여 심볼 연결
    - BOM 테이블과 매칭
    """
    import time
    import uuid
    import re
    import math
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    balloons = []

    # 검출 결과에서 벌룬 찾기
    detections = session.get("detections", [])
    balloon_detections = []
    other_detections = []

    for det in detections:
        class_name = str(det.get("class_name", "")).lower()
        if "balloon" in class_name or "번호" in class_name or "item" in class_name:
            balloon_detections.append(det)
        else:
            other_detections.append(det)

    # 벌룬 번호 추출 및 심볼 매칭
    for det in balloon_detections:
        bbox = det.get("bbox", [0, 0, 0, 0])
        center_x = (bbox[0] + bbox[2]) / 2 if len(bbox) >= 4 else 0
        center_y = (bbox[1] + bbox[3]) / 2 if len(bbox) >= 4 else 0

        # 벌룬 번호 추출 (클래스명에서 숫자 추출)
        class_name = det.get("class_name", "")
        numbers = re.findall(r'\d+', class_name)
        balloon_number = numbers[0] if numbers else "?"

        # 가장 가까운 심볼 찾기
        matched_symbol_id = None
        matched_symbol_class = None
        min_distance = float('inf')

        for other in other_detections:
            other_bbox = other.get("bbox", [0, 0, 0, 0])
            if len(other_bbox) >= 4:
                other_center_x = (other_bbox[0] + other_bbox[2]) / 2
                other_center_y = (other_bbox[1] + other_bbox[3]) / 2
                distance = math.sqrt((center_x - other_center_x)**2 + (center_y - other_center_y)**2)
                if distance < min_distance and distance < 500:  # 500px 이내
                    min_distance = distance
                    matched_symbol_id = other.get("id")
                    matched_symbol_class = other.get("class_name")

        balloons.append({
            "id": str(uuid.uuid4()),
            "number": balloon_number,
            "numeric_value": int(balloon_number) if balloon_number.isdigit() else None,
            "shape": "circle",
            "matched_symbol_id": matched_symbol_id,
            "matched_symbol_class": matched_symbol_class,
            "leader_line_endpoint": None,
            "bom_item": None,
            "center": [center_x, center_y],
            "bbox": bbox,
            "confidence": det.get("confidence", 0.0),
        })

    processing_time = (time.time() - start_time) * 1000

    matched_count = sum(1 for b in balloons if b.get("matched_symbol_id"))

    result = {
        "session_id": session_id,
        "balloons": balloons,
        "total_balloons": len(balloons),
        "matched_count": matched_count,
        "unmatched_count": len(balloons) - matched_count,
        "match_rate": (matched_count / len(balloons) * 100) if balloons else 0,
        "processing_time_ms": processing_time,
    }

    session_service.update_session(session_id, {"balloon_matching": result})

    return result


@router.get("/balloon/{session_id}")
async def get_balloons(session_id: str) -> Dict[str, Any]:
    """벌룬 매칭 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("balloon_matching")
    if not result:
        return {
            "session_id": session_id,
            "balloons": [],
            "total_balloons": 0,
            "message": "벌룬 매칭을 먼저 실행하세요.",
        }

    return result


@router.put("/balloon/{session_id}/{balloon_id}")
async def update_balloon(
    session_id: str,
    balloon_id: str,
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """벌룬 매칭 정보 수정"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("balloon_matching", {})
    balloons = result.get("balloons", [])

    updated_balloon = None
    for i, b in enumerate(balloons):
        if b.get("id") == balloon_id:
            balloons[i] = {**b, **update}
            updated_balloon = balloons[i]
            break

    result["balloons"] = balloons
    session_service.update_session(session_id, {"balloon_matching": result})

    return {"success": True, "balloon": updated_balloon}


@router.post("/balloon/{session_id}/{balloon_id}/link")
async def link_balloon_to_symbol(
    session_id: str,
    balloon_id: str,
    symbol_id: str
) -> Dict[str, Any]:
    """벌룬을 심볼에 수동 연결"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("balloon_matching", {})
    balloons = result.get("balloons", [])

    # 심볼 정보 가져오기
    detections = session.get("detections", [])
    symbol_class = None
    for det in detections:
        if det.get("id") == symbol_id:
            symbol_class = det.get("class_name")
            break

    updated_balloon = None
    for i, b in enumerate(balloons):
        if b.get("id") == balloon_id:
            balloons[i]["matched_symbol_id"] = symbol_id
            balloons[i]["matched_symbol_class"] = symbol_class
            updated_balloon = balloons[i]
            break

    # 매칭 통계 업데이트
    matched_count = sum(1 for b in balloons if b.get("matched_symbol_id"))
    result["balloons"] = balloons
    result["matched_count"] = matched_count
    result["unmatched_count"] = len(balloons) - matched_count
    result["match_rate"] = (matched_count / len(balloons) * 100) if balloons else 0

    session_service.update_session(session_id, {"balloon_matching": result})

    return {"success": True, "balloon": updated_balloon}


# ============================================================
# 장기 로드맵 기능 (Long-term Roadmap Features)
# ============================================================

# ============================================================
# 도면 영역 세분화 (Drawing Region Segmentation)
# ============================================================

@router.post("/drawing-regions/{session_id}/segment")
async def segment_drawing_regions(session_id: str) -> Dict[str, Any]:
    """도면 영역 세분화 실행

    정면도, 측면도, 단면도, 상세도, 표제란 등을 자동 구분합니다.
    SAM/U-Net 기반 세그멘테이션 모델이 필요합니다 (현재: 더미 구현).
    """
    import time
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
    import time
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
    import time
    import uuid
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
    import time
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
