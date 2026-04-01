#!/usr/bin/env python3
"""S08 Cardinal Projection v3 — HOUGH_GRADIENT_ALT 동심원 기반

v1/v2 실패 원인: 원 검출 부정확 (케이싱 잡음) → 끝점 좌표 틀림 → 매칭 실패
v3 개선: GRADIENT_ALT로 동심원 3개를 정확히 잡은 뒤 Cardinal Projection 재시도

파이프라인:
1. 메인 뷰 크롭 (콘텐츠 밀도 기반 4-뷰 분할)
2. HOUGH_GRADIENT_ALT → 동심원 검출
3. 각 원의 N/S/E/W 끝점에서 직선 투사
4. 투사선 위의 화살촉(모폴로지) 검출
5. 화살촉 쌍 → 치수선 → OCR 매칭
6. 결과 시각화
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


def save_pil(pil_img, name, max_w=1000):
    if pil_img.width > max_w:
        ratio = max_w / pil_img.width
        pil_img = pil_img.resize(
            (max_w, int(pil_img.height * ratio)), Image.LANCZOS
        )
    out = OUT_DIR / name
    pil_img.save(out, quality=85)
    print(f"  ✓ {name}")


# ── 1. 동심원 검출 (ALT) ──

def detect_concentric_alt(gray, min_r, max_r):
    """HOUGH_GRADIENT_ALT — 동심원 검출"""
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


# ── 2. 화살촉 검출 (Black Hat 모폴로지) ──

def detect_arrowheads_morphology(gray, min_area=30, max_area=800):
    """Black Hat 모폴로지 기반 화살촉 후보 검출

    화살촉 = 작고 날카로운 삼각형 형상.
    Black Hat = closing - original → 밝은 배경의 어두운 작은 구조 강조.
    """
    # 이진화
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Black Hat으로 작은 구조 강조
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    blackhat = cv2.morphologyEx(binary, cv2.MORPH_BLACKHAT, kernel)

    # 원본 binary에서 작은 컨투어 = 화살촉 후보
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    arrows = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        # 볼록 껍질 대비 면적 비율 (화살촉은 삼각형 → hull deficiency 낮음)
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area < 1:
            continue
        solidity = area / hull_area
        if solidity < 0.4:
            continue

        # 종횡비 체크 (너무 길쭉하면 선, 정사각이면 점)
        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = min(bw, bh) / max(bw, bh) if max(bw, bh) > 0 else 0
        if aspect < 0.2 or (bw > 40 and bh > 40):
            continue

        M = cv2.moments(cnt)
        if M["m00"] > 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            arrows.append({
                "x": float(cx), "y": float(cy),
                "area": area, "solidity": solidity,
                "bbox": (x, y, bw, bh),
            })

    return arrows


# ── 3. Cardinal Projection ──

def cardinal_projection(circles, arrows, gray, tolerance=15):
    """각 원의 N/S/E/W 끝점에서 원 바깥쪽 수평선 → 화살촉 매칭

    핵심: 각 끝점에서 원에 안 닿는 방향으로만 수평선을 긋는다.
      N끝점 → 수평선 좌(←)로 + 수평선 우(→)로 (원 위쪽이므로 원에 안 닿음)
      S끝점 → 수평선 좌(←)로 + 수평선 우(→)로 (원 아래쪽이므로 원에 안 닿음)
      E끝점 → 수직선 위(↑)로 + 수직선 아래(↓)로 (원 오른쪽이므로 원에 안 닿음)
      W끝점 → 수직선 위(↑)로 + 수직선 아래(↓)로 (원 왼쪽이므로 원에 안 닿음)

    즉 N/S → 수평선, E/W → 수직선. 원 바깥쪽 양방향.

    tolerance: 직선과 화살촉 사이 수직 거리 최대값 (px)
    """
    h, w = gray.shape
    if not arrows:
        return []

    results = []

    # (방향, dx, dy, 직선축)
    # N/S 끝점은 원의 위/아래 → 수평선(좌우)
    # E/W 끝점은 원의 좌/우 → 수직선(상하)
    directions = [
        ("N", 0, -1, "h"),
        ("S", 0,  1, "h"),
        ("E", 1,  0, "v"),
        ("W", -1, 0, "v"),
    ]

    for ci, (cx, cy, r) in enumerate(circles):
        circle_hits = []

        for dir_name, dx, dy, line_axis in directions:
            # 끝점
            px = cx + r * dx
            py = cy + r * dy

            if px < 0 or py < 0 or px >= w or py >= h:
                continue

            matches = []
            for ai, arrow in enumerate(arrows):
                ax, ay = arrow["x"], arrow["y"]

                if line_axis == "h":
                    # 수평선: y좌표가 끝점과 비슷, 원 바깥(좌우 모두)
                    if abs(ay - py) > tolerance:
                        continue
                    # 원 바깥인지 체크: 화살촉이 원 내부가 아닌지
                    dist_to_center = np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2)
                    if dist_to_center < r * 0.9:
                        continue  # 원 내부 화살촉 제외
                    dist = np.sqrt((ax - px) ** 2 + (ay - py) ** 2)
                    matches.append({
                        "arrow_idx": ai, "arrow": arrow,
                        "dist": dist,
                    })
                else:
                    # 수직선: x좌표가 끝점과 비슷, 원 바깥(상하 모두)
                    if abs(ax - px) > tolerance:
                        continue
                    dist_to_center = np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2)
                    if dist_to_center < r * 0.9:
                        continue
                    dist = np.sqrt((ax - px) ** 2 + (ay - py) ** 2)
                    matches.append({
                        "arrow_idx": ai, "arrow": arrow,
                        "dist": dist,
                    })

            if matches:
                best = min(matches, key=lambda m: m["dist"])
                circle_hits.append({
                    "direction": dir_name,
                    "line": line_axis,
                    "endpoint": (px, py),
                    "arrow": best["arrow"],
                    "dist": best["dist"],
                })

        results.append({
            "circle_idx": ci,
            "cx": cx, "cy": cy, "r": r,
            "hits": circle_hits,
        })

    return results


# ── 시각화 ──

def visualize_cardinal(img, circles, arrows, projections, name, gt):
    """Cardinal Projection 결과 시각화"""
    h, w = img.shape[:2]
    canvas = img.copy()

    # 동심원 (초록)
    for cx, cy, r in circles:
        cv2.circle(canvas, (int(cx), int(cy)), int(r), (67, 160, 71), 2)
        cv2.drawMarker(canvas, (int(cx), int(cy)),
                       (67, 160, 71), cv2.MARKER_CROSS, 15, 1)

    # 화살촉 후보 (작은 노란 점)
    for arrow in arrows:
        cv2.circle(canvas, (int(arrow["x"]), int(arrow["y"])), 3,
                   (0, 200, 255), -1)

    # Cardinal 투사 + 히트
    dir_colors = {
        "N": (255, 100, 100),  # 시안
        "S": (255, 100, 100),
        "E": (0, 200, 255),    # 노랑
        "W": (0, 200, 255),
    }

    # 각 끝점에서 원 바깥쪽 직선 + 히트 표시
    line_map = {"N": "h", "S": "h", "E": "v", "W": "v"}
    hit_count = 0

    for proj in projections:
        cx, cy, r = proj["cx"], proj["cy"], proj["r"]
        hit_dirs = {h["direction"] for h in proj["hits"]}

        for dir_name, ddx, ddy in [("N", 0, -1), ("S", 0, 1),
                                    ("E", 1, 0), ("W", -1, 0)]:
            px = int(cx + r * ddx)
            py = int(cy + r * ddy)
            color = dir_colors.get(dir_name, (200, 200, 200))
            la = line_map[dir_name]

            # 원 바깥쪽 직선만 (원에 안 닿게)
            if la == "h":  # N/S → 수평선 좌우
                cv2.line(canvas, (0, py), (int(cx - r), py), color, 1)
                cv2.line(canvas, (int(cx + r), py), (w, py), color, 1)
            else:  # E/W → 수직선 상하
                cv2.line(canvas, (px, 0), (px, int(cy - r)), color, 1)
                cv2.line(canvas, (px, int(cy + r)), (px, h), color, 1)

            # 끝점 마커
            cv2.circle(canvas, (px, py), 5, color, 2)

        # 히트 표시
        for hit in proj["hits"]:
            ap = hit["arrow"]
            ep = hit["endpoint"]
            color = dir_colors.get(hit["direction"], (200, 200, 200))

            # 끝점 → 화살촉 연결선
            cv2.line(canvas, (int(ep[0]), int(ep[1])),
                     (int(ap["x"]), int(ap["y"])), color, 2)

            # 화살촉 히트 (빨간 X)
            cv2.drawMarker(canvas, (int(ap["x"]), int(ap["y"])),
                           (0, 0, 255), cv2.MARKER_TILTED_CROSS, 12, 2)
            hit_count += 1

    # 반지름 라벨
    for cx, cy, r in circles:
        cv2.putText(canvas, f"r={r:.0f}",
                    (int(cx + r * 0.7), int(cy - r * 0.7)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (67, 160, 71), 1)

    total_dirs = len(circles) * 4
    pil = add_header(
        canvas,
        f"{name.upper()} — Cardinal Projection v3 (ALT)",
        f"동심원 {len(circles)}개 × 4방향 = {total_dirs}개 투사 | "
        f"화살촉 히트: {hit_count}/{total_dirs}",
        f"GT: OD={gt['od']} ID={gt['id']} | "
        f"화살촉 후보: {len(arrows)}개",
    )
    return pil


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
        h, w = gray.shape
        min_r = int(min(h, w) * MIN_R_RATIO)
        max_r = int(min(h, w) * MAX_R_RATIO)

        # 1. 동심원 검출
        circles = detect_concentric_alt(gray, min_r, max_r)
        print(f"  동심원: {len(circles)}개")
        for cx, cy, r in circles:
            print(f"    ({cx:.0f},{cy:.0f}) r={r:.0f}")

        # 2. 화살촉 검출
        arrows = detect_arrowheads_morphology(gray)
        print(f"  화살촉 후보: {len(arrows)}개")

        # 3. Cardinal Projection
        projections = cardinal_projection(circles, arrows, gray)
        total_hits = sum(len(p["hits"]) for p in projections)
        # 끝점 4개 × 직선 2개(수평+수직) = 8개 직선/원, × 원 수
        total_lines = len(circles) * 4 * 2
        print(f"  Cardinal 히트: {total_hits} (끝점 {len(circles)*4}개 × 직선2 = {total_lines}개 직선)")

        for proj in projections:
            if proj["hits"]:
                hits_str = ", ".join(
                    f"{h['direction']}-{h['line']}({h['dist']:.0f}px)"
                    for h in proj["hits"]
                )
                print(f"    r={proj['r']:.0f}: {hits_str}")

        # 4. 시각화
        pil = visualize_cardinal(img, circles, arrows, projections, name, gt)
        save_pil(pil, f"{name}_cardinal_v3.jpg")

        summary.append({
            "name": name,
            "circles": len(circles),
            "arrows": len(arrows),
            "total_dirs": len(circles) * 4,
            "hits": total_hits,
            "hit_rate": f"{total_hits}/{len(circles) * 4}",
        })

    # 요약
    print("\n" + "=" * 60)
    print("전체 요약")
    print(f"{'도면':>6} {'동심원':>6} {'화살촉':>6} {'히트':>10}")
    for s in summary:
        print(f"{s['name'].upper():>6} {s['circles']:>6} "
              f"{s['arrows']:>6} {s['hit_rate']:>10}")

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
