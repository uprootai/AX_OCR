# 🎯 AX Drawing Analysis System

**Version**: 2.0.0
**Status**: Production Ready ✅
**Last Updated**: 2025-11-19

> **완전한 마이크로서비스 기반 AI 도면 분석 시스템**
> YOLO + eDOCr2 + EDGNet + Skin Model을 활용한 기계 도면 자동 분석 및 견적 생성

---

## 🚀 Quick Start

### 1. 시스템 시작

```bash
# Docker Compose로 모든 서비스 시작
cd /home/uproot/ax/poc
docker-compose up -d

# 웹 UI 접속
http://localhost:5173
```

### 2. 주요 페이지

| 페이지 | URL | 설명 |
|--------|-----|------|
| **메인** | http://localhost:5173 | 랜딩 페이지 |
| **Gateway 테스트** | http://localhost:5173/test/gateway | 통합 파이프라인 테스트 |
| **YOLO 테스트** | http://localhost:5173/test/yolo | YOLO 객체 검출 테스트 |
| **OCR 테스트** | http://localhost:5173/test/edocr2 | eDOCr2 OCR 테스트 |
| **EDGNet 테스트** | http://localhost:5173/test/edgnet | 그래프 세그멘테이션 테스트 |

---

## 📊 System Architecture

### Services Overview

| Service | Port | Description | Status |
|---------|------|-------------|--------|
| **Web UI** | 5173 | React 프론트엔드 | ✅ |
| **Gateway API** | 8000 | 통합 파이프라인 오케스트레이터 | ✅ |
| **YOLO API** | 5005 | 객체 검출 (YOLO v11) | ✅ |
| **eDOCr2 v2 API** | 5002 | 도면 특화 OCR | ✅ |
| **EDGNet API** | 5012 | 세그멘테이션 (GraphSAGE + UNet) | ✅ |
| **Skin Model API** | 5003 | 공차 예측 (XGBoost) | ✅ |
| **PaddleOCR API** | 5006 | 범용 OCR (보조) | ✅ |
| **VL API** | 5004 | 비전-언어 모델 (API 키 필요) | 🔑 |

### Pipeline Flow

```
사용자 → Web UI → Gateway API → ┬→ YOLO API (객체 검출)
                                 ├→ eDOCr2 API (OCR)
                                 ├→ EDGNet API (세그멘테이션)
                                 ├→ Skin Model API (공차 예측)
                                 └→ Ensemble & Quote Generation
```

---

## 📁 Complete Project Structure

