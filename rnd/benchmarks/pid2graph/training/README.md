# PID2Graph YOLO Fine-tuning Guide

PID2Graph 데이터셋을 사용한 YOLO 모델 fine-tuning 가이드입니다.

## 개요

### 왜 Fine-tuning이 필요한가?

| 항목 | AX POC YOLO | PID2Graph |
|------|-------------|-----------|
| 학습 데이터 | 산업용 P&ID | 합성 다이어그램 |
| 주요 클래스 | Control Valve, Pump 등 | crossing, connector 등 |
| 스타일 | 복잡한 실제 도면 | 단순한 합성 도면 |
| 현재 성능 | - | Recall 11.5%, F1 18.4% |

Fine-tuning을 통해 PID2Graph 스타일에 맞는 모델을 학습할 수 있습니다.

## 빠른 시작

```bash
cd /home/uproot/ax/poc/rnd/benchmarks/pid2graph/training

# 1. 데이터셋 준비 (1000개 이미지로 테스트)
python prepare_dataset.py --max_images 1000 --output dataset

# 2. 학습 시작
python train.py train --data dataset/data.yaml --epochs 50

# 3. 검증
python train.py val --model runs/pid2graph/*/weights/best.pt --data dataset/data.yaml
```

## 상세 가이드

### Step 1: 데이터셋 준비

GraphML 어노테이션을 YOLO 형식으로 변환합니다.

```bash
# 전체 데이터셋 (36,000+ 이미지)
python prepare_dataset.py --source ../data/PID2Graph --output dataset

# 빠른 테스트 (1000개)
python prepare_dataset.py --max_images 1000 --output dataset_small

# 옵션
python prepare_dataset.py \
    --source ../data/PID2Graph \
    --output dataset \
    --max_images 5000 \
    --train_ratio 0.8 \
    --val_ratio 0.15 \
    --seed 42
```

**출력 구조:**
```
dataset/
├── data.yaml          # YOLO 설정 파일
├── images/
│   ├── train/         # 학습 이미지
│   ├── val/           # 검증 이미지
│   └── test/          # 테스트 이미지
└── labels/
    ├── train/         # 학습 라벨 (.txt)
    ├── val/           # 검증 라벨
    └── test/          # 테스트 라벨
```

**YOLO 라벨 형식:**
```
# class_id x_center y_center width height (0-1 정규화)
0 0.234567 0.456789 0.123456 0.234567
1 0.345678 0.567890 0.098765 0.198765
```

### Step 2: 학습

```bash
# 기본 학습 (yolov11n 기반)
python train.py train --data dataset/data.yaml

# AX POC 모델에서 시작 (권장)
python train.py train \
    --data dataset/data.yaml \
    --pretrained pid_class_agnostic \
    --epochs 100 \
    --batch 8 \
    --imgsz 1024

# 더 큰 모델 사용
python train.py train \
    --data dataset/data.yaml \
    --pretrained yolov11m \
    --epochs 100

# GPU 지정
python train.py train --device 0    # GPU 0
python train.py train --device cpu  # CPU
```

**학습 옵션:**
| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--epochs` | 100 | 학습 에폭 수 |
| `--batch` | 8 | 배치 크기 |
| `--imgsz` | 1024 | 입력 이미지 크기 |
| `--device` | 0 | GPU 번호 또는 cpu |
| `--pretrained` | yolov11n | 사전 학습 모델 |

**사용 가능한 사전 학습 모델:**
- `yolov11n` - 가장 작고 빠름
- `yolov11s` - 작음
- `yolov11m` - 중간 (권장)
- `yolov11l` - 큼
- `pid_class_agnostic` - AX POC 기존 모델

### Step 3: 검증

```bash
python train.py val \
    --model runs/pid2graph/finetune_*/weights/best.pt \
    --data dataset/data.yaml
```

### Step 4: 모델 내보내기

```bash
# ONNX 형식
python train.py export --model runs/pid2graph/*/weights/best.pt --format onnx

# TorchScript
python train.py export --model runs/pid2graph/*/weights/best.pt --format torchscript
```

## 클래스 정의

| ID | 클래스 | 설명 |
|----|--------|------|
| 0 | crossing | 파이프 교차점 |
| 1 | connector | 연결점 |
| 2 | border_node | 경계 노드 |
| 3 | general | 일반 장비 |
| 4 | tank | 탱크 |
| 5 | valve | 밸브 |
| 6 | pump | 펌프 |
| 7 | arrow | 화살표 |

## 예상 결과

| 학습 데이터 | 에폭 | mAP50 | mAP50-95 |
|------------|------|-------|----------|
| 1,000 이미지 | 50 | ~60-70% | ~40-50% |
| 5,000 이미지 | 100 | ~70-80% | ~50-60% |
| 전체 (36k) | 100 | ~80-90% | ~60-70% |

## AX POC 통합

Fine-tuning된 모델을 AX POC에 통합하려면:

```bash
# 1. 모델 복사
cp runs/pid2graph/*/weights/best.pt \
   /home/uproot/ax/poc/models/yolo-api/weights/pid2graph.pt

# 2. 모델 설정 추가 (models/yolo-api/config.py)
MODEL_PATHS = {
    ...
    "pid2graph": "weights/pid2graph.pt",
}

# 3. API에서 사용
curl -X POST http://localhost:5005/api/v1/detect \
  -F "image=@test.png" \
  -F "model_type=pid2graph"
```

## 문제 해결

### GPU 메모리 부족
```bash
# 배치 크기 줄이기
python train.py train --batch 4

# 이미지 크기 줄이기
python train.py train --imgsz 640
```

### 학습이 수렴하지 않음
```bash
# 학습률 조정
python train.py train --lr0 0.001

# 더 많은 에폭
python train.py train --epochs 200 --patience 50
```

## 참고 자료

- [Ultralytics YOLO Documentation](https://docs.ultralytics.com/)
- [PID2Graph Dataset Paper](https://arxiv.org/abs/2303.03542)
- [AX POC YOLO API](../../models/yolo-api/README.md)
