# YOLO Confidence Threshold 실험 결과

> **실험일**: 2026-01-20
> **상태**: ✅ 1차 완료
> **결론**: SAHI 캐시 문제로 인해 threshold 변경이 적용되지 않음. 별도 실험 필요.

---

## 1. 실험 개요

### 1.1 목적
BWMS P&ID 도면에서 YOLO 검출 시 confidence threshold 변경에 따른 검출 결과 비교.

### 1.2 실험 설정
```yaml
이미지: bwms_pid_sample.png (423KB)
모델: pid_class_aware
파라미터:
  iou: 0.45
  imgsz: 640
  use_sahi: true
테스트 설정:
  - Baseline: confidence=0.25 (현재 설정)
  - Test_A: confidence=0.35 (권장 설정)
  - Test_B: confidence=0.45 (보수적 설정)
  - Test_C: confidence=0.50 (고신뢰도 전용)
```

---

## 2. 실험 결과

### 2.1 문제 발견: SAHI 캐시

**모든 테스트에서 동일한 결과 출력:**

| Config | Conf | Total | Avg% | Min% | <50% | <70% |
|--------|------|-------|------|------|------|------|
| Baseline | 0.25 | 83 | 51.7 | 10.3 | 42 | 52 |
| Test_A | 0.35 | 83 | 51.7 | 10.3 | 42 | 52 |
| Test_B | 0.45 | 83 | 51.7 | 10.3 | 42 | 52 |
| Test_C | 0.50 | 83 | 51.7 | 10.3 | 42 | 52 |

**원인 분석:**
```python
# sahi_inference.py:45-58
if model_path not in _sahi_model_cache:
    sahi_model = AutoDetectionModel.from_pretrained(
        model_type="yolov8",
        model_path=model_path,
        confidence_threshold=confidence,  # 최초 로드 시 설정
        device="cuda:0"
    )
    _sahi_model_cache[model_path] = sahi_model
else:
    sahi_model = _sahi_model_cache[model_path]
    sahi_model.confidence_threshold = confidence  # 속성만 업데이트 (내부 모델 미반영)
```

**문제점:**
- SAHI 모델이 한번 캐시되면 내부 YOLO 모델의 confidence가 고정됨
- `sahi_model.confidence_threshold` 속성 변경이 실제 추론에 반영되지 않음
- 결과적으로 첫 번째 호출의 confidence 값이 이후 모든 호출에 적용됨

---

## 3. 현재 검출 결과 분석

### 3.1 전체 통계 (confidence=0.25 기준)

```
총 검출: 83개
평균 신뢰도: 51.7%
최소 신뢰도: 10.3%
최대 신뢰도: 97.2%
```

### 3.2 신뢰도 분포

| 범위 | 수량 | 비율 |
|------|------|------|
| 90-100% | 18 | 21.7% |
| 80-90% | 5 | 6.0% |
| 70-80% | 8 | 9.6% |
| 50-70% | 10 | 12.0% |
| 30-50% | 10 | 12.0% |
| <30% | 32 | 38.6% |

**⚠️ 문제:** 38.6%의 검출이 30% 미만의 저신뢰도

### 3.3 클래스별 분석 (상위 10개)

| 클래스 | 수량 | 평균 신뢰도 | 최소 신뢰도 | 상태 |
|--------|------|-------------|-------------|------|
| Control Valve | 12 | 64.8% | 19.4% | ❌ 저신뢰 혼재 |
| DB&BBV | 10 | 42.5% | 11.7% | ❌ 과반 저신뢰 |
| Sensor | 9 | 64.1% | 11.5% | ❌ 저신뢰 혼재 |
| ESDV Valve Ball | 9 | 75.0% | 10.7% | ❌ 저신뢰 혼재 |
| Barred Tee | 7 | 28.8% | 11.2% | ❌ 전체 저신뢰 |
| Control Valve Angle Choke | 6 | 56.8% | 16.2% | ❌ 저신뢰 혼재 |
| Rupture Disc | 4 | 40.6% | 11.3% | ❌ 저신뢰 |
| Control | 4 | 25.2% | 18.3% | ❌ 전체 저신뢰 |
| Control Valve Globe | 2 | 92.0% | 89.5% | ✅ 양호 |
| Line Blindspacer | 2 | 54.4% | 16.8% | ❌ 저신뢰 혼재 |

