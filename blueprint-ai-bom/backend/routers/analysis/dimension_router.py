"""Dimension Router - 치수 관리 API

치수 CRUD, 검증, 일괄 처리 기능:
- 치수 목록 조회
- 치수 수정/삭제
- 일괄 검증
- eDOCr2 결과 가져오기
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging

from schemas.dimension import (
    Dimension,
    DimensionListResponse,
    DimensionUpdate,
    BulkDimensionVerificationUpdate,
    BulkDimensionImport,
    BulkDimensionImportResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Dimensions"])


def get_session_service():
    """core_router에서 세션 서비스 가져오기"""
    from .core_router import get_session_service as _get_session_service
    return _get_session_service()


def get_dimension_service():
    """core_router에서 치수 서비스 가져오기"""
    from .core_router import get_dimension_service as _get_dimension_service
    return _get_dimension_service()


# ==================== 치수 관리 API ====================

@router.get("/dimensions/{session_id}")
async def get_dimensions(session_id: str) -> DimensionListResponse:
    """세션의 치수 목록 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    dimensions = session.get("dimensions", [])

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

    dim_idx = None
    for idx, dim in enumerate(dimensions):
        if dim.get("id") == dimension_id:
            dim_idx = idx
            break

    if dim_idx is None:
        raise HTTPException(status_code=404, detail="치수를 찾을 수 없습니다")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            dimensions[dim_idx][key] = value

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

    session_service.update_session(session_id, {"dimensions": dimensions})

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

    new_dimension = dimension_service.add_manual_dimension(
        value=value,
        bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    )

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
    """eDOCr2 치수 결과 일괄 가져오기"""
    import uuid

    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    existing_dimensions = session.get("dimensions", [])
    imported_dimensions = []
    auto_approved_count = 0

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
            dim_id = f"dim_{uuid.uuid4().hex[:8]}"

            # "bbox" 또는 "location" 필드 모두 지원 (eDOCr2는 "location" 사용)
            bbox_raw = dim_data.get("bbox") or dim_data.get("location", {})
            if isinstance(bbox_raw, dict):
                bbox = {
                    "x1": int(bbox_raw.get("x1", bbox_raw.get("x", 0))),
                    "y1": int(bbox_raw.get("y1", bbox_raw.get("y", 0))),
                    "x2": int(bbox_raw.get("x2", bbox_raw.get("x", 0) + bbox_raw.get("width", 0))),
                    "y2": int(bbox_raw.get("y2", bbox_raw.get("y", 0) + bbox_raw.get("height", 0))),
                }
            elif isinstance(bbox_raw, list) and len(bbox_raw) >= 4:
                # nested list [[x1,y1],[x2,y2],...] (eDOCr2 polygon format)
                if isinstance(bbox_raw[0], (list, tuple)):
                    xs = [pt[0] for pt in bbox_raw]
                    ys = [pt[1] for pt in bbox_raw]
                    bbox = {
                        "x1": int(min(xs)),
                        "y1": int(min(ys)),
                        "x2": int(max(xs)),
                        "y2": int(max(ys)),
                    }
                else:
                    # flat list [x1, y1, x2, y2]
                    bbox = {
                        "x1": int(bbox_raw[0]),
                        "y1": int(bbox_raw[1]),
                        "x2": int(bbox_raw[2]),
                        "y2": int(bbox_raw[3]),
                    }
            else:
                logger.warning(f"알 수 없는 bbox 형식: {bbox_raw}")
                continue

            confidence = float(dim_data.get("confidence", dim_data.get("score", 0.5)))

            verification_status = "pending"
            if request.auto_approve_threshold and confidence >= request.auto_approve_threshold:
                verification_status = "approved"
                auto_approved_count += 1

            value = dim_data.get("value") or dim_data.get("text", "")

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

    all_dimensions = existing_dimensions + imported_dimensions

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
