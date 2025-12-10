"""
Phase 1.3: Improved Instrument Detection
개선된 계기 검출 - 다양한 색상 및 형태 인식
"""
import cv2
import numpy as np
import requests
from pathlib import Path
import json
from collections import defaultdict

SAMPLE_IMAGE = Path(__file__).parent.parent.parent / "web-ui/public/samples/pid_detection_optimized.png"
OCR_API_URL = "http://localhost:5008/api/v1/ocr"
OUTPUT_DIR = Path(__file__).parent


def detect_instrument_boxes(image_path: str, debug: bool = True) -> list:
    """
    다양한 방법으로 계기 박스 검출
    1. 색상 기반 검출 (HSV)
    2. 에지 기반 사각형 검출
    3. 텍스트 영역 검출
    """
    img = cv2.imread(str(image_path))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    all_boxes = []

    # 1. 다양한 색상 범위로 박스 검출
    color_ranges = {
        # 빨간색 (두 범위)
        "red": [
            (np.array([0, 70, 70]), np.array([10, 255, 255])),
            (np.array([170, 70, 70]), np.array([180, 255, 255])),
        ],
        # 주황색/갈색
        "orange": [
            (np.array([10, 100, 100]), np.array([25, 255, 255])),
        ],
        # 노란색
        "yellow": [
            (np.array([20, 80, 150]), np.array([40, 255, 255])),
        ],
        # 녹색
        "green": [
            (np.array([35, 80, 80]), np.array([85, 255, 255])),
        ],
        # 시안
        "cyan": [
            (np.array([80, 80, 80]), np.array([100, 255, 255])),
        ],
        # 파란색
        "blue": [
            (np.array([100, 80, 80]), np.array([130, 255, 255])),
        ],
        # 마젠타/분홍
        "magenta": [
            (np.array([140, 60, 60]), np.array([170, 255, 255])),
        ],
    }

    for color_name, ranges in color_ranges.items():
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

        for lower, upper in ranges:
            mask = cv2.inRange(hsv, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, mask)

        # Morphological operations
        kernel = np.ones((3, 3), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            # P&ID 계기 박스는 보통 100~5000 픽셀 면적
            if area < 100 or area > 8000:
                continue

            x, y, w, h = cv2.boundingRect(contour)

            # 최소 크기 필터
            if w < 10 or h < 10:
                continue

            # 적당한 종횡비 (극단적인 선 제외)
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio < 0.2 or aspect_ratio > 5:
                continue

            all_boxes.append({
                "bbox": [x, y, x + w, y + h],
                "center": [x + w / 2, y + h / 2],
                "width": w,
                "height": h,
                "color": color_name,
                "area": area,
                "method": "color"
            })

    # 2. 에지 기반 사각형 검출 (흰색/검은색 박스)
    edges = cv2.Canny(gray, 50, 150)
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # 사각형 근사
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

        # 4각형이고 적절한 크기인 경우
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            area = w * h

            if 200 < area < 5000 and w > 15 and h > 10:
                aspect_ratio = w / h
                if 0.3 < aspect_ratio < 4:
                    all_boxes.append({
                        "bbox": [x, y, x + w, y + h],
                        "center": [x + w / 2, y + h / 2],
                        "width": w,
                        "height": h,
                        "color": "edge",
                        "area": area,
                        "method": "edge"
                    })

    # 중복 제거
    filtered = remove_overlapping(all_boxes, iou_threshold=0.3)

    if debug:
        debug_img = img.copy()
        color_map = {
            "red": (0, 0, 255), "orange": (0, 128, 255), "yellow": (0, 255, 255),
            "green": (0, 255, 0), "cyan": (255, 255, 0), "blue": (255, 0, 0),
            "magenta": (255, 0, 255), "edge": (128, 128, 128)
        }
        for box in filtered:
            x1, y1, x2, y2 = box["bbox"]
            color = color_map.get(box["color"], (0, 255, 0))
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 2)

        cv2.imwrite(str(OUTPUT_DIR / "improved_detection_all.jpg"), debug_img)
        print(f"디버그 이미지 저장: improved_detection_all.jpg")

    return filtered


def remove_overlapping(boxes: list, iou_threshold: float = 0.5) -> list:
    """겹치는 박스 제거"""
    if not boxes:
        return []

    # 면적 기준 정렬
    boxes = sorted(boxes, key=lambda x: x["area"], reverse=True)
    keep = []

    for box in boxes:
        x1, y1, x2, y2 = box["bbox"]
        is_duplicate = False

        for kept in keep:
            kx1, ky1, kx2, ky2 = kept["bbox"]

            inter_x1 = max(x1, kx1)
            inter_y1 = max(y1, ky1)
            inter_x2 = min(x2, kx2)
            inter_y2 = min(y2, ky2)

            if inter_x1 < inter_x2 and inter_y1 < inter_y2:
                inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                box_area = (x2 - x1) * (y2 - y1)
                kept_area = (kx2 - kx1) * (ky2 - ky1)
                iou = inter_area / (box_area + kept_area - inter_area)

                if iou > iou_threshold:
                    is_duplicate = True
                    break

        if not is_duplicate:
            keep.append(box)

    return keep


