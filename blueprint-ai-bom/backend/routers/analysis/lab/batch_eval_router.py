"""Batch Evaluation Router — 다수 도면 일괄 치수 분석 + 후행 평가

GT 없는 도면에서도 결과를 보여주고, 사용자가 맞음/틀림 평가:
- POST /dimensions/batch-eval              — 배치 시작
- GET  /dimensions/batch-eval/{batch_id}/status  — 진행률 + 부분 결과
- GET  /dimensions/batch-eval/{batch_id}/results — 최종 결과
- GET  /dimensions/batch-eval/list         — 배치 목록 (새로고침 복원용)
- PATCH /dimensions/batch-eval/{batch_id}/sessions/{session_id}/eval — 후행 평가
"""

import asyncio
import logging
import random
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Dimension Lab - Batch Eval"])


# ==================== 스키마 ====================

class BatchEvalRequest(BaseModel):
    count: int = Field(10, ge=1, le=100, description="랜덤 선택 세션 수")
    session_ids: Optional[List[str]] = Field(None, description="명시적 세션 ID 목록")


class BatchEvalStartResponse(BaseModel):
    batch_id: str
    total: int
    session_ids: List[str]


class SessionEvalRow(BaseModel):
    session_id: str
    filename: str = ""
    status: str = "pending"  # pending / running / done / error
    # geometry_guided (K) 결과
    geometry_od: Optional[str] = None
    geometry_id: Optional[str] = None
    geometry_w: Optional[str] = None
    # value_ranking (H) 결과
    ranking_od: Optional[str] = None
    ranking_id: Optional[str] = None
    ranking_w: Optional[str] = None
    # endpoint_topology (L) 결과
    endpoint_od: Optional[str] = None
    endpoint_id: Optional[str] = None
    endpoint_w: Optional[str] = None
    # symbol_search (M) 결과
    symbol_od: Optional[str] = None
    symbol_id: Optional[str] = None
    symbol_w: Optional[str] = None
    # center_raycast (N) 결과
    raycast_od: Optional[str] = None
    raycast_id: Optional[str] = None
    raycast_w: Optional[str] = None
    # 세션명 참조 (S)
    ref_od: Optional[str] = None
    ref_id: Optional[str] = None
    ref_w: Optional[str] = None
    # 최종 선택
    od: Optional[str] = None
    id_val: Optional[str] = None
    width: Optional[str] = None
    # 후행 평가
    od_correct: Optional[bool] = None
    id_correct: Optional[bool] = None
    w_correct: Optional[bool] = None
    has_gt: bool = False
    error: Optional[str] = None


class BatchEvalStatus(BaseModel):
    batch_id: str
    status: str = "pending"  # pending / running / completed / error
    total: int = 0
    completed: int = 0
    failed: int = 0
    rows: List[SessionEvalRow] = Field(default_factory=list)


class BatchListItem(BaseModel):
    batch_id: str
    status: str
    total: int
    completed: int
    failed: int


class SessionEvalUpdate(BaseModel):
    od_correct: Optional[bool] = None
    id_correct: Optional[bool] = None
    w_correct: Optional[bool] = None


# ==================== 영속화 + In-memory 상태 ====================

import json
from pathlib import Path

_BATCH_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads" / "batch_evals"
_BATCH_DIR.mkdir(parents=True, exist_ok=True)

_batches: Dict[str, BatchEvalStatus] = {}
_tasks: Dict[str, asyncio.Task] = {}  # 배치별 asyncio.Task (취소용)


def _save_batch(batch: BatchEvalStatus):
    """배치 상태를 디스크에 JSON 저장"""
    path = _BATCH_DIR / f"{batch.batch_id}.json"
    path.write_text(json.dumps(batch.model_dump(), ensure_ascii=False, indent=2))


def _load_all_batches():
    """서버 시작 시 디스크에서 모든 배치 복원"""
    for f in _BATCH_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            b = BatchEvalStatus(**data)
            # 실행 중이었던 배치는 error로 표시 (서버 재시작으로 중단)
            if b.status == "running":
                b.status = "error"
                for r in b.rows:
                    if r.status in ("pending", "running"):
                        r.status = "error"
                        r.error = "서버 재시작으로 중단"
            _batches[b.batch_id] = b
        except Exception:
            pass


_load_all_batches()


def _get_services():
    from routers.analysis.core_router import (
        get_session_service as _sess,
        get_dimension_service as _dim,
    )
    return _sess(), _dim()


# ==================== 헬퍼 ====================

def _sanity_check(k_val: Optional[str], ref_val: Optional[float]) -> bool:
    """K 결과가 세션명 참조 대비 50% 이내인지 확인"""
    if not k_val or not ref_val:
        return True  # 비교 불가 → 통과
    try:
        k_num = float(k_val)
        ratio = abs(k_num - ref_val) / ref_val
        return ratio <= 0.5
    except (ValueError, ZeroDivisionError):
        return True


