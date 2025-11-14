# 🟢 우선순위 3-1: GPU 하드웨어 설정

**목적**: 처리 시간 45초 → 10-15초로 단축 (3-4배 향상)
**소요 시간**: 1-2일
**비용**: 하드웨어 의존 (기존 GPU 활용 시 $0)

---

## 📋 현재 상태

### 처리 시간
| 작업 | CPU | GPU (예상) | 개선 |
|------|-----|-----------|------|
| EDGNet 세그멘테이션 | 45초 | 12초 | 3.8배 |
| eDOCr2 OCR | 23초 | 8초 | 2.9배 |
| 전체 파이프라인 | 70초 | 20초 | 3.5배 |

---

## ✅ GPU 요구사항

### 최소 사양
- **GPU**: NVIDIA GTX 1060 (6GB) 이상
- **CUDA**: 11.0+
- **cuDNN**: 8.0+
- **VRAM**: 6GB+

### 권장 사양
- **GPU**: NVIDIA RTX 3060 (12GB) 이상
- **CUDA**: 11.8+
- **cuDNN**: 8.9+
- **VRAM**: 12GB+

---

## 🔍 GPU 확인

### 1단계: GPU 존재 확인

```bash
# NVIDIA GPU 확인
lspci | grep -i nvidia

# 예상 출력:
# 01:00.0 VGA compatible controller: NVIDIA Corporation ...
```

### 2단계: NVIDIA 드라이버 확인

```bash
nvidia-smi

# 예상 출력:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.60.11    Driver Version: 525.60.11    CUDA Version: 12.0     |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
```

**GPU 없는 경우**: `TODO/PRIORITY_3_GPU_ALTERNATIVES.md` 참조

---

## 🔧 설치 작업

### 옵션 A: 드라이버 이미 설치됨

**확인**:
```bash
nvidia-smi  # 정상 출력되면 OK
docker run --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**결과**: ✅ Skip to Docker GPU 설정

### 옵션 B: 드라이버 설치 필요

#### Ubuntu/Debian
```bash
# 1. 기존 드라이버 제거 (있다면)
sudo apt-get purge nvidia-*
sudo apt-get autoremove

# 2. 드라이버 설치
sudo apt-get update
sudo apt-get install -y nvidia-driver-525

# 3. 재부팅
sudo reboot

# 4. 확인
nvidia-smi
```

#### Docker NVIDIA Runtime 설치
```bash
# 1. NVIDIA Docker 런타임 설치
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2

# 2. Docker 재시작
sudo systemctl restart docker

# 3. 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

## 🐳 Docker GPU 설정

### docker-compose.yml 수정

```bash
# (Claude가 자동으로 수정함)
# GPU 지원 추가됨
```

### 개별 서비스 GPU 할당

**EDGNet API** (가장 느림, 최우선):
```yaml
edgnet-api:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

**eDOCr2 API** (두 번째 우선):
```yaml
edocr2-api-v1:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

---

## 🧪 GPU 테스트

### 1. PyTorch GPU 확인

```bash
docker exec -it edgnet-api python3 << 'PYEOF'
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
PYEOF

# 예상 출력:
# CUDA available: True
# CUDA version: 11.8
# GPU count: 1
# GPU name: NVIDIA GeForce RTX 3060
```

### 2. 모델 GPU 로딩 확인

```bash
# EDGNet API 로그 확인
docker-compose logs edgnet-api | grep -i "cuda\|gpu"

# 예상 출력:
# Model loaded on device: cuda:0
# GPU memory allocated: 2048 MB
```

### 3. 성능 벤치마크

```bash
# GPU 활성화 전/후 비교
python TODO/scripts/benchmark_gpu.py

# 예상 결과:
# CPU: 45.2s
# GPU: 11.8s
# Speedup: 3.8x
```

---

## 📊 성공 기준

### 최소 요구사항
- [ ] nvidia-smi 정상 작동
- [ ] Docker GPU 접근 가능
- [ ] PyTorch CUDA available: True
- [ ] 처리 시간 30% 이상 단축

### 이상적 목표
- [ ] EDGNet: 45s → 12s
- [ ] eDOCr2: 23s → 8s
- [ ] 전체: 70s → 20s

---

## 🚨 트러블슈팅

### nvidia-smi: command not found
```bash
# 드라이버 미설치
sudo apt-get install nvidia-driver-525
sudo reboot
```

### Docker: could not select device driver
```bash
# NVIDIA Docker 런타임 미설치
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### CUDA out of memory
```bash
# GPU VRAM 부족
# 해결: Batch size 줄이기
# edgnet-api/config.py
BATCH_SIZE = 8  # 16 → 8로 줄임
```

---

## ✅ 완료 확인

```bash
# 1. GPU 사용 확인
nvidia-smi

# 2. Docker GPU 확인
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# 3. 서비스 GPU 확인
docker exec -it edgnet-api python3 -c "import torch; print(torch.cuda.is_available())"
# 출력: True

# 4. 벤치마크
python TODO/scripts/benchmark_gpu.py
# Speedup: 3x 이상이면 성공!
```

---

**작성일**: 2025-11-08
**예상 소요 시간**: 1-2일
**다음 단계**: `PRIORITY_3_PRODUCTION.md`
