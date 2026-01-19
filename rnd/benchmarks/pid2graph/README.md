# PID2Graph Benchmark Evaluation

> **목적**: 현재 AX POC P&ID 파이프라인의 정량적 성능 평가
> **데이터셋**: [PID2Graph](https://zenodo.org/records/14803338) (9.3GB)
> **기준**: Relationformer 논문 (arXiv:2411.13929)
> **최종 업데이트**: 2026-01-19

---

## 디렉토리 구조

```
pid2graph/
├── README.md              # 이 파일
├── data/                  # PID2Graph 원본 데이터셋
│   └── PID2Graph/         # GraphML 어노테이션 + 이미지
├── training/              # ⭐ Fine-tuning 학습
│   ├── prepare_dataset.py # GraphML → YOLO 변환
│   ├── train.py           # 학습 스크립트
│   ├── dataset/           # YOLO 형식 데이터셋 (999장)
│   └── runs/              # 학습 결과
├── scripts/
│   ├── download.py        # 데이터셋 다운로드
│   ├── evaluate.py        # 평가 실행
│   └── analyze_results.py # 결과 분석
└── results/               # 시각화 결과
```

---

## Fine-tuning 결과 (2026-01-19)

### 성능 요약

| 지표 | 학습 전 (기존 YOLO) | 학습 후 (Fine-tuned) | 개선 |
|------|---------------------|----------------------|------|
| **Precision** | 46.6% | **78.5%** | +31.9% |
| **Recall** | 11.5% | **66.0%** | +54.5% |
| **mAP50** | ~18% | **68.5%** | +50.5% |
| **mAP50-95** | ~13% | **51.2%** | +38.2% |

### 학습 상세

| 항목 | 값 |
|------|-----|
| **기반 모델** | yolo11n.pt (pretrained) |
| **학습 데이터** | 999장 (train 800, val 149, test 50) |
| **클래스** | 8개 (crossing, connector, border_node, general, tank, valve, pump, arrow) |
| **Epochs** | 20/50 (Early stopping, patience=20) |
| **Batch Size** | 4 |
| **Image Size** | 640 |
| **학습 시간** | ~9분 (RTX 3080 8GB) |

### 모델 파일

- **Best 모델**: `training/runs/pid2graph/pid2graph_finetune/weights/best.pt`
- **복사본**: `../../models/pid2graph_yolo11n_finetuned.pt`

### 문제 해결

**기존 문제**: Recall이 11.5%로 매우 낮음
- 원인: PID2Graph GT 클래스(crossing, connector 등 96.3%)가 기존 YOLO 모델에 없음
- 해결: 8개 클래스로 Fine-tuning하여 Recall 66.0% 달성

---

## 빠른 시작

### 1. 데이터셋 다운로드

```bash
cd /home/uproot/ax/poc/rnd/benchmarks/pid2graph

# 전체 데이터셋 다운로드 (9.3GB)
python scripts/download.py --full

# 또는 샘플만 다운로드 (테스트용)
python scripts/download.py --sample
```

### 2. 평가 실행

```bash
# 현재 AX POC 파이프라인 평가
python scripts/evaluate.py \
  --data_dir data/ \
  --output results/ax_poc_eval.json

# 특정 이미지만 평가
python scripts/evaluate.py \
  --image data/complete/sample.png \
  --output results/single_eval.json
```

### 3. 결과 분석

```bash
python scripts/analyze_results.py \
  --results results/ax_poc_eval.json \
  --report results/report.md
```

---

## 평가 지표

| 지표 | 설명 | 목표 |
|------|------|------|
| **Symbol AP@50** | 심볼 검출 정확도 (IoU≥0.5) | 70%+ |
| **Symbol AP@75** | 심볼 검출 정확도 (IoU≥0.75) | 50%+ |
| **Edge mAP** | 연결선 검출 정확도 | 60%+ |
| **Graph F1** | 전체 그래프 구조 정확도 | 55%+ |

---

## 현재 파이프라인 구성

```
[P&ID 이미지]
    ↓
[YOLO (5005)] → 심볼 검출 (pid_class_aware 모델)
    ↓
[Line Detector (5016)] → 라인/연결선 검출
    ↓
[PID Analyzer (5018)] → 연결성 분석, 그래프 생성
    ↓
[결과 그래프] → NetworkX 형식
```

---

## 비교 대상: Relationformer

| 항목 | AX POC (기존) | AX POC (Fine-tuned) | Relationformer (SOTA) |
|------|--------------|---------------------|----------------------|
| 아키텍처 | 모듈식 | 모듈식 | End-to-End |
| 심볼 mAP50 | ~18% | **68.5%** | 83.63% |
| Recall | 11.5% | **66.0%** | - |
| GPU 요구 | ~2-4GB | ~2-4GB | ~6-8GB |
| 처리 시간 | 1-2초 | 1-2초 | ~0.5초 |

**Gap 분석**: Fine-tuning으로 SOTA 대비 ~82% 수준 달성 (68.5% / 83.63%)

---

## 참고 자료

- [PID2Graph 데이터셋](https://zenodo.org/records/14803338)
- [Relationformer 논문](https://arxiv.org/abs/2411.13929)
- [NetworkX 문서](https://networkx.org/documentation/stable/)
