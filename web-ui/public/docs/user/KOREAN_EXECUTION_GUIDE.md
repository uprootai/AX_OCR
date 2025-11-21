# AX 실증산단 시스템 통합 실행 가이드

**작성일**: 2025-11-03
**대상**: 개발자 및 운영자
**목적**: YOLOv11 기반 공학 도면 분석 시스템의 완벽한 실행 가이드

---

## 📋 목차

1. [시스템 요구사항](#1-시스템-요구사항)
2. [초기 설정](#2-초기-설정)
3. [YOLOv11 학습 실행 (권장)](#3-yolov11-학습-실행-권장)
4. [API 서버 실행](#4-api-서버-실행)
5. [통합 시스템 실행](#5-통합-시스템-실행)
6. [성능 평가](#6-성능-평가)
7. [실전 사용 예제](#7-실전-사용-예제)

---

## 1. 시스템 요구사항

### 하드웨어
- **GPU (권장)**: NVIDIA RTX 3060 이상 (VRAM 6GB+)
- **CPU (최소)**: Intel Core i5 이상, 8코어 권장
- **RAM**: 16GB 이상 (32GB 권장)
- **디스크**: 50GB 이상 여유 공간

### 소프트웨어
- **OS**: Ubuntu 20.04+ / Windows 10+ (WSL2) / macOS
- **Python**: 3.8 ~ 3.11 (3.10 권장)
- **Docker**: 20.10+ (선택사항)
- **CUDA**: 11.8+ (GPU 사용 시)

### 확인 방법
```bash
# Python 버전 확인
python3 --version

# GPU 확인 (NVIDIA)
nvidia-smi

# Docker 확인
docker --version
docker-compose --version

# CUDA 확인
nvcc --version
```

---

## 2. 초기 설정

### Step 1: 프로젝트 클론 및 이동
```bash
cd /home/uproot/ax/poc
```

### Step 2: Python 가상환경 생성 (권장)
```bash
# 가상환경 생성
python3 -m venv venv

# 활성화
source venv/bin/activate  # Linux/macOS
# 또는
venv\Scripts\activate  # Windows
```

### Step 3: 의존성 설치
```bash
# YOLOv11 학습용 (Ultralytics)
pip install ultralytics pyyaml pillow opencv-python tqdm

# API 서버용
pip install fastapi uvicorn python-multipart

# 추가 도구
pip install matplotlib seaborn pandas numpy
```

### Step 4: 디렉토리 구조 확인
```bash
ls -la
```

**예상 출력**:
```
edocr2-api/
edgnet-api/
skinmodel-api/
gateway-api/
yolo-api/
scripts/
datasets/
YOLOV11_QUICKSTART.md
SYNTHETIC_DATA_QUICKSTART.md
README.md
```

---

## 3. YOLOv11 학습 실행 (권장)

### 🎯 방법 A: 전체 자동화 파이프라인 (가장 간단) ⭐

**한 줄 명령어로 전체 실행**:
```bash
./scripts/train_with_synthetic.sh
```

**이 명령이 하는 일**:
1. 합성 데이터 1,000장 자동 생성 (~3분)
2. 실제 데이터 확인 및 병합 (있으면)
3. YOLOv11n 모델 학습 (100 epochs, ~1-2시간 GPU)
4. 성능 평가 및 결과 출력

**예상 소요 시간**:
- GPU (RTX 3080): 1.5 ~ 2시간
- GPU (RTX 3060): 2 ~ 3시간
- CPU (16코어): 8 ~ 12시간

**예상 성능**:
- F1 Score: 60-70% (합성 데이터만)
- F1 Score: 75-85% (합성 + 실제 100장)

---

### 🎯 방법 B: 단계별 실행 (커스터마이징 필요시)

#### Step 1: 합성 데이터 생성
```bash
# 1,000장 생성 (기본)
python scripts/generate_synthetic_random.py \
    --count 1000 \
    --output datasets/synthetic_random \
    --width 1920 \
    --height 1080
```

**생성 옵션**:
```bash
# 대량 생성 (10,000장, ~30분)
python scripts/generate_synthetic_random.py --count 10000

# 테스트용 소량 (100장, ~20초)
python scripts/generate_synthetic_random.py --count 100

# 고해상도 (2560x1440)
python scripts/generate_synthetic_random.py \
    --count 1000 \
    --width 2560 \
    --height 1440
```

**생성 결과 확인**:
```bash
# 생성된 이미지 개수 확인
ls datasets/synthetic_random/images/train/ | wc -l

# 라벨 확인
head datasets/synthetic_random/labels/train/synthetic_train_000000.txt

# 통계 확인
cat datasets/synthetic_random/dataset_stats.json
```

#### Step 2: (선택) 실제 데이터 추가
```bash
# eDOCr 데이터가 있으면 YOLO 형식으로 변환
python scripts/prepare_dataset.py

# 합성 + 실제 데이터 병합
python scripts/merge_datasets.py \
    --datasets datasets/synthetic_random datasets/engineering_drawings \
    --output datasets/combined
```

#### Step 3: 모델 학습
```bash
# 기본 학습 (nano 모델, 100 epochs)
python scripts/train_yolo.py \
    --model-size n \
    --data datasets/synthetic_random/data.yaml \
    --epochs 100 \
    --batch 16 \
    --device 0

# 고성능 학습 (medium 모델, 200 epochs)
python scripts/train_yolo.py \
    --model-size m \
    --data datasets/combined/data.yaml \
    --epochs 200 \
    --batch 8 \
    --imgsz 1920 \
    --device 0
```

**학습 파라미터 설명**:
- `--model-size`: n (nano), s (small), m (medium), l (large)
- `--epochs`: 학습 반복 횟수 (100-200 권장)
- `--batch`: 배치 크기 (GPU VRAM에 따라 조정)
- `--imgsz`: 입력 이미지 크기 (1280/1920/2560)
- `--device`: GPU 번호 (0, 1, ...) 또는 cpu

**학습 모니터링**:
```bash
# 실시간 로그 확인
tail -f runs/train/engineering_drawings/train.log

# TensorBoard (선택)
tensorboard --logdir runs/train
```

#### Step 4: 모델 평가
```bash
# 테스트셋 평가
python scripts/evaluate_yolo.py \
    --model runs/train/engineering_drawings/weights/best.pt \
    --data datasets/synthetic_random/data.yaml \
    --split test \
    --device 0

# 결과 확인
cat runs/train/engineering_drawings/evaluation_results.json
```

#### Step 5: 추론 테스트
```bash
# 이미지 폴더에 대한 추론
python scripts/inference_yolo.py \
    --model runs/train/engineering_drawings/weights/best.pt \
    --source test_images/ \
    --conf 0.25 \
    --save

# 단일 이미지 추론
python scripts/inference_yolo.py \
    --model runs/train/engineering_drawings/weights/best.pt \
    --source drawing.jpg \
    --visualize
```

---

### 🎯 방법 C: 프로토타입 빠른 테스트 (사전학습 모델)

실제 학습 없이 사전학습된 YOLO 모델로 빠른 테스트:

```bash
# 프로토타입 테스트 스크립트 실행
python test_yolo_prototype.py
```

**예상 결과**:
- F1 Score: 40-50% (사전학습 COCO 가중치)
- 즉시 실행 가능 (학습 불필요)
- 시스템 동작 검증용

---

## 4. API 서버 실행

### 방법 A: YOLOv11 API만 실행 (개발/테스트용)

```bash
cd yolo-api

# 학습된 모델 복사
mkdir -p models
cp ../runs/train/engineering_drawings/weights/best.pt models/

# 의존성 설치
pip install -r requirements.txt

# API 서버 실행
python api_server.py
```

**확인**:
```bash
# 헬스체크
curl http://localhost:5005/api/v1/health

# Swagger UI 접속
open http://localhost:5005/docs
```

### 방법 B: Docker로 실행

```bash
cd yolo-api

# Docker 이미지 빌드
docker build -t yolo-api .

# 컨테이너 실행
docker run -d \
    -p 5005:5005 \
    -v $(pwd)/models:/app/models:ro \
    --name yolo-api \
    yolo-api

# 로그 확인
docker logs -f yolo-api
```

### API 테스트

```bash
# 객체 검출 API
curl -X POST http://localhost:5005/api/v1/detect \
    -F "file=@test_drawing.jpg" \
    -F "conf_threshold=0.25" \
    -F "visualize=true"

# 치수 추출 API
curl -X POST http://localhost:5005/api/v1/extract_dimensions \
    -F "file=@test_drawing.jpg" \
    -F "conf_threshold=0.3"
```

**예상 응답**:
```json
{
  "status": "success",
  "data": {
    "detections": [
      {
        "class": "diameter_dim",
        "confidence": 0.87,
        "bbox": [120, 340, 180, 365],
        "text": "φ476"
      },
      {
        "class": "linear_dim",
        "confidence": 0.92,
        "bbox": [450, 220, 490, 245],
        "text": "120"
      }
    ],
    "total_detections": 23,
    "processing_time": 2.3
  }
}
```

---

## 5. 통합 시스템 실행

### 전체 마이크로서비스 실행 (Docker Compose)

```bash
cd /home/uproot/ax/poc

# 전체 시스템 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 확인
docker-compose logs -f yolo-api

# 서비스 상태 확인
docker-compose ps
```

**실행되는 서비스**:
- Gateway API: http://localhost:8000 (통합 오케스트레이션)
- YOLOv11 API: http://localhost:5005 (객체 검출, GPU)
- eDOCr2 v1 API: http://localhost:5001 (한글 OCR Fast, GPU)
- eDOCr2 v2 API: http://localhost:5002 (한글 OCR Advanced, GPU)
- PaddleOCR API: http://localhost:5006 (다국어 OCR, GPU)
- EDGNet API: http://localhost:5012 (도면 세그멘테이션, GPU)
- Skin Model API: http://localhost:5003 (공차 예측)
- VL API: http://localhost:5004 (멀티모달 분석)

### 통합 시스템 테스트

```bash
# Gateway를 통한 전체 파이프라인 실행
curl -X POST http://localhost:8000/api/v1/process \
    -F "file=@drawing.pdf" \
    -F "use_yolo=true" \
    -F "generate_quote=true"
```

### 시스템 중지

```bash
# 전체 중지
docker-compose down

# 전체 중지 + 볼륨 삭제
docker-compose down -v
```

---

## 6. 성능 평가

### 학습된 모델 평가

```bash
# 전체 평가
python scripts/evaluate_yolo.py \
    --model runs/train/engineering_drawings/weights/best.pt \
    --data datasets/synthetic_random/data.yaml \
    --split test

# 클래스별 평가
python scripts/evaluate_yolo.py \
    --model runs/train/engineering_drawings/weights/best.pt \
    --data datasets/synthetic_random/data.yaml \
    --split test \
    --per-class
```

**평가 지표 설명**:
- **Precision (정밀도)**: 검출한 것 중 실제 정답 비율
- **Recall (재현율)**: 실제 정답 중 검출한 비율
- **F1 Score**: Precision과 Recall의 조화평균 (핵심 지표)
- **mAP50**: IoU 0.5 기준 평균 정밀도
- **mAP50-95**: IoU 0.5~0.95 범위의 평균 정밀도

### 예상 성능 로드맵

| 단계 | 데이터 구성 | F1 Score | 상태 |
|------|------------|----------|------|
| Phase 0 | 프로토타입 (사전학습) | 40-50% | 즉시 사용 |
| Phase 1 | 합성 1,000장 | 60-70% | 실용 가능 ✅ |
| Phase 2 | 합성 1,000 + 실제 100 | 75-85% | **권장** ✅✅ |
| Phase 3 | 합성 10,000 + 실제 500 | 85-95% | 프로덕션 ✅✅✅ |

### vs 기존 eDOCr 성능 비교

```
eDOCr v1:     8.3%   ████░░░░░░░░░░░░░░░░ (실패)
                            ↓
YOLO (합성):  65%    █████████████░░░░░░░ (8배 향상)
                            ↓
YOLO (최적): 80%     ████████████████░░░░ (10배 향상)
```

---

## 7. 실전 사용 예제

### 예제 1: 도면 1장 빠른 분석

```bash
# 1. 이미지 추론
python scripts/inference_yolo.py \
    --model runs/train/engineering_drawings/weights/best.pt \
    --source my_drawing.jpg \
    --save \
    --visualize

# 2. 결과 확인
ls runs/detect/exp/
# my_drawing.jpg (바운딩박스 포함 이미지)
# labels/my_drawing.txt (검출 결과 YOLO 형식)
```

### 예제 2: 배치 처리 (폴더 내 모든 도면)

```bash
# drawings/ 폴더 내 모든 이미지 처리
python scripts/inference_yolo.py \
    --model runs/train/engineering_drawings/weights/best.pt \
    --source drawings/ \
    --conf 0.3 \
    --save

# 결과는 runs/detect/exp2/ 에 저장
```

### 예제 3: API를 통한 웹 서비스 연동

```python
import requests

# API 엔드포인트
url = "http://localhost:5005/api/v1/detect"

# 도면 이미지 업로드
files = {"file": open("drawing.jpg", "rb")}
data = {
    "conf_threshold": 0.25,
    "visualize": True
}

# 요청
response = requests.post(url, files=files, data=data)
result = response.json()

# 결과 처리
print(f"검출된 객체: {result['data']['total_detections']}개")
for det in result['data']['detections']:
    print(f"  - {det['class']}: {det['text']} (신뢰도: {det['confidence']:.2f})")
```

### 예제 4: Gateway를 통한 전체 워크플로우

```bash
# 도면 업로드 → 분석 → 견적 생성
curl -X POST http://localhost:8000/api/v1/process \
    -F "file=@engineering_drawing.pdf" \
    -F "use_yolo=true" \
    -F "use_edgnet=true" \
    -F "use_skinmodel=true" \
    -F "generate_quote=true" \
    > result.json

# 결과 확인
cat result.json | jq '.data.quote.total'
```

---

## 🎯 권장 워크플로우

### Week 1: 시스템 검증
```bash
# 1. 프로토타입 테스트
python test_yolo_prototype.py

# 2. 합성 데이터 생성 및 학습
./scripts/train_with_synthetic.sh

# 3. 결과 확인
python scripts/evaluate_yolo.py --model runs/train/synthetic_training/weights/best.pt
```

**예상 결과**: F1 60-70%

### Week 2: 실제 데이터 추가
```bash
# 1. 실제 도면 100장 준비 (eDOCr 또는 수동 라벨링)
python scripts/prepare_dataset.py

# 2. 데이터 병합
python scripts/merge_datasets.py \
    --datasets datasets/synthetic_random datasets/engineering_drawings \
    --output datasets/combined

# 3. 재학습
python scripts/train_yolo.py \
    --data datasets/combined/data.yaml \
    --epochs 150
```

**예상 결과**: F1 75-85%

### Week 3: API 배포
```bash
# 1. 최적 모델 복사
cp runs/train/best_model/weights/best.pt yolo-api/models/

# 2. API 서버 실행
docker-compose up -d

# 3. 프로덕션 테스트
curl -X POST http://localhost:5005/api/v1/detect -F "file=@test.jpg"
```

---

## 📞 문제 발생 시

- **트러블슈팅 가이드**: `TROUBLESHOOTING_GUIDE.md` 참조
- **API 사용법**: `API_USAGE_MANUAL.md` 참조
- **상세 구현 가이드**: `YOLOV11_IMPLEMENTATION_GUIDE.md` 참조

---

**작성자**: AX 실증사업팀
**최종 업데이트**: 2025-11-03
