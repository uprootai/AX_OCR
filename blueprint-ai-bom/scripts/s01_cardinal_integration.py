#!/usr/bin/env python3
"""S01 + Cardinal v3 통합 — S01 화살촉 쌍 매칭 + 투사선 필터

1. S01 arrowhead_detector: detect_arrowheads + match_arrowhead_pairs
2. Cardinal v3: 동심원 + 돌출부 끝점 투사선
3. 투사선 위에 있는 치수선 쌍만 필터
4. 치수선 중점 근처 OCR → 값 추출
5. 전체 도면 시각화
"""

import sys
import os
import cv2
import numpy as np
import requests
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# S01 arrowhead_detector import
sys.path.insert(0, str(Path(__file__).parent / ".." / "backend"))
from services.arrowhead_detector import detect_arrowheads, match_arrowhead_pairs

SRC_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs")
OUT_DIR = Path("/home/uproot/ax/poc/docs-site-starlight/public/images/gt-validation/steps")
OUT_DIR.mkdir(exist_ok=True)

OCR_API = "http://localhost:5006/api/v1/ocr"
MIN_R_RATIO = 0.08
MAX_R_RATIO = 0.48

GT = {
    "TD0062015": {"name": "t1", "od": 360, "id": 190, "w": 200},
    "TD0062021": {"name": "t2", "od": 380, "id": 190, "w": 200},
}


