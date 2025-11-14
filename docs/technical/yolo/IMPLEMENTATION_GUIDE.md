# YOLOv11 구현 가이드 (상세)

**작성일**: 2025-10-31
**목적**: 공학 도면 치수/GD&T 추출을 위한 YOLOv11 End-to-End 구현

---

## 📑 목차

1. [데이터셋 조합 방법](#1-데이터셋-조합-방법)
2. [모델 학습 방법](#2-모델-학습-방법)
3. [추론 방법](#3-추론-방법)
4. [API 서버 구축](#4-api-서버-구축)
5. [Gateway 통합](#5-gateway-통합)
6. [성능 평가](#6-성능-평가)

---

## 1. 데이터셋 조합 방법

### 1.1 데이터 구조 설계

YOLOv11은 다음과 같은 디렉토리 구조를 요구합니다:

```
datasets/
└── engineering_drawings/
    ├── images/
    │   ├── train/
    │   │   ├── drawing_001.jpg
    │   │   ├── drawing_002.jpg
    │   │   └── ...
    │   ├── val/
    │   │   ├── drawing_101.jpg
    │   │   └── ...
    │   └── test/
    │       ├── drawing_201.jpg
    │       └── ...
    └── labels/
        ├── train/
        │   ├── drawing_001.txt
        │   ├── drawing_002.txt
        │   └── ...
        ├── val/
        │   ├── drawing_101.txt
        │   └── ...
        └── test/
            ├── drawing_201.txt
            └── ...
```

### 1.2 클래스 정의

**파일**: `datasets/engineering_drawings/classes.yaml`

```yaml
# YOLOv11 Dataset Configuration
path: /home/uproot/ax/poc/datasets/engineering_drawings
train: images/train
val: images/val
test: images/test

# Classes (14개)
names:
  0: diameter_dim        # φ476, φ370
  1: linear_dim          # 120, 245
  2: radius_dim          # R50, R25
  3: angular_dim         # 45°, 90°
  4: chamfer_dim         # 2x45°, C3
  5: tolerance_dim       # ±0.1, +0.2/-0.1
  6: reference_dim       # (177), (245)
  7: flatness            # ⌹
  8: cylindricity        # ○
  9: position            # ⌖
  10: perpendicularity   # ⊥
  11: parallelism        # ∥
  12: surface_roughness  # Ra3.2, Ra6.3
  13: text_block         # 일반 텍스트

# Number of classes
nc: 14
```

### 1.3 라벨 포맷 (YOLO Format)

각 이미지에 대응하는 `.txt` 파일:

```
<class_id> <x_center> <y_center> <width> <height>
```

- **class_id**: 0-13 (클래스 인덱스)
- **x_center, y_center**: 중심점 좌표 (0-1 정규화)
- **width, height**: 박스 크기 (0-1 정규화)

**예시**: `drawing_001.txt`
```
0 0.234 0.456 0.05 0.03   # diameter_dim at (23.4%, 45.6%)
1 0.678 0.234 0.04 0.02   # linear_dim
7 0.456 0.789 0.06 0.04   # flatness symbol
```

### 1.4 좌표 변환 함수

eDOCr의 bbox를 YOLO 포맷으로 변환:

```python
def edocr_to_yolo_format(bbox, image_width, image_height):
    """
    eDOCr bbox를 YOLO 포맷으로 변환

    Args:
        bbox: dict with keys x, y, width, height (픽셀 좌표)
        image_width: 이미지 너비
        image_height: 이미지 높이

    Returns:
        tuple: (x_center, y_center, width, height) 정규화된 좌표
    """
    x = bbox['x']
    y = bbox['y']
    w = bbox['width']
    h = bbox['height']

    # 중심점 계산
    x_center = (x + w / 2) / image_width
    y_center = (y + h / 2) / image_height

    # 크기 정규화
    norm_width = w / image_width
    norm_height = h / image_height

    # 0-1 범위로 클리핑
    x_center = max(0, min(1, x_center))
    y_center = max(0, min(1, y_center))
    norm_width = max(0, min(1, norm_width))
    norm_height = max(0, min(1, norm_height))

    return x_center, y_center, norm_width, norm_height
```

### 1.5 데이터셋 생성 스크립트

**파일**: `scripts/prepare_dataset.py`

```python
#!/usr/bin/env python3
"""
eDOCr 결과를 YOLO 데이터셋으로 변환
"""
import os
import json
import shutil
from pathlib import Path
from PIL import Image
import random

def create_dataset_structure(output_dir):
    """데이터셋 디렉토리 생성"""
    dirs = [
        'images/train', 'images/val', 'images/test',
        'labels/train', 'labels/val', 'labels/test'
    ]
    for d in dirs:
        Path(output_dir / d).mkdir(parents=True, exist_ok=True)

def classify_dimension(text):
    """치수 텍스트를 클래스로 분류"""
    text = text.strip()

    # Diameter
    if text.startswith('φ') or text.startswith('Ø'):
        return 0, 'diameter_dim'

    # Radius
    if text.startswith('R'):
        return 2, 'radius_dim'

    # Angular
    if '°' in text:
        return 3, 'angular_dim'

    # Chamfer
    if 'x' in text and '°' in text:
        return 4, 'chamfer_dim'
    if text.startswith('C'):
        return 4, 'chamfer_dim'

    # Tolerance
    if '±' in text or ('+' in text and '-' in text):
        return 5, 'tolerance_dim'

    # Reference (in parentheses)
    if text.startswith('(') and text.endswith(')'):
        return 6, 'reference_dim'

    # Default: linear dimension
    return 1, 'linear_dim'

def classify_gdt_symbol(symbol_type):
    """GD&T 기호 분류"""
    gdt_map = {
        'flatness': 7,
        'cylindricity': 8,
        'position': 9,
        'perpendicularity': 10,
        'parallelism': 11
    }
    return gdt_map.get(symbol_type.lower(), 7)

def convert_annotation(annotation, image_path, output_label_path):
    """
    단일 어노테이션을 YOLO 포맷으로 변환

    Args:
        annotation: dict with OCR results
        image_path: 이미지 파일 경로
        output_label_path: 출력 라벨 파일 경로
    """
    # 이미지 크기 가져오기
    with Image.open(image_path) as img:
        img_width, img_height = img.size

    yolo_lines = []

    # Dimensions 변환
    if 'dimensions' in annotation and annotation['dimensions']:
        for dim in annotation['dimensions']:
            if 'bbox' not in dim or 'value' not in dim:
                continue

            bbox = dim['bbox']
            value = dim['value']

            # 클래스 분류
            class_id, class_name = classify_dimension(value)

            # YOLO 포맷 변환
            x_center, y_center, width, height = edocr_to_yolo_format(
                bbox, img_width, img_height
            )

            yolo_lines.append(
                f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
            )

    # GD&T 기호 변환
    if 'gdt' in annotation and annotation['gdt']:
        for gdt in annotation['gdt']:
            if 'bbox' not in gdt or 'type' not in gdt:
                continue

            bbox = gdt['bbox']
            symbol_type = gdt['type']

            # 클래스 분류
            class_id = classify_gdt_symbol(symbol_type)

            # YOLO 포맷 변환
            x_center, y_center, width, height = edocr_to_yolo_format(
                bbox, img_width, img_height
            )

            yolo_lines.append(
                f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
            )

    # Surface Roughness (표면조도)
    if 'surface_roughness' in annotation and annotation['surface_roughness']:
        for sr in annotation['surface_roughness']:
            if 'bbox' not in sr:
                continue

            bbox = sr['bbox']
            class_id = 12  # surface_roughness

            x_center, y_center, width, height = edocr_to_yolo_format(
                bbox, img_width, img_height
            )

            yolo_lines.append(
                f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
            )

    # 라벨 파일 저장
    with open(output_label_path, 'w') as f:
        f.write('\n'.join(yolo_lines))

    return len(yolo_lines)

def split_dataset(image_files, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
    """데이터셋을 train/val/test로 분할"""
    random.shuffle(image_files)

    total = len(image_files)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)

    return {
        'train': image_files[:train_end],
        'val': image_files[train_end:val_end],
        'test': image_files[val_end:]
    }

def main():
    """메인 실행 함수"""
    # 설정
    source_images_dir = Path('/home/uproot/ax/poc/edocr2-api/uploads')
    source_annotations_dir = Path('/home/uproot/ax/poc/edocr2-api/results')
    output_dir = Path('/home/uproot/ax/poc/datasets/engineering_drawings')

    print("📁 Creating dataset structure...")
    create_dataset_structure(output_dir)

    # 이미지 파일 수집
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []

    for ext in image_extensions:
        image_files.extend(source_images_dir.glob(f'*{ext}'))

    print(f"📊 Found {len(image_files)} images")

    if len(image_files) == 0:
        print("❌ No images found. Please add images to:", source_images_dir)
        return

    # Train/Val/Test 분할
    splits = split_dataset(image_files)

    print(f"✂️  Split: Train={len(splits['train'])}, Val={len(splits['val'])}, Test={len(splits['test'])}")

    # 각 분할별로 처리
    total_annotations = 0

    for split_name, split_files in splits.items():
        print(f"\n🔄 Processing {split_name} split...")

        for img_path in split_files:
            # 어노테이션 파일 찾기
            annotation_path = source_annotations_dir / f"{img_path.stem}_result.json"

            if not annotation_path.exists():
                print(f"⚠️  No annotation for {img_path.name}, skipping")
                continue

            # 이미지 복사
            dst_image = output_dir / 'images' / split_name / img_path.name
            shutil.copy(img_path, dst_image)

            # 어노테이션 로드
            with open(annotation_path, 'r') as f:
                annotation = json.load(f)

            # YOLO 라벨 생성
            dst_label = output_dir / 'labels' / split_name / f"{img_path.stem}.txt"
            count = convert_annotation(annotation, img_path, dst_label)

            total_annotations += count

            if count > 0:
                print(f"✅ {img_path.name}: {count} objects")
            else:
                print(f"⚠️  {img_path.name}: No objects detected")

    print(f"\n🎉 Dataset creation complete!")
    print(f"   Total images: {len(image_files)}")
    print(f"   Total annotations: {total_annotations}")
    print(f"   Output directory: {output_dir}")

    # data.yaml 생성
    yaml_path = output_dir / 'data.yaml'
    with open(yaml_path, 'w') as f:
        f.write(f"""# Engineering Drawings Dataset
path: {output_dir}
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
""")

    print(f"📝 Created data.yaml at: {yaml_path}")

def edocr_to_yolo_format(bbox, image_width, image_height):
    """eDOCr bbox를 YOLO 포맷으로 변환"""
    x = bbox.get('x', 0)
    y = bbox.get('y', 0)
    w = bbox.get('width', 50)
    h = bbox.get('height', 30)

    # 중심점 계산
    x_center = (x + w / 2) / image_width
    y_center = (y + h / 2) / image_height

    # 크기 정규화
    norm_width = w / image_width
    norm_height = h / image_height

    # 0-1 범위로 클리핑
    x_center = max(0, min(1, x_center))
    y_center = max(0, min(1, y_center))
    norm_width = max(0, min(1, norm_width))
    norm_height = max(0, min(1, norm_height))

    return x_center, y_center, norm_width, norm_height

if __name__ == '__main__':
    main()
```

---

## 2. 모델 학습 방법

### 2.1 학습 환경 설정

**필요 라이브러리**:
```bash
pip install ultralytics>=8.0.0
pip install torch>=2.0.0
pip install torchvision>=0.15.0
pip install opencv-python>=4.8.0
pip install pillow>=10.0.0
pip install pyyaml>=6.0
pip install tqdm
```

### 2.2 학습 스크립트

**파일**: `scripts/train_yolo.py`

```python
#!/usr/bin/env python3
"""
YOLOv11 모델 학습 스크립트
"""
import argparse
from pathlib import Path
from ultralytics import YOLO
import torch

def train_model(
    model_size='n',
    data_yaml='datasets/engineering_drawings/data.yaml',
    epochs=100,
    imgsz=1280,
    batch=16,
    device='0',
    project='runs/train',
    name='engineering_drawings',
    resume=False,
    pretrained=True
):
    """
    YOLOv11 모델 학습

    Args:
        model_size: 모델 크기 (n, s, m, l, x)
        data_yaml: 데이터셋 YAML 경로
        epochs: 에폭 수
        imgsz: 이미지 크기
        batch: 배치 크기
        device: GPU 디바이스
        project: 프로젝트 디렉토리
        name: 실험 이름
        resume: 중단된 학습 재개
        pretrained: 사전 학습 가중치 사용
    """

    print("=" * 70)
    print("🚀 YOLOv11 Training Configuration")
    print("=" * 70)
    print(f"Model Size: yolo11{model_size}")
    print(f"Dataset: {data_yaml}")
    print(f"Epochs: {epochs}")
    print(f"Image Size: {imgsz}")
    print(f"Batch Size: {batch}")
    print(f"Device: {device}")
    print(f"Pretrained: {pretrained}")
    print("=" * 70)

    # GPU 확인
    if device != 'cpu':
        if not torch.cuda.is_available():
            print("⚠️  CUDA not available, using CPU")
            device = 'cpu'
        else:
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ Using GPU: {gpu_name}")

    # 모델 로드
    if resume:
        print("📂 Resuming from last checkpoint...")
        model_path = Path(project) / name / 'weights' / 'last.pt'
        if not model_path.exists():
            print(f"❌ Checkpoint not found: {model_path}")
            return
        model = YOLO(str(model_path))
    else:
        if pretrained:
            model_name = f'yolo11{model_size}.pt'
            print(f"📥 Loading pretrained model: {model_name}")
        else:
            model_name = f'yolo11{model_size}.yaml'
            print(f"🔨 Training from scratch: {model_name}")

        model = YOLO(model_name)

    # 학습 시작
    print("\n🎯 Starting training...")
    print("=" * 70)

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=project,
        name=name,

        # Optimization
        optimizer='AdamW',
        lr0=0.001,           # 초기 학습률
        lrf=0.01,            # 최종 학습률 (lr0 * lrf)
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,

        # Augmentation
        hsv_h=0.015,         # 색조 증강
        hsv_s=0.7,           # 채도 증강
        hsv_v=0.4,           # 명도 증강
        degrees=10.0,        # 회전 (±10도)
        translate=0.1,       # 이동
        scale=0.5,           # 스케일
        shear=0.0,           # 전단
        perspective=0.0,     # 원근
        flipud=0.0,          # 상하 반전 (도면은 방향 중요)
        fliplr=0.5,          # 좌우 반전
        mosaic=1.0,          # 모자이크 증강
        mixup=0.0,           # MixUp 증강
        copy_paste=0.0,      # Copy-Paste 증강

        # Settings
        save=True,
        save_period=10,      # 10 에폭마다 체크포인트 저장
        plots=True,
        verbose=True,
        patience=50,         # Early stopping

        # Validation
        val=True,

        # Multi-GPU (optional)
        # workers=8,
    )

    print("\n" + "=" * 70)
    print("✅ Training complete!")
    print("=" * 70)
    print(f"📊 Results saved to: {results.save_dir}")
    print(f"🏆 Best model: {results.save_dir / 'weights' / 'best.pt'}")
    print(f"📈 Metrics:")
    print(f"   - mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
    print(f"   - mAP50-95: {results.results_dict.get('metrics/mAP50-95(B)', 'N/A')}")

    return results

def main():
    parser = argparse.ArgumentParser(description='Train YOLOv11 on engineering drawings')

    parser.add_argument('--model-size', type=str, default='n',
                        choices=['n', 's', 'm', 'l', 'x'],
                        help='Model size (n=nano, s=small, m=medium, l=large, x=xlarge)')
    parser.add_argument('--data', type=str,
                        default='datasets/engineering_drawings/data.yaml',
                        help='Path to data.yaml')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of epochs')
    parser.add_argument('--imgsz', type=int, default=1280,
                        help='Image size (high resolution for drawings)')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size')
    parser.add_argument('--device', type=str, default='0',
                        help='CUDA device (0, 1, 2, ...) or cpu')
    parser.add_argument('--project', type=str, default='runs/train',
                        help='Project directory')
    parser.add_argument('--name', type=str, default='engineering_drawings',
                        help='Experiment name')
    parser.add_argument('--resume', action='store_true',
                        help='Resume training from last checkpoint')
    parser.add_argument('--no-pretrained', action='store_true',
                        help='Train from scratch (no pretrained weights)')

    args = parser.parse_args()

    train_model(
        model_size=args.model_size,
        data_yaml=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        resume=args.resume,
        pretrained=not args.no_pretrained
    )

if __name__ == '__main__':
    main()
```

### 2.3 학습 실행 명령어

#### 기본 학습 (Nano 모델, 권장)
```bash
cd /home/uproot/ax/poc
python scripts/train_yolo.py \
    --model-size n \
    --epochs 100 \
    --imgsz 1280 \
    --batch 16 \
    --device 0
```

#### 고해상도 + 큰 모델 (GPU 메모리 16GB 이상)
```bash
python scripts/train_yolo.py \
    --model-size m \
    --epochs 150 \
    --imgsz 1920 \
    --batch 8 \
    --device 0
```

#### CPU 학습 (느림, 테스트용)
```bash
python scripts/train_yolo.py \
    --model-size n \
    --epochs 50 \
    --batch 4 \
    --device cpu
```

#### 중단된 학습 재개
```bash
python scripts/train_yolo.py --resume
```

### 2.4 학습 모니터링

학습 중 실시간 모니터링:

```bash
# TensorBoard (권장)
tensorboard --logdir runs/train

# 또는 로그 파일 확인
tail -f runs/train/engineering_drawings/results.txt
```

---

## 3. 추론 방법

### 3.1 추론 스크립트

**파일**: `scripts/inference_yolo.py`

```python
#!/usr/bin/env python3
"""
YOLOv11 추론 스크립트
"""
import argparse
from pathlib import Path
from ultralytics import YOLO
import cv2
import json
import time

# 클래스 이름 매핑
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

def yolo_to_edocr_format(result, image_shape):
    """
    YOLO 결과를 eDOCr 호환 포맷으로 변환

    Args:
        result: YOLO detection result
        image_shape: (height, width) tuple

    Returns:
        dict: eDOCr 형식의 결과
    """
    img_height, img_width = image_shape[:2]

    dimensions = []
    gdt = []
    surface_roughness = []
    text_blocks = []

    boxes = result.boxes

    for i, box in enumerate(boxes):
        # 클래스 ID와 신뢰도
        cls_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = CLASS_NAMES.get(cls_id, 'unknown')

        # 바운딩 박스 (xyxy 포맷)
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        # 픽셀 좌표로 변환
        x = int(x1)
        y = int(y1)
        width = int(x2 - x1)
        height = int(y2 - y1)

        bbox = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }

        # 클래스별로 분류
        if cls_id <= 6:  # Dimensions (0-6)
            dimensions.append({
                'type': class_name,
                'value': '',  # OCR refinement 필요
                'unit': 'mm',
                'bbox': bbox,
                'confidence': confidence
            })

        elif cls_id <= 11:  # GD&T symbols (7-11)
            gdt.append({
                'type': class_name,
                'value': '',  # OCR refinement 필요
                'bbox': bbox,
                'confidence': confidence
            })

        elif cls_id == 12:  # Surface roughness
            surface_roughness.append({
                'value': '',  # OCR refinement 필요
                'bbox': bbox,
                'confidence': confidence
            })

        elif cls_id == 13:  # Text block
            text_blocks.append({
                'text': '',  # OCR refinement 필요
                'bbox': bbox,
                'confidence': confidence
            })

    return {
        'dimensions': dimensions,
        'gdt': gdt,
        'surface_roughness': surface_roughness,
        'text_blocks': text_blocks,
        'total_detections': len(boxes)
    }

def draw_detections(image, result):
    """
    이미지에 검출 결과 그리기

    Args:
        image: numpy array (BGR)
        result: YOLO detection result

    Returns:
        numpy array: 어노테이션된 이미지
    """
    annotated_img = image.copy()
    boxes = result.boxes

    # 색상 정의 (BGR)
    colors = {
        'dimension': (255, 100, 0),     # Blue for dimensions
        'gdt': (0, 255, 100),           # Green for GD&T
        'surface': (0, 165, 255),       # Orange for surface
        'text': (255, 255, 0)           # Cyan for text
    }

    for box in boxes:
        cls_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = CLASS_NAMES.get(cls_id, 'unknown')

        # 바운딩 박스
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # 색상 선택
        if cls_id <= 6:
            color = colors['dimension']
        elif cls_id <= 11:
            color = colors['gdt']
        elif cls_id == 12:
            color = colors['surface']
        else:
            color = colors['text']

        # 박스 그리기
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)

        # 라벨 그리기
        label = f"{class_name} {confidence:.2f}"
        (label_w, label_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )

        cv2.rectangle(
            annotated_img,
            (x1, y1 - label_h - 10),
            (x1 + label_w, y1),
            color,
            -1
        )

        cv2.putText(
            annotated_img,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )

    return annotated_img

def run_inference(
    model_path,
    source,
    output_dir='runs/inference',
    conf_threshold=0.25,
    iou_threshold=0.7,
    imgsz=1280,
    save_images=True,
    save_json=True,
    device='0'
):
    """
    YOLO 추론 실행

    Args:
        model_path: 학습된 모델 경로
        source: 이미지 또는 디렉토리 경로
        output_dir: 출력 디렉토리
        conf_threshold: 신뢰도 임계값
        iou_threshold: NMS IoU 임계값
        imgsz: 이미지 크기
        save_images: 어노테이션된 이미지 저장
        save_json: JSON 결과 저장
        device: GPU 디바이스
    """

    print("=" * 70)
    print("🔍 YOLOv11 Inference")
    print("=" * 70)
    print(f"Model: {model_path}")
    print(f"Source: {source}")
    print(f"Confidence threshold: {conf_threshold}")
    print(f"Image size: {imgsz}")
    print("=" * 70)

    # 모델 로드
    model = YOLO(model_path)

    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 추론 실행
    start_time = time.time()

    results = model.predict(
        source=source,
        conf=conf_threshold,
        iou=iou_threshold,
        imgsz=imgsz,
        device=device,
        save=False,  # 우리가 직접 저장
        verbose=True
    )

    elapsed_time = time.time() - start_time

    # 결과 처리
    print(f"\n📊 Processing {len(results)} images...")

    all_results = []

    for i, result in enumerate(results):
        image_path = Path(result.path)
        image_name = image_path.stem

        # 이미지 로드
        image = cv2.imread(str(image_path))

        # eDOCr 포맷으로 변환
        detection_result = yolo_to_edocr_format(result, image.shape)

        detection_result['image_name'] = image_name
        detection_result['image_path'] = str(image_path)
        detection_result['model'] = str(model_path)
        detection_result['inference_time'] = elapsed_time / len(results)

        all_results.append(detection_result)

        # 통계 출력
        print(f"✅ {image_name}: {detection_result['total_detections']} detections")

        # 어노테이션된 이미지 저장
        if save_images:
            annotated_img = draw_detections(image, result)
            save_path = output_path / f"{image_name}_annotated.jpg"
            cv2.imwrite(str(save_path), annotated_img)

        # JSON 저장
        if save_json:
            json_path = output_path / f"{image_name}_result.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(detection_result, f, indent=2, ensure_ascii=False)

    # 전체 통계
    total_detections = sum(r['total_detections'] for r in all_results)
    avg_time = elapsed_time / len(results)

    print("\n" + "=" * 70)
    print("✅ Inference complete!")
    print("=" * 70)
    print(f"📊 Statistics:")
    print(f"   - Total images: {len(results)}")
    print(f"   - Total detections: {total_detections}")
    print(f"   - Average detections/image: {total_detections / len(results):.1f}")
    print(f"   - Total time: {elapsed_time:.2f}s")
    print(f"   - Average time/image: {avg_time:.2f}s")
    print(f"   - FPS: {1/avg_time:.2f}")
    print(f"📁 Results saved to: {output_path}")

    # 전체 요약 저장
    summary = {
        'total_images': len(results),
        'total_detections': total_detections,
        'average_detections_per_image': total_detections / len(results),
        'total_time': elapsed_time,
        'average_time_per_image': avg_time,
        'fps': 1 / avg_time,
        'results': all_results
    }

    summary_path = output_path / 'summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary

def main():
    parser = argparse.ArgumentParser(description='YOLOv11 Inference on engineering drawings')

    parser.add_argument('--model', type=str, required=True,
                        help='Path to trained model (best.pt)')
    parser.add_argument('--source', type=str, required=True,
                        help='Image file or directory')
    parser.add_argument('--output', type=str, default='runs/inference',
                        help='Output directory')
    parser.add_argument('--conf', type=float, default=0.25,
                        help='Confidence threshold')
    parser.add_argument('--iou', type=float, default=0.7,
                        help='NMS IoU threshold')
    parser.add_argument('--imgsz', type=int, default=1280,
                        help='Image size')
    parser.add_argument('--device', type=str, default='0',
                        help='CUDA device or cpu')
    parser.add_argument('--no-save-images', action='store_true',
                        help='Do not save annotated images')
    parser.add_argument('--no-save-json', action='store_true',
                        help='Do not save JSON results')

    args = parser.parse_args()

    run_inference(
        model_path=args.model,
        source=args.source,
        output_dir=args.output,
        conf_threshold=args.conf,
        iou_threshold=args.iou,
        imgsz=args.imgsz,
        save_images=not args.no_save_images,
        save_json=not args.no_save_json,
        device=args.device
    )

if __name__ == '__main__':
    main()
```

### 3.2 추론 실행 명령어

#### 단일 이미지 추론
```bash
python scripts/inference_yolo.py \
    --model runs/train/engineering_drawings/weights/best.pt \
    --source test_images/drawing_001.jpg \
    --output runs/inference/test
```

#### 디렉토리 배치 추론
```bash
python scripts/inference_yolo.py \
    --model runs/train/engineering_drawings/weights/best.pt \
    --source test_images/ \
    --conf 0.25 \
    --imgsz 1280
```

#### 고신뢰도만 검출
```bash
python scripts/inference_yolo.py \
    --model runs/train/engineering_drawings/weights/best.pt \
    --source test_image.jpg \
    --conf 0.5  # 50% 이상만
```

---

## 4. API 서버 구축

### 4.1 FastAPI 서버

**파일**: `yolo-api/api_server.py` (다음 단계에서 구현)

### 4.2 Docker 설정

**파일**: `yolo-api/Dockerfile` (다음 단계에서 구현)

---

## 5. Gateway 통합

Gateway API에 YOLO 엔드포인트 추가 (다음 단계)

---

## 6. 성능 평가

### 6.1 평가 스크립트

**파일**: `scripts/evaluate_yolo.py`

```python
#!/usr/bin/env python3
"""
YOLOv11 모델 평가
"""
import argparse
from ultralytics import YOLO

def evaluate_model(
    model_path,
    data_yaml='datasets/engineering_drawings/data.yaml',
    split='test',
    imgsz=1280,
    device='0'
):
    """
    모델 평가 실행
    """
    print("=" * 70)
    print("📊 YOLOv11 Model Evaluation")
    print("=" * 70)
    print(f"Model: {model_path}")
    print(f"Dataset: {data_yaml}")
    print(f"Split: {split}")
    print("=" * 70)

    # 모델 로드
    model = YOLO(model_path)

    # 평가 실행
    metrics = model.val(
        data=data_yaml,
        split=split,
        imgsz=imgsz,
        device=device,
        save_json=True,
        save_hybrid=True,
        plots=True
    )

    # 결과 출력
    print("\n" + "=" * 70)
    print("📈 Evaluation Results")
    print("=" * 70)
    print(f"Precision: {metrics.box.p:.4f}")
    print(f"Recall: {metrics.box.r:.4f}")
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    print(f"F1 Score: {2 * (metrics.box.p * metrics.box.r) / (metrics.box.p + metrics.box.r):.4f}")

    return metrics

def main():
    parser = argparse.ArgumentParser(description='Evaluate YOLOv11 model')

    parser.add_argument('--model', type=str, required=True,
                        help='Path to model weights')
    parser.add_argument('--data', type=str,
                        default='datasets/engineering_drawings/data.yaml',
                        help='Path to data.yaml')
    parser.add_argument('--split', type=str, default='test',
                        choices=['train', 'val', 'test'],
                        help='Dataset split to evaluate')
    parser.add_argument('--imgsz', type=int, default=1280,
                        help='Image size')
    parser.add_argument('--device', type=str, default='0',
                        help='CUDA device or cpu')

    args = parser.parse_args()

    evaluate_model(
        model_path=args.model,
        data_yaml=args.data,
        split=args.split,
        imgsz=args.imgsz,
        device=args.device
    )

if __name__ == '__main__':
    main()
```

---

## 요약: 전체 워크플로우

```
1. 데이터셋 준비
   └─> python scripts/prepare_dataset.py

2. 모델 학습
   └─> python scripts/train_yolo.py --model-size n --epochs 100

3. 모델 평가
   └─> python scripts/evaluate_yolo.py --model runs/train/engineering_drawings/weights/best.pt

4. 추론 테스트
   └─> python scripts/inference_yolo.py --model best.pt --source test_images/

5. API 서버 구축
   └─> (다음 단계에서 구현)

6. Gateway 통합
   └─> (다음 단계에서 구현)
```

---

**다음 문서**: API 서버 구축 및 Docker 배포
**작성자**: Claude 3.7 Sonnet
**최종 업데이트**: 2025-10-31
