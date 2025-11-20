# EDGNet Training

EDGNet (GraphSAGE + UNet) 모델 학습 자료

## 📁 디렉토리 구조

```
training/
├── datasets/           # 학습 데이터셋
│   ├── original/      # 원본 데이터
│   ├── augmented/     # 증강 데이터
│   └── large/         # Large 데이터셋
├── scripts/           # 학습 스크립트
│   ├── train_edgnet_large.py
│   ├── train_edgnet_simple.py
│   ├── augment_edgnet*.py
│   └── generate_edgnet_dataset.py
└── README.md
```

## 🚀 학습 방법

### 1. 데이터셋 증강

```bash
python training/scripts/augment_edgnet_data.py \
  --input training/datasets/original \
  --output training/datasets/augmented
```

### 2. 모델 학습

```bash
python training/scripts/train_edgnet_large.py \
  --data training/datasets/large \
  --epochs 50 \
  --batch-size 4 \
  --save-dir models/
```

### 3. 학습된 모델 배치

학습 완료 후 `models/` 디렉토리에 생성된 모델 파일을 API에서 사용합니다.

## 📊 데이터셋 정보

- **Original**: 원본 도면 데이터
- **Augmented**: 회전, 밝기, 노이즈 증강
- **Large**: 대규모 학습용 데이터셋

## 🔧 의존성

학습에 필요한 패키지는 상위 디렉토리의 `requirements.txt`를 참조하세요.
