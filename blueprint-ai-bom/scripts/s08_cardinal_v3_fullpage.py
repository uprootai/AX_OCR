#!/usr/bin/env python3
"""S08 Cardinal Projection v3 — 전체 도면에서 직선 투사

메인 뷰 크롭이 아닌 전체 도면에서:
1. 메인 뷰 영역에서 ALT 동심원 검출
2. 동서남북 4방향 최대치 스캔으로 돌출부 끝점 검출
3. 동심원/돌출부 끝점에서 전체 도면을 가로지르는 직선
4. SECTION 영역의 화살촉과 만나는지 확인
"""

import argparse
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from generate_protrusion_detect import cardinal_max_scan

SRC_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs")
OUT_DIR = Path("/home/uproot/ax/poc/docs-site-starlight/public/images/gt-validation/steps")
OUT_DIR.mkdir(exist_ok=True)

GT = {
    "TD0062015": {"name": "t1", "od": 360, "id": 190},
    "TD0062021": {"name": "t2", "od": 380, "id": 190},
    "TD0062031": {"name": "t4", "od": 420, "id": 260},
    "TD0062050": {"name": "t8", "od": 500, "id": 260},
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
    font = get_font(max(16, h // 60))
    font_sm = get_font(max(12, h // 80))
    bar_h = 80 if subtitle2 else 60
    draw.rectangle([0, 0, w, bar_h], fill="#222222")
    draw.text((10, 5), title, fill="white", font=font)
    if subtitle:
        draw.text((10, 30), subtitle, fill="#AAAAAA", font=font_sm)
    if subtitle2:
        draw.text((10, 52), subtitle2, fill="#66BB6A", font=font_sm)
    return pil


def save_pil(pil_img, name, max_w=1400):
    if pil_img.width > max_w:
        ratio = max_w / pil_img.width
        pil_img = pil_img.resize(
            (max_w, int(pil_img.height * ratio)), Image.LANCZOS
        )
    out = OUT_DIR / name
    pil_img.save(out, quality=85)
    print(f"  ✓ {name} ({pil_img.width}x{pil_img.height})")


def find_main_view_region(gray):
    """콘텐츠 밀도 기반 메인 뷰 영역 추정

    전체 도면에서 좌측 ~55%가 정면도(메인 뷰) 영역.
    상하는 콘텐츠 밀도로 추정.
    """
    h, w = gray.shape
    # 좌측 55% = 메인 뷰 영역
    x1, x2 = 0, int(w * 0.55)
    # 상하 마진 10%
    y1, y2 = int(h * 0.10), int(h * 0.90)
    return x1, y1, x2, y2


def detect_concentric_alt(gray_roi, min_r, max_r):
    """메인 뷰 ROI에서 ALT 동심원 검출"""
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


def select_primary_concentric_circles(circles, center_tol=12, radius_tol=8, max_count=3):
    """같은 중심의 주 동심원 클러스터만 남긴다."""
    if not circles:
        return []

    groups = []
    for cx, cy, r in circles:
        matched_group = None
        for group in groups:
            gcx, gcy = group["center"]
            if np.hypot(cx - gcx, cy - gcy) <= center_tol:
                matched_group = group
                break
        if matched_group is None:
            groups.append({"center": (cx, cy), "circles": [(cx, cy, r)]})
            continue
        matched_group["circles"].append((cx, cy, r))
        xs = [item[0] for item in matched_group["circles"]]
        ys = [item[1] for item in matched_group["circles"]]
        matched_group["center"] = (float(np.mean(xs)), float(np.mean(ys)))

    groups.sort(
        key=lambda group: (
            len(group["circles"]),
            max(circle[2] for circle in group["circles"]),
        ),
        reverse=True,
    )

    deduped = []
    for circle in sorted(groups[0]["circles"], key=lambda item: item[2]):
        if deduped and abs(circle[2] - deduped[-1][2]) < radius_tol:
            continue
        deduped.append(circle)

    if len(deduped) <= max_count:
        return deduped

    pick_idx = np.linspace(0, len(deduped) - 1, max_count).round().astype(int)
    return [deduped[idx] for idx in pick_idx]


def detect_arrowheads(gray):
    """S01 방식 — Black Hat 모폴로지로 실선 삼각형 화살촉만 검출

    Black Hat = closing - original → 작은 실선 구조(화살촉)만 강조.
    원본 이진화 컨투어와 달리 문자/해칭/볼트홀이 제거됨.
    """
    _, binary = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    ks = max(3, min(gray.shape[0], gray.shape[1]) // 150)
    ks = ks if ks % 2 == 1 else ks + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))
    black_hat = cv2.subtract(
        cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel), binary
    )

    dil_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    black_hat = cv2.dilate(black_hat, dil_k, iterations=1)

    contours, _ = cv2.findContours(
        black_hat, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    arrows = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 50 or area > 500:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if h == 0 or w == 0:
            continue
        aspect = w / h
        if aspect < 0.3 or aspect > 3.0:
            continue
        M = cv2.moments(cnt)
        if M["m00"] < 1e-6:
            acx, acy = x + w // 2, y + h // 2
        else:
            acx = int(M["m10"] / M["m00"])
            acy = int(M["m01"] / M["m00"])
        arrows.append({"x": float(acx), "y": float(acy), "area": float(area)})
    return arrows


def collect_projection_data(gray):
    """전체 도면에서 직선 투사에 필요한 끝점 좌표를 수집한다."""
    rx1, ry1, rx2, ry2 = find_main_view_region(gray)
    roi_gray = gray[ry1:ry2, rx1:rx2]
    roi_h, roi_w = roi_gray.shape
    min_r = int(min(roi_h, roi_w) * MIN_R_RATIO)
    max_r = int(min(roi_h, roi_w) * MAX_R_RATIO)

    raw_circles_roi = detect_concentric_alt(roi_gray, min_r, max_r)
    circles_roi = select_primary_concentric_circles(raw_circles_roi)
    circles_full = [(cx + rx1, cy + ry1, r) for cx, cy, r in circles_roi]

    peaks_full = []
    outer_r = None
    center_full = None
    if circles_roi:
        outer_r = max(c[2] for c in circles_roi)
        ccx_roi, ccy_roi = circles_roi[0][0], circles_roi[0][1]
        center_full = (circles_full[0][0], circles_full[0][1])
        _, protrusions_roi = cardinal_max_scan(roi_gray, ccx_roi, ccy_roi, outer_r)
        peaks_full = [
            (angle_deg, max_radius, px + rx1, py + ry1)
            for angle_deg, max_radius, px, py in protrusions_roi
        ]

    return {
        "raw_circles_roi": raw_circles_roi,
        "circles_full": circles_full,
        "peaks_full": peaks_full,
        "outer_r": outer_r,
        "center_full": center_full,
    }


def build_circle_lines(circles_full):
    dir_colors = {
        "N": (255, 100, 100),
        "S": (255, 100, 100),
        "E": (0, 200, 255),
        "W": (0, 200, 255),
    }
    lines = []
    for cx, cy, r in circles_full:
        for dir_name, ddx, ddy, axis in [
            ("N", 0, -1, "h"),
            ("S", 0, 1, "h"),
            ("E", 1, 0, "v"),
            ("W", -1, 0, "v"),
        ]:
            px = int(round(cx + r * ddx))
            py = int(round(cy + r * ddy))
            lines.append(
                {
                    "px": px,
                    "py": py,
                    "axis": axis,
                    "color": dir_colors[dir_name],
                    "dir_name": dir_name,
                    "cx": float(cx),
                    "cy": float(cy),
                    "r": float(r),
                }
            )
    return lines


def attach_circle_hits(circle_lines, arrows=None, hit_tolerance=15):
    arrows = arrows or []
    annotated = []
    for line in circle_lines:
        hits = []
        cx = line["cx"]
        cy = line["cy"]
        r = line["r"]
        for arrow in arrows:
            ax, ay = arrow["x"], arrow["y"]
            if line["axis"] == "h" and abs(ay - line["py"]) <= hit_tolerance:
                if np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2) < r * 0.9:
                    continue
                hits.append((int(ax), int(ay)))
            elif line["axis"] == "v" and abs(ax - line["px"]) <= hit_tolerance:
                if np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2) < r * 0.9:
                    continue
                hits.append((int(ax), int(ay)))
        annotated.append({**line, "hits": hits})
    return annotated


def build_protrusion_lines(peaks_full, center_full, outer_r):
    lines = []
    if not peaks_full or center_full is None or outer_r is None:
        return lines

    ccx, ccy = center_full
    for angle, _, ppx, ppy in peaks_full:
        for axis in ["h", "v"]:
            lines.append(
                {
                    "px": int(ppx),
                    "py": int(ppy),
                    "axis": axis,
                    "color": (255, 0, 200),
                    "angle": angle,
                    "ccx": float(ccx),
                    "ccy": float(ccy),
                    "outer_r": float(outer_r),
                }
            )
    return lines


def attach_protrusion_hits(protrusion_lines, arrows=None, hit_tolerance=15):
    arrows = arrows or []
    annotated = []
    for line in protrusion_lines:
        hits = []
        ccx = line["ccx"]
        ccy = line["ccy"]
        outer_r = line["outer_r"]
        for arrow in arrows:
            ax, ay = arrow["x"], arrow["y"]
            if line["axis"] == "h" and abs(ay - line["py"]) <= hit_tolerance:
                if np.sqrt((ax - ccx) ** 2 + (ay - ccy) ** 2) > outer_r * 0.9:
                    hits.append((int(ax), int(ay)))
            elif line["axis"] == "v" and abs(ax - line["px"]) <= hit_tolerance:
                if np.sqrt((ax - ccx) ** 2 + (ay - ccy) ** 2) > outer_r * 0.9:
                    hits.append((int(ax), int(ay)))
        annotated.append({**line, "hits": hits})
    return annotated


def draw_projection_axis(canvas, line, full_w, full_h, thickness):
    if line["axis"] == "h":
        cv2.line(canvas, (0, line["py"]), (full_w, line["py"]), line["color"], thickness)
    else:
        cv2.line(canvas, (line["px"], 0), (line["px"], full_h), line["color"], thickness)


def draw_fullpage_projection(img, circles_full, circle_lines, protrusion_lines, gt, name):
    full_h, full_w = img.shape[:2]
    canvas = img.copy()

    for cx, cy, r in circles_full:
        cv2.circle(canvas, (int(cx), int(cy)), int(r), (67, 160, 71), 3)

    circle_hit = 0
    circle_hit_lines = 0
    for line in circle_lines:
        draw_projection_axis(canvas, line, full_w, full_h, 2 if line["hits"] else 1)
        cv2.circle(
            canvas,
            (line["px"], line["py"]),
            8,
            (255, 255, 255),
            2 if line["hits"] else 1,
        )
        if not line["hits"]:
            continue
        circle_hit_lines += 1
        for hx, hy in line["hits"]:
            cv2.drawMarker(
                canvas,
                (hx, hy),
                (0, 0, 255),
                cv2.MARKER_TILTED_CROSS,
                15,
                2,
            )
            circle_hit += 1

    protrusion_hit = 0
    protrusion_hit_lines = 0
    for line in protrusion_lines:
        draw_projection_axis(canvas, line, full_w, full_h, 2 if line["hits"] else 1)
        cv2.drawMarker(
            canvas,
            (line["px"], line["py"]),
            (0, 0, 255),
            cv2.MARKER_DIAMOND,
            12,
            3 if line["hits"] else 1,
        )
        if not line["hits"]:
            continue
        protrusion_hit_lines += 1
        for hx, hy in line["hits"]:
            cv2.drawMarker(
                canvas,
                (hx, hy),
                (255, 0, 200),
                cv2.MARKER_TILTED_CROSS,
                12,
                2,
            )
            protrusion_hit += 1

    total_lines = len(circle_lines) + len(protrusion_lines)
    active_lines = circle_hit_lines + protrusion_hit_lines
    print(f"  전체 직선: {total_lines}개 → 히트 있는 직선: {active_lines}개")
    print(f"  동심원 히트: {circle_hit}개 ({circle_hit_lines}개 직선)")
    print(f"  돌출부 히트: {protrusion_hit}개 ({protrusion_hit_lines}개 직선)")

    for cx, cy, r in circles_full:
        cv2.putText(
            canvas,
            f"r={r:.0f}",
            (int(cx + r * 0.7), int(cy - r * 0.3)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (67, 160, 71),
            2,
        )

    pil = add_header(
        canvas,
        f"{name.upper()} — Cardinal v3 + Protrusion ({full_w}x{full_h})",
        f"동심원 {len(circles_full)}개 + 돌출 {len(protrusion_lines) // 2}개 | "
        f"히트: 원{circle_hit} + 돌출{protrusion_hit}",
        f"GT: OD={gt['od']} ID={gt['id']}",
    )
    return pil


def draw_projection_lines_only(img, circles_full, circle_lines, peaks_full, protrusion_lines):
    """문서용: 끝점과 직선만 남긴 깔끔한 투사선 시각화."""
    full_h, full_w = img.shape[:2]
    canvas = img.copy()

    for cx, cy, r in circles_full:
        cv2.circle(canvas, (int(cx), int(cy)), int(r), (67, 160, 71), 4)

    circle_endpoint_color = (255, 255, 0)
    horizontal_color = (255, 255, 0)
    vertical_color = (0, 255, 255)
    protrusion_color = (255, 0, 200)

    for line in circle_lines:
        color = horizontal_color if line["axis"] == "h" else vertical_color
        if line["axis"] == "h":
            cv2.line(canvas, (0, line["py"]), (full_w, line["py"]), color, 2)
        else:
            cv2.line(canvas, (line["px"], 0), (line["px"], full_h), color, 2)
        cv2.circle(canvas, (line["px"], line["py"]), 10, circle_endpoint_color, -1)
        cv2.circle(canvas, (line["px"], line["py"]), 14, (60, 60, 60), 2)

    for line in protrusion_lines:
        if line["axis"] == "h":
            cv2.line(canvas, (0, line["py"]), (full_w, line["py"]), protrusion_color, 2)
        else:
            cv2.line(canvas, (line["px"], 0), (line["px"], full_h), protrusion_color, 2)

    for _, _, px, py in peaks_full:
        cv2.drawMarker(
            canvas,
            (int(px), int(py)),
            (0, 0, 255),
            cv2.MARKER_DIAMOND,
            28,
            3,
        )

    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--doc",
        choices=[gt["name"] for gt in GT.values()],
        help="특정 도면만 처리",
    )
    parser.add_argument(
        "--lines-only",
        action="store_true",
        help="화살촉 히트 없이 끝점과 투사선만 그린 이미지 생성",
    )
    return parser.parse_args()


def run():
    args = parse_args()
    print("S08 Cardinal v3 — 전체 도면 투사 + 4방향 돌출부")
    print("=" * 60)

    targets = [
        (doc_id, gt)
        for doc_id, gt in GT.items()
        if args.doc is None or gt["name"] == args.doc
    ]

    for doc_id, gt in targets:
        name = gt["name"]
        img_path = SRC_DIR / f"{doc_id}.png"
        if not img_path.exists():
            print(f"⚠ {name}: {img_path} 없음")
            continue

        print(f"\n{name.upper()} — {doc_id} (GT: OD={gt['od']} ID={gt['id']})")

        img = cv2.imread(str(img_path))
        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        full_h, full_w = gray.shape
        print(f"  전체 도면: {full_w}x{full_h}")

        data = collect_projection_data(gray)
        circles_full = data["circles_full"]
        peaks_full = data["peaks_full"]
        outer_r = data["outer_r"]
        center_full = data["center_full"]

        print(
            f"  ALT 후보: {len(data['raw_circles_roi'])}개 → "
            f"주 동심원: {len(circles_full)}개"
        )
        print(f"  돌출 끝점: {len(peaks_full)}개")

        if not circles_full:
            continue

        # Shared geometry: lines-only/fullpage 모두 동일한 끝점 집합을 사용한다.
        base_circle_lines = build_circle_lines(circles_full)
        base_protrusion_lines = build_protrusion_lines(peaks_full, center_full, outer_r)

        if args.lines_only:
            print(
                f"  lines-only 산출물: 동심원 직선 {len(base_circle_lines)}개 + "
                f"돌출 직선 {len(base_protrusion_lines)}개"
            )
            pil = draw_projection_lines_only(
                img,
                circles_full,
                base_circle_lines,
                peaks_full,
                base_protrusion_lines,
            )
            save_pil(pil, f"{name}_projection_lines_only.jpg", max_w=1600)
            continue

        arrows = detect_arrowheads(gray)
        print(f"  화살촉 후보: {len(arrows)}개")
        circle_lines = attach_circle_hits(base_circle_lines, arrows)
        protrusion_lines = attach_protrusion_hits(
            base_protrusion_lines,
            arrows,
        )

        pil = draw_fullpage_projection(
            img,
            circles_full,
            circle_lines,
            protrusion_lines,
            gt,
            name,
        )
        save_pil(pil, f"{name}_cardinal_v3_full.jpg", max_w=1600)

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
