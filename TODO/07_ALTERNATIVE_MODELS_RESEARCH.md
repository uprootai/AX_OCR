# 대안 모델 및 개선 방안 조사

> 작성일: 2025-11-13
> 우선순위: 🟡 중장기 (연구 및 실험)
> 목적: 현재 모델의 대안 및 업그레이드 옵션 파악

---

## 🎯 조사 목적

현재 시스템의 각 AI 모델에 대해:
1. **더 나은 대안**이 있는지 조사
2. **최신 기술 동향** 파악
3. **업그레이드 가능성** 평가
4. **비용-효과 분석**

---

## 1. YOLO 대안 모델

### 현재: YOLOv11n (Nano)

**사양**:
- 파라미터: 2.6M
- 속도: 30-50ms (GPU)
- 정확도: 85-90% (F1)

### 대안 1: YOLOv8/YOLOv9

**YOLOv8**:
```
장점:
- ✅ 더 성숙함 (2023년 출시, 안정적)
- ✅ 커뮤니티 크고 문서 많음
- ✅ 더 많은 pre-trained weights

단점:
- ⚠️ v11보다 정확도 약간 낮음 (~2-3%p)
```

**YOLOv9**:
```
장점:
- ✅ PGI (Programmable Gradient Information) 기법
- ✅ GELAN (Generalized Efficient Layer Aggregation) 아키텍처
- ✅ 파라미터 효율성 좋음

단점:
- ⚠️ v11보다 느릴 수 있음
```

**비교**:
| 모델 | mAP@0.5 | 속도(ms) | 파라미터 | 권장 |
|------|---------|----------|----------|------|
| YOLOv8n | 37.3 | 40ms | 3.2M | ⭐⭐⭐ |
| YOLOv9n | 39.1 | 50ms | 2.5M | ⭐⭐⭐ |
| YOLOv11n | 39.5 | 30ms | 2.6M | ⭐⭐⭐⭐⭐ 현재 |

**결론**: YOLOv11 유지 권장 (최신 + 빠름 + 정확함)

---

### 대안 2: Faster R-CNN / Mask R-CNN (정확도 우선)

**Faster R-CNN**:
```
Two-stage detector (RPN + Detection)

장점:
- ✅ 정확도 높음 (mAP 40-45%)
- ✅ 작은 객체 검출 우수
- ✅ False positive 낮음

단점:
- ⚠️ 느림 (200-300ms per image)
- ⚠️ 실시간 처리 어려움
- ⚠️ 복잡한 아키텍처
```

**Mask R-CNN**:
```
Faster R-CNN + Instance Segmentation

장점:
- ✅ 세그멘테이션 마스크 제공
- ✅ 객체 경계 정확함
- ✅ GD&T 기호의 정확한 윤곽 추출 가능

단점:
- ⚠️ 매우 느림 (500-800ms)
- ⚠️ GPU 메모리 많이 사용
- ⚠️ 학습 데이터 많이 필요 (마스크 라벨링)
```

**권장 시나리오**:
- 실시간 처리 불필요한 경우
- 정확도가 절대적으로 중요한 경우
- 배치 처리 (overnight jobs)

**비용-효과**: 🟡 중간 (정확도 +5-10%, 속도 -5x)

---

### 대안 3: ViT (Vision Transformer) 기반 검출

**DETR (DEtection TRansformer)**:
```
End-to-end object detection with transformers

장점:
- ✅ NMS 불필요 (set prediction)
- ✅ 복잡한 장면 처리 우수
- ✅ Attention map으로 해석 가능

단점:
- ⚠️ 학습 느림 (300 epochs)
- ⚠️ 작은 객체 검출 약함
- ⚠️ 추론 속도 느림 (100-150ms)
```

**Swin Transformer**:
```
Hierarchical vision transformer

장점:
- ✅ Multi-scale feature 우수
- ✅ 도면의 다양한 크기 요소 처리 좋음
- ✅ SOTA 정확도

단점:
- ⚠️ 매우 느림 (200-300ms)
- ⚠️ 학습 데이터 많이 필요
- ⚠️ GPU 메모리 크게 사용
```

**권장**: 현재는 YOLO 유지, 장기적으로 연구 가치 있음

---

### 대안 4: 도메인 특화 모델 (Engineering Drawing Specific)

