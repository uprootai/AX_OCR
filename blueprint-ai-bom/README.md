# Blueprint AI BOM

> **AI 기반 도면 분석 및 BOM 생성 솔루션**
> AX POC BlueprintFlow에서 Export되는 납품용 독립 실행 모듈
> **최종 업데이트**: 2026-01-17

---

## 개요

```
도면 업로드 → VLM 분류 → YOLO 검출 → OCR 치수 인식 → GD&T 분석 → 리비전 비교 → BOM 생성
```

| 항목 | 값 |
|------|-----|
| **상태** | ✅ 구현 완료 (v10.5) |
| **프론트엔드** | http://localhost:3000 (Docker) / :5173 (dev) |
| **백엔드** | http://localhost:5020 |
| **검출 클래스** | 27개 산업용 전장 부품 |
| **검출 백엔드** | YOLO (빠른 검출) / Detectron2 (마스킹 포함) |
| **출력 형식** | Excel, CSV, JSON, PDF |
| **장기 로드맵** | ✅ 4/4 기능 완료 (VLM 분류, 노트 추출, 영역 세분화, 리비전 비교) |

---

## 빠른 시작

```bash
# Docker로 실행
docker-compose up -d

# 또는 개발 모드
cd backend && uvicorn api_server:app --port 5020
cd frontend && npm run dev
```

---

## 프로젝트 구조

```
blueprint-ai-bom/
├── backend/                      # FastAPI 백엔드
│   ├── api_server.py             # 메인 서버
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── schemas/                  # Pydantic 모델 (13개)
│   │   ├── session.py
│   │   ├── detection.py
│   │   ├── bom.py
│   │   ├── dimension.py
│   │   ├── gdt.py                # GD&T 파싱
│   │   ├── region.py             # 영역 분할
│   │   ├── relation.py           # 치수-심볼 관계
│   │   ├── verification.py       # 검증 스키마 (v8.0)
│   │   ├── feedback.py           # Feedback 스키마 (v8.0)
│   │   └── typed_dicts.py        # TypedDict 정의
│   ├── services/                 # 비즈니스 로직 (19개)
│   │   ├── session_service.py
│   │   ├── detection_service.py  # YOLO/Detectron2 검출
│   │   ├── detectron2_service.py # Mask R-CNN 세그멘테이션 (NEW)
│   │   ├── bom_service.py
│   │   ├── dimension_service.py
│   │   ├── dimension_relation_service.py
│   │   ├── gdt_parser.py         # GD&T 파서
│   │   ├── region_segmenter.py   # 영역 분할
│   │   ├── line_detector_service.py
│   │   ├── connectivity_analyzer.py
│   │   ├── vlm_classifier.py     # VLM 분류
│   │   ├── active_learning_service.py  # 검증 큐
│   │   └── utils/pricing_utils.py
│   ├── routers/                  # API 엔드포인트 (8개)
│   │   ├── session_router.py
│   │   ├── detection_router.py
│   │   ├── bom_router.py
│   │   ├── analysis_router.py
│   │   ├── relation_router.py
│   │   ├── classification_router.py
│   │   ├── verification_router.py  # Active Learning
│   │   └── feedback_router.py      # Feedback Loop (v8.0)
│   └── tests/                    # 단위 테스트 (27개)
│
├── frontend/                     # React 19 + TypeScript
│   ├── src/
│   │   ├── pages/               # 페이지 (5개)
│   │   │   ├── HomePage.tsx
│   │   │   ├── DetectionPage.tsx
│   │   │   ├── VerificationPage.tsx
│   │   │   ├── WorkflowPage.tsx  # 메인 워크플로우
│   │   │   └── BOMPage.tsx
│   │   ├── components/          # 컴포넌트 (20+개)
│   │   │   ├── VerificationQueue.tsx  # Active Learning UI
│   │   │   ├── DrawingCanvas.tsx
│   │   │   ├── DetectionCard.tsx
│   │   │   ├── DimensionList.tsx
│   │   │   ├── GDTEditor.tsx
│   │   │   ├── RegionEditor.tsx
│   │   │   ├── RelationOverlay.tsx
│   │   │   └── ...
│   │   ├── lib/api.ts           # API 클라이언트
│   │   └── store/               # Zustand 스토어
│   ├── Dockerfile
│   └── nginx.conf
│
├── scripts/                      # 유틸리티 스크립트
│   └── export/
│       └── export_package.py     # 납품 패키지 생성
│
├── docs/                         # 문서
│   ├── deployment/              # 배포 가이드
│   ├── features/                # 기능 문서
│   └── migration/               # 마이그레이션 가이드
│
├── docker-compose.yml
└── README.md
```

