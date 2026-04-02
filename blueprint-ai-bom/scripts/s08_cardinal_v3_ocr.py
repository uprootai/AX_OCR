#!/usr/bin/env python3
"""S08 Cardinal v3 — 전체 파이프라인: 동심원 → 투사선 → 화살촉 → 선분 추적 → OCR

1. 전체 도면에서 ALT 동심원 검출
2. 끝점 투사선 위 화살촉 히트
3. Line Detector로 화살촉과 연결된 선분 찾기
4. 선분 반대쪽 끝의 화살촉 = 치수선 쌍
5. 치수선 중점 근처 OCR → OD/ID/W 추출
"""

import cv2
import io
import numpy as np
import requests
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SRC_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs")
OUT_DIR = Path("/home/uproot/ax/poc/docs-site-starlight/public/images/gt-validation/steps")
OUT_DIR.mkdir(exist_ok=True)

LINE_API = "http://localhost:5016/api/v1/process"
OCR_API = "http://localhost:5006/api/v1/ocr"

GT = {
    "TD0062015": {"name": "t1", "od": 360, "id": 190, "w": 200},
    "TD0062021": {"name": "t2", "od": 380, "id": 190, "w": 200},
}

MIN_R_RATIO = 0.08
MAX_R_RATIO = 0.48
ARROW_TOLERANCE = 15     # 투사선-화살촉 거리
LINE_ARROW_DIST = 40     # 선분 끝점-화살촉 거리


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


# ── Step 1: 동심원 검출 ──

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


# ── Step 2: 화살촉 검출 ──

def detect_arrowheads(gray, min_area=50, max_area=1500):
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    arrows = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area < 1:
            continue
        if area / hull_area < 0.4:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = min(bw, bh) / max(bw, bh) if max(bw, bh) > 0 else 0
        if aspect < 0.2 or (bw > 80 and bh > 80):
            continue
        M = cv2.moments(cnt)
        if M["m00"] > 0:
            arrows.append({
                "x": float(M["m10"] / M["m00"]),
                "y": float(M["m01"] / M["m00"]),
            })
    return arrows


# ── Step 3: 투사선 → 화살촉 히트 ──

def find_projection_hits(circles, arrows, gray, cx_offset=0, cy_offset=0, tolerance=15):
    """각 원의 끝점에서 투사선 → 화살촉 히트 (전체 도면 좌표)

    끝점당 가장 가까운 화살촉 1개만 유지 (중복 제거).
    """
    h, w = gray.shape
    hits = []

    for ci, (cx_roi, cy_roi, r) in enumerate(circles):
        cx = cx_roi + cx_offset
        cy = cy_roi + cy_offset

        for dir_name, dx, dy, axis in [
            ("N", 0, -1, "h"), ("S", 0, 1, "h"),
            ("E", 1, 0, "v"), ("W", -1, 0, "v"),
        ]:
            px = cx + r * dx
            py = cy + r * dy

            candidates = []
            for arrow in arrows:
                ax, ay = arrow["x"], arrow["y"]
                on_line = False
                if axis == "h" and abs(ay - py) <= tolerance:
                    on_line = True
                elif axis == "v" and abs(ax - px) <= tolerance:
                    on_line = True

                if not on_line:
                    continue
                dist_c = np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2)
                if dist_c < r * 0.9:
                    continue
                dist = np.sqrt((ax - px) ** 2 + (ay - py) ** 2)
                candidates.append({
                    "circle_idx": ci, "r": r,
                    "direction": dir_name, "axis": axis,
                    "endpoint": (px, py),
                    "arrow": arrow, "dist": dist,
                })

            # 가장 가까운 1개만
            if candidates:
                best = min(candidates, key=lambda c: c["dist"])
                hits.append(best)

    return hits


# ── Step 4: Line Detector → 화살촉 쌍 찾기 ──

def detect_lines_api(image_path):
    """Line Detector API 호출"""
    with open(image_path, 'rb') as f:
        resp = requests.post(LINE_API, files={
            'file': (image_path.name, f, 'image/png')
        }, data={
            'method': 'lsd',
            'min_length': 20,
            'max_lines': 2000,
            'merge_lines': 'true',
            'classify_types': 'false',
            'find_intersections_flag': 'false',
            'visualize': 'false',
        }, timeout=120)
        resp.raise_for_status()
    data = resp.json().get("data", {})
    return data.get("lines", [])