**논문 조사 필요**:
```
1. "Deep Learning for Technical Drawing Analysis" (2023)
2. "CAD Drawing Recognition with CNN" (2022)
3. "Engineering Symbol Detection using YOLO" (2024)

검색 키워드:
- "engineering drawing object detection"
- "technical drawing deep learning"
- "CAD symbol recognition"
- "mechanical drawing analysis"
```

**가능성**:
- 도면 전용 데이터셋으로 사전학습된 모델
- GD&T 기호 특화 아키텍처
- 멀티태스크 학습 (검출 + 분류 + OCR)

**Action**: 논문 DB 검색 후 적용 가능성 평가

---

## 2. OCR 대안 (eDOCr2 개선/대체)

### 현재: eDOCr2 (Mock, 실제 구현 필요)

### 대안 1: PaddleOCR (이미 구현됨)

**현황**:
- ✅ API 서버 구현 완료 (port 5006)
- ❌ Gateway 통합 안 됨

**통합 시나리오**:

**Scenario A: 완전 대체**
```
eDOCr2 제거 → PaddleOCR만 사용

장점:
- ✅ 즉시 사용 가능
- ✅ 정확도 85-95%
- ✅ 속도 빠름 (2-5초)

단점:
- ⚠️ GD&T 기호 인식 안 됨
- ⚠️ 치수 후처리 필요
```

**Scenario B: 앙상블**
```
eDOCr2 + PaddleOCR 병렬 실행 → 투표

장점:
- ✅ 정확도 향상 (앙상블 효과)
- ✅ Fallback 가능

단점:
- ⚠️ 처리 시간 2배
```

**Scenario C: Hybrid (권장)**
```
영역별로 다른 OCR 사용:
- GD&T 기호: eDOCr2 (특화)
- 일반 텍스트: PaddleOCR (범용)
- 치수: eDOCr2 + PaddleOCR 투표

장점:
- ✅ 각 영역별 최적 엔진 사용
- ✅ 정확도 최대화

단점:
- ⚠️ 복잡한 로직
- ⚠️ 영역 구분 필요 (YOLO 또는 EDGNet)
```

---

### 대안 2: EasyOCR

**라이브러리**: easyocr
**GitHub**: https://github.com/JaidedAI/EasyOCR

**장점**:
- ✅ 80+ 언어 지원
- ✅ 설치 간단 (pip install)
- ✅ GPU/CPU 자동 선택
- ✅ 각도 보정 자동

**단점**:
- ⚠️ PaddleOCR보다 느림
- ⚠️ GD&T 기호 인식 안 됨
- ⚠️ 도면 특화 아님

**비교**:
| OCR | 정확도 | 속도 | GD&T | 권장 |
|-----|--------|------|------|------|
| Tesseract | 80-85% | 중간 | ❌ | ⭐⭐ |
| EasyOCR | 85-90% | 느림 | ❌ | ⭐⭐⭐ |
| PaddleOCR | 90-95% | 빠름 | ❌ | ⭐⭐⭐⭐ |
| eDOCr2 | 90-95% | 빠름 | ✅ | ⭐⭐⭐⭐⭐ |

**결론**: eDOCr2 수리 후 PaddleOCR는 보조/검증용

---

### 대안 3: TrOCR (Transformer OCR)

**모델**: microsoft/trocr-base-handwritten
**기술**: ViT (encoder) + GPT-2 (decoder)

**장점**:
- ✅ End-to-end Transformer
- ✅ 손글씨 인식 우수
- ✅ 전후 맥락 고려 (언어 모델)

**단점**:
- ⚠️ 속도 느림 (200-500ms per line)
- ⚠️ Fine-tuning 필요
- ⚠️ GPU 메모리 사용 큼

**적용 가능성**:
```python
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

# Fine-tune on engineering drawings
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base")

# Train on:
# - Dimension text (φ476, 50±0.5)
# - GD&T symbols (⊥, ⌖, ⊗)
# - Technical terms (Tolerance, Material)

# 예상 정확도: 95%+
# 예상 속도: 300ms per text region
```

**권장**: 연구 프로젝트로 시도 가능 (2-3주)

---

### 대안 4: Multimodal LLM Fine-tuning

**모델**: LLaVA, Qwen2-VL, Florence-2

**LLaVA-NeXT**:
```
오픈소스 Vision-Language Model

장점:
- ✅ 로컬 실행 가능 (외부 API 불필요)
- ✅ Fine-tuning 가능
- ✅ 공간 추론 우수

단점:
- ⚠️ GPU 메모리 12GB+ 필요
- ⚠️ 추론 느림 (5-10초)
- ⚠️ Fine-tuning 데이터 많이 필요
```

