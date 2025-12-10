"""
Phase 1.3: OCR Debug Script
OCR 서비스가 P&ID 텍스트를 인식하지 못하는 원인 분석
"""
import cv2
import numpy as np
import requests
from pathlib import Path
import base64
import json

SAMPLE_IMAGE = Path(__file__).parent.parent.parent / "web-ui/public/samples/pid_detection_optimized.png"
OUTPUT_DIR = Path(__file__).parent

# OCR API endpoints
OCR_APIS = {
    "tesseract": "http://localhost:5008/api/v1/process",
    "paddleocr": "http://localhost:5006/api/v1/process",
    "easyocr": "http://localhost:5015/api/v1/process",
    "ensemble": "http://localhost:5011/api/v1/process",
}


def preprocess_for_ocr(img: np.ndarray, method: str = "adaptive") -> np.ndarray:
    """OCR을 위한 이미지 전처리"""

    # 그레이스케일 변환
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    if method == "simple":
        # 단순 이진화
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        return binary

    elif method == "adaptive":
        # 적응적 이진화
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return binary

    elif method == "otsu":
        # Otsu 이진화
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    elif method == "contrast":
        # 대비 향상 + Otsu
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    elif method == "upscale":
        # 업스케일 + 대비 향상
        scale = 2
        upscaled = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(upscaled)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    return gray


def extract_roi(img: np.ndarray, bbox: tuple, margin: int = 10) -> np.ndarray:
    """ROI 추출"""
    x1, y1, x2, y2 = bbox
    h, w = img.shape[:2]
    x1 = max(0, x1 - margin)
    y1 = max(0, y1 - margin)
    x2 = min(w, x2 + margin)
    y2 = min(h, y2 + margin)
    return img[y1:y2, x1:x2]


def test_ocr_api(image_path: str, api_name: str, api_url: str) -> dict:
    """OCR API 테스트"""
    try:
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f, "image/png")}
            data = {"lang": "eng"}

            response = requests.post(api_url, files=files, data=data, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "api": api_name,
                "result": result
            }
        else:
            return {
                "success": False,
                "api": api_name,
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except Exception as e:
        return {
            "success": False,
            "api": api_name,
            "error": str(e)
        }


def create_test_image():
    """테스트용 이미지 생성 (OCR 서비스 정상 작동 확인용)"""
    img = np.ones((100, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img, "FC-1 P-34 TI-3", (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

    test_path = OUTPUT_DIR / "test_ocr_image.png"
    cv2.imwrite(str(test_path), img)
    return test_path


def run_ocr_debug():
    """OCR 디버그 실행"""
    print("=" * 70)
    print("Phase 1.3: OCR Debug - P&ID 텍스트 인식 문제 분석")
    print("=" * 70)

    # 1. 테스트 이미지로 OCR 서비스 정상 작동 확인
    print("\n[Test 1] 간단한 테스트 이미지로 OCR 서비스 확인")
    print("-" * 50)

    test_img_path = create_test_image()
    print(f"테스트 이미지 생성: {test_img_path}")

    for api_name, api_url in OCR_APIS.items():
        result = test_ocr_api(str(test_img_path), api_name, api_url)
        if result["success"]:
            # Extract texts from result
            texts = []
            if "data" in result["result"]:
                data = result["result"]["data"]
                if isinstance(data, dict) and "results" in data:
                    texts = [r.get("text", "") for r in data["results"]]
                elif isinstance(data, list):
                    texts = [r.get("text", "") for r in data]
            print(f"  {api_name}: {len(texts)} texts - {texts[:3]}")
        else:
            print(f"  {api_name}: ERROR - {result['error'][:100]}")

    # 2. P&ID 이미지에서 텍스트 영역 추출 및 전처리
    print("\n[Test 2] P&ID 이미지 ROI 전처리 테스트")
    print("-" * 50)

    img = cv2.imread(str(SAMPLE_IMAGE))
    print(f"원본 이미지 크기: {img.shape}")

    # FC-1 영역 (이미지에서 직접 확인한 좌표)
    # 이미지를 보면 FC-1은 대략 왼쪽 하단에 있음
    test_regions = [
        {"name": "FC-1 area", "bbox": (195, 560, 245, 595)},  # 수동 지정
        {"name": "Column-1 area", "bbox": (295, 265, 345, 350)},  # Column 영역
        {"name": "P-34 text area", "bbox": (330, 445, 380, 470)},  # P-34 텍스트
    ]

    # 전처리 방법별 테스트
    preprocess_methods = ["simple", "adaptive", "otsu", "contrast", "upscale"]

    for region in test_regions:
        roi = extract_roi(img, region["bbox"])
        print(f"\n{region['name']} (크기: {roi.shape[:2]})")

        # 원본 ROI 저장
        roi_path = OUTPUT_DIR / f"roi_{region['name'].replace(' ', '_')}_original.png"
        cv2.imwrite(str(roi_path), roi)

        # 전처리 방법별 테스트
        for method in preprocess_methods:
            processed = preprocess_for_ocr(roi, method)
            proc_path = OUTPUT_DIR / f"roi_{region['name'].replace(' ', '_')}_{method}.png"
            cv2.imwrite(str(proc_path), processed)

            # Tesseract로 OCR 테스트
            result = test_ocr_api(str(proc_path), "tesseract", OCR_APIS["tesseract"])
            if result["success"]:
                texts = []
                if "data" in result["result"]:
                    data = result["result"]["data"]
                    if isinstance(data, dict) and "results" in data:
                        texts = [r.get("text", "") for r in data["results"]]
                    elif isinstance(data, list):
                        texts = [r.get("text", "") for r in data]
                text_str = ", ".join(texts) if texts else "(empty)"
                print(f"  {method}: {text_str[:50]}")

    # 3. 전체 이미지 OCR (큰 텍스트만)
    print("\n[Test 3] 전체 P&ID 이미지 OCR")
    print("-" * 50)

    # 전처리 후 OCR
    for method in ["original", "contrast", "upscale"]:
        if method == "original":
            proc_img = img
        else:
            proc_img = preprocess_for_ocr(img, method)

        proc_path = OUTPUT_DIR / f"full_pid_{method}.png"
        cv2.imwrite(str(proc_path), proc_img)

        result = test_ocr_api(str(proc_path), "tesseract", OCR_APIS["tesseract"])
        if result["success"]:
            texts = []
            if "data" in result["result"]:
                data = result["result"]["data"]
                if isinstance(data, dict) and "results" in data:
                    texts = [r.get("text", "") for r in data["results"]]
                elif isinstance(data, list):
                    texts = [r.get("text", "") for r in data]
            print(f"  {method}: {len(texts)} texts detected")
            if texts:
                print(f"    샘플: {texts[:5]}")

    print("\n" + "=" * 70)
    print("디버그 완료. 결과 이미지는 experiments/pid_analysis_improvement/ 에 저장됨")
    print("=" * 70)


if __name__ == "__main__":
    run_ocr_debug()
