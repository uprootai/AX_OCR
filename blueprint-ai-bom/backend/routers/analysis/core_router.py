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
_table_service = None

# 세션별 옵션 캐시 (메모리) - 다른 라우터에서도 접근 필요
_session_options: Dict[str, AnalysisOptions] = {}


def set_core_services(dimension_service, detection_service, session_service, relation_service=None, table_service=None):
    """서비스 인스턴스 설정 (api_server.py에서 호출)"""
    global _dimension_service, _detection_service, _session_service, _relation_service, _table_service
    _dimension_service = dimension_service
    _detection_service = detection_service
    _session_service = session_service
    _relation_service = relation_service
    _table_service = table_service


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


# VLM 도면 분류 결과 → 심볼 검출 모델 자동 매핑
_DRAWING_TYPE_MODEL_MAP = {
    "mechanical_part": "engineering",
    "assembly": "engineering",
    "pid": "pid_symbol",
    "electrical": "panasia",
    "architectural": "engineering",
}


def _resolve_options(session_id: str, session: dict) -> AnalysisOptions:
    """세션의 분석 옵션 결정 (캐시 → features 기반 자동 생성)"""
    cached = _session_options.get(session_id)
    if cached is not None:
        return cached

    options = AnalysisOptions()
    features = session.get("features", [])
    if features:
        feature_to_option = {
            "symbol_detection": "enable_symbol_detection",
            "dimension_ocr": "enable_dimension_ocr",
            "line_detection": "enable_line_detection",
            "text_extraction": "enable_text_extraction",
            "table_extraction": "enable_text_extraction",
        }
        data = options.model_dump()
        # features 리스트가 있으면 모든 enable_* 플래그를 False로 리셋
        for key in data:
            if key.startswith("enable_"):
                data[key] = False
        # 리스트에 있는 기능만 활성화
        for feature in features:
            opt_key = feature_to_option.get(feature)
            if opt_key:
                data[opt_key] = True
        # dimension_ocr 시 line_detection 자동 활성화 (치수선 관계 분석용)
        # 단, features에 line_detection이 명시적으로 없으면 스킵 (BOM 세션 등)
        if data.get("enable_dimension_ocr") and "line_detection" not in features:
            # line_detection 미요청 → 관계 분석만 활성화 (로컬 계산, API 호출 없음)
            data["enable_relation_extraction"] = True
        elif data.get("enable_dimension_ocr") and "line_detection" in features:
            data["enable_line_detection"] = True
            data["enable_relation_extraction"] = True
        options = AnalysisOptions(**data)
        logger.info(f"세션 features에서 옵션 자동 생성: {features}")

    # VLM drawing_type에 따라 심볼 모델 자동 선택 (기본값일 때만)
    drawing_type = session.get("drawing_type", "")
    if drawing_type in _DRAWING_TYPE_MODEL_MAP:
        if options.symbol_model_type == "panasia":
            options.symbol_model_type = _DRAWING_TYPE_MODEL_MAP[drawing_type]
            logger.info(f"도면 유형 '{drawing_type}' → 모델 '{options.symbol_model_type}' 자동 선택")

    _session_options[session_id] = options
    return options


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

    return _resolve_options(session_id, session)


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

    # AnalysisOptions → session features 동기화
    OPTION_TO_FEATURE = {
        "enable_symbol_detection": "symbol_detection",
        "enable_dimension_ocr": "dimension_ocr",
        "enable_line_detection": "line_detection",
        "enable_text_extraction": "title_block_ocr",
        "enable_relation_extraction": "relation_extraction",
    }
    features = [
        feat for opt_key, feat in OPTION_TO_FEATURE.items()
        if getattr(options, opt_key, False)
    ]
    session_service.update_session(session_id, {"features": features})

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

    options = _resolve_options(session_id, session)

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
                confidence_threshold=options.confidence_threshold,
                ocr_engines=options.ocr_engines,
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

    # 4. 텍스트/테이블 추출 (Table Detector API)
    if options.enable_text_extraction and _table_service:
        try:
            table_result = _table_service.extract_tables(
                image_path=image_path,
                enable_cell_reocr=True,   # E1-B: EasyOCR 셀 재인식
                enable_crop_upscale=True, # E1-B-2: 크롭 이미지 ESRGAN 업스케일
                upscale_scale=2,          # 2x 업스케일 (4x는 너무 느림)
            )

            if table_result.get("error"):
                result.errors.append(table_result["error"])
            else:
                tables = table_result.get("tables", [])
                regions = table_result.get("regions", [])
                total_time += table_result.get("processing_time_ms", 0)

                text_entries = []
                for region in regions:
                    text_entries.append({
                        "type": "table_region",
                        "bbox": region.get("bbox"),
                        "confidence": region.get("confidence"),
                        "label": region.get("label", "table"),
                    })
                for table in tables:
                    text_entries.append({
                        "type": "table",
                        "table_id": table.get("id"),
                        "rows": table.get("rows"),
                        "cols": table.get("cols"),
                        "headers": table.get("headers", []),
                        "data": table.get("data", []),
                        "html": table.get("html", ""),
                        "source_region": table.get("source_region", ""),
                    })

                result.texts = text_entries

                # E1-B: 재OCR 통계
                reocr_stats = table_result.get("reocr_stats")
                update_data = {
                    "texts": text_entries,
                    "tables_count": len(tables),
                    "table_regions_count": len(regions),
                    "table_results": tables,
                }
                if reocr_stats:
                    update_data["reocr_stats"] = reocr_stats

                session_service.update_session(session_id, update_data)

                log_msg = f"테이블 추출 완료: {len(regions)}개 영역, {len(tables)}개 테이블"
                if reocr_stats and reocr_stats.get("corrected", 0) > 0:
                    log_msg += f" [재OCR: {reocr_stats['corrected']}개 셀 수정]"
                logger.info(log_msg)

        except Exception as e:
            error_msg = f"테이블 추출 실패: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    # 5. 표제란/NOTES 텍스트 OCR (EasyOCR 직접 호출)
    if options.enable_text_extraction and _table_service:
        try:
            text_result = _table_service.extract_text_regions(
                image_path=image_path,
                ocr_engine="easyocr",
                lang="en",
            )
            text_regions = text_result.get("text_regions", [])
            total_time += text_result.get("processing_time_ms", 0)

            if text_regions:
                session_service.update_session(session_id, {
                    "text_regions": text_regions,
                    "text_regions_count": len(text_regions),
                })

                # text_entries에 텍스트 영역 추가
                for tr in text_regions:
                    result.texts.append({
                        "type": "text_region",
                        "region": tr.get("region"),
                        "full_text": tr.get("full_text", ""),
                        "text_count": tr.get("text_count", 0),
                        "detections": tr.get("detections", []),
                    })

                # texts가 갱신되었으면 세션도 갱신
                session_service.update_session(session_id, {
                    "texts": result.texts,
                })

                logger.info(
                    f"텍스트 영역 OCR 완료: {len(text_regions)}개 영역, "
                    f"총 {sum(r.get('text_count', 0) for r in text_regions)}개 텍스트"
                )

        except Exception as e:
            error_msg = f"텍스트 영역 OCR 실패: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    # 6. 표제란 자동 추출 (title_block_ocr feature 활성화 시)
    features = session.get("features", [])
    if "title_block_ocr" in features:
        try:
            from services.region_segmenter import RegionSegmenter, RegionSegmentationConfig, RegionType
            from schemas.gdt import TitleBlockData

            segmenter = RegionSegmenter()
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

            title_block_region = None
            for region in seg_result.regions:
                if region.region_type == RegionType.TITLE_BLOCK:
                    title_block_region = region
                    break

            if title_block_region:
                process_result = await segmenter.process_region(
                    session_id=session_id,
                    region_id=title_block_region.id,
                    image_path=image_path,
                )

                title_block_data = TitleBlockData(
                    raw_text=process_result.ocr_text,
                    **(process_result.metadata or {})
                )

                session_service.update_session(session_id, {
                    "title_block": title_block_data.model_dump(),
                    "title_block_region_id": title_block_region.id,
                })

                logger.info(f"표제란 자동 추출 완료: {title_block_data.drawing_number or 'N/A'}")

        except Exception as e:
            logger.warning(f"표제란 자동 추출 실패 (계속 진행): {str(e)}")

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

    # 핵심 결과(치수/검출)가 있으면 비핵심 오류(OCR 엔진 미접속 등)는 무시
    has_results = len(result.dimensions) > 0 or len(result.detections) > 0
    if result.errors and not has_results:
        session_service.update_status(session_id, SessionStatus.ERROR)
    else:
        session_service.update_status(session_id, SessionStatus.VERIFIED)

    return result
