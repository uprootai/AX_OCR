# YOLO Training

YOLOv11 객체 탐지 모델 학습 자료

## 📁 디렉토리 구조

```
training/
├── datasets/          # 학습 데이터셋
│   ├── combined/
│   ├── synthetic_random/
│   ├── pid_symbols/
│   └── synthetic_test/
├── runs/              # 학습 결과
│   ├── detect/       # 추론 결과
│   └── train/        # 학습 로그
├── scripts/          # 학습 스크립트
│   ├── train_yolo.py
│   ├── evaluate_yolo.py
│   ├── prepare_dataset.py
│   └── merge_datasets.py
└── README.md
```

## 🚀 학습 방법

### 1. 데이터셋 준비

```bash
python training/scripts/prepare_dataset.py \
  --input /path/to/raw/data \
  --output training/datasets/combined
```

### 2. 모델 학습

```bash
python training/scripts/train_yolo.py \
  --data training/datasets/combined \
  --epochs 100 \
  --imgsz 1280
```

### 3. 모델 평가

```bash
python training/scripts/evaluate_yolo.py \
  --model training/runs/train/exp/weights/best.pt \
  --data training/datasets/combined
```

### 4. 학습된 모델 배치

학습 완료 후 `best.pt`를 `models/best.pt`로 복사하여 API에서 사용합니다.

## 📊 데이터셋 정보

- **combined**: 실제 + 합성 데이터 혼합
- **synthetic_random**: 랜덤 생성 합성 데이터
- **pid_symbols**: P&ID 심볼 데이터
- **synthetic_test**: 테스트용 합성 데이터

## 🔧 학습 파라미터

- Image size: 1280x1280
- Batch size: 16
- Epochs: 100
- Model: YOLOv11 nano
