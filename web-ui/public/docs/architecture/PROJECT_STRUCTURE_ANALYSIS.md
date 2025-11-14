# AX POC 프로젝트 구조 분석 및 개선 제안

**작성일**: 2025-10-29
**버전**: 1.0
**목적**: 장기 프로젝트를 위한 디렉토리 구조 검토 및 개선안 제시

---

## 📁 현재 프로젝트 구조

### 전체 구조 개요

```
/home/uproot/ax/
├── poc/                    # POC 메인 디렉토리 (Git 관리)
│   ├── web-ui/            # 프론트엔드 (React + TypeScript)
│   ├── edocr2-api/        # eDOCr OCR 마이크로서비스
│   ├── edgnet-api/        # EdgeNet 벡터화 마이크로서비스
│   ├── skinmodel-api/     # SkinModel 마이크로서비스
│   ├── gateway-api/       # API Gateway (통합 라우팅)
│   ├── dev/               # 개발용 원본 소스
│   ├── test_samples/      # 테스트 샘플 파일들
│   └── *.md               # 문서 및 스크린샷
│
├── opensource/            # GitHub 오픈소스 레포지토리 (Git 관리 X)
│   ├── 01-immediate/
│   ├── 02-short-term/
│   ├── 03-research/
│   ├── 04-not-available/
│   └── 05-out-of-scope/
│
├── dev/                   # 개발 환경
├── docs/                  # 문서
├── paper/                 # 논문 자료
└── reference/             # 참고 자료
```

---

## 🔍 현재 구조 분석

### ✅ 장점

1. **마이크로서비스 아키텍처**
   - 각 서비스가 독립적으로 분리됨 (`*-api/`)
   - 서비스별 독립 배포 가능
   - 확장성 우수

2. **API Gateway 패턴**
   - `gateway-api`가 중앙 라우팅 담당
   - 프론트엔드는 단일 엔드포인트로 통신

3. **모노레포 구조**
   - `poc/` 하위에 모든 서비스 통합
   - Git으로 전체 프로젝트 관리 용이
   - 버전 관리 일관성

4. **명확한 문서화**
   - README, 상태 보고서, 개선 요약 등 체계적 문서
   - 진행 과정 추적 가능

### ⚠️ 개선 필요사항

#### 1. **디렉토리 구조 혼재**

**문제점**:
```
poc/
├── dev/                    # 개발용? 왜 여기에?
├── edocr2-api/            # 서비스
├── gateway-api/           # 서비스
├── *.py                   # 테스트 스크립트들 (루트에 산재)
├── *.md                   # 문서들 (루트에 산재)
└── screenshot_*.png       # 스크린샷들 (루트에 산재)
```

**개선안**: 명확한 카테고리 분리 필요

#### 2. **개발/배포 환경 분리 불명확**

**문제점**:
- `dev/` 디렉토리 용도 불명확
- `*-api/` 서비스들이 Docker 기반인데 로컬 개발 환경 설정 누락
- 환경 변수 관리 분산 (`.env` 파일 없음)

#### 3. **테스트 코드 관리**

**문제점**:
- 테스트 스크립트들이 루트에 흩어져 있음
  - `test_apis.py`, `test_pdf_conversion.py`, `test_tooltip.py` 등
- 단위 테스트 vs 통합 테스트 구분 없음

#### 4. **정적 파일 (스크린샷, 샘플) 관리**

**문제점**:
- 40+ 스크린샷 파일이 루트에 있음
- Git 저장소 크기 증가
- 버전 관리 대상이 아닌 파일들

#### 5. **opensource 디렉토리 위치**

**현재**: `/home/uproot/ax/opensource`
- POC Git 저장소 밖에 위치
- 문서에서 참조하기 어려움

---

## 🎯 개선안

### 제안 1: 표준 모노레포 구조

```
/home/uproot/ax/poc/
│
├── apps/                           # 애플리케이션들
│   ├── web-ui/                    # 프론트엔드
│   ├── gateway-api/               # API Gateway
│   └── [future-apps]/             # 향후 추가 앱
│
├── services/                       # 백엔드 마이크로서비스
│   ├── edocr2-api/                # eDOCr OCR 서비스
│   │   ├── v1/                    # v1 API 코드
│   │   ├── v2/                    # v2 API 코드
│   │   ├── models/                # AI 모델 파일
│   │   ├── tests/                 # 서비스별 테스트
│   │   ├── Dockerfile.v1
│   │   ├── Dockerfile.v2
│   │   └── README.md
│   ├── edgnet-api/                # EdgeNet 서비스
│   ├── skinmodel-api/             # SkinModel 서비스
│   └── [future-services]/         # 향후 추가 서비스
│
├── packages/                       # 공유 라이브러리 (향후)
│   ├── shared-types/              # TypeScript 타입 정의
│   ├── common-utils/              # 공통 유틸리티
│   └── api-client/                # API 클라이언트 SDK
│
├── docs/                           # 문서화
│   ├── architecture/              # 아키텍처 문서
│   ├── api/                       # API 문서
│   ├── guides/                    # 가이드
│   ├── progress/                  # 진행 상황 보고서
│   └── screenshots/               # 스크린샷 (Git LFS 사용)
│
├── tests/                          # 통합 테스트
│   ├── integration/               # 통합 테스트
│   ├── e2e/                       # E2E 테스트 (Playwright)
│   └── performance/               # 성능 테스트
│
├── scripts/                        # 유틸리티 스크립트
│   ├── setup/                     # 환경 설정
│   ├── deploy/                    # 배포
│   └── test/                      # 테스트 실행
│
├── data/                           # 데이터 파일
│   ├── samples/                   # 테스트 샘플
│   │   ├── drawings/
│   │   ├── blueprints/
│   │   └── pdfs/
│   └── fixtures/                  # 테스트 픽스처
│
├── infra/                          # 인프라 코드
│   ├── docker/                    # Docker 관련
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.dev.yml
│   │   └── docker-compose.prod.yml
│   ├── k8s/                       # Kubernetes (향후)
│   └── terraform/                 # Terraform (향후)
│
├── .github/                        # GitHub Actions
│   ├── workflows/
│   └── ISSUE_TEMPLATE/
│
├── .gitignore
├── .gitattributes                 # Git LFS 설정
├── README.md                      # 프로젝트 소개
├── CONTRIBUTING.md                # 기여 가이드
└── LICENSE
```

