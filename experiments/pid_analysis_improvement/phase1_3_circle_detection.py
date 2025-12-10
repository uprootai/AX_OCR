"""
Phase 1.3: Circle-based Instrument Detection
원형 심볼 검출 + 전체 이미지 OCR로 계기 태그 매칭
"""
import cv2
import numpy as np
import requests
from pathlib import Path
import json
import re
from collections import defaultdict

# Clean P&ID image without YOLO annotations
SAMPLE_IMAGE = Path(__file__).parent.parent.parent / "web-ui/public/samples/sample6_pid_diagram.png"
OCR_API_URL = "http://localhost:5015/api/v1/ocr"  # EasyOCR - better at small text
OUTPUT_DIR = Path(__file__).parent


def detect_circles(image_path: str, debug: bool = True) -> list:
    """원형 심볼 검출 (HoughCircles)"""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Gaussian blur for noise reduction
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detect circles using HoughCircles
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=50,
        param2=30,
        minRadius=8,
        maxRadius=40
    )

    detected = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            x, y, r = circle
            detected.append({
                "center": [int(x), int(y)],
                "radius": int(r),
                "bbox": [int(x - r), int(y - r), int(x + r), int(y + r)],
                "type": "circle"
            })

    if debug and detected:
        debug_img = img.copy()
        for d in detected:
            cx, cy = d["center"]
            r = d["radius"]
            cv2.circle(debug_img, (cx, cy), r, (0, 255, 0), 2)
            cv2.circle(debug_img, (cx, cy), 2, (0, 0, 255), 3)
        cv2.imwrite(str(OUTPUT_DIR / "detected_circles.jpg"), debug_img)
        print(f"원형 검출: {len(detected)}개")

    return detected


def ocr_full_image(image_path: str) -> list:
    """전체 이미지 OCR"""
    try:
        with open(image_path, "rb") as f:
            response = requests.post(
                OCR_API_URL,
                files={"file": f},
                data={"lang": "en"},
                timeout=180
            )

        if response.status_code == 200:
            result = response.json()
            # Handle different response formats
            texts = result.get("texts", [])
            if not texts:
                texts = result.get("data", {}).get("texts", [])
            return texts
    except Exception as e:
        print(f"OCR error: {e}")

    return []


def get_bbox_center(bbox) -> tuple:
    """다양한 bbox 형식에서 중심 좌표 계산"""
    if not bbox:
        return (0, 0)

    # EasyOCR format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    if isinstance(bbox[0], list):
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)

    # Standard format: [x1, y1, x2, y2]
    if len(bbox) >= 4:
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

    return (0, 0)


def parse_instrument_tags(ocr_results: list) -> list:
    """OCR 결과에서 계기 태그 추출"""
    # P&ID 계기 태그 패턴: FC-1, TI-3, LC-2, PC-1, PI-1, FI-2, TC-1, etc.
    tag_pattern = re.compile(r'([FTLPSC][ICTR])-?(\d+)', re.IGNORECASE)

    instruments = []
    for text_item in ocr_results:
        text = text_item.get("text", "")
        bbox = text_item.get("bbox", [])
        confidence = text_item.get("confidence", 0)

        match = tag_pattern.search(text.upper())
        if match:
            code = match.group(1).upper()
            number = match.group(2)
            tag = f"{code}-{number}"

            cx, cy = get_bbox_center(bbox)

            instruments.append({
                "tag": tag,
                "code": code,
                "number": int(number),
                "text": text,
                "bbox": bbox,
                "center": [cx, cy],
                "confidence": confidence,
                "type": get_instrument_type(code)
            })

    # 장비 태그 패턴: E-1, V-1, Column, etc.
    equipment_pattern = re.compile(r'([EV])-?(\d+)', re.IGNORECASE)
    for text_item in ocr_results:
        text = text_item.get("text", "")
        bbox = text_item.get("bbox", [])

        match = equipment_pattern.search(text.upper())
        if match:
            prefix = match.group(1).upper()
            number = match.group(2)
            tag = f"{prefix}-{number}"

            cx, cy = get_bbox_center(bbox)

            etype = "Heat Exchanger/Vessel" if prefix == "E" else "Valve/Vessel"
            instruments.append({
                "tag": tag,
                "code": prefix,
                "number": int(number),
                "text": text,
                "bbox": bbox,
                "center": [cx, cy],
                "confidence": text_item.get("confidence", 0),
                "type": etype
            })

    # 중복 제거
    seen_tags = set()
    unique = []
    for inst in instruments:
        if inst["tag"] not in seen_tags:
            seen_tags.add(inst["tag"])
            unique.append(inst)

    return unique