def _pick_best(
    k_val: Optional[str], h_val: Optional[str], s_val: Optional[str],
    ref_num: Optional[float],
) -> Optional[str]:
    """K → H → S 폴백, K가 세션명 참조 대비 50%+ 벗어나면 S 우선"""
    if k_val and _sanity_check(k_val, ref_num):
        return k_val
    if k_val and s_val and not _sanity_check(k_val, ref_num):
        return s_val  # K 의심 → S 우선
    return k_val or h_val or s_val


def _extract_role_value(dims, role_val: str) -> Optional[str]:
    """material_role 기반 최고 신뢰도 값 추출 (L/M/N 방법용)"""
    matches = [d for d in dims if d.material_role and d.material_role.value == role_val]
    if not matches:
        return None
    best = max(matches, key=lambda d: d.confidence)
    return best.value


# ==================== 배치 실행 로직 ====================

async def _run_batch(batch_id: str):
    """배치 평가 백그라운드 실행"""
    batch = _batches[batch_id]
    batch.status = "running"
    _save_batch(batch)  # 즉시 디스크 저장 (OOM 크래시 대비)
    session_service, dimension_service = _get_services()

    for row in batch.rows:
        # 취소 체크
        if batch.status == "cancelled":
            break
        row.status = "running"
        try:
            session = session_service.get_session(row.session_id)
            if not session:
                row.status = "error"
                row.error = "세션 없음"
                batch.failed += 1
                continue

            image_path = session.get("image_path") or session.get("file_path")
            if not image_path:
                row.status = "error"
                row.error = "이미지 없음"
                batch.failed += 1
                continue

            row.filename = session.get("filename", row.session_id)
            row.has_gt = bool(session.get("ground_truth_dimensions"))

            # S. 세션명 파서 (미리 파싱 — sanity check에 사용)
            ref_od_num, ref_id_num, ref_w_num = None, None, None
            try:
                from services.session_name_parser import parse_session_name_dimensions
                ref = parse_session_name_dimensions(row.filename)
                if ref["od"]:
                    ref_od_num = ref["od"]
                    row.ref_od = str(int(ref["od"]))
                if ref["id"]:
                    ref_id_num = ref["id"]
                    row.ref_id = str(int(ref["id"]))
                if ref["w"]:
                    ref_w_num = ref["w"]
                    row.ref_w = str(int(ref["w"]))
            except Exception:
                pass

            # 경량 OCR: edocr2 API 직접 호출 (YOLO 파이프라인 스킵)
            from services.geometry_guided_extractor import (
                get_geometry_supplementary_dims, filter_ocr_noise,
                extract_by_geometry,
            )
            from services.opencv_classifier import clean_dimension_value as _clean

            try:
                dims_list = await asyncio.wait_for(
                    asyncio.to_thread(
                        dimension_service._call_edocr2, image_path, 0.3,
                    ),
                    timeout=600,
                )
                # Dimension 객체 → dict 변환
                ocr_result = {
                    "dimensions": [
                        {"value": d.value, "confidence": d.confidence,
                         "dimension_type": d.dimension_type, "bbox": d.bbox}
                        for d in dims_list
                    ]
                }
            except asyncio.TimeoutError:
                logger.warning(f"세션 {row.session_id} OCR 타임아웃 (600s)")
                row.status = "error"
                row.error = "OCR 타임아웃 (600s)"
                batch.failed += 1
                _save_batch(batch)
                continue

            # 기하학 분석 — 실패해도 OCR만으로 진행 (graceful skip)
            supp_result = ([], None)
            geo_result = {}
            try:
                supp_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        get_geometry_supplementary_dims, image_path, "paddleocr", 0.3,
                    ),
                    timeout=300,
                )
                geo_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        extract_by_geometry, image_path, "paddleocr", 0.3,
                    ),
                    timeout=300,
                )
            except (asyncio.TimeoutError, RecursionError, Exception) as e:
                logger.warning(f"세션 {row.session_id} 기하학 스킵: {e}")

            # OCR 결과 + 기하학 보강 병합
            raw_dims = ocr_result.get("dimensions", [])
            supp_dims, circle_r = supp_result
            if supp_dims and circle_r:
                supp_dims = filter_ocr_noise(supp_dims, circle_r)
            existing_vals = {
                (d.get("value", "").strip() if isinstance(d, dict) else "")
                for d in raw_dims
            }
            for sd in (supp_dims or []):
                sv = sd.get("value", "").strip() if isinstance(sd, dict) else ""
                if sv and sv not in existing_vals:
                    raw_dims.append(sd)
                    existing_vals.add(sv)
            raw_dims = filter_ocr_noise(raw_dims, circle_r)

            # K. geometry_guided
            try:
                geo_od = geo_result.get("od", {})
                geo_id = geo_result.get("id", {})
                geo_w = geo_result.get("w", {})
                row.geometry_od = _clean(geo_od.get("value", "")) if geo_od else None
                row.geometry_id = _clean(geo_id.get("value", "")) if geo_id else None
                row.geometry_w = _clean(geo_w.get("value", "")) if geo_w else None
            except Exception as e:
                logger.warning(f"K 방법 실패 ({row.session_id}): {e}")

            # H. value_ranking
            try:
                from schemas.dimension import Dimension
                from services.opencv_classifier import _parse_numeric_value

                dims_h = [
                    Dimension(**d).model_copy(update={"material_role": None})
                    for d in raw_dims
                ]
                all_vals = []
                for d in dims_h:
                    cleaned = _clean(d.value)
                    if not cleaned:
                        continue
                    v = _parse_numeric_value(d.value)
                    if v and v > 5 and d.dimension_type not in (
                        "thread", "surface_finish", "angle", "chamfer"
                    ):
                        all_vals.append((v, cleaned))
                all_vals.sort(key=lambda x: x[0], reverse=True)
                if len(all_vals) >= 1:
                    row.ranking_od = all_vals[0][1]
                if len(all_vals) >= 2:
                    row.ranking_id = all_vals[1][1]
                if len(all_vals) >= 3:
                    row.ranking_w = all_vals[2][1]
            except Exception as e:
                logger.warning(f"H 방법 실패 ({row.session_id}): {e}")

            # L/M/N 기하학 방법 (graceful skip)
            try:
                from schemas.dimension import Dimension as DimSchema
                from services.geometric_methods import (
                    endpoint_topology_classify,
                    symbol_search_classify,
                    center_raycast_classify,
                )
                import cv2

                img_for_geo = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                img_h, img_w = (img_for_geo.shape[:2]) if img_for_geo is not None else (0, 0)

                dims_lmn = [DimSchema(**d) for d in raw_dims]

                # L. endpoint_topology
                try:
                    l_dims, _ = endpoint_topology_classify(dims_lmn, image_path, img_w, img_h)
                    l_od = _extract_role_value(l_dims, "outer_diameter")
                    l_id = _extract_role_value(l_dims, "inner_diameter")
                    l_w = _extract_role_value(l_dims, "length")
                    row.endpoint_od = _clean(l_od) if l_od else None
                    row.endpoint_id = _clean(l_id) if l_id else None
                    row.endpoint_w = _clean(l_w) if l_w else None
                except Exception as e:
                    logger.warning(f"L 방법 실패 ({row.session_id}): {e}")

                # M. symbol_search
                try:
                    m_dims, _ = symbol_search_classify(dims_lmn)
                    m_od = _extract_role_value(m_dims, "outer_diameter")
                    m_id = _extract_role_value(m_dims, "inner_diameter")
                    m_w = _extract_role_value(m_dims, "length")
                    row.symbol_od = _clean(m_od) if m_od else None
                    row.symbol_id = _clean(m_id) if m_id else None
                    row.symbol_w = _clean(m_w) if m_w else None
                except Exception as e:
                    logger.warning(f"M 방법 실패 ({row.session_id}): {e}")

                # N. center_raycast
                try:
                    n_dims, _ = center_raycast_classify(dims_lmn, image_path, img_w, img_h)
                    n_od = _extract_role_value(n_dims, "outer_diameter")
                    n_id = _extract_role_value(n_dims, "inner_diameter")
                    n_w = _extract_role_value(n_dims, "length")
                    row.raycast_od = _clean(n_od) if n_od else None
                    row.raycast_id = _clean(n_id) if n_id else None
                    row.raycast_w = _clean(n_w) if n_w else None
                except Exception as e:
                    logger.warning(f"N 방법 실패 ({row.session_id}): {e}")
            except Exception as e:
                logger.warning(f"L/M/N 초기화 실패 ({row.session_id}): {e}")

            # 최종 선택: K → H → S (sanity check 적용)
            row.od = _pick_best(row.geometry_od, row.ranking_od, row.ref_od, ref_od_num)
            row.id_val = _pick_best(row.geometry_id, row.ranking_id, row.ref_id, ref_id_num)
            row.width = _pick_best(row.geometry_w, row.ranking_w, row.ref_w, ref_w_num)

            # GT 있으면 자동 평가
            if row.has_gt:
                from routers.analysis.lab.dimension_lab_router import _value_matches
                gt_data = session.get("ground_truth_dimensions", [])
                gt_od = next((g["value"] for g in gt_data if g["role"] == "od"), None)
                gt_id = next((g["value"] for g in gt_data if g["role"] == "id"), None)
                gt_w = next((g["value"] for g in gt_data if g["role"] == "w"), None)
                row.od_correct = _value_matches(row.od, gt_od)
                row.id_correct = _value_matches(row.id_val, gt_id)
                row.w_correct = _value_matches(row.width, gt_w)

            row.status = "done"
            batch.completed += 1

        except Exception as e:
            logger.error(f"배치 세션 {row.session_id} 실패: {e}")
            row.status = "error"
            row.error = str(e)[:200]
            batch.failed += 1

        _save_batch(batch)
        await asyncio.sleep(0.1)

    if batch.status == "cancelled":
        # 남은 row들 cancelled 처리
        for r in batch.rows:
            if r.status == "pending":
                r.status = "error"
                r.error = "취소됨"
    else:
        batch.status = "completed"
    _save_batch(batch)
    _tasks.pop(batch_id, None)


