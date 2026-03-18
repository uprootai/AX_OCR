---
sidebar_position: 2
title: 온프레미스 인프라 구성
description: 하드웨어/소프트웨어 요구사항, 네트워크/보안 설정, 모니터링, 오프라인 설치, 납품 패키지 구성
tags: [배포, 운영, 온프레미스, 인프라]
---

# 온프레미스 인프라 구성 (On-Premise Infrastructure)

> 하드웨어/소프트웨어 요구사항, 네트워크/보안 설정, 모니터링, 오프라인 설치 절차를 정리한다.

## 1. 시스템 개요

### 1.1 시스템 목적

제조업 도면으로부터 치수 데이터를 자동으로 추출하여 견적을 생성하는 AI 기반 시스템.

**주요 특성**:
- **처리 시간**: 8-12초 (수작업 30-60분 대비)
- **정확도**: 95-98%
- **모듈성**: API 교체 가능한 마이크로서비스 아키텍처
- **온프레미스**: 폐쇄망 환경 지원, 데이터 외부 유출 없음

### 1.2 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                    Web UI (Port 5173)                    │
│              사용자 인터페이스 + Admin 대시보드             │
└────────────────────┬─────────────────────────────────────┘
                     │
                     v
┌──────────────────────────────────────────────────────────┐
│                Gateway API (Port 8000)                    │
│              파이프라인 오케스트레이터                       │
│   - Hybrid Mode (정확도 95-98%, 10-15초)                  │
│   - Speed Mode (정확도 93%, 8-10초)                       │
└──┬────┬────┬────┬────┬────┬──────────────────────────────┘
   │    │    │    │    │    │
   v    v    v    v    v    v
┌─────┬──────┬──────┬──────┬──────┬────────┐
│eDOCr│ YOLO │EDGNet│ Skin │  VL  │Paddle  │
│ 5001│ 5005 │ 5012 │ 5003 │ 5004 │ 5006   │
│ GPU │ GPU  │ CPU  │  ML  │ API  │ CPU    │
│ OCR │ Det. │ Seg. │ Tol. │ LLM  │ OCR    │
└─────┴──────┴──────┴──────┴──────┴────────┘
   │
   v
┌──────────────────────────────────────────────────────────┐
│          Monitoring Stack (Port 9090, 3000)              │
│          Prometheus + Grafana                            │
└──────────────────────────────────────────────────────────┘
```

### 1.3 주요 컴포넌트

| 컴포넌트 | 포트 | 기능 | GPU | 외부 의존성 |
|---------|------|------|-----|-----------|
| **Web UI** | 5173 | 사용자 인터페이스 | - | - |
| **Gateway API** | 8000 | 파이프라인 오케스트레이터 | - | - |
| **eDOCr2 API** | 5002 | 한글 OCR 엔진 | Yes | - |
| **YOLO API** | 5005 | 객체 탐지 | Yes | - |
| **EDGNet API** | 5012 | 그래프 기반 세그멘테이션 | - | - |
| **Skin Model API** | 5003 | 공차 예측 (XGBoost) | - | - |
| **VL API** | 5004 | Vision-Language 모델 | - | 있음 (선택적) |
| **PaddleOCR API** | 5006 | 중국어 OCR (선택) | - | - |
| **Prometheus** | 9090 | 메트릭 수집 | - | - |
| **Grafana** | 3001 | 모니터링 대시보드 | - | - |

---

## 2. 하드웨어 요구사항

### 2.1 최소 사양 (테스트/개발 환경)

```
CPU: Intel Xeon E5-2640 v4 (10코어) 또는 동급
RAM: 32GB DDR4
GPU: NVIDIA RTX 3060 (12GB VRAM) 또는 동급
Storage: 500GB SSD
Network: 1Gbps Ethernet
```

### 2.2 권장 사양 (프로덕션 환경)

```
CPU: Intel Xeon Gold 6248R (24코어) 또는 AMD EPYC 7402P
RAM: 64GB DDR4 ECC
GPU: NVIDIA RTX 3080 (16GB VRAM) 또는 A4000
Storage: 1TB NVMe SSD (시스템) + 2TB SSD (데이터)
Network: 10Gbps Ethernet
RAID: RAID 1 (데이터 백업)
UPS: 1500VA 이상 (정전 대비)
```

### 2.3 GPU 요구사항 상세

| API | GPU 필요 | VRAM 사용량 | 대안 (GPU 없을 시) |
|-----|---------|------------|-------------------|
| eDOCr2 | 필수 | 2-4GB | CPU 모드 (5배 느림) |
| YOLO | 필수 | 1-2GB | CPU 모드 (10배 느림) |
| EDGNet | 선택 | 0.5-1GB | CPU 모드 (2배 느림) |
| 기타 | 불필요 | - | - |

---

## 3. 소프트웨어 요구사항

### 3.1 운영체제

```
지원: Ubuntu 20.04/22.04 LTS
지원: CentOS 7.9+ / Rocky Linux 8+
지원: Red Hat Enterprise Linux 8+
미지원: Windows Server (Docker Desktop 제한 사항)
```

### 3.2 필수 소프트웨어

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

---

## 4. 네트워크 요구사항

### 4.1 포트 사용 (방화벽 설정 필요)

```bash
# 외부 접근 (사용자)
5173/tcp  - Web UI