---

## 핵심 기능

### 1. AI 심볼 검출 (YOLO v11)
- 27개 전장 부품 클래스 자동 검출
- 신뢰도 기반 필터링 (기본 0.4)
- GPU/CPU 자동 감지

### 2. OCR 치수 인식 (eDOCr2)
- 한국어 치수 텍스트 인식
- mm, cm, inch 등 단위 파싱
- 공차 표기 인식 (±0.1mm)

### 3. GD&T 분석
- 기하공차 파싱 (⌀, ⊥, ∥, ⊙, ⌖)
- 데이텀 검출 (A, B, C)
- 공차값 추출

### 4. Active Learning 검증 큐
| 우선순위 | 조건 | 설명 |
|---------|------|------|
| CRITICAL | 신뢰도 < 0.7 | 즉시 확인 필요 |
| HIGH | 심볼 연결 없음 | 연결 확인 필요 |
| MEDIUM | 신뢰도 0.7-0.9 | 검토 권장 |
| LOW | 신뢰도 ≥ 0.9 | 자동 승인 후보 |

### 5. Human-in-the-Loop 검증
- 바운딩 박스 수정 (이동, 크기 조절)
- 클래스 변경
- 승인/반려/수정 워크플로우
- 일괄 승인 기능

### 6. BOM 생성 및 내보내기
- 검증된 검출 결과 집계
- 가격 정보 자동 매칭
- Excel/CSV/JSON/PDF 내보내기

---

## API 엔드포인트

### 세션 관리
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/sessions/upload` | 이미지 업로드 |
| GET | `/sessions` | 세션 목록 |
| GET | `/sessions/{id}` | 세션 상세 |
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
| GET | `/verification/stats/{id}` | 검증 통계 |
| POST | `/verification/verify/{id}` | 단일 항목 검증 |
| POST | `/verification/auto-approve/{id}` | 자동 승인 |
| POST | `/verification/bulk-approve/{id}` | 일괄 승인 |

### BOM
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/bom/generate/{id}` | BOM 생성 |
| GET | `/bom/export/{id}/{format}` | 내보내기 (excel/csv/json/pdf) |

---

## 27개 검출 클래스

| ID | 클래스명 | 한글명 |
|----|---------|--------|
| 0 | ARRESTER | 피뢰기 |
| 1 | BUS | 모선 |
| 2 | CT | 변류기 |
| 3 | DS | 단로기 |
| 4 | ES | 접지개폐기 |
| 5 | GCB | 가스차단기 |
| 6 | GPT | 접지형계기용변압기 |
| 7 | GS | 가스구간개폐기 |
| 8 | LBS | 부하개폐기 |
| 9 | MOF | 계기용변성기 |
| 10 | OCB | 유입차단기 |
| 11 | PT | 계기용변압기 |
| 12 | RECLOSER | 리클로저 |
| 13 | SC | 직렬콘덴서 |
| 14 | SHUNT_REACTOR | 분로리액터 |
| 15 | SS | 정류기 |
| 16 | TC | 탭절환기 |
| 17 | TR | 변압기 |
| 18 | TVSS | 서지흡수기 |
| 19 | VCB | 진공차단기 |
| 20 | 고장점표시기 | 고장점표시기 |
| 21 | 단로기_1P | 단로기(1P) |
| 22 | 부하개폐기_1P | 부하개폐기(1P) |
| 23 | 접지 | 접지 |
| 24 | 차단기 | 차단기 |
| 25 | 퓨즈 | 퓨즈 |
| 26 | 피뢰기 | 피뢰기 |

