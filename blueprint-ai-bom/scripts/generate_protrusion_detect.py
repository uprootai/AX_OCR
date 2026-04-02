#!/usr/bin/env python3
"""돌출부 검출 — 동심원 중심에서 방사 스캔으로 원 바깥 돌출 영역 식별

1. ALT 동심원 중심 + 외원 반지름 확보
2. 중심에서 360도 방사 방향으로 엣지 스캔
3. 외원 반지름보다 먼 엣지 = 돌출부
4. 돌출부 끝점(가장 먼 엣지)을 시각화
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

INPUT_DIR = Path("/home/uproot/ax/poc/docs-site-starlight/public/images/gt-validation")
OUT_DIR = INPUT_DIR / "steps"
OUT_DIR.mkdir(exist_ok=True)

GT = {
    "t1": {"od": 360, "id": 190},
    "t2": {"od": 380, "id": 190},
    "t4": {"od": 420, "id": 260},
    "t8": {"od": 500, "id": 260},
}

MIN_R_RATIO = 0.08
MAX_R_RATIO = 0.48


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
    font = get_font(max(14, h // 40))
    font_sm = get_font(max(11, h // 55))
    bar_h = 70 if sub2 else 55
    draw.rectangle([0, 0, w, bar_h], fill="#222222")
    draw.text((10, 5), title, fill="white", font=font)
    if sub1:
        draw.text((10, 28), sub1, fill="#AAAAAA", font=font_sm)
    if sub2:
        draw.text((10, 48), sub2, fill="#66BB6A", font=font_sm)
    return pil


def save_pil(pil_img, name, max_w=900):
    if pil_img.width > max_w:
        r = max_w / pil_img.width
        pil_img = pil_img.resize((max_w, int(pil_img.height * r)), Image.LANCZOS)
    out = OUT_DIR / name
    pil_img.save(out, quality=85)
    print(f"  ✓ {name}")


def detect_concentric_alt(gray, min_r, max_r):
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
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


def radial_edge_scan(gray, cx, cy, outer_r, n_angles=360, max_scan_r=None):
    """중심에서 방사 방향으로 엣지 스캔

    Returns:
        radial_profile: [(angle_deg, max_edge_r, edge_x, edge_y), ...]
        protrusions: radial_profile 중 outer_r보다 먼 것들
    """
    h, w = gray.shape
    if max_scan_r is None:
        max_scan_r = int(outer_r * 1.5)

    # 엣지 맵
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    edges = cv2.Canny(blurred, 50, 150)

    radial_profile = []

    for i in range(n_angles):
        angle_deg = i * 360.0 / n_angles
        angle_rad = np.radians(angle_deg)
        dx = np.cos(angle_rad)
        dy = np.sin(angle_rad)

        # 외원 반지름 ~ max_scan_r 범위에서 엣지 스캔
        max_edge_r = 0
        max_edge_x, max_edge_y = cx, cy

        for r_px in range(int(outer_r * 0.8), max_scan_r):
            px = int(cx + r_px * dx)
            py = int(cy + r_px * dy)
            if 0 <= px < w and 0 <= py < h:
                if edges[py, px] > 0:
                    max_edge_r = r_px
                    max_edge_x = px
                    max_edge_y = py

        radial_profile.append((angle_deg, max_edge_r, max_edge_x, max_edge_y))

    # 돌출부 = outer_r보다 10% 이상 먼 엣지
    threshold = outer_r * 1.05
    protrusions = [p for p in radial_profile if p[1] > threshold]

    return radial_profile, protrusions


def cluster_protrusions(protrusions, angle_gap=10):
    """인접한 각도의 돌출부를 그룹핑 → 각 그룹의 최대점 = 돌출 끝점"""
    if not protrusions:
        return []

    # 각도순 정렬
    sorted_p = sorted(protrusions, key=lambda p: p[0])

    groups = []
    current_group = [sorted_p[0]]

    for i in range(1, len(sorted_p)):
        if sorted_p[i][0] - sorted_p[i - 1][0] <= angle_gap:
            current_group.append(sorted_p[i])
        else:
            groups.append(current_group)
            current_group = [sorted_p[i]]
    groups.append(current_group)

    # 각 그룹에서 가장 먼 점 = 돌출 끝점
    peaks = []
    for g in groups:
        peak = max(g, key=lambda p: p[1])
        peaks.append({
            "angle": peak[0],
            "r": peak[1],
            "x": peak[2],
            "y": peak[3],
            "span": len(g),  # 각도 범위
        })

    return peaks


def visualize(img, circles, radial_profile, protrusion_peaks, outer_r, name, gt):
    h, w = img.shape[:2]
    canvas = img.copy()

    if not circles:
        return canvas

    cx, cy = circles[0][0], circles[0][1]

    # 동심원 (초록)
    for ccx, ccy, r in circles:
        cv2.circle(canvas, (int(ccx), int(ccy)), int(r), (67, 160, 71), 2)

    # 방사 프로파일 (연한 시안 — 외원 이내)
    for angle_deg, edge_r, ex, ey in radial_profile:
        if edge_r > 0 and edge_r <= outer_r * 1.05:
            cv2.circle(canvas, (ex, ey), 1, (200, 200, 100), -1)

    # 돌출부 영역 (주황)
    for angle_deg, edge_r, ex, ey in radial_profile:
        if edge_r > outer_r * 1.05:
            cv2.circle(canvas, (ex, ey), 2, (0, 140, 255), -1)

    # 돌출 끝점 (빨간 큰 마커 + 라벨)
    for peak in protrusion_peaks:
        px, py = peak["x"], peak["y"]
        cv2.drawMarker(canvas, (px, py),
                       (0, 0, 255), cv2.MARKER_DIAMOND, 15, 3)
        # 중심 → 끝점 연결선
        cv2.line(canvas, (int(cx), int(cy)), (px, py), (0, 0, 255), 1)
        # 라벨
        cv2.putText(canvas, f"{peak['angle']:.0f}° r={peak['r']}",
                    (px + 8, py - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

    # 외원 반지름 원 (점선 효과 — 기준선)
    cv2.circle(canvas, (int(cx), int(cy)), int(outer_r),
               (100, 100, 255), 1)

    pil = add_header(
        canvas,
        f"{name.upper()} — Protrusion Detection (Radial Scan)",
        f"동심원 {len(circles)}개 | 외원 r={outer_r:.0f} | "
        f"돌출 끝점: {len(protrusion_peaks)}개",
        f"GT: OD={gt['od']} ID={gt['id']}",
    )
    return pil


def run():
    print("돌출부 검출 — Radial Edge Scan")
    print("=" * 60)

    for name, gt in GT.items():
        img_path = INPUT_DIR / f"{name}_main_view.jpg"
        if not img_path.exists():
            print(f"⚠ {name}: 없음")
            continue

        print(f"\n{name.upper()} (GT: OD={gt['od']} ID={gt['id']})")

        img = cv2.imread(str(img_path))
        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        h, w = gray.shape
        min_r = int(min(h, w) * MIN_R_RATIO)
        max_r = int(min(h, w) * MAX_R_RATIO)

        # 동심원
        circles = detect_concentric_alt(gray, min_r, max_r)
        if not circles:
            print("  동심원 미검출")
            continue

        # 외원 = 가장 큰 반지름
        outer_r = max(c[2] for c in circles)
        cx, cy = circles[0][0], circles[0][1]
        print(f"  동심원: {len(circles)}개, 외원 r={outer_r:.0f}")
        print(f"  중심: ({cx:.0f}, {cy:.0f})")

        # 방사 스캔
        profile, protrusions = radial_edge_scan(gray, cx, cy, outer_r)
        print(f"  방사 스캔: {len(profile)}방향, 돌출 {len(protrusions)}개")

        # 돌출부 클러스터링 → 끝점
        peaks = cluster_protrusions(protrusions)
        print(f"  돌출 끝점: {len(peaks)}개")
        for p in peaks:
            print(f"    {p['angle']:.0f}° r={p['r']} ({p['x']},{p['y']}) span={p['span']}°")

        # 시각화
        pil = visualize(img, circles, profile, peaks, outer_r, name, gt)
        save_pil(pil, f"{name}_protrusion.jpg")

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
