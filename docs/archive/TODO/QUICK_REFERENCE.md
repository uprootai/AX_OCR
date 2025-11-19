# 🚀 Quick Reference - 빠른 참조 가이드

**목적**: 가장 자주 사용하는 명령어와 설정을 한눈에 볼 수 있는 치트시트

---

## 🎯 시작하기 (5분 안에)

### 1. 기본 모드로 시작 (개선사항 없이)

```bash
cd /home/uproot/ax/poc
docker-compose up -d
```

### 2. Enhanced 모드로 시작 (모든 개선사항 포함) ⭐ 추천

```bash
# .env 파일 생성
cp .env.template .env

# 시스템 시작
docker-compose -f docker-compose.enhanced.yml up -d

# 로그 확인
docker-compose -f docker-compose.enhanced.yml logs -f
```

### 3. 서비스 확인

```bash
# Health check (한 줄에)
curl -s http://localhost:8000/api/v1/health && \
curl -s http://localhost:5001/api/v1/health && \
curl -s http://localhost:5002/api/v2/health && \
echo "All services healthy!"
```

---

## 📊 모니터링 접속

| 서비스 | URL | 용도 |
|--------|-----|------|
| Gateway API | http://localhost:8000 | 메인 API |
| eDOCr2 v1 | http://localhost:5001 | OCR v1 |
| eDOCr2 v2 | http://localhost:5002 | OCR v2 (테이블 지원) |
| EDGNet | http://localhost:5012 | 세그멘테이션 |
| Skin Model | http://localhost:5003 | 공차 예측 |
| Web UI | http://localhost:5173 | 웹 인터페이스 |
| Prometheus | http://localhost:9090 | 메트릭 수집 |
| Grafana | http://localhost:3000 | 대시보드 (admin/admin) |

---

## 🔧 자주 사용하는 명령어

### Docker Compose

```bash
# 시작
docker-compose -f docker-compose.enhanced.yml up -d

# 중지
docker-compose -f docker-compose.enhanced.yml down

# 재시작
docker-compose -f docker-compose.enhanced.yml restart

# 특정 서비스만 재시작
docker-compose -f docker-compose.enhanced.yml restart gateway-api

# 로그 보기 (실시간)
docker-compose -f docker-compose.enhanced.yml logs -f

# 특정 서비스 로그만
docker-compose -f docker-compose.enhanced.yml logs -f gateway-api

# 컨테이너 상태 확인
docker-compose -f docker-compose.enhanced.yml ps
```

### API 테스트

```bash
# Health check 전체
./test_apis.sh

# OCR 테스트 (v1)
curl -X POST http://localhost:5001/api/v1/ocr \
  -F "file=@drawing.pdf" \
  -F "extract_dimensions=true"

# OCR 테스트 (v2, 테이블 포함)
curl -X POST http://localhost:5002/api/v2/ocr \
  -F "file=@drawing.pdf" \
  -F "extract_tables=true"

# Gateway 전체 파이프라인
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@drawing.pdf"
```

### 인증 포함 API 호출

```bash
# API 키와 함께 요청
curl -H "X-API-Key: your-api-key-here" \
     http://localhost:8000/api/v1/protected

# 환경변수에서 API 키 읽기
curl -H "X-API-Key: $API_KEY" \
     http://localhost:8000/api/v1/protected
```

---

## 🔒 보안 설정 (1분)

### 개발 환경 (보안 비활성화)

```bash
# .env 파일
ENABLE_AUTH=false
ENABLE_RATE_LIMIT=false
```

### 프로덕션 환경 (보안 활성화)

```bash
# API 키 생성
openssl rand -hex 32

# .env 파일
ENABLE_AUTH=true
API_KEY=<생성된-키>
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=30
```

---

## 🧪 테스트 실행

### 통합 테스트

```bash
# 모든 개선 사항 테스트
python /home/uproot/ax/poc/TODO/scripts/test_improvements.py
```

### 성능 벤치마크

```bash
# 시스템 성능 측정
python /home/uproot/ax/poc/TODO/scripts/benchmark_system.py

# 결과 확인
cat /home/uproot/ax/poc/benchmark_results.json
```

