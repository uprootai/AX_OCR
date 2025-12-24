# 🏢 AX 도면 분석 시스템 - 온프레미스 납품 가이드

**문서 버전**: 1.0.0
**작성일**: 2025-11-14
**대상**: 온프레미스 환경 구축 및 납품

---

## 📋 목차

1. [시스템 개요](#1-시스템-개요)
2. [온프레미스 요구사항](#2-온프레미스-요구사항)
3. [보안 고려사항](#3-보안-고려사항)
4. [외부 의존성 제거 방안](#4-외부-의존성-제거-방안)
5. [모니터링 시스템 구성](#5-모니터링-시스템-구성)
6. [오프라인 설치 준비](#6-오프라인-설치-준비)
7. [납품 패키지 구성](#7-납품-패키지-구성)
8. [설치 절차](#8-설치-절차)
9. [고객사 교육 계획](#9-고객사-교육-계획)
10. [유지보수 가이드](#10-유지보수-가이드)

---

## 1. 시스템 개요

### 1.1 시스템 목적

제조업 도면으로부터 치수 데이터를 자동으로 추출하여 견적을 생성하는 AI 기반 시스템

**핵심 가치**:
- ⚡ **처리 속도**: 8-12초 (기존 수작업 30-60분 대비 300배 빠름)
- 🎯 **정확도**: 95-98% (인간 작업자 수준)
- 🔄 **모듈성**: API 교체 가능한 마이크로서비스 아키텍처
- 🏢 **온프레미스**: 폐쇄망 환경 지원, 데이터 외부 유출 없음

### 1.2 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                    Web UI (Port 5173)                    │
│              사용자 인터페이스 + Admin 대시보드             │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│                Gateway API (Port 8000)                    │
│              파이프라인 오케스트레이터                       │
│   • Hybrid Mode (정확도 95-98%, 10-15초)                  │
│   • Speed Mode (정확도 93%, 8-10초)                       │
└──┬────┬────┬────┬────┬────┬──────────────────────────────┘
   │    │    │    │    │    │
   ▼    ▼    ▼    ▼    ▼    ▼
┌─────┬──────┬──────┬──────┬──────┬────────┐
│eDOCr│ YOLO │EDGNet│ Skin │  VL  │Paddle  │
│ 5001│ 5005 │ 5012 │ 5003 │ 5004 │ 5006   │
│ GPU │ GPU  │ CPU  │  ML  │ API  │ CPU    │
│ OCR │ Det. │ Seg. │ Tol. │ LLM  │ OCR    │
└─────┴──────┴──────┴──────┴──────┴────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────┐
│          Monitoring Stack (Port 9090, 3000)              │
│          Prometheus + Grafana                            │
└──────────────────────────────────────────────────────────┘
```

### 1.3 주요 컴포넌트

| 컴포넌트 | 포트 | 기능 | GPU | 외부 의존성 |
|---------|------|------|-----|-----------|
| **Web UI** | 5173 | 사용자 인터페이스 | ❌ | ❌ |
| **Gateway API** | 8000 | 파이프라인 오케스트레이터 | ❌ | ❌ |
| **eDOCr2 API** | 5001 | 한글 OCR 엔진 | ✅ | ❌ |
| **YOLO API** | 5005 | 객체 탐지 | ✅ | ❌ |
| **EDGNet API** | 5012 | 그래프 기반 세그멘테이션 | ❌ | ❌ |
| **Skin Model API** | 5003 | 공차 예측 (XGBoost) | ❌ | ❌ |
| **VL API** | 5004 | Vision-Language 모델 | ❌ | ⚠️ **있음** |
| **PaddleOCR API** | 5006 | 중국어 OCR (선택) | ❌ | ❌ |
| **Prometheus** | 9090 | 메트릭 수집 | ❌ | ❌ |
| **Grafana** | 3000 | 모니터링 대시보드 | ❌ | ❌ |
| **Admin Dashboard** | 9000 | 관리자 백엔드 | ❌ | ❌ |

---

## 2. 온프레미스 요구사항

### 2.1 하드웨어 요구사항

#### 최소 사양 (테스트/개발 환경)

```
CPU: Intel Xeon E5-2640 v4 (10코어) 또는 동급
RAM: 32GB DDR4
GPU: NVIDIA RTX 3060 (12GB VRAM) 또는 동급
Storage: 500GB SSD
Network: 1Gbps Ethernet
```

#### 권장 사양 (프로덕션 환경)

```
CPU: Intel Xeon Gold 6248R (24코어) 또는 AMD EPYC 7402P
RAM: 64GB DDR4 ECC
GPU: NVIDIA RTX 3080 (16GB VRAM) 또는 A4000
Storage: 1TB NVMe SSD (시스템) + 2TB SSD (데이터)
Network: 10Gbps Ethernet
RAID: RAID 1 (데이터 백업)
UPS: 1500VA 이상 (정전 대비)
```

#### GPU 요구사항 상세

| API | GPU 필요 | VRAM 사용량 | 대안 (GPU 없을 시) |
|-----|---------|------------|-------------------|
| eDOCr2 | 필수 | 2-4GB | CPU 모드 (5배 느림) |
| YOLO | 필수 | 1-2GB | CPU 모드 (10배 느림) |
| EDGNet | 선택 | 0.5-1GB | CPU 모드 (2배 느림) |
| 기타 | 불필요 | - | - |

### 2.2 소프트웨어 요구사항

#### 운영체제

```
✅ 지원: Ubuntu 20.04/22.04 LTS
✅ 지원: CentOS 7.9+ / Rocky Linux 8+
✅ 지원: Red Hat Enterprise Linux 8+
❌ 미지원: Windows Server (Docker Desktop 제한 사항)
```

#### 필수 소프트웨어

```bash
# Docker Engine
Docker: 24.0.0+
Docker Compose: 2.20.0+

# NVIDIA GPU 드라이버 (GPU 사용 시)
NVIDIA Driver: 525.0+
NVIDIA Container Toolkit: latest

# 시스템 패키지
Python: 3.9+ (스크립트용)
curl, wget, tar, gzip
```

### 2.3 네트워크 요구사항

#### 포트 사용 (방화벽 설정 필요)

```bash
# 외부 접근 (사용자)
5173/tcp  - Web UI

# 내부 통신 (서비스 간)
8000/tcp  - Gateway API
5001/tcp  - eDOCr2 API
5005/tcp  - YOLO API
5012/tcp  - EDGNet API
5003/tcp  - Skin Model API
5004/tcp  - VL API
5006/tcp  - PaddleOCR API
9000/tcp  - Admin Dashboard API

# 모니터링 (관리자만)
9090/tcp  - Prometheus
3000/tcp  - Grafana

# SSH (관리자만)
22/tcp    - SSH 접속
```

#### 인터넷 연결

```
✅ 완전 오프라인 (폐쇄망): 지원
   - VL API 비활성화 또는 로컬 LLM 사용
   - 모든 Docker 이미지 사전 준비
   - 시스템 패키지 오프라인 번들

⚠️ 제한적 인터넷: 지원 (권장)
   - VL API만 인터넷 필요 (선택사항)
   - Docker Hub 접근 불필요 (사전 로드)
```

---

## 3. 보안 고려사항

### 3.1 데이터 보안

#### 도면 파일 처리

```
❌ 외부 저장소 업로드: 절대 없음
✅ 로컬 처리: 모든 처리 온프레미스 내부
✅ 임시 파일: 처리 후 자동 삭제 (24시간)
✅ 백업: 고객사 정책에 따름
```

#### 암호화

```python
# 저장 시 암호화 (AES-256)
ENCRYPTION_ENABLED = true
ENCRYPTION_KEY_PATH = /opt/ax-system/keys/encryption.key

# 전송 시 암호화 (TLS 1.3)
TLS_ENABLED = true
TLS_CERT_PATH = /opt/ax-system/certs/server.crt
TLS_KEY_PATH = /opt/ax-system/certs/server.key
```

### 3.2 접근 제어

#### 역할 기반 접근 제어 (RBAC)

| 역할 | 권한 | 접근 범위 |
|-----|------|----------|
| **관리자** | 전체 | 시스템 설정, 모델 관리, 사용자 관리, 모니터링 |
| **운영자** | 제한적 | 도면 처리, 로그 조회, 기본 모니터링 |
| **사용자** | 최소 | 도면 업로드, 결과 다운로드만 |
| **감사자** | 읽기 전용 | 감사 로그, 통계 조회만 |

#### 인증 방식

```yaml
# config/auth.yml
auth:
  method: api_key  # 또는 ldap, oauth2
  api_key:
    enabled: true
    header_name: X-API-Key
    keys:
      - key: "admin-key-xxxxx"
        role: admin
        description: "관리자 키"
      - key: "operator-key-xxxxx"
        role: operator
        description: "운영자 키"

  session:
    timeout: 3600  # 1시간
    max_concurrent: 3  # 동시 세션 제한
```

### 3.3 감사 로그

#### 로그 기록 항목

```json
{
  "timestamp": "2025-11-14T13:30:00Z",
  "user": "operator01",
  "action": "upload_drawing",
  "resource": "drawing_12345.pdf",
  "ip_address": "192.168.1.100",
  "result": "success",
  "processing_time": 12.5,
  "metadata": {
    "file_size": 2048576,
    "pages": 3
  }
}
```

#### 로그 보관

```
위치: /opt/ax-system/logs/audit/
형식: JSON Lines (JSONL)
보관 기간: 2년 (고객사 정책에 따름)
로테이션: 매일 (gzip 압축)
백업: 별도 스토리지에 자동 복사
```

### 3.4 네트워크 보안

#### 방화벽 규칙 (iptables)

```bash
# 기본 정책: 모두 차단
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 허용: Loopback
iptables -A INPUT -i lo -j ACCEPT

# 허용: 기존 연결 유지
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 허용: Web UI (특정 IP만)
iptables -A INPUT -p tcp --dport 5173 -s 192.168.1.0/24 -j ACCEPT

# 허용: SSH (특정 IP만)
iptables -A INPUT -p tcp --dport 22 -s 192.168.1.0/24 -j ACCEPT

# 허용: Prometheus/Grafana (관리자 네트워크만)
iptables -A INPUT -p tcp --dport 9090 -s 192.168.1.10 -j ACCEPT
iptables -A INPUT -p tcp --dport 3000 -s 192.168.1.10 -j ACCEPT

# 저장
iptables-save > /etc/iptables/rules.v4
```

#### Docker 네트워크 격리

```yaml
# docker-compose.yml
networks:
  frontend:
    driver: bridge
    internal: false  # 외부 접근 가능
  backend:
    driver: bridge
    internal: true   # 내부 통신만
  monitoring:
    driver: bridge
    internal: true   # 모니터링 전용
```

---

## 4. 외부 의존성 제거 방안

### 4.1 VL API 외부 의존성 분석

#### 현재 상태

```python
# vl-api/api_server.py
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 외부 API 호출
async def call_claude_vision(image, prompt):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",  # ❌ 외부 API
            headers={"x-api-key": ANTHROPIC_API_KEY},
            json=payload
        )
```

**문제점**:
- ❌ 도면 데이터가 외부 서버(Anthropic, OpenAI)로 전송됨
- ❌ 인터넷 연결 필수
- ❌ 폐쇄망 환경 사용 불가
- ❌ 비용 발생 (API 사용료)

### 4.2 해결 방안

#### 방안 1: VL API 비활성화 (권장)

VL API는 선택적 기능이므로 비활성화해도 핵심 기능 사용 가능

```yaml
# docker-compose.yml
services:
  vl-api:
    # image: vl-api:latest
    # 주석 처리하여 비활성화
    profiles:
      - optional  # 필요 시에만 활성화
```

```python
# gateway-api/api_server.py
# VL API 호출 부분을 옵션으로 변경
VL_ENABLED = os.getenv("VL_ENABLED", "false").lower() == "true"

if VL_ENABLED:
    vl_result = await call_vl_api(...)
else:
    logger.info("VL API disabled - skipping")
```

**장점**:
- ✅ 완전 오프라인 운영 가능
- ✅ 외부 데이터 유출 없음
- ✅ 즉시 적용 가능

**단점**:
- ⚠️ 정보 블록 추출 기능 사용 불가
- ⚠️ 고급 분석 기능 제한

#### 방안 2: 로컬 LLM으로 대체 (최적)

오픈소스 LLM을 로컬에서 실행하여 VL API 대체

**추천 모델**:
```
1. Llama 3.2 Vision (11B)
   - Meta 공개 모델
   - Vision-Language 지원
   - GPU 16GB 필요
   - 상업적 사용 가능

2. CogVLM2 (19B)
   - 중국어 강점
   - Vision-Language 전문
   - GPU 24GB 필요

3. LLaVA 1.6 (7B/13B)
   - 가벼운 모델
   - GPU 8GB~16GB
   - 빠른 추론 속도
```

**구현 예시** (Llama 3.2 Vision):

```python
# vl-api/local_llm.py
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq

class LocalVLM:
    def __init__(self, model_name="meta-llama/Llama-3.2-11B-Vision"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = AutoModelForVision2Seq.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )

    async def analyze_drawing(self, image, prompt):
        inputs = self.processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=500)

        result = self.processor.decode(outputs[0], skip_special_tokens=True)
        return result

# api_server.py에서 사용
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

if USE_LOCAL_LLM:
    vlm = LocalVLM()
else:
    vlm = None  # 외부 API 사용
```

**Docker 구성**:

```dockerfile
# vl-api/Dockerfile.local
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

RUN pip install torch transformers accelerate

# 모델 가중치 미리 다운로드 (오프라인 대비)
RUN python3 -c "from transformers import AutoModelForVision2Seq; \
                AutoModelForVision2Seq.from_pretrained('meta-llama/Llama-3.2-11B-Vision')"

COPY local_llm.py /app/
COPY api_server.py /app/

CMD ["python3", "/app/api_server.py"]
```

**장점**:
- ✅ 완전 오프라인 운영
- ✅ 외부 데이터 유출 없음
- ✅ API 비용 없음
- ✅ VL API 기능 유지

**단점**:
- ⚠️ GPU 메모리 추가 필요 (16GB+)
- ⚠️ 성능 약간 저하 (Claude 대비 90-95%)
- ⚠️ 모델 다운로드 크기 (20-40GB)

#### 방안 3: Hybrid 모드 (유연성)

온프레미스 + 클라우드 선택적 사용

```python
# config.yml
vl_mode: hybrid  # local, cloud, hybrid

vl_config:
  default: local  # 기본은 로컬 LLM
  fallback: cloud  # 실패 시 클라우드
  sensitive_data_policy: local_only  # 민감 데이터는 로컬만
```

### 4.3 권장 설정 (온프레미스)

```yaml
# config/deployment.yml
deployment:
  mode: onpremise
  internet: false

  vl_api:
    enabled: true
    mode: local  # local, cloud, disabled
    model: llama-3.2-11b-vision

  security:
    data_encryption: true
    audit_logging: true
    external_api_block: true
```

---

## 5. 모니터링 시스템 구성

### 5.1 Prometheus 설정

#### prometheus.yml

```yaml
# config/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'onpremise-production'
    site: 'customer-site-01'

# 알림 규칙
rule_files:
  - 'alerts/*.yml'

# 메트릭 수집 대상
scrape_configs:
  # Gateway API
  - job_name: 'gateway-api'
    static_configs:
      - targets: ['gateway-api:8000']
    metrics_path: '/metrics'

  # eDOCr2 API
  - job_name: 'edocr2-api'
    static_configs:
      - targets: ['edocr2-api:5001']

  # YOLO API
  - job_name: 'yolo-api'
    static_configs:
      - targets: ['yolo-api:5005']

  # EDGNet API
  - job_name: 'edgnet-api'
    static_configs:
      - targets: ['edgnet-api:5012']

  # Skin Model API
  - job_name: 'skinmodel-api'
    static_configs:
      - targets: ['skinmodel-api:5003']

  # Admin Dashboard
  - job_name: 'admin-dashboard'
    static_configs:
      - targets: ['admin-dashboard:9000']

  # Node Exporter (시스템 메트릭)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # NVIDIA GPU (nvidia-smi)
  - job_name: 'nvidia-gpu'
    static_configs:
      - targets: ['nvidia-gpu-exporter:9835']

# 데이터 보관
storage:
  tsdb:
    retention.time: 90d  # 90일
    retention.size: 50GB
```

#### 알림 규칙 (alerts/api_alerts.yml)

```yaml
# config/prometheus/alerts/api_alerts.yml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      # API 다운 알림
      - alert: APIDown
        expr: up{job=~".*-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API {{ $labels.job }} is down"
          description: "{{ $labels.job }} has been down for more than 1 minute"

      # 높은 에러율
      - alert: HighErrorRate
        expr: rate(http_requests_total{status="500"}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.job }}"
          description: "Error rate is {{ $value }}% over 5 minutes"

      # 느린 응답 시간
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time on {{ $labels.job }}"
          description: "95th percentile is {{ $value }}s"

      # GPU 메모리 부족
      - alert: GPUMemoryHigh
        expr: nvidia_gpu_memory_used_bytes / nvidia_gpu_memory_total_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU memory usage is high"
          description: "GPU {{ $labels.gpu }} memory usage is {{ $value }}%"

      # 디스크 공간 부족
      - alert: DiskSpaceLow
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space is running low"
          description: "Only {{ $value }}% disk space remaining"
```

### 5.2 Grafana 대시보드

#### 대시보드 1: 운영 대시보드 (고객사 IT팀용)

```json
{
  "dashboard": {
    "title": "AX 도면 분석 시스템 - 운영 현황",
    "panels": [
      {
        "title": "시스템 상태",
        "type": "stat",
        "targets": [{
          "expr": "up{job=~\".*-api\"}"
        }],
        "fieldConfig": {
          "overrides": [{
            "matcher": { "id": "byName", "options": "up" },
            "properties": [{
              "id": "thresholds",
              "value": {
                "steps": [
                  { "value": 0, "color": "red" },
                  { "value": 1, "color": "green" }
                ]
              }
            }]
          }]
        }
      },
      {
        "title": "처리된 도면 수 (일별)",
        "type": "graph",
        "targets": [{
          "expr": "sum(increase(drawings_processed_total[1d]))"
        }]
      },
      {
        "title": "평균 처리 시간",
        "type": "gauge",
        "targets": [{
          "expr": "avg(rate(processing_time_seconds_sum[5m]) / rate(processing_time_seconds_count[5m]))"
        }],
        "fieldConfig": {
          "thresholds": {
            "steps": [
              { "value": 0, "color": "green" },
              { "value": 10, "color": "yellow" },
              { "value": 20, "color": "red" }
            ]
          }
        }
      },
      {
        "title": "시스템 가용률 (SLA)",
        "type": "stat",
        "targets": [{
          "expr": "avg_over_time(up{job=\"gateway-api\"}[30d]) * 100"
        }],
        "fieldConfig": {
          "unit": "percent",
          "decimals": 2
        }
      }
    ]
  }
}
```

#### 대시보드 2: 기술 대시보드 (개발/유지보수팀용)

패널:
- API 응답 시간 (p50, p95, p99)
- GPU 메모리/활용률 추이
- 에러율 (5xx, 4xx)
- 처리량 (RPS)
- 큐 대기 시간

#### 대시보드 3: 경영진 대시보드

패널:
- 월별 처리 도면 수
- 평균 처리 시간 추이
- 시스템 가용률 (99.x%)
- 비용 절감 효과 (자동화 전후 비교)

### 5.3 알림 연동

#### 이메일 알림

```yaml
# config/grafana/provisioning/notifiers/email.yml
notifiers:
  - name: email-admin
    type: email
    uid: email-admin
    settings:
      addresses: admin@company.com
      singleEmail: false
    isDefault: true
```

#### Slack 알림 (선택)

```yaml
# config/grafana/provisioning/notifiers/slack.yml
notifiers:
  - name: slack-ops
    type: slack
    uid: slack-ops
    settings:
      url: https://hooks.slack.com/services/xxx/yyy/zzz
      recipient: '#ops-alerts'
```

---

## 6. 오프라인 설치 준비

### 6.1 Docker 이미지 Export

```bash
#!/bin/bash
# scripts/export_images.sh

echo "Docker 이미지 Export 시작..."

# 이미지 목록
IMAGES=(
    "poc_web-ui:latest"
    "poc_gateway-api:latest"
    "poc_edocr2-api:latest"
    "poc_yolo-api:latest"
    "poc_edgnet-api:latest"
    "poc_skinmodel-api:latest"
    "poc_vl-api:latest"
    "poc_paddleocr-api:latest"
    "prom/prometheus:latest"
    "grafana/grafana:latest"
    "prom/node-exporter:latest"
    "nvidia/gpu-exporter:latest"
)

# Export 디렉토리
EXPORT_DIR="./docker-images"
mkdir -p "$EXPORT_DIR"

# 각 이미지 Export
for IMAGE in "${IMAGES[@]}"; do
    FILENAME=$(echo $IMAGE | tr '/:' '_')
    echo "Exporting $IMAGE -> $FILENAME.tar"
    docker save "$IMAGE" -o "$EXPORT_DIR/$FILENAME.tar"

    # 압축 (선택)
    # gzip "$EXPORT_DIR/$FILENAME.tar"
done

echo "✅ Export 완료!"
echo "총 크기:"
du -sh "$EXPORT_DIR"
```

**Export 결과**:
```
docker-images/
├── poc_web-ui_latest.tar          (200 MB)
├── poc_gateway-api_latest.tar     (1.2 GB)
├── poc_edocr2-api_latest.tar      (2.5 GB)
├── poc_yolo-api_latest.tar        (1.8 GB)
├── poc_edgnet-api_latest.tar      (1.1 GB)
├── poc_skinmodel-api_latest.tar   (800 MB)
├── poc_vl-api_latest.tar          (500 MB)
├── poc_paddleocr-api_latest.tar   (600 MB)
├── prom_prometheus_latest.tar     (300 MB)
├── grafana_grafana_latest.tar     (400 MB)
├── prom_node-exporter_latest.tar  (50 MB)
└── nvidia_gpu-exporter_latest.tar (100 MB)

총 크기: ~9.5 GB
```

### 6.2 시스템 패키지 번들

```bash
#!/bin/bash
# scripts/prepare_offline_packages.sh

BUNDLE_DIR="./offline-packages"
mkdir -p "$BUNDLE_DIR"

# Python 패키지
pip download -r requirements.txt -d "$BUNDLE_DIR/python-wheels"

# 시스템 패키지 (Ubuntu)
apt-get download $(cat packages.txt) -d "$BUNDLE_DIR/deb-packages"

# 또는 CentOS/RHEL
# yumdownloader --resolve --destdir="$BUNDLE_DIR/rpm-packages" $(cat packages.txt)
```

### 6.3 모델 가중치 준비

```bash
# scripts/prepare_models.sh

MODEL_DIR="./model-weights"
mkdir -p "$MODEL_DIR"

# EDGNet Large
cp /home/uproot/ax/poc/edgnet-api/models/edgnet_large.pth "$MODEL_DIR/"

# YOLO
cp /home/uproot/ax/poc/yolo-api/models/yolo11n.pt "$MODEL_DIR/"

# Skin Model
cp -r /home/uproot/ax/poc/skinmodel-api/models/skinmodel_xgboost "$MODEL_DIR/"

# 로컬 LLM (선택)
# huggingface-cli download meta-llama/Llama-3.2-11B-Vision --local-dir "$MODEL_DIR/llama-3.2-11b-vision"
```

---

## 7. 납품 패키지 구성

### 7.1 최종 납품물 구조

```
AX_Drawing_Analysis_System_v1.0.0/
├── README.txt                          # 시작 가이드
├── LICENSE.txt                         # 라이선스
├── RELEASE_NOTES.txt                   # 릴리스 노트
│
├── docker-images/                      # Docker 이미지 (9.5GB)
│   ├── *.tar
│   └── checksums.txt                   # SHA256 체크섬
│
├── offline-packages/                   # 오프라인 패키지
│   ├── python-wheels/                  # Python 의존성
│   ├── deb-packages/                   # Ubuntu 패키지
│   └── rpm-packages/                   # CentOS 패키지
│
├── model-weights/                      # 학습된 모델 (2GB)
│   ├── edgnet_large.pth
│   ├── yolo11n.pt
│   ├── skinmodel_xgboost/
│   └── llama-3.2-11b-vision/ (선택)
│
├── scripts/                            # 설치/관리 스크립트
│   ├── install.sh                      # 자동 설치
│   ├── uninstall.sh                    # 제거
│   ├── backup.sh                       # 백업
│   ├── restore.sh                      # 복구
│   ├── check_system.sh                 # 사전 점검
│   ├── update.sh                       # 업데이트
│   ├── health_check.sh                 # 헬스 체크
│   └── export_logs.sh                  # 로그 추출
│
├── config/                             # 설정 파일
│   ├── docker-compose.yml              # 메인 구성
│   ├── docker-compose.monitoring.yml   # 모니터링
│   ├── .env.template                   # 환경변수 템플릿
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts/
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── provisioning/
│   └── nginx/
│       └── nginx.conf
│
├── docs/                               # 문서 (PDF)
│   ├── 00_빠른시작가이드.pdf
│   ├── 01_설치가이드.pdf
│   ├── 02_관리자매뉴얼.pdf
│   ├── 03_사용자가이드.pdf
│   ├── 04_트러블슈팅.pdf
│   ├── 05_API레퍼런스.pdf
│   ├── 06_보안가이드.pdf
│   ├── 07_백업복구가이드.pdf
│   └── 08_업그레이드가이드.pdf
│
├── training/                           # 교육 자료
│   ├── slides/                         # PPT
│   ├── hands-on/                       # 실습 자료
│   └── videos/                         # 동영상 (선택)
│
└── tools/                              # 유틸리티
    ├── test-dataset/                   # 테스트 도면
    ├── performance-test.sh             # 성능 테스트
    └── migration-tool.py               # 데이터 마이그레이션
```

### 7.2 체크섬 생성

```bash
# scripts/generate_checksums.sh

cd docker-images
sha256sum *.tar > checksums.txt

# 검증
sha256sum -c checksums.txt
```

---

## 8. 설치 절차

### 8.1 사전 점검

```bash
#!/bin/bash
# scripts/check_system.sh

echo "==================================="
echo "AX 시스템 요구사항 점검"
echo "==================================="

# OS 확인
echo -n "OS 확인: "
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "$NAME $VERSION"
else
    echo "❌ 지원하지 않는 OS"
    exit 1
fi

# CPU 확인
echo -n "CPU 코어: "
CORES=$(nproc)
echo "$CORES cores"
if [ $CORES -lt 8 ]; then
    echo "⚠️  경고: 최소 10코어 권장"
fi

# RAM 확인
echo -n "메모리: "
RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
echo "${RAM_GB}GB"
if [ $RAM_GB -lt 32 ]; then
    echo "❌ 오류: 최소 32GB 필요"
    exit 1
fi

# GPU 확인
echo -n "GPU 확인: "
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    echo "$GPU_NAME"

    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    echo "  VRAM: ${GPU_MEM}MB"

    if [ $GPU_MEM -lt 8000 ]; then
        echo "⚠️  경고: 최소 8GB VRAM 권장"
    fi
else
    echo "❌ GPU 없음 (CPU 모드 - 느림)"
fi

# Docker 확인
echo -n "Docker: "
if command -v docker &> /dev/null; then
    DOCKER_VER=$(docker --version | awk '{print $3}' | tr -d ',')
    echo "$DOCKER_VER"
else
    echo "❌ Docker 미설치"
    exit 1
fi

# Docker Compose 확인
echo -n "Docker Compose: "
if command -v docker-compose &> /dev/null; then
    COMPOSE_VER=$(docker-compose --version | awk '{print $4}' | tr -d ',')
    echo "$COMPOSE_VER"
else
    echo "❌ Docker Compose 미설치"
    exit 1
fi

# 디스크 공간
echo -n "디스크 공간: "
DISK_AVAIL=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
echo "${DISK_AVAIL}GB 사용 가능"
if [ $DISK_AVAIL -lt 100 ]; then
    echo "❌ 오류: 최소 100GB 필요"
    exit 1
fi

echo "==================================="
echo "✅ 모든 요구사항 충족!"
echo "==================================="
```

### 8.2 자동 설치 스크립트

```bash
#!/bin/bash
# scripts/install.sh

set -e  # 에러 시 중단

echo "===================================="
echo "AX 도면 분석 시스템 설치 시작"
echo "===================================="

# 1. 사전 점검
echo "[1/7] 시스템 요구사항 점검..."
./scripts/check_system.sh || exit 1

# 2. 설치 디렉토리 생성
echo "[2/7] 설치 디렉토리 생성..."
INSTALL_DIR="/opt/ax-system"
sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER "$INSTALL_DIR"

# 3. Docker 이미지 로드
echo "[3/7] Docker 이미지 로딩 중... (약 5분 소요)"
for img in docker-images/*.tar; do
    echo "  Loading $(basename $img)..."
    docker load < "$img"
done

# 4. 설정 파일 복사
echo "[4/7] 설정 파일 복사..."
cp -r config/* "$INSTALL_DIR/"
cp docker-compose.yml "$INSTALL_DIR/"

# 환경변수 설정
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp config/.env.template "$INSTALL_DIR/.env"
    echo "⚠️  .env 파일을 수정하세요: $INSTALL_DIR/.env"
fi

# 5. 데이터 디렉토리 생성
echo "[5/7] 데이터 디렉토리 생성..."
mkdir -p "$INSTALL_DIR/data"/{models,uploads,logs,backups}
mkdir -p "$INSTALL_DIR/prometheus-data"
mkdir -p "$INSTALL_DIR/grafana-data"

# 6. 모델 가중치 복사
echo "[6/7] 모델 가중치 복사..."
cp -r model-weights/* "$INSTALL_DIR/data/models/"

# 7. 시스템 시작
echo "[7/7] 시스템 시작..."
cd "$INSTALL_DIR"
docker-compose up -d

# 헬스 체크 대기
echo "시스템 시작 대기 중... (30초)"
sleep 30

# 헬스 체크
echo "헬스 체크 실행..."
./scripts/health_check.sh

echo "===================================="
echo "✅ 설치 완료!"
echo "===================================="
echo ""
echo "📌 접속 정보:"
echo "  Web UI: http://localhost:5173"
echo "  Admin 대시보드: http://localhost:5173/admin"
echo "  Grafana: http://localhost:3000 (admin/admin)"
echo "  API 문서: http://localhost:8000/docs"
echo ""
echo "📖 다음 단계:"
echo "  1. .env 파일 수정: $INSTALL_DIR/.env"
echo "  2. Grafana 비밀번호 변경"
echo "  3. 관리자 매뉴얼 참조: docs/02_관리자매뉴얼.pdf"
echo ""
```

### 8.3 헬스 체크

```bash
#!/bin/bash
# scripts/health_check.sh

SERVICES=(
    "http://localhost:8000/api/v1/health"
    "http://localhost:5001/api/v1/health"
    "http://localhost:5005/api/v1/health"
    "http://localhost:5012/api/v1/health"
    "http://localhost:5003/api/v1/health"
    "http://localhost:9000/api/status"
)

echo "==================================="
echo "헬스 체크"
echo "==================================="

ALL_HEALTHY=true

for URL in "${SERVICES[@]}"; do
    SERVICE=$(echo $URL | awk -F'//' '{print $2}' | awk -F'/' '{print $1}')

    if curl -sf "$URL" > /dev/null; then
        echo "✅ $SERVICE: OK"
    else
        echo "❌ $SERVICE: FAIL"
        ALL_HEALTHY=false
    fi
done

echo "==================================="
if [ "$ALL_HEALTHY" = true ]; then
    echo "✅ 모든 서비스 정상"
    exit 0
else
    echo "❌ 일부 서비스 오류"
    exit 1
fi
```

---

## 9. 고객사 교육 계획

### 9.1 교육 과정 (2일)

#### Day 1: 운영자 교육

**시간표**:
```
09:00 - 09:30  오리엔테이션 및 시스템 소개
09:30 - 10:30  시스템 아키텍처 이해
10:30 - 10:45  휴식
10:45 - 12:00  Admin Dashboard 사용법

12:00 - 13:00  점심

13:00 - 14:00  Grafana 모니터링 대시보드
14:00 - 15:00  Docker 관리 (시작/중지/재시작)
15:00 - 15:15  휴식
15:15 - 16:30  로그 분석 및 기본 트러블슈팅
16:30 - 17:00  Q&A 및 실습
```

**실습 내용**:
1. 도면 업로드 및 처리
2. Admin Dashboard에서 시스템 상태 확인
3. Grafana에서 메트릭 조회
4. Docker 컨테이너 재시작
5. 로그 파일 확인

#### Day 2: 관리자 교육

**시간표**:
```
09:00 - 10:00  모델 재학습 방법
10:00 - 11:00  백업/복구 실습
11:00 - 12:00  성능 튜닝 및 최적화

12:00 - 13:00  점심

13:00 - 14:00  보안 설정 및 권한 관리
14:00 - 15:00  시스템 업그레이드 방법
15:00 - 15:15  휴식
15:15 - 16:30  장애 대응 시나리오 실습
16:30 - 17:00  종합 Q&A 및 수료증 발급
```

**실습 내용**:
1. EDGNet 모델 재학습
2. 전체 시스템 백업 생성
3. 백업에서 복구
4. API 키 추가/삭제
5. 모의 장애 대응

### 9.2 교육 자료

```
training/
├── slides/
│   ├── Day1_시스템소개.pptx
│   ├── Day1_운영자교육.pptx
│   ├── Day2_관리자교육.pptx
│   └── Day2_장애대응.pptx
│
├── hands-on/
│   ├── 01_첫도면처리.md
│   ├── 02_모니터링.md
│   ├── 03_백업복구.md
│   └── 04_장애시나리오.md
│
└── cheat-sheets/
    ├── docker-commands.pdf
    ├── grafana-queries.pdf
    └── troubleshooting-guide.pdf
```

---

## 10. 유지보수 가이드

### 10.1 백업

#### 자동 백업 스크립트

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/opt/ax-system/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ax-system-backup-$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

mkdir -p "$BACKUP_PATH"

echo "백업 시작: $BACKUP_NAME"

# 1. Docker 볼륨 백업
docker run --rm \
  -v ax-system_models:/data \
  -v "$BACKUP_PATH":/backup \
  alpine tar czf /backup/models.tar.gz -C /data .

# 2. 설정 파일 백업
tar czf "$BACKUP_PATH/config.tar.gz" /opt/ax-system/config

# 3. Prometheus 데이터 백업
tar czf "$BACKUP_PATH/prometheus.tar.gz" /opt/ax-system/prometheus-data

# 4. Grafana 데이터 백업
tar czf "$BACKUP_PATH/grafana.tar.gz" /opt/ax-system/grafana-data

# 5. 감사 로그 백업
tar czf "$BACKUP_PATH/audit-logs.tar.gz" /opt/ax-system/logs

# 6. 메타데이터
echo "$TIMESTAMP" > "$BACKUP_PATH/metadata.txt"
echo "Hostname: $(hostname)" >> "$BACKUP_PATH/metadata.txt"
docker-compose config > "$BACKUP_PATH/docker-compose.yml"

echo "✅ 백업 완료: $BACKUP_PATH"

# 오래된 백업 삭제 (30일 이상)
find "$BACKUP_DIR" -type d -name "ax-system-backup-*" -mtime +30 -exec rm -rf {} \;
```

#### Cron 설정 (매일 자동 백업)

```bash
# crontab -e
0 2 * * * /opt/ax-system/scripts/backup.sh >> /opt/ax-system/logs/backup.log 2>&1
```

### 10.2 복구

```bash
#!/bin/bash
# scripts/restore.sh

if [ -z "$1" ]; then
    echo "사용법: $0 <백업디렉토리>"
    echo "예시: $0 /opt/ax-system/backups/ax-system-backup-20251114_020000"
    exit 1
fi

BACKUP_PATH="$1"

echo "복구 시작: $BACKUP_PATH"

# 시스템 중지
cd /opt/ax-system
docker-compose down

# 복구
tar xzf "$BACKUP_PATH/models.tar.gz" -C /opt/ax-system/data/models
tar xzf "$BACKUP_PATH/config.tar.gz" -C /
tar xzf "$BACKUP_PATH/prometheus.tar.gz" -C /opt/ax-system
tar xzf "$BACKUP_PATH/grafana.tar.gz" -C /opt/ax-system

# 시스템 시작
docker-compose up -d

echo "✅ 복구 완료"
```

### 10.3 업데이트

```bash
#!/bin/bash
# scripts/update.sh

NEW_VERSION="$1"

if [ -z "$NEW_VERSION" ]; then
    echo "사용법: $0 <버전>"
    echo "예시: $0 1.1.0"
    exit 1
fi

echo "업데이트 시작: v$NEW_VERSION"

# 1. 백업
./scripts/backup.sh

# 2. 새 이미지 로드
docker load < updates/v$NEW_VERSION/*.tar

# 3. Docker Compose 업데이트
cp updates/v$NEW_VERSION/docker-compose.yml /opt/ax-system/

# 4. 재시작
cd /opt/ax-system
docker-compose up -d

echo "✅ 업데이트 완료"
```

---

## 부록

### A. 트러블슈팅

| 증상 | 원인 | 해결 방법 |
|------|------|----------|
| GPU out of memory | VRAM 부족 | batch_size 줄이기, 불필요한 모델 종료 |
| API 응답 느림 | 높은 부하 | 리소스 증설, 파이프라인 모드 변경 |
| Docker 시작 실패 | 포트 충돌 | netstat -tulpn으로 확인, 포트 변경 |

### B. 성능 튜닝

```yaml
# docker-compose.yml
services:
  gateway-api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

### C. 라이선스

```
상업적 라이선스
온프레미스 단일 서버 라이선스
```

---

**문서 버전**: 1.0.0
**최종 수정**: 2025-11-14
**작성자**: AX 개발팀
