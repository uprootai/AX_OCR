# 🔧 개선 사항 통합 가이드

**생성 일시**: 2025-11-08
**목적**: 새로 구현된 기능들을 기존 코드에 통합하는 방법

---

## 📦 구현된 기능

### 1. API 인증 시스템 (`common/auth.py`)
- ✅ API 키 기반 인증
- ✅ 환경변수 또는 YAML 설정 파일 지원
- ✅ 선택적 활성화 (ENABLE_AUTH)

### 2. Rate Limiting (`common/rate_limiter.py`)
- ✅ 분/시간/일 단위 요청 제한
- ✅ IP 기반 추적
- ✅ 선택적 활성화 (ENABLE_RATE_LIMIT)

### 3. Retry Logic (`common/resilience.py`)
- ✅ Exponential backoff
- ✅ 설정 가능한 재시도 횟수
- ✅ Decorator 지원

### 4. Circuit Breaker (`common/resilience.py`)
- ✅ 서비스 장애 시 요청 차단
- ✅ Half-open 상태로 자동 복구 시도
- ✅ 서비스별 독립적 관리

### 5. Prometheus Monitoring (`common/monitoring.py`)
- ✅ HTTP 요청 메트릭
- ✅ OCR 처리 메트릭
- ✅ Circuit breaker 상태 메트릭
- ✅ /metrics 엔드포인트

---

## 🚀 빠른 통합 (Gateway API 예시)

### 1단계: 의존성 설치

```bash
cd /home/uproot/ax/poc/gateway-api
pip install -r ../common/requirements.txt
```

### 2단계: 코드 수정

```python
# gateway-api/api_server.py

from fastapi import FastAPI, Depends
import sys
sys.path.insert(0, '/home/uproot/ax/poc')

# Import common utilities
from common import (
    verify_api_key,
    check_rate_limit,
    retry_async,
    get_circuit_breaker,
    metrics_endpoint,
    PrometheusMiddleware,
    record_request,
    record_error
)

app = FastAPI()

# Add monitoring middleware
app.add_middleware(PrometheusMiddleware)

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    return await metrics_endpoint()

# Protected endpoint example
@app.get(
    "/api/v1/protected",
    dependencies=[Depends(verify_api_key), Depends(check_rate_limit)]
)
async def protected_endpoint():
    return {"message": "You are authenticated"}

# Using retry and circuit breaker
@app.post("/api/v1/process")
async def process_drawing(file: UploadFile):
    # Get circuit breaker for EDGNet
    breaker = get_circuit_breaker("edgnet")
    
    async def call_edgnet():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:5012/api/v1/segment",
                files={"file": file.file}
            )
            return response.json()
    
    try:
        # Use retry + circuit breaker
        result = await retry_async(
            lambda: breaker.call(call_edgnet),
            max_attempts=3,
            initial_delay=1.0
        )
        return result
    except Exception as e:
        record_error("gateway", str(type(e).__name__))
        raise HTTPException(status_code=500, detail=str(e))
```

### 3단계: 환경변수 설정

```bash
# .env 파일 생성
cat > .env << 'ENV'
# 인증
ENABLE_AUTH=true
API_KEY=your-secret-key-here

# Rate limiting
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500
RATE_LIMIT_PER_DAY=3000
ENV
```

### 4단계: 테스트

```bash
# 서비스 재시작
docker-compose restart gateway-api

# 인증 없이 요청 → 401
curl http://localhost:8000/api/v1/protected
# {"detail":"Missing API key"}

# 인증 포함 요청 → 200
curl -H "X-API-Key: your-secret-key-here" \
     http://localhost:8000/api/v1/protected
# {"message":"You are authenticated"}

# Prometheus 메트릭 확인
curl http://localhost:8000/metrics
```

---

## 📊 각 서비스별 통합 방법

### eDOCr2 API (v1)