**Qwen2-VL**:
```
Alibaba의 오픈소스 VLM

장점:
- ✅ 정확도 높음 (GPT-4V 수준)
- ✅ 한국어 지원
- ✅ Fine-tuning 공식 지원

단점:
- ⚠️ 모델 크기 큼 (7B-72B)
- ⚠️ 추론 느림
```

**Florence-2** (Microsoft):
```
Unified Vision Model

장점:
- ✅ 다양한 태스크 (Detection, OCR, Segmentation)
- ✅ 경량 버전 존재 (florence-2-base: 0.23B)
- ✅ Fine-tuning 쉬움

단점:
- ⚠️ 도메인 특화 필요
```

**권장**: Florence-2-base로 실험 (경량 + 범용)

---

## 3. 그래프 신경망 대안 (EDGNet 개선)

### 현재: GraphSAGE (5-layer)

**성능**:
- 3-클래스 정확도: 90.82%
- 2-클래스 정확도: 98.48%

### 대안 1: GAT (Graph Attention Networks)

**특징**:
- Attention mechanism으로 이웃 노드 가중치 학습

**장점**:
- ✅ 중요한 연결에 집중
- ✅ GD&T와 치수선 관계 모델링 우수
- ✅ GraphSAGE보다 표현력 높음

**단점**:
- ⚠️ 학습 느림
- ⚠️ Over-smoothing 가능

**적용**:
```python
import torch.nn as nn
from torch_geometric.nn import GATConv

class GATDrawingClassifier(nn.Module):
    def __init__(self, in_channels=19, hidden=128, out=3, heads=8):
        super().__init__()
        self.conv1 = GATConv(in_channels, hidden, heads=heads)
        self.conv2 = GATConv(hidden * heads, hidden, heads=heads)
        self.conv3 = GATConv(hidden * heads, out, heads=1)

    def forward(self, x, edge_index):
        x = F.elu(self.conv1(x, edge_index))
        x = F.elu(self.conv2(x, edge_index))
        return self.conv3(x, edge_index)
```

**예상 개선**: +2-5% 정확도

---

### 대안 2: GCN + Transformer Hybrid

**아이디어**:
- GCN으로 로컬 구조 학습
- Transformer로 글로벌 관계 모델링

**장점**:
- ✅ 멀리 떨어진 요소 관계 파악 (치수선 - 부품)
- ✅ Attention으로 해석 가능

**단점**:
- ⚠️ 복잡도 높음
- ⚠️ 학습 데이터 많이 필요

**논문**: "Graph Transformer Networks" (2019)

---

### 대안 3: DeepGCN (Very Deep GNN)

**특징**:
- 100+ 레이어 GNN
- Residual connections, DenseNet 스타일

**장점**:
- ✅ 복잡한 도면 패턴 학습 가능
- ✅ Over-smoothing 해결

**단점**:
- ⚠️ 학습 매우 느림
- ⚠️ 오버피팅 위험

**권장**: 현재 5-layer로 충분 (90%+ 정확도)

---

## 4. 공차 예측 개선 (Skin Model 대체)

### 현재: 규칙 기반 휴리스틱 (~70% 정확도)

### 대안 1: 머신러닝 회귀 모델

**Option A: Random Forest**
```python
from sklearn.ensemble import RandomForestRegressor

# 특징:
features = [
    "dimension_value",      # 치수 크기
    "material_type",        # 재질 (카테고리)
    "process",              # 공정 (카테고리)
    "surface_area",         # 표면적
    "aspect_ratio",         # 종횡비
    "edge_length",          # 모서리 길이
    "num_features"          # 특징 개수
]

# 타겟:
target = "optimal_tolerance"  # mm 단위

# 학습:
model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)

# 예상 정확도: 85-90% (MAE < 0.01mm)
```

**장점**:
- ✅ 해석 가능 (feature importance)
- ✅ 학습 빠름
- ✅ Overfitting 적음

**단점**:
- ⚠️ 복잡한 비선형 관계 캡처 어려움

---

**Option B: Neural Network**
```python
import torch.nn as nn

class TolerancePredictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(num_materials, 16)
        self.fc = nn.Sequential(
            nn.Linear(16 + 6, 128),  # 16 (material) + 6 (numerical)
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)  # Tolerance prediction
        )

    def forward(self, material_id, numerical_features):
        mat_emb = self.embedding(material_id)
        x = torch.cat([mat_emb, numerical_features], dim=1)
        return self.fc(x)

# 예상 정확도: 90-95%
```

