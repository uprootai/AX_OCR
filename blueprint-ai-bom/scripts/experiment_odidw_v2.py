#!/usr/bin/env python3
"""OD/ID/W 분류 개선 실험 v2

실용적 접근 3가지:
  A. OCR 텍스트에서 Ø(파이) 기호 필터 → 확실한 지름 추출
  B. 세션명 파싱 → "(OD670×ID440)" 또는 "(500×260)" 패턴
  C. 도면 영역 분리 → 정면도(원형 뷰)만 추출 후 원 검출

Usage:
    python3 experiment_odidw_v2.py
"""

import cv2
import numpy as np
import re
import requests
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple

BASE = "http://localhost:5020"
PROJECT_ID = "b97237fd"


# ================================================================
# 전략 A: OCR Ø 기호 필터링
# ================================================================

def strategy_phi_filter(dimensions: List[Dict]) -> Dict:
    """OCR 결과에서 Ø/φ 기호가 있는 치수만 필터 → OD/ID 확정

    Ø가 붙은 치수는 100% 지름이므로 신뢰도가 높음.
    Ø 없는 치수 중 수직 방향 → W 후보
    """
    phi_dims = []
    non_phi_dims = []

    for d in dimensions:
        raw = d.get("raw_text", "") or d.get("value", "")
        value_str = d.get("value", "")

        # Ø/φ/Φ/⌀ 기호 포함 여부
        has_phi = bool(re.search(r'[ØφΦ⌀]', raw))

        # 숫자 추출
        num = _extract_number(value_str)
        if num is None or num <= 0:
            num = _extract_number(raw)
        if num is None or num <= 0:
            continue

        bbox = d.get("bbox", {})
        dim_type = d.get("dimension_type", "unknown")

        entry = {
            "value": num,
            "raw": raw[:40],
            "has_phi": has_phi,
            "dim_type": dim_type,
            "bbox": bbox,
            "direction": _get_direction(bbox),
        }

        if has_phi:
            phi_dims.append(entry)
        else:
            non_phi_dims.append(entry)

    # Ø 치수 → 값 기준 정렬 (큰 순)
    phi_dims.sort(key=lambda d: d["value"], reverse=True)

    # 비-Ø 수직 치수 → W 후보
    vertical_dims = [d for d in non_phi_dims if d["direction"] == "vertical"]
    vertical_dims.sort(key=lambda d: d["value"], reverse=True)

    # 비-Ø 수평 치수 (Ø 없지만 큰 수평 치수 → OD/ID 후보)
    horizontal_dims = [d for d in non_phi_dims if d["direction"] == "horizontal"]
    horizontal_dims.sort(key=lambda d: d["value"], reverse=True)

    # OD/ID/W 결정
    od = phi_dims[0]["value"] if len(phi_dims) >= 1 else None
    id_ = phi_dims[1]["value"] if len(phi_dims) >= 2 else None
    w = vertical_dims[0]["value"] if vertical_dims else None

    # Ø가 없으면 수평 치수에서 보완
    if od is None and horizontal_dims:
        od = horizontal_dims[0]["value"]
    if id_ is None and len(horizontal_dims) >= 2:
        id_ = horizontal_dims[1]["value"]

    return {
        "strategy": "phi_filter",
        "od": od,
        "id": id_,
        "w": w,
        "phi_count": len(phi_dims),
        "phi_values": [d["value"] for d in phi_dims[:5]],
        "vertical_values": [d["value"] for d in vertical_dims[:5]],
        "horizontal_values": [d["value"] for d in horizontal_dims[:5]],
        "confidence": "high" if len(phi_dims) >= 2 else "medium" if phi_dims else "low",
    }


def _extract_number(text: str) -> Optional[float]:
    """텍스트에서 숫자 추출"""
    if not text:
        return None
    # Ø, 공백 등 제거하고 첫 번째 숫자 패턴 추출
    cleaned = re.sub(r'[ØφΦ⌀\s]', '', text)
    m = re.search(r'(\d+\.?\d*)', cleaned)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def _get_direction(bbox: Dict) -> str:
    """바운딩박스로 치수 방향 판단"""
    if not bbox:
        return "unknown"
    w = abs(bbox.get("x2", 0) - bbox.get("x1", 0))
    h = abs(bbox.get("y2", 0) - bbox.get("y1", 0))
    if w == 0 and h == 0:
        return "unknown"
    ratio = w / max(h, 1)
    if ratio > 2.0:
        return "horizontal"
    elif ratio < 0.5:
        return "vertical"
    return "diagonal"


