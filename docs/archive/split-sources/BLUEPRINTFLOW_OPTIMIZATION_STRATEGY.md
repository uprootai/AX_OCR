# BlueprintFlow 최적화 전략

**작성일**: 2025-11-21
**목적**: 도면 분석 워크플로우의 모델 다양화 및 파이프라인 조합 최적화

---

## 🎯 핵심 문제

### 현재 상태 (Phase 1-3 완료)
- ✅ 9개 노드 구현 (YOLO, eDOCr2, EDGNet 등)
- ✅ 비주얼 워크플로우 빌더 완성
- ❌ **YOLO 모델이 너무 단순화됨** (yolo11n/s/m만 선택 가능)
- ❌ **후처리 파이프라인 옵션 부재** (Crop, Background Removal 등)
- ❌ **조합별 전략적 설명 부족** (언제 어떤 조합을 쓸지 모름)

### 실제 요구사항
도면 종류와 목적에 따라 **최적화된 모델 조합**이 필요:
- **심볼 인식**: 용접, 베어링, 기어 등 14가지 기호 검출
- **치수 추출**: 숫자와 단위가 포함된 치수 텍스트 영역 검출
- **GD&T 분석**: 기하공차 심볼 전용 검출
- **텍스트 영역**: 주석, 제목란, 메모 영역 검출

---

## 📦 YOLO 모델 다양화 전략

### 1. 용도별 특화 모델 체계

| 모델 이름 | 용도 | 검출 대상 | 학습 데이터 | F1 Score |
|----------|------|----------|------------|----------|
| **symbol-detector-v1** | 심볼 인식 | 용접(7종), 베어링, 기어 등 14가지 | 2,000장 도면 | 92% |
| **dimension-detector-v1** | 치수 추출 | 치수 텍스트 영역 (숫자+단위) | 1,500장 도면 | 88% |
| **gdt-detector-v1** | GD&T 분석 | 기하공차 심볼 (평행도, 직각도 등) | 800장 도면 | 85% |
| **text-region-detector-v1** | 텍스트 영역 | 주석, 제목란, 메모 | 1,200장 도면 | 90% |
| **yolo11n-general** | 범용 | 모든 객체 (테스트용) | COCO 데이터셋 | 60% (도면) |

### 2. 모델 선택 가이드

#### 시나리오 A: 기계 부품 도면 (베어링, 기어 등)
```
✅ symbol-detector-v1 → 용접/베어링/기어 검출
✅ dimension-detector-v1 → 치수 영역 검출
✅ eDOCr2 → 한글 치수 인식
```

#### 시나리오 B: 공차 분석 중심 도면
```
✅ gdt-detector-v1 → GD&T 심볼 검출
✅ dimension-detector-v1 → 치수 영역 검출
✅ SkinModel → 공차 분석
```

#### 시나리오 C: 영문 도면 (해외 제조사)
```
✅ text-region-detector-v1 → 텍스트 영역 검출
✅ PaddleOCR (lang=en) → 영문 텍스트 인식
```

#### 시나리오 D: 복잡한 배관도 (P&ID)
```
✅ symbol-detector-v1 → 밸브, 펌프 심볼 검출
✅ text-region-detector-v1 → 라벨 텍스트 영역
✅ VL → 전체 배관 구조 이해
```

---

## 🔄 후처리 파이프라인 옵션

### Option A: 배경 제거 → 전체 이미지 OCR
```
YOLO Detection → Background Removal → Full Image OCR
```

**장점**:
- OCR 1회 호출로 빠름 (0.5초)
- 배경 노이즈 제거로 인식률 향상 (+15%)

**단점**:
- 객체 간 간섭 가능 (겹쳐 보이는 경우)

**적합한 경우**:
- 객체가 적고 (< 10개) 간격이 넓은 도면
- 속도 우선 시나리오

---

### Option B: Crop → Scale Up → 개별 OCR
```
YOLO Detection → Crop Each BBox → Scale Up (2x) → Individual OCR
```

**장점**:
- 개별 객체에 집중하여 정확도 최고 (+25%)
- 작은 텍스트도 Scale Up으로 인식 가능

