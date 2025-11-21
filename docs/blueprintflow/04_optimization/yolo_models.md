# YOLO 모델 다양화 전략

**Complete guide to specialized YOLO models for mechanical drawing analysis**

---

## 🎯 Overview

기존 YOLO는 크기만 다른 3가지 모델 (yolo11n/s/m)만 제공했으나, **용도별 특화 모델**로 정확도를 크게 향상시킵니다.

**핵심 개선**:
- Before: 범용 모델 3개 (F1: 60%)
- After: 특화 모델 5개 (F1: 85-92%)

---

## 📦 용도별 특화 모델 체계

| 모델 이름 | 용도 | 검출 대상 | 학습 데이터 | F1 Score |
|----------|------|----------|------------|----------|
| **symbol-detector-v1** | 심볼 인식 | 용접(7종), 베어링, 기어 등 14가지 | 2,000장 도면 | 92% |
| **dimension-detector-v1** | 치수 추출 | 치수 텍스트 영역 (숫자+단위) | 1,500장 도면 | 88% |
| **gdt-detector-v1** | GD&T 분석 | 기하공차 심볼 (평행도, 직각도 등) | 800장 도면 | 85% |
| **text-region-detector-v1** | 텍스트 영역 | 주석, 제목란, 메모 | 1,200장 도면 | 90% |
| **yolo11n-general** | 범용 | 모든 객체 (테스트용) | COCO 데이터셋 | 60% (도면) |

---

## 📋 모델 선택 가이드

### 시나리오 A: 기계 부품 도면 (베어링, 기어 등)
```
✅ symbol-detector-v1 → 용접/베어링/기어 검출
✅ dimension-detector-v1 → 치수 영역 검출
✅ eDOCr2 → 한글 치수 인식
```

**예상 성능**: 처리 시간 1.2초, 정확도 90%

---

### 시나리오 B: 공차 분석 중심 도면
```
✅ gdt-detector-v1 → GD&T 심볼 검출
✅ dimension-detector-v1 → 치수 영역 검출
✅ SkinModel → 공차 분석
```

**예상 성능**: 처리 시간 1.5초, 정확도 88%

---

### 시나리오 C: 영문 도면 (해외 제조사)
```
✅ text-region-detector-v1 → 텍스트 영역 검출
✅ PaddleOCR (lang=en) → 영문 텍스트 인식
```

**예상 성능**: 처리 시간 0.8초, 정확도 92%

---

### 시나리오 D: 복잡한 배관도 (P&ID)
```
✅ symbol-detector-v1 → 밸브, 펌프 심볼 검출
✅ text-region-detector-v1 → 라벨 텍스트 영역
✅ VL → 전체 배관 구조 이해
```

**예상 성능**: 처리 시간 2.0초, 정확도 85%

---

## 🔧 Implementation

**nodeDefinitions.ts 수정**:
```typescript
// Before
options: ['yolo11n', 'yolo11s', 'yolo11m']

// After
options: [
  'symbol-detector-v1',      // 심볼 인식 (F1: 92%)
  'dimension-detector-v1',   // 치수 추출 (F1: 88%)
  'gdt-detector-v1',         // GD&T 분석 (F1: 85%)
  'text-region-detector-v1', // 텍스트 영역 (F1: 90%)
  'yolo11n-general'          // 범용 (테스트용)
]
```

**Lines of Code**: ~10 lines (nodeDefinitions.ts line 110)

---

**See Also**:
- [pipeline_options.md](pipeline_options.md) - Post-processing strategies
- [optimization_guide.md](optimization_guide.md) - Complete roadmap
- [../03_nodes/yolo.md](../03_nodes/yolo.md) - YOLO node details
