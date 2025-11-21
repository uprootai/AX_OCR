---
name: workflow-optimizer
description: Analyzes drawing types and recommends optimal BlueprintFlow pipeline combinations based on content, accuracy requirements, and performance needs
allowed-tools: [read, grep, glob, bash]
---

# Workflow Optimizer Skill

**목적**: 도면 유형 분석 및 최적 BlueprintFlow 파이프라인 자동 추천

---

## 🎯 스킬 개요

이 스킬은 다음을 수행합니다:
1. 사용자 도면의 특성 분석 (심볼 종류, 텍스트 밀도, 복잡도)
2. 요구사항 파악 (속도 vs 정확도, 특정 정보 추출 목표)
3. 최적 YOLO 모델 + 후처리 조합 추천
4. 예상 성능 메트릭 제공 (처리 시간, 정확도)

---

## 📋 분석 워크플로우

### Step 1: 도면 유형 분석

사용자에게 질문:
```
1. 도면 종류가 무엇인가요?
   - [ ] 기계 부품 도면 (베어링, 기어, 샤프트 등)
   - [ ] 용접 도면 (용접 기호 포함)
   - [ ] 공차 분석 도면 (GD&T 기호 포함)
   - [ ] 배관도 (P&ID)
   - [ ] 텍스트 위주 단순 도면
   - [ ] 영문 도면 (해외 제조사)

2. 추출하려는 정보는?
   - [ ] 심볼 위치 및 종류
   - [ ] 치수 및 공차 값
   - [ ] GD&T 기하공차
   - [ ] 텍스트 주석/메모
   - [ ] 전체 도면 이해 (구조, 설명)

3. 우선순위는?
   - [ ] 속도 (빠른 결과, 80% 정확도)
   - [ ] 정확도 (느려도 95%+ 정확도)
   - [ ] 균형 (중간 속도, 90% 정확도)
```

### Step 2: 파이프라인 추천

#### 시나리오 A: 기계 부품 도면 (베어링, 기어)

**추천 파이프라인**:
```
1. symbol-detector-v1 (YOLO) → 베어링/기어 검출
2. CropAndScale (후처리) → 각 심볼을 2배 확대
3. eDOCr2 (OCR) → 심볼별 치수 인식
4. dimension-detector-v1 (YOLO) → 추가 치수 영역 검출
5. Merge → 모든 결과 통합
```

**예상 성능**:
- 처리 시간: 2.5초 (심볼 10개 기준)
- 정확도: 92% (심볼), 88% (치수)
- 메모리: 중간 (1.2GB GPU)

**적합한 이유**:
- symbol-detector-v1은 베어링/기어에 특화 (F1: 92%)
- CropAndScale로 작은 텍스트도 정확히 인식
- eDOCr2는 한글 치수에 강점

---

#### 시나리오 B: 용접 도면

**추천 파이프라인**:
```
1. symbol-detector-v1 (YOLO) → 7가지 용접 기호 검출
2. BackgroundRemoval (후처리) → 배경 제거
3. eDOCr2 (OCR) → 전체 이미지 OCR
4. IF 조건 분기 → confidence < 0.8이면
   → PaddleOCR (대안) → 영문 텍스트 추가 인식
5. Merge → 모든 OCR 결과 통합
```

**예상 성능**:
- 처리 시간: 1.2초
- 정확도: 90% (용접 기호), 85% (텍스트)
- 메모리: 낮음 (0.8GB GPU)

**적합한 이유**:
- 용접 기호 검출률 높음 (F1: 94%)
- BackgroundRemoval로 OCR 1회만 호출 (빠름)
- IF 분기로 실패 케이스 보완

---

#### 시나리오 C: 공차 분석 도면 (GD&T)

**추천 파이프라인**:
```
1. gdt-detector-v1 (YOLO) → GD&T 심볼 검출
2. dimension-detector-v1 (YOLO) → 치수 영역 검출
3. Loop → 각 검출 영역마다
   → CropAndScale → 2배 확대
   → eDOCr2 → 텍스트 인식
4. SkinModel → 공차 계산 및 제조 가능성 분석
5. Merge → 최종 보고서 생성
```