# 내부 통신 (서비스 간)
8000/tcp  - Gateway API
5002/tcp  - eDOCr2 API
5005/tcp  - YOLO API
5012/tcp  - EDGNet API
5003/tcp  - Skin Model API
5004/tcp  - VL API
5006/tcp  - PaddleOCR API
9000/tcp  - Admin Dashboard API

# 모니터링 (관리자만)
9090/tcp  - Prometheus
3001/tcp  - Grafana

# SSH (관리자만)
22/tcp    - SSH 접속
```

### 4.2 인터넷 연결

```
완전 오프라인 (폐쇄망): 지원
   - VL API 비활성화 또는 로컬 LLM 사용
   - 모든 Docker 이미지 사전 준비
   - 시스템 패키지 오프라인 번들

제한적 인터넷: 지원 (권장)
   - VL API만 인터넷 필요 (선택사항)
   - Docker Hub 접근 불필요 (사전 로드)
```

---

## 5. 보안 고려사항

### 5.1 데이터 보안

#### 도면 파일 처리

```
- 외부 저장소 업로드: 절대 없음
- 로컬 처리: 모든 처리 온프레미스 내부
- 임시 파일: 처리 후 자동 삭제 (24시간)
- 백업: 고객사 정책에 따름
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

### 5.2 접근 제어

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

### 5.3 감사 로그

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

### 5.4 네트워크 보안

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

## 6. 외부 의존성 제거 방안

### 6.1 VL API 외부 의존성 분석

#### 현재 상태

```python
# vl-api/api_server.py
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 외부 API 호출
async def call_claude_vision(image, prompt):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",  # 외부 API
            headers={"x-api-key": ANTHROPIC_API_KEY},
            json=payload
        )
```

**문제점**:
- 도면 데이터가 외부 서버(Anthropic, OpenAI)로 전송됨
- 인터넷 연결 필수
- 폐쇄망 환경 사용 불가
- 비용 발생 (API 사용료)

### 6.2 해결 방안

#### 방안 1: VL API 비활성화 (권장)

VL API는 선택적 기능이므로 비활성화해도 핵심 기능 사용 가능

```yaml
# docker-compose.yml
services:
  vl-api:
    profiles:
      - optional  # 필요 시에만 활성화
```

```python
# gateway-api/api_server.py
VL_ENABLED = os.getenv("VL_ENABLED", "false").lower() == "true"

if VL_ENABLED:
    vl_result = await call_vl_api(...)
else:
    logger.info("VL API disabled - skipping")
```

**장점**: 완전 오프라인 운영 가능, 외부 데이터 유출 없음, 즉시 적용 가능

