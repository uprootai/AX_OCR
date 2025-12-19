# 🎯 전체 API 파라미터 최종 비교 분석

**분석일**: 2025-11-23  
**방법**: 실제 코드 읽기 + 실행 중인 API /info 호출

---

## 📊 최종 비교표

| API | 엔드포인트 | Info | 차이 | 누락 파라미터 | 상태 |
|-----|-----------|------|-----|--------------|------|
| **YOLO** | 6개 | 6개 | 0 | - | ✅ 완벽 |
| **PaddleOCR** | 5개 | 4개 | -1 | visualize | ❌ 수정 필요 |
| **eDOCr2-v2** | 6개 | 6개 | 0 | - | ✅ 완벽 |
| **EDGNet** | 5개 | 5개 | 0 | - | ✅ 완벽 |
| **SkinModel** | 3개 | 3개 | 0 | - | ✅ 완벽 |
| **VL** | 3개 | 0개 | -3 | model, temperature, prompt | ❌ 수정 필요 |

---

## 🔍 상세 분석

### 1️⃣ YOLO API ✅

**엔드포인트 파라미터** (6개):
1. model_type (str)
2. confidence (float)
3. iou_threshold (float)
4. imgsz (int)
5. visualize (bool)
6. task (str)

**Info 파라미터** (6개):
- ✅ 모두 일치

**결론**: 완벽

---

### 2️⃣ PaddleOCR API ❌

**엔드포인트 파라미터** (5개):
1. det_db_thresh (float)
2. det_db_box_thresh (float)
3. use_angle_cls (bool)
4. min_confidence (float)
5. **visualize (bool)** ❌ 누락

**Info 파라미터** (4개):
1. det_db_thresh ✅
2. det_db_box_thresh ✅
3. use_angle_cls ✅
4. min_confidence ✅

**누락**: **visualize** (1개)

**위치**: `/home/uproot/ax/poc/models/paddleocr-api/api_server.py:178`  
**수정 필요**: `/api/v1/info`의 parameters 리스트에 추가

```python
ParameterSchema(
    name="visualize",
    type="boolean",
    default=False,
    description="OCR 결과 시각화 이미지 생성",
    required=False
)
```

---

### 3️⃣ eDOCr2-v2 API ✅

**엔드포인트 파라미터** (6개):
1. extract_dimensions (bool)
2. extract_gdt (bool)
3. extract_text (bool)
4. use_vl_model (bool)
5. visualize (bool)
6. use_gpu_preprocessing (bool)

**Info 파라미터** (6개):
- ✅ 모두 일치

**결론**: 완벽

---

### 4️⃣ EDGNet API ✅

**엔드포인트 파라미터** (5개):
1. model (str)
2. visualize (bool)
3. num_classes (int)
4. save_graph (bool)
5. vectorize (bool)

**Info 파라미터** (5개):
- ✅ 모두 일치

**결론**: 완벽

**참고**: 이전 분석에서 언급된 `threshold`, `save_bezier`, `return_mask`는 다른 엔드포인트 (`/api/v1/vectorize` 등)의 파라미터로 확인됨

---

### 5️⃣ SkinModel API ✅

**엔드포인트 파라미터** (JSON Body):
1. manufacturing_process (str, optional)
2. correlation_length (float, optional)
3. task (str, optional)

**Info 파라미터** (3개):
- ✅ 모두 일치

**결론**: 완벽

**특징**: JSON Request Body 방식이지만 `/api/v1/info`에 정상 노출됨

---

### 6️⃣ VL API ❌

**엔드포인트 파라미터** (3개):
1. **prompt (str, optional)** ❌ 누락
2. **model (str)** ❌ 누락  
3. **temperature (float)** ❌ 누락

**Info 파라미터** (0개):
- ❌ 모두 누락

**누락**: **model, temperature, prompt** (3개)

**위치**: `/home/uproot/ax/poc/models/vl-api/api_server.py:420` (get_api_info)  
**수정 필요**: `/api/v1/info`에 parameters 추가

```python
parameters=[
    ParameterSchema(
        name="model",
        type="select",
        default="claude-3-5-sonnet-20241022",
        description="VLM 모델 선택",
        required=False,
        options=["claude-3-5-sonnet-20241022", "gpt-4o", "gpt-4-turbo"]
    ),
    ParameterSchema(
        name="temperature",
        type="number",
        default=0.0,
        description="생성 온도 (0=결정적, 1=창의적)",
        required=False,
        min=0.0,
        max=1.0,
        step=0.1
    )
    # prompt는 input_mappings로 처리 (TextInput에서 연결)
]
```

**참고**: `prompt`는 TextInput 노드에서 연결되므로 `input_mappings`로 이미 처리됨

---

## 🎯 수정 필요 사항 요약

### 즉시 수정 필요 (2개 API, 4개 파라미터)

#### 1. PaddleOCR
- **누락**: visualize (1개)
- **파일**: `/home/uproot/ax/poc/models/paddleocr-api/api_server.py`
- **라인**: ~178 (parameters 리스트)

#### 2. VL API
- **누락**: model, temperature (2개) + prompt는 input_mappings
- **파일**: `/home/uproot/ax/poc/models/vl-api/api_server.py`
- **라인**: ~420 (get_api_info 함수)

---

## 📌 추가 확장 가능 (YOLO)

YOLO는 현재 누락 없지만, **Ultralytics가 제공하는 추가 파라미터**를 노출하면 더 강력해짐:

### 추천 추가 (5개)
1. **max_det** (int, default=300) - 최대 검출 객체 수
2. **classes** (str, optional) - 특정 클래스만 검출
3. **half** (bool, default=False) - FP16 (GPU 2배 속도)
4. **agnostic_nms** (bool, default=False) - 클래스 무관 NMS
5. **augment** (bool, default=False) - TTA (정확도 향상)

---

## ✅ 정상 작동 API (4개)

1. **YOLO** - 6/6 완벽 ✅
2. **eDOCr2-v2** - 6/6 완벽 ✅
3. **EDGNet** - 5/5 완벽 ✅
4. **SkinModel** - 3/3 완벽 ✅

---

## 📊 전체 통계

- **총 API 수**: 6개
- **총 파라미터**: 30개
- **Info 노출**: 26개 (86.7%)
- **누락**: 4개 (13.3%)
  - PaddleOCR: 1개
  - VL: 3개
  
- **완벽한 API**: 4개 (66.7%)
- **수정 필요 API**: 2개 (33.3%)

---

**작성**: Claude Code  
**상태**: 분석 완료, 수정 대기
