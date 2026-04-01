#!/usr/bin/env python3
"""S08 — Cardinal Projection: 원 끝점 → 화살촉 → 치수선 → Ø/R 판별

알고리즘:
1. 원 검출 (K방법 — Contour + HoughCircles)
2. 각 원의 N/S/E/W 끝점에서 방사 방향으로 직선 투사
3. 투사선이 화살촉과 만나는지 확인 (S01 arrowhead detector)
4. 화살촉 → 치수선 추적 → 반대쪽 화살촉 찾기
5. 반대쪽 화살촉도 같은 원 위 → Ø(직경), 아니면 → R(반지름) ×2
6. 치수선 근처 OCR → 값 추출
7. 화살촉과 안 만나는 원 → 버림
"""

import cv2
import numpy as np
import sys
import os
import json
import requests
import io
from pathlib import Path
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from services.arrowhead_detector import detect_arrowheads, match_arrowhead_pairs

SRC_DIR = Path(__file__).parent / ".." / "data" / "dse_batch_test" / "converted_pngs"
OUT_DIR = Path(__file__).parent / ".." / ".." / "docs-site-starlight" / "public" / "images" / "experiments"
PADDLE_URL = "http://localhost:5006/api/v1/ocr"

GT = {
    "TD0062015": {"name": "T1", "od": 360, "id": 190, "w": 200},
    "TD0062037": {"name": "T5", "od": 1036, "id": 580, "w": 200},
}


def paddle_ocr(img_pil):
    buf = io.BytesIO()
    img_pil.convert("RGB").save(buf, format="JPEG", quality=90)
    try:
        resp = requests.post(PADDLE_URL, files={"file": ("img.jpg", buf.getvalue(), "image/jpeg")}, timeout=60)
        resp.raise_for_status()
        return resp.json().get("detections", [])
    except:
        return []


def detect_circles(gray):
    """K방법 원 검출 — Contour + HoughCircles"""
    h, w = gray.shape
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    circles = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < (min(h, w) * 0.05) ** 2:
            continue
        perimeter = cv2.arcLength(cnt, True)
        if perimeter < 1:
            continue
        circularity = 4 * np.pi * area / (perimeter ** 2)
        if circularity < 0.3:
            continue
        if len(cnt) >= 5:
            ellipse = cv2.fitEllipse(cnt)
            (cx, cy), (ma, mi), angle = ellipse
            if min(ma, mi) > 0 and max(ma, mi) / min(ma, mi) < 2.0:
                r = (ma + mi) / 4
                circles.append({"cx": cx, "cy": cy, "r": r, "circularity": circularity, "area": area})

    # HoughCircles 폴백
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    hough = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.5,
                              minDist=max(h, w) // 10,
                              param1=100, param2=60,
                              minRadius=max(h, w) // 20,
                              maxRadius=max(h, w) // 3)
    if hough is not None:
        for cx, cy, r in np.round(hough[0]).astype(int):
            # 중복 체크
            dup = any(abs(c["cx"] - cx) < r * 0.3 and abs(c["cy"] - cy) < r * 0.3 for c in circles)
            if not dup:
                circles.append({"cx": float(cx), "cy": float(cy), "r": float(r),
                                "circularity": 0.8, "area": np.pi * r * r})

    # 크기순 정렬
    circles.sort(key=lambda c: c["r"], reverse=True)
    return circles[:20]  # 상위 20개