**핵심 문제점:**
1. Barred Tee: 평균 28.8% - 모델이 이 클래스를 잘 인식하지 못함
2. Control: 평균 25.2% - 전반적으로 낮은 신뢰도
3. DB&BBV: 평균 42.5% - 절반 이상이 저신뢰

---

## 4. 권장 조치

### 4.1 즉시 적용 (코드 수정 불필요)

**현재 분석에서 확인된 사항:**
- confidence=0.25 설정 시 83개 검출
- 이 중 42개(50.6%)가 50% 미만 신뢰도
- 32개(38.6%)가 30% 미만 신뢰도

**클라이언트 측 필터링 권장:**
```javascript
// BlueprintFlow 또는 프론트엔드에서 후처리
const filteredDetections = detections.filter(d => d.confidence >= 0.35);
// 예상: 83개 → ~50개 (신뢰도 35% 미만 제거)
```

### 4.2 SAHI 캐시 문제 해결 (코드 수정 필요)

**Option A: 캐시 비활성화**
```python
# sahi_inference.py 수정
# _sahi_model_cache 사용 제거
sahi_model = AutoDetectionModel.from_pretrained(
    model_type="yolov8",
    model_path=model_path,
    confidence_threshold=confidence,
    device="cuda:0"
)
```

**Option B: confidence 포함 캐시 키**
```python
cache_key = f"{model_path}_{confidence}"
if cache_key not in _sahi_model_cache:
    # 새 모델 로드
```

**Option C: SAHI 캐시 명시적 클리어**
```python
# 호출 전 캐시 클리어
clear_sahi_cache()
result = run_sahi_inference(...)
```

### 4.3 모델 재학습 (장기)

저신뢰도 클래스에 대한 추가 학습 필요:
- Barred Tee
- Control
- DB&BBV

---

## 5. 다음 실험

### 5.1 SAHI 캐시 없이 실험

```bash
# Docker 재시작으로 캐시 클리어 후 테스트
docker restart yolo-api
python test_confidence_threshold.py
```

### 5.2 클라이언트 측 필터링 효과 측정

confidence threshold별 검출 수 시뮬레이션:
- 0.25: 83개 (현재)
- 0.35: ~51개 (추정, 32개 <30% 제거)
- 0.50: ~41개 (추정, 42개 <50% 제거)
- 0.70: ~31개 (추정, 52개 <70% 제거)

---

## 6. 실험 파일

- `test_confidence_threshold.py`: 실험 스크립트
- `../results/yolo_confidence_test_*.json`: 결과 파일
- `ANALYSIS.md`: 문제 분석 문서

---

## 7. 결론

### 7.1 주요 발견

1. **SAHI 캐시 문제**: confidence threshold 변경이 런타임에 적용되지 않음
2. **저신뢰도 검출 과다**: 50.6%가 50% 미만 신뢰도
3. **특정 클래스 문제**: Barred Tee, Control 등 모델 성능 저하

### 7.2 권장 설정

```yaml
# 현재 상태에서 권장
confidence: 0.35  # API 측 (SAHI 캐시 수정 후)
client_filter: 0.50  # 클라이언트 측 후처리
```

### 7.3 예상 효과

- 노이즈 검출 40-50% 감소
- 실제 심볼 검출 유지 (고신뢰도 검출은 보존)
- Design Checker 입력 품질 향상

---

*작성자*: Claude Code (Opus 4.5)
*실험일*: 2026-01-20
