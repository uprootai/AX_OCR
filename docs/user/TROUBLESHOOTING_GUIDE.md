# 트러블슈팅 가이드

**작성일**: 2025-11-03
**대상**: 개발자 및 시스템 관리자
**버전**: v1.0

---

## 📋 목차

1. [일반적인 문제](#1-일반적인-문제)
2. [학습 관련 문제](#2-학습-관련-문제)
3. [API 서버 문제](#3-api-서버-문제)
4. [Docker 관련 문제](#4-docker-관련-문제)
5. [성능 문제](#5-성능-문제)
6. [데이터 관련 문제](#6-데이터-관련-문제)
7. [GPU 관련 문제](#7-gpu-관련-문제)

---

## 1. 일반적인 문제

### 1.1. Python 버전 불일치

**증상**:
```
ERROR: Python 3.12 is not supported
```

**원인**: Ultralytics는 Python 3.8-3.11만 지원

**해결**:
```bash
# pyenv로 Python 3.10 설치
pyenv install 3.10.12
pyenv local 3.10.12

# 또는 conda 사용
conda create -n yolo python=3.10
conda activate yolo
```

---

### 1.2. 의존성 충돌

**증상**:
```
ERROR: Cannot install ultralytics and opencv-python
```

**해결**:
```bash
# 가상환경 재생성
rm -rf venv
python3.10 -m venv venv
source venv/bin/activate

# 순서대로 설치
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install ultralytics
```

---

### 1.3. 권한 문제

**증상**:
```bash
Permission denied: '/home/uproot/ax/poc/datasets'
```

**해결**:
```bash
# 디렉토리 권한 확인
ls -la datasets/

# 권한 부여
chmod -R 755 datasets/
chown -R $USER:$USER datasets/
```

---

## 2. 학습 관련 문제

### 2.1. CUDA Out of Memory

**증상**:
```
RuntimeError: CUDA out of memory. Tried to allocate 1.5 GB
```

**원인**: GPU VRAM 부족

**해결 1: 배치 크기 줄이기**
```bash
python scripts/train_yolo.py \
    --batch 8 \  # 16 → 8로 줄임
    --imgsz 1280  # 또는 이미지 크기 줄이기
```

**해결 2: 작은 모델 사용**
```bash
python scripts/train_yolo.py \
    --model-size n  # nano 사용 (n < s < m < l)
```

**해결 3: CPU 학습**
```bash
python scripts/train_yolo.py \
    --device cpu
```

---

### 2.2. 학습이 너무 느림

**증상**: 1 epoch에 30분 이상 소요

**확인**:
```python
import torch
print(torch.cuda.is_available())  # True여야 함
print(torch.cuda.get_device_name(0))
```

**해결 1: GPU 사용 확인**
```bash
# GPU 사용 중인지 확인
nvidia-smi

# GPU 강제 사용
python scripts/train_yolo.py --device 0
```

**해결 2: 데이터 로딩 최적화**
```bash
python scripts/train_yolo.py \
    --workers 8  # CPU 코어 수에 맞게 조정
```

---

### 2.3. 학습 중 중단

**증상**: 학습 중 갑자기 멈춤

**원인 1: Timeout**

**해결**:
```bash
# 체크포인트에서 재개
python scripts/train_yolo.py \
    --resume runs/train/engineering_drawings/weights/last.pt
```

**원인 2: 디스크 공간 부족**

**해결**:
```bash
# 디스크 공간 확인
df -h

# 불필요한 파일 삭제
rm -rf runs/detect/exp*  # 이전 추론 결과 삭제
```

---

### 2.4. Loss가 감소하지 않음

**증상**: Loss가 계속 일정하거나 증가

**원인**: 학습률이 너무 크거나 작음

**해결**:
```bash
# 학습률 조정
python scripts/train_yolo.py \
    --lr0 0.0001  # 기본값 0.001보다 작게
```

**원인 2: 데이터 문제**

**확인**:
```bash
# 데이터셋 확인
python -c "
from ultralytics import YOLO
model = YOLO('yolo11n.pt')
model.val(data='datasets/synthetic_random/data.yaml')
"
```

---

### 2.5. mAP가 낮음

**증상**: mAP50 < 0.3

**해결 1: 더 많은 데이터**
```bash
# 합성 데이터 10,000장 생성
python scripts/generate_synthetic_random.py --count 10000
```

**해결 2: 더 긴 학습**
```bash
python scripts/train_yolo.py --epochs 200
```

**해결 3: 더 큰 모델**
```bash
python scripts/train_yolo.py --model-size m
```

---

## 3. API 서버 문제

### 3.1. 포트 이미 사용 중

**증상**:
```
ERROR: Port 5005 is already in use
```

**확인**:
```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :5005

# 또는
sudo netstat -tulpn | grep 5005
```

**해결 1: 프로세스 종료**
```bash
# PID 확인 후 종료
kill -9 <PID>
```

**해결 2: 다른 포트 사용**
```bash
# 환경변수 설정
export YOLO_API_PORT=5006
python yolo-api/api_server.py
```

---

### 3.2. 모델 파일 없음

**증상**:
```
FileNotFoundError: Model file not found: /app/models/best.pt
```

**해결**:
```bash
# 학습된 모델 복사
mkdir -p yolo-api/models
cp runs/train/engineering_drawings/weights/best.pt yolo-api/models/

# 또는 심볼릭 링크
ln -s $(pwd)/runs/train/engineering_drawings/weights/best.pt yolo-api/models/best.pt
```

---

### 3.3. API 응답 없음

**증상**: 요청 후 응답이 없음 (타임아웃)

**확인**:
```bash
# API 서버 로그 확인
tail -f yolo-api/api.log

# 또는 Docker 로그
docker logs -f yolo-api
```

**해결**:
```bash
# 타임아웃 증가
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@drawing.jpg" \
  --max-time 300  # 5분
```

---

### 3.4. 파일 업로드 실패

**증상**:
```json
{
  "error": "FILE_TOO_LARGE"
}
```

**해결 1: 이미지 크기 줄이기**
```bash
# ImageMagick 사용
convert input.jpg -resize 1920x1080 output.jpg

# Python
from PIL import Image
img = Image.open('input.jpg')
img.thumbnail((1920, 1080))
img.save('output.jpg')
```

**해결 2: 서버 설정 변경**
```python
# yolo-api/api_server.py
app.add_middleware(
    CORSMiddleware,
    max_upload_size=50 * 1024 * 1024  # 50MB
)
```

---

## 4. Docker 관련 문제

### 4.1. Docker 이미지 빌드 실패

**증상**:
```
ERROR: failed to solve: process "/bin/sh -c pip install ..." did not complete
```

**해결**:
```bash
# 캐시 없이 재빌드
docker build --no-cache -t yolo-api yolo-api/

# 또는 buildkit 사용
DOCKER_BUILDKIT=1 docker build -t yolo-api yolo-api/
```

---

### 4.2. 컨테이너가 즉시 종료됨

**증상**:
```bash
docker ps  # 컨테이너가 목록에 없음
```

**확인**:
```bash
# 로그 확인
docker logs yolo-api

# 모든 컨테이너 확인 (종료된 것 포함)
docker ps -a
```

**해결**:
```bash
# 인터랙티브 모드로 실행
docker run -it yolo-api /bin/bash

# 문제 확인 후 재시작
docker restart yolo-api
```

---

### 4.3. Docker Compose 실행 실패

**증상**:
```
ERROR: Network ax_poc_network not found
```

**해결**:
```bash
# 네트워크 생성
docker network create ax_poc_network

# 또는 전체 재시작
docker-compose down
docker-compose up -d
```

---

### 4.4. 볼륨 마운트 문제

**증상**: 컨테이너 내에서 모델 파일 접근 불가

**해결**:
```bash
# 절대 경로 사용
docker run -v $(pwd)/yolo-api/models:/app/models:ro yolo-api

# 권한 확인
ls -la yolo-api/models/

# SELinux가 활성화된 경우
docker run -v $(pwd)/yolo-api/models:/app/models:ro,z yolo-api
```

---

## 5. 성능 문제

### 5.1. 추론이 너무 느림

**증상**: 1장당 10초 이상 소요

**확인**:
```python
import torch
print(torch.cuda.is_available())
print(torch.__version__)
```

**해결 1: GPU 사용**
```bash
# GPU 강제 사용
python scripts/inference_yolo.py \
    --model best.pt \
    --source test.jpg \
    --device 0
```

**해결 2: 이미지 크기 줄이기**
```bash
python scripts/inference_yolo.py \
    --imgsz 640  # 1280 → 640
```

**해결 3: Half precision (FP16)**
```bash
python scripts/inference_yolo.py \
    --half  # GPU만 지원
```

---

### 5.2. 메모리 부족

**증상**:
```
MemoryError: Unable to allocate array
```

**해결 1: 배치 처리 줄이기**
```python
# inference_yolo.py 수정
for img_path in image_list:
    results = model.predict(img_path)  # 한 장씩
    # 처리 후 메모리 해제
    del results
    torch.cuda.empty_cache()
```

**해결 2: Swap 메모리 증가**
```bash
# Linux
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 6. 데이터 관련 문제

### 6.1. 합성 데이터 생성 실패

**증상**:
```
OSError: cannot open resource
```

**원인**: 폰트 파일 없음

**해결**:
```bash
# 시스템 폰트 설치
sudo apt-get install fonts-dejavu fonts-liberation

# 또는 폰트 다운로드
wget https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.tar.bz2
tar -xvf dejavu-fonts-ttf-2.37.tar.bz2
cp dejavu-fonts-ttf-2.37/ttf/*.ttf ~/.fonts/
fc-cache -f -v
```

---

### 6.2. 라벨 형식 오류

**증상**:
```
ValueError: Invalid YOLO label format
```

**확인**:
```bash
# 라벨 파일 확인
head datasets/synthetic_random/labels/train/synthetic_train_000000.txt
```

**예상 형식**:
```
0 0.5234 0.6123 0.0345 0.0234
1 0.3456 0.7890 0.0456 0.0345
```

**해결**:
```bash
# 라벨 재생성
python scripts/generate_synthetic_random.py --count 100
```

---

### 6.3. 데이터셋 병합 실패

**증상**:
```
FileNotFoundError: data.yaml not found
```

**해결**:
```bash
# 각 데이터셋에 data.yaml이 있는지 확인
ls datasets/synthetic_random/data.yaml
ls datasets/engineering_drawings/data.yaml

# 없으면 생성
python scripts/prepare_dataset.py
```

---

## 7. GPU 관련 문제

### 7.1. CUDA 버전 불일치

**증상**:
```
RuntimeError: CUDA version mismatch
```

**확인**:
```bash
# CUDA 버전 확인
nvcc --version
nvidia-smi  # Driver version

# PyTorch CUDA 버전
python -c "import torch; print(torch.version.cuda)"
```

**해결**:
```bash
# PyTorch 재설치 (CUDA 11.8 기준)
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

---

### 7.2. GPU 인식 안 됨

**증상**:
```python
torch.cuda.is_available()  # False
```

**확인**:
```bash
# NVIDIA 드라이버 확인
nvidia-smi

# CUDA 라이브러리 확인
ls /usr/local/cuda*/lib64/libcudart.so*
```

**해결 1: 드라이버 재설치**
```bash
# Ubuntu
sudo apt-get purge nvidia*
sudo apt-get install nvidia-driver-535  # 최신 버전

# 재부팅
sudo reboot
```

**해결 2: LD_LIBRARY_PATH 설정**
```bash
export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda-11.8/bin:$PATH
```

---

### 7.3. 다중 GPU 문제

**증상**: GPU 0번만 사용됨

**해결 1: 특정 GPU 선택**
```bash
# GPU 1번 사용
CUDA_VISIBLE_DEVICES=1 python scripts/train_yolo.py --device 0

# GPU 0,1번 사용
python scripts/train_yolo.py --device 0,1
```

**해결 2: DDP (DistributedDataParallel)**
```bash
# 멀티 GPU 학습
python -m torch.distributed.run \
    --nproc_per_node=2 \
    scripts/train_yolo.py \
    --device 0,1
```

---

## 🔍 디버깅 팁

### 1. 로그 레벨 설정

```bash
# 상세 로그
export YOLO_VERBOSE=1
python scripts/train_yolo.py

# Python logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 프로파일링

```python
import torch
from torch.profiler import profile, ProfilerActivity

with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
    results = model.predict("test.jpg")

print(prof.key_averages().table(sort_by="cuda_time_total"))
```

### 3. 메모리 추적

```python
import torch

# GPU 메모리 확인
print(torch.cuda.memory_allocated() / 1024**3, "GB")
print(torch.cuda.memory_reserved() / 1024**3, "GB")

# 메모리 요약
print(torch.cuda.memory_summary())
```

---

## 📞 추가 지원

문제가 해결되지 않는 경우:

1. **GitHub Issues**: 프로젝트 이슈 등록
2. **로그 수집**: 전체 에러 로그 첨부
3. **환경 정보**: Python/CUDA/GPU 정보 제공
4. **재현 방법**: 문제 재현 단계 상세히 기술

**문의**:
- 이메일: dev@uproot.com
- 내부 Slack: #ax-support

---

**작성자**: AX 실증사업팀
**최종 업데이트**: 2025-11-03