```
/home/uproot/ax/poc/
│
├── 📄 핵심 문서 (Root Documentation)
│   ├── README.md                    # 이 파일 - 프로젝트 개요
│   ├── CLAUDE.md                    # LLM을 위한 프로젝트 가이드
│   ├── QUICK_START.md               # 5분 빠른 시작 가이드
│   ├── ARCHITECTURE.md              # 시스템 아키텍처 상세
│   ├── WORKFLOWS.md                 # 개발 워크플로우 가이드
│   ├── ROADMAP.md                   # 프로젝트 진행 상황 및 계획
│   ├── KNOWN_ISSUES.md              # 알려진 이슈 추적
│   ├── LLM_USABILITY_GUIDE.md       # LLM 최적화 가이드
│   ├── FILE_AUDIT_REPORT.md         # 파일 감사 보고서
│   └── README_DASHBOARD.md          # 대시보드 문서
│
├── 🌐 Frontend (Web UI)
│   └── web-ui/                      # React + TypeScript + Vite
│       ├── src/
│       │   ├── pages/               # 페이지 컴포넌트
│       │   │   ├── Landing.tsx
│       │   │   ├── test/            # API 테스트 페이지
│       │   │   │   ├── TestGateway.tsx
│       │   │   │   ├── TestYOLO.tsx
│       │   │   │   ├── TestEDOCr2.tsx
│       │   │   │   ├── TestEDGNet.tsx
│       │   │   │   └── TestVL.tsx
│       │   ├── components/          # 재사용 컴포넌트
│       │   │   ├── debug/           # 디버그 UI
│       │   │   ├── guides/          # 사용 가이드
│       │   │   ├── ui/              # 공통 UI
│       │   │   └── upload/          # 파일 업로드
│       │   ├── config/
│       │   │   └── api.ts           # API 엔드포인트 중앙 설정
│       │   └── lib/                 # 유틸리티
│       ├── public/
│       │   └── samples/             # 샘플 도면 이미지
│       └── dist/                    # 빌드 결과물
│
├── 🔗 Backend APIs (Microservices)
│   ├── gateway-api/                 # 통합 Gateway (Port 8000)
│   │   ├── api_server.py            # FastAPI 서버 (1500+ 라인)
│   │   ├── models/                  # Pydantic 모델
│   │   │   ├── request.py           # 요청 스키마
│   │   │   └── response.py          # 응답 스키마
│   │   ├── services/                # 비즈니스 로직
│   │   │   ├── yolo_service.py
│   │   │   ├── ocr_service.py
│   │   │   ├── segmentation_service.py
│   │   │   ├── tolerance_service.py
│   │   │   ├── ensemble_service.py
│   │   │   └── quote_service.py
│   │   ├── utils/                   # 유틸리티
│   │   │   ├── visualization.py     # 시각화 생성 ⭐
│   │   │   ├── progress.py          # 진행 상황 추적
│   │   │   ├── filters.py           # 필터링
│   │   │   └── helpers.py
│   │   ├── uploads/                 # 업로드 임시 저장
│   │   └── results/                 # 결과 저장
│   │
│   ├── yolo-api/                    # YOLO 객체 검출 (Port 5005)
│   │   ├── api_server.py            # FastAPI 서버 (324 라인)
│   │   ├── models/
│   │   │   ├── schemas.py           # Pydantic 스키마
│   │   │   └── yolo11n.pt           # YOLO v11 nano 모델
│   │   ├── services/
│   │   │   └── inference.py         # YOLO 추론 로직
│   │   └── utils/
│   │       └── helpers.py
│   │
│   ├── edocr2-v2-api/               # eDOCr v2 OCR (Port 5002)
│   │   ├── api_server.py            # FastAPI 서버 (228 라인)
│   │   ├── models/
│   │   │   ├── schemas.py
│   │   │   └── edocr_*.ckpt         # eDOCr2 체크포인트
│   │   ├── services/
│   │   │   └── ocr_processor.py     # OCR 처리 (Singleton)
│   │   ├── utils/
│   │   │   ├── visualization.py     # OCR 시각화 ⭐
│   │   │   └── helpers.py
│   │   └── enhancers/               # 전처리 모듈
│   │
│   ├── edgnet-api/                  # EDGNet 세그멘테이션 (Port 5012)
│   │   ├── api_server.py            # FastAPI 서버 (349 라인)
│   │   ├── models/
│   │   │   ├── schemas.py
│   │   │   ├── graphsage_*.pth      # GraphSAGE 모델
│   │   │   └── edgnet_large.pth     # UNet 모델 (355MB)
│   │   ├── services/
│   │   │   ├── inference.py         # EDGNet 파이프라인
│   │   │   └── unet_inference.py    # UNet 추론 서비스
│   │   └── utils/
│   │       ├── visualization.py     # EDGNet/UNet 시각화 ⭐
│   │       └── helpers.py
│   │
│   ├── skinmodel-api/               # Skin Model 공차 예측 (Port 5003)
│   │   ├── api_server.py            # FastAPI 서버 (205 라인)
│   │   ├── models/
│   │   │   ├── schemas.py
│   │   │   └── xgb_model.json       # XGBoost 모델
│   │   ├── services/
│   │   │   └── tolerance.py         # 공차 예측 로직
│   │   ├── utils/
│   │   │   ├── visualization.py     # 공차 게이지 시각화 ⭐
│   │   │   └── helpers.py
│   │   └── data/                    # 학습 데이터
│   │
│   ├── paddleocr-api/               # PaddleOCR (Port 5006)
│   │   ├── api_server.py            # FastAPI 서버 (203 라인)
│   │   ├── services/
│   │   │   └── ocr.py               # PaddleOCR 래퍼
│   │   └── utils/
│   │
│   └── vl-api/                      # Vision-Language API (Port 5004)
│       ├── api_server.py            # FastAPI 서버
│       └── uploads/
│
├── 📊 Datasets
│   ├── datasets/                    # 학습/테스트 데이터셋
│   │   ├── combined/                # 통합 데이터셋
│   │   ├── engineering_drawings/    # 기계 도면
│   │   ├── pid_symbols/             # P&ID 심볼
│   │   ├── synthetic_random/        # 합성 데이터 (랜덤)
│   │   └── synthetic_test/          # 합성 데이터 (테스트)
│   ├── edgnet_dataset/              # EDGNet 원본 데이터 (5개)
│   │   └── drawings/
│   ├── edgnet_dataset_augmented/    # EDGNet 증강 데이터
│   │   └── drawings/
│   ├── edgnet_dataset_large/        # EDGNet 대규모 데이터
│   └── test_samples/                # 테스트 샘플 이미지
│       ├── Mechanical-Engineering-Drawings/
│       ├── MechanicalBlueprints/
│       └── drawings/
│
├── 🔧 Scripts & Tools
│   └── scripts/                     # 유틸리티 스크립트
│       ├── tests/                   # 주요 테스트 스크립트
│       │   ├── test_full_pipeline.py
│       │   ├── test_yolo_api_direct.py
│       │   ├── test_pid_ocr.py
│       │   └── test_sample_final.py
│       ├── test/                    # 기타 테스트
│       ├── deploy/                  # 배포 스크립트
│       └── archive/                 # 보관된 스크립트
│
├── 📚 Documentation
│   └── docs/
│       ├── archive/                 # 아카이브 (과거 문서)
│       │   ├── TODO/                # 과거 TODO 및 보고서
│       │   ├── analysis/            # 과거 분석 문서
│       │   ├── refactoring/         # 리팩토링 문서
│       │   └── screenshots/         # 스크린샷
│       ├── architecture/            # 아키텍처 문서
│       ├── developer/               # 개발자 가이드
│       ├── user/                    # 사용자 가이드
│       ├── technical/               # 기술 문서
│       ├── testing/                 # 테스트 문서
│       ├── reports/                 # 보고서
│       ├── references/              # 참고 자료
│       └── opensource/              # 오픈소스 문서
│
├── 🛠️ Development
│   ├── dev/                         # 개발 중인 기능
│   │   ├── edgnet/                  # EDGNet 개발
│   │   ├── edocr2/                  # eDOCr2 개발
│   │   ├── skinmodel/               # Skin Model 개발
│   │   └── test_results/            # 테스트 결과
│   ├── experiments/                 # 실험적 기능
│   ├── common/                      # 공통 모듈
│   └── admin-dashboard/             # 관리 대시보드 (구버전)
│       ├── dashboard.py
│       ├── training_manager.py
│       └── templates/
│
├── 📈 Monitoring & Logs
│   ├── monitoring/                  # 모니터링 설정
│   │   ├── prometheus/              # Prometheus 설정
│   │   └── grafana/                 # Grafana 대시보드
│   ├── logs/                        # 애플리케이션 로그
│   ├── runs/                        # YOLO 학습/검출 결과
│   │   ├── train/                   # 학습 결과
│   │   └── detect/                  # 검출 결과
│   └── test_results/                # 테스트 결과
│       └── archive/                 # 보관된 테스트 결과
│
├── 🐳 Docker & Config
│   ├── docker-compose.yml           # Docker Compose 설정
│   ├── .env                         # 환경 변수 (git ignore)
│   ├── .dockerignore                # Docker 제외 파일
│   └── .gitignore                   # Git 제외 파일
│
├── 🤖 Claude Code Integration
│   └── .claude/                     # Claude Code 설정
│       ├── commands/                # 커스텀 명령어
│       └── skills/                  # 커스텀 스킬
│
└── 🔍 Cache & Temp
    ├── __pycache__/                 # Python 캐시
    └── web-ui/node_modules/         # Node.js 의존성
```

