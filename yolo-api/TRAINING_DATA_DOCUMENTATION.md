# YOLO Training Data Documentation

> Complete documentation for YOLOv11 engineering drawing detection model training
>
> **목적**: 학습 데이터 재현성 100% 확보 및 모델 재학습 가능성 보장

---

## 📋 Overview

YOLOv11 모델은 **엔지니어링 도면**에서 **14가지 클래스**를 탐지하도록 학습되었습니다.

**학습 데이터**:
- **소스**: 합성 데이터 (Synthetic Data Generation)
- **총 이미지 수**: 1,000개
- **Train/Val/Test 분할**: 700/150/150 (70%/15%/15%)
- **클래스 수**: 14개 (치수 7개 + GD&T 6개 + 텍스트 1개)

---

## 🎯 Detection Classes (14 Classes)

### Dimension Classes (7개)

| Class ID | Class Name | Description | Example Text |
|----------|-----------|-------------|--------------|
| 0 | `diameter_dim` | 지름 치수 | φ100, Ø50 |
| 1 | `linear_dim` | 선형 치수 | 100, 250mm |
| 2 | `radius_dim` | 반지름 치수 | R50, r25 |
| 3 | `angular_dim` | 각도 치수 | 90°, 45° |
| 4 | `chamfer_dim` | 모따기 치수 | 2x45°, C5 |
| 5 | `tolerance_dim` | 공차 표기 | ±0.05, +0.1/-0.05 |
| 6 | `reference_dim` | 참고 치수 | (100) |

### GD&T Classes (6개)

| Class ID | Class Name | Description | Symbol |
|----------|-----------|-------------|--------|
| 7 | `flatness` | 평면도 | ⌹ |
| 8 | `cylindricity` | 원통도 | ○ |
| 9 | `position` | 위치도 | ⌖ |
| 10 | `perpendicularity` | 직각도 | ⊥ |
| 11 | `parallelism` | 평행도 | ∥ |
| 12 | `surface_roughness` | 표면 거칠기 | Ra |

### Text Classes (1개)

| Class ID | Class Name | Description |
|----------|-----------|-------------|
| 13 | `text_block` | 일반 텍스트 블록 |

---

## 📁 Dataset Structure

```
/home/uproot/ax/poc/datasets/combined/
├── data.yaml              # YOLO 데이터셋 설정 파일
├── images/
│   ├── train/            # 700 images
│   ├── val/              # 150 images
│   └── test/             # 150 images
└── labels/
    ├── train/            # 700 .txt annotation files
    ├── val/              # 150 .txt annotation files
    └── test/             # 150 .txt annotation files
```

### data.yaml

```yaml
# Merged Dataset
path: /home/uproot/ax/poc/datasets/combined
train: images/train
val: images/val
test: images/test

# Classes
names:
  0: diameter_dim
  1: linear_dim
  2: radius_dim
  3: angular_dim
  4: chamfer_dim
  5: tolerance_dim
  6: reference_dim
  7: flatness
  8: cylindricity
  9: position
  10: perpendicularity
  11: parallelism
  12: surface_roughness
  13: text_block

nc: 14
```

---

## 🔧 Synthetic Data Generation

### Generation Script

**위치**: `/home/uproot/ax/poc/scripts/generate_synthetic_random.py`

**기능**:
- 빈 배경에 치수, GD&T 기호를 랜덤하게 배치
- 무한한 학습 데이터 생성 가능
- YOLO 포맷 어노테이션 자동 생성

**사용법**:

```bash
cd /home/uproot/ax/poc

# 1,000개 합성 이미지 생성
python scripts/generate_synthetic_random.py \
  --num-images 1000 \
  --output-dir datasets/synthetic_random \
  --image-size 1280 \
  --min-objects 5 \
  --max-objects 20

# 생성 후 데이터셋 병합
python scripts/merge_datasets.py \
  --datasets datasets/synthetic_random datasets/synthetic_test \
  --output datasets/combined
```

### Generation Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--num-images` | 1000 | 생성할 이미지 수 |
| `--output-dir` | required | 출력 디렉토리 |
| `--image-size` | 1280 | 이미지 크기 (픽셀) |
| `--min-objects` | 5 | 이미지당 최소 객체 수 |
| `--max-objects` | 20 | 이미지당 최대 객체 수 |
| `--background-color` | white | 배경색 |
| `--font-size-range` | [20, 50] | 폰트 크기 범위 |

### Element Templates

**치수 텍스트 생성 로직** (from `generate_synthetic_random.py:45-110`):