def get_font(size=16):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def add_header(img_bgr, title, sub1="", sub2=""):
    pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    h, w = img_bgr.shape[:2]
    font = get_font(max(16, h // 60))
    font_sm = get_font(max(12, h // 80))
    bar_h = 80 if sub2 else 60
    draw.rectangle([0, 0, w, bar_h], fill="#222222")
    draw.text((10, 5), title, fill="white", font=font)
    if sub1:
        draw.text((10, 30), sub1, fill="#AAAAAA", font=font_sm)
    if sub2:
        draw.text((10, 52), sub2, fill="#66BB6A", font=font_sm)
    return pil


def save_pil(pil_img, name, max_w=1400):
    if pil_img.width > max_w:
        r = max_w / pil_img.width
        pil_img = pil_img.resize((max_w, int(pil_img.height * r)), Image.LANCZOS)
    out = OUT_DIR / name
    pil_img.save(out, quality=85)
    print(f"  ✓ {name} ({pil_img.width}x{pil_img.height})")


# ── 동심원 + 돌출부 ──

def detect_concentric_alt(gray_roi, min_r, max_r):
    blurred = cv2.GaussianBlur(gray_roi, (5, 5), 1.5)
    circles = []
    hc = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT_ALT, dp=1.5,
        minDist=20, param1=150, param2=0.85,
        minRadius=min_r, maxRadius=max_r,
    )
    if hc is not None:
        for cx, cy, r in hc[0]:
            circles.append((float(cx), float(cy), float(r)))
    return circles


def radial_edge_scan(gray, cx, cy, outer_r, n_angles=360):
    h, w = gray.shape
    max_scan_r = int(outer_r * 1.5)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    edges = cv2.Canny(blurred, 50, 150)
    profile = []
    for i in range(n_angles):
        angle_rad = np.radians(i * 360.0 / n_angles)
        dx, dy = np.cos(angle_rad), np.sin(angle_rad)
        max_r_found, mx, my = 0, int(cx), int(cy)
        for r_px in range(int(outer_r * 0.8), max_scan_r):
            px = int(cx + r_px * dx)
            py = int(cy + r_px * dy)
            if 0 <= px < w and 0 <= py < h and edges[py, px] > 0:
                max_r_found, mx, my = r_px, px, py
        profile.append((i * 360.0 / n_angles, max_r_found, mx, my))
    protrusions = [p for p in profile if p[1] > outer_r * 1.05]
    if not protrusions:
        return []
    sorted_p = sorted(protrusions, key=lambda p: p[0])
    groups, cur = [], [sorted_p[0]]
    for i in range(1, len(sorted_p)):
        if sorted_p[i][0] - sorted_p[i - 1][0] <= 10:
            cur.append(sorted_p[i])
        else:
            groups.append(cur)
            cur = [sorted_p[i]]
    groups.append(cur)
    return [max(g, key=lambda p: p[1]) for g in groups]


# ── 투사선 생성 ──

def build_projection_lines(circles_full, peaks_full):
    """동심원 + 돌출부 끝점에서 투사선 목록 생성

    Returns: [(px, py, axis, source), ...]
        axis: 'h' or 'v'
        source: 'circle' or 'protrusion'
    """
    lines = []
    for cx, cy, r in circles_full:
        for dir_name, ddx, ddy, axis in [
            ("N", 0, -1, "h"), ("S", 0, 1, "h"),
            ("E", 1, 0, "v"), ("W", -1, 0, "v"),
        ]:
            lines.append((int(cx + r * ddx), int(cy + r * ddy), axis, "circle"))

    for angle, r_val, px, py in peaks_full:
        lines.append((px, py, "h", "protrusion"))
        lines.append((px, py, "v", "protrusion"))

    return lines


# ── 투사선 위 치수선 쌍 필터 ──

def filter_pairs_on_projections(dim_lines, proj_lines, tolerance=20):
    """S01 치수선 쌍 중 투사선 위에 있는 것만 필터

    치수선의 시작점 또는 끝점이 투사선(수평/수직) 위에 있으면 통과.
    """
    filtered = []
    for dl in dim_lines:
        sx, sy = dl["start"]["x"], dl["start"]["y"]
        ex, ey = dl["end"]["x"], dl["end"]["y"]
        mx, my = dl["midpoint"]["x"], dl["midpoint"]["y"]

        on_line = False
        for px, py, axis, source in proj_lines:
            if axis == "h":
                # 수평 투사선: 시작점/끝점/중점의 y가 투사선 y와 근접
                if (abs(sy - py) <= tolerance or
                    abs(ey - py) <= tolerance or
                    abs(my - py) <= tolerance):
                    on_line = True
                    dl["_proj_source"] = source
                    break
            else:
                if (abs(sx - px) <= tolerance or
                    abs(ex - px) <= tolerance or
                    abs(mx - px) <= tolerance):
                    on_line = True
                    dl["_proj_source"] = source
                    break

        if on_line:
            filtered.append(dl)

    return filtered


# ── OCR ──

def run_ocr(image_path):
    with open(image_path, 'rb') as f:
        resp = requests.post(OCR_API, files={
            'file': (image_path.name, f, 'image/jpeg')
        }, timeout=120)
        resp.raise_for_status()
    return resp.json().get("detections", [])


def match_ocr_to_dimlines(dim_lines, ocr_dets, search_radius=150):
    """치수선 중점 근처 OCR 텍스트 매칭"""
    ocr_nums = []
    for d in ocr_dets:
        text = d.get("text", "")
        bbox = d.get("bbox", [])
        m = re.search(r"[Øø]?\s*(\d+\.?\d*)", re.sub(r"[()]", "", text))
        if m and isinstance(bbox, list) and len(bbox) >= 4:
            val = float(m.group(1))
            if 10 < val < 3000:
                try:
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    ocr_nums.append({
                        "value": val, "text": text,
                        "cx": sum(xs) / len(xs), "cy": sum(ys) / len(ys),
                        "has_phi": bool(re.search(r"[Øø]", text)),
                    })
                except (TypeError, IndexError):
                    pass

    results = []
    for dl in dim_lines:
        mx = dl["midpoint"]["x"]
        my = dl["midpoint"]["y"]
        best, best_dist = None, float("inf")
        for ocr in ocr_nums:
            d = np.sqrt((ocr["cx"] - mx) ** 2 + (ocr["cy"] - my) ** 2)
            if d < search_radius and d < best_dist:
                best_dist = d
                best = ocr
        results.append({"dim_line": dl, "ocr": best})
    return results


# ── 시각화 ──

def visualize(img, circles_full, proj_lines, arrowheads, all_pairs,
              filtered_pairs, ocr_matched, name, gt):
    h, w = img.shape[:2]
    canvas = img.copy()

    # 동심원 (초록)
    for cx, cy, r in circles_full:
        cv2.circle(canvas, (int(cx), int(cy)), int(r), (67, 160, 71), 3)

    # 화살촉 (빨간 작은 점 — S01)
    for a in arrowheads:
        cv2.circle(canvas, (int(a["x"]), int(a["y"])), 4, (0, 0, 255), -1)

    # S01 전체 치수선 쌍 (회색 얇은선)
    for dl in all_pairs:
        cv2.line(canvas,
                 (int(dl["start"]["x"]), int(dl["start"]["y"])),
                 (int(dl["end"]["x"]), int(dl["end"]["y"])),
                 (180, 180, 180), 1)

    # 히트 있는 투사선만 (시안/노랑/보라)
    for px, py, axis, source in proj_lines:
        has_hit = False
        for dl in filtered_pairs:
            sx, sy = dl["start"]["x"], dl["start"]["y"]
            ex, ey = dl["end"]["x"], dl["end"]["y"]
            mx, my = dl["midpoint"]["x"], dl["midpoint"]["y"]
            if axis == "h" and (abs(sy - py) <= 20 or abs(ey - py) <= 20 or abs(my - py) <= 20):
                has_hit = True
                break
            if axis == "v" and (abs(sx - px) <= 20 or abs(ex - px) <= 20 or abs(mx - px) <= 20):
                has_hit = True
                break
        if not has_hit:
            continue
        if source == "protrusion":
            color = (255, 0, 200)
        elif axis == "h":
            color = (255, 100, 100)
        else:
            color = (0, 200, 255)
        if axis == "h":
            cv2.line(canvas, (0, py), (w, py), color, 2)
        else:
            cv2.line(canvas, (px, 0), (px, h), color, 2)

    # 투사선 위 치수선 쌍 (두꺼운 녹색)
    for dl in filtered_pairs:
        cv2.line(canvas,
                 (int(dl["start"]["x"]), int(dl["start"]["y"])),
                 (int(dl["end"]["x"]), int(dl["end"]["y"])),
                 (0, 255, 0), 3)

    # OCR 매칭 라벨
    for om in ocr_matched:
        if not om["ocr"]:
            continue
        dl = om["dim_line"]
        mx = int(dl["midpoint"]["x"])
        my = int(dl["midpoint"]["y"])
        val = om["ocr"]["value"]
        text = om["ocr"]["text"]
        gt_label = ""
        for label, gtv in [("OD", gt["od"]), ("ID", gt["id"]), ("W", gt["w"])]:
            if abs(val - gtv) / gtv < 0.05:
                gt_label = f" ={label}✓"
                break
        cv2.putText(canvas, f"{text}{gt_label}",
                    (mx + 10, my - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    ocr_vals = [om["ocr"]["value"] for om in ocr_matched if om["ocr"]]
    pil = add_header(
        canvas,
        f"{name.upper()} — S01 + Cardinal v3 Integration",
        f"화살촉 {len(arrowheads)}개 → 쌍 {len(all_pairs)}개 → "
        f"투사선 필터 {len(filtered_pairs)}개 → OCR {len(ocr_vals)}개",
        f"GT: OD={gt['od']} ID={gt['id']} W={gt['w']} | 검출: {ocr_vals}",
    )
    return pil


def run():
    print("S01 + Cardinal v3 통합")
    print("=" * 60)

    for doc_id, gt in GT.items():
        name = gt["name"]
        img_path = SRC_DIR / f"{doc_id}.png"
        if not img_path.exists():
            print(f"⚠ {name}: 없음")
            continue

        print(f"\n{'='*60}")
        print(f"{name.upper()} — {doc_id}")

        img = cv2.imread(str(img_path))
        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        full_h, full_w = gray.shape

        # 1. 동심원 (ROI)
        rx1, ry1 = 0, int(full_h * 0.10)
        rx2, ry2 = int(full_w * 0.55), int(full_h * 0.90)
        roi = gray[ry1:ry2, rx1:rx2]
        min_r = int(min(roi.shape) * MIN_R_RATIO)
        max_r = int(min(roi.shape) * MAX_R_RATIO)
        circles_roi = detect_concentric_alt(roi, min_r, max_r)
        circles_full = [(cx + rx1, cy + ry1, r) for cx, cy, r in circles_roi]
        print(f"  [1] 동심원: {len(circles_full)}개")

        # 2. 돌출부
        if circles_roi:
            outer_r = max(c[2] for c in circles_roi)
            peaks = radial_edge_scan(roi, circles_roi[0][0], circles_roi[0][1], outer_r)
            peaks_full = [(p[0], p[1], p[2] + rx1, p[3] + ry1) for p in peaks]
        else:
            peaks_full = []
        print(f"  [2] 돌출부: {len(peaks_full)}개")

        # 3. 투사선 생성
        proj_lines = build_projection_lines(circles_full, peaks_full)
        print(f"  [3] 투사선: {len(proj_lines)}개")

        # 4. S01 화살촉 검출 + 쌍 매칭
        arrowheads = detect_arrowheads(gray)
        all_pairs = match_arrowhead_pairs(arrowheads)
        print(f"  [4] S01 화살촉: {len(arrowheads)}개 → 쌍: {len(all_pairs)}개")

        # 5. 투사선 위 치수선 필터
        filtered = filter_pairs_on_projections(all_pairs, proj_lines)
        print(f"  [5] 투사선 위 쌍: {len(filtered)}개 / {len(all_pairs)}개")

        # 6. OCR 매칭
        print(f"  [6] OCR 호출 중...")
        ocr_dets = run_ocr(img_path)
        ocr_matched = match_ocr_to_dimlines(filtered, ocr_dets)
        matched = [om for om in ocr_matched if om["ocr"]]
        print(f"      OCR 매칭: {len(matched)}개")

        for om in matched:
            val = om["ocr"]["value"]
            text = om["ocr"]["text"]
            gt_label = ""
            for label, gtv in [("OD", gt["od"]), ("ID", gt["id"]), ("W", gt["w"])]:
                if abs(val - gtv) / gtv < 0.05:
                    gt_label = f" ← {label} ✓"
                    break
            print(f"      {text} = {val}{gt_label}")

        # 7. 시각화
        pil = visualize(img, circles_full, proj_lines, arrowheads,
                        all_pairs, filtered, ocr_matched, name, gt)
        save_pil(pil, f"{name}_s01_cardinal.jpg")

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