**단점**: 정보 블록 추출 기능 사용 불가, 고급 분석 기능 제한

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
```

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

### 6.3 권장 설정 (온프레미스)

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

## 7. 모니터링 시스템 구성

### 7.1 Prometheus 설정

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
  - job_name: 'gateway-api'
    static_configs:
      - targets: ['gateway-api:8000']
    metrics_path: '/metrics'

  - job_name: 'edocr2-v2-api'
    static_configs:
      - targets: ['edocr2-v2-api:5002']

  - job_name: 'yolo-api'
    static_configs:
      - targets: ['yolo-api:5005']

  - job_name: 'edgnet-api'
    static_configs:
      - targets: ['edgnet-api:5012']

  - job_name: 'skinmodel-api'
    static_configs:
      - targets: ['skinmodel-api:5003']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'nvidia-gpu'
    static_configs:
      - targets: ['nvidia-gpu-exporter:9835']

# 데이터 보관
storage:
  tsdb:
    retention.time: 90d  # 90일
    retention.size: 50GB
```

### 7.2 알림 규칙

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

      # 느린 응답 시간
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning

      # GPU 메모리 부족
      - alert: GPUMemoryHigh
        expr: nvidia_gpu_memory_used_bytes / nvidia_gpu_memory_total_bytes > 0.9
        for: 5m
        labels:
          severity: warning

      # 디스크 공간 부족
      - alert: DiskSpaceLow
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes < 0.1
        for: 5m
        labels:
          severity: critical
```

### 7.3 Grafana 대시보드

#### 대시보드 1: 운영 대시보드 (고객사 IT팀용)

패널:
- 시스템 상태 (서비스별 Up/Down)
- 처리된 도면 수 (일별)
- 평균 처리 시간 (게이지)
- 시스템 가용률 (SLA)

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

### 7.4 알림 연동

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

## 8. 오프라인 설치 준비

### 8.1 Docker 이미지 Export

```bash
#!/bin/bash
# scripts/export_images.sh

echo "Docker 이미지 Export 시작..."

