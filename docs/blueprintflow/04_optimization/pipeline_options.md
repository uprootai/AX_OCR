# 후처리 파이프라인 옵션

**4 post-processing strategies for optimal OCR accuracy**

---

## 🎯 Overview

YOLO 검출 후 OCR 정확도를 높이는 4가지 후처리 전략을 제공합니다.

**핵심 선택 기준**:
- 속도 우선 → Option A 또는 D
- 정확도 우선 → Option B
- 균형 → Option C

---

## Option A: 배경 제거 → 전체 이미지 OCR

### Pipeline
```
YOLO Detection → Background Removal → Full Image OCR
```

### 장점
- ⚡ OCR 1회 호출로 빠름 (0.5초)
- 📈 배경 노이즈 제거로 인식률 향상 (+15%)

### 단점
- ⚠️ 객체 간 간섭 가능 (겹쳐 보이는 경우)

### 적합한 경우
- 객체가 적고 (< 10개) 간격이 넓은 도면
- 속도 우선 시나리오

---

## Option B: Crop → Scale Up → 개별 OCR

### Pipeline
```
YOLO Detection → Crop Each BBox → Scale Up (2x) → Individual OCR
```

### 장점
- 🎯 개별 객체에 집중하여 정확도 최고 (+25%)
- 🔍 작은 텍스트도 Scale Up으로 인식 가능

### 단점
- 🐌 OCR N회 호출로 느림 (N * 0.3초)
- 💾 메모리 사용량 높음

### 적합한 경우
- 정확도 최우선 (품질 검사, 규격 검증)
- 작은 글씨가 많은 도면

---

## Option C: 배경 제거 + Crop → 개별 OCR

### Pipeline
```
YOLO Detection → Background Removal → Crop Each → Individual OCR
```

### 장점
- ⚖️ 배경 제거 + 개별 처리로 균형 잡힌 정확도
- ⚡ Option B보다 빠름 (Scale Up 생략)

### 단점
- 🔄 여전히 OCR N회 호출 필요

### 적합한 경우
- 중간 정도 객체 수 (10-30개)
- 정확도와 속도 균형

---

## Option D: YOLO 스킵 → 전체 이미지 직접 OCR

### Pipeline
```
Image → eDOCr2 (Full Image)
```

### 장점
- ⚡⚡ 가장 빠름 (0.5초)
- ✅ YOLO 오검출 위험 없음

### 단점
- 📉 배경 노이즈로 인식률 낮음 (-20%)
- ❌ 심볼 위치 정보 없음

### 적합한 경우
- 텍스트만 있는 단순 도면
- 프로토타입 테스트

---

## 📊 성능 비교표

| 파이프라인 | 속도 | 정확도 | 메모리 | 추천 상황 |
|----------|------|--------|--------|----------|
| **Option A** (배경 제거 + 전체 OCR) | ⚡⚡⚡ (0.5초) | 80% | 낮음 | 객체 < 10개, 간격 넓음 |
| **Option B** (Crop + Scale Up) | ⚡ (N * 0.3초) | 95% | 높음 | 정확도 최우선, 작은 글씨 |
| **Option C** (배경 제거 + Crop) | ⚡⚡ (N * 0.2초) | 90% | 중간 | 균형 잡힌 품질 |
| **Option D** (YOLO 스킵) | ⚡⚡⚡⚡ (0.5초) | 60% | 낮음 | 텍스트만 있는 단순 도면 |

---

## 🔧 Required Nodes (Implementation)

BlueprintFlow에 다음 노드 추가 필요:

1. **BackgroundRemoval Node**
   - OpenCV 기반 배경 제거
   - Parameter: `threshold` (0-255)

2. **CropAndScale Node**
   - BBox 기반 Crop + Resize
   - Parameters: `scale_factor` (1.0-3.0), `padding` (0-50px)

3. **BatchOCR Node**
   - 여러 영역 동시 OCR
   - Parameter: `batch_size` (1-32)

**Estimated LOC**: ~200 lines (3 new nodes)

---

**See Also**:
- [yolo_models.md](yolo_models.md) - YOLO model selection
- [optimization_guide.md](optimization_guide.md) - Implementation roadmap
- [../02_builder/README.md](../02_builder/README.md) - Node creation guide
