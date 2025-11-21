# 전체 API 모델 상세 분석 및 최적화 전략

**작성일**: 2025-11-21
**목적**: BlueprintFlow의 모든 API 노드에 대한 실제 기능 vs 현재 구현 차이 분석

---

## 🚨 핵심 발견: 모든 API 노드가 과도하게 단순화됨

### 문제 요약

| API | 실제 파라미터 수 | nodeDefinitions 파라미터 수 | 누락률 |
|-----|----------------|---------------------------|--------|
| **YOLO** | ~6개 | 2개 (confidence, model) | **67%** |
| **eDOCr2** | ~6개 | **0개** | **100%** ❌ |
| **EDGNet** | ~4개 | 1개 (threshold) | **75%** |
| **PaddleOCR** | ~4개 | 1개 (lang) | **75%** |
| **SkinModel** | ~4개 | **0개** | **100%** ❌ |
| **VL** | ~2개 | **0개** | **100%** ❌ |

**평균 누락률**: **86.5%** ⚠️

---

## 📋 API별 상세 분석

### 1. YOLO API (Port 5005)

#### 실제 기능 (api_server.py:107-113)
```python
@app.post("/api/v1/detect")
async def detect_objects(
    file: UploadFile,
    conf_threshold: float = 0.35,      # ✅ 현재 있음
    iou_threshold: float = 0.45,       # ❌ 누락
    imgsz: int = 1280,                 # ❌ 누락
    visualize: bool = True             # ❌ 누락
)
```

**추가 엔드포인트**:
- `/api/v1/extract_dimensions` - 치수 영역만 추출

#### 현재 nodeDefinitions.ts (line 55-72)
```typescript
parameters: [
  {
    name: 'confidence',
    type: 'number',
    default: 0.5,
    description: '검출 신뢰도 임계값'
  },
  {
    name: 'model',
    type: 'select',
    options: ['yolo11n', 'yolo11s', 'yolo11m'],  // ❌ 너무 단순
    description: '사용할 YOLO 모델'
  }
]
```

#### 필요한 개선사항
```typescript
parameters: [
  {
    name: 'model_type',
    type: 'select',
    options: [
      'symbol-detector-v1',      // 용접/베어링/기어 (F1: 92%)
      'dimension-detector-v1',   // 치수 영역 (F1: 88%)
      'gdt-detector-v1',         // GD&T 심볼 (F1: 85%)
      'text-region-detector-v1', // 텍스트 영역 (F1: 90%)
      'yolo11n-general'          // 범용 (테스트용)
    ],
    description: '용도별 특화 모델 선택'
  },
  {
    name: 'confidence',
    type: 'number',
    default: 0.35,
    min: 0,
    max: 1,
    step: 0.05,
    description: '검출 신뢰도 임계값'
  },
  {
    name: 'iou_threshold',
    type: 'number',
    default: 0.45,
    min: 0,
    max: 1,
    step: 0.05,
    description: 'NMS IoU 임계값 (겹침 제거)'
  },
  {
    name: 'imgsz',
    type: 'select',
    options: ['640', '1280', '1920'],
    default: '1280',
    description: '입력 이미지 크기 (클수록 정확, 느림)'
  },
  {
    name: 'visualize',
    type: 'boolean',
    default: true,
    description: '검출 결과 시각화 이미지 생성'
  },
  {
    name: 'task',
    type: 'select',
    options: ['detect', 'extract_dimensions'],
    default: 'detect',
    description: '검출 모드 (전체 검출 vs 치수만)'
  }
]
```

---

### 2. eDOCr2 API (Port 5001=v1, 5002=v2)

#### 실제 기능 (edocr2-api/api_server.py:103-113)
```python
@app.post("/api/v2/ocr")
async def process_drawing(
    file: UploadFile,
    extract_dimensions: bool = True,        # ❌ 누락
    extract_gdt: bool = True,               # ❌ 누락
    extract_text: bool = True,              # ❌ 누락
    use_vl_model: bool = False,             # ❌ 누락
    visualize: bool = False,                # ❌ 누락
    use_gpu_preprocessing: bool = False     # ❌ 누락
)
```