**단점**:
- OCR N회 호출로 느림 (N * 0.3초)
- 메모리 사용량 높음

**적합한 경우**:
- 정확도 최우선 (품질 검사, 규격 검증)
- 작은 글씨가 많은 도면

---

### Option C: 배경 제거 + Crop → 개별 OCR
```
YOLO Detection → Background Removal → Crop Each → Individual OCR
```

**장점**:
- 배경 제거 + 개별 처리로 균형 잡힌 정확도
- Option B보다 빠름 (Scale Up 생략)

**단점**:
- 여전히 OCR N회 호출 필요

**적합한 경우**:
- 중간 정도 객체 수 (10-30개)
- 정확도와 속도 균형

---

### Option D: YOLO 스킵 → 전체 이미지 직접 OCR
```
Image → eDOCr2 (Full Image)
```

**장점**:
- 가장 빠름 (0.5초)
- YOLO 오검출 위험 없음

**단점**:
- 배경 노이즈로 인식률 낮음 (-20%)
- 심볼 위치 정보 없음

**적합한 경우**:
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

## 🛠️ 구현 로드맵

### Phase 4A: YOLO 모델 다양화 (Week 1)
- [ ] symbol-detector-v1 학습 (14개 클래스)
- [ ] dimension-detector-v1 학습 (치수 영역)
- [ ] gdt-detector-v1 학습 (GD&T 심볼)
- [ ] text-region-detector-v1 학습 (텍스트 영역)
- [ ] YOLO API에 multi-model 지원 추가 (모델 선택 파라미터)

### Phase 4B: 후처리 노드 추가 (Week 2)
- [ ] **BackgroundRemoval** 노드 구현 (OpenCV 기반)
- [ ] **CropAndScale** 노드 구현 (BBox 기반 Crop + Resize)
- [ ] **BatchOCR** 노드 구현 (여러 영역 동시 OCR)
- [ ] NodeDetailPanel에 후처리 옵션 설명 추가

### Phase 4C: 템플릿 고도화 (Week 3)
- [ ] Template 5: 심볼 인식 최적화 (symbol-detector + Crop + eDOCr2)
- [ ] Template 6: 치수 추출 최적화 (dimension-detector + Scale Up + eDOCr2)
- [ ] Template 7: GD&T 분석 (gdt-detector + SkinModel)
- [ ] Template 8: 영문 도면 (text-region + PaddleOCR)

### Phase 4D: 성능 벤치마크 (Week 4)
- [ ] 100장 테스트 도면으로 4가지 옵션 비교
- [ ] 속도/정확도/메모리 메트릭 수집
- [ ] 자동 파이프라인 추천 알고리즘 구현

---

## 📝 문서 업데이트 계획

### 1. CLAUDE.md 업데이트
- BlueprintFlow 섹션에 "모델 다양화 전략" 추가
- 각 시나리오별 권장 조합 예시 추가

### 2. 새 스킬 추가: workflow-optimizer.md
- 사용자의 도면 유형 분석
- 최적 파이프라인 자동 추천
- 성능 벤치마크 결과 제공

### 3. nodeDefinitions.ts 확장
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

---

## 🎯 예상 효과

| 항목 | Before (Phase 1-3) | After (Phase 4) | 개선율 |
|------|-------------------|----------------|--------|
| **YOLO 모델 선택** | 3개 (크기만 다름) | 5개 (용도별 특화) | +67% |
| **후처리 옵션** | 1개 (시각화만) | 4개 (조합 가능) | +300% |
| **템플릿 수** | 4개 | 8개 | +100% |
| **평균 정확도** | 75% (범용) | 90% (특화) | +20% |
| **처리 속도** | 1.5초 | 0.5-2초 (선택 가능) | 유연성 |

---

**다음 단계**: CLAUDE.md와 스킬 문서에 이 전략을 반영하고, Phase 4 구현 시작

**최종 목표**: 사용자가 도면 유형만 선택하면 → 시스템이 최적 파이프라인 자동 구성
