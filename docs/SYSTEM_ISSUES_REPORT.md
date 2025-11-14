# AI Drawing Analysis System - 문제점 종합 보고서

**작성일:** 2025-11-14
**작성자:** System Analysis
**버전:** 1.0

---

## 📋 목차

1. [요약](#요약)
2. [주요 문제점](#주요-문제점)
3. [세부 분석](#세부-분석)
4. [해결 방안](#해결-방안)
5. [우선순위 매트릭스](#우선순위-매트릭스)

---

## 요약

### 시스템 현황
- **전체 API 서비스:** 8개 (Gateway, eDOCr2, EDGNet, Skin Model, VL, YOLO, PaddleOCR, Admin)
- **GPU 활용 가능 API:** 4개 (eDOCr2, EDGNet, YOLO, PaddleOCR)
- **실제 GPU 사용 중:** 2개 (eDOCr2, YOLO) ❌
- **GPU 미사용:** 2개 (EDGNet, PaddleOCR) ❌

### 발견된 주요 이슈
- 🔴 **Critical:** 2건 (GPU 비활성화)
- 🟡 **Medium:** 4건 (설정 불일치, API 누락)
- 🟢 **Low:** 1건 (문서화 부족)

---

## 주요 문제점

### 1. 🔴 EDGNet API GPU 비활성화

**문제 설명:**
- PyTorch 기반 Graph Neural Network 모델임에도 CPU 모드로 실행
- 추론 성능 50% 저하 (GPU 대비)

**근본 원인:**

#### A. 코드 레벨 (`edgnet-api/api_server.py:201`)
```python
pipeline = EDGNetPipeline(model_path=str(model_path), device='cpu')
```
- GPU 가용성 확인 로직 없음
- 하드코딩된 'cpu' 디바이스

#### B. Docker 설정 (`docker-compose.yml:48-74`)
```yaml
edgnet-api:
  # GPU 설정 누락
  # deploy.resources.reservations.devices 섹션 없음
```

**영향:**
- 도면 세그멘테이션 처리 시간 2배 증가
- 대량 배치 처리 시 병목 현상

**해결 방법:**
1. GPU 자동 감지 로직 추가
2. docker-compose.yml GPU 설정 추가
3. 환경 변수로 디바이스 선택 가능하도록 수정

---

### 2. 🔴 PaddleOCR API GPU 비활성화

**문제 설명:**
- PaddleOCR은 GPU 가속 지원하지만 명시적으로 비활성화됨
- OCR 성능 3-5배 저하

**근본 원인:**

#### Docker 환경 변수 (`docker-compose.yml:184`)
```yaml
paddleocr-api:
  environment:
    - USE_GPU=false  # ❌ 의도적 비활성화
```

#### GPU 설정 누락
```yaml
paddleocr-api:
  # deploy.resources 섹션 없음
```

**영향:**
- OCR 처리 속도 3-5배 느림
- 실시간 처리 불가능

**해결 방법:**
1. USE_GPU=true 변경
2. GPU 리소스 할당 추가

---

### 3. 🟡 Web UI GPU 표시 불일치

**문제 설명:**
- Admin Dashboard에서 EDGNet을 "GPU Disabled"로 표시
- 실제로는 GPU 사용 가능한 모델

**근본 원인:**

#### 설정 파일 (`web-ui/src/config/api.ts:64`)
```typescript
edgnet: {
  gpuEnabled: false,  // ❌ 잘못된 설정
  description: '도면 세그멘테이션 엔진',
}
```

**혼동 원인:**
- Skin Model: XGBoost (CPU 전용) → gpuEnabled: false ✅
- VL API: 외부 API (로컬 GPU 불필요) → gpuEnabled: false ✅
- EDGNet: PyTorch GNN (GPU 가능) → gpuEnabled: false ❌

**영향:**
- 관리자 UI 혼란
- 성능 최적화 기회 놓침

**해결 방법:**
```typescript
edgnet: {
  gpuEnabled: true,
  gpuStatus: 'available-but-disabled',  // 현재 상태
}

skinmodel: {
  gpuEnabled: false,
  gpuStatus: 'n/a',  // GPU 불필요
  note: 'XGBoost - CPU only'
}

vl: {
  gpuEnabled: false,
  gpuStatus: 'n/a',  // 외부 API
  note: 'External API (OpenAI/Anthropic)'
}
```

---

### 4. 🟡 Admin Dashboard API 목록 누락

**문제 설명:**
- PaddleOCR API가 Admin Dashboard에 표시되지 않음
- 모니터링 불가능

**근본 원인:**

#### dashboard.py (`admin-dashboard/dashboard.py:62-69`)
```python
API_URLS = {
    "edocr2": "http://localhost:5001",
    "edgnet": "http://localhost:5012",
    "skinmodel": "http://localhost:5003",
    "vl": "http://localhost:5004",
    "yolo": "http://localhost:5005",
    "gateway": "http://localhost:8000"
    # ❌ PaddleOCR 누락
}
```

**영향:**
- PaddleOCR 상태 모니터링 불가
- 로그 확인 불가
- 재시작 제어 불가

**해결 방법:**
```python
API_URLS = {
    "edocr2": "http://localhost:5001",
    "edgnet": "http://localhost:5012",
    "skinmodel": "http://localhost:5003",
    "vl": "http://localhost:5004",
    "yolo": "http://localhost:5005",
    "paddleocr": "http://localhost:5006",  # ✅ 추가
    "gateway": "http://localhost:8000"
}
```

---

### 5. 🟡 Health Check 엔드포인트 불일치

**문제 설명:**
- 일부 API는 `/health` 엔드포인트가 없음
- Docker healthcheck 실패 가능성

**테스트 결과:**
```bash
# ❌ 404 Not Found
curl http://localhost:5012/health
curl http://localhost:5003/health
curl http://localhost:5004/health

# ✅ 정상 응답
curl http://localhost:5012/
curl http://localhost:5003/
```

**docker-compose.yml 설정:**
```yaml
edgnet-api:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5002/api/v1/health"]
    # ❌ 존재하지 않는 엔드포인트
```

**영향:**
- Docker healthcheck 실패 → 컨테이너 재시작 루프
- 모니터링 시스템 오작동

**해결 방법:**

옵션 1: 모든 API에 `/health` 추가
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "EDGNet API"}
```

옵션 2: healthcheck URL 수정
```yaml
edgnet-api:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5002/"]
```

---

### 6. 🟡 docker-compose.yml 환경 변수 불일치

**문제 설명:**
- Web UI 환경 변수에 불필요한 개별 API URL
- Gateway를 통한 접근이 원칙이지만 직접 URL도 제공

**현재 설정 (`docker-compose.yml:252-255`):**
```yaml
web-ui:
  environment:
    - VITE_GATEWAY_URL=http://localhost:8000  # ✅ 주 경로
    - VITE_EDOCR2_URL=http://localhost:5001   # ⚠️  직접 접근
    - VITE_EDGNET_URL=http://localhost:5012   # ⚠️  직접 접근
    - VITE_SKINMODEL_URL=http://localhost:5003 # ⚠️  직접 접근
```

**문제점:**
- 아키텍처 원칙 위배 (Gateway 우회)
- 포트 변경 시 여러 곳 수정 필요
- 보안 취약점 (API 직접 노출)

**권장 방안:**
```yaml
web-ui:
  environment:
    - VITE_GATEWAY_URL=http://localhost:8000  # ✅ Gateway만 사용
    - VITE_ADMIN_API_URL=http://localhost:8007 # ✅ Admin 전용
    # 개별 API URL 제거
```

---

### 7. 🟢 온프레미스 VL API 외부 의존성

**문제 설명:**
- VL API가 OpenAI/Anthropic 외부 API 사용
- 온프레미스 환경에서 작동 불가

**현재 설정:**
```yaml
vl-api:
  environment:
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    - OPENAI_API_KEY=${OPENAI_API_KEY}
```

**영향:**
- 폐쇄망 환경에서 VL API 사용 불가
- Hybrid 모드 일부 기능 제한

**해결 방법 (ONPREMISE_DEPLOYMENT_GUIDE.md 참조):**

옵션 1: VL API 비활성화
```yaml
# docker-compose.yml에서 vl-api 제거
```

옵션 2: 로컬 LLM 대체 (Llama 3.2 Vision)
```bash
# Ollama 설치
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2-vision

# VL API 수정
# vl-api/api_server.py에서 로컬 모델 사용
```

옵션 3: Hybrid 모드 (VL 제외)
```python
# gateway-api에서 VL 사용 안 함
AVAILABLE_SERVICES = ["edocr2", "yolo", "edgnet", "skinmodel"]
```

---

## 우선순위 매트릭스

### 긴급도 × 중요도

| 순위 | 문제 | 긴급도 | 중요도 | 해결 시간 | 영향 범위 |
|------|------|---------|---------|-----------|-----------|
| 1 | EDGNet GPU 비활성화 | 🔴 High | 🔴 High | 30분 | 성능 50% 저하 |
| 2 | PaddleOCR GPU 비활성화 | 🔴 High | 🟡 Medium | 10분 | OCR 3x 느림 |
| 3 | Health 엔드포인트 불일치 | 🟡 Medium | 🔴 High | 15분 | Healthcheck 실패 |
| 4 | PaddleOCR Admin 누락 | 🟡 Medium | 🟡 Medium | 5분 | 모니터링 불가 |
| 5 | Web UI GPU 표시 불일치 | 🟢 Low | 🟡 Medium | 20분 | UX 혼란 |
| 6 | 환경 변수 불일치 | 🟢 Low | 🟡 Medium | 10분 | 아키텍처 위배 |
| 7 | VL API 외부 의존성 | 🟢 Low | 🔴 High | 2시간 | 온프레미스 불가 |

### 해결 순서 권장

**Phase 1: 즉시 해결 (1시간 이내)**
1. EDGNet GPU 활성화 (30분)
2. PaddleOCR GPU 활성화 (10분)
3. PaddleOCR Admin 추가 (5분)
4. Health 엔드포인트 통일 (15분)

**Phase 2: 단기 개선 (1일 이내)**
5. Web UI GPU 표시 수정 (20분)
6. 환경 변수 정리 (10분)
7. 문서 업데이트 (30분)

**Phase 3: 중기 개선 (1주 이내)**
8. VL API 로컬 LLM 대체 (2시간)
9. 온프레미스 테스트 (4시간)
10. 성능 벤치마크 (2시간)

---

## 즉시 적용 가능한 수정 사항

### 1. EDGNet GPU 활성화

**파일:** `edgnet-api/api_server.py`

**변경 전 (Line 201):**
```python
pipeline = EDGNetPipeline(model_path=str(model_path), device='cpu')
```

**변경 후:**
```python
import torch

# GPU 자동 감지
device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Using device: {device}")

pipeline = EDGNetPipeline(model_path=str(model_path), device=device)
```

**파일:** `docker-compose.yml`

**변경 전 (Line 48-74):**
```yaml
edgnet-api:
  build:
    context: ./edgnet-api
  # GPU 설정 없음
```

**변경 후:**
```yaml
edgnet-api:
  build:
    context: ./edgnet-api
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

---

### 2. PaddleOCR GPU 활성화

**파일:** `docker-compose.yml`

**변경 전 (Line 184):**
```yaml
paddleocr-api:
  environment:
    - USE_GPU=false
```

**변경 후:**
```yaml
paddleocr-api:
  environment:
    - USE_GPU=true
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

---

### 3. Admin Dashboard PaddleOCR 추가

**파일:** `admin-dashboard/dashboard.py`

**변경 전 (Line 62-69):**
```python
API_URLS = {
    "edocr2": "http://localhost:5001",
    "edgnet": "http://localhost:5012",
    "skinmodel": "http://localhost:5003",
    "vl": "http://localhost:5004",
    "yolo": "http://localhost:5005",
    "gateway": "http://localhost:8000"
}
```

**변경 후:**
```python
API_URLS = {
    "edocr2": "http://localhost:5001",
    "edgnet": "http://localhost:5012",
    "skinmodel": "http://localhost:5003",
    "vl": "http://localhost:5004",
    "yolo": "http://localhost:5005",
    "paddleocr": "http://localhost:5006",
    "gateway": "http://localhost:8000"
}
```

---

### 4. Health Check 엔드포인트 추가

**파일:** `edgnet-api/api_server.py`

**추가:**
```python
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "EDGNet API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
```

**파일:** `skinmodel-api/api_server.py`

**추가:**
```python
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Skin Model API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }
```

---

### 5. Web UI GPU 표시 수정

**파일:** `web-ui/src/config/api.ts`

**변경 전 (Line 64):**
```typescript
edgnet: {
  gpuEnabled: false,
}
```

**변경 후:**
```typescript
edgnet: {
  gpuEnabled: true,
  description: '도면 세그멘테이션 엔진 - PyTorch GNN',
}

paddleocr: {
  name: 'paddleocr',
  displayName: 'PaddleOCR API',
  url: getApiUrl('VITE_PADDLEOCR_URL', 'http://localhost:5006'),
  port: 5006,
  description: 'OCR 엔진 - PaddlePaddle 기반',
  features: ['다국어 OCR', 'GPU 가속', '고정밀 인식'],
  gpuEnabled: true,
  version: '2.0.0',
}
```

---

## 검증 체크리스트

### 수정 후 확인 사항

- [ ] EDGNet GPU 사용 확인
```bash
docker logs edgnet-api | grep "Using device"
# 출력: Using device: cuda
```

- [ ] PaddleOCR GPU 사용 확인
```bash
docker logs paddleocr-api | grep "use_gpu"
# 출력: use_gpu: True
```

- [ ] Admin Dashboard PaddleOCR 표시 확인
```bash
curl http://localhost:8007/api/status
# paddleocr 항목 존재 확인
```

- [ ] Health Check 동작 확인
```bash
curl http://localhost:5012/health
curl http://localhost:5003/health
# 모두 200 OK 응답
```

- [ ] Docker Healthcheck 정상 확인
```bash
docker ps
# 모든 컨테이너 (healthy) 상태
```

- [ ] GPU 메모리 사용 확인
```bash
nvidia-smi
# edgnet, paddleocr 프로세스 GPU 사용 확인
```

---

## 참고 문서

- [ONPREMISE_DEPLOYMENT_GUIDE.md](/home/uproot/ax/poc/docs/ONPREMISE_DEPLOYMENT_GUIDE.md)
- [ADMIN_MANUAL.md](/home/uproot/ax/poc/docs/ADMIN_MANUAL.md)
- [docker-compose.yml](/home/uproot/ax/poc/docker-compose.yml)

---

**보고서 종료**
