"""
Model Loader Utilities
모델 로딩 관련 유틸리티 함수들
"""
import os
import streamlit as st
import torch
from ultralytics import YOLO

# OCR 설정을 위한 플래그 (필요시 main에서 설정)
ENHANCED_OCR_AVAILABLE = False
OCR_AVAILABLE = False
OCR_TYPE = None
OCR_VERSION = "v5.1.0"

# Enhanced OCR import (optional)
try:
    from enhanced_ocr_detector_v4 import EnhancedOCRDetectorV4
    ENHANCED_OCR_AVAILABLE = True
except ImportError:
    pass

# PaddleOCR import (optional)
try:
    from paddleocr import PaddleOCR
    OCR_AVAILABLE = True
    OCR_TYPE = "PaddleOCR"
except ImportError:
    pass

@st.cache_resource
def get_enhanced_ocr_detector():
    """Enhanced OCR Detector 캐시 로드"""
    try:
        if ENHANCED_OCR_AVAILABLE:
            detector = EnhancedOCRDetectorV4()
            print(f"✅ Enhanced OCR {OCR_VERSION} 초기화 완료")
            return detector
        else:
            return None
    except Exception as e:
        st.error(f"Enhanced OCR Detector 초기화 실패: {e}")
        return None

@st.cache_resource
def load_yolo_model_cached(model_path: str):
    """YOLO 모델을 캐시된 리소스로 로드"""
    try:
        st.info(f"🔄 모델 로딩 시도: {model_path}")

        # 파일 존재 확인
        if not os.path.exists(model_path):
            st.error(f"❌ 모델 파일이 존재하지 않습니다: {model_path}")
            return None

        model = YOLO(model_path)

        # 모델 유효성 확인
        if not hasattr(model, 'predict'):
            st.error(f"❌ 로드된 모델에 predict 메서드가 없습니다")
            return None

        # GPU 사용 가능한 경우 GPU로 이동
        if torch.cuda.is_available():
            model.to('cuda')
            st.info(f"✅ 모델을 GPU로 이동했습니다")
        else:
            st.info(f"ℹ️ CPU 모드로 실행됩니다")

        st.success(f"✅ 모델 로드 성공: {model_path}")
        return model
    except Exception as e:
        st.error(f"❌ 모델 로드 실패 ({model_path}): {e}")
        import traceback
        st.error(f"상세 오류: {traceback.format_exc()}")
        return None

@st.cache_resource
def get_paddleocr_cached():
    """PaddleOCR 캐시 로드"""
    try:
        if OCR_AVAILABLE and OCR_TYPE == "PaddleOCR":
            use_gpu = torch.cuda.is_available()
            ocr_reader = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, use_gpu=use_gpu)
            return ocr_reader
        return None
    except Exception as e:
        st.error(f"PaddleOCR 초기화 실패: {e}")
        return None