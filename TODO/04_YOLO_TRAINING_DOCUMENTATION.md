# YOLO 학습 데이터 문서화

> 작성일: 2025-11-13
> 상태: 🔴 문서 부재
> 우선순위: 🔴 Priority 1

---

## 🚨 문제 정의

### 현재 상황

**파일**: `yolo-api/api_server.py` (291-340줄)

```python
# 14개 클래스 정의
DIMENSION_CLASSES = {
    0: "diameter_dim",
    1: "linear_dim",
    2: "radius_dim",
    3: "angular_dim",
    4: "chamfer_dim",
    5: "tolerance_dim",
    6: "reference_dim",
    7: "flatness",
    8: "cylindricity",
    9: "position",
    10: "perpendicularity",
    11: "parallelism",
    12: "surface_roughness",
    13: "unclassified_text"
}

# 모델 로드
model = YOLO("yolo11n.pt")  # ← 어디서 학습했는지 불명
```

### 문제점

**❓ 알 수 없는 것들**:
1. 어떤 데이터셋으로 학습했는가?
2. 라벨링은 어떻게 했는가?
3. 학습 하이퍼파라미터는?
4. 성능 지표는?
5. 검증 방법은?
6. 재학습 가능한가?

**🚨 영향**:
- ❌ 재현 불가능
- ❌ 성능 개선 불가능
- ❌ 새로운 클래스 추가 불가능
- ❌ 데이터 편향 검증 불가능
- ❌ 버전 관리 불가능

---

## 📋 필요한 문서

### 1. 데이터셋 명세서

#### 1.1 데이터셋 기본 정보

```yaml
dataset_name: "Engineering Drawing Dimension Detection v1.0"
creation_date: "YYYY-MM-DD"
version: "1.0.0"
license: "Proprietary" or "CC-BY-4.0" etc.

description: |
  공학 도면에서 치수, GD&T, 표면 거칠기 등을 검출하기 위한 데이터셋

domain: "Mechanical Engineering Drawings"
languages: ["eng", "kor"]  # OCR 언어
```

#### 1.2 데이터 수집 정보

```yaml
data_sources:
  - type: "Real drawings"
    count: ???  # 실제 도면 몇 장?
    source: "Company internal / Public datasets / Synthetic"

  - type: "Synthetic drawings"
    count: ???
    generator: "CAD software / Drawing generator"

  - type: "Augmented samples"
    count: ???
    augmentation_methods: ["rotation", "scaling", "noise", etc.]

total_images: ???
total_annotations: ???  # 총 bbox 개수

# 도면 해상도 분포
resolution_distribution:
  - range: "1000x1000 - 2000x2000"
    count: ???
  - range: "2000x2000 - 4000x4000"
    count: ???
  - range: "4000x4000+"
    count: ???

# 파일 포맷
image_formats: ["PNG", "JPEG", "TIFF", "PDF"]
```

#### 1.3 클래스 분포

```yaml
class_distribution:
  - class_id: 0
    class_name: "diameter_dim"
    count: ???
    percentage: ???%
    description: "지름 치수 (Ø)"

  - class_id: 1
    class_name: "linear_dim"
    count: ???
    percentage: ???%
    description: "선형 치수"

  # ... 나머지 12개 클래스

# 클래스 불균형 확인
most_common_class: "???"
least_common_class: "???"
imbalance_ratio: ???  # max_count / min_count
```

#### 1.4 라벨링 정보

```yaml
labeling_tool: "LabelImg" or "Roboflow" or "CVAT" etc.
labeling_format: "YOLO" or "COCO" or "Pascal VOC"

annotation_guidelines: |
  - Bbox는 치수 기호 전체를 포함
  - 리더선(leader line)은 제외
  - 중첩된 객체는 모두 라벨링
  - ...

labelers:
  - role: "Domain expert"
    count: ???
  - role: "Trained annotator"
    count: ???

quality_control:
  - method: "Inter-annotator agreement (IoU > 0.8)"
  - method: "Expert review (random 10%)"
  - method: "Automated validation (bbox size, aspect ratio)"

estimated_labeling_time: "??? hours"
```

