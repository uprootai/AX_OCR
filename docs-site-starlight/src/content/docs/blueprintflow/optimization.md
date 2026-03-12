---
sidebar_position: 5
title: BlueprintFlow 최적화
description: YOLO 모델 다양화 전략 및 후처리 파이프라인 최적화 가이드
tags: [워크플로우, DAG, 최적화, 성능]
---

# 최적화 (Optimization)

> 용도별 YOLO 모델 다양화(5종), 후처리 파이프라인 4가지 옵션, 성능 벤치마크 계획을 포함한 파이프라인 최적화 로드맵이다.

## 핵심 문제

### 현재 상태 (Phase 1-3 완료)

- YOLO 모델이 크기만 다른 3가지 (yolo11n/s/m)만 선택 가능
- 후처리 파이프라인 옵션 부재
- 도면 종류별 최적화된 모델 조합 가이드 부족

### 실제 요구사항

도면 종류와 목적에 따라 **최적화된 모델 조합**이 필요:
- **심볼 인식**: 용접, 베어링, 기어 등 14가지 기호 검출
- **치수 추출**: 숫자와 단위가 포함된 치수 텍스트 영역 검출
- **GD&T 분석**: 기하공차 심볼 전용 검출
- **텍스트 영역**: 주석, 제목란, 메모 영역 검출

---

## YOLO 모델 다양화 전략

### 용도별 특화 모델 체계

| 모델 이름 | 용도 | 검출 대상 | 학습 데이터 | F1 Score |
|----------|------|----------|------------|----------|
| **symbol-detector-v1** | 심볼 인식 | 용접(7종), 베어링, 기어 등 14가지 | 2,000장 도면 | 92% |
| **dimension-detector-v1** | 치수 추출 | 치수 텍스트 영역 (숫자+단위) | 1,500장 도면 | 88% |
| **gdt-detector-v1** | GD&T 분석 | 기하공차 심볼 (평행도, 직각도 등) | 800장 도면 | 85% |
| **text-region-detector-v1** | 텍스트 영역 | 주석, 제목란, 메모 | 1,200장 도면 | 90% |
| **yolo11n-general** | 범용 | 모든 객체 (테스트용) | COCO 데이터셋 | 60% (도면) |

### 모델 선택 가이드

#### 시나리오 A: 기계 부품 도면 (베어링, 기어 등)

```
symbol-detector-v1 → 용접/베어링/기어 검출
dimension-detector-v1 → 치수 영역 검출
eDOCr2 → 한글 치수 인식
```

**예상 성능**: 처리 시간 1.2초, 정확도 90%

#### 시나리오 B: 공차 분석 중심 도면

```
gdt-detector-v1 → GD&T 심볼 검출
dimension-detector-v1 → 치수 영역 검출
SkinModel → 공차 분석
```

**예상 성능**: 처리 시간 1.5초, 정확도 88%

#### 시나리오 C: 영문 도면 (해외 제조사)

```
text-region-detector-v1 → 텍스트 영역 검출
PaddleOCR (lang=en) → 영문 텍스트 인식
```

**예상 성능**: 처리 시간 0.8초, 정확도 92%

#### 시나리오 D: 복잡한 배관도 (P&ID)

```
symbol-detector-v1 → 밸브, 펌프 심볼 검출
text-region-detector-v1 → 라벨 텍스트 영역
VL → 전체 배관 구조 이해
```

**예상 성능**: 처리 시간 2.0초, 정확도 85%

---

## 후처리 파이프라인 옵션

YOLO 검출 후 OCR 정확도를 높이는 4가지 후처리 전략:

### Option A: 배경 제거 → 전체 이미지 OCR

```
YOLO Detection → Background Removal → Full Image OCR
```

| 항목 | 값 |
|------|-----|
| 속도 | 0.5초 |
| 정확도 | 80% |
| 메모리 | 낮음 |
| 적합 | 객체 < 10개, 간격 넓은 도면 |

### Option B: Crop → Scale Up → 개별 OCR

```
YOLO Detection → Crop Each BBox → Scale Up (2x) → Individual OCR
```

| 항목 | 값 |
|------|-----|
| 속도 | N * 0.3초 |
| 정확도 | 95% |
| 메모리 | 높음 |
| 적합 | 정확도 최우선, 작은 글씨 |

### Option C: 배경 제거 + Crop → 개별 OCR

```
YOLO Detection → Background Removal → Crop Each → Individual OCR
```

| 항목 | 값 |
|------|-----|
| 속도 | N * 0.2초 |
| 정확도 | 90% |
| 메모리 | 중간 |
| 적합 | 정확도와 속도 균형 |