---

## 🎨 Key Features

### 1. 파이프라인 시각화 시스템 ⭐ NEW (2025-11-19)

각 파이프라인 단계별로 **컬러 시각화** 제공:

- ✅ **YOLO 검출**: 바운딩 박스 + 클래스 라벨
- ✅ **OCR 추출**: 치수선(라임그린), GD&T(시안), 텍스트(노랑)
- ✅ **EDGNet 세그멘테이션**: 클래스별 색상 (804개 컴포넌트)
- ✅ **Ensemble 통합**: 소스별 색상 (마젠타/노랑/시안)
- ✅ **Tolerance 예측**: 제조 가능성 게이지

**기술 스택**:
- OpenCV 기반 고품질 렌더링
- Base64 인코딩으로 JSON 응답 통합
- 고대비 색상 팔레트 (BGR 형식)
- 반투명 오버레이 + 두꺼운 테두리 (3px)

### 2. 모듈화된 아키텍처

**All APIs follow the same structure**:
```
{api-name}/
├── api_server.py (200-350 lines)  ← Endpoints only
├── models/schemas.py              ← Pydantic models
├── services/{service}.py          ← Business logic
└── utils/helpers.py               ← Utility functions
```

**Benefits**:
- 🔍 **LLM 최적화**: <200 라인 파일로 효율적 컨텍스트
- 🔄 **재사용성**: 서비스 간 독립적
- 🧪 **테스트 용이**: 단위 테스트 가능
- 📚 **유지보수**: 단일 책임 원칙

