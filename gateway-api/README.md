# Gateway API

통합 오케스트레이션 및 워크플로우 관리 마이크로서비스

## 개요

Gateway API는 eDOCr2, EDGNet, Skin Model 3개 API를 통합하고 오케스트레이션하는 중앙 서비스입니다:
- **전체 파이프라인 실행**: 세그멘테이션 → OCR → 공차 예측
- **견적서 자동 생성**: 도면 분석 → 비용 산정
- **병렬 처리**: 독립적인 작업을 동시 실행하여 속도 향상
- **서비스 헬스 모니터링**: 연결된 모든 서비스 상태 확인

## 기능

### 핵심 기능
- **통합 처리**: 하나의 API 호출로 전체 파이프라인 실행
- **비동기 병렬 처리**: 세그멘테이션 + OCR 동시 실행
- **견적 자동 생성**: 재료비, 가공비, 공차 프리미엄 자동 계산
- **서비스 오케스트레이션**: 마이크로서비스 간 데이터 흐름 관리

### 워크플로우
```
도면 업로드
    ↓
Gateway API
    ↓
┌───────┴──────────┬──────────────┐
│                  │              │
EDGNet         eDOCr2      (병렬 실행)
(세그멘테이션)    (OCR)
    ↓                  ↓
    └──────┬───────────┘
           ↓
    Skin Model
    (공차 예측)
           ↓
    견적 계산
           ↓
    최종 결과
```

## 빠른 시작

### 전체 시스템 실행

```bash
# 전체 시스템 docker-compose 사용 (poc/ 루트에서)
cd /home/uproot/ax/poc
docker-compose up -d

# Gateway만 실행 (다른 서비스가 이미 실행중일 때)
cd gateway-api
docker-compose up -d
```

### 개별 실행

```bash
cd /home/uproot/ax/poc/gateway-api

# 빌드
docker build -t gateway-api .

# 실행 (다른 서비스 URL 지정)
docker run -d \
  -p 8000:8000 \
  --name gateway \
  -e EDOCR2_URL=http://localhost:5001 \
  -e EDGNET_URL=http://localhost:5002 \
  -e SKINMODEL_URL=http://localhost:5003 \
  gateway-api

# 로그 확인
docker logs -f gateway
```

## API 사용법

### 1. 헬스체크 (전체 시스템)

```bash
curl http://localhost:8000/api/v1/health
```

**응답**:
```json
{
  "status": "healthy",
  "service": "Gateway API",
  "version": "1.0.0",
  "timestamp": "2025-10-27T12:34:56",
  "services": {
    "edocr2": "healthy",
    "edgnet": "healthy",
    "skinmodel": "healthy"
  }
}
```

### 2. 전체 파이프라인 처리

```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@/path/to/drawing.pdf" \
  -F "use_segmentation=true" \
  -F "use_ocr=true" \
  -F "use_tolerance=true" \
  -F "visualize=true"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "segmentation": {
      "status": "success",
      "data": {
        "num_components": 150,
        "classifications": {
          "contour": 80,
          "text": 30,
          "dimension": 40
        }
      },
      "processing_time": 12.3
    },
    "ocr": {
      "status": "success",
      "data": {
        "dimensions": [...],
        "gdt": [...],
        "text": {...}
      },
      "processing_time": 8.5
    },
    "tolerance": {
      "status": "success",
      "data": {
        "predicted_tolerances": {...},
        "manufacturability": {...}
      },
      "processing_time": 2.1
    }
  },
  "processing_time": 15.8,
  "file_id": "1698765432_drawing.pdf"
}
```

### 3. 견적서 생성

```bash
curl -X POST http://localhost:8000/api/v1/quote \
  -F "file=@/path/to/drawing.pdf" \
  -F "material_cost_per_kg=5.0" \
  -F "machining_rate_per_hour=50.0" \
  -F "tolerance_premium_factor=1.2"
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "quote": {
      "quote_id": "Q1698765432",
      "breakdown": {
        "material_cost": 1962.50,
        "machining_cost": 1500.00,
        "tolerance_premium": 240.00,
        "total": 3702.50
      },
      "details": {
        "material_weight_kg": 392.5,
        "estimated_machining_hours": 30.0,
        "num_tight_tolerances": 2,
        "difficulty": "Medium"
      },
      "lead_time_days": 15,
      "confidence": 0.85
    },
    "ocr_summary": {
      "dimensions_count": 5,
      "drawing_number": "A12-311197-9",
      "material": "Steel"
    },
    "tolerance_summary": {
      "score": 0.85,
      "difficulty": "Medium"
    }
  },
  "processing_time": 18.5
}
```

### 4. Python 클라이언트

