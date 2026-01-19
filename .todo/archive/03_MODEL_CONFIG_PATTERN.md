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

### 2. OCR APIs (우선순위: MEDIUM) ✅ 완료 (2026-01-16)
**현재 상태**: 모든 OCR API에 defaults.py 패턴 적용 완료
**결과**: 8개 OCR API + Gateway 통합 설정

**생성된 파일**:
| API | 파일 | 라인 수 | 프로파일 수 |
|-----|------|---------|-------------|
| edocr2 | config/defaults.py | 184줄 | 7개 |
| paddleocr | config/defaults.py | 134줄 | 6개 |
| tesseract | config/defaults.py | 134줄 | 7개 |
| trocr | config/defaults.py | 113줄 | 6개 |
| surya | config/defaults.py | 116줄 | 7개 |
| doctr | config/defaults.py | 111줄 | 6개 |
| easyocr | config/defaults.py | 130줄 | 7개 |
| ensemble | config/defaults.py | 160줄 | 7개 |
| **Gateway** | ocr_defaults.py | 263줄 | 통합 관리 |

**작업 항목**:
- [x] ocr_defaults.py 생성 ✅
- [x] 각 OCR API별 config/defaults.py 생성 ✅
- [x] 용도별 권장 설정 (USE_CASE_RECOMMENDATIONS) 추가 ✅

---

### 3. Line Detector (우선순위: MEDIUM) ✅ 완료 (2026-01-17)
**현재 상태**: ✅ config/defaults.py 적용 및 라우터 통합 완료
**결과**: 4개 프로파일 (pid, simple, region_focus, connectivity)

**적용 내용**:
- `config/defaults.py`: DEFAULTS, DETECTION_DEFAULTS 정의 (189줄)
- `routers/process_router.py`: 프로파일 기반 파라미터 적용
- `/api/v1/profiles` 엔드포인트 추가
- `/api/v1/info`에 profiles 정보 추가
- `/api/v1/process`에 profile 파라미터 추가

```python
# 프로파일 예시
DEFAULTS = {
    "pid": {"method": "lsd", "classify_types": True, "detect_regions": True, ...},
    "simple": {"method": "lsd", "classify_types": False, ...},
    "region_focus": {"detect_regions": True, "classify_styles": True, ...},
    "connectivity": {"find_intersections": True, ...},
}
```

---

### 4. EDGNet (우선순위: MEDIUM) ✅ 완료 (2026-01-17)
**현재 상태**: ✅ config/defaults.py 적용 및 라우터 통합 완료
**결과**: 6개 프로파일 (drawing_classification, text_detection, edge_detection, mask_extraction, graph_analysis, fast)

**적용 내용**:
- `config/defaults.py`: DEFAULTS, MODEL_CONFIGS 정의
- `routers/segment_router.py`: 프로파일 기반 파라미터 적용
- `/api/v1/profiles` 엔드포인트 추가
- `/api/v1/info`에 profiles 정보 추가
- `/api/v1/segment`에 profile 파라미터 추가

---

### 5. Design Checker (우선순위: LOW)
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

| 작업 | 우선순위 | 예상 작업량 | 영향 범위 | 상태 |
|------|----------|-------------|-----------|------|
| YOLO model_defaults.py | P0 | 2시간 | yolo-api | ✅ 완료 |
| OCR defaults 통합 | P1 | 3시간 | 8개 OCR API | ✅ 완료 (2026-01-16) |
| Line Detector defaults | P1 | 1시간 | line-detector-api | ✅ 완료 (2026-01-17, 라우터 통합) |
| EDGNet defaults | P1 | 1시간 | edgnet-api | ✅ 완료 (2026-01-17, 6 프로파일) |
| API 스펙 profiles 섹션 | P2 | 1시간 | 4개 스펙 | ✅ 완료 (2026-01-17) |
| 프론트엔드 동기화 | P2 | 1시간 | specService, NodeDetailPanel | ✅ 완료 (2026-01-17) |

---

## API 스펙 profiles 섹션 (2026-01-17 완료)

백엔드 `config/defaults.py`와 동기화된 `profiles` 섹션을 API 스펙에 추가:

| API | 스펙 파일 | 프로파일 수 | 기본 프로파일 |
|-----|----------|-------------|---------------|
| YOLO | yolo.yaml | 4개 | bom_detector |
| eDOCr2 | edocr2.yaml | 7개 | full |
| EDGNet | edgnet.yaml | 6개 | drawing_classification |
| Line Detector | line-detector.yaml | 4개 | pid |

### profiles 섹션 구조

```yaml
profiles:
  default: profile_name
  available:
    - name: profile_name
      label: "표시 이름"
      description: "프로파일 설명"
      params:
        param1: value1
        param2: value2
```

### 프론트엔드 활용

- `specService.ts`에서 `profiles` 섹션 파싱
- 노드 파라미터 UI에서 프로파일 선택 시 기본값 자동 적용
- `params` 값으로 해당 파라미터 필드 업데이트

---

## 프론트엔드 동기화 (2026-01-17 완료)

### 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `src/config/nodes/types.ts` | `ProfileDefinition`, `ProfilesConfig` 타입 추가 |
| `src/config/nodes/index.ts` | 프로파일 타입 export |
| `src/config/nodeDefinitions.ts` | 프로파일 타입 re-export |
| `src/services/specService.ts` | `APISpec` 인터페이스에 profiles 추가, `specToNodeDefinition`에서 파싱 |
| `src/components/blueprintflow/NodeDetailPanel.tsx` | 프로파일 선택 UI 추가 |

### 프로파일 선택 UI

```tsx
{/* Profile Selector */}
{definition.profiles && (
  <div className="p-3 bg-gradient-to-r from-purple-50 to-indigo-50 ...">
    <select
      value={selectedNode.data?.parameters?._profile || definition.profiles.default}
      onChange={(e) => {
        const profile = definition.profiles?.available.find(p => p.name === profileName);
        if (profile) {
          // 프로파일의 모든 파라미터 적용
          onUpdateNode(selectedNode.id, {
            parameters: {
              ...currentParams,
              ...profile.params,
              _profile: profileName,
            },
          });
        }
      }}
    >
      {definition.profiles.available.map((profile) => (
        <option key={profile.name} value={profile.name}>
          {profile.label}
        </option>
      ))}
    </select>
  </div>
)}
```

### 동작 방식

1. API 스펙에서 `profiles` 섹션 로드
2. `NodeDetailPanel`에서 프로파일 선택 드롭다운 표시
3. 프로파일 선택 시 해당 프로파일의 `params`가 노드의 파라미터에 적용
4. `_profile` 필드에 선택된 프로파일 이름 저장 (상태 유지용)
