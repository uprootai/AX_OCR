# Skin Model API

기하공차 예측 및 제조 가능성 분석 마이크로서비스

## 개요

FEM 기반 Skin Model Shapes 이론을 활용한 독립 API 서버로, 다음 기능을 제공합니다:
- **기하공차 예측**: Flatness, Cylindricity, Position 등
- **GD&T 검증**: 요구사항 대비 실제 공차 비교
- **제조 가능성 분석**: 난이도 평가 및 권장사항 제공
- **조립 가능성 평가**: 클리어런스 및 간섭 위험도 분석

## 기능

### 핵심 기능
- **공차 예측**: Random Field Theory + FEM 기반 예측
- **GD&T 검증**: ISO 1101/ASME Y14.5 기준 검증
- **제조 난이도 평가**: Easy/Medium/Hard 분류
- **조립 가능성**: 클리어런스 및 간섭 분석

### 지원 공차 타입
- Flatness (평탄도)
- Cylindricity (원통도)
- Position (위치 공차)
- Perpendicularity (수직도)

## 빠른 시작

### 🆕 단독 실행 (Standalone)

```bash
# 독립 실행 (docker-compose.single.yml 사용)
cd /home/uproot/ax/poc/models/skinmodel-api
docker-compose -f docker-compose.single.yml up -d

# 로그 확인
docker logs skinmodel-api-standalone -f

# 헬스체크
curl http://localhost:5003/api/v1/health

# API 문서
# http://localhost:5003/docs
```

**주의**: GPU 불필요 (CPU only)

### Docker로 실행 (권장)

```bash
# 1. 빌드
cd /home/uproot/ax/poc/skinmodel-api
docker build -t skinmodel-api .

# 2. 실행
docker run -d \
  -p 5003:5003 \
  --name skinmodel \
  -v $(pwd)/../dev/skinmodel:/app/skinmodel:ro \
  skinmodel-api

# 3. 로그 확인
docker logs -f skinmodel

# 4. 헬스체크
curl http://localhost:5003/api/v1/health
```

### Docker Compose로 실행

```bash
cd /home/uproot/ax/poc/skinmodel-api
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

## API 사용법

### 1. 헬스체크

```bash
curl http://localhost:5003/api/v1/health
```

**응답**:
```json
{
  "status": "healthy",
  "service": "Skin Model API",
  "version": "1.0.0",
  "timestamp": "2025-10-27T12:34:56"
}
```

### 2. 기하공차 예측

```bash
curl -X POST http://localhost:5003/api/v1/tolerance \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": [
      {
        "type": "diameter",
        "value": 392.0,
        "tolerance": 0.1,
        "unit": "mm"
      },
      {
        "type": "length",
        "value": 163.0,
        "tolerance": 0.2,
        "unit": "mm"
      }
    ],
    "material": {
      "name": "Steel",
      "youngs_modulus": 200.0,
      "poisson_ratio": 0.3,
      "density": 7850.0
    },
    "manufacturing_process": "machining",
    "correlation_length": 1.0
  }'
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "predicted_tolerances": {
      "flatness": 0.048,
      "cylindricity": 0.092,
      "position": 0.065,
      "perpendicularity": 0.035
    },
    "manufacturability": {
      "score": 0.85,
      "difficulty": "Medium",
      "recommendations": [
        "Consider tighter fixturing for flatness control",
        "Use precision grinding for cylindrical surfaces",
        "Verify alignment during setup"
      ]
    },
    "assemblability": {
      "score": 0.92,
      "clearance": 0.215,
      "interference_risk": "Low"
    }
  },
  "processing_time": 2.1
}
```

### 3. GD&T 검증

```bash
curl -X POST http://localhost:5003/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": [
      {"type": "diameter", "value": 392.0, "tolerance": 0.1}
    ],
    "gdt_specs": {
      "flatness": 0.05,
      "cylindricity": 0.1,
      "position": 0.08
    },
    "material": {
      "name": "Steel"
    }
  }'
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "validation_results": {
      "flatness": {
        "spec": 0.05,
        "predicted": 0.048,
        "status": "PASS",
        "margin": 0.002
      },
      "cylindricity": {
        "spec": 0.1,
        "predicted": 0.092,
        "status": "PASS",
        "margin": 0.008
      }
    },
    "overall_status": "PASS",
    "pass_rate": 1.0,
    "recommendations": [
      "All tolerances within specification",
      "Consider process capability study (Cpk > 1.33)"
    ]
  },
  "processing_time": 1.5
}
```

### 4. 제조 가능성 분석

```bash
curl -X POST http://localhost:5003/api/v1/manufacturability \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": [
      {"type": "diameter", "value": 392.0, "tolerance": 0.1}
    ],
    "material": {"name": "Steel"},
    "manufacturing_process": "machining"
  }'
