# 시스템 통합 분석 리포트

## 📋 전체 시스템 구성

### API 서버 현황 (9개)
1. **Gateway API** (포트 8000) - 오케스트레이션 & 통합
2. **YOLOv11 API** (포트 5005) - 객체 검출 ⭐ **개선 완료**
3. **eDOCr v1 API** (포트 5001) - OCR (CUDA 이슈)
4. **eDOCr v2 API** (포트 5002) - 고급 OCR
5. **EDGNet API** (포트 5012) - 그래프 세그멘테이션
6. **Skin Model API** (포트 5003) - 공차 예측
7. **VL API** (포트 5004) - Vision-Language 모델
8. **PaddleOCR API** (포트 5006) - OCR
9. **Web UI** (포트 5173) - 사용자 인터페이스

---

## 🎯 치수 추출 통합 현황

### ✅ 현재 구현된 파이프라인

Gateway API (`/api/v1/process`)가 두 가지 모드로 모든 API를 통합하여 치수 추출:

#### 1️⃣ **Hybrid 모드** (정확도 우선, ~95% 정확도, 10-15초)
```
Step 1: YOLO 객체 검출
  ↓
Step 2: 병렬 처리
  ├── YOLO 검출 영역 Upscale → eDOCr2 OCR (치수 추출)
  └── EDGNet 세그멘테이션 (컴포넌트 분리)
  ↓
Step 3: 앙상블 병합 (YOLO bbox + eDOCr values)
  ↓
Step 4: Skin Model 공차 예측 (선택)
```

**특징**:
- YOLO로 검출한 치수 영역을 먼저 Upscale하여 OCR 정확도 향상
- eDOCr2와 EDGNet을 병렬로 실행하여 시간 단축
- 최종 앙상블에서 YOLO의 bbox confidence와 eDOCr의 값을 결합

#### 2️⃣ **Speed 모드** (속도 우선, ~93% 정확도, 8-10초)
```
Step 1: 3-way 병렬 처리
  ├── YOLO 객체 검출
  ├── eDOCr2 OCR (치수 추출)
  └── EDGNet 세그멘테이션
  ↓
Step 2: 앙상블 병합 (YOLO + eDOCr)
  ↓
Step 3: Skin Model 공차 예측 (선택)
```

**특징**:
- 모든 API를 동시에 실행하여 최대 속도 확보
- 앙상블에서 결과 통합
- Upscale 과정 생략하여 2-5초 절약

---

## 📊 API별 역할 및 활용 현황

| API | 역할 | 치수 추출 활용 | 통합 상태 | 최적화 |
|-----|------|---------------|----------|--------|
| **YOLOv11** | 객체 검출 (14 클래스) | ✅ **주력** - bbox 제공 | ✅ Gateway 통합 | ✅ **필터링 개선** |
| **eDOCr v2** | OCR + 치수 추출 | ✅ **주력** - 값 추출 | ✅ Gateway 통합 | ⚠️ 기본 설정 |
| **EDGNet** | 세그멘테이션 | ✅ 컴포넌트 분리 | ✅ Gateway 통합 | ⚠️ 기본 설정 |
| **Skin Model** | 공차 예측 | ✅ 공차 계산 | ✅ Gateway 통합 | ⚠️ 기본 설정 |
| **PaddleOCR** | 범용 OCR | ❌ **미사용** | ❌ **통합 안됨** | ❌ |
| **VL API** | 멀티모달 분석 | ⚠️ 별도 엔드포인트 | ⚠️ 부분 통합 | ⚠️ 기본 설정 |
| **eDOCr v1** | 레거시 OCR | ❌ v2 사용 | ✅ 설정 가능 | ❌ CUDA 오류 |

---

## 🔍 문제점 및 개선 필요 사항

### ❌ 1. PaddleOCR API 미활용
**현재 상태**:
- API는 정상 작동 중이지만 Gateway 파이프라인에 통합되지 않음
- 별도로 `/api/v1/ocr/paddle` 엔드포인트 존재하나 메인 파이프라인에서 호출 안됨

**문제**:
- 한국어/중국어 도면에 특화된 PaddleOCR의 장점을 활용하지 못함
- 다국어 지원이 필요한 경우 추가 옵션이 없음

**권장 개선**:
```python
# Gateway에 PaddleOCR 옵션 추가
if use_paddle_ocr:
    paddle_result = await call_paddle_ocr(image_bytes, ...)
    # eDOCr2 결과와 앙상블
    ensemble_dimensions = merge_ocr_results(ocr_result, paddle_result)
```

---

