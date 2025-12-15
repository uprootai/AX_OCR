#!/usr/bin/env python3
"""
AI 심볼 인식 기반 스마트 BOM 분석 및 견적 자동화 솔루션 v2.0
새로운 순차적 워크플로우 및 다중 모델 지원
"""

import streamlit as st
import pandas as pd
import json
import os
import glob
from pathlib import Path
import cv2
import numpy as np
# PDF 처리를 위한 라이브러리
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# OCR 라이브러리 (PaddleOCR 우선, EasyOCR 백업)
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
        OCR_AVAILABLE = False
        OCR_TYPE = None

# Enhanced OCR Detector v4.0 Rotation (회전 + 이진화 + Super Resolution)
try:
    from enhanced_ocr_v4_rotation import EnhancedOCRDetectorV4
    ENHANCED_OCR_AVAILABLE = True
    OCR_VERSION = "v4.0 Rotation"
except ImportError:
    try:
        from enhanced_ocr_v3_ultimate import EnhancedOCRDetectorV3 as EnhancedOCRDetectorV4
        ENHANCED_OCR_AVAILABLE = True
        OCR_VERSION = "v3.0 Ultimate"
    except ImportError:
        try:
            from enhanced_ocr_v2 import EnhancedOCRDetectorV2 as EnhancedOCRDetectorV4
            ENHANCED_OCR_AVAILABLE = True
            OCR_VERSION = "v2.0"
        except ImportError:
            ENHANCED_OCR_AVAILABLE = False
            OCR_VERSION = None
from PIL import Image
import tempfile
import time
import io
from ultralytics import YOLO
import torch
try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_AVAILABLE = True
except ImportError as e:
    CANVAS_AVAILABLE = False
    st_canvas = None
    print(f"⚠️ streamlit-drawable-canvas import 실패: {e}")
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Detectron2 imports (with error handling)
try:
    from detectron2.config import get_cfg
    from detectron2.engine import DefaultPredictor
    from detectron2.data import MetadataCatalog
    DETECTRON2_AVAILABLE = True
except ImportError:
    DETECTRON2_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="스마트 BOM 분석 솔루션 v2.0",
    page_icon="🔧",
    layout="wide"
)

# ================ 캐싱 최적화 함수들 ================

@st.cache_data
def load_pricing_data_cached():
    """가격 데이터 캐시 로드"""
    pricing_db_path = "classes_info_with_pricing.json"
    if os.path.exists(pricing_db_path):
        with open(pricing_db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@st.cache_data
def load_ground_truth_cached():
    """Ground Truth 데이터 캐시 로드"""
    ground_truth_path = "ocr_ground_truth.json"
    if os.path.exists(ground_truth_path):
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@st.cache_data
def load_class_names_from_examples_cached():
    """class_examples 디렉토리에서 클래스명 추출 (캐시됨)"""
    class_examples_path = "class_examples"
    class_names = []

    if not os.path.exists(class_examples_path):
        return []

    pattern = os.path.join(class_examples_path, "class_*.jpg")
    files = glob.glob(pattern)

    for file_path in files:
        filename = os.path.basename(file_path)
        if filename.startswith("class_") and filename.endswith(".jpg"):
            class_name = filename[6:-4]  # "class_" 제거하고 ".jpg" 제거
            class_names.append(class_name)

    return sorted(class_names)

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

def safe_mean(values):
    """안전한 평균 계산 - 빈 배열 처리"""
    if not values or len(values) == 0:
        return 0.0
    return np.mean(values)

class ModelRegistry:
    """모델 레지스트리 관리 클래스"""
    
    def __init__(self, registry_path="models/registry.json"):
        self.registry_path = registry_path
        self.registry = self.load_registry()
    
    def load_registry(self):
        """모델 레지스트리 로드"""
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"models": {}, "classes": {}, "metadata": {}}
    
    def get_available_models(self):
        """활성화된 모델 목록 반환"""
        available = {}
        for model_id, model_info in self.registry.get("models", {}).items():
            if model_info.get("active", True):
                # 실제 파일 존재 여부 확인
                model_path = model_info.get("path", "")
                if self._check_model_exists(model_path, model_info.get("type")):
                    available[model_id] = model_info
        return available
    
    def _check_model_exists(self, path, model_type):
        """모델 파일 존재 여부 확인"""
        if model_type == "YOLO":
            return os.path.exists(path) and path.endswith('.pt')
        elif model_type == "Detectron2":
            # Detectron2는 실제 구현 전까지 임시로 True 반환
            return True  # os.path.isdir(path) and DETECTRON2_AVAILABLE
        return False

