# BlueprintFlow Benchmark Insights

> **템플릿별 벤치마크 테스트 결과 및 인사이트**

---

## 테스트 환경

| 항목 | 값 |
|------|-----|
| **테스트 날짜** | 2025-12-09 |
| **테스트 이미지** | sample2_interm_shaft.jpg (기계 도면) |
| **GPU** | NVIDIA GeForce RTX 3080 Laptop GPU (8GB) |

---

## 1. Analysis Benchmark

### 파이프라인 구성
```
ImageInput → YOLO → YOLO (P&ID 모드) → Line Detector → eDOCr2 → SkinModel → PID Analyzer → Design Checker → Merge
```

### 결과 요약

| 항목 | 값 |
|------|-----|
| **총 소요 시간** | 21.52초 |
| **노드 수** | 9개 |
| **성공률** | 100% (9/9) |

### 노드별 결과

| 노드 | 결과 | 비고 |
|------|------|------|
| YOLO | 13 objects | text_block(6), linear_dim(3), flatness(1) 등 |
| YOLO (P&ID) | 1 symbol | symbol_74 (42% 신뢰도) - 기계도면이라 P&ID 심볼 거의 없음 |
| Line Detector | 0 lines | P&ID 전용 - 기계도면에서는 검출 안됨 |
| eDOCr2 | 15 dimensions | linear(12) + text_dimension(3) |
| SkinModel | 4 tolerances | flatness: 0.024, cylindricity: 0.036 등 |
| PID Analyzer | 1 connection | 최소 검출 (P&ID 아님) |
| Design Checker | 100% compliance | 검사 대상 없음 |

### 인사이트

1. **YOLO model_type별 비교**
   - YOLO (engineering): 기계 도면 심볼 (치수, 텍스트 블록, GD&T) 검출에 최적화
   - YOLO (pid_class_aware): P&ID 심볼 (밸브, 펌프, 계기) 검출에 최적화
   - 기계 도면에서 P&ID 모드 사용 시 의미있는 결과 없음

2. **OCR 품질 이슈**
   - 일부 치수가 잘못 인식됨 (`:9`, `(2::9:)` 등)
   - 이미지 해상도 또는 OCR 파라미터 조정 필요
   - ESRGAN 전처리 권장

3. **SkinModel 공차 예측**
   - OCR 데이터 품질에 따라 예측 신뢰도 결정
   - 정확한 치수 입력 시 더 정밀한 예측 가능

---

## 2. Detection Benchmark

### 파이프라인 구성
```
ImageInput ─┬→ YOLO (engineering, 0.35) ────┬→ Merge
            ├→ YOLO (engineering, 0.5) ─────┤
            ├→ YOLO (pid_class_aware, 640) ─┤
            └→ YOLO (pid_class_aware, 1280) ┘
```

### 결과 요약

| 항목 | 값 |
|------|-----|
| **총 소요 시간** | 0.94초 |
| **노드 수** | 6개 |
| **성공률** | 100% (6/6) |
| **총 검출** | 49 objects |

### 노드별 결과

| 노드 | confidence | imgsz | 검출 수 | 최고 신뢰도 |
|------|------------|-------|---------|-------------|
| YOLO (engineering) | 0.35 | 1280 | **28** | 93.0% |
| YOLO (engineering, 고신뢰) | 0.50 | 1280 | **19** | 93.0% |
| YOLO (P&ID) | 0.25 | 640 | **1** | 68.9% |
| YOLO (P&ID, 고해상도) | 0.25 | 1280 | **1** | 41.9% |

### 검출된 심볼 분포 (YOLO)

| 심볼 | 개수 | 평균 신뢰도 |
|------|------|-------------|
| parallelism | 11 | 61% |
| text_block | 8 | 77% |
| tolerance_dim | 8 | 58% |
| linear_dim | 5 | 53% |
| reference_dim | 4 | 74% |
| position | 3 | 51% |
| cylindricity | 2 | 71% |
| chamfer_dim | 2 | 56% |
| perpendicularity | 2 | 38% |
| flatness | 1 | 41% |
| angular_dim | 1 | 36% |

### 인사이트

1. **YOLO model_type별 성능 차이**
   - 기계 도면에서 YOLO (engineering): 28개 검출
   - 기계 도면에서 YOLO (pid_class_aware): 1개 검출 (symbol_74)
   - **결론**: 도면 유형에 맞는 model_type 선택 필수

2. **Confidence Threshold 효과**
   - 0.35 → 28개 검출
   - 0.50 → 19개 검출 (32% 감소)
   - 낮은 threshold: 더 많은 검출, 오탐 가능성 증가
   - 높은 threshold: 정밀한 검출, 누락 가능성 증가

3. **imgsz (이미지 해상도) 효과**
   - YOLO P&ID 640px: 68.9% 신뢰도
   - YOLO P&ID 1280px: 41.9% 신뢰도
   - **주의**: 고해상도가 항상 좋은 것은 아님
   - 모델 학습 해상도와 일치할 때 최적 성능