### 3. 성능 최적화

| Component | Optimization | Impact |
|-----------|--------------|--------|
| **eDOCr2** | GPU 전처리 | 2-5x 빠름 |
| **Skin Model** | sklearn → XGBoost | 8x 빠름 |
| **YOLO** | v8 → v11 nano | 경량화 |
| **Gateway** | 비동기 병렬 처리 | 3-way parallel |

### 4. 프로덕션 준비

- ✅ **Docker Compose**: 8개 서비스 오케스트레이션
- ✅ **Health Checks**: 모든 API 헬스체크 엔드포인트
- ✅ **Error Handling**: 포괄적 에러 처리
- ✅ **Logging**: 구조화된 로깅 시스템
- ✅ **CORS**: 프론트엔드 통합 지원

---

## 🔧 Development Guide

### Prerequisites

```bash
# Python 3.10+
python --version

# Docker & Docker Compose
docker --version
docker-compose --version

# Node.js 18+ (for web-ui)
node --version
```

### Installation

```bash
# 1. Clone repository
cd /home/uproot/ax/poc

# 2. Start all services
docker-compose up -d

# 3. Check health
curl http://localhost:8000/api/v1/health

# 4. Start web UI (development)
cd web-ui
npm install
npm run dev
```

### Testing

```bash
# 전체 파이프라인 테스트
python3 scripts/tests/test_full_pipeline.py

# YOLO API 직접 테스트
python3 scripts/tests/test_yolo_api_direct.py

# PID OCR 테스트
python3 scripts/tests/test_pid_ocr.py
```

### Adding New Features