# ==================== 엔드포인트 ====================

@router.post("/dimensions/batch-eval", response_model=BatchEvalStartResponse)
async def start_batch_eval(request: BatchEvalRequest):
    """배치 평가 시작 — 랜덤 또는 명시적 세션"""
    session_service, _ = _get_services()

    if request.session_ids:
        session_ids = request.session_ids
    else:
        all_sessions = session_service.list_sessions(limit=500)
        valid = [
            s["session_id"] for s in all_sessions
            if s.get("image_path") or s.get("file_path")
        ]
        if not valid:
            raise HTTPException(400, "이미지가 있는 세션이 없습니다")
        count = min(request.count, len(valid))
        session_ids = random.sample(valid, count)

    batch_id = str(uuid.uuid4())[:8]
    rows = [SessionEvalRow(session_id=sid) for sid in session_ids]
    batch = BatchEvalStatus(batch_id=batch_id, total=len(session_ids), rows=rows)
    _batches[batch_id] = batch

    task = asyncio.create_task(_run_batch(batch_id))
    _tasks[batch_id] = task

    return BatchEvalStartResponse(
        batch_id=batch_id, total=len(session_ids), session_ids=session_ids,
    )


@router.post("/dimensions/batch-eval/{batch_id}/cancel")
async def cancel_batch_eval(batch_id: str):
    """배치 취소 — 실행 중인 배치를 중단"""
    batch = _batches.get(batch_id)
    if not batch:
        raise HTTPException(404, "배치를 찾을 수 없습니다")
    if batch.status not in ("running", "pending"):
        return {"ok": False, "message": "이미 완료된 배치입니다"}
    batch.status = "cancelled"
    task = _tasks.get(batch_id)
    if task and not task.done():
        task.cancel()
    _save_batch(batch)
    return {"ok": True, "batch_id": batch_id}