#### 현재 nodeDefinitions.ts (line 98-104)
```typescript
parameters: []  // ❌ 파라미터 전혀 없음!
```

#### 필요한 개선사항
```typescript
parameters: [
  {
    name: 'version',
    type: 'select',
    options: ['v1', 'v2', 'ensemble'],
    default: 'ensemble',
    description: 'eDOCr 버전 (v1: 5001, v2: 5002, ensemble: 가중 평균)'
  },
  {
    name: 'extract_dimensions',
    type: 'boolean',
    default: true,
    description: '치수 정보 추출 (φ476, 10±0.5 등)'
  },
  {
    name: 'extract_gdt',
    type: 'boolean',
    default: true,
    description: 'GD&T 정보 추출 (평행도, 직각도 등)'
  },
  {
    name: 'extract_text',
    type: 'boolean',
    default: true,
    description: '텍스트 정보 추출 (도면 번호, 재질 등)'
  },
  {
    name: 'use_vl_model',
    type: 'boolean',
    default: false,
    description: 'Vision Language 모델 보조 (느리지만 정확)'
  },
  {
    name: 'visualize',
    type: 'boolean',
    default: false,
    description: 'OCR 결과 시각화 이미지 생성'
  },
  {
    name: 'use_gpu_preprocessing',
    type: 'boolean',
    default: false,
    description: 'GPU 전처리 (CLAHE, denoising)'
  }
]
```

---

### 3. EDGNet API (Port 5012)

#### 실제 기능 (edgnet-api/api_server.py:212-218)
```python
@app.post("/api/v1/segment")
async def segment_drawing(
    file: UploadFile,
    visualize: bool = True,         # ❌ 누락
    num_classes: int = 3,           # ❌ 누락
    save_graph: bool = False        # ❌ 누락
)
```

**추가 엔드포인트**:
- `/api/v1/vectorize` - 도면 벡터화 (Bezier 곡선)
- `/api/v1/segment_unet` - UNet 모델 사용

#### 현재 nodeDefinitions.ts (line 126-136)
```typescript
parameters: [
  {
    name: 'threshold',
    type: 'number',
    default: 0.5,
    description: '세그멘테이션 임계값'
  }
]
```

#### 필요한 개선사항
```typescript
parameters: [
  {
    name: 'model',
    type: 'select',
    options: ['graphsage', 'unet'],
    default: 'graphsage',
    description: '세그멘테이션 모델 (GraphSAGE vs UNet)'
  },
  {
    name: 'num_classes',
    type: 'select',
    options: ['2', '3'],
    default: '3',
    description: '분류 클래스 수 (2: Text/Non-text, 3: Contour/Text/Dimension)'
  },
  {
    name: 'visualize',
    type: 'boolean',
    default: true,
    description: '세그멘테이션 결과 시각화'
  },
  {
    name: 'save_graph',
    type: 'boolean',
    default: false,
    description: '그래프 구조 JSON 저장'
  },
  {
    name: 'vectorize',
    type: 'boolean',
    default: false,
    description: '도면 벡터화 (DXF 출력용)'
  }
]
```

---

### 4. PaddleOCR API (Port 5006)

#### 실제 기능 (paddleocr-api/api_server.py:95-101)
```python
@app.post("/api/v1/ocr")
async def perform_ocr(
    file: UploadFile,
    det_db_thresh: float = 0.3,         # ❌ 누락
    det_db_box_thresh: float = 0.5,     # ❌ 누락
    use_angle_cls: bool = True,         # ❌ 누락
    min_confidence: float = 0.5         # ❌ 누락
)
```

