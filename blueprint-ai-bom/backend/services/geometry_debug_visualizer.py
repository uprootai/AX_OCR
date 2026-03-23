"""기하학 파이프라인 디버그 시각화

K방법(extract_by_geometry)의 4단계를 개별 오버레이 이미지로 생성.
각 단계에서 어떤 처리가 이루어지는지 시각적으로 추적한다.
"""
import cv2
import numpy as np
import logging
import os
import tempfile
from typing import Dict, Optional

from services.geometry_guided_extractor import (
    _detect_circles,
    _detect_dimension_lines,
    _crop_ocr_around_circles,
    _classify_by_circle_proximity,
)

logger = logging.getLogger(__name__)

# 색상 상수 (BGR)
BLUE = (255, 100, 0)
CYAN = (255, 255, 0)
GREEN = (0, 200, 0)
RED = (0, 0, 255)
ORANGE = (0, 165, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)


def _draw_label(canvas, text: str, pos: tuple, color: tuple, scale: float = 0.7, thickness: int = 2):
    """반투명 배경이 있는 텍스트 라벨"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
    x, y = int(pos[0]), int(pos[1])
    cv2.rectangle(canvas, (x - 2, y - th - 4), (x + tw + 4, y + baseline + 2), (0, 0, 0), -1)
    cv2.putText(canvas, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)


def generate_debug_step_images(
    image_path: str,
    ocr_engine: str = "paddleocr",
    confidence_threshold: float = 0.3,
    output_dir: Optional[str] = None,
) -> Dict:
    """4단계 디버그 오버레이 이미지 생성

    Returns:
        {"steps": [{"step": 1, "title": ..., "image_path": ..., "data": {...}}, ...],
         "success": bool, "error": str|None}
    """
    img_color = cv2.imread(image_path)
    if img_color is None:
        return {"steps": [], "success": False, "error": "이미지 로드 실패"}

    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    orig_h, orig_w = img_gray.shape[:2]

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="geo_debug_")
    os.makedirs(output_dir, exist_ok=True)

    steps = []

    # ── Step 1: 원 검출 ──
    circles_info = _detect_circles(img_gray, orig_w, orig_h)
    canvas1 = img_color.copy()

    if not circles_info["found"]:
        _draw_label(canvas1, "Circle detection FAILED", (50, 50), RED, 1.0, 2)
        p1 = os.path.join(output_dir, "step1_circles.png")
        cv2.imwrite(p1, canvas1)
        steps.append({"step": 1, "title": "원 검출 (실패)", "image_path": p1,
                       "data": {"found": False, "reason": circles_info.get("reason", "")}})
        return {"steps": steps, "success": False, "error": "원 검출 실패"}

    outer = circles_info["outer"]
    inner = circles_info.get("inner")
    cx, cy, r_out = int(outer[0]), int(outer[1]), int(outer[2])

    # 외원 (파란색)
    cv2.circle(canvas1, (cx, cy), r_out, BLUE, 3)
    _draw_label(canvas1, f"Outer R={r_out}px", (cx + r_out + 10, cy - 20), BLUE)
    # 중심 십자
    cv2.drawMarker(canvas1, (cx, cy), BLUE, cv2.MARKER_CROSS, 20, 2)

    step1_data = {"outer": {"cx": cx, "cy": cy, "r": r_out}, "total_circles": circles_info.get("total_circles", 0)}

    if inner is not None:
        icx, icy, r_in = int(inner[0]), int(inner[1]), int(inner[2])
        cv2.circle(canvas1, (icx, icy), r_in, CYAN, 3)
        _draw_label(canvas1, f"Inner R={r_in}px", (icx + r_in + 10, icy + 20), CYAN)
        step1_data["inner"] = {"cx": icx, "cy": icy, "r": r_in}

    p1 = os.path.join(output_dir, "step1_circles.png")
    cv2.imwrite(p1, canvas1)
    steps.append({"step": 1, "title": "원 검출 (Contour + HoughCircles)", "image_path": p1, "data": step1_data})

    # ── Step 2: 치수선 검출 ──
    dim_lines = _detect_dimension_lines(img_gray, outer, inner, orig_w, orig_h)
    canvas2 = canvas1.copy()

    for i, line in enumerate(dim_lines):
        x1, y1, x2, y2 = int(line["x1"]), int(line["y1"]), int(line["x2"]), int(line["y2"])
        cv2.line(canvas2, (x1, y1), (x2, y2), GREEN, 2)
        mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
        _draw_label(canvas2, line.get("direction", "?"), (mid_x, mid_y), GREEN, 0.5, 1)

    p2 = os.path.join(output_dir, "step2_dimlines.png")
    cv2.imwrite(p2, canvas2)
    steps.append({"step": 2, "title": "치수선 검출 (LSD)", "image_path": p2,
                   "data": {"line_count": len(dim_lines)}})

    # ── Step 3: ROI 크롭 + OCR ──
    canvas3 = canvas2.copy()

    # 크롭 영역 재계산 (geometry_guided_extractor와 동일 로직)
    m1 = int(r_out * 1.8)
    c1_y1, c1_y2 = max(0, cy - m1), min(orig_h, cy + m1)
    c1_x1, c1_x2 = max(0, cx - m1), min(orig_w, cx + m1)
    cv2.rectangle(canvas3, (c1_x1, c1_y1), (c1_x2, c1_y2), ORANGE, 2)
    _draw_label(canvas3, "Focused ROI (1.8r)", (c1_x1, c1_y1 - 5), ORANGE, 0.5, 1)

    c2_y1 = max(0, cy - int(r_out * 3.0))
    c2_y2 = min(orig_h, cy + int(r_out * 1.5))
    c2_x1 = max(0, cx - int(r_out * 2.0))
    c2_x2 = min(orig_w, cx + int(r_out * 2.0))
    cv2.rectangle(canvas3, (c2_x1, c2_y1), (c2_x2, c2_y2), YELLOW, 2)
    _draw_label(canvas3, "Wide ROI (3.0r)", (c2_x1, c2_y1 - 5), YELLOW, 0.5, 1)

    # OCR 실행
    try:
        crop_dims, crop_offset = _crop_ocr_around_circles(
            image_path, img_gray, outer, inner, ocr_engine, confidence_threshold, orig_w, orig_h,
        )
    except Exception as e:
        logger.warning(f"Step 3 OCR 실패: {e}")
        crop_dims = []

    ocr_values = []
    for d in crop_dims:
        val = d.get("value", "") if isinstance(d, dict) else (d.value if hasattr(d, "value") else "")
        bbox = d.get("bbox", {}) if isinstance(d, dict) else {}
        if isinstance(bbox, dict) and "x1" in bbox:
            bx1, by1 = int(bbox["x1"]), int(bbox["y1"])
            bx2, by2 = int(bbox["x2"]), int(bbox["y2"])
            cv2.rectangle(canvas3, (bx1, by1), (bx2, by2), WHITE, 1)
            _draw_label(canvas3, str(val), (bx1, by1 - 5), WHITE, 0.5, 1)
        ocr_values.append(val)

    p3 = os.path.join(output_dir, "step3_ocr.png")
    cv2.imwrite(p3, canvas3)
    steps.append({"step": 3, "title": "ROI 크롭 → OCR", "image_path": p3,
                   "data": {"ocr_count": len(crop_dims), "values": ocr_values}})

    # ── Step 4: OD/ID/W 분류 ──
    canvas4 = canvas3.copy()

    result = _classify_by_circle_proximity(crop_dims, outer, inner, orig_w, orig_h)

    role_colors = {"od": RED, "id": BLUE, "w": GREEN}
    role_labels = {"od": "OD", "id": "ID", "w": "W"}

    for role in ["od", "id", "w"]:
        dim_info = result.get(role)
        if dim_info is None:
            continue
        val = dim_info.get("value", "—")
        conf = dim_info.get("confidence", 0)
        bbox = dim_info.get("bbox", {})
        color = role_colors[role]
        label = f"{role_labels[role]}: {val} ({conf:.0%})"

        if isinstance(bbox, dict) and "x1" in bbox:
            bx1, by1 = int(bbox["x1"]), int(bbox["y1"])
            bx2, by2 = int(bbox["x2"]), int(bbox["y2"])
            cv2.rectangle(canvas4, (bx1, by1), (bx2, by2), color, 3)
            _draw_label(canvas4, label, (bx1, by1 - 10), color, 0.8, 2)

    p4 = os.path.join(output_dir, "step4_classify.png")
    cv2.imwrite(p4, canvas4)
    steps.append({"step": 4, "title": "OD/ID/W 역할 분류", "image_path": p4,
                   "data": {
                       "od": result.get("od", {}).get("value") if result.get("od") else None,
                       "id": result.get("id", {}).get("value") if result.get("id") else None,
                       "w": result.get("w", {}).get("value") if result.get("w") else None,
                   }})

    return {"steps": steps, "success": True, "error": None}
