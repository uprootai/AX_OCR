# Blueprint AI BOM 디렉토리 구조

> **최종 업데이트**: 2026-01-17
> **버전**: v10.5 (Detectron2 통합)
> **총 파일 수**: ~320개 (node_modules 제외)
> **총 용량**: ~14MB (node_modules 제외)

---

## 프로젝트 개요

**AI 기반 도면 분석 및 BOM(Bill of Materials) 생성 솔루션**

```
도면 업로드 → VLM 분류 → YOLO 검출 → OCR 치수 인식 → GD&T 분석 → 리비전 비교 → BOM 생성
```

| 항목 | 값 |
|------|-----|
| **기술 스택** | FastAPI + React 19 + YOLO v11 + eDOCr2 |
| **프론트엔드** | http://localhost:3000 (Docker) / :5173 (dev) |
| **백엔드** | http://localhost:5020 |
| **검출 클래스** | 27개 산업용 전장 부품 |
| **출력 형식** | Excel, CSV, JSON, PDF |

---

## 디렉토리 트리

```
blueprint-ai-bom/
├── README.md                      # 프로젝트 문서
├── ROADMAP.md                     # 개발 로드맵
├── DIRECTORY_STRUCTURE.md         # 본 문서
├── docker-compose.yml             # Docker 배포 설정
├── docker-compose.onprem.yml      # 온프레미스 배포 설정
├── classes_info_with_pricing.json # 부품 가격 DB (27개)
├── ocr_ground_truth.json          # OCR 정답지
├── .gitignore
├── .dockerignore
│
├── backend/                       # FastAPI 백엔드 (7.8MB)
│   ├── api_server.py              # 메인 서버 (1030줄)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── services/                  # 비즈니스 로직 (19개)
│   ├── routers/                   # API 엔드포인트 (12개)
│   ├── schemas/                   # Pydantic 모델 (18개)
│   ├── tests/                     # 단위 테스트 (12개)
│   ├── uploads/                   # 런타임 세션 데이터
│   ├── test_results/              # 테스트 출력
│   └── class_examples/            # 전력설비 클래스 (27개)
│
├── frontend/                      # React 19 프론트엔드 (190MB)
│   ├── src/                       # 소스코드 (87개 파일)
│   │   ├── pages/                 # 페이지 (7개)
│   │   ├── components/            # 컴포넌트 (17+개)
│   │   ├── lib/                   # API 클라이언트
│   │   ├── store/                 # Zustand 스토어
│   │   ├── hooks/                 # 커스텀 훅
│   │   ├── types/                 # TypeScript 타입
│   │   └── config/                # 설정
│   ├── node_modules/              # npm 의존성 (188MB)
│   ├── dist/                      # 빌드 결과물 (688KB)
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── docs/                          # 문서 (408KB)
│   ├── api/                       # API 레퍼런스
│   ├── deployment/                # 배포 가이드
│   ├── features/                  # 기능 문서
│   ├── archive/                   # 레거시 문서
│   └── migration/                 # 마이그레이션 문서
│
├── scripts/                       # 유틸리티 스크립트 (44KB)
│   ├── export/export_package.py   # 납품 패키지 생성
│   ├── batch_test.py              # 배치 테스트
│   └── deploy_onprem.sh           # 온프레미스 배포
│
├── class_examples/                # 전장부품 클래스 예시 (188KB, 26개)
├── test_drawings/                 # 테스트 도면 (580KB)
├── models/                        # AI 모델 (심볼릭 링크 → 988MB 외부)
├── uploads/                       # Docker 런타임 업로드 (3MB)
└── results/                       # BOM 출력 결과 (44KB)
```

---

## 1. 루트 파일

| 파일명 | 용량 | 운영 필요 | 설명 |
|--------|------|-----------|------|
| `README.md` | 10KB | ✅ 필수 | 프로젝트 전체 문서, API 스펙 |
| `ROADMAP.md` | 8KB | ⚠️ 개발용 | 개발 로드맵 (v10.3 완료) |
| `classes_info_with_pricing.json` | 5KB | ✅ **필수** | 27개 부품 가격 정보 - BOM 생성 핵심 |
| `ocr_ground_truth.json` | 5KB | ⚠️ 테스트용 | OCR 정답지 - 정확도 검증용 |
| `docker-compose.yml` | 1.4KB | ✅ 필수 | Docker 배포 설정 |
| `docker-compose.onprem.yml` | 1.8KB | ✅ 필수 | 온프레미스 배포 설정 |
| `.gitignore` | 2KB | ✅ 필수 | Git 설정 |
| `.dockerignore` | 0.5KB | ✅ 필수 | Docker 빌드 설정 |

---

## 2. backend/ - FastAPI 백엔드

### 핵심 파일

| 파일 | 용량 | 설명 |
|------|------|------|
| `api_server.py` | 36KB | 메인 FastAPI 서버 (1030줄) |
| `Dockerfile` | 0.7KB | Docker 빌드 |
| `requirements.txt` | 0.5KB | Python 의존성 |

