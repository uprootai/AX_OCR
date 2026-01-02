# PID2Graph 벤치마크 검토

> **작성일**: 2026-01-02
> **우선순위**: P1
> **상태**: 검토 완료

---

## 1. 논문 개요

- **제목**: Transforming Engineering Diagrams: P&ID Digitization with Transformers
- **arXiv**: [2411.13929](https://arxiv.org/abs/2411.13929)
- **날짜**: 2024-11
- **핵심 기여**:
  - **Relationformer**: P&ID 전용 Transformer 아키텍처
  - **PID2Graph**: 최초 공개 P&ID 그래프 데이터셋
  - 노드 검출 AP 83.63%, 엣지 mAP 75.46%

---

## 2. PID2Graph 데이터셋

### 2.1 구성

| 항목 | 값 |
|------|-----|
| 이미지 수 | 500+ P&ID 도면 |
| 어노테이션 | 심볼 바운딩박스 + 연결 그래프 |
| 포맷 | COCO + 커스텀 관계 JSON |
| 라이선스 | 학술 연구용 |

### 2.2 심볼 클래스

| 카테고리 | 클래스 수 | 예시 |
|----------|----------|------|
| Valve | 15+ | Ball, Gate, Check, Control |
| Pump | 5+ | Centrifugal, Reciprocating |
| Instrument | 10+ | FI, LI, PI, TI |
| Equipment | 10+ | Tank, Vessel, Exchanger |
| Connector | 5+ | Flange, Reducer |

### 2.3 관계 타입

| 관계 | 설명 |
|------|------|
| pipe_connection | 배관 연결 |
| signal_connection | 신호선 연결 |
| instrument_to_pipe | 계기-배관 연결 |
| equipment_port | 장비 포트 연결 |

---

## 3. 현재 시스템 비교

### 3.1 현재 AX POC 파이프라인

```
[이미지]
  → YOLO (심볼 검출)
  → Line Detector (라인 검출)
  → PID Analyzer (연결성 분석)
  → Design Checker (규칙 검증)
```

### 3.2 PID2Graph (Relationformer) 파이프라인

```
[이미지]
  → Relationformer (노드 + 엣지 동시 검출)
  → 그래프 구조 직접 출력
```

### 3.3 성능 비교 (예상)

| 지표 | AX POC (현재) | PID2Graph 기준 | 차이 |
|------|--------------|----------------|------|
| 심볼 검출 AP | ~70% | 83.63% | -13.63% |
| 연결성 검출 mAP | ~60% | 75.46% | -15.46% |
| 처리 시간 | 1-2초 | 0.5초 | +50% 느림 |
| GPU 요구량 | ~2GB | ~6GB | -4GB 적음 |

---

## 4. 벤치마크 수행 계획

### 4.1 현재 시스템 평가

**목표**: PID2Graph 데이터셋으로 현재 AX POC 성능 측정

```bash
# 1. PID2Graph 데이터셋 다운로드
# (arXiv 논문 또는 저자 GitHub 확인 필요)

# 2. 평가 스크립트 작성
python evaluate_ax_poc.py \
  --dataset pid2graph_test \
  --yolo_model pid_class_aware \
  --line_detector lsd \
  --output results/pid2graph_eval.json

# 3. 지표 계산
# - Symbol Detection AP (COCO mAP)
# - Edge Detection mAP (연결성)
# - End-to-End F1 Score
```

### 4.2 평가 지표

| 지표 | 수식 | 설명 |
|------|------|------|
| AP@50 | Precision-Recall AUC | IoU 0.5 기준 |
| AP@75 | Precision-Recall AUC | IoU 0.75 기준 |
| mAP | Mean over classes | 클래스 평균 |
| Edge mAP | 연결 정확도 | 노드쌍 연결 예측 |

### 4.3 예상 결과

| 컴포넌트 | AP@50 예상 | 개선 필요 |
|----------|-----------|-----------|
| 밸브 검출 | 75% | 유사 형태 구분 |
| 펌프 검출 | 80% | 양호 |
| 계기 검출 | 70% | 소형 심볼 개선 |
| 연결성 | 55% | ⚠️ Line Detector 개선 필요 |

---

## 5. 개선 방안

### 5.1 단기 개선 (현재 파이프라인 유지)

| 개선점 | 방법 | 효과 |
|--------|------|------|
| 심볼 검출 | SAHI 최적화 | +5-10% AP |
| 연결성 | Line Detector + Heuristic | +5-10% |
| 후처리 | 규칙 기반 보정 | +2-5% |

### 5.2 중기 개선 (아키텍처 변경)

| 개선점 | 방법 | 효과 |
|--------|------|------|
| RT-DETR 도입 | NMS 불필요, 관계 인식 | +10-15% |
| GNN 후처리 | 그래프 신경망 보정 | +5-10% |

### 5.3 장기 개선 (Relationformer 적용)

| 개선점 | 방법 | GPU 요구 |
|--------|------|----------|
| Relationformer | 노드+엣지 동시 검출 | 6-8GB |
| End-to-End | 단일 모델 | 8GB+ |

---

## 6. 리소스 요구사항

### Relationformer 적용 시

| 항목 | 요구 사양 |
|------|----------|
| GPU | RTX 3090 (24GB) 이상 권장 |
| VRAM | 최소 8GB (추론), 16GB (학습) |
| 학습 시간 | ~24시간 (100 epochs) |
| 데이터 | PID2Graph + 커스텀 50+ |

### 현실적 대안 (RTX 3080 8GB)

1. **Relationformer-Lite**: 경량화 버전 (미출시)
2. **단계적 접근**: YOLO (노드) + GNN (엣지)
3. **현재 파이프라인 최적화**: SAHI + Line Detector 개선

---

## 7. 결론 및 권장사항

### 즉시 실행 가능

1. **PID2Graph 데이터셋 획득** - 저자 연락 또는 공개 확인
2. **현재 시스템 벤치마크** - 정량적 기준선 확립
3. **Gap 분석** - 어떤 부분이 가장 약한지 확인

### 중기 계획

1. **Line Detector 고도화** - 연결성 검출 개선
2. **SAHI 파라미터 튜닝** - 소형 심볼 검출 개선
3. **규칙 기반 후처리** - 도메인 지식 활용

### 장기 계획 (GPU 업그레이드 시)

1. **Relationformer 평가** - 성능 vs 리소스 트레이드오프
2. **커스텀 학습** - TECHCROSS 도면 특화

---

## 8. 참고 자료

### 논문

- [Relationformer](https://arxiv.org/abs/2411.13929)
- [DETR](https://arxiv.org/abs/2005.12872)
- [Scene Graph Generation Survey](https://arxiv.org/abs/2104.01111)

### 코드

- PID2Graph: (저자 GitHub 확인 필요)
- Relationformer: (저자 GitHub 확인 필요)

### 데이터셋

- PID2Graph: 최초 공개 P&ID 그래프 데이터셋
- DocLayNet: 문서 레이아웃 벤치마크

---

*작성자*: Claude Code
