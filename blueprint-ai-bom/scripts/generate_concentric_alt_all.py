#!/usr/bin/env python3
"""HOUGH_GRADIENT_ALT 전체 도면 검증 — T1~T8 동심원 검출 + 최종 결과 이미지

T1 스텝별(step1~5)은 기존 스크립트가 생성.
이 스크립트는 전 도면에 ALT를 적용하고 최종 클러스터링 결과만 생성.
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
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def add_header(img_bgr, title, subtitle="", subtitle2=""):
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
    return circles


def detect_hough_alt(gray, min_r, max_r):
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    circles = []
    hc = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT_ALT, dp=1.5,
        minDist=20,
        param1=150, param2=0.85,
        minRadius=min_r, maxRadius=max_r,
    )
    if hc is not None:
        for (cx, cy, r) in hc[0]:
            circles.append((float(cx), float(cy), float(r), "hough"))
    return circles


def detect_hough_original(gray, min_r, max_r):
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    circles = []
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


def draw_final(img, deduped, clusters, name, gt):
    """최종 클러스터링 결과 시각화"""
    canvas = img.copy()
    for cx, cy, r, _ in deduped:
        cv2.circle(canvas, (int(cx), int(cy)), int(r), (180, 180, 180), 1)

    cluster_colors = [
        (67, 160, 71), (229, 57, 53), (30, 136, 229), (255, 179, 0),
    ]
    labels = ["BEARING", "Cluster 2", "Cluster 3", "Cluster 4"]

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
        label = labels[ci] if ci < len(labels) else f"C{ci}"
        cv2.putText(canvas, f"{label} ({len(cluster)})",
                    (int(center_x - 60),
                     int(center_y - max(c[2] for c in cluster) - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        radii = sorted([c[2] for c in cluster])
        info_parts.append(
            f"{label}:{len(cluster)}(r={radii[0]:.0f}~{radii[-1]:.0f})"
        )

    ratio_text = ""
    if clusters and len(clusters[0]) >= 2:
        radii = sorted([c[2] for c in clusters[0]])
        ratio = radii[0] / radii[-1]
        gt_ratio = gt["id"] / gt["od"]
        ratio_text = f" | ID/OD: {ratio:.3f} (GT={gt_ratio:.3f})"

    pil = add_header(
        canvas,
        f"{name.upper()} — GRADIENT_ALT Concentric Clustering",
        f"{' | '.join(info_parts)}{ratio_text}",
        f"GT: OD={gt['od']} ID={gt['id']}",
    )
    return pil


def run():
    print("HOUGH_GRADIENT_ALT 전체 도면 검증")
    print("=" * 60)

    summary = []

    for name, gt in GT.items():
        img_path = INPUT_DIR / f"{name}_main_view.jpg"
        if not img_path.exists():
            print(f"⚠ {name}: {img_path.name} 없음")
            continue

        print(f"\n{name.upper()} (GT: OD={gt['od']} ID={gt['id']})")

        img = cv2.imread(str(img_path))
        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        h, w = gray.shape
        min_r = int(min(h, w) * MIN_R_RATIO)
        max_r = int(min(h, w) * MAX_R_RATIO)

        # Contour
        contour_circles = detect_contour_circles(gray, min_r, max_r)
        print(f"  Contour: {len(contour_circles)}개")

        # Hough ALT
        hough_alt = detect_hough_alt(gray, min_r, max_r)
        print(f"  Hough ALT: {len(hough_alt)}개")
        for cx, cy, r, _ in hough_alt:
            print(f"    ({cx:.0f},{cy:.0f}) r={r:.0f}")

        # Hough 현행 (비교용)
        hough_orig = detect_hough_original(gray, min_r, max_r)
        print(f"  Hough 현행: {len(hough_orig)}개")

        # Dedup + Cluster
        all_circles = contour_circles + hough_alt
        deduped = deduplicate(all_circles)
        clusters = find_clusters(deduped)

        bearing = clusters[0] if clusters else []
        radii = sorted([c[2] for c in bearing]) if bearing else []

        print(f"  Dedup: {len(deduped)}개 → 클러스터 {len(clusters)}개")
        if bearing:
            print(f"  베어링: {len(bearing)}원, "
                  f"r={radii[0]:.0f}~{radii[-1]:.0f}")
            if len(radii) >= 2:
                ratio = radii[0] / radii[-1]
                gt_ratio = gt["id"] / gt["od"]
                print(f"  ID/OD: {ratio:.3f} (GT={gt_ratio:.3f})")

        # 시각화 저장
        pil = draw_final(img, deduped, clusters, name, gt)
        save_pil(pil, f"{name}_alt_cluster.jpg")

        summary.append({
            "name": name,
            "contour": len(contour_circles),
            "hough_alt": len(hough_alt),
            "hough_orig": len(hough_orig),
            "dedup": len(deduped),
            "clusters": len(clusters),
            "bearing_n": len(bearing),
            "bearing_r": f"{radii[0]:.0f}~{radii[-1]:.0f}" if radii else "-",
            "ratio": radii[0] / radii[-1] if len(radii) >= 2 else 0,
            "gt_ratio": gt["id"] / gt["od"],
        })

    # 요약 테이블
    print("\n" + "=" * 60)
    print("전체 비교 요약")
    print(f"{'도면':>6} {'현행Hough':>10} {'ALT':>6} {'Dedup':>6} "
          f"{'베어링':>7} {'ID/OD':>8} {'GT':>8}")
    for s in summary:
        print(f"{s['name'].upper():>6} {s['hough_orig']:>10} "
              f"{s['hough_alt']:>6} {s['dedup']:>6} "
              f"{s['bearing_n']:>7} {s['ratio']:>8.3f} "
              f"{s['gt_ratio']:>8.3f}")


if __name__ == "__main__":
    run()
