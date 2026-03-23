"""기하학 방법 L/M/N 디버그 시각화

각 방법의 처리 단계를 개별 오버레이 이미지로 생성.
K방법은 geometry_debug_visualizer.py에서 처리.
"""
import cv2
import numpy as np
import re
import logging
import os
import tempfile
from typing import Dict, List, Optional, Tuple

from services.geometric_methods import (
    _detect_circles_for_methods,
    _detect_lines_lsd,
    _parse_numeric,
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
MAGENTA = (255, 0, 255)
DARK_GREEN = (0, 128, 0)


def _draw_label(canvas, text: str, pos: tuple, color: tuple, scale: float = 0.7, thickness: int = 2):
    """반투명 배경이 있는 텍스트 라벨"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
    x, y = int(pos[0]), int(pos[1])
    cv2.rectangle(canvas, (x - 2, y - th - 4), (x + tw + 4, y + baseline + 2), (0, 0, 0), -1)
    cv2.putText(canvas, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)


# ==================== Method L: Endpoint Topology Debug ====================

def generate_endpoint_topology_debug(
    image_path: str,
    ocr_dimensions: List[Dict],
    output_dir: Optional[str] = None,
) -> Dict:
    """L방법(끝점토폴로지) 디버그 이미지 생성

    Step 1: 원 검출
    Step 2: 치수선 검출 + 끝점 분류
    Step 3: 치수-치수선 매칭
    Step 4: OD/ID/W 분류 결과
    """
    img_color = cv2.imread(image_path)
    if img_color is None:
        return {"steps": [], "success": False, "error": "이미지 로드 실패"}

    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    orig_h, orig_w = img_gray.shape[:2]

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="l_debug_")
    os.makedirs(output_dir, exist_ok=True)

    steps = []

    # ── Step 1: 원 검출 ──
    circles = _detect_circles_for_methods(img_gray)
    canvas1 = img_color.copy()

    if not circles:
        _draw_label(canvas1, "Circle detection FAILED", (50, 50), RED, 1.0, 2)
        p1 = os.path.join(output_dir, "L_step1_circles.png")
        cv2.imwrite(p1, canvas1)
        steps.append({"step": 1, "title": "원 검출 (실패)", "image_path": p1, "data": {"found": False}})
        return {"steps": steps, "success": False, "error": "원 검출 실패"}

    circles.sort(key=lambda c: c[2], reverse=True)
    outer = circles[0]
    cx, cy, r_outer = outer

    for i, (ccx, ccy, cr) in enumerate(circles[:5]):
        color = BLUE if i == 0 else CYAN
        cv2.circle(canvas1, (ccx, ccy), cr, color, 3)
        label = f"{'Outer' if i == 0 else 'Inner'} R={cr}px" if i < 2 else f"C{i+1} R={cr}"
        _draw_label(canvas1, label, (ccx + cr + 10, ccy - 20 + i * 30), color, 0.6, 1)

    cv2.drawMarker(canvas1, (cx, cy), BLUE, cv2.MARKER_CROSS, 20, 2)

    p1 = os.path.join(output_dir, "L_step1_circles.png")
    cv2.imwrite(p1, canvas1)
    steps.append({"step": 1, "title": "원 검출 (Contour + HoughCircles)",
                  "image_path": p1, "data": {"circles": len(circles), "outer_r": r_outer}})

    # ── Step 2: 치수선 + 끝점 분류 ──
    lines = _detect_lines_lsd(img_gray)
    canvas2 = canvas1.copy()

    dim_lines_info = []
    for x1, y1, x2, y2, length in lines:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dist = np.sqrt((mx - cx)**2 + (my - cy)**2)
        if dist < r_outer * 0.5 or dist > r_outer * 3.5:
            continue

        ep_types = []
        for px, py in [(x1, y1), (x2, y2)]:
            d_center = np.sqrt((px - cx)**2 + (py - cy)**2)
            d_circumference = abs(d_center - r_outer)
            if d_center < r_outer * 0.15:
                ep_types.append("center")
            elif d_circumference < r_outer * 0.2:
                ep_types.append("circumference")
            else:
                ep_types.append("unknown")

        near_center = "center" in ep_types
        ep_type = "center" if near_center else ("circumference" if ep_types.count("circumference") == 2 else "unknown")

        dim_lines_info.append({
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "near_center": near_center, "endpoint_type": ep_type,
            "ep_types": ep_types,
        })

    # 끝점 유형별 색상 표시
    ep_colors = {"center": RED, "circumference": MAGENTA, "unknown": GREEN}
    for dl in dim_lines_info:
        ix1, iy1, ix2, iy2 = int(dl["x1"]), int(dl["y1"]), int(dl["x2"]), int(dl["y2"])
        cv2.line(canvas2, (ix1, iy1), (ix2, iy2), GREEN, 2)

        # 끝점 마커 (유형별 색상)
        for j, (px, py) in enumerate([(ix1, iy1), (ix2, iy2)]):
            ep_col = ep_colors.get(dl["ep_types"][j], GREEN)
            cv2.circle(canvas2, (px, py), 8, ep_col, -1)  # 채워진 원

        # 끝점 유형 라벨
        mid_x, mid_y = (ix1 + ix2) // 2, (iy1 + iy2) // 2
        _draw_label(canvas2, dl["endpoint_type"], (mid_x, mid_y), WHITE, 0.4, 1)

    # 범례
    _draw_label(canvas2, "RED=center  MAGENTA=circumference  GREEN=unknown", (20, orig_h - 30), WHITE, 0.6, 1)

    ep_counts = {"center": 0, "circumference": 0, "unknown": 0}
    for dl in dim_lines_info:
        ep_counts[dl["endpoint_type"]] += 1

    p2 = os.path.join(output_dir, "L_step2_endpoints.png")
    cv2.imwrite(p2, canvas2)
    steps.append({"step": 2, "title": "치수선 끝점 분류",
                  "image_path": p2, "data": {"line_count": len(dim_lines_info), "ep_counts": ep_counts}})

    # ── Step 3: 치수-치수선 매칭 ──
    canvas3 = canvas2.copy()

    matches = []
    for d in ocr_dimensions:
        val = d.get("value", "")
        bbox = d.get("bbox", {})
        v = _try_parse_numeric(val)
        if v is None or v < 5:
            continue
        if re.match(r'^M\d', val.strip(), re.IGNORECASE):
            continue

        dim_cx = (bbox.get("x1", 0) + bbox.get("x2", 0)) / 2
        dim_cy = (bbox.get("y1", 0) + bbox.get("y2", 0)) / 2

        best_dl = None
        best_dist = float('inf')
        for dl in dim_lines_info:
            for px, py in [(dl["x1"], dl["y1"]), (dl["x2"], dl["y2"])]:
                dd = np.sqrt((px - dim_cx)**2 + (py - dim_cy)**2)
                if dd < best_dist:
                    best_dist = dd
                    best_dl = dl

        matched = best_dl is not None and best_dist < r_outer * 0.5
        matches.append({
            "value": val, "numeric": v,
            "bbox": bbox, "matched": matched,
            "endpoint_type": best_dl["endpoint_type"] if matched else None,
            "dist": best_dist,
        })

        # 시각화: 치수와 매칭된 치수선을 연결선으로 표시
        bx = int(dim_cx)
        by = int(dim_cy)
        if matched and best_dl:
            ml_x = int((best_dl["x1"] + best_dl["x2"]) / 2)
            ml_y = int((best_dl["y1"] + best_dl["y2"]) / 2)
            cv2.line(canvas3, (bx, by), (ml_x, ml_y), YELLOW, 1, cv2.LINE_AA)
            _draw_label(canvas3, f"{val} -> {best_dl['endpoint_type']}", (bx, by - 10), YELLOW, 0.5, 1)
        else:
            _draw_label(canvas3, f"{val} (unmatched)", (bx, by - 10), WHITE, 0.4, 1)

    p3 = os.path.join(output_dir, "L_step3_matching.png")
    cv2.imwrite(p3, canvas3)
    matched_count = sum(1 for m in matches if m["matched"])
    steps.append({"step": 3, "title": "치수-치수선 매칭",
                  "image_path": p3, "data": {"total_dims": len(matches), "matched": matched_count}})

    # ── Step 4: OD/ID/W 분류 ──
    canvas4 = canvas3.copy()

    # 실제 분류 로직 재현
    classified = {"od": None, "id": None, "w": None}
    has_od, has_id, has_w = False, False, False

    # center 끝점 매칭 → RADIUS → ×2 → OD/ID
    for m in matches:
        if not m["matched"]:
            continue
        if m["endpoint_type"] == "center" and m["numeric"] >= 5:
            dia_val = m["numeric"] * 2
            if dia_val > 80 and not has_od:
                classified["od"] = {"value": f"Ø{int(dia_val)}", "original": m["value"], "reason": "center endpoint → R×2"}
                has_od = True
            elif not has_id:
                classified["id"] = {"value": f"Ø{int(dia_val)}", "original": m["value"], "reason": "center endpoint → R×2"}
                has_id = True
        elif m["endpoint_type"] == "circumference":
            if m["numeric"] > 80 and not has_od:
                classified["od"] = {"value": m["value"], "original": m["value"], "reason": "circumference endpoint → Ø"}
                has_od = True
            elif not has_id:
                classified["id"] = {"value": m["value"], "original": m["value"], "reason": "circumference endpoint → Ø"}
                has_id = True

    # 미분류 → 크기순 폴백
    unclassified = sorted([m for m in matches if m["value"] not in
                          [classified[r]["original"] for r in ("od", "id", "w") if classified[r]]],
                         key=lambda x: x["numeric"], reverse=True)
    for m in unclassified:
        if not has_od:
            classified["od"] = {"value": m["value"], "reason": "size ranking fallback"}
            has_od = True
        elif not has_id:
            classified["id"] = {"value": m["value"], "reason": "size ranking fallback"}
            has_id = True
        elif not has_w:
            classified["w"] = {"value": m["value"], "reason": "size ranking fallback"}
            has_w = True

    role_colors = {"od": RED, "id": BLUE, "w": GREEN}
    role_labels = {"od": "OD", "id": "ID", "w": "W"}

    for role in ["od", "id", "w"]:
        info = classified[role]
        if info is None:
            continue
        # 해당 치수의 bbox 찾기
        for m in matches:
            if m["value"] == info.get("original", info.get("value", "")):
                bbox = m["bbox"]
                if isinstance(bbox, dict) and "x1" in bbox:
                    bx1, by1 = int(bbox["x1"]), int(bbox["y1"])
                    bx2, by2 = int(bbox["x2"]), int(bbox["y2"])
                    color = role_colors[role]
                    cv2.rectangle(canvas4, (bx1, by1), (bx2, by2), color, 3)
                    reason = info.get("reason", "")
                    _draw_label(canvas4, f"{role_labels[role]}: {info['value']} ({reason})", (bx1, by1 - 15), color, 0.6, 2)
                break

    p4 = os.path.join(output_dir, "L_step4_classify.png")
    cv2.imwrite(p4, canvas4)
    steps.append({"step": 4, "title": "OD/ID/W 분류 결과",
                  "image_path": p4, "data": {
                      "od": classified["od"]["value"] if classified["od"] else None,
                      "id": classified["id"]["value"] if classified["id"] else None,
                      "w": classified["w"]["value"] if classified["w"] else None,
                  }})

    return {"steps": steps, "success": True, "error": None}


# ==================== Method M: Symbol Search Debug ====================

def generate_symbol_search_debug(
    image_path: str,
    ocr_dimensions: List[Dict],
    output_dir: Optional[str] = None,
) -> Dict:
    """M방법(심볼검색) 디버그 이미지 생성

    Step 1: 전체 OCR 결과 표시
    Step 2: R/Ø 심볼 검출 하이라이트
    Step 3: OD/ID/W 분류 결과
    """
    img_color = cv2.imread(image_path)
    if img_color is None:
        return {"steps": [], "success": False, "error": "이미지 로드 실패"}

    orig_h, orig_w = img_color.shape[:2]

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="m_debug_")
    os.makedirs(output_dir, exist_ok=True)

    steps = []

    # ── Step 1: 전체 OCR 결과 ──
    canvas1 = img_color.copy()

    for d in ocr_dimensions:
        bbox = d.get("bbox", {})
        val = d.get("value", "")
        if isinstance(bbox, dict) and "x1" in bbox:
            bx1, by1 = int(bbox["x1"]), int(bbox["y1"])
            bx2, by2 = int(bbox["x2"]), int(bbox["y2"])
            cv2.rectangle(canvas1, (bx1, by1), (bx2, by2), WHITE, 1)
            _draw_label(canvas1, val, (bx1, by1 - 5), WHITE, 0.5, 1)

    p1 = os.path.join(output_dir, "M_step1_ocr.png")
    cv2.imwrite(p1, canvas1)
    steps.append({"step": 1, "title": "전체 OCR 결과",
                  "image_path": p1, "data": {"ocr_count": len(ocr_dimensions)}})

    # ── Step 2: R/Ø 심볼 하이라이트 ──
    canvas2 = img_color.copy()  # 깨끗한 원본에서 시작

    r_pattern = re.compile(r'^[Rr]\s*(\d+[\.,]?\d*)')
    d_pattern = re.compile(r'^[Øø⌀∅ΦφΦ]\s*(\d+[\.,]?\d*)')

    symbols = []
    non_symbols = []

    for d in ocr_dimensions:
        bbox = d.get("bbox", {})
        val = d.get("value", "").strip()
        if not isinstance(bbox, dict) or "x1" not in bbox:
            continue

        bx1, by1 = int(bbox["x1"]), int(bbox["y1"])
        bx2, by2 = int(bbox["x2"]), int(bbox["y2"])

        r_match = r_pattern.match(val)
        d_match = d_pattern.match(val)

        if d_match:
            d_val = float(d_match.group(1).replace(',', '.'))
            cv2.rectangle(canvas2, (bx1, by1), (bx2, by2), MAGENTA, 3)
            _draw_label(canvas2, f"Ø DIAMETER: {val} = {d_val}mm", (bx1, by1 - 15), MAGENTA, 0.7, 2)
            symbols.append({"text": val, "type": "DIAMETER", "value": d_val})
        elif r_match:
            r_val = float(r_match.group(1).replace(',', '.'))
            dia_val = r_val * 2
            cv2.rectangle(canvas2, (bx1, by1), (bx2, by2), ORANGE, 3)
            _draw_label(canvas2, f"R RADIUS: {val} -> Ø{int(dia_val)}", (bx1, by1 - 15), ORANGE, 0.7, 2)
            symbols.append({"text": val, "type": "RADIUS", "original": r_val, "converted": dia_val})
        else:
            cv2.rectangle(canvas2, (bx1, by1), (bx2, by2), WHITE, 1)
            _draw_label(canvas2, val, (bx1, by1 - 5), WHITE, 0.4, 1)
            non_symbols.append(val)

    # 범례
    _draw_label(canvas2, f"MAGENTA=Ø diameter  ORANGE=R radius  WHITE=no symbol  Found: {len(symbols)}", (20, orig_h - 30), WHITE, 0.6, 1)

    p2 = os.path.join(output_dir, "M_step2_symbols.png")
    cv2.imwrite(p2, canvas2)
    steps.append({"step": 2, "title": "R/Ø 심볼 검출",
                  "image_path": p2, "data": {"symbols_found": len(symbols), "symbols": symbols}})

    # ── Step 3: OD/ID/W 분류 ──
    canvas3 = canvas2.copy()

    classified = {"od": None, "id": None, "w": None}

    # 심볼 기반 분류
    diameter_values = []
    for s in symbols:
        if s["type"] == "DIAMETER":
            diameter_values.append(s["value"])
        elif s["type"] == "RADIUS":
            diameter_values.append(s["converted"])

    diameter_values.sort(reverse=True)

    if diameter_values:
        classified["od"] = {"value": f"Ø{int(diameter_values[0])}", "reason": "largest Ø symbol"}
    if len(diameter_values) > 1:
        classified["id"] = {"value": f"Ø{int(diameter_values[1])}", "reason": "2nd largest Ø symbol"}

    # 미분류 → 크기순 폴백 (비심볼 치수)
    numeric_dims = []
    for d in ocr_dimensions:
        val = d.get("value", "").strip()
        if re.match(r'^M\d', val, re.IGNORECASE):
            continue
        v = _try_parse_numeric(val)
        if v is not None and v > 5:
            numeric_dims.append({"value": val, "numeric": v, "bbox": d.get("bbox", {})})

    numeric_dims.sort(key=lambda x: x["numeric"], reverse=True)

    for nd in numeric_dims:
        if not classified["od"]:
            classified["od"] = {"value": nd["value"], "reason": "size fallback (no Ø found)"}
        elif not classified["id"]:
            classified["id"] = {"value": nd["value"], "reason": "size fallback"}
        elif not classified["w"]:
            classified["w"] = {"value": nd["value"], "reason": "size fallback (W)"}

    role_colors = {"od": RED, "id": BLUE, "w": GREEN}
    role_labels = {"od": "OD", "id": "ID", "w": "W"}

    for role in ["od", "id", "w"]:
        info = classified[role]
        if info is None:
            continue
        # bbox 찾기
        for d in ocr_dimensions:
            if d.get("value", "").strip() == info.get("value", "").replace("Ø", "").strip():
                bbox = d.get("bbox", {})
                if isinstance(bbox, dict) and "x1" in bbox:
                    bx1, by1 = int(bbox["x1"]), int(bbox["y1"])
                    bx2, by2 = int(bbox["x2"]), int(bbox["y2"])
                    color = role_colors[role]
                    cv2.rectangle(canvas3, (bx1, by1), (bx2, by2), color, 4)
                    _draw_label(canvas3, f"{role_labels[role]}: {info['value']} ({info['reason']})", (bx1, by1 - 20), color, 0.7, 2)
                break

    p3 = os.path.join(output_dir, "M_step3_classify.png")
    cv2.imwrite(p3, canvas3)
    steps.append({"step": 3, "title": "OD/ID/W 분류 결과",
                  "image_path": p3, "data": {
                      "od": classified["od"]["value"] if classified["od"] else None,
                      "id": classified["id"]["value"] if classified["id"] else None,
                      "w": classified["w"]["value"] if classified["w"] else None,
                  }})

    return {"steps": steps, "success": True, "error": None}


# ==================== Method N: Center Raycast Debug ====================

def generate_center_raycast_debug(
    image_path: str,
    ocr_dimensions: List[Dict],
    output_dir: Optional[str] = None,
) -> Dict:
    """N방법(중심레이캐스트) 디버그 이미지 생성

    Step 1: 원 검출
    Step 2: 8방향 레이 발사 시각화
    Step 3: 레이-치수 교차 분석
    Step 4: OD/ID/W 분류 결과
    """
    img_color = cv2.imread(image_path)
    if img_color is None:
        return {"steps": [], "success": False, "error": "이미지 로드 실패"}

    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    orig_h, orig_w = img_gray.shape[:2]

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="n_debug_")
    os.makedirs(output_dir, exist_ok=True)

    steps = []

    # ── Step 1: 원 검출 ──
    circles = _detect_circles_for_methods(img_gray)
    canvas1 = img_color.copy()

    if not circles:
        _draw_label(canvas1, "Circle detection FAILED", (50, 50), RED, 1.0, 2)
        p1 = os.path.join(output_dir, "N_step1_circles.png")
        cv2.imwrite(p1, canvas1)
        steps.append({"step": 1, "title": "원 검출 (실패)", "image_path": p1, "data": {"found": False}})
        return {"steps": steps, "success": False, "error": "원 검출 실패"}

    circles.sort(key=lambda c: c[2], reverse=True)
    outer = circles[0]
    cx, cy, r_outer = outer

    for i, (ccx, ccy, cr) in enumerate(circles[:5]):
        color = BLUE if i == 0 else CYAN
        cv2.circle(canvas1, (ccx, ccy), cr, color, 3)
    cv2.drawMarker(canvas1, (cx, cy), BLUE, cv2.MARKER_CROSS, 20, 2)
    _draw_label(canvas1, f"Center ({cx},{cy}) R={r_outer}", (cx + r_outer + 10, cy), BLUE, 0.6, 1)

    p1 = os.path.join(output_dir, "N_step1_circles.png")
    cv2.imwrite(p1, canvas1)
    steps.append({"step": 1, "title": "원 검출",
                  "image_path": p1, "data": {"cx": cx, "cy": cy, "r": r_outer}})

    # ── Step 2: 8방향 레이 발사 ──
    canvas2 = canvas1.copy()

    angles = [0, 45, 90, 135, 180, 225, 270, 315]
    ray_length = r_outer * 3
    ray_colors = [RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, MAGENTA, WHITE]

    for idx, angle in enumerate(angles):
        rad = np.radians(angle)
        end_x = int(cx + ray_length * np.cos(rad))
        end_y = int(cy - ray_length * np.sin(rad))
        color = ray_colors[idx % len(ray_colors)]
        cv2.line(canvas2, (cx, cy), (end_x, end_y), color, 2, cv2.LINE_AA)
        # 각도 라벨
        label_x = int(cx + (r_outer * 1.2) * np.cos(rad))
        label_y = int(cy - (r_outer * 1.2) * np.sin(rad))
        _draw_label(canvas2, f"{angle}deg", (label_x, label_y), color, 0.4, 1)

    # 반지름/직경 원 표시
    cv2.circle(canvas2, (cx, cy), r_outer, BLUE, 1, cv2.LINE_AA)
    cv2.circle(canvas2, (cx, cy), r_outer * 2, DARK_GREEN, 1, cv2.LINE_AA)
    _draw_label(canvas2, f"r={r_outer}px", (cx + r_outer + 5, cy + 20), BLUE, 0.5, 1)
    _draw_label(canvas2, f"d={r_outer*2}px", (cx + r_outer * 2 + 5, cy + 20), DARK_GREEN, 0.5, 1)

    p2 = os.path.join(output_dir, "N_step2_rays.png")
    cv2.imwrite(p2, canvas2)
    steps.append({"step": 2, "title": "8방향 레이 발사",
                  "image_path": p2, "data": {"angles": angles, "ray_length": int(ray_length)}})

    # ── Step 3: 레이-치수 교차 ──
    canvas3 = canvas2.copy()

    intersections = []
    for d in ocr_dimensions:
        bbox = d.get("bbox", {})
        val = d.get("value", "").strip()
        v = _try_parse_numeric(val)
        if v is None or v < 5:
            continue
        if re.match(r'^M\d', val, re.IGNORECASE):
            continue
        if not isinstance(bbox, dict) or "x1" not in bbox:
            continue

        bx1, by1 = bbox["x1"], bbox["y1"]
        bx2, by2 = bbox["x2"], bbox["y2"]
        bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2

        # 치수 중심까지의 거리
        distance = np.sqrt((bcx - cx)**2 + (bcy - cy)**2)
        r_ratio = distance / r_outer if r_outer > 0 else 0

        # ray 교차 검사
        hit = False
        for angle in angles:
            rad = np.radians(angle)
            end_x = cx + ray_length * np.cos(rad)
            end_y = cy - ray_length * np.sin(rad)
            hit_result = _simple_ray_bbox_check(cx, cy, end_x, end_y, bx1, by1, bx2, by2)
            if hit_result:
                hit = True
                break

        if hit or distance < r_outer * 3:
            # 거리 분류
            if 0.7 <= r_ratio <= 1.3:
                zone = "RADIUS zone"
                zone_color = ORANGE
            elif 1.7 <= r_ratio <= 2.3:
                zone = "DIAMETER zone"
                zone_color = MAGENTA
            else:
                zone = "outside"
                zone_color = WHITE

            intersections.append({
                "value": val, "numeric": v,
                "distance": distance, "r_ratio": r_ratio,
                "zone": zone, "bbox": bbox, "hit": hit,
            })

            ibx1, iby1, ibx2, iby2 = int(bx1), int(by1), int(bx2), int(by2)
            cv2.rectangle(canvas3, (ibx1, iby1), (ibx2, iby2), zone_color, 2)
            _draw_label(canvas3, f"{val} d={int(distance)}px ratio={r_ratio:.1f} [{zone}]",
                       (ibx1, iby1 - 10), zone_color, 0.4, 1)
            # 중심에서 치수까지 연결선
            cv2.line(canvas3, (cx, cy), (int(bcx), int(bcy)), zone_color, 1, cv2.LINE_AA)

    p3 = os.path.join(output_dir, "N_step3_intersections.png")
    cv2.imwrite(p3, canvas3)
    steps.append({"step": 3, "title": "레이-치수 교차 분석",
                  "image_path": p3, "data": {
                      "intersection_count": len(intersections),
                      "radius_zone": sum(1 for i in intersections if i["zone"] == "RADIUS zone"),
                      "diameter_zone": sum(1 for i in intersections if i["zone"] == "DIAMETER zone"),
                  }})

    # ── Step 4: OD/ID/W 분류 ──
    canvas4 = img_color.copy()  # 깨끗한 원본에서

    # 원 다시 그리기
    for i, (ccx, ccy, cr) in enumerate(circles[:5]):
        color = BLUE if i == 0 else CYAN
        cv2.circle(canvas4, (ccx, ccy), cr, color, 2)

    classified = {"od": None, "id": None, "w": None}

    # RADIUS zone → R×2 → OD/ID
    for inter in sorted(intersections, key=lambda x: x["numeric"], reverse=True):
        if inter["zone"] == "RADIUS zone":
            dia_val = inter["numeric"] * 2
            if dia_val > 80 and not classified["od"]:
                classified["od"] = {"value": f"Ø{int(dia_val)}", "original": inter["value"],
                                   "reason": "radius zone → ×2", "bbox": inter["bbox"]}
            elif not classified["id"]:
                classified["id"] = {"value": f"Ø{int(dia_val)}", "original": inter["value"],
                                   "reason": "radius zone → ×2", "bbox": inter["bbox"]}

    # DIAMETER zone → OD/ID
    for inter in sorted(intersections, key=lambda x: x["numeric"], reverse=True):
        if inter["zone"] == "DIAMETER zone":
            if not classified["od"]:
                classified["od"] = {"value": inter["value"], "reason": "diameter zone", "bbox": inter["bbox"]}
            elif not classified["id"]:
                classified["id"] = {"value": inter["value"], "reason": "diameter zone", "bbox": inter["bbox"]}

    # 크기순 폴백
    all_sorted = sorted(intersections, key=lambda x: x["numeric"], reverse=True)
    for inter in all_sorted:
        v = inter["value"]
        already = [classified[r].get("original", classified[r].get("value", "")) for r in ("od", "id", "w") if classified[r]]
        if v in already:
            continue
        if not classified["od"]:
            classified["od"] = {"value": v, "reason": "size fallback", "bbox": inter["bbox"]}
        elif not classified["id"]:
            classified["id"] = {"value": v, "reason": "size fallback", "bbox": inter["bbox"]}
        elif not classified["w"]:
            classified["w"] = {"value": v, "reason": "size fallback", "bbox": inter["bbox"]}

    role_colors = {"od": RED, "id": BLUE, "w": GREEN}
    role_labels = {"od": "OD", "id": "ID", "w": "W"}

    for role in ["od", "id", "w"]:
        info = classified[role]
        if info is None:
            continue
        bbox = info.get("bbox", {})
        if isinstance(bbox, dict) and "x1" in bbox:
            bx1, by1 = int(bbox["x1"]), int(bbox["y1"])
            bx2, by2 = int(bbox["x2"]), int(bbox["y2"])
            color = role_colors[role]
            cv2.rectangle(canvas4, (bx1, by1), (bx2, by2), color, 4)
            _draw_label(canvas4, f"{role_labels[role]}: {info['value']} ({info['reason']})", (bx1, by1 - 15), color, 0.7, 2)

    p4 = os.path.join(output_dir, "N_step4_classify.png")
    cv2.imwrite(p4, canvas4)
    steps.append({"step": 4, "title": "OD/ID/W 분류 결과",
                  "image_path": p4, "data": {
                      "od": classified["od"]["value"] if classified["od"] else None,
                      "id": classified["id"]["value"] if classified["id"] else None,
                      "w": classified["w"]["value"] if classified["w"] else None,
                  }})

    return {"steps": steps, "success": True, "error": None}


# ==================== 유틸리티 ====================

def _try_parse_numeric(text: str) -> Optional[float]:
    """텍스트에서 숫자 추출"""
    cleaned = re.sub(r'[Øø⌀∅ΦφΦRr()（）\s]', '', text.strip())
    cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None


def _simple_ray_bbox_check(ox, oy, ex, ey, bx1, by1, bx2, by2) -> bool:
    """간이 ray-bbox 교차 검사"""
    bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2
    dx, dy = ex - ox, ey - oy
    length = np.sqrt(dx**2 + dy**2)
    if length < 1:
        return False
    ux, uy = dx / length, dy / length
    vx, vy = bcx - ox, bcy - oy
    proj = vx * ux + vy * uy
    if proj < 0:
        return False
    perp = abs(vx * uy - vy * ux)
    bbox_diag = np.sqrt((bx2 - bx1)**2 + (by2 - by1)**2)
    return perp < bbox_diag * 0.7
