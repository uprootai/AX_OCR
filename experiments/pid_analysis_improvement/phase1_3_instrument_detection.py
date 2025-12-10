"""
Phase 1.3: Instrument Detection via Color Segmentation + OCR
빨간 박스(계기 심볼) 검출 및 OCR 기반 분류

P&ID 특징:
- FC, TI, LC, PC, FI, TC 등의 계기는 빨간색 박스 안에 표시됨
- 박스 안의 텍스트로 계기 유형 식별 가능

접근 방법:
1. HSV 색상 분할로 빨간/주황/컬러 박스 검출
2. 박스 영역 OCR로 텍스트 추출
3. 텍스트 패턴 매칭으로 계기 유형 분류
"""
import cv2
import numpy as np
import requests
from pathlib import Path
import json
from collections import defaultdict

SAMPLE_IMAGE = Path(__file__).parent.parent.parent / "web-ui/public/samples/pid_detection_optimized.png"
OCR_API_URL = "http://localhost:5008/api/v1/ocr"  # Tesseract OCR


def detect_colored_boxes(image_path: str, debug: bool = False) -> list:
    """
    색상 기반으로 계기 박스 검출
    빨간색, 주황색, 노란색 박스를 찾음
    """
    img = cv2.imread(str(image_path))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    detected_boxes = []

    # 빨간색 범위 (두 범위: 0-10, 170-180)
    red_lower1 = np.array([0, 100, 100])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([160, 100, 100])
    red_upper2 = np.array([180, 255, 255])

    mask_red1 = cv2.inRange(hsv, red_lower1, red_upper1)
    mask_red2 = cv2.inRange(hsv, red_lower2, red_upper2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    # 노란색 범위
    yellow_lower = np.array([20, 100, 100])
    yellow_upper = np.array([40, 255, 255])
    mask_yellow = cv2.inRange(hsv, yellow_lower, yellow_upper)

    # 마젠타/핑크 범위
    magenta_lower = np.array([140, 50, 50])
    magenta_upper = np.array([170, 255, 255])
    mask_magenta = cv2.inRange(hsv, magenta_lower, magenta_upper)

    # 시안 범위
    cyan_lower = np.array([80, 100, 100])
    cyan_upper = np.array([100, 255, 255])
    mask_cyan = cv2.inRange(hsv, cyan_lower, cyan_upper)

    # 각 색상별 박스 검출
    colors = {
        "red": mask_red,
        "yellow": mask_yellow,
        "magenta": mask_magenta,
        "cyan": mask_cyan
    }

    for color_name, mask in colors.items():
        # Morphological operations to clean up
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 200 or area > 10000:  # 너무 작거나 큰 영역 제외
                continue

            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0

            # 박스 형태 필터링 (정사각형~직사각형)
            if 0.3 < aspect_ratio < 3.5 and w > 15 and h > 15:
                detected_boxes.append({
                    "bbox": [x, y, x + w, y + h],
                    "center": [x + w/2, y + h/2],
                    "width": w,
                    "height": h,
                    "color": color_name,
                    "area": area
                })

    # 중복 제거 (겹치는 박스들 병합)
    filtered_boxes = remove_overlapping_boxes(detected_boxes)

    if debug:
        # 디버그용 이미지 저장
        debug_img = img.copy()
        for box in filtered_boxes:
            x1, y1, x2, y2 = box["bbox"]
            color = {"red": (0, 0, 255), "yellow": (0, 255, 255),
                     "magenta": (255, 0, 255), "cyan": (255, 255, 0)}.get(box["color"], (0, 255, 0))
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 2)
        cv2.imwrite(str(Path(__file__).parent / "debug_colored_boxes.jpg"), debug_img)
        print(f"Debug image saved: debug_colored_boxes.jpg")

    return filtered_boxes


def remove_overlapping_boxes(boxes: list, iou_threshold: float = 0.5) -> list:
    """겹치는 박스 제거"""
    if not boxes:
        return []

    # 면적 기준 정렬 (큰 것 우선)
    boxes = sorted(boxes, key=lambda x: x["area"], reverse=True)
    keep = []

    for box in boxes:
        x1, y1, x2, y2 = box["bbox"]
        is_duplicate = False

        for kept in keep:
            kx1, ky1, kx2, ky2 = kept["bbox"]

            # IoU 계산
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


def ocr_box_region(image_path: str, box: dict) -> str:
    """박스 영역 OCR"""
    img = cv2.imread(str(image_path))
    x1, y1, x2, y2 = box["bbox"]

    # 여백 추가
    margin = 5
    x1 = max(0, x1 - margin)
    y1 = max(0, y1 - margin)
    x2 = min(img.shape[1], x2 + margin)
    y2 = min(img.shape[0], y2 + margin)

    roi = img[y1:y2, x1:x2]

    # ROI를 임시 파일로 저장
    temp_path = Path(__file__).parent / "temp_roi.jpg"
    cv2.imwrite(str(temp_path), roi)

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
                    # Return all detected texts joined
                    return " ".join([t.get("text", "") for t in texts]).strip()
    except Exception as e:
        print(f"OCR error: {e}")

    return ""


