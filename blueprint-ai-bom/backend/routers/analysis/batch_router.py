"""Batch Analysis Router - 프로젝트 단위 일괄 분석

배치 분석 실행/진행률 조회:
- POST /analysis/batch/{project_id} → 백그라운드 일괄 분석 시작
- GET  /analysis/batch/{project_id}/status → 진행률 조회

다중 이미지 지원:
- 세션의 primary image + sub-images 모두 분석
- sub-image 결과는 image metadata에 저장
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis/batch", tags=["batch-analysis"])


# ==================== 진행률 추적 ====================

class BatchProgress(BaseModel):
    """배치 분석 진행률"""
    project_id: str
    status: str = "idle"  # idle, running, completed, error
    total: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    current_session: Optional[str] = None
    current_drawing: Optional[str] = None
    errors: list = Field(default_factory=list)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    # 품질 추적
    quality_pass: int = 0
    quality_warn: int = 0
    quality_fail: int = 0
    corrections_applied: int = 0

    @property
    def progress_percent(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.completed + self.failed + self.skipped) / self.total * 100, 1)

    @property
    def quality_pass_rate(self) -> float:
        done = self.quality_pass + self.quality_warn + self.quality_fail
        if done == 0:
            return 0.0
        return round(self.quality_pass / done * 100, 1)


# 프로젝트별 진행률 (in-memory)
_batch_progress: Dict[str, BatchProgress] = {}


class BatchRunRequest(BaseModel):
    """배치 분석 요청"""
    root_drawing_number: Optional[str] = Field(
        None, description="특정 어셈블리만 분석 (None이면 전체)"
    )
    force_rerun: bool = Field(
        False, description="이미 분석된 세션도 재실행"
    )


class BatchRunResponse(BaseModel):
    """배치 분석 응답"""
    project_id: str
    status: str
    total: int
    message: str


# ==================== 엔드포인트 ====================

@router.post("/{project_id}", response_model=BatchRunResponse)
async def start_batch_analysis(project_id: str, request: BatchRunRequest = None):
    """프로젝트 전체 세션 일괄 분석 시작 (백그라운드)

    BOM 데이터가 있으면 BOM 기반으로, 없으면 세션 목록 기반으로 분석.
    각 세션의 primary image + sub-images 모두 분석.
    """
    if request is None:
        request = BatchRunRequest()

    # 이미 실행 중이면 거부
    existing = _batch_progress.get(project_id)
    if existing and existing.status == "running":
        raise HTTPException(
            status_code=409,
            detail=f"이미 분석 실행 중입니다 ({existing.completed}/{existing.total})"
        )

    from services.project_service import get_project_service

    project_service = get_project_service(Path("/app/data"))
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    # BOM 기반 세션 수집 시도
    session_ids = _collect_sessions_from_bom(project_id, project_service, request)

    # BOM 세션이 실제로 존재하는지 검증
    if session_ids:
        from .core_router import get_session_service as _get_ss
        _ss = _get_ss()
        valid = {k: v for k, v in session_ids.items() if _ss.get_session(k)}
        if not valid:
            session_ids = {}  # 전부 무효 → fallback으로
        else:
            session_ids = valid

    # BOM 없거나 세션 무효면 프로젝트 세션 목록에서 수집
    if not session_ids:
        session_ids = _collect_sessions_from_project(project_id, request)

    if not session_ids:
        raise HTTPException(status_code=400, detail="분석할 세션이 없습니다")

    # 총 이미지 수 계산 (primary + sub-images)
    from .core_router import get_session_service
    session_service = get_session_service()
    total_images = 0
    for sid in session_ids:
        session = session_service.get_session(sid)
        if session:
            total_images += 1 + len(session.get("images", []))

    # 진행률 초기화 (이미지 단위로 추적)
    progress = BatchProgress(
        project_id=project_id,
        status="running",
        total=total_images,
        started_at=time.time(),
    )
    _batch_progress[project_id] = progress

    # 백그라운드 실행
    asyncio.create_task(
        _run_batch(project_id, session_ids, request.force_rerun)
    )

    return BatchRunResponse(
        project_id=project_id,
        status="running",
        total=total_images,
        message=f"{len(session_ids)}개 세션, {total_images}개 이미지 분석 시작",
    )


def _collect_sessions_from_bom(
    project_id: str,
    project_service,
    request: BatchRunRequest,
) -> Dict[str, str]:
    """BOM 데이터에서 세션 목록 수집"""
    try:
        from services.bom_pdf_parser import BOMPDFParser
        project_dir = project_service.projects_dir / project_id
        bom_parser = BOMPDFParser()
        bom_data = bom_parser.load_bom_items(project_dir)
        if not bom_data:
            return {}

        items = bom_data["items"]

        if request.root_drawing_number:
            from routers.project_router import _get_subtree_items
            items = _get_subtree_items(items, request.root_drawing_number)

        session_ids = {}
        for item in items:
            sid = item.get("session_id")
            if sid and sid not in session_ids:
                session_ids[sid] = item.get("drawing_number", "")
        return session_ids
    except Exception:
        return {}


def _collect_sessions_from_project(
    project_id: str,
    request: BatchRunRequest,
) -> Dict[str, str]:
    """프로젝트 세션 목록에서 직접 수집 (BOM 없을 때 fallback)"""
    from .core_router import get_session_service
    session_service = get_session_service()
    sessions = session_service.list_sessions_by_project(project_id, limit=200)

    session_ids = {}
    for s in sessions:
        sid = s.get("session_id", "")
        fname = s.get("filename", "")
        if sid:
            session_ids[sid] = fname
    return session_ids


@router.get("/{project_id}/status", response_model=BatchProgress)
async def get_batch_status(project_id: str):
    """배치 분석 진행률 조회"""
    progress = _batch_progress.get(project_id)
    if not progress:
        return BatchProgress(project_id=project_id, status="idle")
    return progress


@router.delete("/{project_id}")
async def cancel_batch(project_id: str):
    """배치 분석 취소"""
    progress = _batch_progress.get(project_id)
    if not progress or progress.status != "running":
        raise HTTPException(status_code=400, detail="실행 중인 분석이 없습니다")

    progress.status = "cancelled"
    return {"message": "취소 요청됨", "completed": progress.completed, "total": progress.total}


# ==================== 백그라운드 실행 ====================

async def _run_batch(
    project_id: str,
    session_ids: Dict[str, str],
    force_rerun: bool,
):
    """세션 + sub-images를 순차적으로 분석 (비동기 백그라운드)"""
    from .core_router import get_session_service

    progress = _batch_progress[project_id]
    session_service = get_session_service()

    for session_id, drawing_number in session_ids.items():
        if progress.status == "cancelled":
            break

        progress.current_session = session_id
        progress.current_drawing = drawing_number

        session = session_service.get_session(session_id)
        if not session:
            progress.failed += 1
            progress.errors.append(f"{drawing_number}: 세션 없음")
            continue

        # --- 1) Primary image 분석 ---
        file_path = session.get("file_path", "")
        if not file_path or not Path(file_path).exists():
            progress.failed += 1
            progress.errors.append(f"{drawing_number}: primary 이미지 없음")
        else:
            status = session.get("status", "")
            if status in ("verified", "completed") and not force_rerun:
                progress.skipped += 1
            else:
                try:
                    from .core_router import run_analysis
                    await run_analysis(session_id)
                    progress.completed += 1
                    logger.info(
                        f"[배치] {drawing_number} primary 완료 "
                        f"({progress.completed}/{progress.total})"
                    )
                except Exception as e:
                    progress.failed += 1
                    progress.errors.append(f"{drawing_number}: {str(e)[:100]}")
                    logger.error(f"[배치] {drawing_number} primary 실패: {e}")

        # --- 2) Sub-images 분석 ---
        sub_images = session.get("images", [])
        for img in sub_images:
            if progress.status == "cancelled":
                break

            image_id = img.get("image_id", "")
            img_filename = img.get("filename", "")
            img_path = img.get("file_path", "")

            progress.current_drawing = f"{drawing_number} > {img_filename}"

            if not img_path or not Path(img_path).exists():
                progress.failed += 1
                progress.errors.append(f"{img_filename}: 파일 없음")
                continue

            # 이미 분석된 sub-image 스킵
            if img.get("dimensions") and not force_rerun:
                progress.skipped += 1
                continue

            try:
                grade = await _analyze_sub_image(session_id, image_id, img_path)
                progress.completed += 1
                # 품질 추적
                if grade == "pass":
                    progress.quality_pass += 1
                elif grade == "warn":
                    progress.quality_warn += 1
                elif grade == "fail":
                    progress.quality_fail += 1
                logger.info(
                    f"[배치] {img_filename} 완료 [{grade}] "
                    f"({progress.completed}/{progress.total})"
                )
            except Exception as e:
                progress.failed += 1
                progress.errors.append(f"{img_filename}: {str(e)[:100]}")
                logger.error(f"[배치] {img_filename} 실패: {e}")

        await asyncio.sleep(0.3)

    progress.status = "completed" if progress.status != "cancelled" else "cancelled"
    progress.current_session = None
    progress.current_drawing = None
    progress.finished_at = time.time()

    elapsed = progress.finished_at - (progress.started_at or progress.finished_at)
    logger.info(
        f"[배치] 프로젝트 {project_id} 완료: "
        f"{progress.completed}성공, {progress.skipped}스킵, {progress.failed}실패 "
        f"({elapsed:.0f}초) | "
        f"품질: P={progress.quality_pass}/W={progress.quality_warn}/"
        f"F={progress.quality_fail} ({progress.quality_pass_rate}% pass)"
    )


async def _analyze_sub_image(session_id: str, image_id: str, image_path: str):
    """세션 sub-image 분석 — 치수 OCR + OD/ID/W 분류

    결과를 session.images[image_id]에 저장하여 프론트엔드에서 이미지별 결과 조회 가능.
    """
    from .core_router import get_session_service, get_dimension_service
    import cv2
    from services.opencv_classifier import classify_od_id_width, clean_dimension_value
    from schemas.dimension import Dimension, BoundingBox, MaterialRole

    session_service = get_session_service()
    dimension_service = get_dimension_service()

    # 1. 치수 OCR
    dimension_result = dimension_service.extract_dimensions(
        image_path=image_path,
        confidence_threshold=0.3,
        ocr_engines=["edocr2"],
    )
    dimensions = dimension_result.get("dimensions", [])

    # 2. 이미지 크기
    img = cv2.imread(image_path)
    iw = img.shape[1] if img is not None else 0
    ih = img.shape[0] if img is not None else 0

    # 3. OD/ID/W 분류
    dim_objects = []
    for d in dimensions:
        bbox = d.get("bbox", {})
        try:
            dim_obj = Dimension(
                id=d["id"],
                value=d.get("value", ""),
                raw_text=d.get("raw_text", d.get("value", "")),
                bbox=BoundingBox(
                    x1=bbox.get("x1", 0), y1=bbox.get("y1", 0),
                    x2=bbox.get("x2", 0), y2=bbox.get("y2", 0),
                ),
                dimension_type=d.get("dimension_type", "unknown"),
                confidence=d.get("confidence", 0.5),
                tolerance=d.get("tolerance"),
                material_role=None,
            )
            dim_objects.append(dim_obj)
        except Exception:
            continue

    # 세션명 전달 (BOM 기준값 활용)
    _session = session_service.get_session(session_id)
    _session_name = _session.get("filename", "") if _session else ""
    classified = classify_od_id_width(
        dim_objects, image_width=iw, image_height=ih,
        session_name=_session_name,
    )

    # 4. 분류 결과를 dict로 변환
    classified_dims = []
    for dim in classified:
        d_dict = dim.model_dump()
        d_dict["material_role"] = dim.material_role.value if dim.material_role else None
        classified_dims.append(d_dict)

    # 5. OD/ID/W 요약
    od = next((d for d in classified if d.material_role == MaterialRole.OUTER_DIAMETER), None)
    id_ = next((d for d in classified if d.material_role == MaterialRole.INNER_DIAMETER), None)
    w = next((d for d in classified if d.material_role == MaterialRole.LENGTH), None)
    od_clean = clean_dimension_value(od.value) if od else None
    id_clean = clean_dimension_value(id_.value) if id_ else None
    w_clean = clean_dimension_value(w.value) if w else None

    # 6. 검증 + 자기수정 루프
    from services.validation import validate_and_correct

    raw_result = {
        "od": od_clean, "id": id_clean, "width": w_clean,
        "dimension_count": len(classified_dims),
        "dimensions": classified_dims,
    }
    val_context = {"session_name": _session_name, "image_path": image_path}
    corrected, val_report = validate_and_correct(raw_result, val_context)

    # 7. session.images[image_id]에 보정된 결과 저장
    session = session_service.get_session(session_id)
    if not session:
        return

    images = session.get("images", [])
    for i, img_data in enumerate(images):
        if img_data.get("image_id") == image_id:
            images[i]["dimensions"] = classified_dims
            images[i]["dimension_count"] = len(classified_dims)
            images[i]["image_width"] = iw
            images[i]["image_height"] = ih
            images[i]["od"] = corrected.get("od")
            images[i]["id"] = corrected.get("id")
            images[i]["width"] = corrected.get("width")
            images[i]["quality_grade"] = val_report.grade.value
            images[i]["validation_summary"] = val_report.summary
            images[i]["correction_applied"] = len(val_report.corrections) > 0
            break

    session_service.update_session(session_id, {"images": images})

    return val_report.grade.value