def find_arrow_pairs(hits, lines, all_arrows, max_line_dist=40):
    """화살촉 히트에서 선분을 추적하여 쌍 찾기 (중복 제거)

    hit의 화살촉 A → A 근처에서 시작/끝나는 선분 찾기
    → 선분 반대쪽 끝 근처의 화살촉 B = 쌍
    → 같은 A-B 좌표 쌍은 1번만 기록
    """
    pairs = []
    seen_pairs = set()  # (ax, ay, bx, by) 중복 방지

    for hi, hit in enumerate(hits):
        ax, ay = hit["arrow"]["x"], hit["arrow"]["y"]
        found = False

        for line in lines:
            if found:
                break
            sp = line["start_point"]
            ep = line["end_point"]

            d_start = np.sqrt((sp[0] - ax) ** 2 + (sp[1] - ay) ** 2)
            d_end = np.sqrt((ep[0] - ax) ** 2 + (ep[1] - ay) ** 2)

            if d_start > max_line_dist and d_end > max_line_dist:
                continue

            other_end = ep if d_start <= max_line_dist else sp

            for arrow_b in all_arrows:
                bx, by = arrow_b["x"], arrow_b["y"]
                if abs(bx - ax) < 5 and abs(by - ay) < 5:
                    continue
                d_other = np.sqrt(
                    (other_end[0] - bx) ** 2 + (other_end[1] - by) ** 2)
                if d_other <= max_line_dist:
                    # 중복 체크
                    key = (round(ax), round(ay), round(bx), round(by))
                    key_rev = (round(bx), round(by), round(ax), round(ay))
                    if key in seen_pairs or key_rev in seen_pairs:
                        continue
                    seen_pairs.add(key)

                    pairs.append({
                        "hit_idx": hi,
                        "hit": hit,
                        "arrow_a": hit["arrow"],
                        "arrow_b": arrow_b,
                        "line": line,
                        "length": line["length"],
                        "midpoint": (
                            (ax + bx) / 2,
                            (ay + by) / 2,
                        ),
                    })
                    found = True
                    break

    return pairs


# ── Step 5: OCR → 치수값 추출 ──

def run_ocr(image_path):
    """PaddleOCR API 호출"""
    with open(image_path, 'rb') as f:
        resp = requests.post(OCR_API, files={
            'file': (image_path.name, f, 'image/jpeg')
        }, timeout=120)
        resp.raise_for_status()
    return resp.json().get("detections", [])


def match_ocr_to_pairs(pairs, ocr_dets, search_radius=150):
    """치수선 쌍의 중점 근처 OCR 텍스트 매칭"""
    # OCR에서 숫자 추출
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
                        "cx": sum(xs) / len(xs),
                        "cy": sum(ys) / len(ys),
                        "has_phi": bool(re.search(r"[Øø]", text)),
                    })
                except (TypeError, IndexError):
                    pass

    results = []
    for pair in pairs:
        mx, my = pair["midpoint"]
        best = None
        best_dist = float("inf")

        for ocr in ocr_nums:
            d = np.sqrt((ocr["cx"] - mx) ** 2 + (ocr["cy"] - my) ** 2)
            if d < search_radius and d < best_dist:
                best_dist = d
                best = ocr

        results.append({
            **pair,
            "ocr": best,
            "ocr_dist": best_dist if best else None,
        })

    return results


# ── 시각화 ──