def get_instrument_type(code: str) -> str:
    """계기 코드로 유형 반환"""
    types = {
        "FC": "Flow Controller",
        "FI": "Flow Indicator",
        "FT": "Flow Transmitter",
        "TC": "Temperature Controller",
        "TI": "Temperature Indicator",
        "TT": "Temperature Transmitter",
        "LC": "Level Controller",
        "LI": "Level Indicator",
        "LT": "Level Transmitter",
        "PC": "Pressure Controller",
        "PI": "Pressure Indicator",
        "PT": "Pressure Transmitter",
        "SC": "Speed Controller",
        "SI": "Speed Indicator",
    }
    return types.get(code, "Unknown Instrument")


def match_circles_with_tags(circles: list, tags: list, max_distance: float = 80) -> list:
    """원형과 태그 매칭"""
    matched = []

    for circle in circles:
        cx, cy = circle["center"]
        best_tag = None
        best_dist = float('inf')

        for tag in tags:
            if "center" not in tag:
                continue
            tx, ty = tag["center"]
            dist = np.sqrt((cx - tx)**2 + (cy - ty)**2)

            if dist < best_dist and dist < max_distance:
                best_dist = dist
                best_tag = tag

        if best_tag:
            matched.append({
                **circle,
                "tag": best_tag["tag"],
                "tag_type": best_tag["type"],
                "distance": best_dist
            })

    return matched


def run_circle_detection():
    """원형 기반 검출 실행"""
    print("=" * 70)
    print("Phase 1.3: Circle-based Instrument Detection")
    print("=" * 70)
    print(f"이미지: {SAMPLE_IMAGE.name}")

    # 1. 전체 이미지 OCR
    print("\n1. 전체 이미지 OCR 실행 중...")
    ocr_results = ocr_full_image(str(SAMPLE_IMAGE))
    print(f"   OCR 텍스트: {len(ocr_results)}개 검출")

    # 2. 계기 태그 파싱
    print("\n2. 계기 태그 파싱 중...")
    tags = parse_instrument_tags(ocr_results)
    print(f"   식별된 태그: {len(tags)}개")

    # 유형별 분류
    type_counts = defaultdict(int)
    for tag in tags:
        type_counts[tag["type"]] += 1

    print("\n   유형별 분류:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"     {t}: {c}개")

    # 태그 목록
    print("\n   검출된 태그:")
    for tag in sorted(tags, key=lambda x: (x["code"], x["number"])):
        print(f"     {tag['tag']} ({tag['type']})")

    # 3. 원형 심볼 검출
    print("\n3. 원형 심볼 검출 중...")
    circles = detect_circles(str(SAMPLE_IMAGE), debug=True)

    # 4. 원형과 태그 매칭
    print("\n4. 원형-태그 매칭 중...")
    matched = match_circles_with_tags(circles, tags)
    print(f"   매칭된 계기: {len(matched)}개")

    # 5. 시각화
    img = cv2.imread(str(SAMPLE_IMAGE))

    # 검출된 태그 위치 표시
    for tag in tags:
        bbox = tag.get("bbox", [])
        if bbox:
            # Handle polygon format [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            if isinstance(bbox[0], list):
                xs = [int(p[0]) for p in bbox]
                ys = [int(p[1]) for p in bbox]
                x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
            elif len(bbox) >= 4:
                x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            else:
                continue

            color = (0, 255, 0) if tag["code"] in ["FC", "TC", "LC", "PC"] else (255, 0, 0)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, tag["tag"], (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    cv2.imwrite(str(OUTPUT_DIR / "instrument_tags_detected.jpg"), img)
    print("\n시각화 저장: instrument_tags_detected.jpg")

    # 결과 저장
    output = {
        "total_ocr_texts": len(ocr_results),
        "total_tags": len(tags),
        "total_circles": len(circles),
        "matched": len(matched),
        "by_type": dict(type_counts),
        "tags": tags,
        "circles": circles[:50],  # 처음 50개만
        "matched_instruments": matched
    }

    output_path = OUTPUT_DIR / "phase1_3_circle_detection_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"결과 저장: {output_path}")

    print("\n" + "=" * 70)
    print("검출 완료!")
    print("=" * 70)

    return tags, circles, matched


if __name__ == "__main__":
    tags, circles, matched = run_circle_detection()