### 제안 2: 간소화된 구조 (현재 기반)

현재 구조를 크게 변경하지 않고 개선:

```
/home/uproot/ax/poc/
│
├── web-ui/                        # 프론트엔드 (현재 유지)
├── edocr2-api/                    # OCR 서비스
│   ├── v1/                        # v1 구현
│   │   ├── api_server_edocr_v1.py
│   │   ├── Dockerfile.v1
│   │   └── requirements_v1.txt
│   ├── v2/                        # v2 구현
│   │   ├── api_server_edocr_v2.py
│   │   ├── Dockerfile.v2
│   │   └── requirements_v2.txt
│   ├── models/                    # AI 모델
│   ├── tests/                     # 테스트
│   └── README.md
│
├── edgnet-api/                    # EdgeNet 서비스
├── skinmodel-api/                 # SkinModel 서비스
├── gateway-api/                   # API Gateway
│
├── docs/                           # 📁 NEW: 문서 통합
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── architecture/
│   ├── progress/
│   │   ├── PROGRESS_REPORT.md
│   │   ├── DEPLOYMENT_STATUS.md
│   │   └── IMPROVEMENTS_SUMMARY.md
│   └── screenshots/               # 스크린샷 이동
│
├── tests/                          # 📁 NEW: 테스트 통합
│   ├── test_apis.py
│   ├── test_pdf_conversion.py
│   ├── test_ocr_visualization.py
│   └── integration/
│
├── scripts/                        # 📁 NEW: 스크립트 정리
│   ├── test_apis.sh
│   ├── deploy.sh
│   └── setup_dev.sh
│
├── data/                           # 📁 RENAMED: test_samples → data
│   ├── samples/
│   │   ├── drawings/
│   │   ├── blueprints/
│   │   └── pdfs/
│   └── fixtures/
│
├── docker-compose.yml             # 통합 compose
├── .env.example                   # 환경 변수 예시
├── .gitignore
└── README.md
```

---

## 🔄 마이그레이션 계획

### Phase 1: 문서 및 스크립트 정리 (1-2시간)

```bash
# 1. docs 디렉토리 생성 및 이동
mkdir -p docs/{architecture,progress,screenshots}
mv *.md docs/
mv screenshot_*.png docs/screenshots/
mv analysis-*.png docs/screenshots/

# 2. tests 디렉토리 생성 및 이동
mkdir -p tests/{integration,e2e}
mv test_*.py tests/
mv test_*.sh tests/

# 3. scripts 디렉토리 생성
mkdir -p scripts
mv test_apis.sh scripts/

# 4. data 디렉토리 리네임
mv test_samples data/samples

# 5. 환경 변수 템플릿 생성
cat > .env.example <<EOF
# API Ports
EDOCR2_PORT=5001
EDGNET_PORT=5002
SKINMODEL_PORT=5003
GATEWAY_PORT=5000

# Web UI
VITE_API_GATEWAY_URL=http://localhost:5000
EOF
```

### Phase 2: edocr2-api v1/v2 분리 (2-3시간)

```bash
cd edocr2-api

# v1 디렉토리 생성 및 이동
mkdir -p v1
mv api_server_edocr_v1.py v1/
mv Dockerfile.v1 v1/
mv requirements_v1.txt v1/

# v2 디렉토리 생성 (새로 구현)
mkdir -p v2
# v2 구현 파일 생성

# 공통 모델 디렉토리는 유지
# models/ 디렉토리는 루트에 유지
```

### Phase 3: Docker Compose 통합 (1시간)

