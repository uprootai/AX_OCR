# API별 커스텀 학습 가이드

> **작성일**: 2025-12-31
> **목적**: 각 API에 대한 커스텀 데이터셋 학습 방법 정리
> **GPU 기준**: RTX 3080 8GB (또는 그 이상)

---

## 목차

1. [YOLO API - 심볼 검출 학습](#1-yolo-api---심볼-검출-학습)
2. [PaddleOCR - 치수 인식 Fine-tuning](#2-paddleocr---치수-인식-fine-tuning)
3. [DocLayout-YOLO - 도면 레이아웃 학습](#3-doclayout-yolo---도면-레이아웃-학습)
4. [GD&T (SkinModel) - 기하공차 학습](#4-gdt-skinmodel---기하공차-학습)
5. [학습 데이터 관리](#5-학습-데이터-관리)

---

## 1. YOLO API - 심볼 검출 학습

### 1.1 개요

| 항목 | 내용 |
|------|------|
| **모델** | YOLOv11 (Ultralytics) |
| **용도** | P&ID 심볼, 기계도면 심볼, BOM 항목 검출 |
| **현재 클래스** | engineering(14), pid_class_aware(32), bom_detector(27) |
| **학습 시간** | ~2-4시간 (100 epochs, 1000 이미지 기준) |

### 1.2 데이터셋 구조

```
datasets/
├── pid_symbols/
│   ├── images/
│   │   ├── train/
│   │   │   ├── drawing_001.png
│   │   │   └── ...
│   │   └── val/
│   │       ├── drawing_100.png
│   │       └── ...
│   ├── labels/
│   │   ├── train/
│   │   │   ├── drawing_001.txt  # YOLO 형식
│   │   │   └── ...
│   │   └── val/
│   │       ├── drawing_100.txt
│   │       └── ...
│   └── data.yaml
```

### 1.3 어노테이션 형식 (YOLO Format)

```
# labels/train/drawing_001.txt
# class_id center_x center_y width height (정규화된 값 0-1)
0 0.5123 0.3456 0.0234 0.0312
1 0.7234 0.5678 0.0456 0.0389
2 0.1234 0.8901 0.0178 0.0245
```

### 1.4 data.yaml 설정

```yaml
# datasets/pid_symbols/data.yaml
path: /home/uproot/ax/poc/datasets/pid_symbols
train: images/train
val: images/val

# 클래스 정의
names:
  0: gate_valve
  1: globe_valve
  2: ball_valve
  3: butterfly_valve
  4: check_valve
  5: control_valve
  6: safety_valve
  7: pump
  8: compressor
  9: heat_exchanger
  10: tank
  11: vessel
  12: pressure_indicator
  13: temperature_indicator
  14: flow_indicator
  15: level_indicator
  # ... 추가 클래스
```

### 1.5 학습 명령어

```python
from ultralytics import YOLO

# 1. 기존 모델 로드 (전이학습)
model = YOLO("yolo11m.pt")

# 2. 학습 실행
results = model.train(
    data="datasets/pid_symbols/data.yaml",
    epochs=200,
    imgsz=1280,              # P&ID 심볼용 고해상도
    batch=8,                 # RTX 3080 8GB 기준
    patience=50,             # Early stopping
    device=0,                # GPU 0

    # 하이퍼파라미터
    lr0=0.01,                # 초기 학습률
    lrf=0.01,                # 최종 학습률 비율
    momentum=0.937,
    weight_decay=0.0005,
    warmup_epochs=3,

    # 증강
    hsv_h=0.015,             # 색조 변환
    hsv_s=0.7,               # 채도 변환
    hsv_v=0.4,               # 명도 변환
    degrees=0,               # 회전 (도면은 0 권장)
    translate=0.1,           # 이동
    scale=0.5,               # 스케일
    flipud=0.0,              # 상하 반전 (도면은 0)
    fliplr=0.0,              # 좌우 반전 (도면은 0)
    mosaic=0.5,              # 모자이크 (도면은 낮게)

    # 프로젝트 설정
    project="runs/train",
    name="pid_symbols_v1",
    exist_ok=True,
)

# 3. 모델 저장
model.export(format="onnx")  # ONNX 변환 (선택)
```

### 1.6 모델 배포

```bash
# 학습된 모델을 API에 적용
cp runs/train/pid_symbols_v1/weights/best.pt \
   models/yolo-api/weights/pid_class_aware_custom.pt

# Docker 재빌드
docker-compose build yolo-api
docker-compose up -d yolo-api
```

### 1.7 어노테이션 도구 추천

| 도구 | 특징 | 링크 |
|------|------|------|
| **Roboflow** | 웹 기반, 자동 라벨링 지원 | [roboflow.com](https://roboflow.com) |
| **CVAT** | 오픈소스, 협업 지원 | [cvat.ai](https://cvat.ai) |
| **Label Studio** | 오픈소스, 다양한 형식 | [labelstud.io](https://labelstud.io) |
| **LabelImg** | 가벼운 로컬 도구 | [github.com/HumanSignal/labelImg](https://github.com/HumanSignal/labelImg) |

### 1.8 자동 라벨링 (Grounding DINO)

```python
# 자동 라벨링으로 시간 절약
from autodistill.detection import CaptionOntology
from autodistill_grounding_dino import GroundingDINO

# 클래스 정의
ontology = CaptionOntology({
    "valve": "valve",
    "pump": "pump",
    "tank": "tank",
    "heat exchanger": "heat_exchanger",
})

# 자동 라벨링
base_model = GroundingDINO(ontology=ontology)
base_model.label(
    input_folder="datasets/raw_images",
    output_folder="datasets/labeled"
)
```

---

## 2. PaddleOCR - 치수 인식 Fine-tuning

### 2.1 개요

| 항목 | 내용 |
|------|------|
| **모델** | PP-OCRv5 (PaddleOCR 3.0) |
| **용도** | 도면 치수, 공차, 특수 기호 인식 |
| **현재 성능** | 일반 텍스트 95%+, 치수 텍스트 ~85% |
| **학습 시간** | ~4-8시간 (50 epochs, 10000 샘플 기준) |

### 2.2 데이터셋 구조

```
datasets/
├── dimension_ocr/
│   ├── train/
│   │   ├── img_001.jpg
│   │   ├── img_002.jpg
│   │   └── ...
│   ├── val/
│   │   └── ...
│   ├── train_label.txt
│   ├── val_label.txt
│   └── dict.txt
```

### 2.3 라벨 파일 형식

```
# train_label.txt
# 형식: 이미지경로{탭}텍스트
train/img_001.jpg	∅25.4±0.05
train/img_002.jpg	R12.5
train/img_003.jpg	45°
train/img_004.jpg	□50×30
train/img_005.jpg	⌀10H7
train/img_006.jpg	0.02|A|B
```

### 2.4 사전 파일 (dict.txt)

```
# dict.txt - 인식할 문자 목록
0
1
2
3
4
5
6
7
8
9
.
±
°
∅
⌀
R
×
□
△
▽
/
|
A
B
C
M
H
h
g
f
+
-
```

### 2.5 학습 설정 파일

```yaml
# configs/rec/PP-OCRv5/dimension_rec.yml
Global:
  debug: false
  use_gpu: true
  epoch_num: 50
  log_smooth_window: 20
  print_batch_step: 100
  save_model_dir: ./output/dimension_rec/
  save_epoch_step: 10
  eval_batch_step: [0, 2000]
  cal_metric_during_train: true
  pretrained_model: ./pretrained_models/PP-OCRv5_server_rec_pretrained
  checkpoints: null
  save_inference_dir: null
  use_visualdl: false
  infer_img: null
  character_dict_path: ./datasets/dimension_ocr/dict.txt
  max_text_length: 25
  infer_mode: false
  use_space_char: false

Optimizer:
  name: Adam
  beta1: 0.9
  beta2: 0.999
  lr:
    name: Cosine
    learning_rate: 0.0001  # Fine-tuning은 낮은 학습률
    warmup_epoch: 2

Architecture:
  model_type: rec
  algorithm: SVTR_LCNet
  Transform:
  Backbone:
    name: PPLCNetV3
    scale: 0.95
  Head:
    name: MultiHead
    head_list:
      - CTCHead:
          Neck:
            name: svtr
            dims: 120
            depth: 2
            hidden_dims: 120
            kernel_size: [1, 3]
            use_guide: true
          Head:
            fc_decay: 0.00001
      - NRTRHead:
          nrtr_dim: 384
          max_text_length: *max_text_length

Loss:
  name: MultiLoss
  loss_config_list:
    - CTCLoss:
    - NRTRLoss:

PostProcess:
  name: CTCLabelDecode

Metric:
  name: RecMetric
  main_indicator: acc

Train:
  dataset:
    name: SimpleDataSet
    data_dir: ./datasets/dimension_ocr/
    label_file_list:
      - ./datasets/dimension_ocr/train_label.txt
    transforms:
      - DecodeImage:
          img_mode: BGR
          channel_first: false
      - RecAug:
      - MultiLabelEncode:
      - RecResizeImg:
          image_shape: [3, 48, 320]
      - KeepKeys:
          keep_keys:
            - image
            - label_ctc
            - label_nrtr
            - length
            - valid_ratio
  loader:
    shuffle: true
    batch_size_per_card: 64
    drop_last: true
    num_workers: 4

Eval:
  dataset:
    name: SimpleDataSet
    data_dir: ./datasets/dimension_ocr/
    label_file_list:
      - ./datasets/dimension_ocr/val_label.txt
    transforms:
      - DecodeImage:
          img_mode: BGR
          channel_first: false
      - MultiLabelEncode:
      - RecResizeImg:
          image_shape: [3, 48, 320]
      - KeepKeys:
          keep_keys:
            - image
            - label_ctc
            - label_nrtr
            - length
            - valid_ratio
  loader:
    shuffle: false
    drop_last: false
    batch_size_per_card: 64
    num_workers: 4
```

### 2.6 학습 실행

```bash
# PaddleOCR 환경 설정
cd PaddleOCR

# 사전학습 모델 다운로드
wget https://paddle-model-ecology.bj.bcebos.com/paddlex/official_pretrained_model/PP-OCRv5_server_rec_pretrained.pdparams \
    -P pretrained_models/

# 학습 실행
python tools/train.py -c configs/rec/PP-OCRv5/dimension_rec.yml

# 평가
python tools/eval.py -c configs/rec/PP-OCRv5/dimension_rec.yml \
    -o Global.checkpoints=output/dimension_rec/best_accuracy
```

### 2.7 모델 변환 및 배포

```bash
# 추론용 모델 변환
python tools/export_model.py \
    -c configs/rec/PP-OCRv5/dimension_rec.yml \
    -o Global.pretrained_model=output/dimension_rec/best_accuracy \
       Global.save_inference_dir=./inference/dimension_rec/

# API에 적용
cp -r inference/dimension_rec/ \
   models/paddleocr-api/models/custom_rec/
```

### 2.8 치수 데이터 생성 팁

```python
# 합성 치수 데이터 생성
import random
from PIL import Image, ImageDraw, ImageFont

def generate_dimension_sample():
    """합성 치수 이미지 생성"""
    templates = [
        "∅{:.1f}±{:.2f}",
        "R{:.1f}",
        "{:.0f}°",
        "{:.1f}×{:.1f}",
        "{:.1f}H{:d}",
    ]

    template = random.choice(templates)
    if template.count("{}") == 1:
        text = template.format(random.uniform(1, 100))
    elif template.count("{}") == 2:
        text = template.format(
            random.uniform(1, 100),
            random.uniform(0.01, 0.1)
        )

    # 이미지 생성
    img = Image.new('RGB', (200, 48), color='white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((10, 10), text, fill='black', font=font)

    return img, text
```

---

## 3. DocLayout-YOLO - 도면 레이아웃 학습

### 3.1 개요

| 항목 | 내용 |
|------|------|
| **모델** | DocLayout-YOLO (YOLOv10 기반) |
| **용도** | 도면 영역 분할 (뷰, BOM 표, 타이틀 블록, 노트) |
| **기본 클래스** | 10개 (title, table, figure, 등) |
| **학습 시간** | ~3-6시간 (100 epochs, 1000 이미지 기준) |

### 3.2 데이터셋 구조

```
datasets/
├── drawing_layout/
│   ├── images/
│   │   ├── train/
│   │   └── val/
│   ├── labels/
│   │   ├── train/
│   │   └── val/
│   └── data.yaml
```

### 3.3 도면 전용 클래스 정의

```yaml
# data.yaml
path: /home/uproot/ax/poc/datasets/drawing_layout
train: images/train
val: images/val

names:
  0: title_block       # 타이틀 블록
  1: revision_table    # 리비전 표
  2: bom_table         # BOM 표
  3: main_view         # 메인 뷰
  4: section_view      # 단면도
  5: detail_view       # 상세도
  6: notes_area        # 노트 영역
  7: dimension_area    # 치수 영역
  8: tolerance_block   # 공차 블록
  9: stamp_area        # 스탬프/승인 영역
```

### 3.4 학습 코드

```python
from doclayout_yolo import YOLOv10

# 모델 로드
model = YOLOv10("path/to/doclayout_yolo_pretrained.pt")

# 학습
results = model.train(
    data="datasets/drawing_layout/data.yaml",
    epochs=100,
    imgsz=1024,
    batch=8,
    device=0,

    # DocLayout-YOLO 권장 설정
    lr0=0.001,           # 낮은 학습률 (fine-tuning)
    lrf=0.1,
    momentum=0.937,

    # 프로젝트 설정
    project="runs/doclayout",
    name="drawing_layout_v1",
)
```

### 3.5 Blueprint AI BOM 통합

```python
# blueprint-ai-bom에서 DocLayout-YOLO 사용
from doclayout_yolo import YOLOv10

class DrawingLayoutAnalyzer:
    def __init__(self, model_path: str):
        self.model = YOLOv10(model_path)

    def detect_regions(self, image_path: str) -> dict:
        results = self.model.predict(
            image_path,
            imgsz=1024,
            conf=0.15,  # 낮은 임계값으로 다양한 영역 검출
        )

        regions = {
            "title_block": [],
            "bom_table": [],
            "main_view": [],
            "notes_area": [],
        }

        for det in results[0].boxes:
            cls_name = self.model.names[int(det.cls)]
            bbox = det.xyxy[0].tolist()
            conf = float(det.conf)

            if cls_name in regions:
                regions[cls_name].append({
                    "bbox": bbox,
                    "confidence": conf
                })

        return regions
```

---

## 4. GD&T (SkinModel) - 기하공차 학습

### 4.1 개요

| 항목 | 내용 |
|------|------|
| **모델** | YOLO + 규칙 기반 파서 |
| **용도** | GD&T 기호 검출 및 파싱 |
| **현재 클래스** | 14개 (flatness, cylindricity, position, 등) |
| **학습 시간** | ~2-4시간 (100 epochs) |

### 4.2 GD&T 클래스 정의

```yaml
# datasets/gdt_symbols/data.yaml
path: /home/uproot/ax/poc/datasets/gdt_symbols
train: images/train
val: images/val

names:
  # 형상 공차 (Form)
  0: flatness           # 평면도 ⏥
  1: straightness       # 진직도 ⏤
  2: circularity        # 진원도 ○
  3: cylindricity       # 원통도 ⌭

  # 방향 공차 (Orientation)
  4: parallelism        # 평행도 ∥
  5: perpendicularity   # 직각도 ⊥
  6: angularity         # 경사도 ∠

  # 위치 공차 (Location)
  7: position           # 위치도 ⌖
  8: concentricity      # 동심도 ◎
  9: symmetry           # 대칭도 ⌯

  # 흔들림 공차 (Runout)
  10: circular_runout   # 원주 흔들림 ↗
  11: total_runout      # 전체 흔들림 ↗↗

  # 프로파일 공차 (Profile)
  12: profile_line      # 선의 윤곽도 ⌒
  13: profile_surface   # 면의 윤곽도 ⌓

  # 기타
  14: datum             # 데이텀 기호
  15: feature_control   # 형체 제어 프레임 전체
```

### 4.3 학습 코드

```python
from ultralytics import YOLO

model = YOLO("yolo11m.pt")

results = model.train(
    data="datasets/gdt_symbols/data.yaml",
    epochs=150,
    imgsz=640,           # GD&T는 작은 영역이므로 640 충분
    batch=16,
    device=0,

    # GD&T 특화 설정
    lr0=0.01,
    scale=0.3,           # 스케일 변환 적게
    degrees=0,           # 회전 없음
    translate=0.05,      # 이동 적게

    project="runs/gdt",
    name="gdt_symbols_v1",
)
```

### 4.4 GD&T 파싱 통합

```python
# SkinModel API와 통합
class GDTParser:
    def __init__(self, yolo_model_path: str):
        self.detector = YOLO(yolo_model_path)
        self.ocr = PaddleOCR()  # 값 인식용

    def parse_gdt(self, image) -> list:
        # 1. GD&T 기호 검출
        detections = self.detector.predict(image, conf=0.3)

        gdt_features = []
        for det in detections[0].boxes:
            cls_name = self.detector.names[int(det.cls)]
            bbox = det.xyxy[0].tolist()

            # 2. 검출 영역에서 값 추출 (OCR)
            x1, y1, x2, y2 = map(int, bbox)
            roi = image[y1:y2, x1:x2]
            ocr_result = self.ocr.predict(roi)

            # 3. 파싱
            gdt_features.append({
                "type": cls_name,
                "value": self._parse_value(ocr_result),
                "bbox": bbox,
            })

        return gdt_features
```

---

## 5. 학습 데이터 관리

### 5.1 디렉토리 구조

```
datasets/
├── README.md              # 데이터셋 문서
├── pid_symbols/           # P&ID 심볼
│   ├── images/
│   ├── labels/
│   └── data.yaml
├── dimension_ocr/         # 치수 OCR
│   ├── train/
│   ├── val/
│   └── dict.txt
├── drawing_layout/        # 도면 레이아웃
│   ├── images/
│   ├── labels/
│   └── data.yaml
├── gdt_symbols/           # GD&T 기호
│   ├── images/
│   ├── labels/
│   └── data.yaml
└── raw/                   # 원본 도면 (어노테이션 전)
```

### 5.2 데이터셋 버전 관리

```bash
# DVC (Data Version Control) 사용
pip install dvc

# 초기화
dvc init
dvc remote add -d storage s3://bucket/datasets

# 데이터셋 추적
dvc add datasets/pid_symbols
git add datasets/pid_symbols.dvc .gitignore
git commit -m "Add P&ID symbols dataset v1"

# 푸시
dvc push
```

### 5.3 데이터 증강 파이프라인

```python
import albumentations as A

# 도면 전용 증강 (색상 변환 최소화)
transform = A.Compose([
    A.RandomScale(scale_limit=0.2, p=0.5),
    A.GaussNoise(var_limit=(10, 50), p=0.3),
    A.GaussianBlur(blur_limit=3, p=0.2),
    A.RandomBrightnessContrast(
        brightness_limit=0.1,
        contrast_limit=0.1,
        p=0.3
    ),
    # 주의: 회전/반전은 도면에서 사용 안 함
], bbox_params=A.BboxParams(
    format='yolo',
    label_fields=['class_labels']
))
```

### 5.4 학습 모니터링

```python
# Weights & Biases 연동
import wandb

wandb.init(project="ax-poc-training")

model.train(
    data="data.yaml",
    epochs=100,
    # W&B 연동
    project="ax-poc-training",
    name="pid_symbols_v1",
)
```

### 5.5 모델 레지스트리

```yaml
# models/registry.yaml
models:
  yolo_pid_class_aware:
    version: "v2.0"
    path: "weights/pid_class_aware_v2.pt"
    classes: 32
    trained_on: "2025-01-15"
    metrics:
      mAP50: 0.923
      mAP50-95: 0.847

  yolo_bom_detector:
    version: "v1.5"
    path: "weights/bom_detector_v1.5.pt"
    classes: 27
    trained_on: "2024-12-20"
    metrics:
      mAP50: 0.912
      mAP50-95: 0.834
```

---

## 6. Quick Start 체크리스트

### 새 모델 학습 시

- [ ] 데이터셋 수집 (최소 500+ 이미지 권장)
- [ ] 어노테이션 도구 선택 (Roboflow/CVAT/LabelImg)
- [ ] 클래스 정의 및 data.yaml 작성
- [ ] 학습/검증 분할 (80/20 권장)
- [ ] 기본 학습 실행 및 결과 확인
- [ ] 하이퍼파라미터 튜닝
- [ ] 최종 모델 저장 및 배포
- [ ] API 통합 테스트

### 권장 데이터셋 크기

| 모델 | 최소 이미지 | 권장 이미지 | 클래스당 |
|------|------------|------------|----------|
| YOLO (심볼) | 500 | 2000+ | 50+ |
| OCR (치수) | 5000 | 20000+ | - |
| DocLayout | 500 | 1500+ | 50+ |
| GD&T | 300 | 1000+ | 30+ |

---

## Sources

- [YOLOv11 Custom Training Guide (Roboflow)](https://blog.roboflow.com/yolov11-how-to-train-custom-data/)
- [Ultralytics Training Docs](https://docs.ultralytics.com/modes/train/)
- [PaddleOCR Fine-tuning Guide](https://timchan.me/blog/finetune-paddleocr-text-recognition.html)
- [PP-OCRv5 Documentation](https://paddlepaddle.github.io/PaddleOCR/main/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html)
- [DocLayout-YOLO GitHub](https://github.com/opendatalab/DocLayout-YOLO)

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2025-12-31
