"""기하학 파이프라인 디버그 라우터

K/L/M/N 방법의 디버그 이미지를 생성·제공한다.
- K: 원검출 → 치수선 → OCR → 분류
- L: 원검출 → 끝점 분류 → 매칭 → 분류
- M: OCR → 심볼 검출 → 분류
- N: 원검출 → 레이 발사 → 교차 분석 → 분류
"""
import asyncio
import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis/dimensions")

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))

VALID_METHODS = {"K", "L", "M", "N"}


class GeometryDebugRequest(BaseModel):
    session_id: str
    ocr_engine: str = "paddleocr"


class MethodDebugRequest(BaseModel):
    session_id: str
    method: str = "L"
    ocr_engine: str = "paddleocr"


class DebugStepInfo(BaseModel):
    step: int
    title: str
    image_url: str
    data: dict = Field(default_factory=dict)


class GeometryDebugResponse(BaseModel):
    session_id: str
    method: str = "K"
    steps: list[DebugStepInfo] = Field(default_factory=list)
    success: bool = False
    error: Optional[str] = None


def _find_session_image(session_id: str) -> Optional[str]:
    """세션 디렉터리에서 원본 이미지 경로 반환"""
    session_dir = UPLOAD_DIR / session_id
    if not session_dir.exists():
        return None
    for ext in ("png", "jpg", "jpeg", "tif", "tiff"):
        for f in session_dir.glob(f"*.{ext}"):
            if "debug" not in f.stem and "step" not in f.stem:
                return str(f)
    return None