```yaml
# docker-compose.yml
version: '3.8'

services:
  # eDOCr v1
  edocr2-v1:
    build:
      context: ./edocr2-api/v1
      dockerfile: Dockerfile.v1
    container_name: edocr2-api-v1
    ports:
      - "5001:5001"
    volumes:
      - ./edocr2-api/models:/app/models:ro
      - ./edocr2-api/uploads:/app/uploads
      - ./edocr2-api/results:/app/results
    networks:
      - poc-network

  # eDOCr v2
  edocr2-v2:
    build:
      context: ./edocr2-api/v2
      dockerfile: Dockerfile.v2
    container_name: edocr2-api-v2
    ports:
      - "5002:5002"
    volumes:
      - ./edocr2-api/models:/app/models:ro
      - ./edocr2-api/uploads:/app/uploads
      - ./edocr2-api/results:/app/results
    networks:
      - poc-network

  # Gateway
  gateway:
    build: ./gateway-api
    container_name: gateway-api
    ports:
      - "5000:5000"
    depends_on:
      - edocr2-v1
      - edocr2-v2
      - edgnet
      - skinmodel
    networks:
      - poc-network

  # Web UI
  web-ui:
    build: ./web-ui
    container_name: web-ui
    ports:
      - "5173:5173"
    environment:
      - VITE_API_GATEWAY_URL=http://localhost:5000
    networks:
      - poc-network

networks:
  poc-network:
    driver: bridge
```

### Phase 4: Git 정리 (1시간)

```bash
# Git LFS 설정 (큰 파일 관리)
git lfs install
git lfs track "*.png"
git lfs track "*.jpg"
git lfs track "*.pdf"
git lfs track "*.keras"
git lfs track "*.h5"

# .gitignore 업데이트
cat >> .gitignore <<EOF
# Environment
.env
.env.local

# Data
data/samples/*
!data/samples/.gitkeep
data/fixtures/*
!data/fixtures/.gitkeep

# Results
*/results/*
!*/results/.gitkeep
*/uploads/*
!*/uploads/.gitkeep

# Models (LFS로 관리)
# *.keras
# *.h5

# Screenshots (docs/screenshots는 LFS로 관리)
docs/screenshots/*.png
docs/screenshots/*.jpg

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Python
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
venv/
.venv/

# Node
node_modules/
dist/
build/
.cache/

# Docker
*.log
EOF

# Git commit
git add .
git commit -m "chore: 프로젝트 구조 개선

- docs/ 디렉토리로 문서 통합
- tests/ 디렉토리로 테스트 통합
- edocr2-api v1/v2 분리
- Docker Compose 통합
- Git LFS 설정"
```

---

## 📊 개선 효과

### 1. **유지보수성 향상**
- 파일 찾기 쉬움
- 명확한 책임 분리
- 신규 멤버 온보딩 시간 단축

### 2. **확장성**
- 새로운 서비스 추가 용이
- 공통 라이브러리 관리 가능
- 모노레포 도구 활용 가능 (Turborepo, Nx)

### 3. **Git 관리 효율화**
- Git LFS로 대용량 파일 관리
- 저장소 크기 감소
- 히스토리 깔끔

### 4. **CI/CD 준비**
- GitHub Actions 워크플로우 추가 용이
- 서비스별 독립 배포 가능
- 테스트 자동화 준비

---

## 🚀 권장 사항

### 즉시 적용 (High Priority)

1. **문서 및 스크립트 정리** (Phase 1)
   - 영향: 최소
   - 효과: 즉시 개선
   - 시간: 1-2시간

2. **edocr2-api v1/v2 분리** (Phase 2)
   - 현재 v1/v2 혼재 문제 해결
   - 유지보수 용이
   - 시간: 2-3시간

### 단계적 적용 (Medium Priority)

3. **Docker Compose 통합** (Phase 3)
   - 모든 서비스 통합 관리
   - 개발 환경 일관성
   - 시간: 1시간

4. **환경 변수 관리**
   - `.env.example` 추가
   - 민감 정보 분리
   - 시간: 30분

### 향후 고려 (Low Priority)

5. **모노레포 도구 도입**
   - Turborepo 또는 Nx
   - 빌드 캐싱, 증분 빌드
   - 시간: 1-2일

6. **CI/CD 파이프라인**
   - GitHub Actions 워크플로우
   - 자동 테스트, 배포
   - 시간: 2-3일

---

## 📝 체크리스트

### 마이그레이션 전

- [ ] 현재 상태 Git commit
- [ ] 백업 생성
- [ ] 팀원들과 구조 변경 논의

### 마이그레이션 중

- [ ] Phase 1: 문서 정리
- [ ] Phase 2: edocr2-api 분리
- [ ] Phase 3: Docker Compose 통합
- [ ] Phase 4: Git 정리

### 마이그레이션 후

- [ ] 모든 서비스 정상 동작 확인
- [ ] 문서 업데이트 (README, QUICKSTART)
- [ ] 팀원들에게 변경 사항 공유
- [ ] Git LFS 설정 확인

---

## 🔗 참고 자료

- [Monorepo 구조 Best Practices](https://monorepo.tools/)
- [Git LFS Documentation](https://git-lfs.github.com/)
- [Docker Compose Best Practices](https://docs.docker.com/compose/production/)
- [Microservices 아키텍처 패턴](https://microservices.io/)

---

**문서 작성**: Claude Code
**리뷰**: 검토 필요
**승인**: 미승인