자세한 내용은 **[WORKFLOWS.md](WORKFLOWS.md)** 참조:
- 새 API 추가 방법
- 기존 기능 수정 방법
- 디버깅 및 테스트 방법

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [QUICK_START.md](QUICK_START.md) | 5분 빠른 시작 가이드 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 시스템 아키텍처 상세 설명 |
| [WORKFLOWS.md](WORKFLOWS.md) | 개발 워크플로우 가이드 |
| [ROADMAP.md](ROADMAP.md) | 프로젝트 진행 상황 및 계획 |
| [KNOWN_ISSUES.md](KNOWN_ISSUES.md) | 알려진 이슈 및 해결 방법 |
| [LLM_USABILITY_GUIDE.md](LLM_USABILITY_GUIDE.md) | LLM 최적화 가이드 |
| [CLAUDE.md](CLAUDE.md) | Claude Code를 위한 프로젝트 가이드 |

---

## 🎯 Roadmap

### ✅ Completed (Phase 1-2: 2025-11-18 ~ 2025-11-19)

- [x] Gateway API 모듈화 (1600 → 1500 라인)
- [x] 모든 API 리팩토링 (8개 API)
- [x] 파이프라인 시각화 시스템 구축
- [x] 프로젝트 구조 정리 (70개 → 10개 루트 파일)
- [x] 문서화 시스템 완성

### 🔄 In Progress (Phase 3)

- [ ] EDGNet 대규모 학습 (25KB → 500MB+ 모델)
- [ ] YOLO 커스텀 데이터셋 학습
- [ ] Ensemble 필터링 최적화

### 📋 Planned (Phase 4+)

- [ ] VL API 통합 완료 (API 키 설정)
- [ ] RESTful API 문서 자동 생성 (Swagger/OpenAPI)
- [ ] CI/CD 파이프라인 구축
- [ ] Kubernetes 배포 설정

자세한 내용은 **[ROADMAP.md](ROADMAP.md)** 참조

---

## 🐛 Known Issues

현재 알려진 이슈 및 해결 방법은 **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** 참조

**Critical**: 없음 🎉
**High**: 없음 🎉
**Medium**: 4개 (기술 부채)
**Resolved**: 4개

---

## 📊 Project Metrics

| Metric | Value |
|--------|-------|
| **Total APIs** | 8 (Gateway + 7 Microservices) |
| **Total Lines of Code** | ~15,000+ |
| **Average API Size** | 200-350 lines (after refactoring) |
| **Total Services** | 9 (8 APIs + Web UI) |
| **Docker Containers** | 9 |
| **Documentation Files** | 10 (root) + 158 (archived) |
| **Test Scripts** | 4 (active) + 20 (archived) |

---

## 🤝 Contributing

This is a private project for AX demonstration. For questions or issues:

1. Check [KNOWN_ISSUES.md](KNOWN_ISSUES.md)
2. Review [WORKFLOWS.md](WORKFLOWS.md)
3. Contact the development team

---

## 📄 License

Proprietary - AX Project (2025)

---

## 🎊 Changelog

### 2.1.0 (2025-11-20)
- ✨ **UNet 엣지 세그멘테이션 모델 통합** (355MB, IoU 85.8%)
- 🚀 **EDGNet API 듀얼 모델 지원** (GraphSAGE + UNet)
- 📊 **새 엔드포인트**: `/api/v1/segment_unet`
- 🎨 **UNet 시각화**: 시안 오버레이 + 통계 표시

### 2.0.0 (2025-11-19)
- ✨ **파이프라인 시각화 시스템 추가**
- ♻️ **전체 프로젝트 구조 정리** (70개 → 10개 루트 파일)
- 📝 **문서화 시스템 완성**
- 🐛 **EDGNet 시각화 버그 수정**

### 1.0.0 (2025-11-18)
- ✨ **Gateway API 모듈화 완료**
- ♻️ **모든 API 리팩토링 완료** (8개 API)
- 📚 **핵심 문서 작성** (ARCHITECTURE, WORKFLOWS, ROADMAP 등)

---

**Ready to start?** Run `docker-compose up -d` and visit http://localhost:5173 🚀