**예상 성능**:
- 처리 시간: 3.5초 (GD&T 20개 기준)
- 정확도: 85% (GD&T), 90% (공차 계산)
- 메모리: 높음 (1.5GB GPU)

**적합한 이유**:
- gdt-detector-v1은 기하공차 전용 (F1: 85%)
- Loop로 각 심볼 정밀 처리
- SkinModel이 공차 분석 특화

---

#### 시나리오 D: 텍스트 위주 단순 도면

**추천 파이프라인**:
```
1. Skip YOLO → 직접 OCR
2. EDGNet (전처리) → 흐릿한 이미지 선명하게
3. eDOCr2 (OCR) → 전체 이미지 텍스트 인식
```

**예상 성능**:
- 처리 시간: 0.8초
- 정확도: 80%
- 메모리: 낮음 (0.5GB GPU)

**적합한 이유**:
- YOLO 불필요 (심볼 없음)
- 가장 빠른 파이프라인
- EDGNet으로 인식률 향상

---

#### 시나리오 E: 영문 도면 (해외 제조사)

**추천 파이프라인**:
```
1. text-region-detector-v1 (YOLO) → 텍스트 영역 검출
2. CropAndScale → 각 텍스트 영역 확대
3. PaddleOCR (lang=en) → 영문 인식
4. VL (Vision Language Model) → 도면 전체 구조 이해
5. Merge → 텍스트 + 설명 통합
```

**예상 성능**:
- 처리 시간: 4.0초 (VL 포함)
- 정확도: 90% (영문), 85% (구조 이해)
- 메모리: 매우 높음 (2.5GB GPU, VL 사용)

**적합한 이유**:
- PaddleOCR이 영문에 강점
- VL이 복잡한 구조 설명 가능
- text-region-detector로 주석/제목란 정확히 검출

---

## 📊 비교표: 5가지 시나리오

| 시나리오 | YOLO 모델 | 후처리 | OCR | 속도 | 정확도 | 추천 상황 |
|---------|----------|--------|-----|------|--------|----------|
| **A. 기계 부품** | symbol + dimension | CropAndScale | eDOCr2 | ⚡⚡ (2.5초) | 92% | 베어링, 기어, 샤프트 |
| **B. 용접 도면** | symbol | BackgroundRemoval | eDOCr2 + PaddleOCR | ⚡⚡⚡ (1.2초) | 90% | 용접 기호 7가지 |
| **C. GD&T 공차** | gdt + dimension | Loop + CropAndScale | eDOCr2 → SkinModel | ⚡ (3.5초) | 85% | 기하공차 분석 |
| **D. 텍스트 단순** | Skip YOLO | EDGNet | eDOCr2 | ⚡⚡⚡⚡ (0.8초) | 80% | 주석/메모만 |
| **E. 영문 도면** | text-region | CropAndScale | PaddleOCR + VL | ⚡ (4.0초) | 90% | 해외 제조사 |

---

## 🛠️ 사용 방법

### 자동 모드 (추천)

```bash
# Claude Code에서
/skill workflow-optimizer

# 1. 도면 이미지 경로 제공
Drawing path: /path/to/drawing.jpg

# 2. 질문에 답변
Drawing type: 기계 부품 도면
Priority: 정확도

# 3. 추천 파이프라인 확인
Recommended: Scenario A (symbol-detector + CropAndScale + eDOCr2)

# 4. BlueprintFlow에서 템플릿 자동 생성
→ Template 5 생성: "기계 부품 최적화"
```

### 수동 모드 (고급 사용자)

```bash
# 성능 벤치마크 실행
python scripts/benchmark_pipelines.py \
  --scenarios A,B,C,D,E \
  --test-images /path/to/test/*.jpg \
  --output benchmark_report.json

# 결과 분석
cat benchmark_report.json | jq '.performance'
```

---

## 📈 성능 메트릭 계산

### 처리 시간 추정 공식