### 전체 시스템 데모

```bash
# 모든 기능 데모
python /home/uproot/ax/poc/TODO/scripts/demo_full_system.py
```

---

## 📈 Prometheus 쿼리

### 자주 사용하는 메트릭

```promql
# 초당 요청 수
rate(http_requests_total[5m])

# 평균 응답 시간
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# 에러율 (%)
100 * rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])

# OCR 성공률 (%)
100 * rate(ocr_processing_total{status="success"}[5m]) / rate(ocr_processing_total[5m])

# Circuit breaker 상태 (1=OPEN, 0=CLOSED)
circuit_breaker_state

# p95 응답 시간
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

---

## 🔍 Circuit Breaker 상태 확인

```bash
# 모든 circuit breaker 상태
curl http://localhost:8000/api/v1/circuit-breakers

# 예쁘게 출력 (jq 필요)
curl -s http://localhost:8000/api/v1/circuit-breakers | jq
```

---

## ⚙️ 환경변수 설정

### 필수 설정

```bash
# .env 파일
ENABLE_AUTH=false              # 인증 활성화 여부
API_KEY=                       # API 키 (ENABLE_AUTH=true 시)
ENABLE_RATE_LIMIT=false        # Rate limiting 활성화 여부
```

### 선택 설정

```bash
# Rate limiting
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500
RATE_LIMIT_PER_DAY=3000

# Circuit breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60

# Retry
RETRY_MAX_ATTEMPTS=3
RETRY_INITIAL_DELAY=1.0

# Logging
GATEWAY_LOG_LEVEL=info
EDOCR2_LOG_LEVEL=info
```

---

## 🐛 문제 해결

### 포트 충돌

```bash
# 포트 사용 확인
sudo lsof -i :8000
sudo lsof -i :5001

# 프로세스 종료
sudo kill -9 <PID>
```

### 컨테이너 재빌드

```bash
# 캐시 없이 재빌드
docker-compose -f docker-compose.enhanced.yml build --no-cache

# 재빌드 후 시작
docker-compose -f docker-compose.enhanced.yml up -d --build
```

### 볼륨 초기화

```bash
# 모든 볼륨 삭제 (주의!)
docker-compose -f docker-compose.enhanced.yml down -v

# 재시작
docker-compose -f docker-compose.enhanced.yml up -d
```

### 로그 확인

```bash
# 전체 로그
docker-compose -f docker-compose.enhanced.yml logs

# 최근 100줄만
docker-compose -f docker-compose.enhanced.yml logs --tail=100

# 특정 서비스
docker-compose -f docker-compose.enhanced.yml logs gateway-api
```

---

## 📚 관련 문서

| 문서 | 용도 |
|------|------|
| `QUICKSTART.md` | 빠른 시작 (5분) |
| `STARTUP_GUIDE.md` | 상세 시작 가이드 |
| `INTEGRATION_GUIDE.md` | 코드 통합 방법 |
| `FINAL_SUMMARY.md` | 전체 요약 |
| `PRIORITY_1_*.md` | 우선순위 1 작업 (중요) |
| `PRIORITY_2_*.md` | 우선순위 2 작업 |
| `PRIORITY_3_*.md` | 우선순위 3 작업 |

---

## 🎯 다음 단계

### 개발 환경
```bash
1. docker-compose.enhanced.yml로 시스템 시작
2. http://localhost:5173에서 Web UI 접속
3. http://localhost:9090에서 Prometheus 확인
```

### 프로덕션 준비
```bash
1. .env 파일에서 보안 설정 활성화
2. security_config.yaml 커스터마이징
3. Grafana 대시보드 설정
4. 성능 벤치마크 실행
5. PRIORITY_3_PRODUCTION.md 참고
```

### 정확도 개선
```bash
1. GD&T 도면 10개 수집 → PRIORITY_1_GDT_DRAWINGS.md
2. VL API 키 발급 → PRIORITY_1_VL_API_KEYS.md
3. Skin Model 데이터 수집 → PRIORITY_2_SKIN_MODEL_DATA.md
```

---

**최종 업데이트**: 2025-11-08
**버전**: 1.0