---

### 2. 학습 구성 문서

#### 2.1 모델 아키텍처

```yaml
model_family: "YOLO v11"
model_variant: "yolo11n"  # nano

architecture:
  backbone: "CSPDarknet"
  neck: "PANet"
  head: "YOLOv11 Detection Head"

model_parameters: "2.6M"
model_size: "5.9 MB"

input_size: [1280, 1280]  # (width, height)
num_classes: 14
```

#### 2.2 학습 하이퍼파라미터

```yaml
training:
  # 기본 설정
  epochs: ???
  batch_size: ???
  device: "cuda" or "cpu"
  workers: ???  # DataLoader workers

  # 옵티마이저
  optimizer: "SGD" or "Adam" or "AdamW"
  learning_rate: ???  # 초기 lr
  momentum: ???
  weight_decay: ???

  # 학습률 스케줄러
  lr_scheduler: "cosine" or "linear" or "step"
  warmup_epochs: ???
  warmup_momentum: ???
  warmup_bias_lr: ???

  # 정규화
  dropout: ???
  label_smoothing: ???

  # 데이터 증강
  augmentation:
    hsv_h: ???  # Hue augmentation
    hsv_s: ???  # Saturation
    hsv_v: ???  # Value
    degrees: ???  # Rotation (-??? to +???)
    translate: ???  # Translation (0.0 - 1.0)
    scale: ???  # Scale (0.0 - 1.0)
    shear: ???  # Shear
    perspective: ???  # Perspective warp
    flipud: ???  # Vertical flip probability
    fliplr: ???  # Horizontal flip probability
    mosaic: ???  # Mosaic augmentation probability
    mixup: ???  # Mixup augmentation probability

  # Loss 가중치
  box_loss_gain: ???
  cls_loss_gain: ???
  dfl_loss_gain: ???

  # Early stopping
  patience: ???  # epochs
  early_stop_metric: "mAP50" or "mAP50-95"
```

#### 2.3 데이터 분할

```yaml
dataset_split:
  train:
    count: ???
    percentage: ???%  # 일반적으로 70-80%
  validation:
    count: ???
    percentage: ???%  # 일반적으로 10-15%
  test:
    count: ???
    percentage: ???%  # 일반적으로 10-15%

split_strategy: "random" or "stratified" or "time-based"
random_seed: ???  # 재현성을 위한 시드
```

---

### 3. 성능 평가 문서

#### 3.1 평가 지표

```yaml
evaluation_metrics:
  # Detection 성능
  - metric: "mAP@0.5"
    value: ???
    description: "IoU 0.5에서의 Mean Average Precision"

  - metric: "mAP@0.5:0.95"
    value: ???
    description: "IoU 0.5~0.95 범위의 평균 mAP"

  - metric: "Precision"
    value: ???
    description: "정밀도 (TP / (TP + FP))"

  - metric: "Recall"
    value: ???
    description: "재현율 (TP / (TP + FN))"

  - metric: "F1-Score"
    value: ???
    description: "2 * (Precision * Recall) / (Precision + Recall)"

  # 속도 성능
  - metric: "Inference time (GPU)"
    value: "30-50 ms"
    device: "NVIDIA RTX 3090"

  - metric: "Inference time (CPU)"
    value: "200-500 ms"
    device: "Intel i7-12700K"

  - metric: "FPS (GPU)"
    value: ???

  - metric: "FPS (CPU)"
    value: ???
```

#### 3.2 클래스별 성능

```yaml
per_class_performance:
  - class_id: 0
    class_name: "diameter_dim"
    precision: ???
    recall: ???
    mAP50: ???
    mAP50_95: ???
    num_test_samples: ???

  - class_id: 1
    class_name: "linear_dim"
    precision: ???
    recall: ???
    mAP50: ???
    mAP50_95: ???
    num_test_samples: ???

  # ... 나머지 클래스들

# 성능 분석
best_performing_classes: ["???", "???", "???"]
worst_performing_classes: ["???", "???", "???"]
```

