# DevOps 가이드

> CI/CD, 배포, 환경 설정, 모니터링 가이드
> 트리거: "CI", "CD", "배포", "파이프라인", "Docker", "환경변수"

---

## 1. CI/CD 파이프라인

### 워크플로우 파일

| 파일 | 용도 | 트리거 |
|------|------|--------|
| `.github/workflows/ci.yml` | 테스트/빌드 검증 | Push, PR (main, develop) |
| `.github/workflows/cd.yml` | 이미지 빌드/배포 | CI 성공 후 또는 수동 |

### CI 파이프라인 구조

```
Push/PR
    │
    ├─► Frontend (병렬)
    │   ├── npm ci
    │   ├── ESLint (0 errors 필수)
    │   ├── npm run build
    │   └── npm run test:run (141개)
    │
    ├─► Backend (병렬)
    │   ├── pip install
    │   ├── ruff check
    │   └── pytest (364개)
    │
    ├─► API Validation (병렬)
    │   ├── YAML 스펙 검증
    │   └── Dockerfile 검사
    │
    └─► Sync Check
        └── TypeScript 타입 검사

    ▼
CI Summary (결과 집계)
```

### CD 파이프라인 구조

```
CI 성공 또는 수동 트리거
    │
    ▼
Pre-check (CI 상태 확인)
    │
    ▼
Build Images (6개 서비스)
    ├── gateway-api
    ├── yolo-api
    ├── edocr2-v2-api
    ├── paddleocr-api
    ├── design-checker-api
    └── pid-analyzer-api
    │
    ▼
Deploy Staging (자동)
    │
    ▼
Deploy Production (수동 승인)
    │
    ▼
Rollback (실패 시 자동)
```

### 수동 배포 방법

```bash
# GitHub Actions UI에서:
1. Actions 탭 → CD Pipeline
2. "Run workflow" 클릭
3. 환경 선택: staging / production
4. 서비스 선택: all 또는 특정 서비스
```

### 로컬에서 CI 검증

```bash
# Frontend
cd web-ui
npm run lint          # ESLint
npm run build         # TypeScript 빌드
npm run test:run      # 141개 테스트

# Backend
cd gateway-api
ruff check . --ignore E501
pytest tests/ -v      # 364개 테스트
```

---

## 2. Docker 관리

### 서비스별 포트

| 카테고리 | 서비스 | 포트 |
|----------|--------|------|
| Orchestrator | Gateway | 8000 |
| Detection | YOLO | 5005 |
| OCR | eDOCr2 | 5002 |
| OCR | PaddleOCR | 5006 |
| OCR | Tesseract | 5008 |
| OCR | TrOCR | 5009 |
| OCR | OCR Ensemble | 5011 |
| OCR | Surya OCR | 5013 |
| OCR | DocTR | 5014 |
| OCR | EasyOCR | 5015 |
| Segmentation | EDGNet | 5012 |
| Segmentation | Line Detector | 5016 |
| Preprocessing | ESRGAN | 5010 |
| Analysis | SkinModel | 5003 |
| Analysis | PID Analyzer | 5018 |
| Analysis | Design Checker | 5019 |
| Analysis | Blueprint BOM | 5020 |
| Visualization | PID Composer | 5021 |
| AI | VL | 5004 |
| Knowledge | Knowledge | 5007 |

### Docker 명령어

```bash
# 전체 서비스 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d gateway-api yolo-api

# 로그 확인
docker logs gateway-api -f
docker logs yolo-api -f --tail 100

# 서비스 재시작
docker-compose restart gateway-api

# 이미지 재빌드
docker-compose build --no-cache gateway-api
docker-compose up -d gateway-api

# 전체 정리
docker-compose down
docker system prune -f
```

### GPU 설정

