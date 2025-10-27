# AX 실증산단 - 마이크로서비스 API 시스템

공학 도면 기반 견적 자동화를 위한 독립 API 서버 모음

## 🎯 시스템 개요

4개의 독립적인 API 서버로 구성된 마이크로서비스 아키텍처:

```
┌─────────────────┐         ┌─────────────────┐         ┌──────────────────┐
│  eDOCr2 API     │         │  EDGNet API     │         │  Skin Model API  │
│  포트: 5001     │         │  포트: 5002     │         │  포트: 5003      │
│  OCR 처리       │         │  세그멘테이션    │         │  공차 예측       │
└─────────────────┘         └─────────────────┘         └──────────────────┘
         ↑                           ↑                           ↑
         └───────────────────────────┴───────────────────────────┘
                                     │
                            ┌────────────────┐
                            │  Gateway API   │
                            │  포트: 8000    │
                            │  통합 오케스트레이터 │
                            └────────────────┘
```

## 📦 서비스 구성

### 1. eDOCr2 API (포트 5001)
- **기능**: 공학 도면 OCR 처리
- **위치**: `./edocr2-api/`
- **엔드포인트**:
  - `POST /api/v1/ocr`: 도면 OCR 처리
  - `GET /api/v1/health`: 헬스체크
  - `GET /api/v1/docs`: API 문서 (Swagger)

### 2. EDGNet API (포트 5002)
- **기능**: 그래프 신경망 기반 도면 세그멘테이션
- **위치**: `./edgnet-api/`
- **엔드포인트**:
  - `POST /api/v1/segment`: 도면 컴포넌트 분류
  - `POST /api/v1/vectorize`: 도면 벡터화
  - `GET /api/v1/health`: 헬스체크
  - `GET /api/v1/docs`: API 문서 (Swagger)

### 3. Skin Model API (포트 5003)
- **기능**: 기하공차 예측 및 제조 가능성 분석
- **위치**: `./skinmodel-api/`
- **엔드포인트**:
  - `POST /api/v1/tolerance`: 공차 예측
  - `POST /api/v1/validate`: GD&T 검증
  - `GET /api/v1/health`: 헬스체크
  - `GET /api/v1/docs`: API 문서 (Swagger)

### 4. Gateway API (포트 8000)
- **기능**: 통합 오케스트레이션 및 워크플로우 관리
- **위치**: `./gateway-api/`
- **엔드포인트**:
  - `POST /api/v1/process`: 전체 파이프라인 실행
  - `POST /api/v1/quote`: 견적서 생성
  - `GET /api/v1/health`: 헬스체크
  - `GET /api/v1/docs`: API 문서 (Swagger)

## 🚀 빠른 시작

### 전체 시스템 실행 (docker-compose)

```bash
# 전체 시스템 한 번에 실행
cd /home/uproot/ax/poc
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

### 개별 서비스 실행

#### eDOCr2 API
```bash
cd edocr2-api
docker build -t edocr2-api .
docker run -d -p 5001:5001 --name edocr2 edocr2-api

# 테스트
curl http://localhost:5001/api/v1/health
```

#### EDGNet API
```bash
cd edgnet-api
docker build -t edgnet-api .
docker run -d -p 5002:5002 --name edgnet edgnet-api

# 테스트
curl http://localhost:5002/api/v1/health
```

#### Skin Model API
```bash
cd skinmodel-api
docker build -t skinmodel-api .
docker run -d -p 5003:5003 --name skinmodel skinmodel-api

# 테스트
curl http://localhost:5003/api/v1/health
```

#### Gateway API
```bash
cd gateway-api
docker build -t gateway-api .
docker run -d -p 8000:8000 --name gateway gateway-api