def _run_ocr_with_crop(image_path: str, engine: str = "paddleocr") -> list:
    """원 주변 크롭 후 OCR 실행 (K방법과 동일한 ROI 방식)"""
    import cv2
    import tempfile
    from services.dimension_service import DimensionService
    from services.geometric_methods import _detect_circles_for_methods

    img = cv2.imread(image_path)
    if img is None:
        return []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    orig_h, orig_w = gray.shape[:2]

    # 원 검출 → 가장 큰 원 기준 크롭
    circles = _detect_circles_for_methods(gray)
    if circles:
        circles.sort(key=lambda c: c[2], reverse=True)
        cx, cy, r = circles[0]
    else:
        cx, cy, r = orig_w // 2, orig_h // 2, min(orig_w, orig_h) // 3

    svc = DimensionService()
    all_dims = []

    # 2단계 크롭: focused (1.8r) + wide (3.0r)
    for mult in [1.8, 3.0]:
        margin = int(r * mult)
        y1 = max(0, cy - margin)
        y2 = min(orig_h, cy + margin)
        x1 = max(0, cx - margin)
        x2 = min(orig_w, cx + margin)

        crop = gray[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        fd, tp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            cv2.imwrite(tp, crop)
            result = svc.extract_dimensions(tp, 0.3, [engine])
            dims = result.get("dimensions", [])
            for d in dims:
                bbox = d.get("bbox") if isinstance(d, dict) else (d.bbox if hasattr(d, "bbox") else None)
                if bbox:
                    if isinstance(bbox, dict):
                        bbox["x1"] = bbox.get("x1", 0) + x1
                        bbox["y1"] = bbox.get("y1", 0) + y1
                        bbox["x2"] = bbox.get("x2", 0) + x1
                        bbox["y2"] = bbox.get("y2", 0) + y1
                    elif hasattr(bbox, "x1"):
                        bbox.x1 += x1
                        bbox.y1 += y1
                        bbox.x2 += x1
                        bbox.y2 += y1
                all_dims.append(d)
        finally:
            if os.path.exists(tp):
                os.unlink(tp)

    # Dimension 객체 → dict 변환 + 중복 제거
    out = []
    seen = set()
    for d in all_dims:
        if isinstance(d, dict):
            val = d.get("value", "")
        elif hasattr(d, "value"):
            val = d.value
            bbox = getattr(d, "bbox", None)
            d = {"value": val, "bbox": {}}
            if bbox and hasattr(bbox, "x1"):
                d["bbox"] = {"x1": bbox.x1, "y1": bbox.y1, "x2": bbox.x2, "y2": bbox.y2}
        else:
            continue
        if val not in seen:
            seen.add(val)
            out.append(d)

    return out


@router.post("/geometry-debug-steps", response_model=GeometryDebugResponse)
async def generate_geometry_debug_steps(req: GeometryDebugRequest):
    """K방법 4단계 디버그 오버레이 이미지 생성"""
    image_path = _find_session_image(req.session_id)
    if not image_path:
        raise HTTPException(404, f"세션 이미지 없음: {req.session_id}")

    output_dir = str(UPLOAD_DIR / req.session_id / "debug_steps")

    from services.geometry_debug_visualizer import generate_debug_step_images

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                generate_debug_step_images,
                image_path, req.ocr_engine, 0.3, output_dir,
            ),
            timeout=300,
        )
    except asyncio.TimeoutError:
        raise HTTPException(504, "디버그 파이프라인 타임아웃 (300초)")
    except Exception as e:
        logger.error(f"디버그 파이프라인 오류: {e}", exc_info=True)
        raise HTTPException(500, str(e))

    steps_response = []
    for s in result.get("steps", []):
        filename = os.path.basename(s["image_path"])
        url = f"/analysis/dimensions/geometry-debug-steps/{req.session_id}/{filename}"
        steps_response.append(DebugStepInfo(
            step=s["step"], title=s["title"], image_url=url, data=s.get("data", {}),
        ))

    return GeometryDebugResponse(
        session_id=req.session_id,
        method="K",
        steps=steps_response,
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/method-debug-steps", response_model=GeometryDebugResponse)
async def generate_method_debug_steps(req: MethodDebugRequest):
    """L/M/N 방법 디버그 오버레이 이미지 생성"""
    method = req.method.upper()
    if method not in {"L", "M", "N"}:
        raise HTTPException(400, f"지원 방법: L, M, N (K는 /geometry-debug-steps 사용)")

    image_path = _find_session_image(req.session_id)
    if not image_path:
        raise HTTPException(404, f"세션 이미지 없음: {req.session_id}")

    output_dir = str(UPLOAD_DIR / req.session_id / f"debug_steps_{method}")

    from services.geometry_methods_debug_visualizer import (
        generate_endpoint_topology_debug,
        generate_symbol_search_debug,
        generate_center_raycast_debug,
    )

    method_funcs = {
        "L": generate_endpoint_topology_debug,
        "M": generate_symbol_search_debug,
        "N": generate_center_raycast_debug,
    }

    func = method_funcs[method]

    try:
        # OCR 먼저 실행
        ocr_dims = await asyncio.wait_for(
            asyncio.to_thread(_run_ocr_with_crop, image_path, req.ocr_engine),
            timeout=120,
        )
        logger.info(f"[{method}] OCR 완료: {len(ocr_dims)}개 치수 검출")

        result = await asyncio.wait_for(
            asyncio.to_thread(func, image_path, ocr_dims, output_dir),
            timeout=180,
        )
    except asyncio.TimeoutError:
        raise HTTPException(504, f"{method} 디버그 타임아웃")
    except Exception as e:
        logger.error(f"{method} 디버그 오류: {e}", exc_info=True)
        raise HTTPException(500, str(e))

    steps_response = []
    for s in result.get("steps", []):
        filename = os.path.basename(s["image_path"])
        url = f"/analysis/dimensions/geometry-debug-steps/{req.session_id}/{filename}"
        steps_response.append(DebugStepInfo(
            step=s["step"], title=s["title"], image_url=url, data=s.get("data", {}),
        ))

    return GeometryDebugResponse(
        session_id=req.session_id,
        method=method,
        steps=steps_response,
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.get("/geometry-debug-steps/{session_id}/{filename}")
async def get_debug_step_image(session_id: str, filename: str):
    """디버그 단계 이미지 파일 반환"""
    # debug_steps 또는 debug_steps_L/M/N 디렉터리에서 검색
    for subdir in ["debug_steps", "debug_steps_L", "debug_steps_M", "debug_steps_N"]:
        file_path = UPLOAD_DIR / session_id / subdir / filename
        if file_path.exists():
            return FileResponse(str(file_path), media_type="image/png")
    raise HTTPException(404, f"이미지 없음: {filename}")