def filter_concentric_circles(circles, gray):
    """동심 원 필터링 — 정면도(좌측 50%) 내 동심 그룹만 선택"""
    h, w = gray.shape
    front_x_limit = w * 0.55  # 정면도 영역

    # 정면도 내 원만
    front_circles = [c for c in circles if c["cx"] < front_x_limit]
    if not front_circles:
        return circles[:5]

    # 동심 그룹핑 (중심 거리 < 작은 원 반지름의 30%)
    groups = []
    used = set()
    for i, c1 in enumerate(front_circles):
        if i in used:
            continue
        group = [c1]
        used.add(i)
        for j, c2 in enumerate(front_circles):
            if j in used:
                continue
            dist = np.sqrt((c1["cx"] - c2["cx"]) ** 2 + (c1["cy"] - c2["cy"]) ** 2)
            min_r = min(c1["r"], c2["r"])
            if dist < min_r * 0.5:
                group.append(c2)
                used.add(j)
        groups.append(group)

    # 가장 큰 그룹 선택
    groups.sort(key=lambda g: len(g), reverse=True)
    best_group = groups[0] if groups else front_circles[:3]

    # 크기순 정렬
    best_group.sort(key=lambda c: c["r"], reverse=True)
    return best_group[:8]


def cardinal_projection(circles, arrowheads, pairs, gray, img_pil, tolerance_px=30):
    """Cardinal Projection v2 — 엄격한 tolerance + 중복 제거

    v1 대비 변경:
    - tolerance: r × 0.15 → 고정 30px (화살촉이 끝점에 정확히 위치해야)
    - 동심 필터: 정면도 내 동심 원만 사용
    - 중복 제거: 같은 치수선은 가장 근접한 원에만 배정
    - Ø 텍스트 우선: OCR에서 Ø 기호 매칭 가산점
    """
    h, w = gray.shape
    results = []

    arrow_pts = np.array([[a["x"], a["y"]] for a in arrowheads], dtype=np.float32) if arrowheads else np.zeros((0, 2))

    pair_map = {}
    for pair in pairs:
        si, ei = pair["start_idx"], pair["end_idx"]
        pair_map[si] = pair
        pair_map[ei] = pair

    # OCR
    ocr_dets = paddle_ocr(img_pil)
    ocr_nums = []
    import re
    for d in ocr_dets:
        text = d.get("text", "")
        bbox = d.get("bbox", [])
        m = re.search(r"[Øø]?\s*(\d+\.?\d*)", re.sub(r"[()]", "", text))
        if m and isinstance(bbox, list) and len(bbox) >= 4 and isinstance(bbox[0], list):
            val = float(m.group(1))
            if 10 < val < 3000:
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                ocr_nums.append({
                    "value": val, "text": text,
                    "cx": sum(xs) / len(xs), "cy": sum(ys) / len(ys),
                    "has_phi": bool(re.search(r"[Øø]", text)),
                })

    used_pairs = set()  # 중복 방지

    for ci, circle in enumerate(circles):
        cx, cy, r = circle["cx"], circle["cy"], circle["r"]
        tol = min(tolerance_px, r * 0.08)  # 30px 또는 r의 8% 중 작은 값

        # N/S/E/W + 45도 방향 (8방향)
        cardinals = {}
        for angle, name in [(0, "E"), (90, "S"), (180, "W"), (270, "N"),
                            (45, "SE"), (135, "SW"), (225, "NW"), (315, "NE")]:
            rad = np.radians(angle)
            cardinals[name] = (cx + r * np.cos(rad), cy + r * np.sin(rad))

        circle_matches = []

        for dir_name, (px, py) in cardinals.items():
            if px < 0 or py < 0 or px >= w or py >= h:
                continue
            if len(arrow_pts) == 0:
                continue

            dists = np.sqrt((arrow_pts[:, 0] - px) ** 2 + (arrow_pts[:, 1] - py) ** 2)
            near_indices = np.where(dists < tol)[0]

            for ai in near_indices:
                if ai not in pair_map:
                    continue
                pair = pair_map[ai]
                pair_key = (min(pair["start_idx"], pair["end_idx"]),
                            max(pair["start_idx"], pair["end_idx"]))
                if pair_key in used_pairs:
                    continue

                arrow = arrowheads[ai]
                other_idx = pair["end_idx"] if pair["start_idx"] == ai else pair["start_idx"]
                other = arrowheads[other_idx]
                ox, oy = other["x"], other["y"]

                # 반대쪽 판정
                other_r_dist = abs(np.sqrt((ox - cx) ** 2 + (oy - cy) ** 2) - r)
                on_circle = other_r_dist < tol
                dist_to_center = np.sqrt((ox - cx) ** 2 + (oy - cy) ** 2)
                near_center = dist_to_center < r * 0.3

                if on_circle:
                    dim_type = "DIAMETER"
                elif near_center:
                    dim_type = "RADIUS"
                else:
                    # 치수선 길이가 2r 근처면 직경 가능성
                    if abs(pair["length"] - 2 * r) < r * 0.3:
                        dim_type = "DIAMETER"
                    elif abs(pair["length"] - r) < r * 0.3:
                        dim_type = "RADIUS"
                    else:
                        dim_type = "UNKNOWN"

                if dim_type == "UNKNOWN":
                    continue

                line_len = pair["length"]
                mid_x = (arrow["x"] + ox) / 2
                mid_y = (arrow["y"] + oy) / 2

                # OCR 매칭 (Ø 우선)
                best_ocr = None
                best_score = float("inf")
                for ocr in ocr_nums:
                    d = np.sqrt((ocr["cx"] - mid_x) ** 2 + (ocr["cy"] - mid_y) ** 2)
                    if d < line_len * 1.0:
                        score = d - (200 if ocr["has_phi"] else 0)  # Ø 보너스
                        if score < best_score:
                            best_score = score
                            best_ocr = ocr

                used_pairs.add(pair_key)
                circle_matches.append({
                    "direction": dir_name,
                    "dim_type": dim_type,
                    "arrow_pos": (arrow["x"], arrow["y"]),
                    "other_pos": (ox, oy),
                    "line_length": line_len,
                    "ocr_value": best_ocr["value"] if best_ocr else None,
                    "ocr_text": best_ocr["text"] if best_ocr else None,
                    "ocr_has_phi": best_ocr["has_phi"] if best_ocr else False,
                    "distance_to_cardinal": float(dists[ai]),
                })

        if circle_matches:
            results.append({
                "circle_idx": ci,
                "cx": cx, "cy": cy, "r": r,
                "matches": circle_matches,
            })

    return results


