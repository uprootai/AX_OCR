#!/usr/bin/env python3
"""E12 Phase 2 — SECTION 크롭 OD/ID/W 통합 실험 v3

검증된 전략:
  1. SECTION 기본 크롭 (53~78%, 25~92%) → PaddleOCR → ID/W 후보 (위치 기반)
  2. SECTION 우측 세로 텍스트 스캔 (60~73%) → 90° 회전 → OD 후보
  3. 세션명 힌트 결합 → OD 확정
  4. OD/ID/W 최종 결합

결과:
  - OD: 5/7 (71%) — 기존 1/7 → 5/7
  - ID: 5/7 (71%) — 기존 위치 기반 유지
  - W: 개선 중

Usage:
    python3 experiment_section_od_v3.py
"""

import json
import re
import io
import time
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from PIL import Image, ImageEnhance

# ================================================================
# 설정
# ================================================================

PADDLE_URL = "http://localhost:5006/api/v1/ocr"

GT = {
    "TD0062015": {"name": "T1", "od": 360, "id": 190, "w": 200,
                  "pdf": "01_저널베어링/TD0062015 Rev.A(T1 BEARING ASSY(360X190)).pdf"},
    "TD0062021": {"name": "T2", "od": 380, "id": 190, "w": 200,
                  "pdf": "01_저널베어링/TD0062021 Rev.A(T2 BEARING ASSY(380X190)).pdf"},
    "TD0062026": {"name": "T3", "od": 380, "id": 260, "w": 260,
                  "pdf": "01_저널베어링/TD0062026 Rev.A(T3 BEARING ASSY(380X260)).pdf"},
    "TD0062031": {"name": "T4", "od": 420, "id": 260, "w": 260,
                  "pdf": "01_저널베어링/TD0062031 Rev.B(T4 BEARING ASSY (420x260)).pdf"},
    "TD0062037": {"name": "T5", "od": 1036, "id": 580, "w": 200,
                  "pdf": "01_저널베어링/TD0062037 Rev.A(T5 BEARING ASSY(460x260)).pdf"},
    "TD0062050": {"name": "T8", "od": 500, "id": 260, "w": 200,
                  "pdf": "01_저널베어링/TD0062050 Rev.B(T8 BEARING ASSY 500x260).pdf"},
    "TD0062055": {"name": "Thrust", "od": 515, "id": 440, "w": 48,
                  "pdf": "02_스러스트베어링/TD0062055 Rev.A(THRUST BEARING ASSY(OD670XID440)).pdf"},
}

PDF_BASE = Path("/home/uproot/ax/poc/apply-company/dsebearing/PJT/04_부품도면")


# ================================================================
# PDF → PNG
# ================================================================

def pdf_to_image(pdf_path: Path, dpi: int = 200) -> Image.Image:
    """PDF 첫 페이지를 PIL Image로 변환"""
    import fitz
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    doc.close()
    return Image.open(io.BytesIO(png_bytes))


# ================================================================
# OCR 호출
# ================================================================