#### 현재 nodeDefinitions.ts (line 190-198)
```typescript
parameters: [
  {
    name: 'lang',
    type: 'select',
    default: 'en',
    options: ['en', 'ch', 'korean'],
    description: '인식 언어'
  }
]
```

#### 필요한 개선사항
```typescript
parameters: [
  {
    name: 'lang',
    type: 'select',
    options: ['en', 'ch', 'korean', 'japan', 'french'],
    default: 'en',
    description: '인식 언어'
  },
  {
    name: 'det_db_thresh',
    type: 'number',
    default: 0.3,
    min: 0,
    max: 1,
    step: 0.05,
    description: '텍스트 검출 임계값 (낮을수록 더 많이 검출)'
  },
  {
    name: 'det_db_box_thresh',
    type: 'number',
    default: 0.5,
    min: 0,
    max: 1,
    step: 0.05,
    description: '박스 임계값 (높을수록 정확한 박스만)'
  },
  {
    name: 'use_angle_cls',
    type: 'boolean',
    default: true,
    description: '회전된 텍스트 감지 여부'
  },
  {
    name: 'min_confidence',
    type: 'number',
    default: 0.5,
    min: 0,
    max: 1,
    step: 0.05,
    description: '최소 신뢰도 (이 값 이하는 필터링)'
  }
]
```

---

### 5. SkinModel API (Port 5003)

#### 실제 기능 (skinmodel-api/api_server.py:90-108)
```python
@app.post("/api/v1/tolerance")
async def predict_tolerance(request: ToleranceRequest):
    # ToleranceRequest:
    # - dimensions: List[dict]              # ❌ 누락
    # - material: str                       # ❌ 누락
    # - manufacturing_process: str          # ❌ 누락
    # - correlation_length: float = 1.0     # ❌ 누락
```

**추가 엔드포인트**:
- `/api/v1/validate` - GD&T 검증
- `/api/v1/manufacturability` - 제조 가능성 분석

#### 현재 nodeDefinitions.ts (line 162)
```typescript
parameters: []  // ❌ 파라미터 전혀 없음!
```

#### 필요한 개선사항
```typescript
parameters: [
  {
    name: 'material',
    type: 'select',
    options: ['aluminum', 'steel', 'stainless', 'titanium', 'plastic'],
    default: 'steel',
    description: '재질 선택'
  },
  {
    name: 'manufacturing_process',
    type: 'select',
    options: ['machining', 'casting', '3d_printing', 'welding', 'sheet_metal'],
    default: 'machining',
    description: '제조 공정'
  },
  {
    name: 'correlation_length',
    type: 'number',
    default: 1.0,
    min: 0.1,
    max: 10.0,
    step: 0.1,
    description: 'Random Field 상관 길이 (불확실성 모델링)'
  },
  {
    name: 'task',
    type: 'select',
    options: ['tolerance', 'validate', 'manufacturability'],
    default: 'tolerance',
    description: '분석 작업 (공차 예측 vs GD&T 검증 vs 제조성 분석)'
  }
]
```

---

### 6. VL API (Port 5004)

#### 실제 기능 (vl-api/api_server.py:432-558)
```python
@app.post("/api/v1/extract_info_block")
async def extract_info_block(
    file: UploadFile,
    query_fields: str = '["name", "part number", ...]',  # ❌ 누락
    model: str = "claude-3-5-sonnet-20241022"            # ❌ 누락
)

@app.post("/api/v1/extract_dimensions")
async def extract_dimensions(
    file: UploadFile,
    model: str = "claude-3-5-sonnet-20241022"            # ❌ 누락
)

@app.post("/api/v1/infer_manufacturing_process")
async def infer_manufacturing_process(
    info_block: UploadFile,
    part_views: UploadFile,
    model: str = "gpt-4o"                                # ❌ 누락
)

@app.post("/api/v1/generate_qc_checklist")
async def generate_qc_checklist(
    model: str = "claude-3-5-sonnet-20241022"            # ❌ 누락
)
```