### services/ - 비즈니스 로직 (19개) ✅ 모두 필수

| 서비스 | 용량 | 기능 |
|--------|------|------|
| `detection_service.py` | 14KB | YOLO/Detectron2 객체 검출 |
| `detectron2_service.py` | 10KB | Mask R-CNN 인스턴스 세그멘테이션 (NEW) |
| `bom_service.py` | 20KB | BOM 생성 및 집계 |
| `session_service.py` | 8KB | 세션 관리 |
| `dimension_service.py` | 11KB | 치수 인식 |
| `dimension_relation_service.py` | 26KB | 치수-심볼 관계 |
| `gdt_parser.py` | 36KB | GD&T 파싱 |
| `active_learning_service.py` | 11KB | Active Learning 검증 |
| `vlm_classifier.py` | 25KB | VLM 자동 분류 |
| `notes_extractor.py` | 24KB | 노트 추출 |
| `region_segmenter.py` | 33KB | 영역 세분화 |
| `revision_comparator.py` | 26KB | 리비전 비교 |
| `line_detector_service.py` | 15KB | 라인 검출 |
| `connectivity_analyzer.py` | 17KB | 연결성 분석 |
| `feedback_pipeline.py` | 15KB | Feedback Loop |
| `pdf_report_service.py` | 23KB | PDF 리포트 생성 |
| `layout_analyzer.py` | 10KB | 레이아웃 분석 |
| `api_key_service.py` | 21KB | API 키 관리 |

### routers/ - API 엔드포인트 (12개) ✅ 모두 필수

| 라우터 | 용량 | 기능 |
|--------|------|------|
| `session_router.py` | 7KB | 세션 API |
| `detection_router.py` | 12KB | 검출 API |
| `bom_router.py` | 7KB | BOM API |
| `verification_router.py` | 12KB | 검증 API |
| `relation_router.py` | 12KB | 관계 API |
| `longterm_router.py` | 31KB | 장기 로드맵 API |
| `midterm_router.py` | 19KB | 중기 로드맵 API |
| `classification_router.py` | 10KB | 분류 API |
| `feedback_router.py` | 5KB | 피드백 API |
| `settings_router.py` | 11KB | 설정 API |
| `pid_features_router.py` | 4KB | PID 기능 API |

### schemas/ - Pydantic 모델 (18개) ✅ 모두 필수

API 요청/응답 데이터 검증용 스키마 정의

### tests/ - 단위 테스트 (12개) ⚠️ 개발/QA용

| 테스트 | 용량 | 설명 |
|--------|------|------|
| `test_bom_service.py` | 6KB | BOM 서비스 테스트 |
| `test_detection_service.py` | 3KB | 검출 서비스 테스트 |
| `test_detectron2_service.py` | 5KB | Detectron2 서비스 테스트 (NEW) |
| `test_pricing_utils.py` | 7KB | 가격 유틸 테스트 |
| `test_revision_comparator.py` | 11KB | 리비전 비교 테스트 |
| `test_longterm_api.py` | 6KB | 장기 API 테스트 |
| `test_feedback_pipeline.py` | 14KB | 피드백 테스트 |
| `test_layout_analyzer.py` | 7KB | 레이아웃 테스트 |
| `test_pdf_report_service.py` | 13KB | PDF 리포트 테스트 |
| `test_pid_features_api.py` | 11KB | PID 기능 테스트 |
| `test_techcross_workflow.py` | 14KB | TECHCROSS 워크플로우 테스트 |

### 런타임 디렉토리 ⚠️ 정리 가능

| 디렉토리 | 용량 | 설명 |
|----------|------|------|
| `uploads/` | 4.5MB | 테스트 세션 데이터 (22개) |
| `test_results/` | 2.2MB | 테스트 출력 이미지 |
| `.pytest_cache/` | 48KB | pytest 캐시 |
| `class_examples/` | 117KB | 전력설비 클래스 예시 (27개) |

---

## 3. frontend/ - React 프론트엔드

### 핵심 파일

| 파일 | 용량 | 설명 |
|------|------|------|
| `package.json` | 1KB | npm 의존성 정의 |
| `package-lock.json` | 151KB | 의존성 락 파일 |
| `Dockerfile` | 0.4KB | Docker 빌드 |
| `nginx.conf` | 1.5KB | Nginx 설정 |
| `vite.config.ts` | 0.2KB | Vite 빌드 설정 |
| `tsconfig*.json` | ~1.5KB | TypeScript 설정 |
| `tailwind.config.js` | 0.5KB | TailwindCSS 설정 |

### src/ - 소스코드 (87개 파일) ✅ 모두 필수

| 디렉토리 | 파일 수 | 주요 파일 |
|----------|---------|----------|
| `pages/` | 7개 | HomePage, DetectionPage, BOMPage, WorkflowPage, VerificationPage, GuidePage |
| `components/` | 17+개 | DrawingCanvas, DetectionCard, VerificationQueue, GDTEditor, RegionEditor 등 |
| `lib/` | - | API 클라이언트 (api.ts) |
| `store/` | - | Zustand 상태 관리 |
| `hooks/` | - | 커스텀 React 훅 |
| `types/` | - | TypeScript 타입 정의 |
| `config/` | - | 설정 |