**장점**:
- ✅ 비선형 관계 학습
- ✅ 정확도 높음

**단점**:
- ⚠️ 학습 데이터 많이 필요 (1000+ 샘플)
- ⚠️ 해석 어려움

---

### 대안 2: FEM 시뮬레이션 API 연동

**ANSYS Workbench API**:
```python
import ansys.workbench as wb

def predict_tolerance_fem(part_geometry, material, forces):
    """
    FEM 시뮬레이션으로 실제 변형 계산
    """
    # 1. Geometry import
    model = wb.create_model(part_geometry)

    # 2. Material properties
    model.set_material(material)

    # 3. Boundary conditions
    model.add_force(forces)

    # 4. Mesh generation
    model.generate_mesh()

    # 5. Solve
    results = model.solve()

    # 6. Extract tolerance
    max_deformation = results.get_max_deformation()
    return max_deformation * safety_factor
```

**장점**:
- ✅ 정확도 매우 높음 (95-98%)
- ✅ 물리 기반 (신뢰도)

**단점**:
- ⚠️ 매우 느림 (5-30분 per part)
- ⚠️ 비용 높음 (ANSYS 라이센스)
- ⚠️ 복잡한 설정

**권장**: 중요한 부품만 FEM, 나머지는 ML

---

### 대안 3: Hybrid (ML + ISO 표준)

**아이디어**:
```python
def predict_tolerance_hybrid(dimension, material, process):
    # 1. ISO 2768 표준 조회
    iso_tolerance = ISO2768_TABLE[material][process][dimension]

    # 2. ML 모델로 조정
    ml_adjustment = ml_model.predict(features)

    # 3. 최종 값
    final_tolerance = iso_tolerance * ml_adjustment

    return final_tolerance
```

**장점**:
- ✅ 표준 기반 (신뢰도)
- ✅ ML로 실제 상황 반영
- ✅ 해석 가능

**단점**:
- ⚠️ ISO 표준 DB 구축 필요

**권장**: ⭐⭐⭐⭐⭐ 가장 현실적인 접근

---

## 5. 통합 시스템 개선

### 앙상블 전략 개선

**현재**:
```python
# 단순 병합: eDOCr 값 + YOLO bbox
merged_result = {
    "value": edocr_value,
    "bbox": yolo_bbox,
    "confidence": yolo_confidence
}
```

**개선안: 가중치 기반 앙상블**
```python
def weighted_ensemble(yolo_result, edocr_result, paddleocr_result):
    """
    신뢰도 가중 평균
    """
    weights = {
        "yolo": 0.4,       # Bbox 정확도
        "edocr": 0.4,      # 치수 추출 정확도
        "paddle": 0.2      # 보조 검증
    }

    # 1. Bbox는 YOLO가 최고
    final_bbox = yolo_result["bbox"]

    # 2. 값은 투표
    values = [
        (edocr_result["value"], weights["edocr"]),
        (paddleocr_result["value"], weights["paddle"])
    ]

    # 3. 가중 평균 또는 투표
    final_value = weighted_vote(values)

    # 4. 신뢰도 계산
    final_confidence = calculate_ensemble_confidence(
        yolo_result["confidence"],
        edocr_result["confidence"],
        paddleocr_result["confidence"]
    )

    return {
        "value": final_value,
        "bbox": final_bbox,
        "confidence": final_confidence
    }
```

---

### 멀티태스크 학습

**아이디어**: 하나의 모델로 여러 태스크 동시 학습

**아키텍처**:
```
Shared Backbone (ResNet, ViT)
    ├── Detection Head (YOLO-like)
    ├── OCR Head (TrOCR-like)
    ├── Segmentation Head (U-Net-like)
    └── Classification Head (GD&T symbol)
```

**장점**:
- ✅ Feature sharing (효율적)
- ✅ 통합 모델 (배포 간단)
- ✅ End-to-end 학습

**단점**:
- ⚠️ 학습 복잡함 (loss balancing)
- ⚠️ 개별 태스크 튜닝 어려움

**논문**: "MultiTask-CenterNet" (2020)

**권장**: 장기 R&D 프로젝트 (3-6개월)

---

## 6. 최신 기술 동향 (2024-2025)