def visualize_full_pipeline(img, circles_full, hits, pairs_with_ocr, name, gt):
    h, w = img.shape[:2]
    canvas = img.copy()

    # 동심원 (초록)
    for cx, cy, r in circles_full:
        cv2.circle(canvas, (int(cx), int(cy)), int(r), (67, 160, 71), 3)

    # 투사선 (얇은 선)
    dir_colors = {"N": (255, 100, 100), "S": (255, 100, 100),
                  "E": (0, 200, 255), "W": (0, 200, 255)}

    drawn_lines = set()
    for hit in hits:
        px, py = int(hit["endpoint"][0]), int(hit["endpoint"][1])
        color = dir_colors.get(hit["direction"], (200, 200, 200))
        key = (px, py, hit["axis"])
        if key not in drawn_lines:
            drawn_lines.add(key)
            if hit["axis"] == "h":
                cv2.line(canvas, (0, py), (w, py), color, 1)
            else:
                cv2.line(canvas, (px, 0), (px, h), color, 1)

    # 치수선 쌍 + OCR (굵은 녹색)
    for pr in pairs_with_ocr:
        a = pr["arrow_a"]
        b = pr["arrow_b"]
        # 치수선 (두꺼운 녹색)
        cv2.line(canvas, (int(a["x"]), int(a["y"])),
                 (int(b["x"]), int(b["y"])), (0, 255, 0), 3)
        # 화살촉 마커
        cv2.drawMarker(canvas, (int(a["x"]), int(a["y"])),
                       (0, 0, 255), cv2.MARKER_TILTED_CROSS, 15, 2)
        cv2.drawMarker(canvas, (int(b["x"]), int(b["y"])),
                       (0, 0, 255), cv2.MARKER_TILTED_CROSS, 15, 2)

        # OCR 값 표시
        if pr["ocr"]:
            mx, my = int(pr["midpoint"][0]), int(pr["midpoint"][1])
            text = pr["ocr"]["text"]
            val = pr["ocr"]["value"]
            # GT 매칭 체크
            gt_match = ""
            for label, gtv in [("OD", gt["od"]), ("ID", gt["id"]), ("W", gt["w"])]:
                if abs(val - gtv) / gtv < 0.05:
                    gt_match = f" ={label}"
                    break
            cv2.putText(canvas, f"{text}{gt_match}",
                        (mx + 10, my - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # 요약 텍스트
    ocr_values = [pr["ocr"]["value"] for pr in pairs_with_ocr if pr["ocr"]]
    pil = add_header(
        canvas,
        f"{name.upper()} — Cardinal v3 Full Pipeline",
        f"동심원 {len(circles_full)}개 | 히트 {len(hits)}개 | "
        f"치수선 쌍 {len(pairs_with_ocr)}개 | OCR 매칭 {len(ocr_values)}개",
        f"GT: OD={gt['od']} ID={gt['id']} W={gt['w']} | "
        f"검출값: {ocr_values}",
    )
    return pil


def run():
    print("S08 Cardinal v3 — Full Pipeline (동심원→투사→선분→OCR)")
    print("=" * 60)

    for doc_id, gt in GT.items():
        name = gt["name"]
        img_path = SRC_DIR / f"{doc_id}.png"
        if not img_path.exists():
            print(f"⚠ {name}: 없음")
            continue

        print(f"\n{'='*60}")
        print(f"{name.upper()} — {doc_id} (GT: OD={gt['od']} ID={gt['id']} W={gt['w']})")

        img = cv2.imread(str(img_path))
        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        full_h, full_w = gray.shape
        print(f"  전체 도면: {full_w}x{full_h}")

        # 1. 메인 뷰 ROI → 동심원
        rx1, ry1 = 0, int(full_h * 0.10)
        rx2, ry2 = int(full_w * 0.55), int(full_h * 0.90)
        roi = gray[ry1:ry2, rx1:rx2]
        min_r = int(min(roi.shape) * MIN_R_RATIO)
        max_r = int(min(roi.shape) * MAX_R_RATIO)

        circles_roi = detect_concentric_alt(roi, min_r, max_r)
        circles_full = [(cx + rx1, cy + ry1, r) for cx, cy, r in circles_roi]
        print(f"  [1] 동심원: {len(circles_full)}개")
        for cx, cy, r in circles_full:
            print(f"      ({cx:.0f},{cy:.0f}) r={r:.0f}")

        # 2. 전체 도면 화살촉
        arrows = detect_arrowheads(gray)
        print(f"  [2] 화살촉: {len(arrows)}개")

        # 3. 투사선 → 히트
        hits = find_projection_hits(
            circles_roi, arrows, gray,
            cx_offset=rx1, cy_offset=ry1,
        )
        print(f"  [3] 투사선 히트: {len(hits)}개")

        # 4. Line Detector → 선분 → 화살촉 쌍
        print(f"  [4] Line Detector 호출 중...")
        lines = detect_lines_api(img_path)
        print(f"      선분: {len(lines)}개")

        pairs = find_arrow_pairs(hits, lines, arrows)
        print(f"      치수선 쌍: {len(pairs)}개")
        for p in pairs[:10]:
            a, b = p["arrow_a"], p["arrow_b"]
            print(f"      ({a['x']:.0f},{a['y']:.0f})-"
                  f"({b['x']:.0f},{b['y']:.0f}) len={p['length']:.0f}")

        # 5. OCR → 치수값
        print(f"  [5] OCR 호출 중...")
        ocr_dets = run_ocr(img_path)
        print(f"      OCR 텍스트: {len(ocr_dets)}개")

        pairs_with_ocr = match_ocr_to_pairs(pairs, ocr_dets)
        matched = [p for p in pairs_with_ocr if p["ocr"]]
        print(f"      OCR 매칭: {len(matched)}개")

        for p in matched:
            val = p["ocr"]["value"]
            text = p["ocr"]["text"]
            gt_match = ""
            for label, gtv in [("OD", gt["od"]), ("ID", gt["id"]), ("W", gt["w"])]:
                if abs(val - gtv) / gtv < 0.05:
                    gt_match = f" ← {label} ✓"
                    break
            print(f"      {text} = {val}{gt_match}")

        # 6. 시각화
        pil = visualize_full_pipeline(
            img, circles_full, hits, pairs_with_ocr, name, gt)
        save_pil(pil, f"{name}_cardinal_v3_pipeline.jpg")

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