# 이미지 목록
IMAGES=(
    "poc_web-ui:latest"
    "poc_gateway-api:latest"
    "edocr2-v2-api:latest"
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
done

echo "Export 완료!"
echo "총 크기:"
du -sh "$EXPORT_DIR"
```

**Export 결과 (약 9.5GB)**:
```
docker-images/
├── poc_web-ui_latest.tar          (200 MB)
├── poc_gateway-api_latest.tar     (1.2 GB)
├── edocr2-v2-api_latest.tar        (2.5 GB)
├── poc_yolo-api_latest.tar        (1.8 GB)
├── poc_edgnet-api_latest.tar      (1.1 GB)
├── poc_skinmodel-api_latest.tar   (800 MB)
├── poc_vl-api_latest.tar          (500 MB)
├── poc_paddleocr-api_latest.tar   (600 MB)
├── prom_prometheus_latest.tar     (300 MB)
├── grafana_grafana_latest.tar     (400 MB)
├── prom_node-exporter_latest.tar  (50 MB)
└── nvidia_gpu-exporter_latest.tar (100 MB)
```

### 8.2 시스템 패키지 번들

```bash
#!/bin/bash
# scripts/prepare_offline_packages.sh

BUNDLE_DIR="./offline-packages"
mkdir -p "$BUNDLE_DIR"

# Python 패키지
pip download -r requirements.txt -d "$BUNDLE_DIR/python-wheels"

# 시스템 패키지 (Ubuntu)
apt-get download $(cat packages.txt) -d "$BUNDLE_DIR/deb-packages"
```

### 8.3 모델 가중치 준비

```bash
# scripts/prepare_models.sh

MODEL_DIR="./model-weights"
mkdir -p "$MODEL_DIR"

# EDGNet Large
cp edgnet-api/models/edgnet_large.pth "$MODEL_DIR/"

# YOLO
cp yolo-api/models/yolo11n.pt "$MODEL_DIR/"

# Skin Model
cp -r skinmodel-api/models/skinmodel_xgboost "$MODEL_DIR/"
```

---

## 9. 납품 패키지 구성

### 9.1 최종 납품물 구조

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
│   ├── python-wheels/
│   ├── deb-packages/
│   └── rpm-packages/
│
├── model-weights/                      # 학습된 모델 (2GB)
│   ├── edgnet_large.pth
│   ├── yolo11n.pt
│   ├── skinmodel_xgboost/
│   └── llama-3.2-11b-vision/ (선택)
│
├── scripts/                            # 설치/관리 스크립트
│   ├── install.sh
│   ├── uninstall.sh
│   ├── backup.sh
│   ├── restore.sh
│   ├── check_system.sh
│   ├── update.sh
│   ├── health_check.sh
│   └── export_logs.sh
│
├── config/                             # 설정 파일
│   ├── docker-compose.yml
│   ├── docker-compose.monitoring.yml
│   ├── .env.template
│   ├── prometheus/
│   ├── grafana/
│   └── nginx/
│
├── docs/                               # 문서 (PDF)
│   ├── 00_빠른시작가이드.pdf
│   ├── 01_설치가이드.pdf
│   ├── 02_관리자매뉴얼.pdf
│   └── ...
│
├── training/                           # 교육 자료
│   ├── slides/
│   ├── hands-on/
│   └── videos/ (선택)
│
└── tools/                              # 유틸리티
    ├── test-dataset/
    ├── performance-test.sh
    └── migration-tool.py
```

### 9.2 체크섬 생성

```bash
# scripts/generate_checksums.sh

cd docker-images
sha256sum *.tar > checksums.txt

# 검증
sha256sum -c checksums.txt
```

---

## 10. 설치 절차

### 10.1 사전 점검

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
    echo "지원하지 않는 OS"
    exit 1
fi

# CPU 확인
echo -n "CPU 코어: "
CORES=$(nproc)
echo "$CORES cores"
if [ $CORES -lt 8 ]; then
    echo "경고: 최소 10코어 권장"
fi

# RAM 확인
echo -n "메모리: "
RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
echo "${RAM_GB}GB"
if [ $RAM_GB -lt 32 ]; then
    echo "오류: 최소 32GB 필요"
    exit 1
fi

# GPU 확인
echo -n "GPU 확인: "
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    echo "$GPU_NAME"
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    echo "  VRAM: ${GPU_MEM}MB"
else
    echo "GPU 없음 (CPU 모드 - 느림)"
fi

# Docker 확인
echo -n "Docker: "
if command -v docker &> /dev/null; then
    DOCKER_VER=$(docker --version | awk '{print $3}' | tr -d ',')
    echo "$DOCKER_VER"
else
    echo "Docker 미설치"
    exit 1
fi

# 디스크 공간
echo -n "디스크 공간: "
DISK_AVAIL=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
echo "${DISK_AVAIL}GB 사용 가능"
if [ $DISK_AVAIL -lt 100 ]; then
    echo "오류: 최소 100GB 필요"
    exit 1
fi

echo "==================================="
echo "모든 요구사항 충족!"
echo "==================================="
```

### 10.2 자동 설치 스크립트

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

if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp config/.env.template "$INSTALL_DIR/.env"
    echo ".env 파일을 수정하세요: $INSTALL_DIR/.env"
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

echo "===================================="
echo "설치 완료!"
echo "===================================="
echo ""
echo "접속 정보:"
echo "  Web UI: http://localhost:5173"
echo "  Admin 대시보드: http://localhost:5173/admin"
echo "  Grafana: http://localhost:3001 (admin/admin)"
echo "  API 문서: http://localhost:8000/docs"
```

### 10.3 헬스 체크

```bash
#!/bin/bash
# scripts/health_check.sh

SERVICES=(
    "http://localhost:8000/api/v1/health"
    "http://localhost:5002/api/v2/health"
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
        echo "$SERVICE: OK"
    else
        echo "$SERVICE: FAIL"
        ALL_HEALTHY=false
    fi
done

echo "==================================="
if [ "$ALL_HEALTHY" = true ]; then
    echo "모든 서비스 정상"
    exit 0
else
    echo "일부 서비스 오류"
    exit 1
fi
```

## 관련 문서

- [시스템 설치 가이드](/docs/deployment/installation) — 설치 절차 및 환경 설정
- [온프레미스 운영 가이드](/docs/deployment/on-premise-operation) — 교육, 백업, 업데이트
- [관리자 매뉴얼](/docs/deployment/admin-manual) — 서비스 관리 및 모니터링
- [GPU 설정](/docs/devops/gpu-config) — 서비스별 GPU 할당