```

**응답 예시**:
```json
{
  "status": "success",
  "data": {
    "manufacturability": {
      "score": 0.85,
      "difficulty": "Medium",
      "recommendations": [
        "Consider tighter fixturing",
        "Use precision grinding"
      ]
    },
    "assemblability": {
      "score": 0.92,
      "clearance": 0.215,
      "interference_risk": "Low"
    }
  },
  "processing_time": 1.8
}
```

### 5. Python 클라이언트

```python
import requests

# API URL
url = "http://localhost:5003/api/v1/tolerance"

# 요청 데이터
data = {
    "dimensions": [
        {
            "type": "diameter",
            "value": 392.0,
            "tolerance": 0.1,
            "unit": "mm"
        }
    ],
    "material": {
        "name": "Steel",
        "youngs_modulus": 200.0,
        "poisson_ratio": 0.3
    },
    "manufacturing_process": "machining",
    "correlation_length": 1.0
}

response = requests.post(url, json=data)
result = response.json()

print(f"Status: {result['status']}")
print(f"Flatness: {result['data']['predicted_tolerances']['flatness']}")
print(f"Manufacturability: {result['data']['manufacturability']['score']}")
print(f"Difficulty: {result['data']['manufacturability']['difficulty']}")
```

### 6. JavaScript/TypeScript 클라이언트

```javascript
const data = {
  dimensions: [
    {
      type: 'diameter',
      value: 392.0,
      tolerance: 0.1,
      unit: 'mm'
    }
  ],
  material: {
    name: 'Steel'
  },
  manufacturing_process: 'machining'
};

const response = await fetch('http://localhost:5003/api/v1/tolerance', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
});

const result = await response.json();
console.log('Tolerance Prediction:', result);
```

## API 문서

서버 실행 후 다음 URL에서 상세 API 문서 확인:

- **Swagger UI**: http://localhost:5003/docs
- **ReDoc**: http://localhost:5003/redoc
- **OpenAPI JSON**: http://localhost:5003/openapi.json

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `SKINMODEL_PORT` | 5003 | API 서버 포트 |
| `SKINMODEL_WORKERS` | 2 | Uvicorn 워커 수 |
| `SKINMODEL_LOG_LEVEL` | INFO | 로그 레벨 |

## 성능

- **처리 속도**:
  - 공차 예측: ~2-5초/요청
  - GD&T 검증: ~1-2초/요청
  - 제조 가능성 분석: ~1-3초/요청
- **동시 처리**: 워커 2개 기준 최대 2개 동시 처리

## 제한 사항

- **재질 데이터베이스**: 주요 재질만 지원 (Steel, Aluminum, Titanium 등)
- **제조 공정**: machining, casting, 3d_printing
- **공차 타입**: Flatness, Cylindricity, Position, Perpendicularity

## 문제 해결

### 포트 충돌
```bash
# 포트 사용 확인
sudo lsof -i :5003

# 다른 포트 사용
docker run -p 5030:5003 skinmodel-api
```

### 로그 확인
```bash
# 실시간 로그
docker logs -f skinmodel

# 최근 100줄
docker logs --tail 100 skinmodel
```

### 컨테이너 재시작
```bash
docker restart skinmodel
```

## 개발

### 로컬 실행 (개발용)

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행 (hot reload)
uvicorn api_server:app --reload --port 5003
```

### 테스트

```bash
# 헬스체크
curl http://localhost:5003/api/v1/health

# 공차 예측 테스트
curl -X POST http://localhost:5003/api/v1/tolerance \
  -H "Content-Type: application/json" \
  -d '{"dimensions":[{"type":"diameter","value":392.0,"tolerance":0.1}],"material":{"name":"Steel"},"manufacturing_process":"machining"}'
```

## 아키텍처

```
Client (HTTP POST JSON)
    ↓
FastAPI Server (Uvicorn)
    ↓
Input Validation
    ↓
Skin Model Generator
    ├── Random Field Theory
    ├── FEM Simulation
    └── Deviation Models
    ↓
GDT Validator
    ├── Flatness Check
    ├── Cylindricity Check
    ├── Position Check
    └── Overall Assessment
    ↓
Response (JSON)
```

## 기술 스택

- **웹 프레임워크**: FastAPI 0.104
- **ASGI 서버**: Uvicorn 0.24
- **수치 계산**: NumPy 1.24, SciPy 1.11
- **3D 모델링**: Trimesh 4.0
- **컨테이너**: Docker

## 알고리즘

### Skin Model Shapes
1. **Systematic Deviation**: 수축, 열팽창 등
2. **Random Deviation**: Random Field Theory 기반
3. **Correlation Length**: 공간적 상관관계

### GD&T 검증
1. **Flatness**: 최소자승평면 대비 최대 편차
2. **Cylindricity**: 최소자승원통 대비 반지름 편차
3. **Position**: 기준 위치 대비 중심 편차

## 라이선스

MIT License

## 문의

- 기술 문의: dev@uproot.com
- 이슈 리포트: https://github.com/uproot/ax-poc/issues
