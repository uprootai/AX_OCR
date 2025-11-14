# 🚀 Enhanced System Startup Guide

**목적**: 개선된 기능(보안, Rate limiting, Monitoring 등)을 포함한 시스템 시작 가이드

---

## 📋 사전 준비

### 1. 의존성 설치

```bash
cd /home/uproot/ax/poc

# Common 모듈 의존성 설치
pip install -r common/requirements.txt

# 또는 각 서비스별로 설치
cd gateway-api && pip install -r requirements.txt
cd ../edocr2-api && pip install -r requirements.txt
cd ../edgnet-api && pip install -r requirements.txt
```

### 2. 환경 설정 파일 생성

```bash
cd /home/uproot/ax/poc

# .env 파일 생성
cp .env.template .env

# 보안 설정 파일 생성 (선택)
cp security_config.yaml.template security_config.yaml
```

### 3. 환경변수 커스터마이징

#### 개발 환경 (.env)
```bash
# 보안 비활성화
ENABLE_AUTH=false
ENABLE_RATE_LIMIT=false

# Grafana 기본 비밀번호
GRAFANA_PASSWORD=admin
```

#### 프로덕션 환경 (.env)
```bash
# 보안 활성화
ENABLE_AUTH=true
API_KEY=$(openssl rand -hex 32)

# Rate limiting 활성화
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500
RATE_LIMIT_PER_DAY=3000

# Grafana 강력한 비밀번호
GRAFANA_PASSWORD=your-strong-password-here
```

---

## 🏃 시스템 시작

### 옵션 1: 기본 모드 (개선 사항 없이)

```bash
# 기존 docker-compose 사용
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 옵션 2: Enhanced 모드 (모든 개선 사항 포함) ⭐ 추천

```bash
# Enhanced docker-compose 사용
docker-compose -f docker-compose.enhanced.yml up -d

# 로그 확인
docker-compose -f docker-compose.enhanced.yml logs -f
```

### 서비스 확인

```bash
# Health check
curl http://localhost:8000/api/v1/health    # Gateway
curl http://localhost:5001/api/v1/health    # eDOCr2 v1
curl http://localhost:5002/api/v2/health    # eDOCr2 v2
curl http://localhost:5012/api/v1/health    # EDGNet
curl http://localhost:5003/api/v1/health    # Skin Model

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health
```

---

## 🔒 보안 기능 사용법

### API 인증 활성화

#### 1. 환경변수 방식

```bash
# .env 파일 수정
ENABLE_AUTH=true
API_KEY=my-secret-key-abc123

# 서비스 재시작
docker-compose -f docker-compose.enhanced.yml restart
```

#### 2. YAML 설정 파일 방식

```bash
# security_config.yaml 생성
cp security_config.yaml.template security_config.yaml

# API 키 생성
openssl rand -hex 32

# security_config.yaml에 키 추가
vi security_config.yaml
```

#### 3. API 호출 예제

```bash
# 인증 없이 (실패)
curl http://localhost:8000/api/v1/protected
# {"detail":"Missing API key"}

# 인증 포함 (성공)
curl -H "X-API-Key: my-secret-key-abc123" \
     http://localhost:8000/api/v1/protected
# {"message":"You are authenticated"}
```

### Rate Limiting 활성화

```bash
# .env 파일 수정
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500

# 서비스 재시작
docker-compose -f docker-compose.enhanced.yml restart gateway-api
```

테스트:
```bash
# 30번 이상 요청 시 차단
for i in {1..35}; do
    curl http://localhost:8000/api/v1/health
    echo " - Request $i"
done
```

---

## 📊 모니터링 사용법

### Prometheus 접속

1. 브라우저에서 http://localhost:9090 열기
2. Status → Targets에서 모든 서비스 확인
3. Graph 탭에서 쿼리 실행

**유용한 쿼리**:
```promql
# 요청 처리율 (초당)
rate(http_requests_total[5m])

# 평균 응답 시간
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# 에러율
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])

# Circuit breaker 상태 (1=OPEN, 0=CLOSED)
circuit_breaker_state
```

### Grafana 대시보드 설정

1. **Grafana 접속**: http://localhost:3000
   - ID: admin
   - PW: admin (또는 .env에서 설정한 값)

2. **Prometheus 데이터소스 추가**:
   - Configuration → Data Sources
   - Add data source → Prometheus
   - URL: http://prometheus:9090
   - Save & Test

3. **대시보드 Import**:
   - Dashboards → Import
   - ID 입력: `7587` (FastAPI Dashboard)
   - Select Prometheus data source
   - Import

4. **커스텀 패널 추가**:
   ```
   Panel 1: Request Rate
   Query: rate(http_requests_total{service="gateway"}[5m])

   Panel 2: Response Time
   Query: rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

   Panel 3: OCR Success Rate
   Query: rate(ocr_processing_total{status="success"}[5m]) / rate(ocr_processing_total[5m])
   ```

---

## 🧪 테스트

### 통합 테스트 실행

```bash
# 모든 개선 사항 테스트
python /home/uproot/ax/poc/TODO/scripts/test_improvements.py