def ocr_region(image: np.ndarray, bbox: list, margin: int = 5) -> str:
    """영역 OCR"""
    x1, y1, x2, y2 = bbox
    h, w = image.shape[:2]

    x1 = max(0, x1 - margin)
    y1 = max(0, y1 - margin)
    x2 = min(w, x2 + margin)
    y2 = min(h, y2 + margin)

    roi = image[y1:y2, x1:x2]
    if roi.size == 0:
        return ""

    # 전처리: 대비 향상
    if len(roi.shape) == 3:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi

    # Upscale for better OCR
    scale = 2
    upscaled = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Otsu binarization
    _, binary = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    temp_path = OUTPUT_DIR / "temp_ocr_roi.png"
    cv2.imwrite(str(temp_path), binary)

    try:
        with open(temp_path, "rb") as f:
            response = requests.post(
                OCR_API_URL,
                files={"file": f},
                data={"lang": "eng"},
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                texts = result.get("texts", [])
                if texts:
                    return " ".join([t.get("text", "") for t in texts]).strip()
    except Exception as e:
        pass

    return ""


def classify_instrument(text: str) -> dict:
    """계기 분류"""
    text = text.upper().replace(" ", "").replace("-", "").replace("_", "")

    instrument_codes = {
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
    }

    # 패턴 매칭
    import re
    for code, name in instrument_codes.items():
        if code in text:
            match = re.search(rf"({code})[-_]?(\d+)", text)
            tag = match.group(0) if match else code
            return {"code": code, "type": name, "tag": tag}

    # 펌프, 밸브 등 기타 장비
    if "V" in text and re.search(r"V[-_]?\d+", text):
        match = re.search(r"V[-_]?(\d+)", text)
        return {"code": "V", "type": "Valve", "tag": f"V-{match.group(1)}"}

    if "P" in text and re.search(r"P[-_]?\d+", text):
        match = re.search(r"P[-_]?(\d+)", text)
        return {"code": "P", "type": "Pump/Piping", "tag": f"P-{match.group(1)}"}

    if "E" in text and re.search(r"E[-_]?\d+", text):
        match = re.search(r"E[-_]?(\d+)", text)
        return {"code": "E", "type": "Heat Exchanger", "tag": f"E-{match.group(1)}"}

    return {"code": "UNKNOWN", "type": "Unknown", "tag": text}


def run_improved_detection():
    """개선된 검출 실행"""
    print("=" * 70)
    print("Phase 1.3: Improved Instrument Detection")
    print("=" * 70)

    # 1. 박스 검출
    print("\n1. 계기/장비 박스 검출 중...")
    boxes = detect_instrument_boxes(SAMPLE_IMAGE, debug=True)
    print(f"   총 검출 박스: {len(boxes)}개")

    # 색상별 통계
    color_counts = defaultdict(int)
    for box in boxes:
        color_counts[box["color"]] += 1
    print(f"   색상별: {dict(color_counts)}")

    # 2. OCR로 텍스트 추출
    print("\n2. OCR 분류 중...")
    img = cv2.imread(str(SAMPLE_IMAGE))

    instruments = []
    ocr_success = 0

    for i, box in enumerate(boxes):
        text = ocr_region(img, box["bbox"])
        if text:
            ocr_success += 1

        classification = classify_instrument(text)

        instrument = {
            "id": i,
            "bbox": box["bbox"],
            "center": box["center"],
            "color": box["color"],
            "method": box["method"],
            "ocr_text": text,
            **classification
        }
        instruments.append(instrument)

        if text and classification["code"] != "UNKNOWN":
            print(f"   박스 {i} ({box['color']}): '{text}' → {classification['type']} ({classification['tag']})")

    print(f"\n   OCR 성공: {ocr_success}/{len(boxes)}개")

    # 3. 분류 결과 집계
    print("\n" + "=" * 70)
    print("분류 결과")
    print("=" * 70)

    type_counts = defaultdict(int)
    for inst in instruments:
        type_counts[inst["type"]] += 1

    for inst_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {inst_type}: {count}개")

    # 알려진 계기만 필터링
    known_instruments = [i for i in instruments if i["code"] != "UNKNOWN"]
    print(f"\n식별된 계기: {len(known_instruments)}개")

    # 결과 저장
    output = {
        "total_boxes": len(boxes),
        "ocr_success": ocr_success,
        "known_instruments": len(known_instruments),
        "by_color": dict(color_counts),
        "by_type": dict(type_counts),
        "instruments": instruments
    }

    output_path = OUTPUT_DIR / "phase1_3_improved_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n결과 저장: {output_path}")

    # 식별된 계기 시각화
    result_img = img.copy()
    for inst in known_instruments:
        x1, y1, x2, y2 = inst["bbox"]
        cv2.rectangle(result_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{inst['tag']}"
        cv2.putText(result_img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    cv2.imwrite(str(OUTPUT_DIR / "identified_instruments.jpg"), result_img)
    print("시각화 저장: identified_instruments.jpg")

    return instruments


if __name__ == "__main__":
    instruments = run_improved_detection()
