# 모델 설정 패턴 적용 계획

> Blueprint AI BOM의 MODEL_CONFIGS 패턴을 다른 서비스에 적용
> 모델별 기본 파라미터 중앙화

---

## 현재 패턴 (Blueprint AI BOM)

### detection_service.py

```python
MODEL_CONFIGS = {
    "bom_detector": {
        "name": "전력 설비 단선도 YOLOv11N",
        "confidence": 0.40,
        "iou": 0.50,
        "imgsz": 1024,
        "use_sahi": False,
    },
    "pid_symbol": {
        "name": "P&ID 심볼 (60종)",
        "confidence": 0.10,  # P&ID는 낮은 신뢰도 권장
        "iou": 0.45,
        "imgsz": 1024,
        "use_sahi": True,  # SAHI 자동 활성화
    },
    "pid_class_aware": {
        "name": "P&ID 분류 (32종)",
        "confidence": 0.10,
        "iou": 0.45,
        "imgsz": 1024,
        "use_sahi": True,
    },
    # ...
}
```

### 장점
- 모델별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 모델 추가 시 설정만 추가

---

## 적용 대상 서비스

### 1. YOLO API (우선순위: HIGH)
**현재 상태**: model_registry.yaml에 메타데이터만 존재
**개선안**: 런타임 기본값 설정 추가

```python
# models/yolo-api/config/model_defaults.py

MODEL_DEFAULTS = {
    "engineering": {
        "confidence": 0.50,
        "iou": 0.45,
        "imgsz": 640,
        "use_sahi": False,
        "augment": False,
    },
    "pid_symbol": {
        "confidence": 0.10,
        "iou": 0.45,
        "imgsz": 1024,
        "use_sahi": True,
        "slice_size": 640,
        "overlap": 0.2,
    },
    "pid_class_aware": {
        "confidence": 0.10,
        "iou": 0.45,
        "imgsz": 1024,
        "use_sahi": True,
    },
    "bom_detector": {
        "confidence": 0.40,
        "iou": 0.50,
        "imgsz": 1024,
        "use_sahi": False,
    },
}
```

**작업 항목**:
- [ ] model_defaults.py 생성
- [ ] detection_router.py에서 기본값 적용 로직 추가
- [ ] API 스펙 YAML에 기본값 반영

---

### 2. OCR APIs (우선순위: MEDIUM)
**현재 상태**: 각 OCR 서비스마다 하드코딩된 기본값
**개선안**: OCR 타입별 기본 설정

```python
# gateway-api/config/ocr_defaults.py

OCR_DEFAULTS = {
    "edocr2": {
        "language": "kor+eng",
        "dpi": 300,
        "enhance_contrast": True,
        "denoise": True,
    },
    "paddleocr": {
        "lang": "korean",
        "use_angle_cls": True,
        "det_db_thresh": 0.3,
    },
    "tesseract": {
        "lang": "kor+eng",
        "psm": 6,
        "oem": 3,
    },
    "trocr": {
        "model_size": "base",
        "task": "printed",
    },
}
```

**작업 항목**:
- [ ] ocr_defaults.py 생성
- [ ] ocr_service.py에서 기본값 적용
- [ ] 각 OCR API의 파라미터 정리

---

### 3. Line Detector (우선순위: MEDIUM)
**현재 상태**: method별 설정 분산
**개선안**: 검출 방식별 기본 설정

```python
LINE_DETECTOR_DEFAULTS = {
    "lsd": {
        "scale": 0.8,
        "sigma_scale": 0.6,
        "line_length_threshold": 30,
    },
    "hough": {
        "threshold": 100,
        "min_line_length": 50,
        "max_line_gap": 10,
    },
    "combined": {
        "lsd_weight": 0.6,
        "hough_weight": 0.4,
    },
}
```

---

### 4. Design Checker (우선순위: LOW)
**현재 상태**: 규칙별 severity 하드코딩
**개선안**: 프로필별 규칙 설정

```python
DESIGN_CHECKER_PROFILES = {
    "bwms": {
        "enabled_rules": ["R001", "R002", ...],
        "severity_overrides": {
            "R001": "error",
            "R005": "warning",
        },
    },
    "hvac": {...},
    "process": {...},
}
```

---

## 통합 설정 관리 패턴

### 위치: `gateway-api/config/`

```
gateway-api/config/
├── __init__.py
├── model_defaults.py     # YOLO 모델 기본값
├── ocr_defaults.py       # OCR 기본값
├── detector_defaults.py  # Line Detector 기본값
└── checker_profiles.py   # Design Checker 프로필
```

### 로딩 패턴

```python
# config/__init__.py

from pathlib import Path
import yaml

CONFIG_DIR = Path(__file__).parent

def load_yaml_config(filename: str) -> dict:
    """YAML 설정 파일 로드"""
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}

# 각 서비스에서 사용
MODEL_DEFAULTS = load_yaml_config("model_defaults.yaml")
OCR_DEFAULTS = load_yaml_config("ocr_defaults.yaml")
```

---

## nodeDefinitions.ts와 동기화

### 문제
- 백엔드 기본값과 프론트엔드 기본값 불일치 가능
- 수동 동기화 필요

### 해결책
API 스펙 YAML을 SSOT로 사용:

```yaml
# gateway-api/api_specs/yolo.yaml
blueprintflow:
  parameters:
    - name: confidence
      type: number
      default: 0.50              # 이 값이 SSOT
      model_defaults:            # 모델별 오버라이드
        pid_symbol: 0.10
        pid_class_aware: 0.10
        bom_detector: 0.40
```

**작업 항목**:
- [ ] API 스펙에 model_defaults 섹션 추가
- [ ] specService.ts에서 model_defaults 파싱
- [ ] 노드 파라미터 UI에서 모델 선택 시 기본값 변경

---

## 우선순위 및 일정

| 작업 | 우선순위 | 예상 작업량 | 영향 범위 |
|------|----------|-------------|-----------|
| YOLO model_defaults.py | P0 | 2시간 | yolo-api |
| OCR defaults 통합 | P1 | 3시간 | 8개 OCR API |
| Line Detector defaults | P1 | 1시간 | line-detector-api |
| API 스펙 model_defaults | P2 | 2시간 | 모든 스펙 |
| 프론트엔드 동기화 | P2 | 3시간 | nodeDefinitions |