---

## 테스트

```bash
# 백엔드 테스트
cd backend

# 전체 테스트 (59개)
python -m pytest tests/ -v

# 장기 로드맵 단위 테스트 (19개)
python -m pytest tests/test_revision_comparator.py -v

# 장기 로드맵 API 테스트 (13개)
python -m pytest tests/test_longterm_api.py -v

# 프론트엔드 빌드
cd frontend
npm run build
```

### 테스트 현황 (v10.3)

| 카테고리 | 테스트 수 | 상태 |
|----------|----------|------|
| BOM Service | 9개 | ✅ 통과 |
| Detection Service | 7개 | ✅ 통과 |
| Pricing Utils | 11개 | ✅ 통과 |
| Revision Comparator | 19개 | ✅ 통과 |
| Longterm API | 13개 | ✅ 통과 (12 통과 + 1 스킵) |
| **총계** | **59개** | **✅ 통과** |

---

## 납품 패키지 생성

```bash
python scripts/export/export_package.py --customer "고객명" --output ./export
```

생성 내용:
- `config/` - 설정 파일
- `frontend/` - React 빌드
- `backend/` - FastAPI 서버
- `docker/` - Docker Compose 설정
- `scripts/` - 설치/시작/중지 스크립트
- `docs/` - 설치 및 사용 매뉴얼

---

## 성능 지표

| 항목 | 값 |
|------|-----|
| 검출 정확도 | 96% (YOLOv11) |
| 처리 속도 (GPU) | ~2-3초/페이지 |
| 처리 속도 (CPU) | ~8-10초/페이지 |
| 단위 테스트 | 59개 통과 |
| 프론트엔드 빌드 | 451 kB |

### 장기 로드맵 기능 성능

| 기능 | 처리 시간 | 정확도 |
|------|----------|--------|
| VLM 자동 분류 | ~2초 | 88% |
| 영역 세분화 | ~0.5초 | 90% |
| 노트 추출 | ~2초 | 85% |
| 리비전 비교 | ~1.5초 | 92% |

---

## 버전 히스토리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| **v10.3** | **2025-12-27** | **장기 로드맵 전체 완료**: 리비전 비교 (SSIM + 데이터 + VLM), 4/4 기능 완료, 테스트 59개 |
| v10.2 | 2025-12-27 | 영역 세분화 완전 구현: 휴리스틱 + VLM 하이브리드, 11개 영역 타입 |
| v10.1 | 2025-12-27 | 노트 추출 완전 구현: GPT-4o-mini LLM + 정규식 폴백 |
| v10.0 | 2025-12-27 | VLM 자동 분류 완전 구현: OpenAI/Anthropic/로컬 멀티 프로바이더 |
| v9.0 | 2025-12-24 | 장기 로드맵 API 스텁: 영역 세분화, 노트 추출, 리비전 비교, VLM 분류 |
| v8.1 | 2025-12-24 | 18개 기능 체크박스 툴팁 추가, UI 개선 |
| v8.0 | 2025-12-23 | Feedback Loop Pipeline, YOLO 재학습 데이터셋 내보내기, 온프레미스 배포 |
| v5.0 | 2025-12-23 | Active Learning 검증 큐, TypedDict 타입 안전성 |
| v4.0 | 2025-12-19 | GD&T 파서, 영역 분할, 치수-심볼 관계 |
| v3.0 | 2025-12-14 | AX POC 통합, React 전환 완료 |
| v2.0 | 2025-09-30 | 모듈러 아키텍처 (Streamlit) |
| v1.0 | 2025-09-01 | 초기 버전 |

---

## 관련 문서

| 문서 | 위치 |
|------|------|
| 기능 문서 | `docs/features/` |
| 배포 가이드 | `docs/deployment/` |
| AX POC 가이드 | `../CLAUDE.md` |
| 작업 추적 | `../.todos/README.md` |

---

**Powered by AX POC BlueprintFlow + YOLOv11 + eDOCr2**
