"""
File Handler Utilities
파일 처리 관련 유틸리티 함수들
"""
import os
import io
import numpy as np
import streamlit as st
from PIL import Image
from typing import List, Dict, Any, Optional

# PDF 처리 라이브러리 (옵션)
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

def get_test_files(system) -> List[str]:
    """테스트 파일 목록 가져오기"""
    test_drawings_path = "test_drawings"
    if os.path.exists(test_drawings_path):
        files = []
        for file in os.listdir(test_drawings_path):
            if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                files.append(file)
        return sorted(files)
    return []

def process_uploaded_file(uploaded_file, system) -> Optional[Dict[str, Any]]:
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

def load_test_image(filename: str, system) -> Optional[Dict[str, Any]]:
    """테스트 이미지 로드"""
    test_drawings_path = "test_drawings"
    filepath = os.path.join(test_drawings_path, filename)
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

def load_ground_truth_for_current_image(test_drawings_path: str, data_yaml: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """현재 이미지에 대한 Ground Truth 라벨 로드"""
    if not st.session_state.current_image:
        return None

    # 이미지 파일명에서 라벨 파일명 추출
    image_filename = st.session_state.current_image.get('filename', '')
    if not image_filename:
        return None

    # 라벨 파일 경로 구성
    label_filename = os.path.splitext(image_filename)[0] + '.txt'
    label_path = os.path.join(test_drawings_path, 'labels', label_filename)

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
                        if data_yaml and 'names' in data_yaml:
                            class_names = data_yaml['names']
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

def load_ground_truth_labels(image_filename: str, test_drawings_path: str, data_yaml: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """정답 라벨 로드 및 파싱"""
    # 이미지 파일명에서 확장자 제거
    base_name = os.path.splitext(image_filename)[0]
    label_path = os.path.join(test_drawings_path, 'labels', f"{base_name}.txt")

    if not os.path.exists(label_path):
        return None

    labels = []
    try:
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

                        # 클래스 이름 가져오기
                        if data_yaml and 'names' in data_yaml:
                            class_names = data_yaml['names']
                            class_name = class_names[class_id] if class_id < len(class_names) else f"Unknown_{class_id}"
                        else:
                            class_name = f"Class_{class_id}"

                        labels.append({
                            'class_id': class_id,
                            'class_name': class_name,
                            'x_center': x_center,
                            'y_center': y_center,
                            'width': width,
                            'height': height
                        })
        return labels
    except Exception as e:
        st.error(f"라벨 파일 로드 중 오류 발생: {e}")
        return None