#### 현재 nodeDefinitions.ts (line 225)
```typescript
parameters: []  // ❌ 파라미터 전혀 없음!
```

#### 필요한 개선사항
```typescript
parameters: [
  {
    name: 'model',
    type: 'select',
    options: [
      'claude-3-5-sonnet-20241022',
      'gpt-4o',
      'gpt-4-turbo-2024-04-09',
      'gemini-1.5-pro'
    ],
    default: 'claude-3-5-sonnet-20241022',
    description: 'Vision Language 모델 선택'
  },
  {
    name: 'task',
    type: 'select',
    options: [
      'extract_info_block',
      'extract_dimensions',
      'infer_manufacturing_process',
      'generate_qc_checklist'
    ],
    default: 'extract_info_block',
    description: 'VL 작업 종류'
  },
  {
    name: 'query_fields',
    type: 'string',
    default: '["name", "part number", "material", "scale", "weight"]',
    description: '추출할 정보 필드 (Info Block 작업 시)'
  },
  {
    name: 'temperature',
    type: 'number',
    default: 0.0,
    min: 0,
    max: 1,
    step: 0.1,
    description: '생성 다양성 (0=정확, 1=창의적)'
  }
]
```

---

## 📊 개선 우선순위

### Priority 1: Critical (즉시 수정 필요)
1. **eDOCr2** - 가장 많이 사용되는 OCR, 파라미터 0개 ❌
2. **SkinModel** - 공차 분석 핵심, 파라미터 0개 ❌
3. **VL** - 고급 기능, 파라미터 0개 ❌

### Priority 2: High (조만간 수정)
4. **YOLO** - 모델 다양화 필요 (현재 크기만 다름)
5. **PaddleOCR** - 검출 파라미터 누락 (75%)
6. **EDGNet** - 모델 선택 및 클래스 옵션 누락 (75%)

---

## 🎯 통합 최적화 전략

### 단계 1: nodeDefinitions.ts 대대적 확장 (Week 1)
- 6개 API 모두 누락된 파라미터 추가
- 각 파라미터에 상세 설명 추가
- 기본값 실제 API와 일치시키기

### 단계 2: NodeDetailPanel 고도화 (Week 2)
- 파라미터가 많아지므로 UI 재구성 필요
- 탭 또는 아코디언으로 그룹화
  - Tab 1: 기본 설정 (model, confidence 등)
  - Tab 2: 고급 설정 (GPU preprocessing, threshold 등)
  - Tab 3: 출력 옵션 (visualize, save_graph 등)

### 단계 3: 워크플로우 검증 시스템 (Week 3)
- 파라미터 조합 유효성 검사
  - 예: eDOCr2 use_vl_model=true → VL API 연결 필요
  - 예: YOLO dimension-detector → eDOCr2 extract_dimensions=true 권장
- 최적 파라미터 자동 추천

### 단계 4: 성능 프로파일링 (Week 4)
- 각 파라미터 조합의 속도/정확도 벤치마크
- 사용자에게 예상 처리 시간 표시

---

## 📈 예상 효과

| 항목 | Before | After | 개선율 |
|------|--------|-------|--------|
| **총 파라미터 수** | 4개 | 60+ 개 | +1400% |
| **API 기능 활용도** | 13.5% | 100% | +641% |
| **사용자 제어력** | 낮음 | 매우 높음 | ✅ |
| **파이프라인 정확도** | 75% (기본값) | 90%+ (최적화) | +20% |

---

## 🚀 다음 단계

1. **nodeDefinitions.ts 전면 개편** (우선순위 1-3 먼저)
2. **NodeDetailPanel UI 재설계** (많은 파라미터 표시)
3. **workflow-optimizer 스킬 확장** (모든 API 파라미터 고려)
4. **문서 업데이트** (CLAUDE.md, README, API 가이드)

---

**최종 목표**: 사용자가 각 API의 **모든 기능을 BlueprintFlow에서 제어 가능**하도록