# ================================================================
# 전략 B: 세션명 패턴 파싱
# ================================================================

def strategy_session_name(session_name: str) -> Dict:
    """세션 이름에서 OD/ID/W 패턴 추출

    패턴 예시:
    - "스러스트베어링 ASSY (OD670×ID440)" → OD=670, ID=440
    - "T8 저널베어링 ASSY (500×260)" → OD=500, W=260 (or ID?)
    - "(420×260)" → 두 숫자
    """
    result = {
        "strategy": "session_name",
        "od": None,
        "id": None,
        "w": None,
        "pattern": None,
    }

    # 패턴 1: OD숫자×ID숫자 (명시적)
    m = re.search(r'OD\s*(\d+)\s*[×xX]\s*ID\s*(\d+)', session_name)
    if m:
        result["od"] = float(m.group(1))
        result["id"] = float(m.group(2))
        result["pattern"] = "explicit_OD_ID"
        return result

    # 패턴 2: (숫자×숫자) — 괄호 안 두 수
    m = re.search(r'\((\d+)\s*[×xX]\s*(\d+)\)', session_name)
    if m:
        v1 = float(m.group(1))
        v2 = float(m.group(2))
        # 큰 쪽이 OD, 작은 쪽이 W(폭) — 저널베어링 관례
        result["od"] = max(v1, v2)
        result["w"] = min(v1, v2)
        result["pattern"] = "parenthesized_pair"
        return result

    # 패턴 3: 숫자×숫자 (괄호 없이)
    m = re.search(r'(\d{3,})\s*[×xX]\s*(\d{2,})', session_name)
    if m:
        v1 = float(m.group(1))
        v2 = float(m.group(2))
        result["od"] = max(v1, v2)
        result["w"] = min(v1, v2)
        result["pattern"] = "inline_pair"
        return result

    return result


# ================================================================
# 전략 C: 도면 영역 분리 + 원형 뷰 검출
# ================================================================