### Option D: YOLO 스킵 → 전체 이미지 직접 OCR

```
Image → eDOCr2 (Full Image)
```

| 항목 | 값 |
|------|-----|
| 속도 | 0.5초 |
| 정확도 | 60% |
| 메모리 | 낮음 |
| 적합 | 텍스트만 있는 단순 도면, 프로토타입 |

### 성능 비교표

| 파이프라인 | 속도 | 정확도 | 메모리 | 추천 상황 |
|----------|------|--------|--------|----------|
| **Option A** (배경 제거 + 전체 OCR) | 0.5초 | 80% | 낮음 | 객체 < 10개 |
| **Option B** (Crop + Scale Up) | N * 0.3초 | 95% | 높음 | 정확도 최우선 |
| **Option C** (배경 제거 + Crop) | N * 0.2초 | 90% | 중간 | 균형 잡힌 품질 |
| **Option D** (YOLO 스킵) | 0.5초 | 60% | 낮음 | 단순 도면 |

---

## 구현 로드맵

### Phase 4A: YOLO 모델 다양화 (Week 1)

- symbol-detector-v1 학습 (14개 클래스)
- dimension-detector-v1 학습 (치수 영역)
- gdt-detector-v1 학습 (GD&T 심볼)
- text-region-detector-v1 학습 (텍스트 영역)
- YOLO API에 multi-model 지원 추가

**구현량**: ~50 lines (YOLO API model loading logic)

### Phase 4B: 후처리 노드 추가 (Week 2)

필요한 노드:

1. **BackgroundRemoval Node** - OpenCV 기반 배경 제거 (parameter: `threshold` 0-255)
2. **CropAndScale Node** - BBox 기반 Crop + Resize (parameters: `scale_factor` 1.0-3.0, `padding` 0-50px)
3. **BatchOCR Node** - 여러 영역 동시 OCR (parameter: `batch_size` 1-32)

**구현량**: ~200 lines (3 new nodes)

### Phase 4C: 템플릿 고도화 (Week 3)

- Template 5: 심볼 인식 최적화 (symbol-detector + Crop + eDOCr2)
- Template 6: 치수 추출 최적화 (dimension-detector + Scale Up + eDOCr2)
- Template 7: GD&T 분석 (gdt-detector + SkinModel)
- Template 8: 영문 도면 (text-region + PaddleOCR)

**구현량**: ~100 lines (4 new templates)

### Phase 4D: 성능 벤치마크 (Week 4)

- 100장 테스트 도면으로 4가지 옵션 비교
- 속도/정확도/메모리 메트릭 수집
- 자동 파이프라인 추천 알고리즘 구현

**구현량**: ~150 lines

---

## 예상 효과

| 항목 | Before (Phase 1-3) | After (Phase 4) | 개선율 |
|------|-------------------|----------------|--------|
| **YOLO 모델 선택** | 3개 (크기만 다름) | 5개 (용도별 특화) | +67% |
| **후처리 옵션** | 1개 (시각화만) | 4개 (조합 가능) | +300% |
| **템플릿 수** | 4개 | 8개 | +100% |
| **평균 정확도** | 75% (범용) | 90% (특화) | +20% |

---

## 개발 예상치

| Phase | 예상 시간 | 코드량 |
|-------|----------|--------|
| Phase 4A (YOLO 모델) | 1 week | ~50 lines |
| Phase 4B (후처리 노드) | 2 weeks | ~200 lines |
| Phase 4C (템플릿) | 1 week | ~100 lines |
| Phase 4D (벤치마크) | 1 week | ~150 lines |
| **합계** | **5 weeks** | **~500 lines** |

**사전 요구사항**:
- Training data: 2,000+ labeled drawings
- GPU: RTX 3080 이상
- Storage: 10GB+ for model weights

---

*출처: blueprintflow/04_optimization/ 3파일 통합 (optimization_guide.md + pipeline_options.md + yolo_models.md)*

## 관련 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `Gateway /blueprintflow/execute` | 최적화 실행 |

## 관련 문서

- [BlueprintFlow](/docs/blueprintflow/) -- BlueprintFlow 개요
- [YOLO 검출](/docs/analysis-pipeline/yolo-detection) -- YOLO 검출 파이프라인 상세
- [OCR 처리](/docs/analysis-pipeline/ocr-processing) -- 후처리 파이프라인의 OCR 단계
- [템플릿](/docs/blueprintflow/templates) -- 기존 워크플로우 템플릿
- [노드 카탈로그](/docs/blueprintflow/node-catalog) -- 노드 타입 전체 레퍼런스
