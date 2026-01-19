# API 배포 가이드

> 개별 API 배포 및 Docker 이미지 전달 가이드
> **버전**: 2.0.0
> **최종 수정**: 2026-01-17

---

## 프로젝트 구조

```
/home/uproot/ax/poc/
├── docker-compose.yml      # 전체 시스템 통합
├── gateway-api/            # Gateway (오케스트레이터)
├── web-ui/                 # 프론트엔드
└── models/                 # 모든 추론 API (20개)
    ├── yolo-api/           # YOLO 객체 검출
    ├── edocr2-v2-api/      # eDOCr2 도면 OCR
    ├── edgnet-api/         # EDGNet 세그멘테이션
    ├── paddleocr-api/      # PaddleOCR
    ├── skinmodel-api/      # SkinModel 공차 예측
    ├── vl-api/             # VL Vision-Language
    ├── tesseract-api/      # Tesseract OCR
    ├── trocr-api/          # TrOCR
    ├── esrgan-api/         # ESRGAN 업스케일링
    ├── ocr-ensemble-api/   # OCR 앙상블
    ├── surya-ocr-api/      # Surya OCR
    ├── doctr-api/          # DocTR OCR
    ├── easyocr-api/        # EasyOCR
    ├── line-detector-api/  # Line Detector
    ├── pid-analyzer-api/   # PID Analyzer
    ├── design-checker-api/ # Design Checker
    └── knowledge-api/      # Knowledge (Neo4j)
```

**각 API는 독립적으로 실행 가능합니다.**

---

## API 서비스 목록 (20개)

| 서비스 | 포트 | GPU | 이미지 크기 | 용도 |
|--------|------|-----|-------------|------|
| Gateway | 8000 | - | ~500MB | API 오케스트레이션 |
| YOLO | 5005 | Yes | ~8GB | 도면 객체 검출 |
| eDOCr2 | 5002 | Yes | ~10GB | 도면 OCR |
| PaddleOCR | 5006 | Yes | ~2GB | 범용 OCR |
| Tesseract | 5008 | - | ~1GB | 문서 OCR |
| TrOCR | 5009 | Yes | ~3GB | 필기체 OCR |
| ESRGAN | 5010 | Yes | ~2GB | 4x 업스케일링 |
| OCR Ensemble | 5011 | - | ~500MB | 4엔진 투표 |
| EDGNet | 5012 | Yes | ~8GB | 세그멘테이션 |
| Surya OCR | 5013 | - | ~2GB | 다국어 OCR |
| DocTR | 5014 | - | ~2GB | 문서 OCR |
| EasyOCR | 5015 | Yes | ~2GB | 범용 OCR |
| Line Detector | 5016 | - | ~1GB | P&ID 라인 검출 |
| PID Analyzer | 5018 | - | ~1GB | P&ID 연결 분석 |
| Design Checker | 5019 | - | ~1GB | P&ID 설계 검증 |
| Blueprint AI BOM | 5020 | - | ~1GB | Human-in-the-Loop BOM |
| SkinModel | 5003 | - | ~1GB | 공차 예측 |
| VL | 5004 | - | ~200MB | Vision-Language |
| Knowledge | 5007 | - | ~500MB | Neo4j GraphRAG |

---

## 배포 방법

### Option 1: Docker Image 파일로 전달

#### 1. Docker Image 빌드 및 저장

```bash
# API 디렉토리로 이동
cd /home/uproot/ax/poc/models/yolo-api

# Docker 이미지 빌드
docker build -t ax-yolo-api:latest .

# 이미지를 tar 파일로 저장
docker save ax-yolo-api:latest -o yolo-api.tar
```

#### 2. 파일 전달

```bash
# 네트워크 전송
scp yolo-api.tar user@remote-server:/path/to/destination/

# 또는 외장 HDD에 복사
cp yolo-api.tar /mnt/usb/
```

#### 3. 수신 측에서 실행

```bash
# 이미지 로드
docker load -i yolo-api.tar

# 컨테이너 실행
docker run -d \
  --name yolo-api \
  -p 5005:5005 \
  --gpus all \
  -e USE_GPU=true \
  ax-yolo-api:latest

# 헬스 체크
curl http://localhost:5005/health
```

---

### Option 2: Docker Compose로 배포

#### 1. API 디렉토리 전체 전달

```bash
# API 디렉토리 압축
cd /home/uproot/ax/poc/models
tar -czf yolo-api.tar.gz yolo-api/

# 전달
scp yolo-api.tar.gz user@remote:/path/
```

#### 2. 수신 측에서 실행

```bash
# 압축 해제
tar -xzf yolo-api.tar.gz
cd yolo-api/

# docker-compose로 실행
docker compose up -d

# 로그 확인
docker logs yolo-api -f

# API 문서 확인
# http://localhost:5005/docs
```

---

## 전체 시스템 실행

### 모든 API 동시 실행

```bash
cd /home/uproot/ax/poc
docker compose up -d

# 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f gateway-api
```

### 선택적 API 실행

```bash
# 필수 서비스만
docker compose up -d gateway-api yolo-api edocr2-v2-api skinmodel-api

# YOLO + OCR 조합
docker compose up -d gateway-api yolo-api paddleocr-api

# P&ID 분석 조합
docker compose up -d gateway-api yolo-api pid-analyzer-api design-checker-api
```

---

## API 테스트

### Health Check

```bash
# 개별 서비스
curl http://localhost:5005/health  # YOLO
curl http://localhost:5002/api/v2/health  # eDOCr2
curl http://localhost:8000/health  # Gateway

# 전체 서비스 일괄 확인
for port in 5002 5003 5004 5005 5006 5007 5008 5009 5010 5011 5012; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/health | jq -r '.status // "error"'
done
```

### 테스트 요청

```bash
# YOLO 분석
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@test_drawing.png" \
  -F "model_type=engineering"

# eDOCr2 분석
curl -X POST http://localhost:5002/api/v2/process \
  -F "file=@test_drawing.png" \
  -F "language=ko"

# Gateway 통합 분석
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "file=@test_drawing.png"
```

---

## 문제 해결

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
netstat -tulpn | grep 5005

# docker-compose.yml에서 포트 변경
ports:
  - "5006:5005"  # 호스트:컨테이너
```

### 3. 볼륨 마운트 오류

```bash
# 디렉토리 존재 확인
ls -la /path/to/volume

# 권한 확인
chmod -R 755 /path/to/volume
```

### 4. Docker Image 용량 확인

```bash
# 모든 API 이미지 크기
docker images | grep "ax-.*-api"

# 특정 이미지 상세 정보
docker inspect ax-yolo-api:latest
```

---

## 다음 단계

1. **CI/CD 파이프라인**
   - GitHub Actions 자동 빌드
   - Container Registry 배포

2. **Kubernetes 지원**
   - Helm charts
   - Production 배포 자동화

---

**AX 도면 분석 시스템 v23.1**
© 2026 All Rights Reserved
