#!/usr/bin/env python3
"""OpenCV 기반 OD/ID/W 분류 실험

3가지 접근법 비교:
  1. Hough Circle Detection — 동심원에서 OD/ID 추출
  2. Ø 기호 기반 OCR 필터 — 확실한 지름 치수만 추출
  3. 단면도 윤곽 분석 — 외곽/내부 사각형에서 OD/ID/W 추출

Usage:
    python3 experiment_opencv_odidw.py /tmp/dse-samples/TD0062051.png
    python3 experiment_opencv_odidw.py /tmp/dse-samples/  # 전체
"""

import cv2
import numpy as np
import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict


# ================================================================
# 실험 1: Hough Circle Detection
# ================================================================

def detect_concentric_circles(
    image_path: str,
    debug_dir: Optional[str] = None,
) -> Dict:
    """정면도(Front View)에서 동심원 검출 → OD/ID 추정

    베어링 도면의 정면도는 보통 큰 동심원이 있음.
    가장 큰 원 → OD, 두 번째 큰 원 → ID (있으면)
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"method": "hough_circle", "error": "이미지 로드 실패"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # 전처리: 블러 + 이진화
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)

    # Hough Circle 검출
    # param1: Canny edge 상한, param2: 중심 투표 임계값
    # minRadius/maxRadius: 이미지 크기 대비 비율로 설정
    min_r = int(min(h, w) * 0.05)   # 최소 5%
    max_r = int(min(h, w) * 0.45)   # 최대 45%

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=int(min(h, w) * 0.1),  # 원 간 최소 거리
        param1=80,
        param2=60,
        minRadius=min_r,
        maxRadius=max_r,
    )

    result = {
        "method": "hough_circle",
        "image": os.path.basename(image_path),
        "image_size": (w, h),
        "circles_found": 0,
        "concentric_groups": [],
    }

    if circles is None:
        # param2를 낮춰서 재시도
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1.5,
            minDist=int(min(h, w) * 0.08),
            param1=60, param2=40,
            minRadius=min_r, maxRadius=max_r,
        )
        if circles is None:
            return result

    circles = np.round(circles[0]).astype(int)
    result["circles_found"] = len(circles)

    # 동심원 그룹 찾기: 중심이 가까운 원들을 그룹화
    center_threshold = int(min(h, w) * 0.05)  # 중심 거리 5% 이내
    groups = _group_concentric(circles, center_threshold)

    for group in groups:
        if len(group) < 2:
            continue
        # 반지름 기준 정렬 (큰 순)
        group.sort(key=lambda c: c[2], reverse=True)
        outer_r = group[0][2]
        inner_r = group[1][2] if len(group) > 1 else None

        result["concentric_groups"].append({
            "center": (int(group[0][0]), int(group[0][1])),
            "outer_radius_px": int(outer_r),
            "inner_radius_px": int(inner_r) if inner_r else None,
            "count": len(group),
            "ratio": round(inner_r / outer_r, 3) if inner_r else None,
        })

    # 디버그 이미지 저장
    if debug_dir:
        debug_img = img.copy()
        for cx, cy, r in circles:
            cv2.circle(debug_img, (cx, cy), r, (0, 255, 0), 2)
            cv2.circle(debug_img, (cx, cy), 3, (0, 0, 255), -1)
        for g in groups:
            if len(g) >= 2:
                cx, cy = int(g[0][0]), int(g[0][1])
                cv2.putText(debug_img, f"OD_r={g[0][2]}", (cx+10, cy-20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)
                cv2.putText(debug_img, f"ID_r={g[1][2]}", (cx+10, cy+30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        os.makedirs(debug_dir, exist_ok=True)
        name = Path(image_path).stem
        cv2.imwrite(f"{debug_dir}/{name}_circles.png", debug_img)

    return result


def _group_concentric(
    circles: np.ndarray,
    threshold: int,
) -> List[List]:
    """중심이 가까운 원들을 그룹화"""
    used = set()
    groups = []
    for i, (cx1, cy1, r1) in enumerate(circles):
        if i in used:
            continue
        group = [(cx1, cy1, r1)]
        used.add(i)
        for j, (cx2, cy2, r2) in enumerate(circles):
            if j in used:
                continue
            dist = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
            if dist < threshold:
                group.append((cx2, cy2, r2))
                used.add(j)
        groups.append(group)
    # 원이 많은 그룹을 앞으로
    groups.sort(key=lambda g: len(g), reverse=True)
    return groups


# ================================================================
# 실험 2: Ø 기호 기반 OCR 필터
# ================================================================

def detect_diameter_symbols(
    image_path: str,
    debug_dir: Optional[str] = None,
) -> Dict:
    """Ø 기호(지름 표시)의 위치를 템플릿 매칭으로 검출

    Ø 기호 근처의 숫자 → 확실한 지름(OD 또는 ID)
    가장 큰 Ø값 → OD, 두번째 → ID
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"method": "diameter_symbol", "error": "이미지 로드 실패"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Ø 기호를 직접 찾기는 어려우므로,
    # 원+사선 패턴을 Hough + 형태학으로 검출
    # 대안: 작은 원(Ø의 O 부분) 검출
    small_circles = cv2.HoughCircles(
        cv2.GaussianBlur(gray, (3, 3), 1),
        cv2.HOUGH_GRADIENT,
        dp=1.0,
        minDist=20,
        param1=100,
        param2=25,
        minRadius=3,
        maxRadius=15,
    )

    result = {
        "method": "diameter_symbol",
        "image": os.path.basename(image_path),
        "small_circles": 0,
        "phi_candidates": [],
    }

    if small_circles is not None:
        small_circles = np.round(small_circles[0]).astype(int)
        result["small_circles"] = len(small_circles)

        # Ø 기호는 작은 원 + 사선으로 구성
        # 사선 존재 여부 확인 (원 주변 ROI에서 대각선 검출)
        for cx, cy, r in small_circles:
            roi_pad = max(r * 3, 10)
            y1 = max(0, cy - roi_pad)
            y2 = min(h, cy + roi_pad)
            x1 = max(0, cx - roi_pad)
            x2 = min(w, cx + roi_pad)
            roi = gray[y1:y2, x1:x2]

            if roi.size == 0:
                continue

            # 사선 검출 (Ø의 슬래시)
            edges = cv2.Canny(roi, 50, 150)
            lines = cv2.HoughLinesP(
                edges, 1, np.pi / 180, 5, None, r, 5,
            )
            if lines is not None:
                for line in lines:
                    lx1, ly1, lx2, ly2 = line[0]
                    angle = abs(np.arctan2(ly2 - ly1, lx2 - lx1) * 180 / np.pi)
                    # 대각선 (30~60도 또는 120~150도)
                    if 25 < angle < 65 or 115 < angle < 155:
                        result["phi_candidates"].append({
                            "center": (int(cx), int(cy)),
                            "radius": int(r),
                        })
                        break

    if debug_dir:
        debug_img = img.copy()
        for cand in result["phi_candidates"]:
            cx, cy = cand["center"]
            r = cand["radius"]
            cv2.circle(debug_img, (cx, cy), r + 5, (0, 0, 255), 2)
            cv2.putText(debug_img, "Phi?", (cx + 10, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        os.makedirs(debug_dir, exist_ok=True)
        name = Path(image_path).stem
        cv2.imwrite(f"{debug_dir}/{name}_phi.png", debug_img)

    return result


# ================================================================
# 실험 3: 단면도 윤곽 분석
# ================================================================

def detect_section_contours(
    image_path: str,
    debug_dir: Optional[str] = None,
) -> Dict:
    """단면도(Section View)에서 외곽 윤곽 검출 → OD/ID/W 추정

    단면도는 보통 직사각형+내부 공간 구조.
    - 외곽 사각형의 가로폭 → OD 관련
    - 외곽 사각형의 세로폭 → W 관련
    - 내부 공간의 가로폭 → ID 관련
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"method": "section_contour", "error": "이미지 로드 실패"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # 이진화 (도면은 보통 흰 배경 + 검은 선)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # 노이즈 제거
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # 윤곽 검출
    contours, hierarchy = cv2.findContours(
        binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE,
    )

    result = {
        "method": "section_contour",
        "image": os.path.basename(image_path),
        "total_contours": len(contours),
        "large_rects": [],
        "nested_rects": [],
    }

    if not contours:
        return result

    # 큰 사각형 윤곽 필터링 (이미지 면적의 1%~80%)
    min_area = h * w * 0.01
    max_area = h * w * 0.80
    rects = []
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if min_area < area < max_area:
            x, y, rw, rh = cv2.boundingRect(cnt)
            aspect = rw / rh if rh > 0 else 0
            # 너무 가늘거나 너무 넓은 건 제외
            if 0.15 < aspect < 7.0:
                rect_info = {
                    "index": i,
                    "bbox": (x, y, rw, rh),
                    "area": int(area),
                    "aspect_ratio": round(aspect, 2),
                    "width_px": rw,
                    "height_px": rh,
                }
                rects.append(rect_info)

    # 면적순 정렬
    rects.sort(key=lambda r: r["area"], reverse=True)
    result["large_rects"] = rects[:10]

    # 포함 관계 분석 (nested rectangles → OD 외곽 / ID 내부)
    if hierarchy is not None and len(rects) >= 2:
        hier = hierarchy[0]
        for outer in rects[:5]:
            oi = outer["index"]
            ox, oy, ow, oh = outer["bbox"]
            children = []
            # hierarchy: [next, prev, first_child, parent]
            child_idx = hier[oi][2]
            while child_idx >= 0:
                cx, cy, cw, ch = cv2.boundingRect(contours[child_idx])
                child_area = cv2.contourArea(contours[child_idx])
                if child_area > min_area * 0.5:
                    children.append({
                        "bbox": (cx, cy, cw, ch),
                        "area": int(child_area),
                        "width_px": cw,
                        "height_px": ch,
                    })
                child_idx = hier[child_idx][0]

            if children:
                result["nested_rects"].append({
                    "outer": outer,
                    "inner_count": len(children),
                    "largest_inner": max(children, key=lambda c: c["area"]),
                })

    # 디버그 이미지
    if debug_dir:
        debug_img = img.copy()
        for i, rect in enumerate(rects[:5]):
            x, y, rw, rh = rect["bbox"]
            color = [(0, 255, 0), (255, 0, 0), (0, 0, 255),
                     (255, 255, 0), (255, 0, 255)][i % 5]
            cv2.rectangle(debug_img, (x, y), (x + rw, y + rh), color, 2)
            cv2.putText(debug_img, f"#{i} {rw}x{rh}",
                        (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, color, 2)

        os.makedirs(debug_dir, exist_ok=True)
        name = Path(image_path).stem
        cv2.imwrite(f"{debug_dir}/{name}_contours.png", debug_img)

    return result


# ================================================================
# 실험 4: 치수선 검출 (Dimension Lines)
# ================================================================

def detect_dimension_lines(
    image_path: str,
    debug_dir: Optional[str] = None,
) -> Dict:
    """치수선(화살표 + 직선 + 숫자) 검출

    수평 치수선 → 지름(OD/ID) 후보
    수직 치수선 → 폭(W) 후보
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"method": "dimension_lines", "error": "이미지 로드 실패"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # 엣지 검출
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # 직선 검출
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, 80, None,
        int(min(h, w) * 0.05), 10,
    )

    result = {
        "method": "dimension_lines",
        "image": os.path.basename(image_path),
        "total_lines": 0,
        "horizontal_lines": [],
        "vertical_lines": [],
    }

    if lines is None:
        return result

    result["total_lines"] = len(lines)

    h_lines = []
    v_lines = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

        if angle < 5 or angle > 175:  # 수평
            h_lines.append({
                "start": (int(x1), int(y1)),
                "end": (int(x2), int(y2)),
                "length_px": int(length),
                "y_pos": int((y1 + y2) / 2),
            })
        elif 85 < angle < 95:  # 수직
            v_lines.append({
                "start": (int(x1), int(y1)),
                "end": (int(x2), int(y2)),
                "length_px": int(length),
                "x_pos": int((x1 + x2) / 2),
            })

    # 길이순 정렬
    h_lines.sort(key=lambda l: l["length_px"], reverse=True)
    v_lines.sort(key=lambda l: l["length_px"], reverse=True)

    result["horizontal_lines"] = h_lines[:15]
    result["vertical_lines"] = v_lines[:15]

    # 디버그 이미지
    if debug_dir:
        debug_img = img.copy()
        for hl in h_lines[:10]:
            cv2.line(debug_img, hl["start"], hl["end"], (0, 0, 255), 2)
        for vl in v_lines[:10]:
            cv2.line(debug_img, vl["start"], vl["end"], (255, 0, 0), 2)

        os.makedirs(debug_dir, exist_ok=True)
        name = Path(image_path).stem
        cv2.imwrite(f"{debug_dir}/{name}_dimlines.png", debug_img)

    return result


# ================================================================
# 통합 실행
# ================================================================

def run_all_experiments(image_path: str, debug_dir: str = "/tmp/dse-debug"):
    """모든 실험을 실행하고 결과 비교"""
    print(f"\n{'='*60}")
    print(f"  도면: {os.path.basename(image_path)}")
    print(f"{'='*60}")

    # 1. Hough Circle
    r1 = detect_concentric_circles(image_path, debug_dir)
    print(f"\n[1] Hough Circle Detection")
    print(f"    검출된 원: {r1['circles_found']}개")
    for g in r1.get("concentric_groups", []):
        print(f"    동심원 그룹: {g['count']}개 원, "
              f"외경_r={g['outer_radius_px']}px, "
              f"내경_r={g['inner_radius_px']}px, "
              f"비율={g['ratio']}")

    # 2. Ø 기호
    r2 = detect_diameter_symbols(image_path, debug_dir)
    print(f"\n[2] Ø 기호 검출")
    print(f"    작은 원: {r2['small_circles']}개, "
          f"Ø 후보: {len(r2['phi_candidates'])}개")

    # 3. 단면도 윤곽
    r3 = detect_section_contours(image_path, debug_dir)
    print(f"\n[3] 단면도 윤곽 분석")
    print(f"    전체 윤곽: {r3['total_contours']}개, "
          f"큰 사각형: {len(r3['large_rects'])}개")
    for nr in r3.get("nested_rects", [])[:3]:
        outer = nr["outer"]
        inner = nr["largest_inner"]
        print(f"    외곽: {outer['width_px']}×{outer['height_px']}px, "
              f"내부: {inner['width_px']}×{inner['height_px']}px")

    # 4. 치수선
    r4 = detect_dimension_lines(image_path, debug_dir)
    print(f"\n[4] 치수선 검출")
    print(f"    전체: {r4['total_lines']}개 직선, "
          f"수평: {len(r4['horizontal_lines'])}개, "
          f"수직: {len(r4['vertical_lines'])}개")
    if r4["horizontal_lines"]:
        top3 = r4["horizontal_lines"][:3]
        print(f"    수평 Top3: {[l['length_px'] for l in top3]}px")
    if r4["vertical_lines"]:
        top3 = r4["vertical_lines"][:3]
        print(f"    수직 Top3: {[l['length_px'] for l in top3]}px")

    print(f"\n    디버그 이미지 → {debug_dir}/")
    return {"circle": r1, "phi": r2, "contour": r3, "dimline": r4}


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/tmp/dse-samples/"

    if os.path.isdir(target):
        images = sorted(Path(target).glob("*.png"))
        print(f"총 {len(images)}개 도면 분석")
        for img_path in images:
            run_all_experiments(str(img_path))
    else:
        run_all_experiments(target)

    print(f"\n{'='*60}")
    print("완료! 디버그 이미지 확인: /tmp/dse-debug/")
    print(f"{'='*60}")
