# 장기 개선 과제

> 작성일: 2025-11-13
> 기간: 1-3개월
> 우선순위: 🟢 Priority 3

---

## 📋 개요

시스템의 장기적인 안정성, 확장성, 유지보수성을 위한 개선 과제들을 정리합니다.
각 과제는 1-2주 이상의 시간이 소요되며, 시스템의 근본적인 개선을 목표로 합니다.

---

## 1. 모델 레지스트리 및 버전 관리 🎯

### 1.1 문제 정의

**현재 상황**:
```
/models/
├── yolo11n.pt              # 버전 불명, 체크섬 없음
├── graphsage_dimension_classifier.pth  # 버전 불명
└── (기타 모델들...)
```

**문제점**:
- ❌ 모델 버전 추적 불가능
- ❌ 모델 변경 이력 없음
- ❌ 체크섬 검증 없음
- ❌ 자동 다운로드/배포 불가능
- ❌ A/B 테스트 어려움

### 1.2 해결 방안: MLflow Model Registry

#### 아키텍처

```
┌─────────────────────────────────────────────────┐
│                 MLflow Server                    │
│  ┌──────────────┐  ┌──────────────────────────┐ │
│  │   Tracking   │  │     Model Registry       │ │
│  │   Server     │  │  - Versioning            │ │
│  │   (Metrics,  │  │  - Staging/Production    │ │
│  │    Logs)     │  │  - Metadata              │ │
│  └──────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────┘
          │                      │
          │                      │
          ▼                      ▼
┌──────────────────┐    ┌──────────────────────┐
│  Training Script │    │   Inference API      │
│  - Log metrics   │    │   - Load model v2    │
│  - Register v2   │    │   - Fallback to v1   │
└──────────────────┘    └──────────────────────┘
```

#### 구현 예시

```python
import mlflow
import mlflow.pytorch

# 1. MLflow 초기화
mlflow.set_tracking_uri("http://mlflow-server:5000")
mlflow.set_experiment("yolo-training")

# 2. 학습 중 메트릭 로깅
with mlflow.start_run(run_name="yolo11n-v1.2"):
    # 하이퍼파라미터 기록
    mlflow.log_params({
        "model": "yolo11n",
        "epochs": 100,
        "batch_size": 16,
        "lr": 0.001,
        "dataset": "engineering_drawings_v1.0"
    })

    # 학습
    for epoch in range(100):
        train_loss = train_one_epoch(model, ...)
        val_loss = validate(model, ...)

        # 메트릭 로깅
        mlflow.log_metrics({
            "train_loss": train_loss,
            "val_loss": val_loss,
            "mAP50": compute_map(model, ...),
            "mAP50_95": compute_map_range(model, ...)
        }, step=epoch)

    # 모델 저장
    mlflow.pytorch.log_model(
        model,
        artifact_path="model",
        registered_model_name="yolo-dimension-detector"
    )

# 3. 프로덕션으로 승격
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="yolo-dimension-detector",
    version=2,
    stage="Production"
)

# 4. 추론 시 로드
model_uri = "models:/yolo-dimension-detector/Production"
model = mlflow.pytorch.load_model(model_uri)
```

#### 배포

```yaml
# docker-compose.yml에 MLflow 추가
services:
  mlflow:
    image: ghcr.io/mlflow/mlflow:latest
    container_name: mlflow-server
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://user:pass@postgres:5432/mlflow
      - MLFLOW_ARTIFACT_ROOT=s3://mlflow-artifacts/  # 또는 /mlflow/artifacts
    volumes:
      - mlflow-artifacts:/mlflow/artifacts
    command: >
      mlflow server
      --backend-store-uri postgresql://user:pass@postgres:5432/mlflow
      --default-artifact-root /mlflow/artifacts
      --host 0.0.0.0
      --port 5000

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=mlflow
      - POSTGRES_PASSWORD=mlflow
      - POSTGRES_DB=mlflow
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  mlflow-artifacts:
  postgres-data:
```

### 1.3 장점

- ✅ 모델 버전 자동 추적
- ✅ 하이퍼파라미터 기록
- ✅ 메트릭 시각화
- ✅ 모델 비교 (v1 vs v2)
- ✅ A/B 테스트 지원
- ✅ Staging/Production 환경 분리
- ✅ 체크섬 자동 검증

**예상 소요**: 3-4일

---

## 2. 분산 추론 (Load Balancing) ⚡

### 2.1 문제 정의

**현재 상황**:
- 각 API가 단일 인스턴스로 실행
- 동시 요청 처리 제한 (1-2개)
- GPU 리소스 미활용 (단일 프로세스)