```python
import requests

# 전체 파이프라인 처리
url = "http://localhost:8000/api/v1/process"

with open("drawing.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "use_segmentation": True,
        "use_ocr": True,
        "use_tolerance": True,
        "visualize": True
    }

    response = requests.post(url, files=files, data=data)
    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Total time: {result['processing_time']}s")
    print(f"Components: {result['data']['segmentation']['data']['num_components']}")
```

```python
# 견적서 생성
url = "http://localhost:8000/api/v1/quote"

with open("drawing.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "material_cost_per_kg": 5.0,
        "machining_rate_per_hour": 50.0,
        "tolerance_premium_factor": 1.2
    }

    response = requests.post(url, files=files, data=data)
    quote = response.json()

    print(f"Quote ID: {quote['data']['quote']['quote_id']}")
    print(f"Total Cost: ${quote['data']['quote']['breakdown']['total']}")
    print(f"Lead Time: {quote['data']['quote']['lead_time_days']} days")
```

### 5. JavaScript/TypeScript 클라이언트

```javascript
// 전체 파이프라인
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('use_segmentation', 'true');
formData.append('use_ocr', 'true');
formData.append('use_tolerance', 'true');

const response = await fetch('http://localhost:8000/api/v1/process', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Pipeline Result:', result);
```

```javascript
// 견적서 생성
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('material_cost_per_kg', '5.0');
formData.append('machining_rate_per_hour', '50.0');

const response = await fetch('http://localhost:8000/api/v1/quote', {
  method: 'POST',
  body: formData
});

const quote = await response.json();
console.log('Quote:', quote.data.quote);
```

## API 문서

서버 실행 후 다음 URL에서 상세 API 문서 확인:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `GATEWAY_PORT` | 8000 | Gateway API 포트 |
| `GATEWAY_WORKERS` | 4 | Uvicorn 워커 수 |
| `EDOCR2_URL` | http://localhost:5001 | eDOCr2 API URL |
| `EDGNET_URL` | http://localhost:5002 | EDGNet API URL |
| `SKINMODEL_URL` | http://localhost:5003 | Skin Model API URL |
| `GATEWAY_LOG_LEVEL` | INFO | 로그 레벨 |

## 성능

- **전체 파이프라인**: ~15-20초/장 (병렬 처리)
  - 세그멘테이션 + OCR 병렬: ~12초
  - 공차 예측: ~2초
- **견적 생성**: ~18-25초/장
- **병렬 처리 효과**: 순차 대비 약 40% 속도 향상

## 오류 처리

Gateway는 개별 서비스 오류를 gracefully 처리합니다:

```json
{
  "status": "partial_success",
  "data": {
    "segmentation": {"error": "EDGNet unreachable"},
    "ocr": {"status": "success", "data": {...}},
    "tolerance": {"status": "success", "data": {...}}
  }
}
```

## 문제 해결

### 서비스 연결 실패

```bash
# 헬스체크로 확인
curl http://localhost:8000/api/v1/health

# 개별 서비스 확인
curl http://localhost:5001/api/v1/health  # eDOCr2
curl http://localhost:5002/api/v1/health  # EDGNet
curl http://localhost:5003/api/v1/health  # Skin Model
```

### Docker 네트워크 문제

```bash
# 네트워크 생성
docker network create ax_poc_network

# 컨테이너를 같은 네트워크에 연결
docker network connect ax_poc_network edocr2
docker network connect ax_poc_network edgnet
docker network connect ax_poc_network skinmodel
docker network connect ax_poc_network gateway
```

### 로그 확인

```bash
# Gateway 로그
docker logs -f gateway

# 전체 시스템 로그
docker-compose logs -f
```

## 개발

### 로컬 실행

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn api_server:app --reload --port 8000
```

### 테스트

```bash
# 헬스체크
curl http://localhost:8000/api/v1/health

# 전체 파이프라인
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg"
```

## 아키텍처

```
Client
   ↓
Gateway API (FastAPI)
   ↓
┌──┴───────────┬─────────────┬──────────────┐
│              │             │              │
eDOCr2 API  EDGNet API  Skin Model API  (병렬)
   ↓              ↓             ↓
OCR 결과     세그멘테이션   공차 예측
   ↓              ↓             ↓
└──┬───────────┴─────────────┴──────────────┘
   ↓
데이터 통합
   ↓
견적 계산 (선택)
   ↓
Response
```

## 기술 스택

- **웹 프레임워크**: FastAPI 0.104
- **ASGI 서버**: Uvicorn 0.24
- **HTTP 클라이언트**: httpx 0.25 (비동기)
- **비동기 처리**: asyncio
- **컨테이너**: Docker

## 라이선스

MIT License

## 문의

- 기술 문의: dev@uproot.com
- 이슈 리포트: https://github.com/uproot/ax-poc/issues
