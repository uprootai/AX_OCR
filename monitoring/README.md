# AX POC 모니터링 스택

Prometheus + Grafana + Loki 기반 모니터링 시스템

## 구성 요소

| 서비스 | 포트 | 용도 |
|--------|------|------|
| **Grafana** | 3000 | 대시보드 시각화 |
| **Prometheus** | 9090 | 메트릭 수집/저장 |
| **Loki** | 3100 | 로그 집계 |
| **Promtail** | - | Docker 로그 수집기 |
| **Node Exporter** | 9100 | 시스템 메트릭 |
| **cAdvisor** | 8080 | 컨테이너 메트릭 |

## 시작하기

```bash
# 1. AX POC 메인 서비스가 실행 중인지 확인
docker network ls | grep ax_poc_network

# 2. 모니터링 스택 시작
docker-compose -f docker-compose.monitoring.yml up -d

# 3. Grafana 접속
open http://localhost:3000
# ID: admin / PW: admin
```

## 대시보드

### 1. 시스템 현황 (AX POC - 시스템 현황)

- CPU/메모리/디스크 사용률
- 실행 중인 컨테이너 수
- API 컨테이너별 CPU/메모리 사용량
- 최근 에러 로그

## 로그 조회

Grafana → Explore → Loki 선택

```logql
# 모든 API 로그
{container=~".*api.*"}

# 에러 로그만
{container=~".*api.*"} |~ "(?i)(error|exception|fail)"

# 특정 API 로그
{container="yolo-api"}

# JSON 필드 파싱
{container=~".*api.*"} | json | level="ERROR"
```

## 메트릭 조회

Grafana → Explore → Prometheus 선택

```promql
# 컨테이너 CPU 사용률
rate(container_cpu_usage_seconds_total{name=~".*api.*"}[5m]) * 100

# 컨테이너 메모리 사용량
container_memory_usage_bytes{name=~".*api.*"}

# 시스템 CPU 사용률
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 시스템 메모리 사용률
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

## 데이터 보존

- Prometheus: 15일
- Loki: 15일

## 중지

```bash
docker-compose -f docker-compose.monitoring.yml down

# 데이터 볼륨도 삭제
docker-compose -f docker-compose.monitoring.yml down -v
```

## 문제 해결

### 네트워크 에러
```bash
# ax_poc_network가 없으면 생성
docker network create ax_poc_network
```

### Promtail 로그 수집 안됨
```bash
# Docker 소켓 권한 확인
ls -la /var/run/docker.sock
# srw-rw---- 필요
```

### Grafana 대시보드 안보임
1. Grafana → Data sources → 연결 테스트
2. Configuration → Data sources → Prometheus/Loki URL 확인
