# 🚀 API Deployment Guide

> **개별 API 배포 및 전달 가이드**

---

## 📦 프로젝트 구조

```
/home/uproot/ax/poc/
├── docker-compose.yml      # 전체 시스템 통합
├── gateway-api/            # Gateway (오케스트레이터)
├── web-ui/                 # 프론트엔드
└── models/                 # 🎯 모든 추론 API
    ├── yolo-api/
    ├── edocr2-api/
    ├── edocr2-v2-api/
    ├── edgnet-api/
    ├── paddleocr-api/
    ├── skinmodel-api/
    └── vl-api/
```

**각 API는 독립적으로 실행 가능합니다!**

---

## 🎯 개별 API 배포 방법

### Option 1: Docker Image 파일로 전달

#### 1. Docker Image 빌드 및 저장

```bash
# API 디렉토리로 이동
cd /home/uproot/ax/poc/models/paddleocr-api

# Docker 이미지 빌드
docker build -t ax-paddleocr-api:latest .

# 이미지를 tar 파일로 저장
docker save ax-paddleocr-api:latest -o paddleocr-api.tar
```

#### 2. 파일 전달

```bash
# USB, 네트워크 등으로 전달
scp paddleocr-api.tar user@remote-server:/path/to/destination/

# 또는 외장 HDD에 복사
cp paddleocr-api.tar /mnt/usb/
```

#### 3. 수신 측에서 실행

```bash
# 이미지 로드
docker load -i paddleocr-api.tar

# 컨테이너 실행
docker run -d \
  --name paddleocr-api \
  -p 5006:5006 \
  --gpus all \
  -e USE_GPU=true \
  -e OCR_LANG=en \
  ax-paddleocr-api:latest

# 헬스 체크
curl http://localhost:5006/health
```

---

### Option 2: docker-compose로 배포

#### 1. API 디렉토리 전체 전달

```bash
# API 디렉토리 압축
cd /home/uproot/ax/poc/models
tar -czf paddleocr-api.tar.gz paddleocr-api/

# 전달
scp paddleocr-api.tar.gz user@remote:/path/
```

#### 2. 수신 측에서 압축 해제 및 실행

```bash
# 압축 해제
tar -xzf paddleocr-api.tar.gz
cd paddleocr-api/

# docker-compose로 실행
docker-compose -f docker-compose.single.yml up -d

# 로그 확인
docker logs paddleocr-api-standalone -f

# API 문서 확인
# http://localhost:5006/docs
```

---

### Option 3: GitHub Container Registry (추후)

```bash
# Push (관리자)
docker tag ax-paddleocr-api:latest ghcr.io/your-org/ax-paddleocr-api:latest
docker push ghcr.io/your-org/ax-paddleocr-api:latest

# Pull (사용자)
docker pull ghcr.io/your-org/ax-paddleocr-api:latest
docker run -d -p 5006:5006 --gpus all ghcr.io/your-org/ax-paddleocr-api:latest
```

---

## 📋 각 API 정보

### 1. PaddleOCR API

| 속성 | 값 |
|------|-----|
| **포트** | 5006 |
| **GPU** | Recommended |
| **이미지 크기** | ~1.7GB |
| **용도** | 범용 OCR (80+ 언어 지원) |
| **문서** | `models/paddleocr-api/README.md` |

**전달 명령어**:
```bash
cd models/paddleocr-api
docker build -t ax-paddleocr-api .
docker save ax-paddleocr-api -o paddleocr-api.tar
```

---

### 2. YOLO API

| 속성 | 값 |
|------|-----|
| **포트** | 5005 |
| **GPU** | Required |
| **이미지 크기** | ~8.2GB |
| **용도** | 도면 객체 검출 (14 classes) |
| **문서** | `models/yolo-api/README.md` |

**전달 명령어**:
```bash
cd models/yolo-api
docker build -t ax-yolo-api .
docker save ax-yolo-api -o yolo-api.tar
```

---

### 3. eDOCr2 v1 API

| 속성 | 값 |
|------|-----|
| **포트** | 5001 |
| **GPU** | Required |
| **이미지 크기** | ~10.2GB |
| **용도** | 빠른 도면 OCR |
| **문서** | `models/edocr2-api/README.md` |

**주의**: 외부 모델 의존성
```
/home/uproot/ax/opensource/01-immediate/edocr2/edocr2
```

---

### 4. eDOCr2 v2 API

| 속성 | 값 |
|------|-----|
| **포트** | 5002 |
| **GPU** | Required |
| **이미지 크기** | ~10.4GB |
| **용도** | 고급 도면 OCR + 테이블 지원 |
| **문서** | `models/edocr2-v2-api/README.md` |

**주의**: 외부 모델 의존성
```
/home/uproot/ax/opensource/01-immediate/edocr2/edocr2
```

---

### 5. EDGNet API

| 속성 | 값 |
|------|-----|
| **포트** | 5012 (외부) / 5002 (내부) |
| **GPU** | Required |
| **이미지 크기** | ~8.1GB |
| **용도** | 세그멘테이션 (GraphSAGE + UNet) |
| **문서** | `models/edgnet-api/README.md` |

