# 🟢 우선순위 3-2: 프로덕션 배포 준비

**목적**: 개발 환경 → 프로덕션 환경으로 전환
**소요 시간**: 3-5일
**담당자**: DevOps 엔지니어

---

## 📋 프로덕션 체크리스트

### ✅ 완료 필요 항목

#### 보안
- [ ] API 인증 활성화
- [ ] HTTPS/SSL 설정
- [ ] Rate limiting 적용
- [ ] 환경변수 암호화
- [ ] 시크릿 관리 (Vault, AWS Secrets Manager)

#### 안정성
- [ ] Retry 로직 구현
- [ ] Circuit breaker 추가
- [ ] Health check 강화
- [ ] Graceful shutdown
- [ ] 자동 재시작 정책

#### 모니터링
- [ ] Prometheus 메트릭 수집
- [ ] Grafana 대시보드 구축
- [ ] 로그 중앙화 (ELK Stack)
- [ ] 알림 설정 (Slack, Email)

#### 성능
- [ ] GPU 설정
- [ ] 캐싱 (Redis)
- [ ] CDN (정적 파일)
- [ ] Load balancer

#### 백업
- [ ] 데이터 백업 전략
- [ ] 모델 버전 관리
- [ ] 재해 복구 계획

---

## 🏗️ 인프라 구조

### 개발 환경 (현재)
```
Docker Compose (로컬)
├── 5개 컨테이너
├── Host network
└── Volume mount
```

### 프로덕션 환경 (목표)

#### 옵션 A: Docker Swarm
```
Docker Swarm Cluster
├── Manager Node x 3
├── Worker Node x 5
├── Load Balancer (Traefik)
├── Service Mesh
└── Persistent Volume (NFS)
```

#### 옵션 B: Kubernetes
```
Kubernetes Cluster
├── Control Plane x 3
├── Worker Node x 5
├── Ingress Controller (Nginx)
├── Service Mesh (Istio)
└── Persistent Volume (Ceph, AWS EBS)
```

#### 옵션 C: Cloud PaaS
```
AWS/Azure/GCP
├── ECS/AKS/GKE
├── RDS (데이터베이스)
├── S3 (파일 저장)
├── CloudWatch (모니터링)
└── ALB/NLB (Load Balancer)
```

### 결정 사항

**선택한 배포 환경**: _______________

---

## 🔧 설정 파일

### 프로덕션 docker-compose.yml

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  gateway-api:
    image: gateway-api:1.0.0
    environment:
      - ENV=production
      - LOG_LEVEL=warning
      - ENABLE_AUTH=true
      - RATE_LIMIT=100
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 환경변수 관리

```bash
# .env.production
ENV=production
LOG_LEVEL=warning
DEBUG=false

# API Keys (암호화 필요)
OPENAI_API_KEY=${VAULT_OPENAI_KEY}
ANTHROPIC_API_KEY=${VAULT_ANTHROPIC_KEY}

# Database
DB_HOST=db.production.internal
DB_PORT=5432
DB_NAME=ax_drawings
DB_USER=${VAULT_DB_USER}
DB_PASSWORD=${VAULT_DB_PASSWORD}

# Redis
REDIS_HOST=redis.production.internal
REDIS_PORT=6379
REDIS_PASSWORD=${VAULT_REDIS_PASSWORD}

# Monitoring
PROMETHEUS_URL=prometheus.production.internal:9090
GRAFANA_URL=grafana.production.internal:3000
```

---

## 🚀 배포 프로세스

### 1. CI/CD 파이프라인

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker images
        run: docker-compose -f docker-compose.prod.yml build
      - name: Push to registry
        run: docker-compose -f docker-compose.prod.yml push

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          ssh production "cd /opt/ax-drawings && \
            docker-compose -f docker-compose.prod.yml pull && \
            docker-compose -f docker-compose.prod.yml up -d"
```

### 2. 배포 단계

```bash
# 1. 이미지 빌드
docker-compose -f docker-compose.prod.yml build

# 2. 이미지 푸시 (Docker Hub/AWS ECR)
docker-compose -f docker-compose.prod.yml push

# 3. 프로덕션 서버 접속
ssh production-server

# 4. 이미지 풀
docker-compose -f docker-compose.prod.yml pull

# 5. 서비스 재시작 (무중단)
docker-compose -f docker-compose.prod.yml up -d --no-deps --build gateway-api

# 6. 헬스 체크
curl https://api.production.com/health
```

---

## 📊 모니터링 대시보드

### Grafana 패널

1. **시스템 메트릭**
   - CPU/Memory 사용률
   - Disk I/O
   - Network 트래픽

2. **API 메트릭**
   - 요청 수 (QPS)
   - 응답 시간 (P50, P95, P99)
   - 에러율
   - Uptime

3. **비즈니스 메트릭**
   - 도면 처리 수
   - 성공/실패 비율
   - 평균 처리 시간
   - 전략별 사용 분포

### 알림 규칙

```yaml
# alerts.yml
groups:
  - name: production_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status="500"}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: ServiceDown
        expr: up{job="gateway-api"} == 0
        for: 1m
        annotations:
          summary: "Gateway API is down"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds[5m])) > 10
        for: 10m
        annotations:
          summary: "95th percentile response time > 10s"
```

---

## ✅ 배포 전 체크리스트

### 기술적 준비
- [ ] 모든 서비스 health check 통과
- [ ] 부하 테스트 완료 (100 req/s)
- [ ] 보안 감사 완료
- [ ] 백업 시스템 테스트
- [ ] 롤백 계획 수립

### 문서화
- [ ] 운영 매뉴얼 작성
- [ ] 장애 대응 가이드
- [ ] API 문서 최신화
- [ ] 변경 이력 기록

### 팀 준비
- [ ] 운영팀 교육 완료
- [ ] On-call 체계 구축
- [ ] 비상 연락망 확인
- [ ] 배포 일정 공지

---

## 🚨 롤백 계획

### 즉시 롤백 조건
1. 에러율 > 10%
2. 응답 시간 > 30초
3. 서비스 다운 > 5분
4. 데이터 손실 발생

### 롤백 절차

```bash
# 1. 이전 버전으로 롤백
docker-compose -f docker-compose.prod.yml down
docker tag gateway-api:1.0.0 gateway-api:rollback
docker-compose -f docker-compose.prod.yml up -d

# 2. 헬스 체크
./scripts/health_check.sh

# 3. 로그 확인
docker-compose logs -f

# 4. 사후 분석
./scripts/incident_report.sh
```

---

## ✅ 완료 확인

```bash
# 1. 프로덕션 접속
curl https://api.production.com/health
# 출력: {"status": "healthy"}

# 2. 모니터링 확인
open https://grafana.production.com/d/overview

# 3. 부하 테스트
ab -n 1000 -c 100 https://api.production.com/api/v1/health

# 4. 알림 테스트
# 서비스 중단 → Slack 알림 수신 확인
```

---

**작성일**: 2025-11-08
**예상 소요 시간**: 3-5일
**최종 목표**: 99.9% Uptime, <1s P95 response time
