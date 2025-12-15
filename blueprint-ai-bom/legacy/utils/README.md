# Utils Module Structure

## 모듈 구조 및 역할

### 📁 data_loader.py
- `load_pricing_data_cached()` - 가격 데이터 로드
- `load_ground_truth_cached()` - Ground Truth 데이터 로드
- `load_class_names_from_examples_cached()` - 클래스명 추출

### 📁 model_loader.py
- `load_yolo_model_cached()` - YOLO 모델 로드
- `get_enhanced_ocr_detector()` - Enhanced OCR 로드
- `get_paddleocr_cached()` - PaddleOCR 로드

### 📁 model_registry.py
- `ModelRegistry` 클래스 - 모델 레지스트리 관리

### 📁 helpers.py
- `safe_mean()` - 안전한 평균 계산
- 기타 유틸리티 함수들

### 📁 detection_utils.py (새로 추가)
- Detection 관련 메서드들
- `detect_with_model()`
- `_detect_with_yolo()`
- `_detect_with_detectron2()`
- `remove_duplicate_detections()`
- `calculate_detection_metrics()`
- `calculate_iou()`

### 📁 visualization_utils.py (새로 추가)
- 시각화 관련 메서드들
- `draw_detection_results()`
- `create_final_verified_image()`
- `draw_detection_with_ground_truth()`
- `draw_ground_truth_only()`
- `draw_detections_only()`

### 📁 file_handler.py (새로 추가)
- 파일 처리 관련 메서드들
- `process_uploaded_file()`
- `load_test_image()`
- `get_test_files()`
- `load_ground_truth_labels()`

### 📁 bom_generator.py (새로 추가)
- BOM 생성 관련 메서드들
- `create_bom_table()`
- `create_excel_export()`
- `create_pdf_report()`

### 📁 ocr_utils.py (새로 추가)
- OCR 관련 메서드들
- `enhance_detection_with_ocr()`
- `apply_enhanced_ocr()`
- `render_enhanced_ocr_analysis()`

### 📁 ui_components.py (새로 추가)
- UI 렌더링 메서드들
- `render_sidebar()`
- `render_main_workflow()`
- `render_drawing_display()`
- `render_model_selection()`
- `render_detection_results()`
- `render_symbol_verification()`
- `render_bom_generation()`
- `render_detection_list()`

## 사용 방법

```python
from utils import (
    # 기본 함수들
    load_pricing_data_cached,
    ModelRegistry,
    safe_mean,

    # Detection 관련
    detect_with_model,
    remove_duplicate_detections,

    # Visualization 관련
    draw_detection_results,

    # File handling
    process_uploaded_file,

    # BOM 생성
    create_bom_table,
    create_excel_export,

    # UI Components
    render_sidebar,
    render_main_workflow
)
```