#### 3.3 학습 곡선

```yaml
training_history:
  # 최종 에포크 결과
  final_epoch: ???
  final_train_loss: ???
  final_val_loss: ???
  best_epoch: ???  # mAP 기준

  # 학습 안정성
  overfitting: "Yes" or "No"
  converged: "Yes" or "No"

  # 학습 로그 파일 위치
  tensorboard_logs: "path/to/runs/detect/train"
  weights_best: "path/to/best.pt"
  weights_last: "path/to/last.pt"
```

---

### 4. 모델 버전 관리

#### 4.1 체크섬 및 식별

```yaml
model_file: "yolo11n.pt"
file_size: "5.9 MB"
md5_checksum: "???"  # md5sum yolo11n.pt
sha256_checksum: "???"  # sha256sum yolo11n.pt

git_commit: "???"  # 학습 시점의 코드 커밋 해시
training_date: "YYYY-MM-DD"
trainer: "???"  # 누가 학습했는지
```

#### 4.2 의존성

```yaml
dependencies:
  - package: "ultralytics"
    version: "8.0.0"
    note: "YOLOv11 requires ultralytics >= 8.0.0"

  - package: "torch"
    version: "2.0.0+"
    note: "PyTorch 2.0+ for CUDA 11.8"

  - package: "torchvision"
    version: "0.15.0+"

  - package: "opencv-python"
    version: "4.8.0+"

  - package: "pillow"
    version: "10.0.0+"
```

---

## 🔍 정보 수집 방법

### 방법 1: 학습 스크립트 역추적

```bash
# YOLO 학습 스크립트 찾기
find /home/uproot/ax -name "train*.py" -o -name "*yolo*train*"

# 학습 관련 노트북 찾기
find /home/uproot/ax -name "*.ipynb" | xargs grep -l "yolo.*train"

# 설정 파일 찾기
find /home/uproot/ax -name "data.yaml" -o -name "hyp*.yaml" -o -name "config*.yaml"
```

### 방법 2: 모델 파일 메타데이터 추출

```python
from ultralytics import YOLO

model = YOLO("yolo11n.pt")

# 모델 정보 추출
print("Model info:")
print(f"  Task: {model.task}")
print(f"  Model type: {model.type}")
print(f"  Num classes: {len(model.names)}")
print(f"  Class names: {model.names}")

# 학습 메타데이터 (있는 경우)
if hasattr(model.model, "args"):
    print(f"  Training args: {model.model.args}")

# 체크포인트 정보
import torch
ckpt = torch.load("yolo11n.pt", map_location="cpu")
print("\nCheckpoint keys:")
for key in ckpt.keys():
    print(f"  {key}: {type(ckpt[key])}")

# 학습 메타데이터
if "train_args" in ckpt:
    print("\nTraining arguments:")
    for k, v in ckpt["train_args"].items():
        print(f"  {k}: {v}")
```

### 방법 3: Git 히스토리 조사

```bash
# Git 로그에서 YOLO 관련 커밋 찾기
cd /home/uproot/ax/poc
git log --all --grep="yolo" --grep="train" --grep="dataset" -i

# 모델 파일 추가 시점 찾기
git log --all -- "**/*.pt" "**/*yolo*"

# 특정 파일의 변경 이력
git log -p -- yolo-api/api_server.py
```

### 방법 4: 문서 및 주석 수집

```bash
# README, docs 찾기
find /home/uproot/ax/poc -name "README*" -o -name "TRAIN*" -o -name "DATA*"

# Python 파일에서 주석 추출
grep -r "dataset\|training\|hyperparameter" yolo-api/ --include="*.py"
```

---

## 📝 작성할 파일 목록

### 필수 문서 (Priority 1)

1. **`yolo-api/docs/DATASET.md`**
   - 데이터셋 명세서
   - 클래스 분포
   - 라벨링 가이드라인

2. **`yolo-api/docs/TRAINING.md`**
   - 학습 하이퍼파라미터
   - 데이터 분할
   - 재학습 스크립트

