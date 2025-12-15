"""
OCR Utilities
OCR 관련 유틸리티 함수들
"""
import re
import streamlit as st
from typing import Dict, Any, List, Optional

# OCR 라이브러리 임포트 시도
OCR_AVAILABLE = False
OCR_TYPE = None

try:
    from paddleocr import PaddleOCR
    OCR_AVAILABLE = True
    OCR_TYPE = "PaddleOCR"
except ImportError:
    try:
        import easyocr
        OCR_AVAILABLE = True
        OCR_TYPE = "EasyOCR"
    except ImportError:
        pass

def enhance_detection_with_ocr(image, detection, ocr_reader=None) -> Dict[str, Any]:
    """OCR을 활용한 검출 결과 향상"""
    if not OCR_AVAILABLE:
        return detection

    try:
        # OCR 초기화 (캐시된 reader 사용 또는 새로 생성)
        if ocr_reader is None:
            if OCR_TYPE == "PaddleOCR":
                import torch
                use_gpu = torch.cuda.is_available()
                ocr_reader = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, use_gpu=use_gpu)
                if use_gpu:
                    print(f"✅ PaddleOCR GPU 모드 활성화")
                else:
                    print(f"⚠️ PaddleOCR CPU 모드 사용 (GPU 불가)")
            else:  # EasyOCR
                import easyocr
                import torch
                use_gpu = torch.cuda.is_available()
                ocr_reader = easyocr.Reader(['en'], gpu=use_gpu)

        # 바운딩 박스에서 텍스트 추출
        x1, y1, x2, y2 = [int(coord) for coord in detection['bbox']]

        # 패딩 추가
        padding = 5
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(image.shape[1], x2 + padding)
        y2 = min(image.shape[0], y2 + padding)

        # 영역 크롭
        cropped = image[y1:y2, x1:x2]
        if cropped.size == 0:
            return detection

        # OCR 수행
        if OCR_TYPE == "PaddleOCR":
            results = ocr_reader.ocr(cropped, cls=True)
            # PaddleOCR 결과 형식 변환
            ocr_results = []
            if results and results[0]:
                for line in results[0]:
                    bbox_coords, (text, confidence) = line
                    ocr_results.append((bbox_coords, text, confidence))
            results = ocr_results
        else:  # EasyOCR
            results = ocr_reader.readtext(cropped)

        # 키워드 매핑
        class_keywords = get_class_keywords()

        # 텍스트 추출 및 정제
        all_text = ""
        extracted_texts = []
        for (bbox_ocr, text, confidence) in results:
            if confidence > 0.5:
                clean_text = re.sub(r'[^\w\-]', '', text.upper())
                all_text += clean_text + " "
                extracted_texts.append({"text": text, "confidence": confidence, "clean_text": clean_text})

        # 키워드 매칭
        enhanced_detection = detection.copy()
        boost_applied = False
        matched_keywords = []

        current_class = detection['class_name'].upper()
        for class_type, keywords in class_keywords.items():
            if class_type in current_class:
                for keyword in keywords:
                    if keyword.upper() in all_text:
                        matched_keywords.append(keyword)
                        # 신뢰도 부스트 적용
                        original_conf = detection['confidence']
                        boost_factor = 1.15  # 15% 부스트
                        enhanced_detection['confidence'] = min(0.99, original_conf * boost_factor)
                        enhanced_detection['ocr_boost'] = True
                        enhanced_detection['matched_keyword'] = keyword
                        boost_applied = True
                        break
            if boost_applied:
                break

        # OCR 결과 저장
        save_ocr_result(detection, extracted_texts, matched_keywords, all_text, boost_applied, enhanced_detection)

        if boost_applied and 'ocr_boost' in enhanced_detection:
            st.success(f"🔍 OCR 향상: {detection['class_name']} "
                      f"{detection['confidence']:.3f} → {enhanced_detection['confidence']:.3f} "
                      f"(키워드: {enhanced_detection['matched_keyword']})")

        return enhanced_detection

    except Exception as e:
        # OCR 오류 시 원본 반환
        return detection

def get_class_keywords() -> Dict[str, List[str]]:
    """클래스별 키워드 매핑 반환"""
    return {
        'CPU': ['CPU', '1513', '1214', '1215', '6ES7', 'PLC'],
        'RS485': ['RS485', 'RS422', '485', '422', 'CM', '1241'],
        'GRAPHIC': ['GP', 'PANEL', 'HMI', '6AV', 'TOUCH', 'MAIN', 'CONTROL'],
        'TERMINAL': ['ST', 'TERMINAL', 'WAGO', '2.5', '4.0'],
        'AI': ['AI', 'ANALOG', 'INPUT', '1231', '8x13'],
        'AO': ['AO', 'ANALOG', 'OUTPUT', '1232', '4x14'],
        'DI': ['DI', 'DIGITAL', 'INPUT', '1221', '16x24'],
        'DO': ['DO', 'DIGITAL', 'OUTPUT', '1222', '16x'],
        'VALVE': ['VALVE', 'EHS', 'CM3', 'CONTROL'],
        'BREAKER': ['MCB', 'BREAKER', '2P', '3P', '4P', 'BK'],
        'TRANSFORMER': ['TRANSFORMER', 'VA', '600VA', 'MST'],
        'SMPS': ['SMPS', 'PS', '24DC', 'POWER', 'SUPPLY'],
        'SWITCH': ['SWITCH', 'SW', 'SELECT', 'MRS'],
        'RELAY': ['RELAY', 'RLY', 'PLC-RSC', 'UC'],
        'FILTER': ['FILTER', 'NF', 'NOISE', 'WYFS'],
        'EMERGENCY': ['EMERGENCY', 'STOP', 'E-STOP', 'MRE']
    }

def save_ocr_result(detection, extracted_texts, matched_keywords, all_text, boost_applied, enhanced_detection):
    """OCR 결과를 세션 상태에 저장"""
    ocr_result = {
        'detection_id': f"{detection['class_name']}_{detection['bbox'][0]}_{detection['bbox'][1]}",
        'extracted_texts': extracted_texts,
        'matched_keywords': matched_keywords,
        'all_text': all_text.strip(),
        'boost_applied': boost_applied,
        'original_confidence': detection['confidence'],
        'enhanced_confidence': enhanced_detection['confidence'] if boost_applied else detection['confidence'],
        'class_name': detection['class_name']
    }

    # 세션 상태에 OCR 결과 저장
    if 'ocr_analysis_results' not in st.session_state:
        st.session_state.ocr_analysis_results = []
    st.session_state.ocr_analysis_results.append(ocr_result)

def apply_enhanced_ocr(detections: List[Dict[str, Any]], image, ocr_reader=None) -> List[Dict[str, Any]]:
    """검출 목록에 Enhanced OCR 적용"""
    enhanced_detections = []
    for detection in detections:
        enhanced = enhance_detection_with_ocr(image, detection, ocr_reader)
        enhanced_detections.append(enhanced)
    return enhanced_detections