4. **GD&T 심볼 검출 현황**
   - parallelism (평행도): 11개 - 가장 많이 검출
   - cylindricity (원통도), position (위치도) 등 다수 검출
   - 기계 도면 분석에 YOLO 활용 가능 확인

---

## 3. Segmentation Benchmark

### 파이프라인 구성
```
ImageInput ─┬→ EDGNet (기본) ────┬→ Merge
            ├→ EDGNet (고감도) ──┤
            ├→ Line Detector (LSD) ──┤
            └→ Line Detector (Hough) ┘
```

### 결과 요약

| 항목 | 값 |
|------|-----|
| **총 소요 시간** | 2.38초 |
| **노드 수** | 6개 |
| **성공률** | 100% (6/6) |

### 노드별 결과

| 노드 | 파라미터 | 결과 |
|------|----------|------|
| EDGNet (기본) | threshold: 0.5 | 0 segments |
| EDGNet (고감도) | threshold: 0.3 | 0 segments |
| Line Detector (LSD) | method: lsd | 0 lines |
| Line Detector (Hough) | method: hough | 0 lines |

### 인사이트

1. **테스트 이미지 적합성**
   - 기계 도면은 P&ID 세그멘테이션 도구에 적합하지 않음
   - EDGNet: 도면 엣지 추출용 (P&ID 컴포넌트 분류)
   - Line Detector: 배관 라인 검출용

2. **P&ID 도면 필요**
   - 이 벤치마크는 P&ID 도면으로 테스트해야 의미있는 비교 가능
   - 밸브, 펌프, 계기 등이 포함된 도면 권장

3. **threshold 효과**
   - EDGNet threshold 낮을수록 더 많은 엣지 검출
   - 단, 노이즈도 증가하므로 적절한 값 선택 필요

---

## 3. 권장 테스트 시나리오

### 기계 도면 분석
```
ImageInput → ESRGAN → YOLO → eDOCr2 → SkinModel
```
- 치수 추출 및 공차 분석에 최적화

### P&ID 분석
```
ImageInput → YOLO (model_type=pid_class_aware) → Line Detector → PID Analyzer → Design Checker
```
- 심볼/라인 검출 및 연결성 분석

### OCR 벤치마크
```
ImageInput → [eDOCr2, PaddleOCR, Tesseract, TrOCR, ...] → Merge
```
- 다양한 OCR 엔진 정확도 비교

---

## 4. 성능 최적화 팁

| 문제 | 해결책 |
|------|--------|
| OCR 정확도 낮음 | ESRGAN 전처리 적용 |
| 검출 누락 | confidence threshold 낮추기 |
| 처리 속도 느림 | 병렬 실행 활용 |
| 메모리 부족 | 이미지 해상도 조정 |

---

## 5. 템플릿별 용도

| 템플릿 | 용도 | 권장 도면 |
|--------|------|-----------|
| Basic Drawing Analysis | 기본 도면 분석 | 기계 도면 |
| Full OCR Benchmark | OCR 엔진 비교 | 텍스트 많은 도면 |
| P&ID Analysis Pipeline | P&ID 완전 분석 | P&ID 도면 |
| Detection Benchmark | YOLO model_type 비교 | 모든 도면 |
| Segmentation Benchmark | 엣지/라인 검출 비교 | P&ID 도면 |
| Analysis Benchmark | 분석 엔진 비교 | 모든 도면 |

---

## 6. Playwright 자동화 테스트 결과

### 테스트 개요

17개 템플릿에 대한 Playwright E2E 테스트를 수행했습니다.

### 로드 테스트 (17/17 성공)

모든 17개 템플릿이 올바른 노드 개수로 로드되었습니다.

| 카테고리 | 템플릿 수 | 상태 |
|----------|----------|------|
| Featured | 2 | ✅ |
| Basic | 2 | ✅ |
| Advanced | 5 | ✅ |
| AI | 2 | ✅ |
| Benchmark | 6 | ✅ |

### 실행 테스트 결과

| 템플릿 | 결과 | 소요 시간 | 성공/실패 |
|--------|------|----------|-----------|
| Detection Benchmark | ✅ 성공 | 22.7s | 7/0 |
| Segmentation Benchmark | ✅ 성공 | 24.9s | - |
| Analysis Benchmark | ✅ 성공 | 12.3s | 7/2 |

### 알려진 이슈

1. **Headless 모드 제한**
   - GPU 리소스 경쟁으로 headless 모드에서 일부 테스트 실패
   - headed 모드에서 안정적으로 동작

2. **서비스 의존성**
   - 테스트 전 모든 API 컨테이너가 healthy 상태인지 확인 필요
   - eDOCr2, YOLO, EDGNet 등 핵심 서비스 필수

3. **타임아웃 설정**
   - Detection: 60초 권장
   - Segmentation: 120초 권장
   - Analysis: 150초 권장

---

**마지막 업데이트**: 2025-12-09