3. **`yolo-api/docs/EVALUATION.md`**
   - 성능 지표
   - 클래스별 성능
   - 테스트 결과

4. **`yolo-api/docs/MODEL_VERSIONING.md`**
   - 모델 체크섬
   - 의존성
   - 변경 이력

### 부가 파일 (Priority 2)

5. **`yolo-api/train.py`**
   - 재학습 스크립트
   - 인자 파싱
   - 학습 로깅

6. **`yolo-api/data.yaml`**
   - YOLO 데이터셋 설정 파일
   - 클래스 이름 매핑
   - 경로 설정

7. **`yolo-api/hyp.yaml`**
   - 하이퍼파라미터 설정 파일
   - Ultralytics 표준 포맷

---

## 🎯 작업 계획

### Phase 1: 정보 수집 (2-4시간)

1. 프로젝트 디렉토리 전체 검색
2. 모델 파일 메타데이터 추출
3. Git 히스토리 조사
4. 기존 문서 수집

### Phase 2: 문서 작성 (4-6시간)

1. 수집된 정보 정리
2. 추정치 계산 (알 수 없는 정보)
3. 4개 필수 문서 작성
4. 코드 주석 업데이트

### Phase 3: 재학습 준비 (4-6시간)

1. `train.py` 스크립트 작성
2. `data.yaml` 생성
3. `hyp.yaml` 생성
4. 재학습 가이드 작성

### Phase 4: 검증 (2-3시간)

1. 재학습 스크립트 테스트 (작은 데이터셋)
2. 문서 리뷰
3. 체크섬 검증
4. CI/CD 통합

**총 예상 소요**: 12-19시간 (약 1.5-2.5일)

---

## 📋 체크리스트

- [ ] 정보 수집
  - [ ] 학습 스크립트 찾기
  - [ ] 모델 메타데이터 추출
  - [ ] Git 히스토리 조사
  - [ ] 기존 문서 수집

- [ ] 문서 작성
  - [ ] `DATASET.md` 작성
  - [ ] `TRAINING.md` 작성
  - [ ] `EVALUATION.md` 작성
  - [ ] `MODEL_VERSIONING.md` 작성

- [ ] 재학습 준비
  - [ ] `train.py` 작성
  - [ ] `data.yaml` 생성
  - [ ] `hyp.yaml` 생성
  - [ ] 재학습 가이드 작성

- [ ] 검증
  - [ ] 재학습 테스트
  - [ ] 문서 리뷰
  - [ ] 체크섬 검증
  - [ ] CI/CD 통합

---

## 🔗 관련 리소스

### Ultralytics 공식 문서

- [YOLOv11 Training](https://docs.ultralytics.com/modes/train/)
- [Custom Dataset](https://docs.ultralytics.com/datasets/)
- [Hyperparameter Tuning](https://docs.ultralytics.com/guides/hyperparameter-tuning/)

### 데이터셋 예시

- [Roboflow - Engineering Drawings](https://roboflow.com/)
- [YOLO Format Specification](https://docs.ultralytics.com/datasets/detect/)

---

## 🚧 경고

### 정보 부재 시 대응

**데이터셋 정보를 찾을 수 없는 경우**:
1. ⚠️ 현재 모델은 "블랙박스"로 간주
2. ⚠️ 재학습 불가능 → 모델 개선 불가능
3. ⚠️ 새 데이터셋으로 재학습 필요
4. ⚠️ 라벨링부터 다시 시작

**권장 사항**:
- 🔴 **즉시 문서화 프로세스 수립**
- 🔴 **현재부터 모든 학습 기록 보관**
- 🔴 **모델 레지스트리 도입 (MLflow, W&B)**

---

**다음 단계**: 정보 수집 시작 → `yolo-api/` 디렉토리 조사

**관련 문서**:
- `01_CURRENT_STATUS_OVERVIEW.md`: 전체 시스템 현황
- `08_LONG_TERM_IMPROVEMENTS.md`: 모델 레지스트리 도입