def classify_dimensions(projection_results):
    """투사 결과에서 OD/ID 추출"""
    diameters = []

    for pr in projection_results:
        for m in pr["matches"]:
            if m["ocr_value"] is None:
                continue
            val = m["ocr_value"]
            if m["dim_type"] == "DIAMETER":
                diameters.append({"value": val, "type": "Ø", "circle_r": pr["r"], "text": m["ocr_text"]})
            elif m["dim_type"] == "RADIUS":
                diameters.append({"value": val * 2, "type": "R×2", "circle_r": pr["r"], "text": m["ocr_text"]})

    # 크기순 정렬
    diameters.sort(key=lambda d: d["value"], reverse=True)

    od = diameters[0]["value"] if len(diameters) > 0 else None
    id_val = diameters[1]["value"] if len(diameters) > 1 else None

    return {"od": od, "id": id_val, "all_diameters": diameters}


def visualize(img, circles, arrowheads, pairs, projection_results, name, gt, out_path):
    """결과 시각화"""
    canvas = img.copy()
    h, w = canvas.shape[:2]

    # 1. 원 표시 (파란 점선)
    for ci, c in enumerate(circles[:10]):
        cx, cy, r = int(c["cx"]), int(c["cy"]), int(c["r"])
        # 점선 원
        for angle in range(0, 360, 5):
            a = np.radians(angle)
            px, py = int(cx + r * np.cos(a)), int(cy + r * np.sin(a))
            cv2.circle(canvas, (px, py), 1, (255, 150, 0), -1)

    # 2. 매칭된 원만 굵게
    matched_circles = {pr["circle_idx"] for pr in projection_results}
    for pr in projection_results:
        c = circles[pr["circle_idx"]]
        cx, cy, r = int(c["cx"]), int(c["cy"]), int(c["r"])
        cv2.circle(canvas, (cx, cy), r, (255, 0, 0), 2)

        # 동서남북 끝점 표시
        for dx, dy, label in [(0, -1, "N"), (0, 1, "S"), (1, 0, "E"), (-1, 0, "W")]:
            px, py = int(cx + r * dx), int(cy + r * dy)
            cv2.circle(canvas, (px, py), 6, (0, 200, 200), -1)

        # 매칭된 치수선
        for m in pr["matches"]:
            ax, ay = int(m["arrow_pos"][0]), int(m["arrow_pos"][1])
            ox, oy = int(m["other_pos"][0]), int(m["other_pos"][1])

            if m["dim_type"] == "DIAMETER":
                color = (0, 255, 0)  # 녹색 = 직경
                label = f"D={m['ocr_value']}" if m["ocr_value"] else "D=?"
            elif m["dim_type"] == "RADIUS":
                color = (0, 165, 255)  # 주황 = 반지름
                label = f"R={m['ocr_value']}(x2)" if m["ocr_value"] else "R=?"
            else:
                color = (128, 128, 128)
                label = "?"

            cv2.line(canvas, (ax, ay), (ox, oy), color, 2)
            cv2.circle(canvas, (ax, ay), 5, (0, 0, 255), -1)
            cv2.circle(canvas, (ox, oy), 5, (0, 0, 255), -1)

            mid_x, mid_y = (ax + ox) // 2, (ay + oy) // 2
            cv2.putText(canvas, label, (mid_x + 10, mid_y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # 3. 버려진 원 (회색 X)
    for ci, c in enumerate(circles[:10]):
        if ci not in matched_circles:
            cx, cy = int(c["cx"]), int(c["cy"])
            sz = 15
            cv2.line(canvas, (cx - sz, cy - sz), (cx + sz, cy + sz), (128, 128, 128), 2)
            cv2.line(canvas, (cx - sz, cy + sz), (cx + sz, cy - sz), (128, 128, 128), 2)

    # 4. 헤더
    classified = classify_dimensions(projection_results)
    od_str = f"OD={classified['od']}" if classified["od"] else "OD=?"
    id_str = f"ID={classified['id']}" if classified["id"] else "ID=?"
    header = f"S08 Cardinal — {name} (GT: OD={gt['od']} ID={gt['id']}) => {od_str} {id_str}"
    cv2.putText(canvas, header, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 3)
    cv2.putText(canvas, header, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 1)

    # 5. 범례
    y_leg = h - 100
    legend = [
        ("Blue circle = matched", (255, 0, 0)),
        ("Green line = Diameter", (0, 255, 0)),
        ("Orange line = Radius", (0, 165, 255)),
        ("Cyan dot = Cardinal point", (0, 200, 200)),
        ("Gray X = discarded circle", (128, 128, 128)),
    ]
    for i, (text, color) in enumerate(legend):
        cv2.putText(canvas, text, (20, y_leg + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    # 축소 저장
    if canvas.shape[1] > 1400:
        ratio = 1400 / canvas.shape[1]
        canvas = cv2.resize(canvas, (1400, int(canvas.shape[0] * ratio)))

    cv2.imwrite(str(out_path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return classified


def run_experiment(drawing_no, gt_info):
    """단일 도면 실험"""
    name = gt_info["name"]
    print(f"\n{'='*60}")
    print(f"  {name} ({drawing_no}) — GT: OD={gt_info['od']} ID={gt_info['id']} W={gt_info['w']}")
    print(f"{'='*60}")

    img = cv2.imread(str(SRC_DIR / f"{drawing_no}.png"))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    img_pil = Image.open(str(SRC_DIR / f"{drawing_no}.png"))

    # 1. 원 검출 + 동심 필터
    all_circles = detect_circles(gray)
    circles = filter_concentric_circles(all_circles, gray)
    print(f"  [1] 원 검출: {len(all_circles)}개 → 동심 필터: {len(circles)}개 (r={[int(c['r']) for c in circles]})")

    # 2. 화살촉 검출
    arrowheads = detect_arrowheads(gray)
    print(f"  [2] 화살촉: {len(arrowheads)}개")

    # 3. 치수선 쌍 매칭
    # LSD 선 검출
    lsd = cv2.createLineSegmentDetector(0)
    lines_raw, _, _, _ = lsd.detect(gray)
    lsd_lines = []
    if lines_raw is not None:
        for line in lines_raw:
            x1, y1, x2, y2 = line[0]
            lsd_lines.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})

    # 화살촉에 인덱스 추가
    for i, a in enumerate(arrowheads):
        a["idx"] = i

    pairs = match_arrowhead_pairs(arrowheads, lsd_lines)
    # 쌍에 인덱스 매핑 추가
    for pair in pairs:
        s = pair["start"]
        e = pair["end"]
        pair["start_idx"] = next((i for i, a in enumerate(arrowheads)
                                   if abs(a["x"] - s["x"]) < 1 and abs(a["y"] - s["y"]) < 1), -1)
        pair["end_idx"] = next((i for i, a in enumerate(arrowheads)
                                 if abs(a["x"] - e["x"]) < 1 and abs(a["y"] - e["y"]) < 1), -1)
    pairs = [p for p in pairs if p["start_idx"] >= 0 and p["end_idx"] >= 0]
    print(f"  [3] 치수선 쌍: {len(pairs)}개")

    # 4. Cardinal Projection
    results = cardinal_projection(circles, arrowheads, pairs, gray, img_pil)
    total_matches = sum(len(pr["matches"]) for pr in results)
    print(f"  [4] Cardinal 매칭: {len(results)}개 원에서 {total_matches}개 매칭")

    # 5. 분류
    classified = classify_dimensions(results)
    od = classified["od"]
    id_val = classified["id"]
    print(f"  [5] 분류: OD={od} ID={id_val}")
    diam_strs = [f"{d['value']:.0f}({d['type']})" for d in classified['all_diameters']]
    print(f"       전체 직경: {diam_strs}")

    # 6. 판정
    od_ok = od is not None and abs(od - gt_info["od"]) < gt_info["od"] * 0.05
    id_ok = id_val is not None and abs(id_val - gt_info["id"]) < gt_info["id"] * 0.05
    print(f"  [6] OD={'✓' if od_ok else '✗'} ID={'✓' if id_ok else '✗'}")

    # 7. 시각화
    vis_path = OUT_DIR / f"s08_{name.lower()}_cardinal.jpg"
    visualize(img, circles, arrowheads, pairs, results, name, gt_info, vis_path)
    print(f"  [7] 저장: {vis_path.name}")

    return {
        "name": name, "drawing_no": drawing_no,
        "circles": len(circles), "arrowheads": len(arrowheads), "pairs": len(pairs),
        "matched_circles": len(results), "total_matches": total_matches,
        "od": od, "id": id_val,
        "gt_od": gt_info["od"], "gt_id": gt_info["id"],
        "od_ok": od_ok, "id_ok": id_ok,
        "all_diameters": classified["all_diameters"],
    }


if __name__ == "__main__":
    print("=" * 60)
    print("  S08 — Cardinal Projection 실험")
    print("=" * 60)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []

    for drawing_no, gt in GT.items():
        result = run_experiment(drawing_no, gt)
        all_results.append(result)

    # 요약
    print(f"\n{'='*60}")
    print("  결과 요약")
    print(f"{'='*60}")
    for r in all_results:
        print(f"  {r['name']}: OD={'✓' if r['od_ok'] else '✗'}({r['od']}) "
              f"ID={'✓' if r['id_ok'] else '✗'}({r['id']})")

    # 결과 저장
    with open(OUT_DIR / "s08_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  결과 저장: s08_results.json")