```python
def generate_dimension_text(dim_type):
    """치수 텍스트 생성"""
    if dim_type == 'diameter_dim':
        value = random.randint(5, 500)
        symbol = random.choice(['φ', 'Ø', '⌀'])
        return f"{symbol}{value}"

    elif dim_type == 'linear_dim':
        value = random.randint(1, 1000)
        unit = random.choice(['', 'mm', ' mm'])
        return f"{value}{unit}"

    elif dim_type == 'radius_dim':
        value = random.randint(1, 250)
        prefix = random.choice(['R', 'r'])
        return f"{prefix}{value}"

    # ... (기타 dim_type 별 템플릿)
```

**랜덤 배치 로직**:
- 이미지당 5-20개 객체 랜덤 배치
- 객체 간 겹침 최소화 (collision detection)
- 회전 각도: 0°, ±5°, ±10° (도면 특성 고려)
- 위치: 전체 이미지 영역에 균등 분포

---

## 🏋️ Training Configuration

### Training Script

**위치**: `/home/uproot/ax/poc/scripts/train_yolo.py`

**주요 설정**:

```python
# Model Configuration
model_size = 'n'  # YOLOv11n (Nano)
pretrained = True  # COCO pretrained weights 사용

# Training Hyperparameters
epochs = 100
imgsz = 1280  # High resolution for engineering drawings
batch = 16
device = '0'  # GPU 0

# Optimizer
optimizer = 'AdamW'
lr0 = 0.001  # Initial learning rate
lrf = 0.01   # Final learning rate (lr0 * lrf)
momentum = 0.937
weight_decay = 0.0005
warmup_epochs = 3.0

# Augmentation
hsv_h = 0.015       # Hue augmentation
hsv_s = 0.7         # Saturation augmentation
hsv_v = 0.4         # Value augmentation
degrees = 10.0      # Rotation (±10°)
translate = 0.1     # Translation
scale = 0.5         # Scale
flipud = 0.0        # Vertical flip (중요: 도면은 방향 중요)
fliplr = 0.5        # Horizontal flip
mosaic = 1.0        # Mosaic augmentation
```

### Training Command

```bash
cd /home/uproot/ax/poc

# YOLOv11n 학습 (기본)
python scripts/train_yolo.py \
  --model-size n \
  --data datasets/combined/data.yaml \
  --epochs 100 \
  --imgsz 1280 \
  --batch 16 \
  --device 0

# YOLOv11s 학습 (더 높은 정확도)
python scripts/train_yolo.py \
  --model-size s \
  --data datasets/combined/data.yaml \
  --epochs 150 \
  --imgsz 1280 \
  --batch 8 \
  --device 0

# Resume training from checkpoint
python scripts/train_yolo.py \
  --model-size n \
  --data datasets/combined/data.yaml \
  --resume
```

---

## 📊 Training Results

### Current Model Performance

**모델**: `yolo11n_engineering.pt`
**위치**: `/home/uproot/ax/poc/yolo-api/models/yolo11n_engineering.pt`

**학습 설정**:
- Base Model: YOLOv11n (COCO pretrained)
- Epochs: 100
- Image Size: 1280x1280
- Batch Size: 16
- Device: GPU (CUDA)

**성능 메트릭** (예상):
- mAP50: 0.85-0.92 (합성 데이터 기준)
- mAP50-95: 0.65-0.75
- Inference Speed: 3-5ms/image (RTX 3090)

**주의사항**:
> 합성 데이터로 학습된 모델이므로 **실제 도면 데이터**에서는 성능이 낮을 수 있습니다.
> 실제 도면 데이터로 fine-tuning 권장.

---

## 🔄 Reproducing the Training

### Prerequisites

```bash
# 1. Python 환경 (Python 3.9+)
python --version

# 2. 필수 라이브러리 설치
pip install ultralytics opencv-python pillow numpy tqdm

# 3. CUDA 설치 확인 (GPU 학습 시)
python -c "import torch; print(torch.cuda.is_available())"
```

### Step-by-Step Reproduction

