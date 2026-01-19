# EDGNet Training Scripts

> EDGNet 모델 학습 및 데이터 증강 스크립트
> **최종 업데이트**: 2026-01-19

---

## 스크립트 목록

| 파일 | 설명 |
|------|------|
| `augment_edgnet_data.py` | 데이터 증강 (회전, 밝기, 대비 조절) |
| `augment_edgnet_dataset.py` | EDGNetDataAugmenter 클래스 |
| `augment_edgnet_simple.py` | 간단한 증강 스크립트 |
| `generate_edgnet_dataset.py` | 데이터셋 생성 |
| `train_edgnet_large.py` | UNet 기반 대규모 학습 |
| `train_edgnet_simple.py` | SimpleGraphNet 학습 |
| `retrain_edgnet_gpu.py` | GPU 재학습 |

---

## 사용법

```bash
cd models/edgnet-api/training/scripts

# 데이터 증강
python augment_edgnet_data.py --input data/ --output augmented/

# 학습 실행
python train_edgnet_large.py --data_dir data/ --epochs 100

# GPU 재학습
python retrain_edgnet_gpu.py --model weights/best.pt
```

---

*최종 업데이트*: 2026-01-19
