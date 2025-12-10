# P&ID 분석 파이프라인 성능 분석 및 최적화 가이드

> **작성일**: 2025-12-10
> **분석 대상**: P&ID Analysis Pipeline 템플릿 실행 결과
> **총 실행 시간**: 483초 (약 8분)

---

## 1. 현재 모델 및 파라미터 분석

### 1.1 YOLO-PID (심볼 검출)

| 항목 | 값 | 비고 |
|------|-----|------|
| **모델** | YOLOv8 + SAHI | Slicing Aided Hyper Inference |
| **모델 파일** | `pid_symbol_detector.pt` (6.3MB) | 32-class 모델 |
| **학습 데이터** | P&ID 도면 (클래스 32종) | 밸브, 펌프, 열교환기 등 |
| **추론 방식** | SAHI 슬라이싱 | 대형 이미지를 512x512로 분할 |
| **기본 신뢰도** | 0.10 (매우 낮음) | ⚠️ 과다 검출 원인 |
| **템플릿 신뢰도** | 0.25 | 적정 수준 |

**32개 클래스 목록:**
```
밸브류: Ball valve, Check valve, Control valve, Gate Valve, Globe Valve, Hand Valve, Valve
펌프류: Centrifugal pump, Pump, Reciprocating pump
압축기: Centrifugal compressor, Compressor, Reciprocating compressor
열교환기: Air-cooled Exchanger, Condenser, Exchanger, Reboiler
탱크류: Column, Decanter, Separator
계측기: In-line Instrument, Regulator, Round Instrument
배관: Blind End, Flange, Off-sheet, Reducer
기타: Agitator, Fan, Motor
```

### 1.2 Line Detector (라인 검출)

| 항목 | 값 | 비고 |
|------|-----|------|
| **모델** | OpenCV LSD | Line Segment Detector (비ML) |
| **알고리즘** | `cv2.createLineSegmentDetector()` | CPU 전용 |
| **학습 데이터** | 없음 | 알고리즘 기반 |
| **병합 기능** | `merge_collinear_lines()` | 활성화됨 |
| **최소 길이 필터** | ❌ 없음 | ⚠️ 과다 검출 원인 |

---

## 2. 검출 결과 분석

### 2.1 이번 실행 결과

| 노드 | 검출 수 | 소요 시간 | 문제점 |
|------|---------|----------|--------|
| **YOLO-PID** | 144개 심볼 | 15초 | 일부 중복 검출 |
| **Line Detector** | 1958개 라인 | 317초 (5분) | ⚠️ 과다 검출 |
| **PID Analyzer** | 141개 연결 | 150초 | 대용량 데이터 처리 |

### 2.2 과다 검출 원인 분석

```
원본: 3849개 라인 (LSD 검출)
  ↓ merge_lines=true
병합 후: 1958개 라인 (여전히 과다)
  ↓
이유:
1. 텍스트 획이 라인으로 인식됨
2. 도면 테두리/프레임이 라인으로 인식됨
3. 심볼 내부 선이 라인으로 인식됨
4. 짧은 라인 세그먼트가 필터링 안됨
```

---

## 3. 최적화 권장사항

### 3.1 YOLO-PID 파라미터 조정

| 파라미터 | 현재 | 권장 (빠름) | 권장 (정밀) |
|----------|------|-------------|-------------|
| `confidence` | 0.25 | 0.35 | 0.20 |
| `slice_height` | 512 | 768 | 256 |
| `slice_width` | 512 | 768 | 256 |
| `overlap_ratio` | 0.25 | 0.15 | 0.30 |

**예상 효과:**
- confidence 0.25 → 0.35: 검출 수 144 → ~80-100개, 속도 10% 향상
- slice 512 → 768: 속도 2배 향상, 작은 심볼 누락 가능

### 3.2 Line Detector 개선 필요 (코드 수정)

**현재 누락된 기능:**
```python
# 추가 필요한 파라미터
min_length: int = 30       # 최소 라인 길이 (픽셀)
max_lines: int = 500       # 최대 라인 수 제한
exclude_borders: bool = True  # 도면 테두리 제외
```

**권장 구현:**
```python
# api_server.py 수정 필요
def filter_lines_by_length(lines, min_length=30):
    return [l for l in lines if l['length'] >= min_length]

# 도면 테두리 제외 (상하좌우 5% 영역)
def exclude_border_lines(lines, width, height, margin_ratio=0.05):
    margin_x = width * margin_ratio
    margin_y = height * margin_ratio
    return [l for l in lines
            if margin_x < l['start_point'][0] < width - margin_x
            and margin_y < l['start_point'][1] < height - margin_y]
```

### 3.3 최적화 효과 예상

| 최적화 | 현재 | 최적화 후 | 시간 절감 |
|--------|------|----------|----------|
| YOLO-PID (conf 0.35) | 144개/15초 | ~100개/12초 | 20% |
| Line Detector (min_len 30) | 1958개/317초 | ~500개/100초 | **68%** |
| PID Analyzer | 141개/150초 | ~100개/50초 | 66% |
| **총 시간** | **483초** | **~170초** | **65%** |

---

## 4. 빠른 테스트를 위한 파라미터 설정

### 4.1 "빠른 분석" 프리셋

```json
{
  "yolopid": {
    "confidence": 0.40,
    "slice_height": 768,
    "slice_width": 768,
    "overlap_ratio": 0.15
  },
  "linedetector": {
    "method": "lsd",
    "merge_lines": true,
    "min_length": 50,
    "max_lines": 300
  }
}
```

### 4.2 "정밀 분석" 프리셋

```json
{
  "yolopid": {
    "confidence": 0.15,
    "slice_height": 256,
    "slice_width": 256,
    "overlap_ratio": 0.30
  },
  "linedetector": {
    "method": "combined",
    "merge_lines": true,
    "min_length": 20,
    "max_lines": 2000
  }
}
```

---

## 5. 모델 학습 데이터 정보

### 5.1 YOLO-PID 모델

| 항목 | 정보 |
|------|------|
| **베이스 모델** | YOLOv8n (nano) |
| **학습 데이터셋** | P&ID 도면 이미지 (출처: 내부) |
| **클래스 수** | 32 (Stage 2 모델) |
| **학습 에폭** | 미확인 |
| **mAP** | 미확인 |

### 5.2 Line Detector

학습 데이터 없음 (OpenCV LSD 알고리즘 기반)

---

## 6. 향후 개선 방향

### 6.1 단기 (파라미터 조정)
- [ ] YOLO-PID 신뢰도 0.30-0.40으로 상향
- [ ] Line Detector에 `min_length` 파라미터 추가
- [ ] 템플릿에 "빠른 분석" / "정밀 분석" 옵션 추가

### 6.2 중기 (코드 개선)
- [ ] Line Detector 테두리 제외 기능 추가
- [ ] SAHI 슬라이스 캐싱으로 중복 처리 방지
- [ ] PID Analyzer 대용량 데이터 최적화

### 6.3 장기 (모델 개선)
- [ ] 더 많은 P&ID 데이터로 YOLO 모델 재학습
- [ ] 딥러닝 기반 Line Detector 개발 검토

---

## 7. 참고 자료

- SAHI 논문: [Slicing Aided Hyper Inference](https://arxiv.org/abs/2202.06934)
- YOLOv8 문서: https://docs.ultralytics.com/
- OpenCV LSD: https://docs.opencv.org/4.x/db/d73/classcv_1_1LineSegmentDetector.html

---

**작성자**: Claude Code (Opus 4.5)
