#!/usr/bin/env python3
"""S08 Cardinal Projection v3 — HOUGH_GRADIENT_ALT 동심원 기반."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from cardinal_common import add_header, detect_concentric_alt, save_pil

INPUT_DIR = Path(__file__).resolve().parents[2] / "docs-site-starlight" / "public" / "images" / "gt-validation"
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


def detect_arrowheads_morphology(gray, min_area=30, max_area=800):
    """Black Hat 모폴로지 기반 화살촉 후보 검출."""
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    cv2.morphologyEx(binary, cv2.MORPH_BLACKHAT, kernel)

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
        solidity = area / hull_area
        if solidity < 0.4:
            continue

        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = min(bw, bh) / max(bw, bh) if max(bw, bh) > 0 else 0
        if aspect < 0.2 or (bw > 40 and bh > 40):
            continue

        moments = cv2.moments(cnt)
        if moments["m00"] > 0:
            cx = moments["m10"] / moments["m00"]
            cy = moments["m01"] / moments["m00"]
            arrows.append(
                {
                    "x": float(cx),
                    "y": float(cy),
                    "area": area,
                    "solidity": solidity,
                    "bbox": (x, y, bw, bh),
                }
            )

    return arrows


def cardinal_projection(circles, arrows, gray, tolerance=15):
    """각 원의 N/S/E/W 끝점에서 원 바깥쪽 직선으로 화살촉을 매칭한다."""
    h, w = gray.shape
    if not arrows:
        return []

    results = []
    directions = [
        ("N", 0, -1, "h"),
        ("S", 0, 1, "h"),
        ("E", 1, 0, "v"),
        ("W", -1, 0, "v"),
    ]

    for ci, (cx, cy, radius) in enumerate(circles):
        circle_hits = []

        for dir_name, dx, dy, line_axis in directions:
            px = cx + radius * dx
            py = cy + radius * dy

            if px < 0 or py < 0 or px >= w or py >= h:
                continue

            matches = []
            for ai, arrow in enumerate(arrows):
                ax, ay = arrow["x"], arrow["y"]

                if line_axis == "h":
                    if abs(ay - py) > tolerance:
                        continue
                    dist_to_center = np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2)
                    if dist_to_center < radius * 0.9:
                        continue
                    dist = np.sqrt((ax - px) ** 2 + (ay - py) ** 2)
                    matches.append({"arrow_idx": ai, "arrow": arrow, "dist": dist})
                else:
                    if abs(ax - px) > tolerance:
                        continue
                    dist_to_center = np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2)
                    if dist_to_center < radius * 0.9:
                        continue
                    dist = np.sqrt((ax - px) ** 2 + (ay - py) ** 2)
                    matches.append({"arrow_idx": ai, "arrow": arrow, "dist": dist})

            if matches:
                best = min(matches, key=lambda m: m["dist"])
                circle_hits.append(
                    {
                        "direction": dir_name,
                        "line": line_axis,
                        "endpoint": (px, py),
                        "arrow": best["arrow"],
                        "dist": best["dist"],
                    }
                )

        results.append(
            {
                "circle_idx": ci,
                "cx": cx,
                "cy": cy,
                "r": radius,
                "hits": circle_hits,
            }
        )

    return results


def visualize_cardinal(img, circles, arrows, projections, name, gt):
    """Cardinal Projection 결과 시각화"""
    h, w = img.shape[:2]
    canvas = img.copy()

    for cx, cy, radius in circles:
        cv2.circle(canvas, (int(cx), int(cy)), int(radius), (67, 160, 71), 2)
        cv2.drawMarker(canvas, (int(cx), int(cy)), (67, 160, 71), cv2.MARKER_CROSS, 15, 1)

    for arrow in arrows:
        cv2.circle(canvas, (int(arrow["x"]), int(arrow["y"])), 3, (0, 200, 255), -1)

    dir_colors = {
        "N": (255, 100, 100),
        "S": (255, 100, 100),
        "E": (0, 200, 255),
        "W": (0, 200, 255),
    }

    line_map = {"N": "h", "S": "h", "E": "v", "W": "v"}
    hit_count = 0

    for proj in projections:
        cx, cy, radius = proj["cx"], proj["cy"], proj["r"]

        for dir_name, ddx, ddy in [("N", 0, -1), ("S", 0, 1), ("E", 1, 0), ("W", -1, 0)]:
            px = int(cx + radius * ddx)
            py = int(cy + radius * ddy)
            color = dir_colors.get(dir_name, (200, 200, 200))
            axis = line_map[dir_name]

            if axis == "h":
                cv2.line(canvas, (0, py), (w, py), color, 2)
            else:
                cv2.line(canvas, (px, 0), (px, h), color, 2)

            cv2.circle(canvas, (px, py), 7, (255, 255, 255), 2)
            cv2.circle(canvas, (px, py), 7, color, 1)

        for hit in proj["hits"]:
            arrow_point = hit["arrow"]
            endpoint = hit["endpoint"]
            color = dir_colors.get(hit["direction"], (200, 200, 200))

            cv2.line(
                canvas,
                (int(endpoint[0]), int(endpoint[1])),
                (int(arrow_point["x"]), int(arrow_point["y"])),
                color,
                2,
            )
            cv2.drawMarker(
                canvas,
                (int(arrow_point["x"]), int(arrow_point["y"])),
                (0, 0, 255),
                cv2.MARKER_TILTED_CROSS,
                12,
                2,
            )
            hit_count += 1

    for cx, cy, radius in circles:
        cv2.putText(
            canvas,
            f"r={radius:.0f}",
            (int(cx + radius * 0.7), int(cy - radius * 0.7)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (67, 160, 71),
            1,
        )

    total_dirs = len(circles) * 4
    return add_header(
        canvas,
        f"{name.upper()} — Cardinal Projection v3 (ALT)",
        f"동심원 {len(circles)}개 × 4방향 = {total_dirs}개 투사 | 화살촉 히트: {hit_count}/{total_dirs}",
        f"GT: OD={gt['od']} ID={gt['id']} | 화살촉 후보: {len(arrows)}개",
        title_min_font=14,
        title_divisor=40,
        subtitle_min_font=11,
        subtitle_divisor=55,
        bar_h_no_sub2=55,
        bar_h_with_sub2=70,
        subtitle_y=28,
        subtitle2_y=48,
    )


def run():
    print("S08 Cardinal Projection v3 — HOUGH_GRADIENT_ALT 기반")
    print("=" * 60)

    summary = []

    for name, gt in GT.items():
        img_path = INPUT_DIR / f"{name}_main_view.jpg"
        if not img_path.exists():
            print(f"⚠ {name}: 없음")
            continue

        print(f"\n{name.upper()} (GT: OD={gt['od']} ID={gt['id']})")

        img = cv2.imread(str(img_path))
        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None or gray is None:
            print(f"  ⚠ 이미지 로드 실패: {img_path}")
            continue

        h, w = gray.shape
        min_r = int(min(h, w) * MIN_R_RATIO)
        max_r = int(min(h, w) * MAX_R_RATIO)

        circles = detect_concentric_alt(gray, min_r, max_r)
        print(f"  동심원: {len(circles)}개")
        for cx, cy, radius in circles:
            print(f"    ({cx:.0f},{cy:.0f}) r={radius:.0f}")

        arrows = detect_arrowheads_morphology(gray)
        print(f"  화살촉 후보: {len(arrows)}개")

        projections = cardinal_projection(circles, arrows, gray)
        total_hits = sum(len(proj["hits"]) for proj in projections)
        total_lines = len(circles) * 4 * 2
        print(
            f"  Cardinal 히트: {total_hits} "
            f"(끝점 {len(circles) * 4}개 × 직선2 = {total_lines}개 직선)"
        )

        for proj in projections:
            if proj["hits"]:
                hits_str = ", ".join(
                    f"{hit['direction']}-{hit['line']}({hit['dist']:.0f}px)"
                    for hit in proj["hits"]
                )
                print(f"    r={proj['r']:.0f}: {hits_str}")

        pil = visualize_cardinal(img, circles, arrows, projections, name, gt)
        save_pil(pil, f"{name}_cardinal_v3.jpg", max_w=1000, out_dir=OUT_DIR)

        summary.append(
            {
                "name": name,
                "circles": len(circles),
                "arrows": len(arrows),
                "total_dirs": len(circles) * 4,
                "hits": total_hits,
                "hit_rate": f"{total_hits}/{len(circles) * 4}",
            }
        )

    print("\n" + "=" * 60)
    print("전체 요약")
    print(f"{'도면':>6} {'동심원':>6} {'화살촉':>6} {'히트':>10}")
    for row in summary:
        print(f"{row['name'].upper():>6} {row['circles']:>6} {row['arrows']:>6} {row['hit_rate']:>10}")

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