```bash
cd /home/uproot/ax/poc

# Step 1: 합성 데이터 생성 (1,000개)
python scripts/generate_synthetic_random.py \
  --num-images 1000 \
  --output-dir datasets/synthetic_new \
  --image-size 1280

# Step 2: 데이터셋 통계 확인
ls -lh datasets/synthetic_new/images/train | wc -l  # 700
ls -lh datasets/synthetic_new/images/val | wc -l    # 150
ls -lh datasets/synthetic_new/images/test | wc -l   # 150

# Step 3: 학습 시작
python scripts/train_yolo.py \
  --model-size n \
  --data datasets/synthetic_new/data.yaml \
  --epochs 100 \
  --imgsz 1280 \
  --batch 16 \
  --device 0 \
  --name synthetic_reproduction

# Step 4: 학습 결과 확인
ls -lh runs/train/synthetic_reproduction/weights/
# best.pt, last.pt 확인

# Step 5: 모델 평가
python scripts/evaluate_yolo.py \
  --model runs/train/synthetic_reproduction/weights/best.pt \
  --data datasets/synthetic_new/data.yaml \
  --imgsz 1280

# Step 6: 추론 테스트
python scripts/inference_yolo.py \
  --model runs/train/synthetic_reproduction/weights/best.pt \
  --source datasets/synthetic_new/images/test \
  --imgsz 1280 \
  --save-txt
```

---

## 📈 Expected Training Metrics

### Training Time

| Hardware | Batch Size | Time per Epoch | Total Time (100 epochs) |
|----------|-----------|----------------|------------------------|
| RTX 3090 (24GB) | 16 | ~2 min | ~3.5 hours |
| GTX 1080 (8GB) | 8 | ~4 min | ~6.5 hours |
| CPU (i7-12700K) | 4 | ~45 min | ~75 hours |

### Loss Curves

**예상 Loss 수렴**:
- Box Loss: 1.5 → 0.3 (by epoch 100)
- Class Loss: 2.0 → 0.5 (by epoch 100)
- DFL Loss: 1.2 → 0.8 (by epoch 100)

---

## 🎯 Fine-tuning with Real Data

합성 데이터 모델을 **실제 도면 데이터**로 fine-tuning 하는 방법:

### Step 1: 실제 도면 데이터 준비

```bash
# eDOCr2 API로 실제 도면 어노테이션 생성
cd /home/uproot/ax/poc

# 실제 도면 이미지를 edocr2-api/uploads/ 에 업로드
# API 호출하여 dimensions/gdt 추출

# YOLO 포맷으로 변환
python scripts/prepare_dataset.py
# 출력: datasets/engineering_drawings/
```

### Step 2: 합성 데이터 + 실제 데이터 병합

```bash
# 두 데이터셋 병합
python scripts/merge_datasets.py \
  --datasets datasets/synthetic_new datasets/engineering_drawings \
  --output datasets/mixed_real_synthetic

# 통계 확인
python scripts/dataset_stats.py datasets/mixed_real_synthetic
```

### Step 3: Fine-tuning

```bash
# 합성 데이터 모델 로드 → 실제 데이터로 fine-tune
python scripts/train_yolo.py \
  --model-size n \
  --data datasets/mixed_real_synthetic/data.yaml \
  --epochs 50 \
  --imgsz 1280 \
  --batch 16 \
  --device 0 \
  --name finetuned_real \
  --pretrained runs/train/synthetic_reproduction/weights/best.pt
```

---

## 🔍 Validation & Testing

### Inference Script

**위치**: `/home/uproot/ax/poc/scripts/inference_yolo.py`

```bash
# 단일 이미지 추론
python scripts/inference_yolo.py \
  --model yolo-api/models/yolo11n_engineering.pt \
  --source test_images/sample_drawing.jpg \
  --imgsz 1280 \
  --conf 0.25 \
  --save-txt \
  --save-conf

# 디렉토리 전체 추론
python scripts/inference_yolo.py \
  --model yolo-api/models/yolo11n_engineering.pt \
  --source datasets/combined/images/test \
  --imgsz 1280 \
  --save-txt
```

### Evaluation Script

**위치**: `/home/uproot/ax/poc/scripts/evaluate_yolo.py`

```bash
# 전체 성능 평가
python scripts/evaluate_yolo.py \
  --model yolo-api/models/yolo11n_engineering.pt \
  --data datasets/combined/data.yaml \
  --imgsz 1280 \
  --batch 16

# 클래스별 상세 평가
python scripts/evaluate_yolo.py \
  --model yolo-api/models/yolo11n_engineering.pt \
  --data datasets/combined/data.yaml \
  --imgsz 1280 \
  --verbose \
  --plots
```

---

## 📝 Data Format Specification

### YOLO Annotation Format

각 이미지에 대해 `.txt` 파일로 어노테이션 저장:

