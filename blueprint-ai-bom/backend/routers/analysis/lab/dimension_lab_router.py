"""Dimension Lab Router — OD/ID/W 분류 실험 API

OCR 엔진 비교, 분류 방법론 비교, Ground Truth, 전체 비교 매트릭스:
- POST /dimensions/compare         — 7엔진 OCR 비교
- POST /dimensions/compare-methods — 10방법 분류 비교
- POST /dimensions/{session_id}/ground-truth — GT 저장
- GET  /dimensions/{session_id}/ground-truth — GT 조회
- POST /dimensions/full-compare    — 70셀 매트릭스 (엔진×방법)
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging

from schemas.dimension import (
    Dimension,
    DimensionCompareRequest,
    DimensionCompareResponse,
    EngineResult,
    MethodCompareResponse,
    MethodResult,
    MethodDimension,
    GroundTruthDimension,
    GroundTruthRequest,
    GroundTruthResponse,
    FullCompareRequest,
    FullCompareResponse,
    CellResult,
    ClassifiedDim,
    MaterialRole,
    RawDimension,
    GeometryDebugInfo,
    CircleInfo,
    DimLineInfo,
    RoiInfo,
)

logger = logging.getLogger(__name__)
# @AX:ANCHOR — Lab 라우터는 dimension_router와 동일한 prefix 공유
router = APIRouter(prefix="/analysis", tags=["Dimension Lab"])


def _get_services():
    """core_router에서 서비스 가져오기"""
    from routers.analysis.core_router import (
        get_session_service as _sess,
        get_dimension_service as _dim,
    )
    return _sess(), _dim()


def _load_session_image(session_service, session_id: str):
    """세션에서 이미지 로드 (공통 헬퍼)"""
    import cv2

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("image_path") or session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="세션에 이미지가 없습니다")

    image = cv2.imread(image_path)
    if image is None:
        raise HTTPException(status_code=400, detail="이미지를 로드할 수 없습니다")

    h, w = image.shape[:2]
    return session, image_path, w, h


def _extract_best(dims, role_val):
    """역할에 해당하는 최고 신뢰도 치수 추출"""
    matches = [d for d in dims if d.material_role and d.material_role.value == role_val]
    if not matches:
        return None, 0.0
    best = max(matches, key=lambda d: d.confidence)
    return best.value, best.confidence


def _extract_best_value(dims, role_val):
    """역할에 해당하는 최고 신뢰도 값만 추출 (full-compare용)"""
    val, _ = _extract_best(dims, role_val)
    return val


def _to_method_dims(dims):
    """분류 결과를 MethodDimension 리스트로 변환"""
    return [
        MethodDimension(
            value=d.value,
            confidence=d.confidence,
            role=d.material_role.value if d.material_role else None,
            bbox={"x1": d.bbox.x1, "y1": d.bbox.y1, "x2": d.bbox.x2, "y2": d.bbox.y2},
        )
        for d in dims
        if d.material_role is not None
    ]


def _to_classified_dims(dims):
    """분류 결과를 ClassifiedDim 리스트로 변환 — 모든 치수 포함 (추론 과정 추적용)"""
    return [
        ClassifiedDim(
            value=d.value,
            role=d.material_role.value if d.material_role and hasattr(d.material_role, 'value') else (str(d.material_role) if d.material_role else None),
            confidence=d.confidence,
            bbox={"x1": d.bbox.x1, "y1": d.bbox.y1, "x2": d.bbox.x2, "y2": d.bbox.y2},
        )
        for d in dims
    ]


def _value_matches(extracted, ground_truth):
    """추출값이 정답과 일치하는지 (숫자 비교, R→Ø 자동 변환 포함)"""
    if not extracted or not ground_truth:
        return None
    try:
        ext = extracted.strip()
        gt = ground_truth.strip()
        is_radius = ext.upper().startswith("R") and not ext.upper().startswith("RA")
        e_raw = ext.lstrip("RrØø").strip()
        g_raw = gt.lstrip("RrØø").strip()
        e = float(e_raw)
        g = float(g_raw)
        # 절대 오차 ±0.5 또는 상대 오차 ±5% 이내 허용
        tol = max(0.5, g * 0.05)
        if abs(e - g) < tol:
            return True
        if is_radius and abs(e * 2 - g) < tol:
            return True
        return False
    except (ValueError, AttributeError):
        return extracted.strip() == ground_truth.strip()


# ==================== OCR 엔진 비교 ====================

@router.post("/dimensions/compare", response_model=DimensionCompareResponse)
async def compare_dimensions(request: DimensionCompareRequest) -> DimensionCompareResponse:
    """OCR 엔진별 치수 추출 결과 비교 (병렬 실행, 머지 없음)"""
    import asyncio
    import time

    session_service, dimension_service = _get_services()
    session, image_path, image_width, image_height = _load_session_image(
        session_service, request.session_id
    )

    async def run_engine(engine: str) -> EngineResult:
        start = time.time()
        try:
            result = await asyncio.to_thread(
                dimension_service.extract_dimensions,
                image_path,
                request.confidence_threshold,
                [engine],
            )
            dims = result.get("dimensions", [])
            elapsed = (time.time() - start) * 1000
            return EngineResult(
                engine=engine,
                dimensions=dims,
                count=len(dims),
                processing_time_ms=round(elapsed, 1),
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.warning(f"엔진 {engine} 비교 실패: {e}")
            return EngineResult(
                engine=engine,
                count=0,
                processing_time_ms=round(elapsed, 1),
                error=str(e),
            )

    tasks = [run_engine(eng) for eng in request.ocr_engines]
    engine_results = await asyncio.gather(*tasks)

    return DimensionCompareResponse(
        session_id=request.session_id,
        image_width=image_width,
        image_height=image_height,
        engine_results=list(engine_results),
    )


# ==================== 분류 방법론 비교 ====================

@router.post("/dimensions/compare-methods", response_model=MethodCompareResponse)
async def compare_classification_methods(
    session_id: str,
    ocr_engine: str = "paddleocr",
    confidence_threshold: float = 0.5,
) -> MethodCompareResponse:
    """동일 OCR 결과에 분류 방법 10개를 각각 독립 적용하여 비교"""
    import asyncio
    import time

    session_service, dimension_service = _get_services()
    session, image_path, image_width, image_height = _load_session_image(
        session_service, session_id
    )

    # 1. OCR 실행 (한 번만)
    start = time.time()
    ocr_result = await asyncio.to_thread(
        dimension_service.extract_dimensions,
        image_path,
        confidence_threshold,
        [ocr_engine],
    )
    ocr_time = (time.time() - start) * 1000

    raw_dims = [
        Dimension(**d).model_copy(update={"material_role": None})
        for d in ocr_result.get("dimensions", [])
    ]
    total_dims = len(raw_dims)
    session_name = session.get("filename", "")

    # 2. 분류 함수 임포트
    from services.opencv_classifier import (
        classify_by_diameter_symbol,
        classify_by_dimension_type,
        classify_by_catalog,
        infer_inner_diameter,
        classify_width_by_position,
        _parse_numeric_value,
        _is_ocr_noise,
    )
    from services.dimension_parser import classify_material_role, postprocess_dimensions
    from services.session_name_parser import parse_session_name_dimensions, validate_with_session_ref

    ref = parse_session_name_dimensions(session_name)

    def _fresh():
        return [d.model_copy(update={"material_role": None}) for d in raw_dims]

    methods = []

    # A. Ø 기호 + 크기 규칙
    dims_a = classify_by_diameter_symbol(_fresh())
    od_a, od_ac = _extract_best(dims_a, "outer_diameter")
    id_a, id_ac = _extract_best(dims_a, "inner_diameter")
    methods.append(MethodResult(
        method_id="diameter_symbol", method_name="Ø 기호 + 크기 규칙",
        description="Ø 접두사 치수 중 최대값 → OD, 차대값 → ID. ≤30은 볼트홀로 제외.",
        od=od_a, id_val=id_a, od_confidence=od_ac, id_confidence=id_ac,
        classified_dims=_to_method_dims(dims_a),
    ))

    # B. dimension_type 기반
    dims_b = classify_by_dimension_type(_fresh())
    od_b, od_bc = _extract_best(dims_b, "outer_diameter")
    id_b, id_bc = _extract_best(dims_b, "inner_diameter")
    methods.append(MethodResult(
        method_id="dimension_type", method_name="dimension_type 기반",
        description="OCR 파서가 판단한 diameter 타입 중 최대 → OD, OD의 20~80% 범위 최소 → ID.",
        od=od_b, id_val=id_b, od_confidence=od_bc, id_confidence=id_bc,
        classified_dims=_to_method_dims(dims_b),
    ))

    # C. 카탈로그 매칭
    dims_c = classify_by_diameter_symbol(_fresh())
    dims_c = classify_by_catalog(dims_c)
    od_c, od_cc = _extract_best(dims_c, "outer_diameter")
    id_c, id_cc = _extract_best(dims_c, "inner_diameter")
    methods.append(MethodResult(
        method_id="catalog", method_name="베어링 카탈로그 매칭",
        description="ISO 355/JIS B 1512 표준 베어링 치수 테이블과 OD 대조 → 표준 ID 추정.",
        od=od_c, id_val=id_c, od_confidence=od_cc, id_confidence=id_cc,
        classified_dims=_to_method_dims(dims_c),
    ))

    # D. 복합 시그널 ID 추정
    dims_d = classify_by_diameter_symbol(_fresh())
    dims_d = infer_inner_diameter(dims_d, image_width, image_height)
    od_d, od_dc = _extract_best(dims_d, "outer_diameter")
    id_d, id_dc = _extract_best(dims_d, "inner_diameter")
    methods.append(MethodResult(
        method_id="composite_signal", method_name="복합 시그널 ID 추정",
        description="OD 대비 비율(0.3~0.9), 값 반복 빈도, 공차 보유, 도면 중앙 위치 등 7개 시그널 합산.",
        od=od_d, id_val=id_d, od_confidence=od_dc, id_confidence=id_dc,
        classified_dims=_to_method_dims(dims_d),
    ))

    # E. 위치 기반 W 분류
    dims_e = classify_by_diameter_symbol(_fresh())
    dims_e = infer_inner_diameter(dims_e, image_width, image_height)
    dims_e = classify_width_by_position(dims_e, image_width, image_height)
    od_e, od_ec = _extract_best(dims_e, "outer_diameter")
    id_e, id_ec = _extract_best(dims_e, "inner_diameter")
    w_e, w_ec = _extract_best(dims_e, "length")
    methods.append(MethodResult(
        method_id="position_width", method_name="위치 기반 W 분류",
        description="도면 좌측/상단의 큰 가로 치수 → 폭(W). OD/ID 확정 후 남은 큰 값에서 최대값 선택.",
        od=od_e, id_val=id_e, width=w_e,
        od_confidence=od_ec, id_confidence=id_ec, width_confidence=w_ec,
        classified_dims=_to_method_dims(dims_e),
    ))

    # F. 세션명 기준값 검증
    dims_f = classify_by_diameter_symbol(_fresh())
    dims_f = infer_inner_diameter(dims_f, image_width, image_height)
    dims_f = classify_width_by_position(dims_f, image_width, image_height)
    if ref["pattern"]:
        dims_f = validate_with_session_ref(dims_f, ref, _parse_numeric_value, _is_ocr_noise)
    od_f, od_fc = _extract_best(dims_f, "outer_diameter")
    id_f, id_fc = _extract_best(dims_f, "inner_diameter")
    w_f, w_fc = _extract_best(dims_f, "length")
    ref_desc = (
        f"세션명 '{session_name[:40]}' → OD={ref.get('od','?')}, ID={ref.get('id','?')}, W={ref.get('w','?')}"
        if ref["pattern"] else "세션명에서 기준값을 파싱할 수 없음"
    )
    methods.append(MethodResult(
        method_id="session_ref", method_name="세션명 기준값 검증",
        description=ref_desc,
        od=od_f, id_val=id_f, width=w_f,
        od_confidence=od_fc, id_confidence=id_fc, width_confidence=w_fc,
        classified_dims=_to_method_dims(dims_f),
    ))

    # G. 공차/끼워맞춤 기반
    dims_g = _fresh()
    tol_od, tol_id = None, None
    tol_od_c, tol_id_c = 0.0, 0.0
    tol_with_fit = [(i, d) for i, d in enumerate(dims_g) if d.tolerance and d.tolerance.strip()]
    if tol_with_fit:
        tol_vals = []
        for i, d in tol_with_fit:
            v = _parse_numeric_value(d.value)
            if v and v > 5:
                tol_vals.append((i, v, d))
        tol_vals.sort(key=lambda x: x[1], reverse=True)
        if len(tol_vals) >= 1:
            dims_g[tol_vals[0][0]] = tol_vals[0][2].model_copy(update={"material_role": MaterialRole.OUTER_DIAMETER})
            tol_od, tol_od_c = tol_vals[0][2].value, tol_vals[0][2].confidence
        if len(tol_vals) >= 2:
            dims_g[tol_vals[1][0]] = tol_vals[1][2].model_copy(update={"material_role": MaterialRole.INNER_DIAMETER})
            tol_id, tol_id_c = tol_vals[1][2].value, tol_vals[1][2].confidence
    methods.append(MethodResult(
        method_id="tolerance_fit", method_name="공차/끼워맞춤 기반",
        description=f"공차(H7, ±0.05 등)가 있는 치수 = 기능치수. 공차 보유 치수 {len(tol_with_fit)}개 중 최대 → OD, 차대 → ID.",
        od=tol_od, id_val=tol_id, od_confidence=tol_od_c, id_confidence=tol_id_c,
        classified_dims=_to_method_dims(dims_g),
    ))

    # H. 값 크기 순위 (단순 통계)
    dims_h = _fresh()
    all_vals = []
    for i, d in enumerate(dims_h):
        v = _parse_numeric_value(d.value)
        if v and v > 5 and d.dimension_type not in ("thread", "surface_finish", "angle", "chamfer"):
            all_vals.append((i, v, d))
    all_vals.sort(key=lambda x: x[1], reverse=True)
    stat_od, stat_id, stat_w = None, None, None
    stat_od_c, stat_id_c, stat_w_c = 0.0, 0.0, 0.0
    if len(all_vals) >= 1:
        dims_h[all_vals[0][0]] = all_vals[0][2].model_copy(update={"material_role": MaterialRole.OUTER_DIAMETER})
        stat_od, stat_od_c = all_vals[0][2].value, all_vals[0][2].confidence
    if len(all_vals) >= 2:
        dims_h[all_vals[1][0]] = all_vals[1][2].model_copy(update={"material_role": MaterialRole.INNER_DIAMETER})
        stat_id, stat_id_c = all_vals[1][2].value, all_vals[1][2].confidence
    if len(all_vals) >= 3:
        dims_h[all_vals[2][0]] = all_vals[2][2].model_copy(update={"material_role": MaterialRole.LENGTH})
        stat_w, stat_w_c = all_vals[2][2].value, all_vals[2][2].confidence
    methods.append(MethodResult(
        method_id="value_ranking", method_name="값 크기 순위 (단순 통계)",
        description=f"전체 {len(all_vals)}개 수치 치수를 크기 내림차순 정렬. 1위 → OD, 2위 → ID, 3위 → W.",
        od=stat_od, id_val=stat_id, width=stat_w,
        od_confidence=stat_od_c, id_confidence=stat_id_c, width_confidence=stat_w_c,
        classified_dims=_to_method_dims(dims_h),
    ))

    # I. 휴리스틱 fallback
    dims_i = _fresh()
    sorted_vals = sorted([v for d in dims_i if (v := _parse_numeric_value(d.value)) is not None])
    for i, d in enumerate(dims_i):
        role = classify_material_role(d, image_width, image_height, sorted_vals)
        dims_i[i] = d.model_copy(update={"material_role": role})
    od_i, od_ic = _extract_best(dims_i, "outer_diameter")
    id_i, id_ic = _extract_best(dims_i, "inner_diameter")
    w_i, w_ic = _extract_best(dims_i, "length")
    methods.append(MethodResult(
        method_id="heuristic", method_name="휴리스틱 규칙 (fallback)",
        description="타입→접두사→위치→크기 순서 규칙. Ø>80=OD, 30~80=ID, 상단 가로=W, 상위30%=OD.",
        od=od_i, id_val=id_i, width=w_i,
        od_confidence=od_ic, id_confidence=id_ic, width_confidence=w_ic,
        classified_dims=_to_method_dims(dims_i),
    ))

    # J. 전체 파이프라인 (프로덕션)
    dims_j_raw = [Dimension(**{**d, "material_role": None}) for d in ocr_result.get("dimensions", [])]
    dims_j = postprocess_dimensions(dims_j_raw, image_width, image_height, image_path=image_path)
    od_j, od_jc = _extract_best(dims_j, "outer_diameter")
    id_j, id_jc = _extract_best(dims_j, "inner_diameter")
    w_j, w_jc = _extract_best(dims_j, "length")
    methods.append(MethodResult(
        method_id="full_pipeline", method_name="전체 파이프라인 (프로덕션)",
        description="OpenCV OD/ID/W 분류 → 휴리스틱 fallback → OCR 보정 순차 적용.",
        od=od_j, id_val=id_j, width=w_j,
        od_confidence=od_jc, id_confidence=id_jc, width_confidence=w_jc,
        classified_dims=_to_method_dims(dims_j),
    ))

    # raw_dimensions (오버레이용)
    raw_dim_list = [
        RawDimension(
            id=d.id, value=d.value, confidence=d.confidence,
            dimension_type=d.dimension_type.value if hasattr(d.dimension_type, 'value') else str(d.dimension_type),
            bbox={"x1": d.bbox.x1, "y1": d.bbox.y1, "x2": d.bbox.x2, "y2": d.bbox.y2},
        )
        for d in raw_dims
    ]

    return MethodCompareResponse(
        session_id=session_id,
        image_width=image_width,
        image_height=image_height,
        ocr_engine=ocr_engine,
        ocr_time_ms=round(ocr_time, 1),
        total_dims=total_dims,
        raw_dimensions=raw_dim_list,
        method_results=methods,
    )


# ==================== Ground Truth ====================

@router.post("/dimensions/{session_id}/ground-truth", response_model=GroundTruthResponse)
async def save_ground_truth(session_id: str, request: GroundTruthRequest) -> GroundTruthResponse:
    """세션에 수동 Ground Truth 치수 저장"""
    session_service, _ = _get_services()
    session, image_path, w, h = _load_session_image(session_service, session_id)

    gt_data = [d.model_dump() for d in request.dimensions]
    session_service.update_session(session_id, {"ground_truth_dimensions": gt_data})

    return GroundTruthResponse(session_id=session_id, dimensions=request.dimensions, image_width=w, image_height=h)


@router.get("/dimensions/{session_id}/ground-truth", response_model=GroundTruthResponse)
async def get_ground_truth(session_id: str) -> GroundTruthResponse:
    """세션의 Ground Truth 치수 조회"""
    session_service, _ = _get_services()
    session, image_path, w, h = _load_session_image(session_service, session_id)

    gt_data = session.get("ground_truth_dimensions", [])
    dims = [GroundTruthDimension(**d) for d in gt_data]

    return GroundTruthResponse(session_id=session_id, dimensions=dims, image_width=w, image_height=h)


# ==================== 전체 비교 (엔진×방법 매트릭스) ====================

@router.post("/dimensions/full-compare", response_model=FullCompareResponse)
async def full_compare(request: FullCompareRequest) -> FullCompareResponse:
    """7 OCR 엔진 × 10 분류 방법 = 70 조합 전체 비교"""
    import asyncio
    import time

    session_service, dimension_service = _get_services()
    session, image_path, image_width, image_height = _load_session_image(
        session_service, request.session_id
    )

    # Ground Truth 로드
    gt_data = session.get("ground_truth_dimensions", [])
    gt_dims = [GroundTruthDimension(**d) for d in gt_data]
    gt_od = next((g.value for g in gt_dims if g.role == "od"), None)
    gt_id = next((g.value for g in gt_dims if g.role == "id"), None)
    gt_w = next((g.value for g in gt_dims if g.role == "w"), None)

    # 1. OCR 엔진 순차 실행 (병렬 시 CPU/메모리 폭주 방지)
    engine_times: dict = {}
    engine_raw: dict = {}

    for engine in request.ocr_engines:
        start = time.time()
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    dimension_service.extract_dimensions,
                    image_path,
                    request.confidence_threshold,
                    [engine],
                ),
                timeout=300,  # 엔진별 5분 타임아웃
            )
            el = round((time.time() - start) * 1000, 1)
            engine_times[engine] = el
            engine_raw[engine] = result.get("dimensions", [])
        except Exception as e:
            el = round((time.time() - start) * 1000, 1)
            engine_times[engine] = el
            engine_raw[engine] = []
            logger.warning(f"엔진 {engine} 실패: {e}")

    # 1.5. 기하학 보강: 원 검출 + 크롭 OCR로 보충 치수 확보 + 노이즈 필터
    #      선택된 첫 번째 엔진 사용 (하드코딩 paddleocr 제거)
    from services.geometry_guided_extractor import (
        get_geometry_supplementary_dims, filter_ocr_noise,
    )
    _geo_ocr_engine = request.ocr_engines[0] if request.ocr_engines else "edocr2"
    try:
        supp_dims, circle_r = await asyncio.wait_for(
            asyncio.to_thread(
                get_geometry_supplementary_dims, image_path, _geo_ocr_engine,
                request.confidence_threshold,
            ),
            timeout=300,  # 보강 OCR 5분 타임아웃
        )
    except Exception as e:
        logger.warning(f"기하학 보강 실패 ({_geo_ocr_engine}): {e}")
        supp_dims, circle_r = [], None

    # 보충 치수 먼저 노이즈 필터 적용 → 정제된 결과로 dimension_type 태깅
    if supp_dims and circle_r:
        supp_dims = filter_ocr_noise(supp_dims, circle_r)

    # 정제된 보충 치수에 dimension_type 태깅 (A/B/D/G/I 방법 개선)
    _supp_type_map = {}
    if supp_dims and circle_r:
        import re as _re
        _valued = []
        for _sd in supp_dims:
            _sv = _sd.get("value", "") if isinstance(_sd, dict) else ""
            _cl = _re.sub(r'^[ØøΦ⌀∅Rr]\s*', '', _sv.strip())
            _cl = _re.sub(r'[()]', '', _cl)
            _mn = _re.match(r'(\d+\.?\d*)', _cl)
            if _mn:
                _valued.append((float(_mn.group(1)), _sd))
        _valued.sort(key=lambda x: x[0], reverse=True)
        # Top 2 → diameter, 3rd → length (OD, ID는 직경, W는 길이)
        for _idx, (_num, _sd) in enumerate(_valued[:3]):
            if isinstance(_sd, dict):
                if _idx < 2:
                    _sd["dimension_type"] = "diameter"
                else:
                    _sd["dimension_type"] = "length"
        # 값→dimension_type 매핑 (병합 시 기존 치수에도 전파)
        for _sd in supp_dims:
            _sv = _sd.get("value", "").strip() if isinstance(_sd, dict) else ""
            _st = _sd.get("dimension_type") if isinstance(_sd, dict) else None
            if _sv and _st:
                _supp_type_map[_sv] = _st
    logger.info(f"supp_type_map: {list(_supp_type_map.keys())}")

    for engine in request.ocr_engines:
        raw = engine_raw.get(engine, [])
        # 보충 치수 병합 + 기존 치수의 dimension_type 업그레이드
        existing_vals = set()
        for d in raw:
            v = d.get("value", "").strip() if isinstance(d, dict) else (d.value.strip() if hasattr(d, "value") else "")
            existing_vals.add(v)
            # 기존 치수에 보충 치수의 dimension_type 전파
            if v in _supp_type_map and isinstance(d, dict):
                cur_type = d.get("dimension_type", "unknown")
                if cur_type in ("unknown", "length", None):
                    d["dimension_type"] = _supp_type_map[v]
        for sd in supp_dims:
            sv = sd.get("value", "").strip() if isinstance(sd, dict) else (sd.value.strip() if hasattr(sd, "value") else "")
            if sv not in existing_vals:
                raw.append(sd)
                existing_vals.add(sv)
        # 공통 노이즈 필터 적용
        engine_raw[engine] = filter_ocr_noise(raw, circle_r)

    # 2. 각 엔진 결과에 10개 방법 적용
    from services.opencv_classifier import (
        classify_by_diameter_symbol,
        classify_by_dimension_type,
        classify_by_catalog,
        infer_inner_diameter,
        classify_width_by_position,
        _parse_numeric_value,
        _is_ocr_noise,
    )
    from services.dimension_parser import classify_material_role, postprocess_dimensions
    from services.session_name_parser import parse_session_name_dimensions, validate_with_session_ref

    session_name = session.get("filename", "")
    ref = parse_session_name_dimensions(session_name)

    def apply_method(method_id: str, raw_dims_list):
        """특정 방법으로 분류하고 OD/ID/W 추출

        Returns: (od, id_val, w, classified_dims, geometry_debug)
        """
        dims = [Dimension(**d).model_copy(update={"material_role": None}) for d in raw_dims_list]
        if not dims:
            return None, None, None, [], None

        geo_debug = None

        if method_id == "diameter_symbol":
            dims = classify_by_diameter_symbol(dims)
        elif method_id == "dimension_type":
            dims = classify_by_dimension_type(dims)
        elif method_id == "catalog":
            dims = classify_by_diameter_symbol(dims)
            dims = classify_by_catalog(dims)
        elif method_id == "composite_signal":
            dims = classify_by_diameter_symbol(dims)
            dims = infer_inner_diameter(dims, image_width, image_height)
        elif method_id == "position_width":
            dims = classify_by_diameter_symbol(dims)
            dims = infer_inner_diameter(dims, image_width, image_height)
            dims = classify_width_by_position(dims, image_width, image_height)
        elif method_id == "session_ref":
            dims = classify_by_diameter_symbol(dims)
            dims = infer_inner_diameter(dims, image_width, image_height)
            dims = classify_width_by_position(dims, image_width, image_height)
            if ref["pattern"]:
                dims = validate_with_session_ref(dims, ref, _parse_numeric_value, _is_ocr_noise)
        elif method_id == "tolerance_fit":
            tol_with_fit = [(i, d) for i, d in enumerate(dims) if d.tolerance and d.tolerance.strip()]
            tol_vals = []
            for i, d in tol_with_fit:
                v = _parse_numeric_value(d.value)
                if v and v > 5:
                    tol_vals.append((i, v, d))
            tol_vals.sort(key=lambda x: x[1], reverse=True)
            if len(tol_vals) >= 1:
                dims[tol_vals[0][0]] = tol_vals[0][2].model_copy(update={"material_role": MaterialRole.OUTER_DIAMETER})
            if len(tol_vals) >= 2:
                dims[tol_vals[1][0]] = tol_vals[1][2].model_copy(update={"material_role": MaterialRole.INNER_DIAMETER})
        elif method_id == "value_ranking":
            all_vals = []
            for i, d in enumerate(dims):
                v = _parse_numeric_value(d.value)
                if v and v > 5 and d.dimension_type not in ("thread", "surface_finish", "angle", "chamfer"):
                    all_vals.append((i, v, d))
            all_vals.sort(key=lambda x: x[1], reverse=True)
            if len(all_vals) >= 1:
                dims[all_vals[0][0]] = all_vals[0][2].model_copy(update={"material_role": MaterialRole.OUTER_DIAMETER})
            if len(all_vals) >= 2:
                dims[all_vals[1][0]] = all_vals[1][2].model_copy(update={"material_role": MaterialRole.INNER_DIAMETER})
            if len(all_vals) >= 3:
                dims[all_vals[2][0]] = all_vals[2][2].model_copy(update={"material_role": MaterialRole.LENGTH})
        elif method_id == "heuristic":
            sorted_vals = sorted([v for d in dims if (v := _parse_numeric_value(d.value)) is not None])
            for i, d in enumerate(dims):
                role = classify_material_role(d, image_width, image_height, sorted_vals)
                dims[i] = d.model_copy(update={"material_role": role})
        elif method_id == "full_pipeline":
            dims = [Dimension(**{**d, "material_role": None}) for d in raw_dims_list]
            dims = postprocess_dimensions(dims, image_width, image_height, image_path=image_path)
        elif method_id == "endpoint_topology":
            from services.geometric_methods import endpoint_topology_classify
            dims, geo_debug = endpoint_topology_classify(dims, image_path, image_width, image_height)
        elif method_id == "symbol_search":
            from services.geometric_methods import symbol_search_classify
            dims, geo_debug = symbol_search_classify(dims)
        elif method_id == "center_raycast":
            from services.geometric_methods import center_raycast_classify
            dims, geo_debug = center_raycast_classify(dims, image_path, image_width, image_height)

        od = _extract_best_value(dims, "outer_diameter")
        id_val = _extract_best_value(dims, "inner_diameter")
        w = _extract_best_value(dims, "length")
        return od, id_val, w, _to_classified_dims(dims), geo_debug

    METHOD_IDS = [
        "diameter_symbol", "dimension_type", "catalog", "composite_signal",
        "position_width", "session_ref", "tolerance_fit", "value_ranking",
        "heuristic", "full_pipeline",
        "endpoint_topology", "symbol_search", "center_raycast",
    ]

    # methods 필터 적용 (None이면 전체)
    active_methods = request.methods if request.methods else METHOD_IDS

    matrix: list = []
    for engine in request.ocr_engines:
        raw = engine_raw.get(engine, [])
        for method_id in active_methods:
            if method_id not in METHOD_IDS:
                continue
            try:
                od, id_val, w, c_dims, geo_debug = apply_method(method_id, raw)
            except Exception as e:
                logger.warning(f"{engine}×{method_id} 실패: {e}")
                od, id_val, w, c_dims, geo_debug = None, None, None, [], None

            od_match = _value_matches(od, gt_od)
            id_match = _value_matches(id_val, gt_id)
            w_match = _value_matches(w, gt_w)

            checks = [m for m in [od_match, id_match, w_match] if m is not None]
            score = sum(1 for c in checks if c) / len(checks) if checks else 0.0

            matrix.append(CellResult(
                engine=engine, method_id=method_id,
                od=od, id_val=id_val, width=w,
                od_match=od_match, id_match=id_match, w_match=w_match,
                score=score, classified_dims=c_dims,
                geometry_debug=geo_debug,
            ))

    # K. 기하학 기반 — 항상 extract_by_geometry 전체 파이프라인 실행
    #   (ID/W 최소값 제약, 스케일 일관성 검증 등 포함)
    _run_geometry = (not request.methods) or ("geometry_guided" in request.methods)
    if _run_geometry:
        from services.geometry_guided_extractor import extract_by_geometry
        try:
            geo_start = time.time()
            geo_result = await asyncio.wait_for(
                asyncio.to_thread(
                    extract_by_geometry, image_path, _geo_ocr_engine, request.confidence_threshold
                ),
                timeout=600,  # geometry 10분 타임아웃
            )
            geo_time = round((time.time() - geo_start) * 1000, 1)
            engine_times["geometry"] = geo_time

            geo_od = geo_result.get("od", {})
            geo_id = geo_result.get("id", {})
            geo_w = geo_result.get("w", {})
            od_val = geo_od.get("value") if geo_od else None
            id_val_g = geo_id.get("value") if geo_id else None
            w_val = geo_w.get("value") if geo_w else None

            c_dims_geo = []
            for item, role in [(geo_od, "outer_diameter"), (geo_id, "inner_diameter"), (geo_w, "length")]:
                if item and item.get("bbox"):
                    c_dims_geo.append(ClassifiedDim(
                        value=item["value"], role=role,
                        confidence=item.get("confidence", 0.5), bbox=item["bbox"],
                    ))

            # geometry_debug 추출
            geo_circles = [
                CircleInfo(cx=c["cx"], cy=c["cy"], radius=c["r"], confidence=0.5)
                for c in geo_result.get("circles", [])
            ]
            geo_dim_lines = [
                DimLineInfo(x1=l["x1"], y1=l["y1"], x2=l["x2"], y2=l["y2"])
                for l in geo_result.get("dim_lines", [])
            ]
            geo_rois = [
                RoiInfo(x=r["x1"], y=r["y1"], w=r["x2"]-r["x1"], h=r["y2"]-r["y1"],
                        ocr_text="", symbol=r.get("direction", ""))
                for r in geo_result.get("rois", [])
            ]
            geo_debug_info = GeometryDebugInfo(
                circles=geo_circles, dim_lines=geo_dim_lines, rois=geo_rois,
            )

            # 세션명 힌트로 K geometry 보정
            if ref.get("od") or ref.get("id"):
                ref_od = ref.get("od")
                ref_id = ref.get("id")
                import re as _re

                def _find_closest(ocr_dims, target, tol=0.15):
                    best, best_d = None, float("inf")
                    for d in ocr_dims:
                        v = d.get("value", "") if isinstance(d, dict) else str(d)
                        v = _re.sub(r'^[ØøΦ⌀∅Rr]\s*', '', str(v).strip())
                        v = _re.sub(r'[()]', '', v)
                        m = _re.match(r'(\d+\.?\d*)', v)
                        if m:
                            num = float(m.group(1))
                            dist = abs(num - target)
                            if dist < best_d and dist / max(target, 1) < tol:
                                best_d = dist
                                best = str(num) if num == int(num) else m.group(1)
                    return best

                all_ocr = []
                for eng_dims in engine_raw.values():
                    all_ocr.extend(eng_dims)

                if ref_od and (not od_val or abs(float(_re.sub(r'[^0-9.]', '', str(od_val)) or '0') - ref_od) / max(ref_od, 1) > 0.3):
                    new_od = _find_closest(all_ocr, ref_od)
                    if new_od:
                        logger.info(f"K 외경 세션명 보정: {od_val} → {new_od} (힌트 {ref_od})")
                        od_val = new_od
                    else:
                        od_val = str(int(ref_od))
                        logger.info(f"K 외경 힌트 직접: {ref_od}")

                if ref_id and (not id_val_g or abs(float(_re.sub(r'[^0-9.]', '', str(id_val_g)) or '0') - ref_id) / max(ref_id, 1) > 0.3):
                    new_id = _find_closest(all_ocr, ref_id)
                    if new_id:
                        logger.info(f"K 내경 세션명 보정: {id_val_g} → {new_id} (힌트 {ref_id})")
                        id_val_g = new_id
                    else:
                        id_val_g = str(int(ref_id))
                        logger.info(f"K 내경 힌트 직접: {ref_id}")

            od_m = _value_matches(od_val, gt_od)
            id_m = _value_matches(id_val_g, gt_id)
            w_m = _value_matches(w_val, gt_w)
            checks_g = [m for m in [od_m, id_m, w_m] if m is not None]
            score_g = sum(1 for c in checks_g if c) / len(checks_g) if checks_g else 0.0

            for engine in request.ocr_engines:
                matrix.append(CellResult(
                    engine=engine, method_id="geometry_guided",
                    od=od_val, id_val=id_val_g, width=w_val,
                    od_match=od_m, id_match=id_m, w_match=w_m,
                    score=score_g, classified_dims=c_dims_geo,
                    geometry_debug=geo_debug_info,
                ))
        except Exception as e:
            logger.warning(f"기하학 기반 실패: {e}")
            for engine in request.ocr_engines:
                matrix.append(CellResult(engine=engine, method_id="geometry_guided", score=0.0))

    return FullCompareResponse(
        session_id=request.session_id,
        image_width=image_width, image_height=image_height,
        ground_truth=gt_dims, engine_times=engine_times,
        matrix=matrix, total_engines=len(request.ocr_engines),
        total_methods=len(active_methods) + (1 if _run_geometry else 0),
    )