def strategy_region_circle(image_path: str, debug_dir: str = "/tmp/dse-debug") -> Dict:
    """도면을 영역으로 분리하고, 원형 뷰가 있는 영역만 원 검출

    1. 도면 프레임(외곽 사각형) 제거
    2. 큰 빈 공간으로 영역 분리
    3. 각 영역에서 원 검출
    4. 가장 뚜렷한 동심원이 있는 영역 → OD/ID
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"strategy": "region_circle", "error": "이미지 로드 실패"}

    # 리사이즈 (성능)
    max_dim = 2000
    h0, w0 = img.shape[:2]
    scale = min(max_dim / max(h0, w0), 1.0)
    if scale < 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # 프레임(테두리) 영역 제거 — 상하좌우 5% 마진
    margin = int(min(h, w) * 0.05)
    roi = gray[margin:h-margin, margin:w-margin]
    roi_h, roi_w = roi.shape

    # 이진화 + 원 검출 (ROI에서만)
    blurred = cv2.GaussianBlur(roi, (7, 7), 2)

    # 전략: 매우 엄격한 파라미터 → 진짜 원만 검출
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT,
        dp=2.0,
        minDist=int(min(roi_h, roi_w) * 0.2),  # 원 간 20% 거리
        param1=120,
        param2=80,   # 매우 엄격
        minRadius=int(min(roi_h, roi_w) * 0.08),
        maxRadius=int(min(roi_h, roi_w) * 0.42),
    )

    result = {
        "strategy": "region_circle",
        "image": Path(image_path).stem,
        "image_size": (w, h),
        "scale": round(scale, 3),
        "circles_found": 0,
        "best_concentric": None,
    }

    if circles is None:
        return result

    circles = np.round(circles[0]).astype(int)
    result["circles_found"] = len(circles)

    # 동심원 쌍 찾기
    best_pair = None
    best_score = 0

    for i in range(len(circles)):
        cx1, cy1, r1 = circles[i]
        for j in range(i+1, len(circles)):
            cx2, cy2, r2 = circles[j]
            center_dist = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
            # 중심이 가까운 쌍
            if center_dist < min(r1, r2) * 0.3:
                big_r = max(r1, r2)
                small_r = min(r1, r2)
                ratio = small_r / big_r
                # 비율이 0.3~0.9면 OD/ID 쌍일 가능성 높음
                if 0.3 < ratio < 0.9:
                    score = big_r * (1 - abs(ratio - 0.6))  # 0.6 비율에 가까울수록 높은 점수
                    if score > best_score:
                        best_score = score
                        best_pair = {
                            "outer_r_px": int(big_r),
                            "inner_r_px": int(small_r),
                            "center": (int((cx1+cx2)//2) + margin,
                                       int((cy1+cy2)//2) + margin),
                            "ratio": round(ratio, 3),
                            "score": round(score, 1),
                        }

    result["best_concentric"] = best_pair

    # 디버그 이미지
    if debug_dir:
        debug_img = img.copy()
        for cx, cy, r in circles:
            cv2.circle(debug_img, (cx + margin, cy + margin), r, (0, 200, 0), 2)
        if best_pair:
            cx, cy = best_pair["center"]
            cv2.circle(debug_img, (cx, cy), best_pair["outer_r_px"], (0, 0, 255), 3)
            cv2.circle(debug_img, (cx, cy), best_pair["inner_r_px"], (255, 0, 0), 3)
            cv2.putText(debug_img, f"OD_r={best_pair['outer_r_px']}",
                        (cx + 10, cy - 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 0, 255), 2)
            cv2.putText(debug_img, f"ID_r={best_pair['inner_r_px']}",
                        (cx + 10, cy + 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (255, 0, 0), 2)

        Path(debug_dir).mkdir(parents=True, exist_ok=True)
        name = Path(image_path).stem
        cv2.imwrite(f"{debug_dir}/{name}_v2_circles.png", debug_img)

    return result


# ================================================================
# 통합 실행
# ================================================================

def run_experiment():
    """프로젝트 전체 세션에 대해 3가지 전략 비교"""

    # 세션 목록
    sessions = requests.get(
        f"{BASE}/sessions",
        params={"project_id": PROJECT_ID, "limit": 50},
    ).json()

    print(f"{'='*80}")
    print(f"  OD/ID/W 분류 개선 실험 v2 — {len(sessions)}개 세션")
    print(f"{'='*80}")

    for s in sessions:
        sid = s["session_id"]
        fname = s["filename"]
        print(f"\n{'─'*80}")
        print(f"세션: {fname[:70]}")
        print(f"{'─'*80}")

        # 전략 B: 세션명 파싱
        rb = strategy_session_name(fname)
        print(f"\n  [B] 세션명 파싱:")
        print(f"      패턴: {rb['pattern']}")
        print(f"      OD={rb['od']}, ID={rb['id']}, W={rb['w']}")

        # 서브이미지 분석
        try:
            images = requests.get(f"{BASE}/sessions/{sid}/images").json()
        except Exception:
            images = []

        if not images:
            print(f"  (서브이미지 없음)")
            continue

        for img in images[:5]:  # 처음 5개만
            img_fn = img.get("filename", "")
            dims = img.get("dimensions", [])
            current_od = img.get("od")
            current_id = img.get("id")
            current_w = img.get("width")

            print(f"\n  📄 {img_fn} (현재: OD={current_od}, ID={current_id}, W={current_w})")

            # 전략 A: OCR Ø 필터
            if dims:
                ra = strategy_phi_filter(dims)
                print(f"    [A] Ø 필터: OD={ra['od']}, ID={ra['id']}, W={ra['w']} "
                      f"(Ø치수 {ra['phi_count']}개, 신뢰={ra['confidence']})")
                if ra["phi_values"]:
                    print(f"        Ø값들: {ra['phi_values']}")
                if ra["vertical_values"]:
                    print(f"        수직값: {ra['vertical_values'][:5]}")
            else:
                print(f"    [A] (치수 데이터 없음)")

            # 전략 C: 원 검출 (이미지 경로 필요)
            img_path = img.get("file_path", "")
            if img_path:
                # Docker 컨테이너 경로 → 로컬 캐시
                local_path = f"/tmp/dse-samples/{img_fn}"
                if not Path(local_path).exists():
                    try:
                        import subprocess
                        subprocess.run(
                            ["docker", "cp",
                             f"blueprint-ai-bom-backend:{img_path}",
                             local_path],
                            capture_output=True, timeout=10,
                        )
                    except Exception:
                        pass

                if Path(local_path).exists():
                    rc = strategy_region_circle(local_path)
                    bc = rc.get("best_concentric")
                    if bc:
                        print(f"    [C] 동심원: 외경_r={bc['outer_r_px']}px, "
                              f"내경_r={bc['inner_r_px']}px, "
                              f"비율={bc['ratio']}")
                    else:
                        print(f"    [C] 동심원 미검출 (총 {rc['circles_found']}개 원)")


if __name__ == "__main__":
    run_experiment()
