"""
Data Loader Utilities
데이터 로딩 관련 유틸리티 함수들
"""
import os
import json
import glob
import streamlit as st

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
            # "class_XX_" 형태에서 실제 클래스명 추출
            # 예: "class_05_17_POWER OUTLET(CONCENT)_(PO)_p01.jpg" -> "17_POWER OUTLET(CONCENT)_(PO)_p01"
            parts = filename[6:-4].split('_', 1)  # "class_" 제거하고 ".jpg" 제거 후 첫 번째 "_"에서 분할
            if len(parts) > 1:
                class_name = parts[1]  # 숫자 부분 제거한 실제 클래스명
                class_names.append(class_name)

    return sorted(class_names)