```python
def estimate_time(pipeline):
    time = 0

    # YOLO inference
    if 'YOLO' in pipeline:
        time += 0.3  # YOLO 모델 추론 (GPU)

    # 후처리
    if 'CropAndScale' in pipeline:
        time += num_detections * 0.1  # Crop + Resize
    if 'BackgroundRemoval' in pipeline:
        time += 0.2  # OpenCV 처리

    # OCR
    if 'Individual OCR' in pipeline:
        time += num_detections * 0.3  # 개별 OCR
    elif 'Full OCR' in pipeline:
        time += 0.5  # 전체 이미지 OCR

    # VL
    if 'VL' in pipeline:
        time += 2.0  # Vision Language Model (느림)

    return time
```

### 정확도 추정

```python
def estimate_accuracy(pipeline, drawing_type):
    # 기본 정확도 (모델별)
    accuracy = {
        'symbol-detector-v1': 0.92,
        'dimension-detector-v1': 0.88,
        'gdt-detector-v1': 0.85,
        'text-region-detector-v1': 0.90
    }

    # 후처리 보너스
    if 'CropAndScale' in pipeline:
        accuracy *= 1.05  # +5%
    if 'BackgroundRemoval' in pipeline:
        accuracy *= 1.03  # +3%

    # 도면 유형 페널티
    if drawing_type == 'complex' and 'YOLO' not in pipeline:
        accuracy *= 0.85  # -15% (복잡한 도면은 YOLO 필요)

    return min(accuracy, 0.98)  # 최대 98%
```

---

## 🎯 실행 예시

### 예시 1: 사용자가 베어링 도면 업로드

**입력**:
```
도면 종류: 기계 부품 (베어링 10개)
우선순위: 정확도
```

**분석 결과**:
```
✅ 추천 파이프라인: Scenario A

[symbol-detector-v1] → [CropAndScale 2x] → [eDOCr2] → [Merge]

예상 성능:
- 처리 시간: 2.8초 (베어링 10개)
- 정확도: 92% (심볼 검출)
- 메모리: 1.2GB GPU

BlueprintFlow Template 생성:
→ Template 5: "기계 부품 최적화" 자동 생성됨
→ http://localhost:5173/blueprintflow/builder 에서 확인
```

### 예시 2: 용접 도면 (속도 우선)

**입력**:
```
도면 종류: 용접 도면 (용접 기호 5개)
우선순위: 속도
```

**분석 결과**:
```
✅ 추천 파이프라인: Scenario B

[symbol-detector-v1] → [BackgroundRemoval] → [eDOCr2]

예상 성능:
- 처리 시간: 1.1초 ⚡⚡⚡
- 정확도: 90%
- 메모리: 0.8GB GPU

최적화 팁:
- confidence_threshold를 0.7로 낮추면 더 많은 용접 기호 검출
- BackgroundRemoval 덕분에 OCR 1회만 호출 (빠름)
```

---

## 🔍 트러블슈팅

### 문제 1: 추천 파이프라인 정확도가 낮음

**원인**: 도면 유형 오판 또는 학습 데이터 부족

**해결**:
1. 도면 샘플 3장 업로드하여 재분석
2. 수동으로 다른 시나리오 시도
3. 벤치마크 실행하여 실제 성능 측정

### 문제 2: 처리 시간이 예상보다 느림

**원인**: GPU 메모리 부족 또는 이미지 해상도 과다

**해결**:
1. 이미지를 1280px로 리사이즈
2. 배치 크기 줄이기 (imgsz=640)
3. 더 가벼운 모델 선택 (yolo11n)

### 문제 3: 특정 심볼 놓침

**원인**: YOLO 모델이 해당 클래스 미학습

**해결**:
1. confidence_threshold 낮추기 (0.5 → 0.3)
2. 추가 학습 데이터 수집 후 재학습
3. VL 모델로 보완 (전체 이미지 이해)

---

## 📝 다음 단계

1. **/skill workflow-optimizer** 실행
2. 도면 유형 답변
3. 추천 파이프라인 확인
4. BlueprintFlow에서 템플릿 적용
5. 실제 도면으로 테스트
6. 성능 만족 시 → 프로덕션 배포

---

**최종 목표**: 사용자가 도면만 올리면 → 시스템이 최적 파이프라인 자동 구성 → 최고 정확도/속도 달성