class SmartBOMSystemV2:
    """새로운 스마트 BOM 시스템 v2.0"""
    
    def __init__(self):
        self.model_registry = ModelRegistry()
        self.pricing_db_path = "classes_info_with_pricing.json"
        self.test_drawings_path = "test_drawings"
        self.class_examples_path = "class_examples"  # 클래스별 예시 이미지 경로
        self.device = self.setup_device()
        self.loaded_models = {}  # 로드된 모델들을 캐시
        self.pricing_data = load_pricing_data_cached()
        self.data_yaml = self.load_data_yaml()  # YOLO 데이터셋 정보

        # Enhanced OCR Detector 초기화 (캐시 기반)
        self.enhanced_ocr_detector = get_enhanced_ocr_detector()
        if self.enhanced_ocr_detector is not None:
            # 초기화 성공 메시지는 한 번만 표시
            if 'enhanced_ocr_init_shown' not in st.session_state:
                st.success("✅ Enhanced OCR Detector 초기화 완료 (Ground Truth 기반)")
                st.session_state.enhanced_ocr_init_shown = True

        # 모델 가중치 (Weighted Ensemble용)
        self.model_weights = {
            'yolo_v11l': 1.0,  # YOLOv11L
            'yolo_v11x': 1.2,  # YOLOv11X (더 큰 모델이므로 더 높은 가중치)
            'yolo_v8': 0.9,    # YOLOv8 (이전 버전이므로 약간 낮은 가중치)
            'detectron2_mask_rcnn': 1.1  # Detectron2 Mask R-CNN
        }
        
        # 세션 상태 초기화
        if 'current_image' not in st.session_state:
            st.session_state.current_image = None
        if 'selected_models' not in st.session_state:
            st.session_state.selected_models = []
        if 'detection_results' not in st.session_state:
            st.session_state.detection_results = {}
        if 'verified_detections' not in st.session_state:
            st.session_state.verified_detections = []
        if 'manual_annotations' not in st.session_state:
            st.session_state.manual_annotations = []

    def setup_device(self):
        """디바이스 설정"""
        if torch.cuda.is_available():
            device = "cuda"
            device_info = f"GPU: {torch.cuda.get_device_name()}"
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            device_info += f" ({gpu_memory:.1f}GB)"
        else:
            device = "cpu"
            device_info = "CPU: 멀티코어 처리"
        
        return {"device": device, "info": device_info, "available": torch.cuda.is_available()}

    def load_pricing_data(self):
        """가격 데이터 로드"""
        if os.path.exists(self.pricing_db_path):
            with open(self.pricing_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def load_class_names_from_examples(self):
        """class_examples 디렉토리에서 클래스명 추출"""
        class_names = []

        if not os.path.exists(self.class_examples_path):
            return []

        # class_examples 디렉토리의 모든 jpg 파일 가져오기
        pattern = os.path.join(self.class_examples_path, "class_*.jpg")
        files = glob.glob(pattern)

        for file_path in files:
            filename = os.path.basename(file_path)
            # class_[정렬번호]_[실제클래스정보]_p01.jpg 패턴에서 실제클래스정보 추출
            # 예: class_00_10_BUZZER_HY-256-2(AC220V)_p01.jpg → 10_BUZZER_HY-256-2(AC220V)

            parts = filename.split('_', 2)  # class, 정렬번호, 나머지로 분리
            if len(parts) >= 3:
                # 나머지 부분에서 _p01.jpg 또는 .jpg 제거
                remaining = parts[2]
                if remaining.endswith('_p01.jpg'):
                    remaining = remaining[:-8]  # _p01.jpg 길이만큼 제거
                elif remaining.endswith('.jpg'):
                    remaining = remaining[:-4]  # .jpg 길이만큼 제거
                class_names.append(remaining)

        # 클래스명 앞 숫자로 정렬
        def get_class_number(class_name):
            parts = class_name.split('_')
            if parts and parts[0].isdigit():
                return int(parts[0])
            # 숫자,숫자 형식 처리 (예: "2,3,4,5_CIRCUIT...")
            if parts and ',' in parts[0]:
                first_num = parts[0].split(',')[0]
                if first_num.isdigit():
                    return int(first_num)
            return 999

        class_names.sort(key=get_class_number)
        return class_names

    def load_data_yaml(self):
        """YOLO data.yaml 파일 로드"""
        data_yaml_path = os.path.join(self.test_drawings_path, 'data.yaml')
        if os.path.exists(data_yaml_path):
            import yaml
            with open(data_yaml_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None

    def render_sidebar(self):
        """사이드바 렌더링"""
        with st.sidebar:
            st.title("🔧 시스템 설정")
            
            # 1. 데이터 입력 섹션
            st.header("📁 데이터 입력")
            
            # 파일 업로드
            uploaded_file = st.file_uploader(
                "도면 파일 업로드",
                type=['pdf', 'png', 'jpg', 'jpeg'],
                help="PDF 또는 이미지 파일을 업로드하세요"
            )
            
            # 테스트 도면 선택
            test_files = self.get_test_files()
            if test_files:
                st.write("또는 테스트 도면 선택:")
                selected_test = st.selectbox(
                    "테스트 도면",
                    ["선택하세요..."] + test_files,
                    key="test_drawing_selector"
                )
            else:
                selected_test = None

            # 이미지 로드 및 설정
            if uploaded_file is not None:
                processed_file = self.process_uploaded_file(uploaded_file)
                if processed_file is not None:
                    st.session_state.current_image = processed_file
                    # 원본 이미지 저장 (Enhanced OCR v3.0 Ultimate를 위해)
                    if isinstance(processed_file, dict) and 'image' in processed_file:
                        st.session_state.original_image = processed_file['image']
                    st.success("✅ 파일 업로드 완료")
            elif selected_test and selected_test != "선택하세요...":
                test_image = self.load_test_image(selected_test)
                if test_image is not None:
                    st.session_state.current_image = test_image
                    # 원본 이미지 저장 (Enhanced OCR v3.0 Ultimate를 위해)
                    if isinstance(test_image, dict) and 'image' in test_image:
                        st.session_state.original_image = test_image['image']
                    st.success(f"✅ {selected_test} 로드 완료")

            st.divider()

            # 2. 시스템 정보
            st.header("🖥️ 시스템 정보")
            st.write(f"**처리장치**: {self.device['info']}")
            st.write(f"**가격 DB**: {len(self.pricing_data)}개 부품")
            
            if self.device['available']:
                gpu_status = self.get_gpu_status()
                if gpu_status['available']:
                    st.write(f"**GPU 메모리**: {gpu_status['memory_used']}MB / {gpu_status['memory_total']}MB")
                    st.progress(gpu_status['memory_percent'] / 100)

            st.divider()

            # 4. 메모리 관리
            st.header("🧠 메모리 관리")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ 캐시 정리"):
                    self.clear_all_cache()
                    st.success("모든 캐시 및 세션 상태 정리 완료")
                    st.rerun()
            
            with col2:
                auto_clear = st.checkbox("자동 정리", value=True)

    def get_test_files(self):
        """테스트 파일 목록 가져오기"""
        if os.path.exists(self.test_drawings_path):
            files = []
            for file in os.listdir(self.test_drawings_path):
                if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                    files.append(file)
            return sorted(files)
        return []

    def process_uploaded_file(self, uploaded_file):
        """업로드된 파일 처리"""
        if uploaded_file.type == "application/pdf":
            # PDF를 이미지로 변환
            if PDF_AVAILABLE:
                try:
                    # PyMuPDF 사용
                    pdf_bytes = uploaded_file.getvalue()
                    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
                    
                    # 첫 페이지를 이미지로 변환
                    page = pdf_document[0]
                    mat = fitz.Matrix(2, 2)  # 200 DPI 상당의 확대
                    pix = page.get_pixmap(matrix=mat)
                    
                    # PIL 이미지로 변환
                    img_data = pix.pil_tobytes(format="PNG")
                    image = Image.open(io.BytesIO(img_data))
                    
                    pdf_document.close()
                    
                    return {"image": np.array(image), "filename": uploaded_file.name, "type": "PDF"}
                except Exception as e:
                    st.error(f"PDF 처리 중 오류가 발생했습니다: {str(e)}")
                    st.info("일시적인 오류입니다. 다시 시도하거나 이미지 파일(JPG, PNG)을 사용해주세요.")
                    return None
            else:
                st.error("⚠️ PDF 처리 라이브러리가 설치되지 않았습니다.")
                st.info("📋 해결 방법:")
                st.code("pip install PyMuPDF pdf2image", language="bash")
                st.info("🖼️ 또는 이미지 파일(JPG, PNG)을 사용해주세요.")
                return None
        else:
            # 이미지 파일 직접 로드
            image = Image.open(uploaded_file)
            return {"image": np.array(image), "filename": uploaded_file.name, "type": "Image"}

    def load_test_image(self, filename):
        """테스트 이미지 로드"""
        filepath = os.path.join(self.test_drawings_path, filename)
        if filename.lower().endswith('.pdf'):
            if PDF_AVAILABLE:
                try:
                    # PyMuPDF 사용
                    pdf_document = fitz.open(filepath)
                    
                    # 첫 페이지를 이미지로 변환
                    page = pdf_document[0]
                    mat = fitz.Matrix(2, 2)  # 200 DPI 상당의 확대
                    pix = page.get_pixmap(matrix=mat)
                    
                    # PIL 이미지로 변환
                    img_data = pix.pil_tobytes(format="PNG")
                    image = Image.open(io.BytesIO(img_data))
                    
                    pdf_document.close()
                    
                    return {"image": np.array(image), "filename": filename, "type": "PDF"}
                except Exception as e:
                    st.error(f"PDF 처리 중 오류가 발생했습니다: {str(e)}")
                    st.info("이미지 파일을 선택해주세요.")
                    return None
            else:
                st.warning("PDF 처리 라이브러리가 설치되지 않았습니다.")
                st.info("이미지 파일을 선택해주세요.")
                return None
        else:
            image = Image.open(filepath)
            return {"image": np.array(image), "filename": filename, "type": "Image"}

    def get_gpu_status(self):
        """GPU 상태 확인"""
        try:
            import subprocess
            result = subprocess.run([
                'nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                gpu_info = result.stdout.strip().split(', ')
                memory_used = int(gpu_info[0])
                memory_total = int(gpu_info[1])
                gpu_util = int(gpu_info[2])
                return {
                    "memory_used": memory_used,
                    "memory_total": memory_total,
                    "memory_percent": (memory_used / memory_total) * 100,
                    "gpu_util": gpu_util,
                    "available": True
                }
        except:
            pass
        return {"available": False}

    def clear_model_cache(self):
        """모델 캐시 정리"""
        self.loaded_models = {}

        # 세션 상태에서 모델 캐시 정리 (model_ 접두사를 가진 키들)
        model_keys_to_clear = [key for key in st.session_state.keys() if key.startswith('model_')]
        for key in model_keys_to_clear:
            del st.session_state[key]

        # Streamlit 자원 캐시 클리어
        st.cache_resource.clear()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        st.info("🧹 모든 모델 캐시가 정리되었습니다")

    def clear_all_cache(self):
        """모든 캐시 및 세션 상태 정리"""
        # 모델 캐시 정리
        self.clear_model_cache()

        # 세션 상태 초기화 (핵심 상태들만)
        session_keys_to_clear = [
            'current_image', 'selected_models', 'detection_results',
            'verified_detections', 'manual_annotations', 'edit_mode',
            'modified_classes', 'temp_class_', 'bom_data', 'bom_generated'
        ]

        for key in list(st.session_state.keys()):
            # temp_class_로 시작하는 키들도 모두 정리
            if key.startswith('temp_class_') or key in session_keys_to_clear:
                del st.session_state[key]

    def render_main_workflow(self):
        """메인 워크플로우 렌더링"""
        
        # 1. 도면 표시 섹션
        st.title("🎯 AI 기반 BOM 추출 워크플로우")
        
        if st.session_state.current_image is not None:
            self.render_drawing_display()
            st.divider()
            
            # 2. AI 모델 선택 섹션
            self.render_model_selection()
            st.divider()
            
            # 3. 검출 결과 표시
            if st.session_state.selected_models:
                self.render_detection_results()
                st.divider()
                
                # 4. 심볼 검증 섹션
                self.render_symbol_verification()
                st.divider()
                
                # 5. BOM 생성 및 내보내기
                self.render_bom_generation()
        else:
            st.info("👈 사이드바에서 도면을 업로드하거나 테스트 도면을 선택하세요.")

    def render_drawing_display(self):
        """선택된 도면 표시"""
        st.header("📋 선택된 도면")
        
        image_data = st.session_state.current_image
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 이미지 크기를 1/4로 줄이기 위해 width 파라미터 사용
            # 원본 이미지의 너비를 기준으로 25%로 표시
            original_width = image_data["image"].shape[1]
            display_width = int(original_width * 0.25)  # 1/4 크기
            st.image(image_data["image"], caption=f"📄 {image_data['filename']}", width=display_width)
        
        with col2:
            st.subheader("📊 도면 정보")
            height, width = image_data["image"].shape[:2]
            st.write(f"**파일명**: {image_data['filename']}")
            st.write(f"**형식**: {image_data['type']}")
            st.write(f"**해상도**: {width} × {height} px")
            st.write(f"**종횡비**: {width/height:.2f}")
            
            # 해상도 경고
            if width < 2000 or height < 2000:
                st.warning("⚠️ 낮은 해상도로 인해 검출 성능이 제한될 수 있습니다.")
            else:
                st.success("✅ 고해상도 이미지로 최적의 검출 성능 기대")

    def render_model_selection(self):
        """AI 모델 선택 섹션"""
        st.header("🤖 AI 모델 선택")

        available_models = self.model_registry.get_available_models()

        if not available_models:
            st.error("사용 가능한 모델이 없습니다.")
            return

        # YOLOv11X 모델만 사용
        yolo_v11x_id = 'yolo_v11x'

        if yolo_v11x_id in available_models:
            # YOLOv11X를 자동으로 선택된 모델 목록에 추가
            selected_models = [yolo_v11x_id]
            st.session_state.selected_models = selected_models

            # 검출 설정 표시
            st.divider()

            # 검출 설정 헤더에 도움말 추가
            col_header, col_info = st.columns([2, 3])
            with col_header:
                st.subheader("🎯 검출 설정")

            # YOLOv11X 최적화 설정
            st.success("✅ YOLOv11X 최적화 활성화됨")
            st.session_state['use_yolo11_approach'] = True  # YOLOv11X는 항상 최적화 모드 사용

            # 파라미터 조정
            col1, col2 = st.columns(2)
            with col1:
                confidence_threshold = st.slider(
                    "신뢰도 임계값",
                    min_value=0.3,
                    max_value=1.0,
                    value=st.session_state.get('confidence_threshold', 0.7),
                    step=0.05,
                    key="yolo11_confidence_threshold",
                    help="YOLOv11X 모델에서는 0.8 이상 권장"
                )
            with col2:
                iou_threshold = st.slider(
                    "IoU 임계값",
                    min_value=0.1,
                    max_value=0.8,
                    value=st.session_state.get('model_iou_threshold', 0.45),
                    step=0.05,
                    key="yolo11_iou_threshold",
                    help="낮을수록 더 관대한 매칭"
                )
            st.session_state.confidence_threshold = confidence_threshold
            st.session_state['model_iou_threshold'] = iou_threshold
            st.session_state.iou_threshold = iou_threshold

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🚀 검출 시작", type="primary"):
                    self.run_detection()
            with col2:
                st.empty()  # 빈 공간 유지
                    
        else:
            st.error("⚠️ YOLOv11X 모델이 없습니다. 모델 파일을 확인해주세요.")

    def run_detection(self):
        """선택된 모델들로 검출 실행"""
        if not st.session_state.current_image or not st.session_state.selected_models:
            return
            
        progress_bar = st.progress(0)
        status_text = st.empty()

        # OCR 분석 결과 초기화
        if 'ocr_analysis_results' not in st.session_state:
            st.session_state.ocr_analysis_results = []
        else:
            st.session_state.ocr_analysis_results.clear()

        results = {}
        total_models = len(st.session_state.selected_models)
        
        for i, model_id in enumerate(st.session_state.selected_models):
            status_text.text(f"검출 중: {model_id} ({i+1}/{total_models})")
            progress_bar.progress((i+1) / total_models)
            
            # 모델 로드 및 실행
            # manual 모델은 model_registry에 없으므로 별도 처리
            if model_id == 'manual':
                model_info = {
                    'name': '수작업 라벨링',
                    'emoji': '✏️',
                    'type': 'MANUAL',
                    'description': '사용자가 수동으로 추가한 검출'
                }
            else:
                model_info = self.model_registry.registry["models"][model_id]
            detections = self.detect_with_model(model_id, model_info)
            results[model_id] = detections
            
            time.sleep(0.5)  # 사용자 경험을 위한 약간의 지연
        
        # OCR 기능 제거 - 바로 결과 저장
        st.session_state.detection_results = results
        status_text.text("✅ 모든 모델 검출 완료!")

        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        st.rerun()

    def detect_with_model(self, model_id, model_info):
        """특정 모델로 검출 수행"""
        try:
            if model_info['type'] == 'YOLO':
                return self._detect_with_yolo(model_id, model_info)
            elif model_info['type'] == 'Detectron2':
                return self._detect_with_detectron2(model_id, model_info)
        except Exception as e:
            st.error(f"❌ {model_id} 검출 실패: {str(e)}")
            return []

    def _detect_with_yolo(self, model_id, model_info):
        """YOLO 모델 검출 - YOLO11-main 접근법 적용 (캐시 최적화)"""
        # 캐시에서 모델 로드 또는 기존 로드된 모델 사용
        cache_key = f"yolo_model_cache_{model_id}"
        if cache_key not in st.session_state:
            model_path = model_info['path']
            st.info(f"🔍 모델 로드 중: {model_id} from {model_path}")

            # 모델 파일 존재 확인
            if not os.path.exists(model_path):
                st.error(f"❌ 모델 파일을 찾을 수 없습니다: {model_path}")
                # 기본 모델로 대체
                model_path = "models/yolo/best.pt"
                st.warning(f"⚠️ 기본 모델 사용: {model_path}")

            # 모델 직접 로드 (캐시 함수 대신)
            try:
                st.info(f"🔄 모델 로딩 시도: {model_path}")
                from ultralytics import YOLO
                model = YOLO(model_path)

                # 모델 유효성 확인
                if not hasattr(model, 'predict'):
                    st.error(f"❌ 로드된 모델에 predict 메서드가 없습니다")
                    return []

                # GPU 사용 가능한 경우 GPU로 이동
                if torch.cuda.is_available():
                    model.to('cuda')
                    st.info(f"✅ 모델을 GPU로 이동했습니다")
                else:
                    st.info(f"ℹ️ CPU 모드로 실행됩니다")

                # 모델 저장 전 최종 검증
                if model is None or not hasattr(model, 'predict'):
                    st.error(f"❌ 로드된 모델이 유효하지 않습니다. 타입: {type(model)}")
                    return []

                # 안전한 캐시 저장
                st.session_state[cache_key] = model
                st.success(f"✅ 모델 로드 성공: {model_path}")

            except Exception as e:
                st.error(f"❌ 모델 로드 실패 ({model_path}): {e}")
                import traceback
                st.error(f"상세 오류: {traceback.format_exc()}")
                # 실패 시 캐시에 None도 저장하지 않음
                return []

        model = st.session_state[cache_key]

        # 모델 유효성 검증
        if model is None or not hasattr(model, 'predict'):
            st.error(f"❌ {model_id}: 유효하지 않은 모델입니다. 모델을 다시 로드합니다.")
            # 캐시에서 제거하고 다시 로드 시도
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            return []

        image = st.session_state.current_image['image']

        # YOLO11-main 접근법 사용 여부 (기본값: True)
        use_yolo11_approach = st.session_state.get('use_yolo11_approach', True)

        if use_yolo11_approach:
            # YOLO11-main 방식: 사용자 설정 적용, 이미지 크기 최적화
            conf_threshold = st.session_state.get('confidence_threshold', 0.7)
            iou_threshold = st.session_state.get('model_iou_threshold', 0.45)

            # 이미지 크기 최적화 (32의 배수로 조정)
            height, width = image.shape[:2]
            max_dim = max(width, height)

            # YOLO stride(32)의 배수로 조정하여 경고 방지
            max_dim = ((max_dim + 31) // 32) * 32

            # 임시 이미지 파일 저장 (파일 경로로 전달하기 위해)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                cv2.imwrite(tmp_file.name, image)
                temp_image_path = tmp_file.name

            # 디버깅 정보 표시
            st.info(f"📊 {model_id} 검출 시작 (YOLO11-main 최적화)")
            st.write(f"🔧 설정: 신뢰도={conf_threshold:.2f}, IoU={iou_threshold:.2f}, imgsz={max_dim}")
            st.write(f"🖼️ 이미지 크기: {width}x{height}, 최대 차원: {max_dim}")

            results = model.predict(
                source=temp_image_path,  # 파일 경로 사용
                conf=conf_threshold,
                iou=iou_threshold,
                imgsz=max_dim,  # 이미지 크기 설정
                device=self.device['device'],
                verbose=False,
                save=False
            )

            # 임시 파일 삭제
            try:
                os.unlink(temp_image_path)
            except:
                pass

        else:
            # 기존 DrawingBOMExtractor 방식 (낮은 confidence)
            conf_threshold = st.session_state.get('model_confidence_threshold', 0.25)
            iou_threshold = st.session_state.get('model_iou_threshold', 0.45)

            # 디버깅 정보 표시
            st.info(f"📊 {model_id} 검출 시작 (기존 방식)")
            st.write(f"🔧 설정: 신뢰도={conf_threshold:.3f}, IoU={iou_threshold:.3f}, 디바이스={self.device['device']}")
            st.write(f"🖼️ 이미지 크기: {image.shape if hasattr(image, 'shape') else 'Unknown'}")

            results = model.predict(
                source=image,
                conf=conf_threshold,
                iou=iou_threshold,
                device=self.device['device'],
                verbose=False
            )
        
        # 원시 검출 결과 로깅
        st.write(f"🔍 원시 검출 결과 수: {len(results) if results else 0}")
        if results and len(results) > 0:
            result = results[0]
            raw_detections = len(result.boxes) if result.boxes is not None else 0
            st.write(f"📦 검출된 박스 수: {raw_detections}")
            if result.boxes is not None and raw_detections > 0:
                raw_confidences = result.boxes.conf.cpu().numpy()
                st.write(f"📊 검출 신뢰도 범위: {raw_confidences.min():.3f} - {raw_confidences.max():.3f}")
        else:
            st.write("❌ 검출 결과 없음")
        
        detections = []
        st.write(f"YOLO 검출 결과 - 총 {len(results[0].boxes) if results and len(results) > 0 and results[0].boxes is not None else 0}개 객체 검출")
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy().astype(int)
                class_names = result.names
                
                for box, conf, cls in zip(boxes, confidences, classes):
                    x1, y1, x2, y2 = box.astype(int)
                    detection = {
                        'bbox': [x1, y1, x2, y2],
                        'confidence': float(conf),
                        'class_id': cls,
                        'class_name': class_names[cls],
                        'model': model_id
                    }

                    # OCR 향상 적용 (옵션)
                    if st.session_state.get('use_ocr_enhancement', True) and OCR_AVAILABLE:
                        detection = self.enhance_detection_with_ocr(image, detection)

                    detections.append(detection)
        
        return detections

    def _detect_with_detectron2(self, model_id, model_info):
        """Detectron2 모델 검출"""
        try:
            # Detectron2 import 시도
            from detectron2.config import get_cfg
            from detectron2.engine import DefaultPredictor
            from detectron2.data import MetadataCatalog
            from detectron2 import model_zoo
            
            st.info(f"ℹ️ {model_id}: Detectron2 모델 로딩 중...")
            
            # Detectron2 모델 경로
            detectron2_path = model_info['path']
            
            if not os.path.exists(detectron2_path):
                st.warning(f"⚠️ Detectron2 모델 파일이 없습니다. YOLO로 대체 실행합니다.")
                return self._fallback_to_yolo(model_id)
                
            # Detectron2 설정
            if model_id not in self.loaded_models:
                cfg = get_cfg()
                cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
                cfg.MODEL.ROI_HEADS.NUM_CLASSES = 27  # 27개 클래스
                cfg.MODEL.WEIGHTS = detectron2_path
                cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = st.session_state.get('confidence_threshold', 0.25)
                cfg.MODEL.DEVICE = self.device['device']
                
                predictor = DefaultPredictor(cfg)
                self.loaded_models[model_id] = predictor
            
            predictor = self.loaded_models[model_id]
            image = st.session_state.current_image['image']
            
            # Detectron2 예측
            outputs = predictor(image)
            
            detections = []
            instances = outputs["instances"].to("cpu")
            boxes = instances.pred_boxes.tensor.numpy()
            scores = instances.scores.numpy()
            classes = instances.pred_classes.numpy()
            
            for box, score, cls in zip(boxes, scores, classes):
                x1, y1, x2, y2 = box.tolist()
                # data.yaml의 클래스 이름 사용 (있으면)
                if self.data_yaml and 'names' in self.data_yaml:
                    class_names = self.data_yaml['names']
                    class_name = class_names[int(cls)] if int(cls) < len(class_names) else f"Unknown_{cls}"
                else:
                    # fallback to registry.json
                    class_name = self.model_registry.registry['classes']['class_names'][int(cls)]

                detection = {
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': float(score),
                    'class_id': int(cls),
                    'class_name': class_name,
                    'model': model_id
                }
                detections.append(detection)
            
            st.success(f"✅ {model_id}: {len(detections)}개 객체 검출 완료 (Detectron2)")
            return detections
            
        except ImportError:
            st.warning("⚠️ Detectron2가 설치되지 않았습니다. YOLO로 대체 실행합니다.")
            return self._fallback_to_yolo(model_id)
        except Exception as e:
            st.error(f"❌ {model_id} 실행 중 오류: {str(e)}")
            return self._fallback_to_yolo(model_id)
    
    def _fallback_to_yolo(self, model_id):
        """Detectron2 실패 시 YOLO로 대체 실행"""
        st.info("ℹ️ YOLO 모델로 대체 실행 중...")
        yolo_path = "models/yolo/best.pt"
        
        if not os.path.exists(yolo_path):
            yolo_path = "models/yolo/best.pt"  # 통합된 경로
            
        if not os.path.exists(yolo_path):
            st.error(f"❌ YOLO 모델 파일을 찾을 수 없습니다")
            return []
            
        try:
            # 캐시에서 YOLO 모델 로드
            fallback_cache_key = f"fallback_model_{model_id}_yolo"
            if fallback_cache_key not in st.session_state:
                model = load_yolo_model_cached(yolo_path)
                if model is not None:
                    st.session_state[fallback_cache_key] = model
                else:
                    st.error(f"❌ 대체 YOLO 모델 로드 실패: {yolo_path}")
                    return []

            model = st.session_state[fallback_cache_key]
            image = st.session_state.current_image['image']
            conf_threshold = st.session_state.get('confidence_threshold', 0.25)
            iou_threshold = st.session_state.get('iou_threshold', 0.45)

            results = model.predict(
                source=image,
                conf=conf_threshold,
                iou=iou_threshold,
                device=self.device['device'],
                verbose=False
            )
            
            detections = []
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    scores = result.boxes.conf.cpu().numpy()
                    classes = result.boxes.cls.cpu().numpy()
                    
                    for box, score, cls in zip(boxes, scores, classes):
                        # data.yaml의 클래스 이름 사용 (있으면)
                        if self.data_yaml and 'names' in self.data_yaml:
                            class_names = self.data_yaml['names']
                            class_name = class_names[int(cls)] if int(cls) < len(class_names) else f"Unknown_{cls}"
                        else:
                            # fallback to registry.json
                            class_name = self.model_registry.registry['classes']['class_names'][int(cls)]

                        detection = {
                            'bbox': box.tolist(),
                            'confidence': float(score),
                            'class_id': int(cls),
                            'class_name': class_name,
                            'model': model_id
                        }
                        detections.append(detection)
            
            st.success(f"✅ {len(detections)}개 객체 검출 완료 (YOLO 대체)")
            return detections
            
        except Exception as e:
            st.error(f"❌ YOLO 대체 실행 중 오류: {str(e)}")
            return []

    def render_detection_results(self):
        """검출 결과 표시"""
        st.header("🔍 AI 검출 결과")

        if not st.session_state.detection_results:
            return

        # Ground Truth 라벨 로드 (있는 경우)
        ground_truth = self.load_ground_truth_for_current_image()

        # 각 모델별 결과 표시
        for model_id, detections in st.session_state.detection_results.items():
            # manual 모델은 model_registry에 없으므로 별도 처리
            if model_id == 'manual':
                model_info = {
                    'name': '수작업 라벨링',
                    'emoji': '✏️',
                    'type': 'MANUAL',
                    'description': '사용자가 수동으로 추가한 검출'
                }
            else:
                model_info = self.model_registry.registry["models"][model_id]

            # F1 스코어 계산 (Ground Truth가 있는 경우)
            f1_score = None
            metrics = None
            if ground_truth:
                metrics = self.calculate_detection_metrics(detections, ground_truth)
                f1_score = metrics['f1_score']

            # 확장 패널 제목에 F1 스코어, 정밀도, 재현율 포함
            expander_title = f"📊 {model_info['name']} - {len(detections)}개 검출"
            if f1_score is not None:
                expander_title += f" (F1: {f1_score:.1%}, 정밀도: {metrics['precision']:.1%}, 재현율: {metrics['recall']:.1%})"

            with st.expander(expander_title, expanded=True):
                if detections or ground_truth:
                    # 디버깅: Ground Truth 상태 표시
                    if ground_truth:
                        st.info(f"✅ Ground Truth 로드됨: {len(ground_truth)}개 라벨")
                    else:
                        st.warning("⚠️ Ground Truth 없음")

                    # Ground Truth가 있으면 분리 표시, 없으면 기존 방식
                    if ground_truth:
                        # Ground Truth와 예측을 분리하여 표시
                        col_gt, col_det = st.columns(2)

                        with col_gt:
                            # Ground Truth만 표시 (초록색, 두꺼운 선)
                            gt_image = self.draw_ground_truth_only(
                                st.session_state.current_image['image'].copy(),
                                ground_truth
                            )
                            gt_width = gt_image.shape[1]
                            gt_display_width = int(gt_width * 0.25)
                            st.image(gt_image, caption=f"🟢 Ground Truth ({len(ground_truth)}개)", width=gt_display_width)

                        with col_det:
                            # 검출 결과만 표시 (빨간색, 두꺼운 선)
                            det_image = self.draw_detections_only(
                                st.session_state.current_image['image'].copy(),
                                detections
                            )
                            det_width = det_image.shape[1]
                            det_display_width = int(det_width * 0.25)
                            st.image(det_image, caption=f"🔴 {model_info['name']} 검출 ({len(detections)}개)", width=det_display_width)
                    else:
                        # 기존 방식: 다양한 색상으로 표시
                        result_image = self.draw_detection_results(
                            st.session_state.current_image['image'].copy(),
                            detections
                        )
                        caption = f"{model_info['name']} 검출 결과"

                        # 검출 결과 이미지도 1/4 크기로 표시
                        result_width = result_image.shape[1]
                        display_width = int(result_width * 0.25)
                        st.image(result_image, caption=caption, width=display_width)

                    # 검출 통계 및 정확도 메트릭
                    if f1_score is not None:
                        # Ground Truth가 있을 때: 4개 컬럼
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("총 검출 수", len(detections))
                        with col2:
                            avg_conf = safe_mean([d['confidence'] for d in detections])
                            st.metric("평균 신뢰도", f"{avg_conf:.3f}")
                        with col3:
                            st.metric("Precision", f"{metrics['precision']:.1%}")
                        with col4:
                            st.metric("Recall", f"{metrics['recall']:.1%}")

                        # F1 스코어를 강조 표시
                        st.success(f"🎯 F1 Score: {f1_score:.1%} (TP:{metrics['true_positives']}, FP:{metrics['false_positives']}, FN:{metrics['false_negatives']})")
                    else:
                        # Ground Truth가 없을 때: 기존처럼 3개 컬럼
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("총 검출 수", len(detections))
                        with col2:
                            avg_conf = safe_mean([d['confidence'] for d in detections])
                            st.metric("평균 신뢰도", f"{avg_conf:.3f}")
                        with col3:
                            unique_classes = len(set(d['class_name'] for d in detections))
                            st.metric("검출 클래스 수", unique_classes)
                else:
                    st.info("검출된 객체가 없습니다.")

    def draw_detection_results(self, image, detections):
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

    def create_final_verified_image(self, detections, prefix):
        """최종 검증된 결과를 시각화 (승인/거부/수정/수작업 포함)"""
        if not st.session_state.get('current_image'):
            return None

        image = st.session_state.current_image['image'].copy()

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

    def draw_detection_with_ground_truth(self, image, detections, ground_truth):
        """Ground Truth와 모델 예측을 함께 시각화"""
        img_height, img_width = image.shape[:2]

        # 1. Ground Truth 그리기 (초록색, 두꺼운 선)
        for gt in ground_truth:
            x1, y1, x2, y2 = self.yolo_to_xyxy(
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

    def load_ground_truth_for_current_image(self):
        """현재 이미지에 대한 Ground Truth 라벨 로드"""
        if not st.session_state.current_image:
            return None

        # 이미지 파일명에서 라벨 파일명 추출
        image_filename = st.session_state.current_image.get('filename', '')
        if not image_filename:
            return None

        # 라벨 파일 경로 구성
        label_filename = os.path.splitext(image_filename)[0] + '.txt'
        label_path = os.path.join(self.test_drawings_path, 'labels', label_filename)

        if not os.path.exists(label_path):
            return None

        # YOLO 형식 라벨 로드
        ground_truth = []
        try:
            with open(label_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 5:
                            class_id = int(parts[0])
                            # data.yaml에서 클래스 이름 가져오기
                            class_name = str(class_id)  # 기본값
                            if self.data_yaml and 'names' in self.data_yaml:
                                class_names = self.data_yaml['names']
                                if class_id < len(class_names):
                                    class_name = class_names[class_id]

                            ground_truth.append({
                                'class_id': class_id,
                                'class_name': class_name,
                                'x_center': float(parts[1]),
                                'y_center': float(parts[2]),
                                'width': float(parts[3]),
                                'height': float(parts[4])
                            })
            return ground_truth if ground_truth else None
        except Exception as e:
            st.warning(f"라벨 파일 로드 오류: {e}")
            return None

    def yolo_to_xyxy(self, x_center, y_center, width, height, img_width, img_height):
        """YOLO 형식을 xyxy 좌표로 변환 (더 정확한 반올림 적용)"""
        x_center_abs = x_center * img_width
        y_center_abs = y_center * img_height
        width_abs = width * img_width
        height_abs = height * img_height

        # round()를 사용하여 더 정확한 좌표 계산
        x1 = round(x_center_abs - width_abs / 2)
        y1 = round(y_center_abs - height_abs / 2)
        x2 = round(x_center_abs + width_abs / 2)
        y2 = round(y_center_abs + height_abs / 2)

        # 이미지 경계 내로 제한
        x1 = max(0, min(x1, img_width - 1))
        y1 = max(0, min(y1, img_height - 1))
        x2 = max(0, min(x2, img_width - 1))
        y2 = max(0, min(y2, img_height - 1))

        return x1, y1, x2, y2

    def calculate_detection_metrics(self, predictions, ground_truth, iou_threshold=0.3):
        """예측과 Ground Truth를 비교하여 정확도 메트릭 계산"""
        if not predictions or not ground_truth:
            return {
                'true_positives': 0,
                'false_positives': len(predictions) if predictions else 0,
                'false_negatives': len(ground_truth) if ground_truth else 0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0
            }

        # 이미지 크기 가져오기
        image = st.session_state.current_image.get('image')
        if image is None:
            return {
                'true_positives': 0,
                'false_positives': len(predictions),
                'false_negatives': len(ground_truth),
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0
            }

        img_height, img_width = image.shape[:2]

        true_positives = 0
        false_positives = len(predictions)
        false_negatives = len(ground_truth)
        matched_gt = set()

        # 각 예측에 대해 가장 잘 매칭되는 GT 찾기
        for pred in predictions:
            best_iou = 0
            best_gt_idx = -1

            pred_bbox = pred.get('bbox', [0, 0, 0, 0])
            pred_class_id = pred.get('class_id', -1)

            # 모든 GT와 비교
            for gt_idx, gt in enumerate(ground_truth):
                if gt_idx not in matched_gt:
                    # GT bbox를 xyxy로 변환
                    gt_bbox = self.yolo_to_xyxy(
                        gt['x_center'], gt['y_center'],
                        gt['width'], gt['height'],
                        img_width, img_height
                    )

                    # IoU 계산
                    iou = self.calculate_iou(pred_bbox, gt_bbox)

                    # 같은 클래스이고 IoU가 더 높으면 업데이트
                    if pred_class_id == gt['class_id'] and iou > best_iou:
                        best_iou = iou
                        best_gt_idx = gt_idx

            # IoU 임계값을 넘고 매칭되면 TP
            if best_iou >= iou_threshold and best_gt_idx >= 0:
                true_positives += 1
                matched_gt.add(best_gt_idx)
                false_positives -= 1
                false_negatives -= 1

        # 메트릭 계산
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score
        }

    def calculate_iou(self, box1, box2):
        """두 바운딩 박스의 IoU(Intersection over Union) 계산"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    def remove_duplicate_detections(self, detections, iou_threshold=0.5):
        """중복 검출 제거 (IoU 기반)"""
        if not detections:
            return []

        # 신뢰도 순으로 정렬
        sorted_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)

        unique_detections = []
        for detection in sorted_detections:
            is_duplicate = False
            for unique in unique_detections:
                if self.calculate_iou(detection['bbox'], unique['bbox']) > iou_threshold:
                    # 같은 클래스인 경우만 중복으로 처리
                    if detection['class_name'] == unique['class_name']:
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique_detections.append(detection)

        return unique_detections

    def remove_duplicate_detections_with_voting(self, detections, iou_threshold=0.5, min_votes=2):
        """Voting과 Weighted Ensemble을 사용한 중복 검출 제거"""
        if not detections:
            return [], {}

        # 검출 그룹 생성 (IoU 기반)
        detection_groups = []
        for detection in detections:
            added_to_group = False
            for group in detection_groups:
                # 그룹의 첫 번째 검출과 비교
                if self.calculate_iou(detection['bbox'], group[0]['bbox']) > iou_threshold:
                    # 같은 클래스이거나 비슷한 위치인 경우 그룹에 추가
                    group.append(detection)
                    added_to_group = True
                    break

            if not added_to_group:
                detection_groups.append([detection])

        # 각 그룹에 대해 Voting 수행
        unique_detections = []
        voting_info = {}

        for group_idx, group in enumerate(detection_groups):
            if len(group) >= min_votes:
                # 클래스별 투표 수 계산
                class_votes = {}
                weighted_scores = {}

                for detection in group:
                    class_name = detection['class_name']
                    model_id = detection.get('model_id', 'unknown')
                    weight = self.model_weights.get(model_id, 1.0)

                    if class_name not in class_votes:
                        class_votes[class_name] = 0
                        weighted_scores[class_name] = 0

                    class_votes[class_name] += 1
                    weighted_scores[class_name] += detection['confidence'] * weight

                # 가장 많은 투표를 받은 클래스 선택
                best_class = max(class_votes.keys(), key=lambda k: (class_votes[k], weighted_scores[k]))

                # 해당 클래스의 가장 높은 신뢰도를 가진 검출 선택
                best_detection = None
                best_weighted_score = 0

                for detection in group:
                    if detection['class_name'] == best_class:
                        model_id = detection.get('model_id', 'unknown')
                        weight = self.model_weights.get(model_id, 1.0)
                        weighted_score = detection['confidence'] * weight

                        if weighted_score > best_weighted_score:
                            best_weighted_score = weighted_score
                            best_detection = detection.copy()

                if best_detection:
                    # Voting 정보 추가
                    best_detection['voting_info'] = {
                        'total_votes': len(group),
                        'class_votes': class_votes,
                        'weighted_scores': weighted_scores,
                        'models_agreed': [d.get('model_id', 'unknown') for d in group]
                    }
                    unique_detections.append(best_detection)
                    voting_info[f"group_{group_idx}"] = best_detection['voting_info']

        return unique_detections, voting_info

    def render_symbol_verification(self):
        """심볼 검증 섹션"""
        st.header("✅ 심볼 검증 및 수정")

        # 승인/거부 상태 초기화
        if 'verification_status' not in st.session_state:
            st.session_state.verification_status = {}

        # 편집 상태 초기화
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = {}

        # 수정된 클래스 이름 저장
        if 'modified_classes' not in st.session_state:
            st.session_state.modified_classes = {}

        # 검출 결과가 없으면 리턴
        if not st.session_state.detection_results:
            st.info("검출된 심볼이 없습니다.")
            return

        # 메인 컨텐츠와 사이드 패널로 레이아웃 분리
        main_col, side_panel = st.columns([4, 1])  # 80% 메인, 20% 사이드

        with side_panel:
            # 심볼 참조 리스트 표시
            self.render_symbol_reference_panel()

        with main_col:
            # 탭으로 모델별 결과와 통합 결과 구분
            # 탭 리스트 생성 - 고정 탭 3개 + 모델별 탭
            fixed_tabs = ["📊 통합 결과 (중복 제거)", "🗳️ Voting 기반 통합", "🔍 OCR 키워드 분석"]
            model_tabs = []
            for model_id in st.session_state.detection_results.keys():
                # manual 모델은 model_registry에 없으므로 별도 처리
                if model_id == 'manual':
                    model_info = {
                        'name': '수작업 라벨링',
                        'emoji': '✏️',
                        'type': 'MANUAL',
                        'description': '사용자가 수동으로 추가한 검출'
                    }
                else:
                    model_info = self.model_registry.registry["models"][model_id]
                model_tabs.append(f"🤖 {model_info['name']}")

            all_tabs = fixed_tabs + model_tabs
            tabs = st.tabs(all_tabs)

            # 통합 결과 탭
            with tabs[0]:
                # 모든 검출 결과를 하나의 리스트로 합치기
                all_detections = []
            for model_id, detections in st.session_state.detection_results.items():
                for detection in detections:
                    detection_with_model = detection.copy()
                    detection_with_model['model_id'] = model_id
                    all_detections.append(detection_with_model)

            if not all_detections:
                st.info("검출된 심볼이 없습니다.")
            else:
                # 중복 제거
                unique_detections = self.remove_duplicate_detections(all_detections)

                # 통계 표시
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("전체 검출", len(all_detections))
                with col2:
                    st.metric("중복 제거 후", len(unique_detections))
                with col3:
                    if len(all_detections) > 0:
                        st.metric("중복률", f"{((len(all_detections)-len(unique_detections))/len(all_detections)*100):.1f}%")

                st.write(f"중복 제거 후 {len(unique_detections)}개의 고유한 심볼이 검출되었습니다:")

                # 일괄 처리 버튼
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔘 모두 승인", key="approve_all_unified"):
                        for i, detection in enumerate(unique_detections):
                            st.session_state.verification_status[f"unified_{i}"] = "approved"
                        st.success("모든 검출이 승인되었습니다.")
                        st.rerun()
                with col2:
                    if st.button("❌ 모두 거부", key="reject_all_unified"):
                        for i, detection in enumerate(unique_detections):
                            st.session_state.verification_status[f"unified_{i}"] = "rejected"
                        st.warning("모든 검출이 거부되었습니다.")
                        st.rerun()
                with col3:
                    if st.button("🔄 상태 초기화", key="reset_status_unified"):
                        # 통합 결과 상태만 초기화
                        keys_to_remove = [k for k in st.session_state.verification_status.keys() if k.startswith("unified_")]
                        for k in keys_to_remove:
                            del st.session_state.verification_status[k]
                        st.info("상태가 초기화되었습니다.")
                        st.rerun()

                # 검출 결과 표시
                self.render_detection_list(unique_detections, "unified")

                # 최종 통합 이미지 표시
                st.divider()
                st.subheader("🖼️ 최종 검증 결과 이미지")

                # 최종 이미지 생성 (승인/거부/수정/수작업 모두 포함)
                final_image = self.create_final_verified_image(unique_detections, "unified")
                if final_image is not None:
                    st.image(final_image, caption="최종 검증 결과 (✅승인 ❌거부 ✏️수정 🎨수작업)")
                else:
                    st.info("검출된 결과가 없습니다.")

        # Voting 기반 통합 탭
        with tabs[1]:
            st.subheader("🗳️ Voting & Weighted Ensemble")

            # Voting 설정
            col1, col2 = st.columns(2)
            with col1:
                min_votes = st.slider("최소 투표 수", min_value=1, max_value=4, value=2,
                                     help="검출을 유효하게 만들기 위한 최소 모델 수")
            with col2:
                st.info(f"현재 {len(st.session_state.detection_results)}개 모델에서 검출 중")

            # 모델 가중치 설정 섹션
            with st.expander("⚙️ 모델 가중치 설정", expanded=False):
                st.write("각 모델의 가중치를 설정하여 Weighted Ensemble의 성능을 조정할 수 있습니다.")

                # 가중치 오버라이드를 위한 세션 상태
                if 'model_weights_override' not in st.session_state:
                    st.session_state.model_weights_override = self.model_weights.copy()

                # 각 모델에 대한 가중치 슬라이더
                for model_id in st.session_state.detection_results.keys():
                    # manual 모델은 model_registry에 없으므로 별도 처리
                    if model_id == 'manual':
                        model_info = {
                            'name': '수작업 라벨링',
                            'emoji': '✏️',
                            'type': 'MANUAL',
                            'description': '사용자가 수동으로 추가한 검출'
                        }
                    else:
                        model_info = self.model_registry.registry["models"][model_id]
                    current_weight = st.session_state.model_weights_override.get(model_id, 1.0)

                    new_weight = st.slider(
                        f"{model_info['name']} 가중치",
                        min_value=0.1,
                        max_value=2.0,
                        value=current_weight,
                        step=0.1,
                        key=f"weight_{model_id}",
                        help=f"{model_info['description']}"
                    )
                    st.session_state.model_weights_override[model_id] = new_weight

                # 가중치 초기화 버튼
                if st.button("🔄 기본값으로 초기화", key="reset_weights"):
                    st.session_state.model_weights_override = self.model_weights.copy()
                    st.rerun()

                # 현재 가중치 표시
                st.write("현재 설정된 가중치:")
                for model_id, weight in st.session_state.model_weights_override.items():
                    if model_id in st.session_state.detection_results:
                        # manual 모델은 model_registry에 없으므로 별도 처리
                        if model_id == 'manual':
                            model_info = {
                                'name': '수작업 라벨링',
                                'emoji': '✏️',
                                'type': 'MANUAL',
                                'description': '사용자가 수동으로 추가한 검출'
                            }
                        else:
                            model_info = self.model_registry.registry["models"][model_id]
                        st.write(f"  - {model_info['name']}: **{weight:.1f}**")

            # 모든 검출 결과를 하나의 리스트로 합치기
            all_detections_voting = []
            for model_id, detections in st.session_state.detection_results.items():
                for detection in detections:
                    detection_with_model = detection.copy()
                    detection_with_model['model_id'] = model_id
                    all_detections_voting.append(detection_with_model)

            if not all_detections_voting:
                st.info("검출된 심볼이 없습니다.")
            else:
                # 세션 상태의 가중치를 임시로 사용
                original_weights = self.model_weights.copy()
                if 'model_weights_override' in st.session_state:
                    self.model_weights = st.session_state.model_weights_override.copy()

                # Voting 기반 중복 제거
                unique_detections_voting, voting_info = self.remove_duplicate_detections_with_voting(
                    all_detections_voting, min_votes=min_votes)

                # 원래 가중치로 복원
                self.model_weights = original_weights

                # 통계 표시
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("전체 검출", len(all_detections_voting))
                with col2:
                    st.metric("Voting 통과", len(unique_detections_voting))
                with col3:
                    if len(all_detections_voting) > 0:
                        st.metric("필터링 비율", f"{((len(all_detections_voting)-len(unique_detections_voting))/len(all_detections_voting)*100):.1f}%")
                with col4:
                    if unique_detections_voting:
                        avg_votes = safe_mean([d['voting_info']['total_votes'] for d in unique_detections_voting])
                        st.metric("평균 투표 수", f"{avg_votes:.1f}")

                st.write(f"Voting을 통과한 {len(unique_detections_voting)}개의 심볼이 검출되었습니다:")

                # 일괄 처리 버튼
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔘 모두 승인", key="approve_all_voting"):
                        for i, detection in enumerate(unique_detections_voting):
                            st.session_state.verification_status[f"voting_{i}"] = "approved"
                        st.success("모든 검출이 승인되었습니다.")
                        st.rerun()
                with col2:
                    if st.button("❌ 모두 거부", key="reject_all_voting"):
                        for i, detection in enumerate(unique_detections_voting):
                            st.session_state.verification_status[f"voting_{i}"] = "rejected"
                        st.warning("모든 검출이 거부되었습니다.")
                        st.rerun()
                with col3:
                    if st.button("🔄 상태 초기화", key="reset_status_voting"):
                        # Voting 결과 상태만 초기화
                        keys_to_remove = [k for k in st.session_state.verification_status.keys() if k.startswith("voting_")]
                        for k in keys_to_remove:
                            del st.session_state.verification_status[k]
                        st.info("상태가 초기화되었습니다.")
                        st.rerun()

                # Voting 결과를 포함한 검출 리스트 표시
                self.render_detection_list_with_voting(unique_detections_voting, "voting")

        # OCR 키워드 분석 탭
        with tabs[2]:
            self.render_enhanced_ocr_analysis()

        # 각 모델별 결과 탭 (고정 탭 3개 이후부터 시작)
        for tab_idx, (model_id, detections) in enumerate(st.session_state.detection_results.items()):
            actual_tab_idx = tab_idx + 3  # 고정 탭 3개 다음부터
            with tabs[actual_tab_idx]:
                # manual 모델은 model_registry에 없으므로 별도 처리
                if model_id == 'manual':
                    model_info = {
                        'name': '수작업 라벨링',
                        'emoji': '✏️',
                        'type': 'MANUAL',
                        'description': '사용자가 수동으로 추가한 검출'
                    }
                else:
                    model_info = self.model_registry.registry["models"][model_id]

                if not detections:
                    st.info(f"{model_info['name']} 모델에서 검출된 심볼이 없습니다.")
                else:
                    # 모델별 통계
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("검출 수", len(detections))
                    with col2:
                        avg_conf = np.mean([d['confidence'] for d in detections])
                        st.metric("평균 신뢰도", f"{avg_conf:.3f}")
                    with col3:
                        unique_classes = len(set(d['class_name'] for d in detections))
                        st.metric("검출 클래스 수", unique_classes)

                    # 모델별 일괄 처리 버튼
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🔘 모두 승인", key=f"approve_all_{model_id}"):
                            for i, detection in enumerate(detections):
                                st.session_state.verification_status[f"{model_id}_{i}"] = "approved"
                            st.success(f"{model_info['name']}의 모든 검출이 승인되었습니다.")
                            st.rerun()
                    with col2:
                        if st.button("❌ 모두 거부", key=f"reject_all_{model_id}"):
                            for i, detection in enumerate(detections):
                                st.session_state.verification_status[f"{model_id}_{i}"] = "rejected"
                            st.warning(f"{model_info['name']}의 모든 검출이 거부되었습니다.")
                            st.rerun()
                    with col3:
                        if st.button("🔄 상태 초기화", key=f"reset_status_{model_id}"):
                            # 해당 모델 상태만 초기화
                            keys_to_remove = [k for k in st.session_state.verification_status.keys() if k.startswith(f"{model_id}_")]
                            for k in keys_to_remove:
                                del st.session_state.verification_status[k]
                            st.info("상태가 초기화되었습니다.")
                            st.rerun()

                    # 검출 결과 표시
                    # 모델 ID를 추가한 검출 결과
                    detections_with_model = []
                    for detection in detections:
                        det = detection.copy()
                        det['model_id'] = model_id
                        detections_with_model.append(det)
                    self.render_detection_list(detections_with_model, model_id)

    def render_enhanced_ocr_analysis(self):
        """통합된 Enhanced OCR 분석 결과 표시"""
        st.subheader("🔍 Enhanced OCR 분석")

        # Enhanced OCR 결과가 없으면 안내 메시지
        if 'enhanced_ocr_results' not in st.session_state or not st.session_state.enhanced_ocr_results:
            st.info("👀 Enhanced OCR 분석 결과가 없습니다.")
            st.markdown("""
            **Enhanced OCR 분석을 보려면:**
            1. 🎯 **검출 설정** 에서 `🔍 Enhanced OCR 텍스트 인식 향상` 체크박스를 활성화
            2. AI 검출을 실행하여 Enhanced OCR 이중 임계값 검출 + Ground Truth 매칭 수행
            3. 이 탭에서 분석 결과 확인

            **Enhanced OCR 특징:**
            - 이중 임계값 검출 (0.25 일반 / 0.1 후보)
            - PaddleOCR API를 통한 정확한 텍스트 추출
            - Ground Truth 데이터베이스와 매칭하여 신뢰도 향상
            - 15개 CAD 심볼에 대한 검증된 정답지 활용
            """)
            return

        # Enhanced OCR 결과 통계
        st.markdown("### 📊 Enhanced OCR 통계")
        col1, col2, col3, col4 = st.columns(4)

        enhanced_results = st.session_state.enhanced_ocr_results
        primary_detections = enhanced_results.get('primary_detections', [])
        ocr_candidates = enhanced_results.get('ocr_candidates', [])
        verified_detections = enhanced_results.get('verified_detections', [])

        total_primary = len(primary_detections)
        total_candidates = len(ocr_candidates)
        total_verified = len(verified_detections)

        with col1:
            st.metric("일반 검출", total_primary)
        with col2:
            st.metric("OCR 후보", total_candidates)
        with col3:
            st.metric("OCR 검증 성공", total_verified)
        with col4:
            verification_rate = (total_verified / total_candidates * 100) if total_candidates > 0 else 0
            st.metric("검증 성공률", f"{verification_rate:.1f}%")

        # 필터링 옵션
        st.markdown("### 🔧 필터링 옵션")
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            show_primary = st.checkbox("🎯 일반 검출 표시", value=True)
        with filter_col2:
            show_verified = st.checkbox("✅ OCR 검증 검출 표시", value=True)

        # 결과 필터링
        filtered_results = []
        if show_primary:
            for det in primary_detections:
                det['detection_type'] = 'primary'
                filtered_results.append(det)
        if show_verified:
            for det in verified_detections:
                det['detection_type'] = 'ocr_verified'
                filtered_results.append(det)

        # Enhanced OCR 상세 결과 섹션은 제거됨 - 메인 검출 결과 테이블에 통합됨

        # Enhanced OCR Ground Truth 규칙 표시
        st.markdown("### 📖 Enhanced OCR Ground Truth 매칭 규칙")
        with st.expander("Ground Truth 매칭 규칙 보기"):
            st.markdown("""
            **Enhanced OCR 이중 임계값 검출:**
            - **일반 검출**: 신뢰도 0.25 이상 (1차 검출)
            - **후보 검출**: 신뢰도 0.1 이상 (OCR 검증용)

            **PaddleOCR 텍스트 추출:**
            - API 엔드포인트: http://localhost:8001/ocr
            - 최소 신뢰도: 0.3 (낮은 임계값으로 더 많은 텍스트 포착)

            **Ground Truth 매칭 규칙:**
            - **HUB-8PORT**: "8.A", "8-A", "8A" → 신뢰도 0.95
            - **CPU1513-1PN**: "1513 1PN CP", "CP 1513 -IPN" → 신뢰도 0.95
            - **CPU1214C**: "CPU-1214C", "CPU-I214C" → 신뢰도 0.95
            - **TERMINAL_ST4**: "ST4", "ST-4", "32A" → 신뢰도 0.85
            - **BREAKER**: "BK63H", "BK-63H", "63H" → 신뢰도 0.90
            - **TRANSFORMER**: "MST600VA", "MST-600VA", "600VA" → 신뢰도 0.85

            ⚡ **매칭 알고리즘**:
            1. 클래스명 정규화 (언더스코어 → 공백)
            2. 텍스트 유사도 계산 (Levenshtein 거리)
            3. 부분 일치 확인 (0.7 임계값)
            4. 신뢰도 부스트 적용
            """)

    def render_symbol_reference_panel(self):
        """오른쪽 사이드 패널에 심볼 참조 리스트 표시"""
        st.markdown("### 📚 심볼 참조")
        st.caption("승인/거부 시 참고용")

        # class_examples 폴더의 모든 이미지 로드
        import glob
        from PIL import Image
        example_images = glob.glob(os.path.join(self.class_examples_path, "*.jpg"))
        example_images.sort()  # 파일명 순으로 정렬

        if not example_images:
            st.info("심볼 이미지가 없습니다.")
            return

        # 스크롤 가능한 컨테이너 생성
        with st.container():
            for img_path in example_images:
                filename = os.path.basename(img_path)
                # 파일명에서 정보 추출
                parts = filename.replace('.jpg', '').split('_')
                if len(parts) >= 3:
                    class_idx = parts[0].replace('class_', '')
                    class_nums = parts[1]
                    class_name = '_'.join(parts[2:])

                    # 이미지 크기 조정 (1/2 크기로 변경)
                    img = Image.open(img_path)
                    width, height = img.size
                    new_width = width // 2
                    new_height = height // 2
                    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    # 클래스 번호와 이름을 크게 표시
                    st.markdown(f"**<span style='font-size: 20px;'>{class_idx}</span>**", unsafe_allow_html=True)
                    st.markdown(f"<span style='font-size: 16px;'>{class_name}</span>", unsafe_allow_html=True)

                    # 이미지 표시 (고정 크기)
                    st.image(img_resized)
                    st.markdown("---")  # 구분선
                else:
                    # 이미지 크기 조정 (1/2 크기로 변경)
                    img = Image.open(img_path)
                    width, height = img.size
                    img_resized = img.resize((width // 2, height // 2), Image.Resampling.LANCZOS)
                    st.image(img_resized, caption=filename)
                    st.markdown("---")

    def get_class_example_image(self, class_name):
        """클래스별 실제 심볼 이미지 찾기

        class_examples 폴더에서 패턴 매칭으로 이미지 찾기:
        - 패턴: class_XX_YY_CLASS_NAME_*.jpg
        - 예: class_13_24,25_GRAPHIC PANEL_6AV7240-3MC07-0HA0(GP)_p01.jpg
        """
        if not os.path.exists(self.class_examples_path):
            return None

        # 클래스 이름으로 직접 매칭 시도
        import glob

        # 파일명에서 사용할 수 없는 문자 처리
        safe_name = class_name.replace('/', '_').replace('\\', '_').replace(':', '_')

        # 여러 패턴으로 시도
        patterns = [
            # 정확한 클래스 이름 매칭
            f"*_{safe_name}_*.jpg",
            # 부분 매칭 (공백 제거)
            f"*_{safe_name.replace(' ', '*')}*.jpg",
            # 클래스 이름의 일부만 매칭
            f"*{safe_name.split()[0] if ' ' in safe_name else safe_name}*.jpg"
        ]

        for pattern in patterns:
            matching_files = glob.glob(os.path.join(self.class_examples_path, pattern))
            if matching_files:
                # 첫 번째 매칭 파일 반환
                return matching_files[0]

        # data.yaml 기반 검색 (fallback)
        if self.data_yaml:
            class_names = self.data_yaml.get('names', [])
            try:
                class_idx = class_names.index(class_name)
                # 인덱스 기반 패턴으로 검색
                pattern = f"class_{class_idx:02d}_*.jpg"
                matching_files = glob.glob(os.path.join(self.class_examples_path, pattern))
                if matching_files:
                    return matching_files[0]
            except (ValueError, IndexError):
                pass

        return None

    def load_ground_truth_labels(self, image_filename):
        """정답 라벨 로드 및 파싱"""
        # 이미지 파일명에서 확장자 제거
        base_name = os.path.splitext(image_filename)[0]
        label_path = os.path.join(self.test_drawings_path, "labels", f"{base_name}.txt")

        ground_truth = []
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 5:
                            class_id = int(parts[0])
                            x_center = float(parts[1])
                            y_center = float(parts[2])
                            width = float(parts[3])
                            height = float(parts[4])

                            # 이미지 크기로 절대 좌표 변환
                            if st.session_state.current_image:
                                img_h, img_w = st.session_state.current_image['image'].shape[:2]
                                x1 = int((x_center - width/2) * img_w)
                                y1 = int((y_center - height/2) * img_h)
                                x2 = int((x_center + width/2) * img_w)
                                y2 = int((y_center + height/2) * img_h)

                                # data.yaml의 클래스 이름 사용
                                if self.data_yaml and 'names' in self.data_yaml:
                                    class_names = self.data_yaml['names']
                                    if class_id < len(class_names):
                                        ground_truth.append({
                                            'class_id': class_id,
                                            'class_name': class_names[class_id],
                                            'bbox': [x1, y1, x2, y2],
                                            'confidence': 1.0,  # 정답은 100% 신뢰도
                                            'is_ground_truth': True
                                        })
        return ground_truth

    def render_detection_list(self, detections, prefix):
        """검출 결과를 리스트 형태로 표시 (정답 비교 포함)"""
        import os  # 함수 내에서 명시적으로 import
        # 검출 결과를 리스트 형태로 표시
        st.subheader("🔍 검출 결과")
        for i, detection in enumerate(detections):
            status_key = f"{prefix}_{i}"
            current_status = st.session_state.verification_status.get(status_key, "pending")

            # 상태에 따른 컨테이너 스타일
            if current_status == "approved":
                container_style = "background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; margin-bottom: 10px;"
            elif current_status == "rejected":
                container_style = "background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; margin-bottom: 10px;"
            else:
                container_style = "background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; border-radius: 5px; margin-bottom: 10px;"

            with st.container():
                col1, col2, col3, col4 = st.columns([2, 4, 2, 2])

                with col1:
                    # 검출된 이미지와 정답 이미지를 나란히 표시
                    x1, y1, x2, y2 = detection['bbox']
                    image = st.session_state.current_image['image']
                    h, w = image.shape[:2]
                    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
                    cropped = image[y1:y2, x1:x2]

                    # 이미지를 가로로 표시하기 위한 구조
                    st.write("**🔍 검출 결과**")

                    # 세 개의 이미지를 준비
                    images_to_show = []
                    captions = []

                    # 1. Ground Truth 이미지
                    ground_truth = self.load_ground_truth_for_current_image()
                    gt_img = None
                    if ground_truth:
                        # 현재 검출 위치와 가장 가까운 Ground Truth 찾기
                        best_gt = None
                        best_iou = 0
                        # 검출 bbox를 정수로 변환
                        det_bbox = [int(x) for x in detection['bbox']]

                        for gt in ground_truth:
                            gt_bbox = self.yolo_to_xyxy(
                                gt['x_center'], gt['y_center'],
                                gt['width'], gt['height'],
                                w, h
                            )
                            iou = self.calculate_iou(det_bbox, gt_bbox)
                            if iou > best_iou:
                                best_iou = iou
                                best_gt = gt

                        # IoU 임계값을 0.1로 낮춤 (10% 이상 겹치면 매칭)
                        if best_gt and best_iou > 0.1:
                            # Ground Truth 박스 영역 crop
                            gt_x1, gt_y1, gt_x2, gt_y2 = self.yolo_to_xyxy(
                                best_gt['x_center'], best_gt['y_center'],
                                best_gt['width'], best_gt['height'],
                                w, h
                            )
                            gt_x1, gt_y1, gt_x2, gt_y2 = max(0, gt_x1), max(0, gt_y1), min(w, gt_x2), min(h, gt_y2)
                            gt_cropped = image[gt_y1:gt_y2, gt_x1:gt_x2]
                            if gt_cropped.size > 0:
                                gt_img = gt_cropped
                                images_to_show.append(gt_cropped)
                                captions.append(f"🏷️ GT: {best_gt['class_name']} (IoU:{best_iou:.2f})")

                    if gt_img is None:
                        # GT 이미지가 없을 때 placeholder
                        import numpy as np
                        placeholder = np.ones((100, 100, 3), dtype=np.uint8) * 200
                        images_to_show.append(placeholder)
                        captions.append("🏷️ GT: 없음")

                    # 2. 모델 검출 결과
                    if cropped.size > 0:
                        images_to_show.append(cropped)
                        captions.append(f"🔍 검출: {detection['class_name']}")
                    else:
                        import numpy as np
                        placeholder = np.ones((100, 100, 3), dtype=np.uint8) * 200
                        images_to_show.append(placeholder)
                        captions.append("🔍 검출: 오류")

                    # 3. 실제 심볼 이미지
                    example_path = self.get_class_example_image(detection['class_name'])
                    if example_path and os.path.exists(example_path):
                        example_img = Image.open(example_path)
                        # numpy array로 변환
                        import numpy as np
                        example_np = np.array(example_img)
                        images_to_show.append(example_np)
                        captions.append(f"📚 실제: {detection['class_name']}")
                    else:
                        import numpy as np
                        placeholder = np.ones((100, 100, 3), dtype=np.uint8) * 200
                        images_to_show.append(placeholder)
                        captions.append("📚 실제: 없음")

                    # 이미지들을 가로로 표시 - HTML과 base64 인코딩 사용
                    import base64
                    from io import BytesIO
                    import numpy as np

                    # HTML 구조를 더 안정적으로 구성
                    html_parts = ['<div style="display: flex; gap: 15px; align-items: center; margin: 10px 0;">']

                    for img, cap in zip(images_to_show, captions):
                        # numpy array를 PIL Image로 변환
                        if isinstance(img, np.ndarray):
                            if img.ndim == 2:  # grayscale
                                img_pil = Image.fromarray(img.astype(np.uint8))
                            else:  # color
                                img_pil = Image.fromarray(img.astype(np.uint8))
                        else:
                            img_pil = img

                        # 이미지를 base64로 인코딩
                        buffered = BytesIO()
                        img_pil.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()

                        # 각 이미지 아이템을 별도의 문자열로 생성
                        item_html = (
                            '<div style="text-align: center; flex-shrink: 0;">'
                            f'<img src="data:image/png;base64,{img_base64}" '
                            'style="width: 100px; height: auto; border: 1px solid #ddd; padding: 2px; display: block;">'
                            f'<p style="font-size: 11px; margin-top: 5px; word-wrap: break-word; max-width: 100px;">{cap}</p>'
                            '</div>'
                        )
                        html_parts.append(item_html)

                    html_parts.append('</div>')
                    final_html = ''.join(html_parts)
                    st.markdown(final_html, unsafe_allow_html=True)

                    # OCR 결과 표시
                    if detection.get('ocr_text'):
                        st.info(f"🔍 **OCR 결과**: '{detection['ocr_text']}'")
                        if detection.get('matched_truth'):
                            st.caption(f"GT: {detection['matched_truth']}")
                    elif detection.get('detection_type') == 'ocr_verified':
                        st.info("✅ OCR 검증됨")
                    elif st.session_state.get('use_enhanced_ocr', False):
                        st.caption("OCR 추출 실패")
                    else:
                        st.caption("OCR 미적용")

                with col2:
                    # 현재 클래스 이름 (수정된 것이 있으면 그것을 사용)
                    current_class_name = st.session_state.modified_classes.get(
                        status_key, detection['class_name']
                    )

                    # 항상 클래스 이름 표시
                    st.markdown(f"### {current_class_name}")
                    if current_class_name != detection['class_name']:
                        st.caption(f"(원래: {detection['class_name']})")

                    # 편집 모드인지 확인
                    is_editing = st.session_state.edit_mode.get(status_key, False)

                    # 편집 모드일 때 드롭다운 표시 (토글 형태)
                    if is_editing:
                        # 사용 가능한 클래스 목록 (class_examples 디렉토리 기반)
                        available_classes = load_class_names_from_examples_cached()
                        if current_class_name not in available_classes:
                            available_classes.append(current_class_name)

                        # 이미 load_class_names_from_examples()에서 정렬됨

                        # 드롭다운을 바로 표시 (on_change 없이)
                        new_class_name = st.selectbox(
                            "🔄 새 클래스 선택:",
                            available_classes,
                            index=available_classes.index(current_class_name) if current_class_name in available_classes else 0,
                            key=f"select_new_{prefix}_{i}",
                            help="클래스를 선택한 후 '💾 수정 완료' 버튼을 눌러주세요"
                        )

                        # 선택된 값을 임시로 저장
                        st.session_state[f"temp_class_{status_key}"] = new_class_name

                    # 정보를 세로로 나열
                    st.write(f"📊 **신뢰도**: {detection['confidence']:.1%}")
                    model_name = detection.get('model', detection.get('model_id', 'unknown'))
                    st.write(f"🤖 **모델**: {model_name}")
                    st.write(f"📍 **위치**: ({x1}, {y1})")
                    st.write(f"📏 **크기**: {x2-x1}×{y2-y1}px")


                with col3:
                    # 현재 상태 표시
                    if current_status == "approved":
                        st.success("✅ 승인됨")
                    elif current_status == "rejected":
                        st.error("❌ 거부됨")
                    else:
                        st.info("⏳ 대기중")

                with col4:
                    # 액션 버튼
                    is_editing = st.session_state.edit_mode.get(status_key, False)

                    # 모든 버튼을 세로로 배치
                    if st.button("✅ 승인", key=f"approve_{prefix}_{i}",
                                disabled=(current_status=="approved" or is_editing),
                                use_container_width=True):
                        st.session_state.verification_status[status_key] = "approved"
                        st.rerun()

                    if st.button("❌ 거부", key=f"reject_{prefix}_{i}",
                                disabled=(current_status=="rejected" or is_editing),
                                use_container_width=True):
                        st.session_state.verification_status[status_key] = "rejected"
                        st.rerun()

                    # 토글 방식으로 수정 버튼 동작
                    edit_button_label = "💾 수정 완료" if is_editing else "✏️ 수정"
                    edit_button_type = "primary" if is_editing else "secondary"
                    if st.button(edit_button_label, key=f"edit_{prefix}_{i}",
                                use_container_width=True,
                                type=edit_button_type):
                        if is_editing:
                            # 수정 완료 - 선택된 클래스 저장
                            temp_class = st.session_state.get(f"temp_class_{status_key}")
                            if temp_class:
                                st.session_state.modified_classes[status_key] = temp_class
                            st.session_state.edit_mode[status_key] = False
                        else:
                            # 수정 시작
                            st.session_state.edit_mode[status_key] = True
                        st.rerun()

                    if st.button("↩️ 초기화", key=f"reset_{prefix}_{i}",
                                use_container_width=True):
                        if status_key in st.session_state.verification_status:
                            del st.session_state.verification_status[status_key]
                        if status_key in st.session_state.modified_classes:
                            del st.session_state.modified_classes[status_key]
                        if status_key in st.session_state.edit_mode:
                            del st.session_state.edit_mode[status_key]
                        st.rerun()
        
        # 수작업 라벨링 섹션
        st.subheader("🎨 수작업 라벨링")
        st.write("모델이 놓친 부품이 있다면 도면 이미지 위에 직접 바운딩 박스를 그려서 추가하세요:")

        # 수작업 라벨링 활성화 옵션 - prefix를 사용하여 고유한 key 생성
        enable_manual = st.checkbox("수작업 라벨링 활성화", value=False, key=f"enable_manual_labeling_{prefix}")

        if enable_manual:
            if not CANVAS_AVAILABLE:
                st.error("❌ streamlit-drawable-canvas가 설치되지 않았습니다.")
                st.code("pip install streamlit-drawable-canvas")
                return

            try:
                # 이미지가 있는지 확인
                if not (st.session_state.current_image and 'image' in st.session_state.current_image):
                    st.info("이미지를 먼저 로드해주세요.")
                    return

                img_array = st.session_state.current_image['image']
                # BGR to RGB 변환 (OpenCV 이미지인 경우)
                if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)

                # 승인된 검출 결과를 먼저 이미지에 그림
                approved_detections = []
                for i, detection in enumerate(detections):
                    status_key = f"{prefix}_{i}"
                    if st.session_state.verification_status.get(status_key) == "approved":
                        approved_detections.append(detection)

                # 승인된 박스들을 배경 이미지에 그림
                background_img = img_array.copy()
                for det in approved_detections:
                    x1, y1, x2, y2 = det['bbox']
                    # 승인된 박스는 초록색으로 표시
                    cv2.rectangle(background_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    # 클래스 이름 표시
                    label = det['class_name']
                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(background_img, (x1, y1-20), (x1+label_size[0], y1), (0, 255, 0), -1)
                    cv2.putText(background_img, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                # 그리기 도구 설정 (네모 박스만 사용)
                drawing_mode = "rect"  # 고정
                stroke_width = 3  # 더 두꺼운 선
                stroke_color = "#FF0000"  # 빨간색 고정

                # 수작업 검출 시 사용할 클래스 선택
                available_classes = load_class_names_from_examples_cached()
                selected_class = st.selectbox(
                    "추가할 부품 종류:",
                    available_classes,
                    key=f"manual_class_{prefix}"
                )

                # 이미지 크기 조정 (캔버스용)
                canvas_height = 700
                img_height, img_width = background_img.shape[:2]
                aspect_ratio = img_width / img_height
                canvas_width = int(canvas_height * aspect_ratio)

                # 이미지를 캔버스 크기에 맞게 리사이즈
                img_resized = cv2.resize(background_img, (canvas_width, canvas_height))

                # PIL 이미지로 변환
                pil_img = Image.fromarray(img_resized.astype('uint8'))

                st.write("✏️ 수작업 라벨링:")
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.info("🎯 도면 이미지 위에 직접 바운딩 박스를 그려주세요:")
                    st.caption("• 🟢 초록색 박스: 이미 승인된 부품")
                    st.caption("• 🔴 빨간색 박스: 새로 추가할 부품")

                with col2:
                    if st.button("🗑️ 모든 박스 지우기", key=f"clear_canvas_{prefix}"):
                        st.session_state[f"manual_labeling_canvas_{prefix}"] = None
                        st.rerun()

                # 캔버스 생성 - 도면 이미지를 배경으로 직접 사용
                canvas_result = st_canvas(
                    fill_color="rgba(255, 0, 0, 0.3)",  # 반투명 빨간색 채우기
                    stroke_width=3,
                    stroke_color="#FF0000",  # 빨간색 테두리
                    background_image=pil_img,  # 도면 이미지(승인된 박스 포함)를 배경으로 설정
                    update_streamlit=True,
                    height=canvas_height,
                    width=canvas_width,
                    drawing_mode="rect",
                    key=f"manual_labeling_canvas_{prefix}",
                    display_toolbar=True,
                )

                # 수작업으로 그린 박스들 처리 (새로 추가된 것만)
                if canvas_result and canvas_result.json_data is not None:
                    all_objects = canvas_result.json_data.get("objects", [])
                    if len(all_objects) > 0:
                        # 모든 객체를 DataFrame으로 변환
                        objects_df = pd.json_normalize(all_objects)
                        st.write(f"📦 그려진 박스: {len(objects_df)}개")

                        # 각 박스에 대해 부품 종류 선택
                        st.write("🎯 각 박스에 대해 부품 종류를 선택하세요:")

                        # 사용 가능한 클래스 목록
                        available_classes = load_class_names_from_examples_cached()

                        box_classes = {}
                        for idx in range(len(objects_df)):
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                st.write(f"박스 {idx+1}:")
                            with col2:
                                selected_class = st.selectbox(
                                    f"부품 선택",
                                    available_classes,
                                    key=f"box_class_{prefix}_{idx}",
                                    label_visibility="collapsed"
                                )
                                box_classes[idx] = selected_class

                        # 수작업 검출을 세션 상태에 추가
                        if st.button("➕ 선택된 부품들 추가", key=f"add_manual_detections_{prefix}", type="primary"):
                            manual_detections = []

                            # 원본 이미지 크기 가져오기
                            original_img = st.session_state.current_image['image']
                            orig_height, orig_width = original_img.shape[:2]

                            # 스케일링 팩터 계산 (캔버스 → 원본 이미지)
                            scale_x = orig_width / canvas_width
                            scale_y = orig_height / canvas_height

                            for index, row in objects_df.iterrows():
                                # 캔버스 좌표를 원본 이미지 좌표로 변환
                                left = int(row['left'] * scale_x)
                                top = int(row['top'] * scale_y)
                                right = int((row['left'] + row['width']) * scale_x)
                                bottom = int((row['top'] + row['height']) * scale_y)

                                # 이 박스에 대해 선택된 클래스 가져오기
                                selected_class = box_classes.get(index, available_classes[0])

                                # 클래스 ID 추출 (클래스명의 첫 번째 숫자 부분)
                                class_id = 0  # 기본값
                                try:
                                    # 클래스명에서 첫 번째 숫자 추출
                                    # 예: "10_BUZZER..." -> 10
                                    parts = selected_class.split('_')
                                    if parts and parts[0].replace(',', '').isdigit():
                                        class_id = int(parts[0].split(',')[0])  # 쉼표가 있는 경우 첫 번째 숫자
                                except:
                                    class_id = available_classes.index(selected_class) if selected_class in available_classes else 0

                                # YOLO 형식으로 변환
                                manual_det = {
                                    'class_name': selected_class,
                                    'class_id': class_id,
                                    'confidence': 1.0,  # 수작업은 100% 신뢰도
                                    'bbox': [left, top, right, bottom],
                                    'model_id': 'manual',
                                    'model': 'manual'  # render_detection_list에서 사용하는 필드
                                }
                                manual_detections.append(manual_det)

                            # 세션 상태에 추가
                            if 'manual' not in st.session_state.detection_results:
                                st.session_state.detection_results['manual'] = []
                            st.session_state.detection_results['manual'].extend(manual_detections)

                            st.success(f"✅ {len(manual_detections)}개의 수작업 검출이 추가되었습니다.")
                            st.rerun()

            except Exception as e:
                st.error(f"수작업 라벨링 오류: {str(e)}")
                st.info("streamlit-drawable-canvas 패키지 설치를 확인해주세요: pip install streamlit-drawable-canvas")
                import traceback
                with st.expander("상세 오류 정보"):
                    st.code(traceback.format_exc())
        else:
            st.info("🖌️ 수작업 라벨링을 사용하려면 위의 체크박스를 선택하세요. 도면 이미지 위에 직접 바운딩 박스를 그릴 수 있습니다.")

    def render_detection_list_with_voting(self, detections, prefix):
        """검출 결과를 리스트 형태로 표시 (Voting 정보 포함)"""
        # 검출 결과를 리스트 형태로 표시
        st.subheader("🔍 검출 결과 (Voting 정보 포함)")
        for i, detection in enumerate(detections):
            status_key = f"{prefix}_{i}"
            current_status = st.session_state.verification_status.get(status_key, "pending")

            # 상태에 따른 컨테이너 스타일
            if current_status == "approved":
                container_style = "background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; margin-bottom: 10px;"
            elif current_status == "rejected":
                container_style = "background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; margin-bottom: 10px;"
            else:
                container_style = "background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; border-radius: 5px; margin-bottom: 10px;"

            with st.container():
                col1, col2, col3, col4 = st.columns([2, 4, 2, 2])

                with col1:
                    # 검출된 이미지와 정답 이미지를 나란히 표시
                    x1, y1, x2, y2 = detection['bbox']
                    image = st.session_state.current_image['image']
                    h, w = image.shape[:2]
                    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
                    cropped = image[y1:y2, x1:x2]

                    # 이미지를 가로로 표시하기 위한 HTML 생성
                    st.subheader("🖼️ 이미지 비교")
                    ground_truth = self.load_ground_truth_for_current_image()
                    if ground_truth:
                        # 현재 검출 위치와 가장 가까운 Ground Truth 찾기
                        best_gt = None
                        best_iou = 0
                        # 검출 bbox를 정수로 변환
                        det_bbox = [int(x) for x in detection['bbox']]

                        for gt in ground_truth:
                            gt_bbox = self.yolo_to_xyxy(
                                gt['x_center'], gt['y_center'],
                                gt['width'], gt['height'],
                                w, h
                            )
                            iou = self.calculate_iou(det_bbox, gt_bbox)
                            if iou > best_iou:
                                best_iou = iou
                                best_gt = gt

                        if best_gt and best_iou > 0.1:  # IoU 임계값을 0.1로 낮춤
                            # Ground Truth 박스 영역 crop
                            gt_x1, gt_y1, gt_x2, gt_y2 = self.yolo_to_xyxy(
                                best_gt['x_center'], best_gt['y_center'],
                                best_gt['width'], best_gt['height'],
                                w, h
                            )
                            gt_x1, gt_y1, gt_x2, gt_y2 = max(0, gt_x1), max(0, gt_y1), min(w, gt_x2), min(h, gt_y2)
                            gt_cropped = image[gt_y1:gt_y2, gt_x1:gt_x2]
                            if gt_cropped.size > 0:
                                # Ground Truth에 이미 class_name이 있음 (load 시 추가함)
                                gt_class_name = best_gt.get('class_name', f"Class {best_gt['class_id']}")
                                st.image(gt_cropped, caption=f"GT: {gt_class_name} (IoU:{best_iou:.2f})")
                            else:
                                st.info("GT 영역 오류")
                        elif best_gt:
                            # IoU가 낮더라도 가장 가까운 GT 표시
                            st.info(f"낮은 IoU: {best_iou:.2f}")
                        else:
                            st.info("GT 없음")
                    else:
                        st.info("라벨 없음")

                    # 모델 검출 결과
                    # 모델이 검출한 이미지 표시
                    st.caption("🔍 모델 검출", help="AI 모델(YOLOv8)이 현재 검출한 영역입니다. 바운딩 박스 좌표와 신뢰도를 기반으로 추출된 이미지를 보여줍니다.")
                    if cropped.size > 0:
                        st.image(cropped, caption=f"검출: {detection['class_name']}")
                    else:
                        st.warning("검출 영역 오류")

                    # OCR 결과
                    # OCR 결과 컬럼 추가
                    st.caption("🔍 OCR 결과", help="Enhanced OCR로 추출된 텍스트 결과입니다.")
                    if detection.get('ocr_text'):
                        st.success(f"✅ '{detection['ocr_text']}'")
                        if detection.get('matched_truth'):
                            st.info(f"GT: {detection['matched_truth']}")
                    elif detection.get('detection_type') == 'ocr_verified':
                        st.success("✅ OCR 검증됨")
                    elif st.session_state.get('use_enhanced_ocr', False):
                        # Enhanced OCR가 활성화되었지만 이 검출에서는 OCR 텍스트가 추출되지 않음
                        st.warning("OCR 추출 실패")
                    else:
                        st.info("OCR 미적용")

                    # 실제 심볼 이미지
                    # 검출된 클래스의 실제 심볼 이미지 표시
                    st.caption("📚 실제 심볼", help="해당 클래스의 표준 심볼 이미지입니다. class_examples 폴더의 참조 이미지로 올바른 심볼인지 시각적으로 비교할 수 있습니다.")
                    example_path = self.get_class_example_image(detection['class_name'])
                    if example_path and os.path.exists(example_path):
                        st.image(example_path, caption=detection['class_name'])
                    else:
                        st.info("심볼 이미지 없음")

                with col2:
                    st.write(f"**{detection['class_name']}**")
                    st.write(f"🎯 신뢰도: {detection['confidence']:.3f}")
                    st.write(f"📦 위치: ({x1}, {y1}) - ({x2}, {y2})")

                    # Voting 정보 표시
                    if 'voting_info' in detection:
                        voting_info = detection['voting_info']
                        st.write(f"🗳️ **Voting 정보:**")
                        st.write(f"  - 투표 수: {voting_info['total_votes']}개 모델")
                        st.write(f"  - 클래스별 투표: {voting_info['class_votes']}")
                        st.write(f"  - 가중 점수: {max(voting_info['weighted_scores'].values()):.3f}")
                        st.write(f"  - 참여 모델: {', '.join(voting_info['models_agreed'])}")

                    # 클래스명 표시
                    st.write(f"**클래스**: {detection['class_name']}")

                with col3:
                    # 현재 상태 표시
                    if current_status == "approved":
                        st.success("✅ 승인됨")
                    elif current_status == "rejected":
                        st.error("❌ 거부됨")
                    else:
                        st.info("🕰️ 대기 중")

                with col4:
                    # 개별 상태 변경 버튼
                    if current_status != "approved":
                        if st.button("✅ 승인", key=f"approve_{prefix}_{i}"):
                            st.session_state.verification_status[status_key] = "approved"
                            st.rerun()
                    if current_status != "rejected":
                        if st.button("❌ 거부", key=f"reject_{prefix}_{i}"):
                            st.session_state.verification_status[status_key] = "rejected"
                            st.rerun()
                    if current_status != "pending":
                        if st.button("🔄 초기화", key=f"reset_{prefix}_{i}"):
                            del st.session_state.verification_status[status_key]
                            st.rerun()

    def render_bom_generation(self):
        """BOM 생성 및 내보내기"""
        st.header("📊 BOM 생성 및 내보내기")

        # 승인된 검출 결과만 필터링
        approved_detections = []

        # 검증 상태 확인하여 승인된 검출만 수집
        if 'verification_status' in st.session_state:
            # 통합 결과에서 승인된 것들
            for key, status in st.session_state.verification_status.items():
                if status == "approved":
                    # key 형식: "unified_0", "voting_1", "model_id_2" 등
                    parts = key.split('_')
                    if len(parts) >= 2:
                        prefix = parts[0]
                        index = int(parts[-1])

                        # 해당하는 검출 찾기
                        if prefix == "unified":
                            # 통합 결과에서 찾기
                            all_dets = []
                            for model_id, dets in st.session_state.detection_results.items():
                                for det in dets:
                                    det_copy = det.copy()
                                    det_copy['model_id'] = model_id
                                    all_dets.append(det_copy)
                            unique_dets = self.remove_duplicate_detections(all_dets)
                            if index < len(unique_dets):
                                detection = unique_dets[index].copy()
                                # 수정된 클래스 이름이 있으면 적용
                                if key in st.session_state.modified_classes:
                                    detection['class_name'] = st.session_state.modified_classes[key]
                                approved_detections.append(detection)
                        elif prefix == "voting":
                            # Voting 결과에서 찾기
                            all_dets = []
                            for model_id, dets in st.session_state.detection_results.items():
                                for det in dets:
                                    det_copy = det.copy()
                                    det_copy['model_id'] = model_id
                                    all_dets.append(det_copy)
                            voting_dets, _ = self.remove_duplicate_detections_with_voting(all_dets)
                            if index < len(voting_dets):
                                detection = voting_dets[index].copy()
                                # 수정된 클래스 이름이 있으면 적용
                                if key in st.session_state.modified_classes:
                                    detection['class_name'] = st.session_state.modified_classes[key]
                                approved_detections.append(detection)
                        elif prefix in st.session_state.detection_results:
                            # 개별 모델 결과에서 찾기
                            model_dets = st.session_state.detection_results[prefix]
                            if index < len(model_dets):
                                detection = model_dets[index].copy()
                                # 수정된 클래스 이름이 있으면 적용
                                if key in st.session_state.modified_classes:
                                    detection['class_name'] = st.session_state.modified_classes[key]
                                approved_detections.append(detection)

        # 승인된 검출이 없으면 전체 검출 사용 (기본값)
        if not approved_detections:
            st.info("승인된 검출이 없습니다. 전체 검출 결과를 사용합니다.")
            all_detections = []
            for model_id, detections in st.session_state.detection_results.items():
                all_detections.extend(detections)
            approved_detections = all_detections

        if not approved_detections:
            st.info("BOM 생성을 위한 검출 결과가 없습니다.")
            return

        # BOM 테이블 생성
        bom_data = self.create_bom_table(approved_detections)

        st.subheader("📋 생성된 BOM")

        # 승인된 검출 수 표시
        st.success(f"✅ 승인된 검출 {len(approved_detections)}개로 BOM 생성")

        st.dataframe(bom_data)

        # 통계 정보
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 부품 수", len(bom_data))
        with col2:
            total_cost = bom_data['총 가격'].sum()
            st.metric("총 예상 비용", f"{total_cost:,}원")
        with col3:
            unique_types = len(bom_data['부품명'].unique())
            st.metric("부품 종류", unique_types)
        with col4:
            avg_confidence = safe_mean([d['confidence'] for d in approved_detections])
            st.metric("평균 신뢰도", f"{avg_confidence:.3f}")
        
        # 내보내기 옵션
        st.subheader("📤 내보내기")
        
        col1, col2 = st.columns(2)
        with col1:
            # Excel 내보내기
            excel_data = self.create_excel_export(bom_data)
            st.download_button(
                label="📊 Excel로 내보내기",
                data=excel_data,
                file_name=f"BOM_{st.session_state.current_image['filename'].split('.')[0]}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            # PDF 내보내기
            if st.button("📄 PDF 보고서 생성"):
                pdf_data = self.create_pdf_report(bom_data, all_detections)
                st.download_button(
                    label="📄 PDF 다운로드",
                    data=pdf_data,
                    file_name=f"BOM_Report_{st.session_state.current_image['filename'].split('.')[0]}.pdf",
                    mime="application/pdf"
                )

    def create_bom_table(self, detections):
        """검출 결과로부터 BOM 테이블 생성"""
        # 동일 부품별로 집계
        component_counts = {}
        for detection in detections:
            class_name = detection['class_name']
            if class_name in component_counts:
                component_counts[class_name]['수량'] += 1
                component_counts[class_name]['신뢰도들'].append(detection['confidence'])
            else:
                component_counts[class_name] = {
                    '수량': 1,
                    '신뢰도들': [detection['confidence']],
                    '모델': detection['model']
                }
        
        # BOM 테이블 생성
        bom_rows = []
        for i, (class_name, info) in enumerate(component_counts.items(), 1):
            # 가격 정보 조회
            price_info = self.pricing_data.get(class_name, {})
            unit_price = price_info.get('unit_price', 10000)  # 기본값
            
            avg_confidence = safe_mean(info['신뢰도들'])
            total_price = unit_price * info['수량']
            
            bom_rows.append({
                '번호': i,
                '부품명': class_name,
                '수량': info['수량'],
                '단가': unit_price,
                '총 가격': total_price,
                '평균 신뢰도': round(avg_confidence, 3),
                '검출 모델': info['모델'],
                '비고': price_info.get('description', '')
            })
        
        return pd.DataFrame(bom_rows)

    def create_excel_export(self, bom_data):
        """Excel 파일 생성"""
        import io
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            bom_data.to_excel(writer, sheet_name='BOM', index=False)
            
            # 추가 정보 시트
            info_data = pd.DataFrame([
                ['도면 파일', st.session_state.current_image['filename']],
                ['생성 일시', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['사용 모델', ', '.join(st.session_state.selected_models)],
                ['총 부품 수', len(bom_data)],
                ['총 예상 비용', f"{bom_data['총 가격'].sum():,}원"]
            ], columns=['항목', '값'])
            
            info_data.to_excel(writer, sheet_name='정보', index=False)
        
        return output.getvalue()

    def create_pdf_report(self, bom_data, detections):
        """PDF 보고서 생성"""
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # 제목
        title = Paragraph("AI 기반 BOM 분석 보고서", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # 기본 정보
        info_data = [
            ['도면 파일', st.session_state.current_image['filename']],
            ['분석 일시', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['사용 모델', ', '.join(st.session_state.selected_models)],
            ['총 검출 수', str(len(detections))],
            ['부품 종류', str(len(bom_data))],
            ['총 예상 비용', f"{bom_data['총 가격'].sum():,}원"]
        ]
        
        info_table = Table(info_data)
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 12))
        
        # BOM 테이블
        bom_title = Paragraph("부품 목록 (BOM)", styles['Heading2'])
        story.append(bom_title)
        story.append(Spacer(1, 12))
        
        # BOM 데이터를 테이블로 변환
        bom_table_data = [bom_data.columns.tolist()]
        for _, row in bom_data.iterrows():
            bom_table_data.append(row.tolist())
        
        bom_table = Table(bom_table_data)
        bom_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(bom_table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def draw_ground_truth_only(self, image, ground_truth):
        """Ground Truth만 표시 (초록색, 두꺼운 선)"""
        h, w = image.shape[:2]

        for gt in ground_truth:
            # YOLO 정규화 좌표를 픽셀 좌표로 변환
            x_center = gt['x_center'] * w
            y_center = gt['y_center'] * h
            width = gt['width'] * w
            height = gt['height'] * h

            x1 = int(x_center - width/2)
            y1 = int(y_center - height/2)
            x2 = int(x_center + width/2)
            y2 = int(y_center + height/2)

            # 초록색 두꺼운 바운딩 박스
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 4)  # 두께 4

            # 클래스 ID 표시
            label = f"GT_{gt['class_id']}"
            cv2.putText(image, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return image

    def draw_detections_only(self, image, detections):
        """검출 결과만 표시 (빨간색, 두꺼운 선)"""
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']

            # 빨간색 두꺼운 바운딩 박스
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 4)  # 두께 4

            # 클래스 이름과 신뢰도 표시
            label = f"{detection['class_name']}: {detection['confidence']:.2f}"
            cv2.putText(image, label, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        return image

    def enhance_detection_with_ocr(self, image, detection):
        """OCR을 활용한 검출 결과 향상 (PaddleOCR 사용)"""
        if not OCR_AVAILABLE:
            return detection

        try:
            # OCR 초기화 (캐시된 reader 사용)
            if not hasattr(self, 'ocr_reader'):
                if OCR_TYPE == "PaddleOCR":
                    # GPU 사용 가능 여부 확인
                    import torch
                    use_gpu = torch.cuda.is_available()
                    self.ocr_reader = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, use_gpu=use_gpu)
                    if use_gpu:
                        print(f"✅ PaddleOCR GPU 모드 활성화")
                    else:
                        print(f"⚠️ PaddleOCR CPU 모드 사용 (GPU 불가)")
                else:  # EasyOCR 백업
                    import easyocr
                    import torch
                    use_gpu = torch.cuda.is_available()
                    self.ocr_reader = easyocr.Reader(['en'], gpu=use_gpu)

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

            # OCR 수행 (PaddleOCR vs EasyOCR)
            if OCR_TYPE == "PaddleOCR":
                results = self.ocr_reader.ocr(cropped, cls=True)
                # PaddleOCR 결과 형식 변환
                ocr_results = []
                if results and results[0]:
                    for line in results[0]:
                        bbox_coords, (text, confidence) = line
                        ocr_results.append((bbox_coords, text, confidence))
                results = ocr_results
            else:  # EasyOCR
                results = self.ocr_reader.readtext(cropped)

            # 키워드 매핑
            class_keywords = {
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

            # OCR 결과를 세션 상태에 저장
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

            if boost_applied and 'ocr_boost' in enhanced_detection:
                # UI에 OCR 정보 표시
                st.success(f"🔍 OCR 향상: {detection['class_name']} "
                          f"{detection['confidence']:.3f} → {enhanced_detection['confidence']:.3f} "
                          f"(키워드: {enhanced_detection['matched_keyword']})")

            return enhanced_detection

        except Exception as e:
            # OCR 오류 시 원본 반환
            return detection

    def apply_enhanced_ocr(self, detections):
        """Enhanced OCR v4.0 Rotation 적용 (진행률 표시 포함)"""
        # 캐시된 Enhanced OCR Detector 사용
        enhanced_ocr_detector = get_enhanced_ocr_detector()
        if not enhanced_ocr_detector or not st.session_state.current_image:
            return detections

        try:
            # 현재 이미지 가져오기
            if isinstance(st.session_state.current_image, dict):
                image = st.session_state.current_image.get('image')
            else:
                image = st.session_state.current_image

            if image is None:
                st.warning(f"⚠️ Enhanced OCR {OCR_VERSION}: 이미지를 찾을 수 없습니다.")
                return detections

            # 원본 이미지 가져오기 (있는 경우)
            original_image = None
            if hasattr(st.session_state, 'original_image'):
                original_image = st.session_state.original_image
            elif hasattr(st.session_state, 'uploaded_image'):
                original_image = st.session_state.uploaded_image

            # 진행률 표시 UI 구성
            total_objects = len(detections)
            st.info(f"🔄 Enhanced OCR {OCR_VERSION} (PaddleOCR API) 처리 중... (총 {total_objects}개 객체)")

            # 진행률 바와 상태 텍스트 컨테이너
            progress_bar = st.progress(0)
            status_container = st.empty()

            # 진행률 콜백 함수 정의
            def progress_callback(current, total, current_obj_name=""):
                progress = current / total if total > 0 else 0
                progress_bar.progress(progress)
                status_container.text(f"진행: {current}/{total} ({progress*100:.1f}%) - {current_obj_name}")

            # Enhanced OCR 적용 (v4.0 Rotation 우선, 폴백 지원)
            if OCR_VERSION == "v4.0 Rotation" and hasattr(enhanced_ocr_detector, 'apply_enhanced_ocr_v4'):
                enhanced_detections = enhanced_ocr_detector.apply_enhanced_ocr_v4(
                    detections, image, original_image, progress_callback=progress_callback
                )
            elif OCR_VERSION == "v3.0 Ultimate" and hasattr(enhanced_ocr_detector, 'apply_enhanced_ocr_v3'):
                enhanced_detections = enhanced_ocr_detector.apply_enhanced_ocr_v3(
                    detections, image, original_image, progress_callback=progress_callback
                )
            else:
                # v2.0 fallback
                enhanced_detections = enhanced_ocr_detector.apply_enhanced_ocr_v2(detections, image)

            # 완료 상태 표시
            progress_bar.progress(1.0)
            status_container.success(f"✅ Enhanced OCR 처리 완료! ({total_objects}개 객체)")

            # 통계 정보 저장 (기존 세션 상태와 호환)
            ocr_extracted_count = len([d for d in enhanced_detections if d.get('ocr_text')])
            ocr_verified_count = len([d for d in enhanced_detections if d.get('matched_truth')])

            st.session_state.enhanced_ocr_results = {
                'total_detections': len(enhanced_detections),
                'ocr_extracted': ocr_extracted_count,
                'ocr_verified': ocr_verified_count,
                'success_rate': (ocr_verified_count / len(enhanced_detections) * 100) if enhanced_detections else 0
            }

            return enhanced_detections

        except Exception as e:
            st.error(f"❌ Enhanced OCR {OCR_VERSION} 처리 오류: {e}")
            import traceback
            traceback.print_exc()
            return detections

    def _calculate_iou_enhanced(self, box1, box2):
        """Enhanced OCR용 IoU 계산"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2

        # 교집합 영역
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)

        if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
            return 0.0

        inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)

        # 합집합 영역
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

def main():
    """메인 애플리케이션"""
    system = SmartBOMSystemV2()
    
    # 사이드바 렌더링
    system.render_sidebar()
    
    # 메인 워크플로우 렌더링
    system.render_main_workflow()
    
    # 푸터
    st.markdown("---")
    st.markdown("**AI 심볼 인식 기반 스마트 BOM 분석 및 견적 자동화 솔루션 v2.0** | Powered by YOLOv11 & Detectron2")

if __name__ == "__main__":
    main()