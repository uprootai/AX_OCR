"""
Configuration and Settings
설정 및 환경 변수 관리
"""

import os
import torch

# Device 설정
def setup_device():
    """GPU/CPU 디바이스 설정"""
    device = "cpu"
    device_info = "CPU"

    if torch.cuda.is_available():
        device = "cuda:0"
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        device_info = f"GPU: {gpu_name} ({gpu_memory:.1f}GB)"

    return device, device_info

# 경로 설정
PATHS = {
    'pricing_db': 'classes_info_with_pricing.json',
    'ground_truth': 'ocr_ground_truth.json',
    'class_examples': 'class_examples',
    'test_drawings': 'test_drawings',
    'uploads': 'uploads',
    'results': 'results',
    'models': 'models',
    'registry': 'models/registry.json'
}

# 모델 설정
MODEL_CONFIG = {
    'yolo_v8': {
        'path': 'model/best.pt',
        'confidence': 0.7,
        'iou': 0.45
    },
    'yolo_v11x': {
        'path': 'models/yolo/v11x/best.pt',
        'confidence': 0.7,
        'iou': 0.45
    }
}

# UI 설정
UI_CONFIG = {
    'page_title': '스마트 BOM 분석 솔루션 v2.0',
    'page_icon': '🔧',
    'layout': 'wide',
    'sidebar_state': 'expanded'
}

# 색상 설정
COLORS = {
    'detection_box': (0, 255, 0),
    'ground_truth_box': (255, 0, 0),
    'verified_box': (0, 255, 255),
    'text_color': (255, 255, 255),
    'bg_color': (0, 0, 0)
}