### 런타임/빌드 디렉토리 ⚠️ 정리 가능

| 디렉토리 | 용량 | 설명 |
|----------|------|------|
| `node_modules/` | **188MB** | npm install로 재생성 가능 |
| `dist/` | 688KB | npm run build로 재생성 가능 |

---

## 4. docs/ - 문서 (408KB)

| 디렉토리 | 파일 수 | 필요성 | 설명 |
|----------|---------|--------|------|
| `api/` | 3개 | ✅ 필수 | API 레퍼런스 (Swagger UI 포함) |
| `deployment/` | 3개 | ✅ 필수 | 배포 가이드 (setup, on-premises, model) |
| `features/` | 6개 | ✅ 필수 | 기능 문서 (Active Learning, GDT, Feedback 등) |
| `archive/` | 3개 | ⚠️ 아카이브 | 레거시 Claude 가이드라인 |
| `migration/` | 7개 | ⚠️ 완료됨 | Streamlit→React 마이그레이션 (완료) |

---

## 5. 기타 디렉토리

| 디렉토리 | 용량 | 필요성 | 설명 |
|----------|------|--------|------|
| `scripts/` | 44KB | ✅ 필수 | 배포/테스트 스크립트 (3개) |
| `class_examples/` | 188KB | ✅ 필수 | 27개 전장부품 클래스 예시 이미지 |
| `test_drawings/` | 580KB | ✅ 필수 | 테스트용 샘플 도면 (8개) |
| `models/` | 심볼릭 | ✅ 필수 | AI 모델 (외부 988MB 참조) |
| `uploads/` | 3MB | ⚠️ 런타임 | Docker 테스트 세션 데이터 |
| `results/` | 44KB | ⚠️ 런타임 | BOM 출력 결과 파일 |

---

## 6. 27개 검출 클래스

| ID | 클래스명 | 한글명 | 단가 |
|----|---------|--------|------|
| 0 | BUZZER | 부저 | 12,000원 |
| 1 | HUB-8PORT | 허브 | 95,000원 |
| 2 | SMPS1 | 스위칭 파워 | 85,000원 |
| 3 | SMPS2 | 스위칭 파워 | 120,000원 |
| 4 | DISCONNECTING SWITCH | 단로기 | 28,000원 |
| 5 | POWER OUTLET | 콘센트 | 15,000원 |
| ... | ... | ... | ... |
| 26 | EMERGENCY BUTTON | 비상 버튼 | 12,000원 |

**전체 가격 정보**: `classes_info_with_pricing.json`

---

## 7. API 엔드포인트 요약

### 세션 관리
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/sessions/upload` | 이미지 업로드 |
| GET | `/sessions` | 세션 목록 |
| DELETE | `/sessions/{id}` | 세션 삭제 |

### 분석
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/analysis/detect/{id}` | YOLO 검출 |
| POST | `/analysis/ocr/{id}` | OCR 인식 |
| POST | `/analysis/full/{id}` | 전체 분석 |

### 검증 (Active Learning)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/verification/queue/{id}` | 검증 큐 조회 |
| POST | `/verification/verify/{id}` | 단일 항목 검증 |
| POST | `/verification/bulk-approve/{id}` | 일괄 승인 |

### BOM
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/bom/generate/{id}` | BOM 생성 |
| GET | `/bom/export/{id}/{format}` | 내보내기 (excel/csv/json/pdf) |

---

## 8. 정리 완료 내역

| 항목 | 상태 | 결과 |
|------|------|------|
| `config/` (루트) | ✅ 삭제됨 | 빈 폴더 제거 |
| `backend/config/` | ✅ 삭제됨 | 빈 폴더 제거 |
| `backend/results/` | ✅ 삭제됨 | 빈 폴더 제거 |
| `yolo_training/` | ✅ 삭제됨 | 빈 폴더 제거 |
| `feedback/` | ✅ 삭제됨 | 빈 폴더 제거 |

---

## 9. 운영 배포 최소 구성

```
blueprint-ai-bom/
├── backend/
│   ├── api_server.py
│   ├── services/
│   ├── routers/
│   ├── schemas/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── models/                        # AI 모델 필수
├── class_examples/
├── classes_info_with_pricing.json
├── docker-compose.yml
└── README.md
```

**최소 용량**: ~8MB (node_modules, 런타임 아티팩트 제외)

---

## 10. 명령어 참조

```bash
# 개발 서버 실행
cd backend && uvicorn api_server:app --port 5020 --reload
cd frontend && npm run dev

# Docker 실행
docker-compose up -d

# 테스트 실행
cd backend && python -m pytest tests/ -v

# 프론트엔드 빌드
cd frontend && npm run build

# 납품 패키지 생성
python scripts/export/export_package.py --customer "고객명" --output ./export
```

---

**작성자**: Claude Code (Opus 4.5)
**버전**: v1.0
