"""
Visualization Utilities
시각화 관련 유틸리티 함수들
"""
import cv2
import streamlit as st
from typing import List, Dict, Any, Optional
import numpy as np

def draw_detection_results(image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
    """검출 결과를 이미지에 그리기 (Enhanced OCR 검증 결과 구분 표시)"""
    # 기본 색상: 빨간색 계열 (일반 검출)
    standard_colors = [(0, 0, 255), (0, 50, 255), (50, 50, 255), (0, 100, 255), (100, 0, 255)]
    # OCR 검증 색상: 초록색 계열
    ocr_color = (0, 255, 0)  # 밝은 초록색

    for i, detection in enumerate(detections):
        x1, y1, x2, y2 = detection['bbox']

        # OCR 검증된 검출인지 확인
        is_ocr_verified = detection.get('ocr_verified', False)

        if is_ocr_verified:
            # OCR 검증된 경우: 초록색 + 두꺼운 선
            color = ocr_color
            thickness = 3
            prefix = "OCR✓ "
        else:
            # 일반 검출: 기존 색상
            color = standard_colors[i % len(standard_colors)]
            thickness = 2
            prefix = ""

        # 바운딩 박스 그리기
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)

        # 라벨 텍스트 (OCR 검증 표시 포함)
        confidence_text = f"({detection['confidence']:.2f})"
        label = f"{prefix}{detection['class_name']} {confidence_text}"

        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(image, (x1, y1-30), (x1+label_size[0], y1), color, -1)
        cv2.putText(image, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # OCR 검증된 경우 추가 정보 표시
        if is_ocr_verified and detection.get('ocr_text'):
            ocr_text = detection['ocr_text'][:15]  # 텍스트 길이 제한
            ocr_label = f"Text: {ocr_text}"
            cv2.putText(image, ocr_label, (x1, y2+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, ocr_color, 1)

    return image

def create_final_verified_image(image: np.ndarray, detections: List[Dict[str, Any]], prefix: str) -> np.ndarray:
    """최종 검증된 결과를 시각화 (승인/거부/수정/수작업 포함)"""
    # 상태별 색상 정의
    status_colors = {
        'approved': (0, 255, 0),     # 초록색 - 승인됨
        'rejected': (0, 0, 255),      # 빨간색 - 거부됨
        'modified': (255, 165, 0),    # 주황색 - 수정됨
        'pending': (128, 128, 128),   # 회색 - 대기중
        'manual': (255, 0, 255)       # 보라색 - 수작업
    }

    # 각 검출에 대해 상태에 따른 색상으로 박스 그리기
    for i, detection in enumerate(detections):
        status_key = f"{prefix}_{i}"
        current_status = st.session_state.verification_status.get(status_key, "pending")

        # 수정된 경우 상태를 modified로 설정
        if status_key in st.session_state.get('modified_classes', {}):
            current_status = 'modified'

        # 수작업 검출인 경우
        if detection.get('model_id') == 'manual' or detection.get('model') == 'manual':
            if current_status == 'pending':
                current_status = 'manual'

        # 색상 선택
        color = status_colors.get(current_status, status_colors['pending'])

        # 바운딩 박스 그리기
        bbox = detection.get('bbox', detection.get('box', []))
        if bbox and len(bbox) >= 4:
            x1, y1, x2, y2 = map(int, bbox[:4])

            # 박스 그리기
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

            # 클래스 이름 표시 (수정된 경우 수정된 이름 사용)
            class_name = detection.get('class_name', 'Unknown')
            if status_key in st.session_state.get('modified_classes', {}):
                class_name = st.session_state.modified_classes[status_key]

            # 상태 아이콘 추가
            status_icon = {
                'approved': '✅',
                'rejected': '❌',
                'modified': '✏️',
                'manual': '🎨',
                'pending': '⏳'
            }.get(current_status, '')

            # 텍스트 라벨
            label = f"{status_icon} {class_name}"

            # 텍스트 배경
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)

            # 배경 사각형
            cv2.rectangle(image, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)

            # 텍스트 그리기
            cv2.putText(image, label, (x1, y1 - 5), font, font_scale, (255, 255, 255), thickness)

    return image

def draw_detection_with_ground_truth(image: np.ndarray, detections: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]], system) -> np.ndarray:
    """Ground Truth와 모델 예측을 함께 시각화"""
    img_height, img_width = image.shape[:2]

    # 1. Ground Truth 그리기 (초록색, 두꺼운 선)
    for gt in ground_truth:
        x1, y1, x2, y2 = system.yolo_to_xyxy(
            gt['x_center'], gt['y_center'],
            gt['width'], gt['height'],
            img_width, img_height
        )
        # 초록색 박스 (두께 3)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)

        # GT 라벨 (클래스 ID만)
        label = f"GT:{gt['class_id']}"
        cv2.putText(image, label, (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # 2. 모델 예측 그리기 (빨간색, 두꺼운 선)
    for detection in detections:
        x1, y1, x2, y2 = detection['bbox']
        # 좌표를 정수로 변환
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        # 빨간색 박스 (두께 3으로 증가)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)

        # 예측 라벨 (클래스 ID와 신뢰도)
        label = f"P:{detection['class_id']}({detection['confidence']:.2f})"
        # 라벨 텍스트 (바로 표시, 배경 없이)
        cv2.putText(image, label, (x1, y2+20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # 범례 추가 (왼쪽 상단, 더 크고 명확하게)
    cv2.rectangle(image, (10, 10), (300, 80), (255, 255, 255), -1)
    cv2.rectangle(image, (10, 10), (300, 80), (0, 0, 0), 3)
    cv2.putText(image, "Legend:", (20, 35),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(image, "Green Box = Ground Truth", (20, 55),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
    cv2.putText(image, "Red Box = Model Prediction", (20, 72),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2)

    return image

def draw_ground_truth_only(image: np.ndarray, ground_truth: List[Dict[str, Any]], system) -> np.ndarray:
    """Ground Truth만 그리기 (초록색, 두꺼운 선)"""
    img_height, img_width = image.shape[:2]

    for gt in ground_truth:
        x1, y1, x2, y2 = system.yolo_to_xyxy(
            gt['x_center'], gt['y_center'],
            gt['width'], gt['height'],
            img_width, img_height
        )
        # 초록색 박스 (두께 3)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)

        # GT 라벨 (클래스 이름)
        label = f"GT: {gt['class_name']}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(image, (x1, y1-30), (x1+label_size[0], y1), (0, 255, 0), -1)
        cv2.putText(image, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return image

def draw_detections_only(image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
    """검출 결과만 그리기 (빨간색, 두꺼운 선)"""
    for detection in detections:
        x1, y1, x2, y2 = detection['bbox']
        # 좌표를 정수로 변환
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        # 빨간색 박스 (두께 3)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)

        # 예측 라벨 (클래스명과 신뢰도)
        label = f"{detection['class_name']} ({detection['confidence']:.2f})"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(image, (x1, y1-30), (x1+label_size[0], y1), (0, 0, 255), -1)
        cv2.putText(image, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return image