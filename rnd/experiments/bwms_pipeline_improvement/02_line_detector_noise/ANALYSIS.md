# Line Detector 노이즈 문제 분석

> **작성일**: 2026-01-20
> **상태**: 🔴 분석 중
> **우선순위**: P1 (High)

---

## 1. 문제 정의

BWMS P&ID 도면에서 Line Detector가 **과도한 수의 라인을 검출**하여 실제 배관 라인과 노이즈 구분이 어려움.

### 현재 설정
```yaml
method: combined  # LSD + Hough
classify_types: true
classify_colors: true
```

### 검출 결과
```
총 라인: 2,370개 (예상: 200-400개)
총 교차점: 3,183개 (예상: 100-300개)
노이즈 비율: ~80% (추정)
```

---

## 2. 라인 타입 분포 분석

### 2.1 타입별 분류 현황

| 타입 | 신뢰도 | 수량 (추정) | 문제점 |
|------|--------|-------------|--------|
| signal | 85% | ~1,800 | ⚠️ 과도함, 대부분 노이즈 |
| process | 90% | ~200 | ✅ 실제 배관 라인 |
| dotted (auxiliary) | 60% | ~150 | ⚠️ 보조선 구분 필요 |
| dashed (instrument) | 65% | ~120 | ⚠️ 계기 라인 |
| unknown | 40% | ~100 | ❌ 미분류, 제거 필요 |

### 2.2 노이즈 원인

1. **심볼 내부 라인**
   - 밸브, 센서 등 심볼 내부의 선이 검출됨
   - YOLO bbox 영역 내 라인 필터링 필요

2. **텍스트 외곽선**
   - 태그, 라벨의 텍스트 획이 라인으로 검출
   - OCR 영역 제외 필요

3. **짧은 노이즈 라인**
   - 10-30px 미만의 짧은 세그먼트
   - 최소 길이 필터링 필요

4. **이미지 아티팩트**
   - 스캔 노이즈, 압축 아티팩트
   - 전처리 개선 필요

---

## 3. 검출 라인 상세 분석

### 3.1 라인 길이 분포 (샘플 5개 기준)

```
Line 1: 410.19px, angle=-179.76°, signal (85%)
Line 2: 445.07px, angle=175.09°, signal (85%), dotted/auxiliary
Line 3: 123.12px, angle=44.35°, signal (85%)  ← 짧은 라인
Line 4: 128.05px, angle=-179.94°, signal (85%), dashed/instrument
Line 5: 30.89px, angle=148.68°, process (90%)  ← 매우 짧음
```

### 3.2 문제 패턴

| 패턴 | 예시 | 필터링 방법 |
|------|------|-------------|
| 짧은 라인 | < 50px | `min_line_length: 50` |
| 비정상 각도 | 44.35°, 148.68° | 주요 각도(0°, 90°, ±45°) 외 필터 |
| 저신뢰도 | < 60% | `min_confidence: 0.6` |
| unknown 타입 | 40% | 제거 |

---

## 4. 라인 분류 문제

### 4.1 현재 분류 로직

```python
# 색상 기반 분류
gray → signal (85%)
black → process (90%)
# 패턴 기반 분류
dotted → auxiliary (60%)
dashed → instrument (65%)
solid → process/signal
```

### 4.2 문제점

1. **색상 구분 한계**
   - 그레이스케일 도면에서 색상 구분 불가
   - 대부분 "gray" → "signal"로 분류됨

2. **패턴 인식 정확도**
   - 점선/파선 구분 정확도 60-65%
   - 해상도에 따라 패턴 인식 실패

3. **라인 타입 정의 부재**
   - P&ID 표준 라인 타입과 매핑 안됨
   - ISO 14617 라인 심볼 기준 필요

---

## 5. 실험 계획

### 실험 1: 최소 라인 길이 필터링

| 설정 | 값 | 예상 효과 |
|------|-----|----------|
| 현재 | 없음 | 2,370 라인 |
| 테스트 A | 30px | ~1,800 라인 |
| 테스트 B | 50px | ~1,200 라인 |
| 테스트 C | 80px | ~600 라인 |
| 테스트 D | 100px | ~400 라인 |

---

### 실험 2: 심볼 영역 제외

**방법**: YOLO bbox 내부 라인 제거

```python
for line in detected_lines:
    for symbol_bbox in yolo_detections:
        if line_inside_bbox(line, symbol_bbox):
            remove(line)
```

**예상 효과**: 30-40% 노이즈 제거

---

### 실험 3: 각도 기반 필터링

**P&ID 주요 라인 각도:**
- 수평: 0°, 180°
- 수직: 90°, -90°
- 대각: ±45° (드물게)

**필터링 기준:**
```python
valid_angles = [0, 90, 180, -90]
tolerance = 10  # ±10°
```

---

### 실험 4: 라인 병합 최적화

| 파라미터 | 현재 | 테스트 |
|----------|------|--------|
| merge_threshold | 10px | 15, 20, 30 |
| angle_threshold | 5° | 10°, 15° |

---

## 6. 권장 즉시 적용 설정

```yaml
# 현재 → 권장
method: combined
classify_types: true
classify_colors: true
# 추가 권장
min_line_length: 50      # 신규
merge_threshold: 15      # 10 → 15
filter_by_angle: true    # 신규
valid_angles: [0, 90, 180, -90]
angle_tolerance: 10
exclude_symbol_areas: true  # 신규 (YOLO bbox 활용)
```

**예상 효과:**
- 라인 수: 2,370 → ~500
- 노이즈 비율: 80% → 20%
- 처리 시간: 약간 증가

---

## 7. 장기 개선 방안

### 7.1 딥러닝 기반 라인 검출

- **Wireframe 검출 모델**: HAWP, LETR
- **장점**: 의미있는 라인만 검출
- **단점**: 학습 데이터 필요, GPU 사용량 증가

### 7.2 심볼-라인 관계 모델

- 연결점(Connection Point) 기반 라인 추적
- 심볼에서 시작/끝나는 라인만 유효로 판정

### 7.3 P&ID 표준 적용

- ISO 14617: 그래픽 심볼
- ISO 10628: P&ID 다이어그램 규칙
- 라인 타입별 표준 패턴 정의

---

## 8. 다음 단계

1. [ ] 실험 1 수행: min_line_length 테스트
2. [ ] 실험 2 수행: 심볼 영역 제외 테스트
3. [ ] Line Detector API 파라미터 추가 검토
4. [ ] 결과 비교 및 최적 설정 도출

---

## 관련 파일

- `EXPERIMENTS.md`: 실험 수행 결과
- `SOLUTION.md`: 최종 해결책
- `../01_yolo_confidence/`: YOLO bbox 활용
- `../../SOTA_GAP_ANALYSIS.md`: SOTA 라인 검출 방법

---

*작성자*: Claude Code (Opus 4.5)
