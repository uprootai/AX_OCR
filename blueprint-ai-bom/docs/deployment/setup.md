# Blueprint AI BOM - 설치 가이드

> **React + FastAPI 기반 도면 분석 시스템**
> **최종 업데이트**: 2025-12-24
> **버전**: v8.0

---

## 시스템 요구사항

### 최소 사양

| 항목 | 최소 | 권장 |
|------|------|------|
| CPU | 4 cores | 8+ cores |
| RAM | 8GB | 16GB+ |
| Storage | 20GB | 50GB+ |
| GPU | - | NVIDIA RTX 3060+ (CUDA 11.8+) |
| Docker | 20.10+ | Latest |
| Node.js | 18+ | 20+ (개발용) |
| Python | 3.10+ | 3.11+ |

---

## 빠른 시작 (Docker)

```bash
# 1. 저장소 클론
git clone <repository-url>
cd blueprint-ai-bom

# 2. Docker Compose 실행
docker-compose up -d

# 3. 접속
# Frontend: http://localhost:3000
# Backend API: http://localhost:5020
# API Docs: http://localhost:5020/docs
```

---

## 개발 환경 설정

### 1. 백엔드 (FastAPI)

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 패키지 설치
pip install -r requirements.txt

# 서버 실행
uvicorn api_server:app --host 0.0.0.0 --port 5020 --reload
```

### 2. 프론트엔드 (React)

```bash
cd frontend

# 패키지 설치
npm install

# 개발 서버 실행
npm run dev
# → http://localhost:5173 (Vite 기본값)

# 프로덕션 빌드
npm run build
```

---

## 필수 파일 및 디렉토리

### Git Clone 후 추가 필요 파일

```
blueprint-ai-bom/
├── models/
│   └── yolo/
│       └── best.pt           # YOLO v11 모델 (필수, 50-100MB)
├── classes_info_with_pricing.json  # 부품 가격 정보 (필수)
├── test_drawings/            # 테스트 도면 (선택)
│   ├── *.jpg, *.png
│   └── labels/               # Ground Truth 라벨
│       └── classes.txt       # 클래스 목록
└── class_examples/           # 클래스별 예시 이미지 (선택)
```

### 자동 생성 디렉토리

```
uploads/           # 사용자 업로드 이미지
results/           # 분석 결과
feedback/          # 검증 피드백 데이터 (v8.0)
yolo_training/     # YOLO 재학습 데이터셋 (v8.0)
```

---

## 환경 변수

### 백엔드 (.env)

```bash
# 서버 설정
HOST=0.0.0.0
PORT=5020

# 외부 API 연동 (AX POC Gateway 사용 시)
YOLO_API_URL=http://localhost:5005
EDOCR2_API_URL=http://localhost:5002

# 데이터 경로
UPLOAD_PATH=/app/uploads
RESULT_PATH=/app/results
FEEDBACK_DATA_PATH=/data/feedback
YOLO_EXPORT_PATH=/data/yolo_training

# GPU 설정
CUDA_VISIBLE_DEVICES=0

# 검증 임계값
AUTO_APPROVE_THRESHOLD=0.9
CRITICAL_THRESHOLD=0.7
```

### 프론트엔드 (.env)

```bash
VITE_API_BASE_URL=http://localhost:5020
```

---

## Docker 배포

### 개발 환경

```bash
# 빌드 및 시작
docker-compose up -d --build

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

### 온프레미스 배포

```bash
# 온프레미스 전용 설정 사용
docker-compose -f docker-compose.onprem.yml up -d --build
```

자세한 내용: [on-premises.md](./on-premises.md)

---

## 서비스 구성

### 포트 구성

| 서비스 | 컨테이너 | 포트 | 설명 |
|--------|----------|------|------|
| Backend | blueprint-ai-bom-backend | 5020 | FastAPI 서버 |
| Frontend | blueprint-ai-bom-frontend | 3000 (→80) | React 앱 (nginx) |

### 외부 의존성 (AX POC 사용 시)

| 서비스 | 포트 | 설명 |
|--------|------|------|
| YOLO API | 5005 | 객체 검출 |
| eDOCr2 API | 5002 | OCR 치수 인식 |
| Gateway | 8000 | 파이프라인 조정 |

---

## Health Check

```bash
# 백엔드 상태 확인
curl http://localhost:5020/health

# 응답 예시
{
  "status": "healthy",
  "version": "8.0.0",
  "services": {
    "yolo": "connected",
    "edocr2": "connected"
  }
}
```

---

## 테스트

```bash
# 백엔드 단위 테스트 (27개)
cd backend
python -m pytest tests/ -v

# 프론트엔드 빌드 검증
cd frontend
npm run build
```

---

## 문제 해결

### 1. 모델 파일 누락

```bash
# 오류: "모델 파일을 찾을 수 없습니다"
# 해결: YOLO 모델 배치
mkdir -p models/yolo
cp /path/to/best.pt models/yolo/best.pt
```

### 2. GPU 메모리 부족

```bash
# CPU 모드로 전환
export CUDA_VISIBLE_DEVICES=-1

# 또는 Docker에서
docker run --gpus '"device=0"' --shm-size=2g ...
```

### 3. 포트 충돌

```bash
# 다른 포트 사용
BACKEND_PORT=5021 FRONTEND_PORT=3001 docker-compose up -d
```

### 4. CORS 오류

프론트엔드와 백엔드 도메인이 다른 경우:

```python
# api_server.py에서 CORS 설정 확인
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 업데이트

```bash
# 최신 코드 가져오기
git pull

# Docker 이미지 재빌드
docker-compose down
docker-compose up -d --build

# 또는 개발 환경
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

---

## 관련 문서

| 문서 | 설명 |
|------|------|
| [on-premises.md](./on-premises.md) | 온프레미스 배포 가이드 |
| [model_download.md](./model_download.md) | 모델 다운로드 |
| [../api/reference.md](../api/reference.md) | API 레퍼런스 |
| [../features/active_learning.md](../features/active_learning.md) | Active Learning |
| [../features/feedback_pipeline.md](../features/feedback_pipeline.md) | Feedback Loop |

---

**작성자**: Claude Code (Opus 4.5)
**최종 업데이트**: 2025-12-24