**주의**: 2개 모델 사용
```
GraphSAGE: /home/uproot/ax/dev/test_results/sample_tests/graphsage_models/
UNet: models/edgnet-api/models/edgnet_large.pth (355MB)
```

---

### 6. Skin Model API

| 속성 | 값 |
|------|-----|
| **포트** | 5003 |
| **GPU** | No |
| **이미지 크기** | ~1.3GB |
| **용도** | 공차 예측 (XGBoost) |
| **문서** | `models/skinmodel-api/README.md` |

**전달 명령어**:
```bash
cd models/skinmodel-api
docker build -t ax-skinmodel-api .
docker save ax-skinmodel-api -o skinmodel-api.tar
```

---

### 7. VL API

| 속성 | 값 |
|------|-----|
| **포트** | 5004 |
| **GPU** | No |
| **이미지 크기** | ~200MB |
| **용도** | 비전-언어 모델 (Claude/GPT-4V) |
| **문서** | `models/vl-api/README.md` |

**주의**: API 키 필요
```bash
-e ANTHROPIC_API_KEY=sk-...
-e OPENAI_API_KEY=sk-...
```

---

## 🧪 단독 API 테스트

### 1. API 빌드 및 실행

```bash
# 예시: PaddleOCR API
cd /home/uproot/ax/poc/models/paddleocr-api

# docker-compose로 실행
docker-compose -f docker-compose.single.yml up -d

# 로그 확인
docker logs -f paddleocr-api-standalone
```

### 2. Health Check

```bash
curl http://localhost:5006/health
```

예상 응답:
```json
{
  "status": "healthy",
  "service": "PaddleOCR API",
  "version": "1.0.0"
}
```

### 3. API 문서 확인

브라우저에서: **http://localhost:5006/docs**

### 4. 테스트 요청

```bash
curl -X POST http://localhost:5006/api/v1/ocr \
  -F "file=@/path/to/test-image.jpg" \
  -F "use_gpu=true" \
  -F "lang=en"
```

### 5. 종료

```bash
docker-compose -f docker-compose.single.yml down
```

---

## 🔧 외부 의존성 처리

일부 API는 외부 소스 코드나 모델을 사용합니다:

### eDOCr2 APIs (v1, v2)

**의존성**:
```
/home/uproot/ax/opensource/01-immediate/edocr2/edocr2
```

**해결책 1**: 소스 코드 함께 전달
```bash
tar -czf edocr2-package.tar.gz \
  models/edocr2-v2-api/ \
  /home/uproot/ax/opensource/01-immediate/edocr2/
```

**해결책 2**: Dockerfile에 소스 복사
```dockerfile
# Dockerfile 수정
COPY edocr2/ /app/edocr2/
COPY models/ /models/
```

### EDGNet API

**의존성**:
```
/home/uproot/ax/dev/edgnet
/home/uproot/ax/dev/test_results/sample_tests/graphsage_models/
```

**해결책**: 모델과 소스 번들링
```bash
tar -czf edgnet-package.tar.gz \
  models/edgnet-api/ \
  /home/uproot/ax/dev/edgnet/ \
  /home/uproot/ax/dev/test_results/sample_tests/graphsage_models/
```

---

## 📊 전체 시스템 실행

### 모든 API 동시 실행

```bash
cd /home/uproot/ax/poc
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f gateway-api
```

### 선택적 API 실행

```bash
# YOLO + PaddleOCR만
docker-compose up -d yolo-api paddleocr-api

# Gateway + 필수 서비스
docker-compose up -d gateway-api yolo-api edocr2-v2-api skinmodel-api
```

---

## 🐛 Troubleshooting

### 1. GPU 인식 안 됨

```bash
# NVIDIA 드라이버 확인
nvidia-smi

# Docker GPU 지원 확인
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 2. 포트 충돌

```bash
# 사용 중인 포트 확인
netstat -tulpn | grep 5006

# docker-compose.single.yml에서 포트 변경
ports:
  - "5007:5006"  # 호스트:컨테이너
```

### 3. 볼륨 마운트 오류

```bash
# 디렉토리 존재 확인
ls -la /home/uproot/ax/opensource/01-immediate/edocr2/edocr2

# 권한 확인
chmod -R 755 /path/to/volume
```

### 4. Docker Image 용량 확인

```bash
# 모든 API 이미지 크기
docker images | grep "ax-.*-api"

# 특정 이미지 상세 정보
docker inspect ax-paddleocr-api:latest
```

---

## 📚 추가 문서

- [ARCHITECTURE.md](../ARCHITECTURE.md) - 시스템 아키텍처
- [README.md](../README.md) - 프로젝트 개요
- [WORKFLOWS.md](../WORKFLOWS.md) - 개발 워크플로우

---

## 🎯 다음 단계

1. **GitHub Repositories 생성**
   - 각 API를 독립 repo로 분리
   - Git submodule로 관리

2. **CI/CD 파이프라인**
   - 자동 Docker 이미지 빌드
   - GitHub Container Registry 배포

3. **Kubernetes 지원**
   - Helm charts 추가
   - Production 배포 자동화

---

**Last Updated**: 2025-11-20
**Version**: 1.0.0
**Maintained By**: AX Project Team