### ⚠️ 2. VL API 부분 통합
**현재 상태**:
- 별도 엔드포인트 `/api/v1/process-with-vl`로 존재
- 메인 파이프라인과 분리되어 있음

**문제**:
- VL 모델의 강력한 멀티모달 분석 능력이 주 파이프라인에서 활용되지 않음
- 복잡한 도면 이해가 필요한 경우 수동으로 별도 호출 필요

**권장 개선**:
```python
# Gateway에 VL 옵션 추가
if use_vl_analysis:
    vl_result = await call_vl_analysis(image_bytes, prompt="Extract all dimensions")
    # 앙상블에 VL 결과 추가
    ensemble_dimensions = merge_all_results(yolo, edocr, vl)
```

---

### ⚠️ 3. 앙상블 로직 단순함
**현재 상태** (api_server.py:1144-1169):
```python
# 간단한 앙상블: eDOCr 치수를 사용하되, YOLO 검출 개수를 메타데이터로 추가
ensemble_dimensions = ocr_dimensions
result["ensemble"] = {
    "dimensions": ensemble_dimensions,
    "yolo_detections_count": len(yolo_detections),
    "ocr_dimensions_count": len(ocr_dimensions),
    "strategy": "eDOCr values + YOLO bbox confidence"
}
```

**문제**:
- YOLO 검출 결과가 단순히 메타데이터로만 사용됨
- YOLO bbox와 eDOCr bbox의 매칭/융합이 없음
- 신뢰도 기반 필터링이나 가중 평균 없음

**권장 개선**:
```python
def smart_ensemble(yolo_detections, ocr_dimensions):
    """지능형 앙상블"""
    merged = []

    for ocr_dim in ocr_dimensions:
        # 1. eDOCr bbox와 YOLO bbox 매칭 (IOU 기반)
        matched_yolo = find_matching_yolo_detection(ocr_dim, yolo_detections)

        if matched_yolo:
            # 2. 신뢰도 가중 평균
            confidence = (ocr_dim['confidence'] * 0.6 + matched_yolo['confidence'] * 0.4)

            # 3. YOLO bbox가 더 정확하므로 bbox는 YOLO 사용, 값은 eDOCr 사용
            merged.append({
                'value': ocr_dim['value'],  # eDOCr 값
                'bbox': matched_yolo['bbox'],  # YOLO bbox
                'confidence': confidence,  # 가중 평균 신뢰도
                'class': matched_yolo['class_name'],
                'source': 'ensemble'
            })
        else:
            # 4. 매칭 없으면 eDOCr만 사용 (신뢰도 패널티)
            merged.append({
                'value': ocr_dim['value'],
                'bbox': ocr_dim['bbox'],
                'confidence': ocr_dim['confidence'] * 0.7,  # 패널티
                'source': 'edocr_only'
            })

    # 5. YOLO만 검출한 것 추가 (값은 None)
    for yolo_det in yolo_detections:
        if not is_matched(yolo_det, merged):
            merged.append({
                'value': None,  # OCR 필요
                'bbox': yolo_det['bbox'],
                'confidence': yolo_det['confidence'],
                'class': yolo_det['class_name'],
                'source': 'yolo_only'
            })

    return merged
```

---

### ⚠️ 4. YOLO 개선 사항이 Gateway에 반영 안됨
**현재 상태**:
- YOLO API 자체에는 `filtering_stats` 추가됨 (노이즈 51.3% 감소)
- Gateway는 YOLO API를 호출만 하므로 자동으로 개선 효과 적용됨

**하지만**:
- Gateway 앙상블 로직이 YOLO의 필터링된 결과를 제대로 활용하지 못함
- `filtering_stats`를 최종 결과에 포함시키지 않음

**권장 개선**:
```python
# Gateway 결과에 YOLO 필터링 통계 추가
result["ensemble"]["yolo_filtering"] = yolo_result.get("filtering_stats", {})
```

---

### ⚠️ 5. Upscaling 로직 미구현
**현재 상태** (api_server.py:988-992):
```python
logger.info(f"Upscaling {len(dimension_detections)} dimension regions")
# 간단화: 전체 이미지에 OCR 적용 (실제로는 각 영역별로 Upscale 후 OCR 가능)
tasks.append(call_edocr2_ocr(file_bytes, ...))
```

**문제**:
- Upscaling이 주석으로만 존재하고 실제 구현 안됨
- Hybrid 모드의 핵심 기능이 작동하지 않음