```yaml
# docker-compose.override.yml 예시
services:
  yolo-api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## 3. 환경변수

### 필수 설정 (.env)

```bash
# API 키 (VL API 사용 시)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# GPU
USE_GPU=true
CUDA_DEVICE=0
```

### 환경변수 템플릿

```bash
# 복사 후 수정
cp .env.example .env
nano .env
```

### 주요 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 | - |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | - |
| `USE_GPU` | GPU 사용 여부 | `true` |
| `VL_PROVIDER` | VL 프로바이더 | `openai` |
| `VL_MODEL` | VL 모델 | `gpt-4o-mini` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |
| `WORKERS` | uvicorn 워커 수 | `1` |

### 서비스별 URL (Docker 내부)

```bash
YOLO_API_URL=http://yolo-api:5005
EDOCR2_URL=http://edocr2-v2-api:5002
DESIGN_CHECKER_URL=http://design-checker-api:5019
# ... 전체 목록은 .env.example 참조
```

---

## 4. 헬스체크

### 표준 헬스체크 응답

```json
{
  "status": "healthy",
  "service": "yolo-api",
  "version": "1.0.0",
  "timestamp": "2026-01-16T18:30:00",
  "gpu_available": true,
  "model_loaded": true,
  "details": {
    "gpu_name": "NVIDIA RTX 3090"
  }
}
```

### 헬스체크 엔드포인트

```bash
# 개별 서비스
curl http://localhost:5005/health          # YOLO
curl http://localhost:5002/api/v1/health   # eDOCr2
curl http://localhost:8000/health          # Gateway

# 전체 서비스 확인
for port in 5002 5003 5004 5005 5006 5007 5008 5009 5010 5011 5012 5013 5014 5015 5016 5018 5019 5021; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/health | jq -r '.status' 2>/dev/null || echo "unreachable"
done
```

### 공유 스키마 사용

```python
# models/shared/schemas.py
from shared.schemas import create_health_response

@app.get("/health")
async def health_check():
    return create_health_response(
        service="my-api",
        version="1.0.0",
        gpu_available=torch.cuda.is_available(),
        model_loaded=model is not None
    )
```

---

## 5. 모니터링

### 프론트엔드 대시보드

```
http://localhost:5173/dashboard

기능:
• API 상태 모니터링 (18개 서비스)
• GPU 메모리 사용량
• 요청/응답 시간
• 에러 로그
```

### 로그 확인

```bash
# 실시간 로그
docker-compose logs -f

# 특정 서비스
docker logs gateway-api -f --tail 100

# 에러만 필터
docker logs gateway-api 2>&1 | grep -i error
```

### 리소스 모니터링

```bash
# Docker 리소스 사용량
docker stats

# GPU 사용량
nvidia-smi -l 1

# 디스크 사용량
docker system df
```

---

## 6. 트러블슈팅

### CI 실패

| 문제 | 해결 |
|------|------|
| ESLint 에러 | `npm run lint -- --fix` |
| TypeScript 에러 | `npm run build` 로 확인 |
| pytest 실패 | `pytest tests/test_xxx.py -v` 로 개별 확인 |
| 의존성 문제 | `npm ci` 또는 `pip install -r requirements.txt` |

### Docker 문제

| 문제 | 해결 |
|------|------|
| 포트 충돌 | `lsof -i :포트` 로 확인 후 종료 |
| 이미지 빌드 실패 | `docker-compose build --no-cache 서비스명` |
| 메모리 부족 | `docker system prune -a` |
| GPU 인식 안됨 | `nvidia-smi` 확인, docker 재시작 |

### 배포 롤백

```bash
# Docker Compose
docker-compose down
docker-compose pull  # 이전 이미지로 변경 후
docker-compose up -d

# Kubernetes (사용 시)
kubectl rollout undo deployment/gateway-api
kubectl rollout status deployment/gateway-api
```

---

## 7. 배포 체크리스트

### Staging 배포 전

- [ ] 모든 테스트 통과 (505개)
- [ ] ESLint 에러 0개
- [ ] TypeScript 빌드 성공
- [ ] .env.example 업데이트 확인

### Production 배포 전

- [ ] Staging에서 테스트 완료
- [ ] 헬스체크 정상
- [ ] 롤백 계획 확인
- [ ] 팀 공유

---

## 8. 파일 위치 참조

```
.github/workflows/
├── ci.yml                    # CI 파이프라인
└── cd.yml                    # CD 파이프라인

models/shared/
├── __init__.py
└── schemas.py                # StandardHealthResponse

.env.example                  # 환경변수 템플릿
docker-compose.yml            # Docker 구성
```
