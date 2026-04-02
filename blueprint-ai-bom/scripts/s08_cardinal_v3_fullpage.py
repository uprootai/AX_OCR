#!/usr/bin/env python3
"""S08 Cardinal Projection v3 — 전체 도면에서 직선 투사

메인 뷰 크롭이 아닌 전체 도면에서:
1. 메인 뷰 영역에서 ALT 동심원 검출
2. 동심원 끝점에서 전체 도면을 가로지르는 직선
3. SECTION 영역의 화살촉과 만나는지 확인
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

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


def detect_arrowheads(gray, min_area=50, max_area=1500):
    """전체 도면에서 화살촉 후보 검출"""
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
        solidity = area / hull_area
        if solidity < 0.4:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = min(bw, bh) / max(bw, bh) if max(bw, bh) > 0 else 0
        if aspect < 0.2 or (bw > 80 and bh > 80):
            continue
        M = cv2.moments(cnt)
        if M["m00"] > 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            arrows.append({"x": float(cx), "y": float(cy), "area": area})
    return arrows


def run():
    print("S08 Cardinal v3 — 전체 도면 투사")
    print("=" * 60)

    for doc_id, gt in GT.items():
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

        # 1. 메인 뷰 영역 추정
        rx1, ry1, rx2, ry2 = find_main_view_region(gray)
        roi_gray = gray[ry1:ry2, rx1:rx2]
        roi_h, roi_w = roi_gray.shape
        min_r = int(min(roi_h, roi_w) * MIN_R_RATIO)
        max_r = int(min(roi_h, roi_w) * MAX_R_RATIO)
        print(f"  메인 뷰 ROI: ({rx1},{ry1})-({rx2},{ry2}) = {roi_w}x{roi_h}")

        # 2. 동심원 검출 (ROI 좌표)
        circles_roi = detect_concentric_alt(roi_gray, min_r, max_r)
        print(f"  동심원: {len(circles_roi)}개")

        # ROI → 전체 도면 좌표로 변환
        circles_full = [(cx + rx1, cy + ry1, r)
                        for cx, cy, r in circles_roi]
        for cx, cy, r in circles_full:
            print(f"    ({cx:.0f},{cy:.0f}) r={r:.0f}")

        # 3. 전체 도면에서 화살촉 검출
        arrows = detect_arrowheads(gray)
        print(f"  화살촉 후보: {len(arrows)}개")

        # 4. 시각화 — 전체 도면 위에 직선 + 화살촉
        canvas = img.copy()

        # 동심원 (초록)
        for cx, cy, r in circles_full:
            cv2.circle(canvas, (int(cx), int(cy)), int(r), (67, 160, 71), 3)

        # 메인 뷰 영역 박스 (점선 효과)
        cv2.rectangle(canvas, (rx1, ry1), (rx2, ry2), (100, 100, 100), 2)
        cv2.putText(canvas, "MAIN VIEW", (rx1 + 10, ry1 + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)

        # 화살촉 후보 (작은 노란 점)
        for arrow in arrows:
            cv2.circle(canvas, (int(arrow["x"]), int(arrow["y"])), 4,
                       (0, 200, 255), -1)

        # 각 끝점에서 접선 직선 (전체 도면 가로지름)
        dir_colors = {
            "N": (255, 100, 100),
            "S": (255, 100, 100),
            "E": (0, 200, 255),
            "W": (0, 200, 255),
        }

        hit_count = 0
        for cx, cy, r in circles_full:
            for dir_name, ddx, ddy, axis in [
                ("N", 0, -1, "h"), ("S", 0, 1, "h"),
                ("E", 1, 0, "v"), ("W", -1, 0, "v"),
            ]:
                px = int(cx + r * ddx)
                py = int(cy + r * ddy)
                color = dir_colors[dir_name]

                # 접선 직선 — 전체 도면 폭/높이
                if axis == "h":
                    cv2.line(canvas, (0, py), (full_w, py), color, 2)
                else:
                    cv2.line(canvas, (px, 0), (px, full_h), color, 2)

                # 끝점 마커
                cv2.circle(canvas, (px, py), 8, (255, 255, 255), 2)

                # 직선 위 화살촉 히트
                for arrow in arrows:
                    ax, ay = arrow["x"], arrow["y"]
                    if axis == "h":
                        if abs(ay - py) <= 15:
                            dist_to_center = np.sqrt(
                                (ax - cx) ** 2 + (ay - cy) ** 2)
                            if dist_to_center < r * 0.9:
                                continue
                            cv2.drawMarker(
                                canvas, (int(ax), int(ay)),
                                (0, 0, 255), cv2.MARKER_TILTED_CROSS, 15, 2)
                            hit_count += 1
                    else:
                        if abs(ax - px) <= 15:
                            dist_to_center = np.sqrt(
                                (ax - cx) ** 2 + (ay - cy) ** 2)
                            if dist_to_center < r * 0.9:
                                continue
                            cv2.drawMarker(
                                canvas, (int(ax), int(ay)),
                                (0, 0, 255), cv2.MARKER_TILTED_CROSS, 15, 2)
                            hit_count += 1

        # 반지름 라벨
        for cx, cy, r in circles_full:
            cv2.putText(canvas, f"r={r:.0f}",
                        (int(cx + r * 0.7), int(cy - r * 0.3)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (67, 160, 71), 2)

        pil = add_header(
            canvas,
            f"{name.upper()} — Cardinal v3 Full Page ({full_w}x{full_h})",
            f"동심원 {len(circles_full)}개 | 화살촉 {len(arrows)}개 | "
            f"직선 위 히트: {hit_count}개",
            f"GT: OD={gt['od']} ID={gt['id']}",
        )
        save_pil(pil, f"{name}_cardinal_v3_full.jpg")

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