### SAM (Segment Anything Model) 활용

**Meta SAM**:
- Zero-shot segmentation
- 도면의 개별 요소 자동 분리 가능

**적용 아이디어**:
```python
from segment_anything import SamPredictor

# 1. SAM으로 모든 요소 세그멘테이션
predictor = SamPredictor(sam_model)
masks = predictor.predict_everything(drawing_image)

# 2. 각 마스크를 YOLO로 분류
for mask in masks:
    region = crop_image(drawing_image, mask)
    class_id = yolo_model.predict(region)

# 3. 결과 병합
# 정확한 bbox (SAM) + 정확한 클래스 (YOLO)
```

---

### Diffusion Model for Data Augmentation

**Stable Diffusion + ControlNet**:
```
도면 이미지 합성으로 학습 데이터 증강

1. 기존 도면을 ControlNet edge map으로 변환
2. Stable Diffusion으로 variations 생성
3. 라벨은 원본 그대로 유지

예상 효과: 학습 데이터 10배 증가
```

---

### LLM for Engineering Knowledge

**GPT-4 + RAG (Retrieval-Augmented Generation)**:
```python
# 공차 예측에 도메인 지식 추가

knowledge_base = [
    "ISO 2768-1: General tolerances",
    "ASME Y14.5: GD&T standards",
    "Material properties database"
]

def predict_with_llm(dimension, material, process):
    # 1. Retrieve relevant standards
    context = retrieve_standards(dimension, material, process)

    # 2. LLM reasoning
    prompt = f"""
    Given:
    - Dimension: {dimension} mm
    - Material: {material}
    - Process: {process}
    - Standards: {context}

    Recommend optimal tolerance and explain why.
    """

    response = gpt4.complete(prompt)

    # 3. Parse tolerance from response
    tolerance = parse_tolerance(response.text)

    return tolerance, response.explanation
```

---

## 7. 비용-효과 분석 요약

| 대안 | 개선 효과 | 구현 시간 | 비용 | 권장도 |
|------|-----------|-----------|------|--------|
| **YOLOv8/v9** | +0-2% | 1일 | 무료 | ⭐⭐ |
| **Faster R-CNN** | +5-10% | 5-7일 | 무료 | ⭐⭐⭐ |
| **PaddleOCR 통합** | +10-15% | 1일 | 무료 | ⭐⭐⭐⭐⭐ |
| **TrOCR Fine-tune** | +5-10% | 14-21일 | 무료 | ⭐⭐⭐⭐ |
| **GAT (GNN)** | +2-5% | 5-7일 | 무료 | ⭐⭐⭐ |
| **Skin Model ML** | +15-25% | 14-21일 | 무료 | ⭐⭐⭐⭐⭐ |
| **FEM API** | +25-30% | 7-14일 | $$$ | ⭐⭐⭐ |
| **SAM 통합** | +5-10% | 3-5일 | 무료 | ⭐⭐⭐⭐ |
| **멀티태스크 학습** | +10-20% | 60-90일 | 무료 | ⭐⭐⭐ |

---

## 8. 우선순위 권장사항

### 즉시 실행 (1주일)
1. ✅ PaddleOCR 통합 (앙상블 또는 fallback)
2. ✅ 가중치 기반 앙상블 구현

### 단기 (1개월)
3. ✅ Skin Model을 ML (Random Forest) 전환
4. ✅ SAM 실험 (세그멘테이션 정확도 향상)

### 중기 (3개월)
5. ✅ TrOCR Fine-tuning (도면 특화)
6. ✅ GAT로 EDGNet 업그레이드

### 장기 (6개월+)
7. 🔬 멀티태스크 End-to-end 모델
8. 🔬 Diffusion 기반 데이터 증강
9. 🔬 LLM + RAG for Engineering Knowledge

---

## 📚 참고 자료

### 논문
- YOLOv11: arXiv 2510.21862
- eDOCr: Frontiers in Manufacturing Technology 2023
- GraphSAGE: arXiv 1706.02216
- TrOCR: arXiv 2109.10282
- SAM: arXiv 2304.02643

### GitHub
- ultralytics/ultralytics: YOLOv11
- PaddlePaddle/PaddleOCR
- facebookresearch/segment-anything
- microsoft/trocr

### 표준
- ISO 2768-1: General tolerances
- ASME Y14.5: GD&T standards

---

**다음 단계**: 우선순위 1-2 항목 실험 시작