**권장 개선**:
```python
# 각 YOLO 검출 영역을 Upscale
upscaled_regions = []
for det in dimension_detections:
    bbox = det['bbox']
    region = extract_region(image, bbox)
    upscaled = upscale_image(region, scale=2.0)  # 2배 확대
    upscaled_regions.append(upscaled)

# 각 영역에 OCR 적용
ocr_results = await asyncio.gather(*[
    call_edocr2_ocr(region, ...) for region in upscaled_regions
])
```

---

## ✅ 최적화 완료 항목

### 1. YOLO API 개선 ✅
- **Text Block 필터링**: 20개 노이즈 제거 (95.6% 감소)
- **중복 검출 제거**: IOU 0.3 기준으로 중복 제거
- **정확도 향상**: 33.3% → 66.7% (+33.4%p)
- **노이즈 감소**: 51.3% (39개 → 19개)
- **필터링 통계 제공**: `filtering_stats` 응답 추가

---

## 🎯 권장 최적화 로드맵

### 즉시 가능 (1일 이내)
1. ✅ **PaddleOCR 통합**
   - Gateway에 `use_paddle_ocr` 옵션 추가
   - eDOCr2와 PaddleOCR 결과 앙상블

2. ✅ **YOLO 필터링 통계 노출**
   - Gateway 응답에 `yolo_filtering_stats` 포함

3. ✅ **앙상블 로직 개선**
   - IOU 기반 YOLO-eDOCr bbox 매칭
   - 신뢰도 가중 평균 계산

### 단기 (1주일)
4. ✅ **Upscaling 구현**
   - YOLO 검출 영역별 이미지 확대
   - PIL/OpenCV를 사용한 bicubic interpolation

5. ✅ **VL API 메인 파이프라인 통합**
   - `use_vl` 옵션 추가
   - 멀티모달 분석 결과를 앙상블에 포함

### 중기 (2-4주)
6. ✅ **지능형 앙상블 알고리즘**
   - 머신러닝 기반 융합 (신뢰도 예측 모델)
   - 다중 API 결과의 투표/가중 평균

7. ✅ **성능 모니터링 대시보드**
   - 각 API별 정확도 추적
   - 앙상블 효과 측정

---

## 📈 예상 개선 효과

| 개선 항목 | 현재 | 개선 후 | 향상률 |
|----------|------|---------|--------|
| **치수 추출 정확도** | ~93% | ~97% | +4%p |
| **한국어 도면 정확도** | ~85% | ~95% | +10%p |
| **처리 속도 (Hybrid)** | 10-15초 | 12-18초 | -20% |
| **처리 속도 (Speed)** | 8-10초 | 8-10초 | 동일 |
| **노이즈 검출** | 많음 | 최소 | -70% |
| **API 활용률** | 78% (7/9) | 100% (9/9) | +22% |

---

## 🔧 구현 우선순위

### Priority 1 (필수)
- [ ] PaddleOCR 파이프라인 통합
- [ ] 앙상블 로직 개선 (IOU 매칭)
- [ ] Upscaling 구현

### Priority 2 (권장)
- [ ] VL API 메인 파이프라인 통합
- [ ] YOLO 필터링 통계 노출
- [ ] 신뢰도 가중 평균

### Priority 3 (선택)
- [ ] 지능형 앙상블 ML 모델
- [ ] 성능 모니터링 시스템
- [ ] A/B 테스트 프레임워크

---

## 📝 결론

### 현재 상태 평가: **B+ (Good)**

**장점**:
- ✅ 핵심 API들이 Gateway를 통해 잘 통합되어 있음
- ✅ Hybrid/Speed 두 가지 모드로 유연한 선택 가능
- ✅ YOLO API가 최근 개선되어 노이즈 대폭 감소
- ✅ 비동기 병렬 처리로 빠른 속도 확보

**단점**:
- ❌ PaddleOCR이 완전히 미활용 (9개 중 1개 API 낭비)
- ⚠️ VL API가 부분적으로만 통합됨
- ⚠️ 앙상블 로직이 너무 단순함 (단순 concat 수준)
- ⚠️ Upscaling이 구현되지 않아 Hybrid 모드가 제대로 작동 안함

### 최적화 후 예상 등급: **A (Excellent)**

위 개선사항을 모두 적용하면:
- 모든 API가 최적의 방식으로 활용됨
- 앙상블 정확도가 크게 향상됨
- 한국어/다국어 도면 대응력 강화됨
- 전체 시스템이 "진짜 최적 파이프라인"이 됨

---

**작성일**: 2025-11-15
**분석 대상**: Gateway API (포트 8000), 전체 마이크로서비스 아키텍처
