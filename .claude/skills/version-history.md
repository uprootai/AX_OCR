# 버전 히스토리 및 서브시스템 레퍼런스

---

## 버전 히스토리

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| **23.0** | **2025-12-31** | **코드 품질 개선**: ESLint 에러 0개, 505개 테스트 통과 |
| 22.0 | 2025-12-31 | BlueprintFlow 5개 신규 노드 (28개 총) |
| 21.0 | 2025-12-31 | R&D 디렉토리: SOTA 논문 35개 수집 |
| 20.0 | 2025-12-31 | 디자인 패턴 100점 달성 |
| 19.0 | 2025-12-31 | P0~P2 리팩토링 완료 (9개 파일) |
| 18.0 | 2025-12-30 | TECHCROSS Human-in-the-Loop 워크플로우 |
| 17.0 | 2025-12-29 | Design Checker v1.0 리팩토링 |
| 16.0 | 2025-12-28 | Line Detector v1.1 |
| 15.0 | 2025-12-27 | Blueprint AI BOM v10.3 장기 로드맵 완료 |
| 14.0 | 2025-12-26 | GPU Override 시스템 |
| 13.0 | 2025-12-26 | 모듈화 리팩토링 |
| 12.0 | 2025-12-24 | Blueprint AI BOM v9.0 |
| 11.0 | 2025-12-24 | 18개 API healthy |
| 10.0 | 2025-12-10 | 웹 기반 GPU/메모리 설정 |
| 9.0 | 2025-12-09 | 동적 리소스 로딩 시스템 |
| 8.0 | 2025-12-06 | P&ID 분석 시스템 |
| 7.0 | 2025-12-03 | API 스펙 표준화 시스템 |
| 6.0 | 2025-12-03 | 테스트 체계 구축 |
| 5.0 | 2025-12-01 | 5개 신규 API 추가 |
| 4.0 | 2025-11-22 | TextInput 노드, 병렬 실행 |

---

## Blueprint AI BOM (v10.5)

**Human-in-the-Loop 도면 BOM 생성 시스템**

### 핵심 기능

| 기능 | 설명 |
|------|------|
| 심볼 검출 | YOLO v11 기반 27개 클래스 |
| 치수 OCR | eDOCr2 한국어 치수 인식 |
| GD&T 파싱 | 기하공차/데이텀 파싱 |
| Active Learning | 신뢰도 기반 검증 큐 |
| Feedback Loop | YOLO 재학습 데이터셋 내보내기 |

### 장기 로드맵 (v10.3 전체 완료)

| 기능 | 상태 | 구현 |
|------|------|------|
| VLM 분류 | 완료 | GPT-4o-mini 멀티 프로바이더 |
| 노트 추출 | 완료 | LLM + 정규식 폴백 |
| 영역 세분화 | 완료 | 휴리스틱 + VLM 하이브리드 |
| 리비전 비교 | 완료 | SSIM + 데이터 + VLM |

### TECHCROSS 워크플로우 (v10.5)

| 요구사항 | 기능 | 상태 |
|----------|------|------|
| 1-1 | BWMS Checklist | 완료 |
| 1-2 | Valve Signal List | 완료 |
| 1-3 | Equipment List | 완료 |
| 1-4 | Deviation List | 계획됨 |

### TECHCROSS 엔드포인트 (10개)

| 그룹 | 엔드포인트 | 설명 |
|------|------------|------|
| Valve Signal | `POST /{session_id}/valve-signal/detect` | 밸브 신호 검출 |
| Equipment | `POST /{session_id}/equipment/detect` | 장비 검출 |
| Checklist | `POST /{session_id}/checklist/check` | 체크리스트 검증 |
| Verification | `GET /{session_id}/verify/queue` | 검증 큐 조회 |
| Verification | `POST /{session_id}/verify` | 단일 항목 검증 |
| Verification | `POST /{session_id}/verify/bulk` | 대량 검증 |
| Export | `POST /{session_id}/export` | Excel 내보내기 |
| Summary | `GET /{session_id}/summary` | 워크플로우 요약 |

### 테스트 현황

| 테스트 | 수량 | 상태 |
|--------|------|------|
| 단위 테스트 | 46개 | 통과 |
| 장기 로드맵 테스트 | 32개 | 통과 |
| **총계** | **59개** | **통과** |

**문서**: [blueprint-ai-bom/docs/](blueprint-ai-bom/docs/README.md)

---

## Design Checker API (v1.0)

**P&ID 도면 설계 오류 검출 및 규정 검증 API**

### 아키텍처

```
models/design-checker-api/
├── api_server.py       (167줄)  # FastAPI 앱
├── schemas.py          (81줄)   # Pydantic 모델
├── constants.py        (219줄)  # 규칙 정의 (20개)
├── checker.py          (354줄)  # 설계 검증 로직
├── bwms_rules.py       (822줄)  # BWMS 규칙 (7+동적)
├── rule_loader.py      (260줄)  # YAML 기반 규칙 관리
├── excel_parser.py     (210줄)  # 체크리스트 Excel 파싱
└── routers/
    ├── check_router.py    (220줄)
    ├── rules_router.py    (295줄)
    └── checklist_router.py (311줄)
```

### 핵심 기능

| 기능 | 설명 |
|------|------|
| 설계 검증 | 20개 규칙 (connectivity, symbol, labeling 등) |
| BWMS 검증 | 7개 내장 규칙 + 동적 규칙 |
| 규칙 관리 | Excel 업로드, YAML 저장, 프로필 관리 |
| 제품 필터 | ALL / ECS / HYCHLOR 타입별 규칙 |

### 엔드포인트 (20개)

| 그룹 | 수량 | 주요 엔드포인트 |
|------|------|----------------|
| Health | 3개 | /health, /api/v1/info |
| Check | 3개 | /api/v1/check, /api/v1/check/bwms |
| Rules | 7개 | /api/v1/rules, /disable, /enable |
| Checklist | 5개 | /upload, /template, /current |
| Profile | 2개 | /activate, /deactivate |

### 지원 표준

| 표준 | 설명 |
|------|------|
| **ISO 10628** | P&ID 표준 |
| **ISA 5.1** | 계기 심볼 표준 |
| **TECHCROSS BWMS** | 선박평형수처리시스템 규정 |

### 규칙 파일 구조

```
config/
├── common/          # 공통 규칙
├── ecs/             # ECS 제품 전용
├── hychlor/         # HYCHLOR 제품 전용
└── custom/          # 사용자 정의
```

**문서**: [docs/api/design-checker/](docs/api/design-checker/)

---

## PID Composer API (v1.0)

**P&ID 도면 SVG 오버레이 시각화 API**

### 핵심 기능

| 기능 | 설명 |
|------|------|
| SVG 생성 | YOLO 검출 결과 → SVG 오버레이 |
| 레이어 분리 | 심볼, 텍스트, 라인 레이어 |
| 인터랙티브 | 클릭 가능한 심볼 영역 |
| 스타일링 | CSS 기반 색상/선 두께 커스터마이징 |

### 엔드포인트

| 엔드포인트 | 설명 |
|------------|------|
| `POST /api/v1/compose` | YOLO 결과 → SVG 생성 |
| `GET /api/v1/layers` | 레이어 목록 조회 |
| `POST /api/v1/export` | PNG/PDF 내보내기 |

### 아키텍처

```
models/pid-composer-api/
├── api_server.py       # FastAPI 앱
├── services/
│   └── svg_generator.py  # SVG 생성 로직
└── tests/
    └── test_svg.py       # 단위 테스트
```

**포트**: 5021
