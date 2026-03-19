"""Batch Evaluation Router — 다수 도면 일괄 치수 분석 + 후행 평가

GT 없는 도면에서도 결과를 보여주고, 사용자가 맞음/틀림 평가:
- POST /dimensions/batch-eval              — 배치 시작
- GET  /dimensions/batch-eval/{batch_id}/status  — 진행률 + 부분 결과
- GET  /dimensions/batch-eval/{batch_id}/results — 최종 결과
- PATCH /dimensions/batch-eval/{batch_id}/sessions/{session_id}/eval — 후행 평가
"""

import asyncio
import logging
import random
import time
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
    # 최종 선택 (K→H 폴백)
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


class SessionEvalUpdate(BaseModel):
    od_correct: Optional[bool] = None
    id_correct: Optional[bool] = None
    w_correct: Optional[bool] = None


# ==================== In-memory 상태 ====================

_batches: Dict[str, BatchEvalStatus] = {}


def _get_services():
    from routers.analysis.core_router import (
        get_session_service as _sess,
        get_dimension_service as _dim,
    )
    return _sess(), _dim()


# ==================== 배치 실행 로직 ====================

async def _run_batch(batch_id: str):
    """배치 평가 백그라운드 실행"""
    batch = _batches[batch_id]
    batch.status = "running"
    session_service, dimension_service = _get_services()

    for row in batch.rows:
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

            # OCR (edocr2 — 도면 특화, 빠름)
            ocr_result = await asyncio.to_thread(
                dimension_service.extract_dimensions,
                image_path, 0.5, ["edocr2"],
            )
            raw_dims = ocr_result.get("dimensions", [])
            img_w = ocr_result.get("image_width", 1)
            img_h = ocr_result.get("image_height", 1)

            # 기하학 보강
            from services.geometry_guided_extractor import (
                get_geometry_supplementary_dims, filter_ocr_noise,
                extract_by_geometry,
            )
            supp_dims, circle_r = await asyncio.to_thread(
                get_geometry_supplementary_dims, image_path, "paddleocr", 0.3,
            )
            if supp_dims and circle_r:
                supp_dims = filter_ocr_noise(supp_dims, circle_r)

            # 보충 치수 병합
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

            # K. geometry_guided (clean_dimension_value로 정제)
            try:
                from services.opencv_classifier import clean_dimension_value as _clean
                geo_result = await asyncio.to_thread(
                    extract_by_geometry, image_path, "paddleocr", 0.3,
                )
                geo_od = geo_result.get("od", {})
                geo_id = geo_result.get("id", {})
                geo_w = geo_result.get("w", {})
                row.geometry_od = _clean(geo_od.get("value", "")) if geo_od else None
                row.geometry_id = _clean(geo_id.get("value", "")) if geo_id else None
                row.geometry_w = _clean(geo_w.get("value", "")) if geo_w else None
            except Exception as e:
                logger.warning(f"K 방법 실패 ({row.session_id}): {e}")

            # H. value_ranking (clean_dimension_value로 노이즈 제거)
            try:
                from schemas.dimension import Dimension
                from services.opencv_classifier import (
                    _parse_numeric_value, clean_dimension_value,
                )

                dims_h = [
                    Dimension(**d).model_copy(update={"material_role": None})
                    for d in raw_dims
                ]
                all_vals = []
                for d in dims_h:
                    cleaned = clean_dimension_value(d.value)
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

            # S. 세션명 파서 (3차 폴백)
            session_ref_od, session_ref_id, session_ref_w = None, None, None
            try:
                from services.session_name_parser import parse_session_name_dimensions
                ref = parse_session_name_dimensions(row.filename)
                if ref["od"]:
                    session_ref_od = str(int(ref["od"]))
                if ref["id"]:
                    session_ref_id = str(int(ref["id"]))
                if ref["w"]:
                    session_ref_w = str(int(ref["w"]))
            except Exception:
                pass

            # 최종 선택: K → H → S 폴백
            row.od = row.geometry_od or row.ranking_od or session_ref_od
            row.id_val = row.geometry_id or row.ranking_id or session_ref_id
            row.width = row.geometry_w or row.ranking_w or session_ref_w

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

        # 세션 간 간격
        await asyncio.sleep(0.1)

    batch.status = "completed"


# ==================== 엔드포인트 ====================

@router.post("/dimensions/batch-eval", response_model=BatchEvalStartResponse)
async def start_batch_eval(request: BatchEvalRequest):
    """배치 평가 시작 — 랜덤 또는 명시적 세션"""
    session_service, _ = _get_services()

    if request.session_ids:
        session_ids = request.session_ids
    else:
        all_sessions = session_service.list_sessions(limit=500)
        # 이미지가 있는 세션만 필터
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

    asyncio.create_task(_run_batch(batch_id))

    return BatchEvalStartResponse(
        batch_id=batch_id, total=len(session_ids), session_ids=session_ids,
    )


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

    # 세션에도 영속화
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