```python
from common import (
    PrometheusMiddleware,
    record_ocr_processing,
    check_rate_limit
)

app.add_middleware(PrometheusMiddleware)

@app.post("/api/v1/ocr", dependencies=[Depends(check_rate_limit)])
async def ocr_endpoint(...):
    start_time = time.time()
    
    try:
        # ... OCR processing ...
        
        # Record metrics
        duration = time.time() - start_time
        record_ocr_processing(
            strategy="basic",
            status="success",
            duration=duration,
            dimensions_count=len(dimensions),
            gdt_count=len(gdt_symbols)
        )
        
        return result
    except Exception as e:
        record_ocr_processing("basic", "error", time.time() - start_time)
        raise
```

### EDGNet API

```python
from common import (
    PrometheusMiddleware,
    record_edgnet_processing
)

app.add_middleware(PrometheusMiddleware)

@app.post("/api/v1/segment")
async def segment_endpoint(...):
    start_time = time.time()
    
    # ... Processing ...
    
    record_edgnet_processing(
        components_count=len(components),
        duration=time.time() - start_time
    )
```

---

## 🔒 보안 설정 파일 (선택)

```yaml
# security_config.yaml
authentication:
  enabled: true
  method: api_key
  api_keys:
    - key: "prod-key-abc123"
      name: "Production Client"
      permissions: ["read", "write"]
    - key: "readonly-key-xyz"
      name: "Read Only Client"
      permissions: ["read"]

rate_limiting:
  enabled: true
  per_minute: 30
  per_hour: 500
  per_day: 3000

cors:
  allow_origins:
    - "https://your-domain.com"
    - "http://localhost:5173"
```

---

## 📈 Prometheus + Grafana 설정

### 1. docker-compose.yml에 추가

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 2. prometheus.yml 생성

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gateway-api'
    static_configs:
      - targets: ['host.docker.internal:8000']
  
  - job_name: 'edocr2-api-v1'
    static_configs:
      - targets: ['host.docker.internal:5001']
  
  - job_name: 'edgnet-api'
    static_configs:
      - targets: ['host.docker.internal:5012']
```

### 3. Grafana 대시보드

1. http://localhost:3000 접속
2. Prometheus 데이터소스 추가
3. 대시보드 Import → ID: 7587 (FastAPI)

---

## ✅ 통합 체크리스트

### Gateway API
- [ ] PrometheusMiddleware 추가
- [ ] /metrics 엔드포인트 추가
- [ ] Retry logic 적용 (외부 API 호출)
- [ ] Circuit breaker 적용 (EDGNet, eDOCr2)
- [ ] 인증 (선택)
- [ ] Rate limiting (선택)

### eDOCr2 API
- [ ] PrometheusMiddleware 추가
- [ ] record_ocr_processing 호출
- [ ] Rate limiting (선택)

### EDGNet API
- [ ] PrometheusMiddleware 추가
- [ ] record_edgnet_processing 호출

### Skin Model API
- [ ] PrometheusMiddleware 추가
- [ ] 메트릭 기록

---

## 🧪 테스트

```bash
# 통합 테스트 실행
python /home/uproot/ax/poc/TODO/scripts/test_improvements.py

# 각 기능별 테스트
# 1. Retry: 네트워크 일시 실패 시 자동 재시도
# 2. Circuit breaker: 서비스 다운 시 요청 차단
# 3. Rate limiting: 초과 요청 차단
# 4. Authentication: 유효한 API 키만 허용
# 5. Monitoring: /metrics 엔드포인트 메트릭 노출
```

---

## 📞 문제 해결

### "ImportError: No module named 'common'"
```bash
# Python path 추가
export PYTHONPATH=/home/uproot/ax/poc:$PYTHONPATH

# 또는 코드에서
import sys
sys.path.insert(0, '/home/uproot/ax/poc')
```

### "prometheus_client not found"
```bash
pip install -r /home/uproot/ax/poc/common/requirements.txt
```

### "Circuit breaker always open"
```bash
# 임계값 확인
breaker = CircuitBreaker(
    failure_threshold=5,  # 5회 실패 후 open
    timeout=60.0  # 60초 후 half-open 시도
)

# 상태 확인
print(breaker.get_status())
```

---

**작성일**: 2025-11-08
**다음 단계**: 각 서비스에 단계별로 통합 → 테스트 → 프로덕션 배포