**문제점**:
- ❌ 동시 처리량 낮음 (1-2 RPS)
- ❌ GPU 활용률 낮음 (<50%)
- ❌ 응답 시간 불안정

### 2.2 해결 방안: Kubernetes + HPA

#### 아키텍처

```
┌──────────────────────────────────────────────────┐
│              Kubernetes Cluster                   │
│                                                    │
│  ┌─────────────────────────────────────────────┐ │
│  │         Ingress (nginx)                     │ │
│  │         gateway.example.com                 │ │
│  └──────────────┬──────────────────────────────┘ │
│                 │                                  │
│                 ▼                                  │
│  ┌──────────────────────────────────────────┐    │
│  │       Gateway API Service                │    │
│  │       Replicas: 3                        │    │
│  └──────────────┬───────────────────────────┘    │
│                 │                                  │
│       ┌─────────┼─────────┬─────────┐            │
│       ▼         ▼         ▼         ▼            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │ YOLO-1  │ │ YOLO-2  │ │ YOLO-3  │            │
│  │ GPU: 0  │ │ GPU: 1  │ │ GPU: 0  │            │
│  └─────────┘ └─────────┘ └─────────┘            │
│                                                    │
│  ┌─────────────────────────────────────────┐    │
│  │  Horizontal Pod Autoscaler (HPA)       │    │
│  │  - CPU > 70% → Scale up                │    │
│  │  - CPU < 30% → Scale down              │    │
│  │  - Min: 2, Max: 10                     │    │
│  └─────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

#### 구현 예시

```yaml
# kubernetes/yolo-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yolo-api
spec:
  replicas: 3  # 초기 레플리카 수
  selector:
    matchLabels:
      app: yolo-api
  template:
    metadata:
      labels:
        app: yolo-api
    spec:
      containers:
      - name: yolo-api
        image: yolo-api:latest
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: "1"  # GPU 요청
          limits:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: "1"
        ports:
        - containerPort: 5005

---
# kubernetes/yolo-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: yolo-api
spec:
  selector:
    app: yolo-api
  ports:
  - protocol: TCP
    port: 5005
    targetPort: 5005
  type: ClusterIP

---
# kubernetes/yolo-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: yolo-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: yolo-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2.3 대안: Ray Serve (추천 - 간단)

```python
# ray_serve_yolo.py
import ray
from ray import serve
from ultralytics import YOLO

ray.init()
serve.start()

@serve.deployment(
    num_replicas=3,  # 3개 레플리카
    ray_actor_options={"num_gpus": 0.33}  # GPU 공유
)
class YOLODetector:
    def __init__(self):
        self.model = YOLO("yolo11n.pt")

    async def __call__(self, request):
        image = await request.body()
        results = self.model(image)
        return results.json()

YOLODetector.deploy()

# 사용
import requests
response = requests.post("http://localhost:8000/YOLODetector", data=image_bytes)
```

**장점**:
- ✅ Kubernetes보다 간단
- ✅ GPU 공유 지원
- ✅ 동적 스케일링
- ✅ Python 네이티브

**예상 소요**: 2-3일 (Ray Serve) / 1주일 (Kubernetes)

---

## 3. 비동기 처리 (Task Queue) 📬

### 3.1 문제 정의

**현재 상황**:
- 동기식 API (요청 → 대기 → 응답)
- 긴 처리 시간 (5-30초)
- 타임아웃 위험

### 3.2 해결 방안: Celery + Redis

#### 아키텍처

```
┌──────────┐    POST /process    ┌──────────────┐
│  Client  │ ──────────────────> │  Gateway API │
└──────────┘                      └──────┬───────┘
     │                                   │
     │  202 Accepted                     │ enqueue task
     │  {"job_id": "abc-123"}            │
     │ <─────────────────────            │
     │                                   ▼
     │                            ┌─────────────┐
     │                            │    Redis    │
     │                            │ (Task Queue)│
     │                            └──────┬──────┘
     │                                   │
     │  GET /status/abc-123              │ dequeue
     │ ──────────────────────>           │
     │                                   ▼
     │  200 OK                    ┌─────────────┐
     │  {"status": "processing"}  │   Celery    │
     │ <─────────────────────     │   Workers   │
     │                            │  (3 nodes)  │
     │                            └─────────────┘
     │                                   │
     │  GET /status/abc-123              │ task complete
     │ ──────────────────────>           │
     │                                   ▼
     │  200 OK                    ┌─────────────┐
     │  {"status": "completed",   │   Redis     │
     │   "result": {...}}         │ (Results DB)│
     │ <─────────────────────     └─────────────┘
```

#### 구현 예시