# 출력 예시:
# === 1. Retry Logic 테스트 ===
# ✅ Retry succeeded: Success!
#    Took 3 attempts
#
# === 2. Circuit Breaker 테스트 ===
# Attempt 1: CLOSED (failures: 1)
# Attempt 2: CLOSED (failures: 2)
# Attempt 3: OPEN (failures: 3)
# ✅ Circuit correctly blocked request
```

### 성능 벤치마크

```bash
# 시스템 성능 측정
python /home/uproot/ax/poc/TODO/scripts/benchmark_system.py

# 결과는 /home/uproot/ax/poc/benchmark_results.json에 저장됨
cat /home/uproot/ax/poc/benchmark_results.json
```

### 수동 테스트

#### 1. Retry 동작 확인
```bash
# 서비스 중지
docker-compose -f docker-compose.enhanced.yml stop edocr2-api-v1

# Gateway를 통해 요청 (자동 재시도)
curl -X POST http://localhost:8000/api/v1/process \
     -F "file=@test.pdf"
# 3회 재시도 후 실패

# 서비스 재시작
docker-compose -f docker-compose.enhanced.yml start edocr2-api-v1
```

#### 2. Circuit Breaker 동작 확인
```bash
# Circuit breaker 상태 확인
curl http://localhost:8000/api/v1/circuit-breakers

# 서비스를 의도적으로 5번 실패시키면 circuit이 OPEN됨
# 이후 요청은 즉시 차단됨 (503 Service Unavailable)
```

---

## 🔧 문제 해결

### "ImportError: No module named 'common'"

```bash
# Python path 설정
export PYTHONPATH=/home/uproot/ax/poc:$PYTHONPATH

# 또는 Dockerfile에 추가
ENV PYTHONPATH=/app:/home/uproot/ax/poc
```

### "prometheus_client not found"

```bash
cd /home/uproot/ax/poc
pip install -r common/requirements.txt
```

### "Circuit breaker always open"

```bash
# 상태 확인
curl http://localhost:8000/api/v1/circuit-breakers

# 수동으로 리셋 (서비스 재시작)
docker-compose -f docker-compose.enhanced.yml restart gateway-api

# 또는 timeout 대기 (기본 60초)
```

### Grafana 접속 불가

```bash
# 컨테이너 상태 확인
docker ps | grep grafana

# 로그 확인
docker-compose -f docker-compose.enhanced.yml logs grafana

# 재시작
docker-compose -f docker-compose.enhanced.yml restart grafana
```

---

## 📂 파일 구조 요약

```
/home/uproot/ax/poc/
├── .env                              # 환경 설정 (생성 필요)
├── .env.template                     # 환경 설정 템플릿
├── security_config.yaml              # 보안 설정 (선택, 생성 필요)
├── security_config.yaml.template     # 보안 설정 템플릿
├── prometheus.yml                    # Prometheus 설정
├── docker-compose.yml                # 기본 Docker Compose
├── docker-compose.enhanced.yml       # Enhanced Docker Compose ⭐
│
├── common/                           # 공통 모듈
│   ├── __init__.py
│   ├── auth.py                      # API 인증
│   ├── rate_limiter.py              # Rate limiting
│   ├── resilience.py                # Retry + Circuit breaker
│   ├── monitoring.py                # Prometheus
│   └── requirements.txt
│
└── TODO/
    ├── STARTUP_GUIDE.md             # 이 파일
    ├── scripts/
    │   ├── test_improvements.py     # 통합 테스트
    │   └── benchmark_system.py      # 성능 벤치마크
    └── ...
```

---

## ✅ Checklist

시작 전 확인 사항:

- [ ] Docker 및 Docker Compose 설치됨
- [ ] Python 3.8+ 설치됨
- [ ] `/home/uproot/ax/poc/common/requirements.txt` 설치됨
- [ ] `.env` 파일 생성 및 설정 완료
- [ ] `security_config.yaml` 생성 (보안 사용 시)
- [ ] 테스트 파일 준비됨 (도면 샘플)

시작 순서:

1. [ ] `.env` 파일 생성 및 수정
2. [ ] `docker-compose.enhanced.yml up -d` 실행
3. [ ] Health check 확인 (모든 서비스)
4. [ ] Prometheus 접속 (http://localhost:9090)
5. [ ] Grafana 접속 및 설정 (http://localhost:3000)
6. [ ] 통합 테스트 실행
7. [ ] 벤치마크 실행 (선택)

---

**작성일**: 2025-11-08
**버전**: 1.0
**다음 단계**: 프로덕션 배포 전 보안 설정 강화 (`PRIORITY_3_PRODUCTION.md` 참고)