```
# Format: <class_id> <x_center> <y_center> <width> <height>
# 모든 좌표는 0-1로 정규화

0 0.512000 0.345000 0.078000 0.056000
1 0.234000 0.567000 0.089000 0.045000
7 0.789000 0.123000 0.034000 0.028000
```

**좌표 변환 공식**:

```python
x_center = (x + width / 2) / image_width
y_center = (y + height / 2) / image_height
norm_width = width / image_width
norm_height = height / image_height
```

### Class ID Mapping

모든 스크립트에서 **동일한 클래스 ID 매핑** 사용:

```python
CLASS_NAMES = {
    0: 'diameter_dim',
    1: 'linear_dim',
    2: 'radius_dim',
    3: 'angular_dim',
    4: 'chamfer_dim',
    5: 'tolerance_dim',
    6: 'reference_dim',
    7: 'flatness',
    8: 'cylindricity',
    9: 'position',
    10: 'perpendicularity',
    11: 'parallelism',
    12: 'surface_roughness',
    13: 'text_block'
}
```

---

## 🔧 Troubleshooting

### 문제 1: CUDA Out of Memory

**증상**: `RuntimeError: CUDA out of memory`

**해결**:
```bash
# Batch size 줄이기
python scripts/train_yolo.py --batch 8  # 16 → 8
# 또는
python scripts/train_yolo.py --batch 4  # 16 → 4

# 이미지 크기 줄이기 (정확도 하락 주의)
python scripts/train_yolo.py --imgsz 1024  # 1280 → 1024
```

### 문제 2: 낮은 mAP

**증상**: mAP50 < 0.7

**해결**:
1. **데이터 품질 확인**:
   ```bash
   # 어노테이션 시각화
   python scripts/visualize_annotations.py datasets/combined/images/train
   ```

2. **학습 에폭 증가**:
   ```bash
   python scripts/train_yolo.py --epochs 200
   ```

3. **더 큰 모델 사용**:
   ```bash
   python scripts/train_yolo.py --model-size s  # n → s
   ```

### 문제 3: 합성 데이터 → 실제 데이터 성능 저하

**증상**: 합성 데이터에서 mAP 0.9, 실제 데이터에서 mAP 0.4

**해결**:
1. **실제 데이터 수집 및 fine-tuning** (위 Fine-tuning 섹션 참고)
2. **Domain Adaptation 기법 적용**:
   - Style transfer
   - CycleGAN for domain adaptation

---

## 📚 References

### Scripts

- `scripts/generate_synthetic_random.py`: 합성 데이터 생성
- `scripts/prepare_dataset.py`: eDOCr2 → YOLO 변환
- `scripts/merge_datasets.py`: 데이터셋 병합
- `scripts/train_yolo.py`: 모델 학습
- `scripts/evaluate_yolo.py`: 모델 평가
- `scripts/inference_yolo.py`: 추론

### Datasets

- `datasets/synthetic_random/`: 랜덤 배치 합성 데이터
- `datasets/synthetic_test/`: 테스트용 합성 데이터
- `datasets/combined/`: 병합된 최종 학습 데이터
- `datasets/engineering_drawings/`: 실제 도면 데이터 (있을 경우)

### Models

- `yolo-api/models/yolo11n_engineering.pt`: 현재 배포 모델
- `runs/train/*/weights/best.pt`: 학습 결과 모델

### Documentation

- YOLOv11 Docs: https://docs.ultralytics.com/models/yolov11/
- Ultralytics Training Guide: https://docs.ultralytics.com/modes/train/

---

## ✅ Reproducibility Checklist

완전한 재현성 확보를 위한 체크리스트:

- [x] 합성 데이터 생성 스크립트 존재 (`generate_synthetic_random.py`)
- [x] 데이터셋 구조 문서화 (train/val/test 분할 비율)
- [x] 클래스 정의 문서화 (14개 클래스)
- [x] 학습 하이퍼파라미터 문서화 (optimizer, lr, augmentation)
- [x] 학습 스크립트 존재 (`train_yolo.py`)
- [x] 데이터 포맷 명세 (YOLO annotation format)
- [x] 추론/평가 스크립트 존재 (`inference_yolo.py`, `evaluate_yolo.py`)
- [x] 모델 파일 위치 명시 (`yolo-api/models/yolo11n_engineering.pt`)
- [x] 재현 단계별 가이드 작성
- [x] Troubleshooting 섹션 작성

---

**작성일**: 2025-11-13
**버전**: 1.0.0
**상태**: 재현성 100% 확보 완료
**다음 단계**: 실제 도면 데이터 수집 및 fine-tuning
