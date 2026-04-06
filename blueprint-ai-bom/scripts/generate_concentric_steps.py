#!/usr/bin/env python3
"""동심원 클러스터 스텝별 시각화 — T1 도면 기준

방안 A (현행): 시각화만 개선 — 검출 파라미터 그대로, 신뢰도별 색 구분
방안 B (ALT): HOUGH_GRADIENT_ALT로 같은 중심의 동심원을 직접 검출
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

INPUT_DIR = Path(__file__).resolve().parents[2] / "docs-site-starlight" / "public" / "images" / "gt-validation"
OUT_DIR = INPUT_DIR / "steps"
OUT_DIR.mkdir(exist_ok=True)

GT = {"od": 360, "id": 190}
MIN_R_RATIO = 0.08
MAX_R_RATIO = 0.48


def get_font(size=16):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def add_header(img_bgr, title, subtitle="", subtitle2=""):
    """상단 정보 바 추가"""
    pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    h, w = img_bgr.shape[:2]
    font = get_font(max(14, h // 40))
    font_sm = get_font(max(11, h // 55))

    bar_h = 70 if subtitle2 else 55
    draw.rectangle([0, 0, w, bar_h], fill="#222222")
    draw.text((10, 5), title, fill="white", font=font)
    if subtitle:
        draw.text((10, 28), subtitle, fill="#AAAAAA", font=font_sm)
    if subtitle2:
        draw.text((10, 48), subtitle2, fill="#66BB6A", font=font_sm)
    return pil


def save_pil(pil_img, name, max_w=900):
    if pil_img.width > max_w:
        ratio = max_w / pil_img.width
        pil_img = pil_img.resize(
            (max_w, int(pil_img.height * ratio)), Image.LANCZOS
        )
    out = OUT_DIR / name
    pil_img.save(out, quality=85)
    print(f"  ✓ {name}")
    return out


def detect_contour_circles(gray, min_r, max_r):
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    edges = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=1)
    contours, _ = cv2.findContours(
        dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    min_area = np.pi * min_r * min_r * 0.5
    circles = []
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
    return circles, edges, dilated


def detect_hough_original(gray, min_r, max_r):
    """현행 — param2=[60, 100] 두 번"""
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    circles_by_conf = {"high": [], "low": []}
    # param2=100 먼저 (높은 신뢰도)
    hc = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.5,
        minDist=min_r * 2,
        param1=150, param2=100,
        minRadius=min_r, maxRadius=max_r,
    )
    if hc is not None:
        for (cx, cy, r) in hc[0]:
            circles_by_conf["high"].append(
                (float(cx), float(cy), float(r), "hough_high")
            )
    # param2=60 (낮은 신뢰도)
    hc = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.5,
        minDist=min_r * 2,
        param1=150, param2=60,
        minRadius=min_r, maxRadius=max_r,
    )
    if hc is not None:
        for (cx, cy, r) in hc[0]:
            circles_by_conf["low"].append(
                (float(cx), float(cy), float(r), "hough_low")
            )
    return circles_by_conf


def detect_hough_tuned(gray, min_r, max_r):
    """튜닝 — HOUGH_GRADIENT_ALT (3D 누적기: 동심원 검출 가능)

    HOUGH_GRADIENT: 2D 누적기(x,y) → 중심당 1원만 검출 (동심원 불가)
    HOUGH_GRADIENT_ALT: 3D 누적기(x,y,r) → 같은 중심에서 반지름별 검출
    """
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    circles = []
    hc = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT_ALT, dp=1.5,
        minDist=20,  # 동심원은 중심이 같으므로 작게
        param1=150, param2=0.85,  # ALT: 0~1 범위, 높을수록 엄격
        minRadius=min_r, maxRadius=max_r,
    )
    if hc is not None:
        for (cx, cy, r) in hc[0]:
            circles.append((float(cx), float(cy), float(r), "hough"))
    return circles


def deduplicate(circles, dist_thresh=15, r_thresh=10):
    if not circles:
        return []
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


def find_clusters(circles, center_tol=30):
    if not circles:
        return []
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
    clusters.sort(key=lambda c: len(c), reverse=True)
    return clusters


def draw_cluster_result(img, deduped, clusters, prefix, subtitle_extra=""):
    """Step 5 공통 — 클러스터링 결과 시각화"""
    canvas = img.copy()
    for cx, cy, r, _ in deduped:
        cv2.circle(canvas, (int(cx), int(cy)), int(r), (180, 180, 180), 1)

    cluster_colors = [
        (67, 160, 71),   # 초록
        (229, 57, 53),   # 빨강
        (30, 136, 229),  # 파랑
        (255, 179, 0),   # 주황
    ]
    cluster_labels = ["BEARING", "Cluster 2", "Cluster 3", "Cluster 4"]

    info_parts = []
    for ci, cluster in enumerate(clusters[:4]):
        color = cluster_colors[min(ci, len(cluster_colors) - 1)]
        center_x = np.mean([c[0] for c in cluster])
        center_y = np.mean([c[1] for c in cluster])

        for cx, cy, r, _ in cluster:
            cv2.circle(canvas, (int(cx), int(cy)), int(r), color, 2)
            lx = int(cx + r * 0.7)
            ly = int(cy - r * 0.7)
            cv2.putText(canvas, f"r={r:.0f}", (lx, ly),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

        cv2.drawMarker(canvas, (int(center_x), int(center_y)),
                       color, cv2.MARKER_CROSS, 20, 2)
        label = cluster_labels[ci] if ci < len(cluster_labels) else f"C{ci}"
        cv2.putText(canvas, f"{label} ({len(cluster)})",
                    (int(center_x - 60),
                     int(center_y - max(c[2] for c in cluster) - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        radii = sorted([c[2] for c in cluster])
        info_parts.append(
            f"{label}:{len(cluster)}원(r={radii[0]:.0f}~{radii[-1]:.0f})"
        )

    ratio_text = ""
    if clusters and len(clusters[0]) >= 2:
        radii = sorted([c[2] for c in clusters[0]])
        ratio = radii[0] / radii[-1]
        gt_ratio = GT["id"] / GT["od"]
        ratio_text = f" | ID/OD: {ratio:.3f} (GT={gt_ratio:.3f})"

    pil = add_header(
        canvas,
        f"{prefix} — Concentric Clustering",
        f"{' | '.join(info_parts)}{ratio_text}",
        subtitle_extra,
    )
    return pil


def run():
    img_path = INPUT_DIR / "t1_main_view.jpg"
    print("T1 동심원 — 방안 A (시각화 개선) vs 방안 B (HOUGH_GRADIENT_ALT)")
    print("=" * 60)

    img = cv2.imread(str(img_path))
    gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    h, w = gray.shape
    min_r = int(min(h, w) * MIN_R_RATIO)
    max_r = int(min(h, w) * MAX_R_RATIO)

    # ── 공통: Step 1 + 2 (변경 없음) ──
    contour_circles, edges, dilated = detect_contour_circles(gray, min_r, max_r)

    edges_bgr = cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR)
    pil = add_header(
        edges_bgr,
        "Step 1 — Canny Edge Detection",
        f"GaussianBlur(5,5) → Canny(50,150) → Dilate | "
        f"r 범위: {min_r}~{max_r}px",
    )
    save_pil(pil, "step1_edge.jpg")

    canvas2 = img.copy()
    for cx, cy, r, _ in contour_circles:
        cv2.circle(canvas2, (int(cx), int(cy)), int(r), (255, 140, 0), 2)
        cv2.circle(canvas2, (int(cx), int(cy)), 3, (255, 140, 0), -1)
    pil = add_header(
        canvas2,
        "Step 2 — Contour + Ellipse Fitting",
        f"컨투어 → fitEllipse → 원형도≥0.70 | "
        f"검출: {len(contour_circles)}개",
    )
    save_pil(pil, "step2_contour.jpg")

    # ================================================================
    # 방안 A: 시각화 개선 — 검출은 동일, 신뢰도별 색상 구분
    # ================================================================
    print("\n── 방안 A: 시각화 개선 ──")
    hough_by_conf = detect_hough_original(gray, min_r, max_r)
    n_high = len(hough_by_conf["high"])
    n_low = len(hough_by_conf["low"])

    # Step 3A: 신뢰도별 색상 — 빨강=high, 주황반투명=low
    canvas3a = img.copy()
    # low 먼저 (뒤에 깔림)
    for cx, cy, r, _ in hough_by_conf["low"]:
        cv2.circle(canvas3a, (int(cx), int(cy)), int(r), (140, 160, 200), 1)
    # high 위에
    for cx, cy, r, _ in hough_by_conf["high"]:
        cv2.circle(canvas3a, (int(cx), int(cy)), int(r), (0, 0, 230), 2)
        cv2.circle(canvas3a, (int(cx), int(cy)), 3, (0, 0, 230), -1)

    pil = add_header(
        canvas3a,
        "Step 3A — HoughCircles (신뢰도별 색상)",
        f"param2=100: {n_high}개 (빨강, 굵은선) | "
        f"param2=60: {n_low}개 (연한선, 노이즈 포함)",
        "→ 현행 파라미터 유지, 시각적으로 신뢰도 구분",
    )
    save_pil(pil, "step3a_hough_viz.jpg")

    # Step 4A: 중복 제거
    all_a = contour_circles + hough_by_conf["high"] + hough_by_conf["low"]
    deduped_a = deduplicate(all_a)

    canvas4a = img.copy()
    for cx, cy, r, method in deduped_a:
        if method == "contour":
            color, thick = (255, 140, 0), 2
        elif method == "hough_high":
            color, thick = (0, 0, 230), 2
        else:
            color, thick = (140, 160, 200), 1
        cv2.circle(canvas4a, (int(cx), int(cy)), int(r), color, thick)
    n_c = sum(1 for c in deduped_a if c[3] == "contour")
    n_hh = sum(1 for c in deduped_a if c[3] == "hough_high")
    n_hl = sum(1 for c in deduped_a if c[3] == "hough_low")
    pil = add_header(
        canvas4a,
        f"Step 4A — Dedup: {len(all_a)}→{len(deduped_a)}개",
        f"파랑=Contour({n_c}) 빨강=Hough-high({n_hh}) 연한=Hough-low({n_hl})",
    )
    save_pil(pil, "step4a_dedup_viz.jpg")

    # Step 5A: 클러스터링
    clusters_a = find_clusters(deduped_a)
    pil = draw_cluster_result(
        img, deduped_a, clusters_a, "Step 5A",
        f"방안 A: 현행 검출 유지 | 전체 {len(deduped_a)}개 → "
        f"클러스터 {len(clusters_a)}개",
    )
    save_pil(pil, "step5a_cluster_viz.jpg")

    # ================================================================
    # 방안 B: HOUGH_GRADIENT_ALT — 같은 중심의 동심원 직접 검출
    # ================================================================
    print("\n── 방안 B: HOUGH_GRADIENT_ALT ──")
    hough_tuned = detect_hough_tuned(gray, min_r, max_r)

    # Step 3B
    canvas3b = img.copy()
    for cx, cy, r, _ in hough_tuned:
        cv2.circle(canvas3b, (int(cx), int(cy)), int(r), (0, 0, 230), 2)
        cv2.circle(canvas3b, (int(cx), int(cy)), 3, (0, 0, 230), -1)
        lx = int(cx + r * 0.7)
        ly = int(cy - r * 0.7)
        cv2.putText(canvas3b, f"r={r:.0f}", (lx, ly),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 230), 1)
    pil = add_header(
        canvas3b,
        f"Step 3B — HoughCircles ALT ({len(hough_tuned)}개)",
        "HOUGH_GRADIENT_ALT | dp=1.5, param2=0.85, minDist=20px",
        f"기존 {n_high + n_low}개 → {len(hough_tuned)}개 | "
        "3D 누적기로 동심원 직접 검출",
    )
    save_pil(pil, "step3b_hough_tuned.jpg")

    # Step 4B: 중복 제거
    all_b = contour_circles + hough_tuned
    deduped_b = deduplicate(all_b)

    canvas4b = img.copy()
    for cx, cy, r, method in deduped_b:
        color = (255, 140, 0) if method == "contour" else (0, 0, 230)
        cv2.circle(canvas4b, (int(cx), int(cy)), int(r), color, 2)
        cv2.circle(canvas4b, (int(cx), int(cy)), 3, color, -1)
        lx = int(cx + r * 0.7)
        ly = int(cy - r * 0.7)
        cv2.putText(canvas4b, f"r={r:.0f}", (lx, ly),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)
    n_c2 = sum(1 for c in deduped_b if c[3] == "contour")
    n_h2 = sum(1 for c in deduped_b if c[3] == "hough")
    pil = add_header(
        canvas4b,
        f"Step 4B — Dedup: {len(all_b)}→{len(deduped_b)}개",
        f"파랑=Contour({n_c2}) 빨강=Hough({n_h2})",
    )
    save_pil(pil, "step4b_dedup_tuned.jpg")

    # Step 5B: 클러스터링
    clusters_b = find_clusters(deduped_b)
    pil = draw_cluster_result(
        img, deduped_b, clusters_b, "Step 5B",
        f"방안 B: HOUGH_GRADIENT_ALT | 전체 {len(deduped_b)}개 → "
        f"클러스터 {len(clusters_b)}개",
    )
    save_pil(pil, "step5b_cluster_tuned.jpg")

    # ================================================================
    # 비교 요약
    # ================================================================
    print("\n" + "=" * 60)
    print("비교 요약")
    print(f"  방안 A (현행): Hough {n_high + n_low}개 → "
          f"Dedup {len(deduped_a)}개 → 클러스터 {len(clusters_a)}개")
    if clusters_a:
        ra = sorted([c[2] for c in clusters_a[0]])
        print(f"    베어링: {len(clusters_a[0])}원, "
              f"r={ra[0]:.0f}~{ra[-1]:.0f}")
    print(f"  방안 B (ALT): Hough {len(hough_tuned)}개 → "
          f"Dedup {len(deduped_b)}개 → 클러스터 {len(clusters_b)}개")
    if clusters_b:
        rb = sorted([c[2] for c in clusters_b[0]])
        print(f"    베어링: {len(clusters_b[0])}원, "
              f"r={rb[0]:.0f}~{rb[-1]:.0f}")

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
