"""
Utils module for Drawing BOM Extractor
유틸리티 함수들을 모듈화하여 관리
"""

from .data_loader import (
    load_pricing_data_cached,
    load_ground_truth_cached,
    load_class_names_from_examples_cached
)

from .model_loader import (
    load_yolo_model_cached,
    get_enhanced_ocr_detector,
    get_paddleocr_cached
)

from .model_registry import ModelRegistry

from .helpers import safe_mean

from .config import (
    setup_device,
    PATHS,
    MODEL_CONFIG,
    UI_CONFIG,
    COLORS
)

from .detection import (
    detect_with_model,
    calculate_iou,
    remove_duplicate_detections,
    calculate_detection_metrics
)

from .visualization import (
    draw_detection_results,
    create_final_verified_image,
    draw_detection_with_ground_truth,
    draw_ground_truth_only,
    draw_detections_only
)

from .bom_generator import (
    create_bom_table,
    create_excel_export,
    create_pdf_report
)

# 모듈화된 UI 컴포넌트들
from .ui_basic import render_sidebar, render_drawing_display, render_main_workflow
from .ui_model import render_model_selection
from .ui_detection import render_detection_results
from .ui_verification import render_symbol_verification, render_manual_labeling
from .ui_bom import render_bom_generation

from .file_handler import (
    get_test_files,
    process_uploaded_file,
    load_test_image,
    load_ground_truth_for_current_image,
    load_ground_truth_labels
)

from .ocr_utils import (
    enhance_detection_with_ocr,
    apply_enhanced_ocr,
    get_class_keywords
)

from .coordinate_utils import (
    yolo_to_xyxy,
    xyxy_to_yolo
)

from .system_utils import (
    get_gpu_status,
    clear_model_cache,
    clear_all_cache
)

__all__ = [
    # 데이터 로더
    'load_pricing_data_cached',
    'load_ground_truth_cached',
    'load_class_names_from_examples_cached',

    # 모델 로더
    'load_yolo_model_cached',
    'get_enhanced_ocr_detector',
    'get_paddleocr_cached',

    # 레지스트리
    'ModelRegistry',

    # 헬퍼
    'safe_mean',

    # 설정
    'setup_device',
    'PATHS',
    'MODEL_CONFIG',
    'UI_CONFIG',
    'COLORS',

    # Detection
    'detect_with_model',
    'calculate_iou',
    'remove_duplicate_detections',
    'calculate_detection_metrics',

    # Visualization
    'draw_detection_results',
    'create_final_verified_image',
    'draw_detection_with_ground_truth',
    'draw_ground_truth_only',
    'draw_detections_only',

    # BOM 생성
    'create_bom_table',
    'create_excel_export',
    'create_pdf_report',

    # UI 컴포넌트
    'render_sidebar',
    'render_main_workflow',
    'render_drawing_display',
    'render_model_selection',
    'render_detection_results',
    'render_symbol_verification',
    'render_manual_labeling',
    'render_bom_generation',

    # 파일 핸들러
    'get_test_files',
    'process_uploaded_file',
    'load_test_image',
    'load_ground_truth_for_current_image',
    'load_ground_truth_labels',

    # OCR
    'enhance_detection_with_ocr',
    'apply_enhanced_ocr',
    'get_class_keywords',

    # 좌표 변환
    'yolo_to_xyxy',
    'xyxy_to_yolo',

    # 시스템 유틸리티
    'get_gpu_status',
    'clear_model_cache',
    'clear_all_cache'
]