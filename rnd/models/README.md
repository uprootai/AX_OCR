# R&D Models

> **목적**: Fine-tuning 및 실험 모델 관리
> **최종 업데이트**: 2026-01-19

---

## 모델 목록

| 모델 파일 | 기반 | 데이터셋 | 성능 | 용도 |
|-----------|------|----------|------|------|
| `pid2graph_yolo11n_finetuned.pt` | YOLOv11n | PID2Graph 1000장 | mAP50: 68.5% | P&ID 심볼 검출 |

---

## PID2Graph Fine-tuned Model

### 학습 정보

| 항목 | 값 |
|------|-----|
| **기반 모델** | yolo11n.pt (pretrained) |
| **학습 데이터** | PID2Graph 999장 (train 800, val 149, test 50) |
| **클래스** | 8개 (crossing, connector, border_node, general, tank, valve, pump, arrow) |
| **Epochs** | 20/50 (Early stopping) |
| **Batch Size** | 4 |
| **Image Size** | 640 |

### 성능 결과

| 지표 | 값 |
|------|-----|
| **Precision** | 78.5% |
| **Recall** | 66.0% |
| **mAP50** | 68.5% |
| **mAP50-95** | 51.2% |

### 기존 모델 대비 개선

| 지표 | 기존 (pid_class_agnostic) | Fine-tuned | 개선 |
|------|---------------------------|------------|------|
| Precision | 46.6% | 78.5% | +31.9% |
| Recall | 11.5% | 66.0% | +54.5% |
| mAP50 | ~18% | 68.5% | +50.5% |

### 사용 방법

```python
from ultralytics import YOLO

model = YOLO("/home/uproot/ax/poc/rnd/models/pid2graph_yolo11n_finetuned.pt")
results = model.predict("pid_image.png", conf=0.25)
```

---

## 관련 파일

- **학습 코드**: `../benchmarks/pid2graph/training/`
- **데이터셋**: `../benchmarks/pid2graph/training/dataset/`
- **학습 로그**: `../benchmarks/pid2graph/training/runs/pid2graph/`

---

*최종 업데이트*: 2026-01-19