@router.get("/dimensions/batch-eval/list", response_model=List[BatchListItem])
async def list_batches():
    """배치 목록 — 새로고침 복원용"""
    return [
        BatchListItem(
            batch_id=b.batch_id, status=b.status,
            total=b.total, completed=b.completed, failed=b.failed,
        )
        for b in _batches.values()
    ]


@router.get("/dimensions/batch-eval/{batch_id}/status", response_model=BatchEvalStatus)
async def get_batch_eval_status(batch_id: str):
    """배치 진행률 + 부분 결과"""
    batch = _batches.get(batch_id)
    if not batch:
        raise HTTPException(404, "배치를 찾을 수 없습니다")
    return batch


@router.get("/dimensions/batch-eval/{batch_id}/results", response_model=BatchEvalStatus)
async def get_batch_eval_results(batch_id: str):
    """최종 결과 (status와 동일, 의미적 분리)"""
    batch = _batches.get(batch_id)
    if not batch:
        raise HTTPException(404, "배치를 찾을 수 없습니다")
    return batch


@router.patch("/dimensions/batch-eval/{batch_id}/sessions/{session_id}/eval")
async def save_session_eval(batch_id: str, session_id: str, update: SessionEvalUpdate):
    """후행 평가 저장 — 사용자가 맞음/틀림 토글"""
    batch = _batches.get(batch_id)
    if not batch:
        raise HTTPException(404, "배치를 찾을 수 없습니다")

    row = next((r for r in batch.rows if r.session_id == session_id), None)
    if not row:
        raise HTTPException(404, "세션을 찾을 수 없습니다")

    if update.od_correct is not None:
        row.od_correct = update.od_correct
    if update.id_correct is not None:
        row.id_correct = update.id_correct
    if update.w_correct is not None:
        row.w_correct = update.w_correct

    # 디스크 + 세션에 영속화
    _save_batch(batch)
    session_service, _ = _get_services()
    session_service.update_session(session_id, {
        "batch_eval": {
            "od": row.od, "id": row.id_val, "w": row.width,
            "od_correct": row.od_correct,
            "id_correct": row.id_correct,
            "w_correct": row.w_correct,
        }
    })

    return {"ok": True, "session_id": session_id}