def paddle_ocr(png_bytes: bytes, timeout: int = 60) -> List[Dict]:
    """PaddleOCR 호출 (재시도 포함)"""
    for attempt in range(2):
        try:
            resp = requests.post(
                PADDLE_URL,
                files={"file": ("img.png", png_bytes, "image/png")},
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json().get("detections", [])
        except Exception:
            if attempt == 0:
                time.sleep(3)
    return []


def image_to_bytes(img: Image.Image, fmt: str = "JPEG", quality: int = 90) -> bytes:
    """PIL Image → bytes"""
    buf = io.BytesIO()
    if fmt == "JPEG":
        img = img.convert("RGB")
    img.save(buf, format=fmt, quality=quality)
    return buf.getvalue()


# ================================================================
# 전략 1: SECTION 기본 크롭 → ID/W (위치 기반)
# ================================================================

def extract_section_basic(img: Image.Image) -> Dict:
    """SECTION 기본 크롭에서 ID/W 추출 (기존 위치 기반 검증됨)"""
    w, h = img.size
    cropped = img.crop((int(w * 0.53), int(h * 0.25), int(w * 0.78), int(h * 0.92)))

    jpg = image_to_bytes(cropped)
    dets = paddle_ocr(jpg)

    cw, ch = cropped.size
    nums = []
    for d in dets:
        text = d.get("text", "")
        m = re.search(r"(\d+\.?\d*)", re.sub(r"[()]", "", text))
        if not m:
            continue
        num = float(m.group(1))
        if num < 10 or num > 2000:
            continue

        bbox = d.get("bbox", [])
        if isinstance(bbox, list) and len(bbox) >= 4 and isinstance(bbox[0], list):
            x_c = sum(p[0] for p in bbox) / len(bbox)
            y_c = sum(p[1] for p in bbox) / len(bbox)
        else:
            continue

        x_r = x_c / max(cw, 1)
        y_r = y_c / max(ch, 1)
        nums.append({"num": num, "text": text, "x": x_r, "y": y_r})

    # ID: 중앙 영역 (x < 0.60, y 30~70%)
    id_candidates = [n for n in nums if n["x"] < 0.60 and 0.30 < n["y"] < 0.70]
    id_candidates.sort(key=lambda n: n["num"])
    id_val = id_candidates[0]["num"] if id_candidates else None

    # W: 상단+하단 양쪽 공통값 우선 전략
    # 실험 결과: W는 SECTION 상단(y<0.20)과 하단(y>0.75) 양쪽에 동일 값으로 표기됨
    # T1/T2/T5/T8: 양쪽 200 공통 → W=200 ✓
    w_top = set(int(n["num"]) for n in nums if n["y"] < 0.20 and n["num"] >= 30)
    w_bot = set(int(n["num"]) for n in nums if n["y"] > 0.75 and n["num"] >= 30)
    w_common = w_top & w_bot

    if w_common:
        # 양쪽 공통값이 있으면 그 중 가장 작은 것 = W
        w_val = float(min(w_common))
    elif w_bot:
        # 하단에만 있으면 가장 큰 값 (Thrust: 48)
        w_val = float(max(w_bot))
    elif w_top:
        # 상단에만 있으면 가장 작은 값
        w_val = float(min(w_top))
    else:
        w_val = None

    return {
        "id": id_val,
        "w": w_val,
        "all_nums": nums,
    }


# ================================================================
# 전략 2: 세로 텍스트 슬라이딩 스캔 → OD
# ================================================================

def scan_od_vertical(img: Image.Image) -> List[Tuple[float, str]]:
    """SECTION 우측의 세로 방향 Ø치수를 슬라이딩 윈도우로 스캔

    검증 결과: T1/T2/T3/T4/T8 5건 모두 성공 (5/5 저널 베어링)
    """
    w, h = img.size
    found = []

    # x: 60~73%, y를 15% 간격으로 슬라이딩
    for y_start in [0.28, 0.35, 0.42, 0.49, 0.56]:
        y_end = y_start + 0.15
        strip = img.crop((int(w * 0.60), int(h * y_start), int(w * 0.73), int(h * y_end)))
        rotated = strip.rotate(-90, expand=True)
        up = rotated.resize((rotated.width * 3, rotated.height * 3), Image.LANCZOS)
        enhanced = ImageEnhance.Contrast(up).enhance(1.8).convert("L")

        png = image_to_bytes(enhanced, fmt="PNG")
        dets = paddle_ocr(png)

        for d in dets:
            text = d.get("text", "")
            # "0360.48" → 360.48, "(380.58" → 380.58
            cleaned = re.sub(r"^[(\s]*0?", "", text)
            m = re.search(r"(\d{3,4}\.?\d*)", cleaned)
            if m:
                num = float(m.group(1))
                if 100 < num < 2000 and num not in [n for n, _ in found]:
                    found.append((num, text))
        time.sleep(1)

    return found


# ================================================================
# 세션명 힌트 파싱
# ================================================================

def parse_hint(filename: str) -> Dict:
    """파일명에서 OD/ID 힌트"""
    m = re.search(r"OD\s*(\d+)\s*[xX×]\s*ID\s*(\d+)", filename, re.IGNORECASE)
    if m:
        return {"od": float(m.group(1)), "id": float(m.group(2))}
    m = re.search(r"\((\d+)\s*[xX×]\s*(\d+)\)", filename)
    if m:
        return {"od": float(m.group(1)), "id": float(m.group(2))}
    m = re.search(r"(\d{3,4})\s*[xX×]\s*(\d{2,3})", filename)
    if m:
        return {"od": float(m.group(1)), "id": float(m.group(2))}
    return {}


# ================================================================
# 통합 분류
# ================================================================

def classify_combined(basic: Dict, od_scan: List, hint: Dict) -> Dict:
    """3가지 소스 결합 → 최종 OD/ID/W

    우선순위:
    - OD: 세로스캔(Ø후보) > 세션힌트 > 기본크롭
    - ID: 기본크롭(위치기반) > 세션힌트
    - W: 기본크롭(위치기반)
    """
    # OD: 세로 스캔에서 가장 큰 3자리+ 값 (일반적으로 OD가 가장 큰 Ø치수)
    od_val = None
    od_source = ""

    if od_scan:
        # 세로 스캔 결과 중 가장 큰 값 = OD
        # 단, 세션힌트가 있으면 힌트에 가까운 값 우선
        hint_od = hint.get("od")
        if hint_od:
            # 힌트 ±20% 이내의 스캔 값 찾기
            near_hint = [(n, t) for n, t in od_scan if abs(n - hint_od) / hint_od < 0.20]
            if near_hint:
                od_val = near_hint[0][0]
                od_source = "scan+hint"
            else:
                # 힌트와 안 맞으면 스캔 값 중 최대
                od_val = max(n for n, _ in od_scan)
                od_source = "scan(no_hint_match)"
        else:
            od_val = max(n for n, _ in od_scan)
            od_source = "scan"
    elif hint.get("od"):
        od_val = hint["od"]
        od_source = "hint_only"

    # ID: 기본 크롭 위치 기반
    id_val = basic.get("id")
    id_source = "section_position"
    if id_val is None and hint.get("id"):
        id_val = hint["id"]
        id_source = "hint"

    # W: 기본 크롭 상단/하단
    w_val = basic.get("w")

    return {
        "od": od_val, "od_source": od_source,
        "id": id_val, "id_source": id_source,
        "w": w_val,
    }


# ================================================================
# 실행
# ================================================================

def run():
    print("=" * 90)
    print("  E12 Phase 2 — SECTION 크롭 OD/ID/W 통합 실험 v3")
    print("  전략: 기본크롭(ID/W) + 세로스캔(OD) + 세션힌트")
    print("=" * 90)

    results = []
    od_ok = id_ok = w_ok = 0
    total = 0
    w_total = 0

    for drawing_no, gt in GT.items():
        pdf_path = PDF_BASE / gt["pdf"]
        if not pdf_path.exists():
            print(f"\n  ⚠ {drawing_no} PDF 없음")
            continue

        total += 1
        print(f"\n{'─' * 70}")
        print(f"  {gt['name']} ({drawing_no})  GT: OD={gt['od']} ID={gt['id']} W={gt['w']}")
        print(f"{'─' * 70}")

        img = pdf_to_image(pdf_path)
        print(f"  이미지: {img.width}×{img.height}px")

        # 전략 1: 기본 크롭 → ID/W
        basic = extract_section_basic(img)
        print(f"  기본크롭: ID={basic['id']} W={basic['w']}")
        if basic["all_nums"]:
            nums_str = ", ".join(f"{n['num']:.0f}(x={n['x']:.2f},y={n['y']:.2f})" for n in basic["all_nums"])
            print(f"    숫자: {nums_str}")

        time.sleep(2)

        # 전략 2: 세로 스캔 → OD
        od_scan = scan_od_vertical(img)
        if od_scan:
            scan_str = ", ".join(f"{n:.1f}({t})" for n, t in od_scan)
            print(f"  세로스캔: {scan_str}")
        else:
            print(f"  세로스캔: (없음)")

        # 세션명 힌트
        hint = parse_hint(gt["pdf"])
        if hint:
            print(f"  세션힌트: {hint}")

        # 통합 분류
        result = classify_combined(basic, od_scan, hint)
        od_v = result["od"]
        id_v = result["id"]
        w_v = result["w"]

        # GT 비교
        od_match = abs(od_v - gt["od"]) / gt["od"] < 0.05 if od_v else False
        id_match = abs(id_v - gt["id"]) / gt["id"] < 0.05 if id_v else False
        w_match = abs(w_v - gt["w"]) / gt["w"] < 0.10 if w_v and gt["w"] else False

        od_ok += od_match
        id_ok += id_match
        if gt["w"]:
            w_total += 1
            w_ok += w_match

        m = lambda x: "✓" if x else "✗"
        print(f"\n  결과: OD={od_v}({result['od_source']}) ID={id_v} W={w_v}")
        print(f"  GT  : OD={gt['od']} ID={gt['id']} W={gt['w']}")
        print(f"  판정: OD {m(od_match)} | ID {m(id_match)} | W {m(w_match)}")

        results.append({
            "drawing_no": drawing_no, "name": gt["name"],
            "gt": {"od": gt["od"], "id": gt["id"], "w": gt["w"]},
            "result": {"od": od_v, "id": id_v, "w": w_v},
            "od_source": result["od_source"],
            "match": {"od": od_match, "id": id_match, "w": w_match},
        })

        time.sleep(3)

    # 요약
    print(f"\n{'=' * 90}")
    print(f"  요약: GT {total}건")
    print(f"  외경(OD): {od_ok}/{total} ({od_ok/total*100:.0f}%)")
    print(f"  내경(ID): {id_ok}/{total} ({id_ok/total*100:.0f}%)")
    print(f"  폭  (W) : {w_ok}/{w_total} ({w_ok/w_total*100:.0f}%)" if w_total else "")
    print(f"{'=' * 90}")

    # 이전 대비
    print(f"\n  {'방법':<40} {'OD':>6} {'ID':>6} {'W':>6}")
    print(f"  {'─'*40} {'─'*6} {'─'*6} {'─'*6}")
    print(f"  {'K geometry (보정 전)':<40} {'0/7':>6} {'0/7':>6} {'0/5':>6}")
    print(f"  {'K + 세션명 힌트':<40} {'1/7':>6} {'0/7':>6} {'0/5':>6}")
    print(f"  {'SECTION 크롭 + 단순 크기':<40} {'1/7':>6} {'1/7':>6} {'1/5':>6}")
    print(f"  {'SECTION 크롭 + 위치 기반':<40} {'1/7':>6} {'5/7':>6} {'0/5':>6}")
    print(f"  {'v3: 세로스캔+위치기반+힌트결합':<40} {f'{od_ok}/{total}':>6} {f'{id_ok}/{total}':>6} {f'{w_ok}/{w_total}':>6}")

    # 저장
    out = Path(__file__).parent / "experiment_section_od_v3_results.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  결과 저장: {out}")


if __name__ == "__main__":
    run()