```python
# celery_app.py
from celery import Celery

app = Celery(
    'gateway',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

@app.task(bind=True)
def process_drawing_async(self, image_path, params):
    """
    비동기 도면 처리
    """
    # 진행 상황 업데이트
    self.update_state(state='PROGRESS', meta={'stage': 'yolo', 'progress': 0})

    # YOLO 검출
    yolo_result = call_yolo(image_path, params["yolo"])
    self.update_state(state='PROGRESS', meta={'stage': 'yolo', 'progress': 30})

    # OCR 추출
    ocr_result = call_edocr2(image_path, params["ocr"])
    self.update_state(state='PROGRESS', meta={'stage': 'ocr', 'progress': 60})

    # 세그멘테이션
    seg_result = call_edgnet(image_path, params["seg"])
    self.update_state(state='PROGRESS', meta={'stage': 'segmentation', 'progress': 90})

    # 결과 통합
    final_result = merge_results(yolo_result, ocr_result, seg_result)
    self.update_state(state='SUCCESS', meta={'result': final_result})

    return final_result

# api_server.py
from fastapi import FastAPI, BackgroundTasks
from celery.result import AsyncResult

app = FastAPI()

@app.post("/api/v1/process")
async def process_drawing(file: UploadFile):
    """
    도면 처리 (비동기)
    """
    # 파일 저장
    image_path = save_uploaded_file(file)

    # Celery 태스크 시작
    task = process_drawing_async.delay(image_path, params)

    return {
        "status": "accepted",
        "job_id": task.id,
        "status_url": f"/api/v1/status/{task.id}"
    }

@app.get("/api/v1/status/{job_id}")
async def get_status(job_id: str):
    """
    작업 상태 조회
    """
    task_result = AsyncResult(job_id, app=celery_app)

    if task_result.state == 'PENDING':
        return {"status": "pending", "progress": 0}
    elif task_result.state == 'PROGRESS':
        return {
            "status": "processing",
            "stage": task_result.info.get('stage'),
            "progress": task_result.info.get('progress')
        }
    elif task_result.state == 'SUCCESS':
        return {
            "status": "completed",
            "result": task_result.result
        }
    elif task_result.state == 'FAILURE':
        return {
            "status": "failed",
            "error": str(task_result.info)
        }
```

**예상 소요**: 3-4일

---

## 4. 모니터링 및 관찰성 (Observability) 📊

### 4.1 Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana-dashboards:/etc/grafana/provisioning/dashboards

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"

  nvidia-gpu-exporter:
    image: utkuozdemir/nvidia_gpu_exporter:latest
    runtime: nvidia
    ports:
      - "9835:9835"
```

#### 커스텀 메트릭 추가

```python
# api_server.py
from prometheus_client import Counter, Histogram, Gauge
import time

# 메트릭 정의
request_count = Counter('yolo_requests_total', 'Total YOLO requests')
request_duration = Histogram('yolo_request_duration_seconds', 'YOLO request duration')
model_confidence = Histogram('yolo_confidence', 'YOLO detection confidence')
active_requests = Gauge('yolo_active_requests', 'Active YOLO requests')

@app.post("/api/v1/detect")
async def detect(file: UploadFile):
    request_count.inc()
    active_requests.inc()

    start_time = time.time()
    try:
        result = model(file)

        # 신뢰도 메트릭 기록
        for detection in result.detections:
            model_confidence.observe(detection.confidence)

        duration = time.time() - start_time
        request_duration.observe(duration)

        return result
    finally:
        active_requests.dec()
```

**예상 소요**: 2-3일

---

## 5. 통합 테스트 및 CI/CD 🔄

### 5.1 GitHub Actions Workflow

```yaml
# .github/workflows/test-and-deploy.yml
name: Test and Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: pytest tests/unit --cov=src --cov-report=xml

      - name: Run integration tests
        run: |
          docker-compose -f docker-compose.test.yml up -d
          pytest tests/integration
          docker-compose -f docker-compose.test.yml down

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker-compose build

      - name: Push to registry
        run: |
          docker tag gateway-api:latest ${{ secrets.REGISTRY }}/gateway-api:${{ github.sha }}
          docker push ${{ secrets.REGISTRY }}/gateway-api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/ax-poc
            docker-compose pull
            docker-compose up -d
```

**예상 소요**: 3-4일

---

## 6. 데이터 파이프라인 (Data Versioning) 💾

### 6.1 DVC (Data Version Control)

```bash
# 데이터 버전 관리 초기화
dvc init

# 데이터셋 추가
dvc add data/training_images.zip
dvc add data/annotations.json

# Git에 메타데이터만 커밋
git add data/training_images.zip.dvc data/annotations.json.dvc .gitignore
git commit -m "Add dataset v1.0"

# 원격 저장소 설정 (S3, GCS, Azure Blob)
dvc remote add -d storage s3://ax-poc-datasets
dvc push