# 테스트
curl http://localhost:8000/api/v1/health
```

## 🧪 API 테스트 예제

### 1. eDOCr2 - 도면 OCR

```bash
curl -X POST http://localhost:5001/api/v1/ocr \
  -F "file=@drawing.pdf" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "dimensions": [
      {"value": 392, "unit": "mm", "type": "diameter", "tolerance": "±0.1"}
    ],
    "gdt": [
      {"type": "flatness", "value": 0.05}
    ],
    "text": {
      "drawing_number": "A12-311197-9",
      "revision": "Rev.2"
    }
  },
  "processing_time": 8.5
}
```

### 2. EDGNet - 도면 세그멘테이션

```bash
curl -X POST http://localhost:5002/api/v1/segment \
  -F "file=@drawing.png" \
  -F "visualize=true"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "classifications": {
      "contour": 80,
      "text": 30,
      "dimension": 40
    },
    "graph": {
      "nodes": 150,
      "edges": 280
    },
    "visualization_url": "/results/drawing_segment.png"
  },
  "processing_time": 12.3
}
```

### 3. Skin Model - 공차 예측

```bash
curl -X POST http://localhost:5003/api/v1/tolerance \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": [
      {"type": "diameter", "value": 392, "tolerance": 0.1}
    ],
    "material": "Steel"
  }'
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "predicted_tolerances": {
      "flatness": 0.048,
      "cylindricity": 0.092
    },
    "manufacturability": {
      "score": 0.85,
      "difficulty": "Medium"
    }
  },
  "processing_time": 2.1
}
```

### 4. Gateway - 통합 처리

```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@drawing.pdf" \
  -F "generate_quote=true"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "ocr_results": {...},
    "segmentation_results": {...},
    "tolerance_prediction": {...},
    "quote": {
      "total": 11200.00,
      "breakdown": {
        "material": 1500.00,
        "machining": 8500.00,
        "tolerance_premium": 1200.00
      }
    }
  },
  "processing_time": 25.8
}
```

## 📊 API 문서

각 서비스 실행 후 Swagger UI에서 상세 API 문서 확인:

- eDOCr2: http://localhost:5001/docs
- EDGNet: http://localhost:5002/docs
- Skin Model: http://localhost:5003/docs
- Gateway: http://localhost:8000/docs

## 🔧 환경 변수

각 서비스는 환경 변수로 설정 가능:

### eDOCr2 API
```env
EDOCR2_PORT=5001
EDOCR2_WORKERS=4
EDOCR2_MODEL_PATH=/models
EDOCR2_LOG_LEVEL=INFO
```

### EDGNet API
```env
EDGNET_PORT=5002
EDGNET_WORKERS=2
EDGNET_MODEL_PATH=/models/graphsage_dimension_classifier.pth
EDGNET_LOG_LEVEL=INFO
```

### Skin Model API
```env
SKINMODEL_PORT=5003
SKINMODEL_WORKERS=2
SKINMODEL_LOG_LEVEL=INFO
```

### Gateway API
```env
GATEWAY_PORT=8000
GATEWAY_WORKERS=4
EDOCR2_URL=http://edocr2-api:5001
EDGNET_URL=http://edgnet-api:5002
SKINMODEL_URL=http://skinmodel-api:5003
GATEWAY_LOG_LEVEL=INFO
```

## 🏗️ 아키텍처

### 데이터 흐름

```
도면 업로드
    ↓
Gateway API (8000)
    ↓
┌───┴──────────┬──────────────┐
↓              ↓              ↓
EDGNet     eDOCr2      직접처리
(5002)     (5001)
↓              ↓              ↓
└──────┬───────┴──────────────┘
       ↓
Skin Model (5003)
       ↓
견적 생성
```

### 기술 스택

- **프레임워크**: FastAPI
- **웹 서버**: Uvicorn
- **컨테이너**: Docker
- **오케스트레이션**: Docker Compose
- **API 문서**: Swagger/OpenAPI 3.0
- **로깅**: Python logging
- **모니터링**: Health check endpoints

## 📁 프로젝트 구조

```
poc/
├── edocr2-api/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── api_server.py
│   ├── requirements.txt
│   ├── models/          # 모델 파일 (볼륨 마운트)
│   └── README.md
│
├── edgnet-api/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── api_server.py
│   ├── requirements.txt
│   ├── models/          # 모델 파일 (볼륨 마운트)
│   └── README.md
│
├── skinmodel-api/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── api_server.py
│   ├── requirements.txt
│   └── README.md
│
├── gateway-api/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── api_server.py
│   ├── requirements.txt
│   └── README.md
│
├── docker-compose.yml   # 전체 시스템 통합
└── README.md           # 이 파일
```

## 🔒 보안

- API 키 인증 (선택적)
- CORS 설정
- 파일 업로드 크기 제한
- Rate limiting
- Input validation

## 📈 성능

- **eDOCr2**: ~8-10초/장 (GPU), ~20-30초/장 (CPU)
- **EDGNet**: ~10-15초/장
- **Skin Model**: ~2-5초/요청
- **Gateway (전체)**: ~25-30초/장

## 🐛 문제 해결

### 포트 충돌
```bash
# 사용 중인 포트 확인
sudo lsof -i :5001
sudo lsof -i :5002
sudo lsof -i :5003
sudo lsof -i :8000
```

### 로그 확인
```bash
# 개별 서비스
docker logs edocr2
docker logs edgnet
docker logs skinmodel
docker logs gateway

# 전체 시스템
docker-compose logs -f
```

### 컨테이너 재시작
```bash
docker restart edocr2
docker restart edgnet
docker restart skinmodel
docker restart gateway
```

## 📝 라이선스

MIT License

## 👥 개발팀

주식회사 업루트 - AX 실증사업팀

## 📞 문의

- 기술 문의: dev@uproot.com
- 사업 문의: business@uproot.com