def classify_instrument(text: str) -> dict:
    """
    OCR 텍스트로 계기 유형 분류

    P&ID 계기 코드:
    - F: Flow (유량)
    - T: Temperature (온도)
    - L: Level (레벨)
    - P: Pressure (압력)

    기능 코드:
    - I: Indicator (지시계)
    - C: Controller (제어기)
    - T: Transmitter (전송기)
    - R: Recorder (기록계)
    """
    text = text.upper().replace(" ", "").replace("-", "")

    instrument_types = {
        "FC": {"type": "Flow Controller", "category": "controller", "korean": "유량 제어기"},
        "FI": {"type": "Flow Indicator", "category": "indicator", "korean": "유량 지시계"},
        "FT": {"type": "Flow Transmitter", "category": "transmitter", "korean": "유량 전송기"},
        "TI": {"type": "Temperature Indicator", "category": "indicator", "korean": "온도 지시계"},
        "TC": {"type": "Temperature Controller", "category": "controller", "korean": "온도 제어기"},
        "TT": {"type": "Temperature Transmitter", "category": "transmitter", "korean": "온도 전송기"},
        "LI": {"type": "Level Indicator", "category": "indicator", "korean": "레벨 지시계"},
        "LC": {"type": "Level Controller", "category": "controller", "korean": "레벨 제어기"},
        "LT": {"type": "Level Transmitter", "category": "transmitter", "korean": "레벨 전송기"},
        "PI": {"type": "Pressure Indicator", "category": "indicator", "korean": "압력 지시계"},
        "PC": {"type": "Pressure Controller", "category": "controller", "korean": "압력 제어기"},
        "PT": {"type": "Pressure Transmitter", "category": "transmitter", "korean": "압력 전송기"},
    }

    # 패턴 매칭
    for code, info in instrument_types.items():
        if code in text:
            # 번호 추출 (예: FC-1, TI-3)
            import re
            match = re.search(rf"{code}[-_]?(\d+)", text)
            tag_number = match.group(0) if match else code

            return {
                "code": code,
                "tag_number": tag_number,
                **info
            }

    return {"code": "UNKNOWN", "type": "Unknown Instrument", "category": "unknown", "korean": "미분류 계기"}


def run_instrument_detection():
    """계기 검출 실행"""
    print("=" * 60)
    print("Phase 1.3: Instrument Detection via Color + OCR")
    print("=" * 60)

    # 1. 색상 기반 박스 검출
    print("\n1. 색상 기반 박스 검출 중...")
    boxes = detect_colored_boxes(SAMPLE_IMAGE, debug=True)
    print(f"   검출된 컬러 박스: {len(boxes)}개")

    # 색상별 통계
    color_counts = defaultdict(int)
    for box in boxes:
        color_counts[box["color"]] += 1
    print(f"   색상별: {dict(color_counts)}")

    # 2. 빨간 박스만 필터링 (주로 계기)
    red_boxes = [b for b in boxes if b["color"] == "red"]
    print(f"\n2. 빨간 박스 (계기 후보): {len(red_boxes)}개")

    # 3. OCR로 텍스트 추출 및 분류
    print("\n3. OCR 분류 중...")
    instruments = []

    for i, box in enumerate(red_boxes[:20]):  # 처음 20개만 테스트
        text = ocr_box_region(SAMPLE_IMAGE, box)
        classification = classify_instrument(text)

        instrument = {
            "id": i,
            "bbox": box["bbox"],
            "center": box["center"],
            "ocr_text": text,
            **classification
        }
        instruments.append(instrument)

        if text:
            print(f"   박스 {i}: '{text}' → {classification['type']}")

    # 4. 분류 결과 집계
    print("\n" + "=" * 60)
    print("계기 분류 결과")
    print("=" * 60)

    type_counts = defaultdict(int)
    for inst in instruments:
        type_counts[inst["type"]] += 1

    for inst_type, count in sorted(type_counts.items()):
        print(f"  {inst_type}: {count}개")

    # 결과 저장
    output_path = Path(__file__).parent / "phase1_3_instruments.json"
    with open(output_path, "w") as f:
        json.dump({
            "total_color_boxes": len(boxes),
            "red_boxes": len(red_boxes),
            "instruments": instruments,
            "type_counts": dict(type_counts)
        }, f, indent=2, ensure_ascii=False)
    print(f"\n결과 저장: {output_path}")

    return instruments


if __name__ == "__main__":
    instruments = run_instrument_detection()
