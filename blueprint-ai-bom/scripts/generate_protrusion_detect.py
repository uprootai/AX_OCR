#!/usr/bin/env python3
"""돌출부 검출 — 동심원 중심에서 방사 스캔으로 원 바깥 돌출 영역 식별."""

from __future__ import annotations

from pathlib import Path

import cv2

from cardinal_common import (
    add_header,
    cardinal_max_scan,
    detect_concentric_alt,
    save_pil,
)

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


def cluster_protrusions(protrusions, angle_gap=10):
    """인접한 각도의 돌출부를 그룹핑 → 각 그룹의 최대점 = 돌출 끝점"""
    if not protrusions:
        return []

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

    peaks = []
    for group in groups:
        peak = max(group, key=lambda p: p[1])
        peaks.append(
            {
                "angle": peak[0],
                "r": peak[1],
                "x": peak[2],
                "y": peak[3],
                "span": len(group),
            }
        )

    return peaks


def draw_dashed_circle(img, center, radius, color, thickness=1, dash_deg=12, gap_deg=8):
    """점선 외원 기준선 렌더링."""
    step = max(1, dash_deg + gap_deg)
    for start in range(0, 360, step):
        end = min(start + dash_deg, 359)
        cv2.ellipse(
            img,
            center,
            (int(radius), int(radius)),
            0,
            start,
            end,
            color,
            thickness,
            cv2.LINE_AA,
        )


def draw_label(canvas, text, origin, color):
    """밝은 도면 배경에서도 읽히도록 라벨에 배경을 준다."""
    x, y = origin
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.45
    thickness = 1
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
    pad = 3
    cv2.rectangle(
        canvas,
        (x - pad, y - th - pad),
        (x + tw + pad, y + baseline + pad),
        (255, 255, 255),
        -1,
    )
    cv2.rectangle(
        canvas,
        (x - pad, y - th - pad),
        (x + tw + pad, y + baseline + pad),
        color,
        1,
    )
    cv2.putText(canvas, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)


def visualize(img, circles, radial_profile, protrusion_peaks, outer_r, name, gt):
    h, w = img.shape[:2]
    canvas = img.copy()

    if not circles:
        return canvas

    cx, cy = circles[0][0], circles[0][1]
    center = (int(round(cx)), int(round(cy)))
    dir_labels = {270: "N", 90: "S", 0: "E", 180: "W"}
    protrusion_dirs = {dir_labels.get(int(peak["angle"]), "?") for peak in protrusion_peaks}
    top_safe_y = 78
    label_offsets = {
        "N": (12, 18),
        "S": (12, 18),
        "E": (12, -10),
        "W": (-96, -10),
    }

    for ccx, ccy, radius in circles:
        cv2.circle(canvas, (int(ccx), int(ccy)), int(radius), (67, 160, 71), 2, cv2.LINE_AA)
        cv2.drawMarker(
            canvas,
            (int(ccx), int(ccy)),
            (67, 160, 71),
            cv2.MARKER_CROSS,
            16,
            1,
        )

    draw_dashed_circle(canvas, center, outer_r, (255, 160, 80), 2)

    for angle_deg, max_r, mx, my in radial_profile:
        direction = dir_labels.get(int(angle_deg), "?")
        endpoint = (int(mx), int(my))
        is_protrusion = direction in protrusion_dirs
        label_x = max(6, min(w - 110, endpoint[0] + label_offsets.get(direction, (10, -8))[0]))
        label_y = max(top_safe_y, min(h - 6, endpoint[1] + label_offsets.get(direction, (10, -8))[1]))

        cv2.line(canvas, center, endpoint, (0, 0, 255), 2, cv2.LINE_AA)

        if is_protrusion:
            cv2.drawMarker(
                canvas,
                endpoint,
                (0, 0, 255),
                cv2.MARKER_DIAMOND,
                18,
                2,
            )
            label_color = (0, 0, 255)
        else:
            cv2.circle(canvas, endpoint, 5, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(canvas, endpoint, 4, (255, 255, 0), -1, cv2.LINE_AA)
            label_color = (220, 180, 0)

        draw_label(canvas, f"{direction} r={int(max_r)}", (label_x, label_y), label_color)

    cv2.drawMarker(canvas, center, (255, 255, 255), cv2.MARKER_CROSS, 22, 5)
    cv2.drawMarker(canvas, center, (67, 160, 71), cv2.MARKER_CROSS, 18, 3)

    return add_header(
        canvas,
        f"{name.upper()} — Protrusion Detection (Radial Scan)",
        f"동심원 {len(circles)}개 | 외원 r={outer_r:.0f} | 돌출 끝점: {len(protrusion_peaks)}개",
        f"GT: OD={gt['od']} ID={gt['id']}",
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
        if img is None or gray is None:
            print(f"  ⚠ 이미지 로드 실패: {img_path}")
            continue

        h, w = gray.shape
        min_r = int(min(h, w) * MIN_R_RATIO)
        max_r = int(min(h, w) * MAX_R_RATIO)

        circles = detect_concentric_alt(gray, min_r, max_r)
        if not circles:
            print("  동심원 미검출")
            continue

        outer_r = max(circle[2] for circle in circles)
        cx, cy = circles[0][0], circles[0][1]
        print(f"  동심원: {len(circles)}개, 외원 r={outer_r:.0f}")
        print(f"  중심: ({cx:.0f}, {cy:.0f})")

        profile, protrusions = cardinal_max_scan(gray, cx, cy, outer_r)
        print(f"  4방향 스캔, 돌출 {len(protrusions)}개")

        peaks = cluster_protrusions(protrusions)
        print(f"  돌출 끝점: {len(peaks)}개")
        for peak in peaks:
            print(
                f"    {peak['angle']:.0f}° r={peak['r']} "
                f"({peak['x']},{peak['y']}) span={peak['span']}°"
            )

        pil = visualize(img, circles, profile, peaks, outer_r, name, gt)
        save_pil(pil, f"{name}_protrusion.jpg", max_w=900, out_dir=OUT_DIR)

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
