#!/usr/bin/env python3
"""동심원 클러스터 PoC — 메인 뷰 크롭에서 베어링 자동 식별

1. 메인 뷰 크롭 이미지에서 원/호 검출 (컨투어+타원피팅 + HoughCircles)
2. 중심이 비슷한 원들을 그룹핑 → 동심원 클러스터
3. 가장 큰 클러스터 = 베어링 → 외곽=OD, 내곽=ID
4. 결과 시각화 캡쳐 저장
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict

INPUT_DIR = Path("/home/uproot/ax/poc/docs-site-starlight/public/images/gt-validation")
OUT_DIR = INPUT_DIR  # 같은 폴더에 저장

GT = {
    "t1": {"od": 360, "id": 190},
    "t2": {"od": 380, "id": 190},
    "t3": {"od": 380, "id": 260},
    "t4": {"od": 420, "id": 260},
    "t8": {"od": 500, "id": 260},
}


def get_font(size=16):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(path).exists():
            from PIL import ImageFont
            return ImageFont.truetype(path, size)
    from PIL import ImageFont
    return ImageFont.load_default()


def detect_all_circles(gray, min_r_ratio=0.08, max_r_ratio=0.48):
    """컨투어+타원피팅 + HoughCircles — 큰 원만 검출 (볼트홀 제외)

    베어링 정면도에서 의미있는 원 = 이미지 크기의 8%~48% 반지름.
    원형도 0.7 이상, 포인트 50개 이상으로 노이즈 제거.
    """
    h, w = gray.shape
    min_r = int(min(h, w) * min_r_ratio)
    max_r = int(min(h, w) * max_r_ratio)
    circles = []

    # --- 방법 1: 컨투어 + 타원 피팅 (높은 원형도 필터) ---
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    edges = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    min_area = np.pi * min_r * min_r * 0.5

    for cnt in contours:
        if len(cnt) < 50:
            continue
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        x, y, bw, bh = cv2.boundingRect(cnt)
        bb_aspect = min(bw, bh) / max(bw, bh) if max(bw, bh) > 0 else 0
        if bb_aspect < 0.65:
            continue

        try:
            ellipse = cv2.fitEllipse(cnt)
            (cx, cy), (ma, MA), angle = ellipse
            aspect = min(ma, MA) / max(ma, MA) if max(ma, MA) > 0 else 0
            if aspect < 0.70:
                continue
            r = (ma + MA) / 4
            if min_r <= r <= max_r:
                circles.append((float(cx), float(cy), float(r), "contour"))
        except cv2.error:
            continue

    # --- 방법 2: HoughCircles (보수적 파라미터) ---
    for param2 in [60, 100]:
        hc = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1.5,
            minDist=min_r * 2,
            param1=150, param2=param2,
            minRadius=min_r, maxRadius=max_r,
        )
        if hc is not None:
            for (cx, cy, r) in hc[0]:
                circles.append((float(cx), float(cy), float(r), "hough"))

    return circles


def deduplicate_circles(circles, dist_thresh=15, r_thresh=10):
    """중복 원 제거 — 중심+반지름이 비슷하면 하나로"""
    if not circles:
        return []
    # 반지름 큰 순으로 정렬
    circles = sorted(circles, key=lambda c: c[2], reverse=True)
    kept = []
    for cx, cy, r, method in circles:
        is_dup = False
        for kx, ky, kr, _ in kept:
            dist = np.sqrt((cx - kx) ** 2 + (cy - ky) ** 2)
            if dist < dist_thresh and abs(r - kr) < r_thresh:
                is_dup = True
                break
        if not is_dup:
            kept.append((cx, cy, r, method))
    return kept


def find_concentric_clusters(circles, center_tolerance=30):
    """중심이 비슷한 원들을 클러스터링 → 동심원 그룹

    center_tolerance: 중심 간 최대 거리 (px). 30px = 타이트.
    """
    if not circles:
        return []

    center_tol = center_tolerance

    clusters = []
    used = set()

    for i, (cx1, cy1, r1, m1) in enumerate(circles):
        if i in used:
            continue
        cluster = [(cx1, cy1, r1, m1)]
        used.add(i)
        for j, (cx2, cy2, r2, m2) in enumerate(circles):
            if j in used:
                continue
            dist = np.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2)
            if dist < center_tol:
                cluster.append((cx2, cy2, r2, m2))
                used.add(j)
        clusters.append(cluster)

    # 원 개수 내림차순 정렬
    clusters.sort(key=lambda c: len(c), reverse=True)
    return clusters


def visualize_result(img_path, circles, clusters, name, gt, out_path):
    """결과 시각화 — 원 검출 + 동심원 클러스터 + 베어링 식별"""
    img = cv2.imread(str(img_path))
    if img is None:
        return
    canvas = img.copy()
    h, w = canvas.shape[:2]

    # 모든 검출 원 — 회색 얇은선
    for cx, cy, r, method in circles:
        cv2.circle(canvas, (int(cx), int(cy)), int(r), (180, 180, 180), 1)

    # 클러스터별 색상
    colors = [
        (67, 160, 71),    # 초록 — 베어링 (1순위)
        (229, 57, 53),    # 빨강
        (30, 136, 229),   # 파랑
        (255, 179, 0),    # 주황
    ]

    bearing_cluster = None
    for ci, cluster in enumerate(clusters[:4]):
        color = colors[min(ci, len(colors) - 1)]
        center_x = np.mean([c[0] for c in cluster])
        center_y = np.mean([c[1] for c in cluster])

        for cx, cy, r, method in cluster:
            cv2.circle(canvas, (int(cx), int(cy)), int(r), color, 2)
            # 반지름 라벨
            label_x = int(cx + r * 0.7)
            label_y = int(cy - r * 0.7)
            cv2.putText(canvas, f"r={r:.0f}", (label_x, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # 중심점 표시
        cv2.drawMarker(canvas, (int(center_x), int(center_y)),
                       color, cv2.MARKER_CROSS, 20, 2)

        # 1순위 = 베어링
        if ci == 0:
            bearing_cluster = cluster
            radii = sorted([c[2] for c in cluster])
            outer_r = radii[-1]
            inner_r = radii[0] if len(radii) > 1 else None

            # 라벨
            cv2.putText(canvas, f"BEARING ({len(cluster)} circles)",
                        (int(center_x - 80), int(center_y - outer_r - 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # PIL로 정보 패널 추가
    pil_img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    font = get_font(max(14, h // 40))
    font_sm = get_font(max(11, h // 55))

    # 상단 정보 바
    info_h = 60
    draw.rectangle([0, 0, w, info_h], fill="#222222")
    draw.text((10, 5),
              f"{name.upper()} — Concentric Circle Detection",
              fill="white", font=font)

    if bearing_cluster:
        radii = sorted([c[2] for c in bearing_cluster])
        info_text = (f"Circles: {len(circles)} detected → "
                     f"{len(bearing_cluster)} concentric (bearing)  |  "
                     f"Outer r={radii[-1]:.0f}  Inner r={radii[0]:.0f}")
        draw.text((10, 30), info_text, fill="#AAAAAA", font=font_sm)

    # GT 비교 (반지름은 치수의 절반이 아님 — 픽셀 비율이므로 비율로 비교)
    if bearing_cluster and len(bearing_cluster) >= 2:
        radii = sorted([c[2] for c in bearing_cluster])
        ratio = radii[0] / radii[-1]  # inner/outer 비율
        gt_ratio = gt["id"] / gt["od"]
        draw.text((10, info_h + 5),
                  f"ID/OD ratio: detected={ratio:.3f}  GT={gt_ratio:.3f}  "
                  f"diff={abs(ratio - gt_ratio):.3f}",
                  fill="#43A047", font=font_sm)

    # 축소
    max_w = 900
    if pil_img.width > max_w:
        ratio = max_w / pil_img.width
        pil_img = pil_img.resize((max_w, int(pil_img.height * ratio)), Image.LANCZOS)

    pil_img.save(out_path, quality=85)
    print(f"  ✓ {out_path.name} ({len(circles)} circles, "
          f"{len(bearing_cluster) if bearing_cluster else 0} concentric)")


def run():
    print("동심원 클러스터 PoC")
    print("=" * 60)

    for name, gt in GT.items():
        img_path = INPUT_DIR / f"{name}_main_view.jpg"
        if not img_path.exists():
            print(f"⚠ {name}: {img_path.name} 없음")
            continue

        print(f"\n{name.upper()} (GT: OD={gt['od']} ID={gt['id']})")

        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            continue

        # 1. 원 검출
        raw_circles = detect_all_circles(gray)
        print(f"  Raw circles: {len(raw_circles)}")

        # 2. 중복 제거
        circles = deduplicate_circles(raw_circles)
        print(f"  Deduplicated: {len(circles)}")

        # 3. 동심원 클러스터링
        clusters = find_concentric_clusters(circles)
        for i, c in enumerate(clusters[:3]):
            radii = sorted([x[2] for x in c])
            print(f"  Cluster {i}: {len(c)} circles, "
                  f"r=[{radii[0]:.0f}~{radii[-1]:.0f}]")

        # 4. 시각화
        visualize_result(
            img_path, circles, clusters, name, gt,
            OUT_DIR / f"{name}_concentric.jpg",
        )

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
