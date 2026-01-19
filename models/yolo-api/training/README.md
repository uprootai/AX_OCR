# YOLO Training Scripts

> YOLO 모델 학습, 평가, 추론 스크립트
> **최종 업데이트**: 2026-01-19

---

## 스크립트 목록

| 파일 | 설명 |
|------|------|
| `train_yolo.py` | YOLO 모델 학습 |
| `evaluate_yolo.py` | 모델 평가 |
| `inference_yolo.py` | 추론 실행 |
| `convert_yolo_to_gpu.py` | GPU 변환 |
| `generate_synthetic_random.py` | 합성 데이터 생성 |
| `merge_datasets.py` | 데이터셋 병합 |
| `train_with_synthetic.sh` | 합성 데이터로 학습 |

---

## 사용법

```bash
cd models/yolo-api/training/scripts

# 학습 실행
python train_yolo.py --data data.yaml --epochs 100 --batch 16

# 모델 평가
python evaluate_yolo.py --model weights/best.pt --data data.yaml

# 추론
python inference_yolo.py --model weights/best.pt --source image.png

# 합성 데이터 생성
python generate_synthetic_random.py --output synthetic/

# 데이터셋 병합
python merge_datasets.py --datasets dataset1/ dataset2/ --output merged/
```

---

## 관련 학습

- **PID2Graph Fine-tuning**: `rnd/benchmarks/pid2graph/training/`

---

*최종 업데이트*: 2026-01-19