# 다른 머신에서 데이터 다운로드
dvc pull
```

#### 데이터 파이프라인

```yaml
# dvc.yaml
stages:
  prepare:
    cmd: python scripts/prepare_data.py
    deps:
      - data/raw/
    outs:
      - data/prepared/

  train:
    cmd: python scripts/train_yolo.py
    deps:
      - data/prepared/
      - scripts/train_yolo.py
    params:
      - train.epochs
      - train.batch_size
    outs:
      - models/yolo11n.pt
    metrics:
      - metrics.json:
          cache: false
```

**예상 소요**: 2-3일

---

## 7. 보안 강화 🔒

### 7.1 API 인증 (JWT)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    JWT 토큰 검증
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/v1/process")
async def process_drawing(
    file: UploadFile,
    user: dict = Depends(verify_token)  # 인증 필요
):
    print(f"Processing for user: {user['sub']}")
    ...
```

### 7.2 Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/process")
@limiter.limit("10/minute")  # 분당 10회 제한
async def process_drawing(request: Request, file: UploadFile):
    ...
```

**예상 소요**: 2-3일

---

## 📊 전체 로드맵

### Phase 1: 인프라 개선 (2-3주)

| 주차 | 작업 | 예상 소요 |
|------|------|----------|
| **Week 1** | 모델 레지스트리 (MLflow) | 3-4일 |
|            | 비동기 처리 (Celery) | 3-4일 |
| **Week 2** | 모니터링 (Prometheus + Grafana) | 2-3일 |
|            | CI/CD 파이프라인 | 3-4일 |
| **Week 3** | 통합 테스트 작성 | 2-3일 |
|            | 문서 업데이트 | 1-2일 |

### Phase 2: 성능 최적화 (2-3주)

| 주차 | 작업 | 예상 소요 |
|------|------|----------|
| **Week 4** | 분산 추론 (Ray Serve) | 2-3일 |
|            | 캐싱 레이어 추가 | 2-3일 |
| **Week 5** | GPU 최적화 (TensorRT) | 3-4일 |
|            | 배치 처리 구현 | 2-3일 |
| **Week 6** | 성능 테스트 및 튜닝 | 3-5일 |

### Phase 3: 보안 및 거버넌스 (1-2주)

| 주차 | 작업 | 예상 소요 |
|------|------|----------|
| **Week 7** | API 인증 (JWT) | 2-3일 |
|            | Rate Limiting | 1-2일 |
|            | 데이터 암호화 | 2-3일 |
| **Week 8** | 감사 로그 (Audit Log) | 2-3일 |
|            | 보안 스캔 및 취약점 수정 | 2-3일 |

**총 예상 소요**: 8-11주 (2-3개월)

---

## 📝 체크리스트

### 인프라

- [ ] MLflow 모델 레지스트리 구축
- [ ] Celery 비동기 처리 구현
- [ ] Prometheus + Grafana 모니터링
- [ ] GitHub Actions CI/CD
- [ ] DVC 데이터 버전 관리

### 성능

- [ ] Ray Serve 또는 Kubernetes 배포
- [ ] Redis 캐싱 레이어
- [ ] GPU 최적화 (TensorRT)
- [ ] 배치 처리 구현
- [ ] 로드 테스트 (Locust)

### 보안

- [ ] JWT 인증
- [ ] Rate Limiting
- [ ] HTTPS/TLS
- [ ] 데이터 암호화
- [ ] 감사 로그

### 문서

- [ ] API 사용 가이드
- [ ] 운영 매뉴얼 (Runbook)
- [ ] 장애 대응 가이드
- [ ] 아키텍처 다이어그램
- [ ] 성능 벤치마크

---

## 🎯 성공 기준

### 인프라

- ✅ 모델 배포 시간: 10분 → **2분 이하**
- ✅ 시스템 가동률 (Uptime): 95% → **99.9%**
- ✅ 장애 감지 시간: ? → **1분 이내**

### 성능

- ✅ 처리량 (Throughput): 1-2 RPS → **10+ RPS**
- ✅ 응답 시간 (P95): 30초 → **5초 이하**
- ✅ GPU 활용률: 50% → **80%+**

### 보안

- ✅ 인증 적용: ❌ → **100% 적용**
- ✅ 취약점: ? → **0건 (Critical/High)**
- ✅ 감사 로그: ❌ → **100% 기록**

---

**관련 문서**:
- `01_CURRENT_STATUS_OVERVIEW.md`: 현재 시스템 현황
- `02_EDOCR2_INTEGRATION_PLAN.md`: 우선순위 1 과제
- `03_MINOR_FIXES.md`: 빠른 개선 사항
