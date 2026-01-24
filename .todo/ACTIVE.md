# 진행 중인 작업

> **마지막 업데이트**: 2026-01-25
> **현재 활성화된 작업 목록**

---

## 📊 프로젝트 상태 (2026-01-24 검증)

| 항목 | 결과 | 상세 |
|------|------|------|
| **테스트** | ✅ **729개** | web-ui 304, gateway **425** |
| **빌드** | ✅ 15.30s | TypeScript 오류 0개 |
| **ESLint** | ✅ 0 errors | 1 warning (minor) |
| **노드 정의** | ✅ **31개** | DSE Bearing 노드 포함 |
| **API 스펙** | ✅ **27개** | dsebearing.yaml 추가 |

---

## ✅ 완료: Self-contained Export 프론트엔드 추가 (Phase 2I)

> 완료일: 2026-01-24

### 구현 내용

백엔드가 포함되면 프론트엔드도 **자동으로 포함**되도록 구현 완료.

```python
# services/self_contained_export_service.py - 구현 완료
BACKEND_TO_FRONTEND_MAP = {
    "blueprint-ai-bom-backend": "blueprint-ai-bom-frontend",
}

SERVICE_PORT_MAP = {
    "blueprint-ai-bom-backend": 5020,
    "blueprint-ai-bom-frontend": 3000,  # ✅ 추가됨
}
```

### 완료 작업

| 작업 | 상태 |
|------|------|
| `SERVICE_PORT_MAP`에 프론트엔드 3000 추가 | ✅ 완료 |
| `BACKEND_TO_FRONTEND_MAP` 추가 (백엔드→프론트엔드 자동 포함) | ✅ 완료 |
| `FRONTEND_SERVICES` 집합 추가 (docker-compose 특별 처리) | ✅ 완료 |
| `detect_required_services()`에서 프론트엔드 자동 포함 | ✅ 완료 |
| `generate_docker_compose()`에서 프론트엔드 포트 80 매핑 | ✅ 완료 |
| Import 스크립트에 UI URL 강조 표시 | ✅ 완료 |
| README.md에 Quick Start 및 프론트엔드 섹션 추가 | ✅ 완료 |
| 로직 테스트 검증 | ✅ 완료 |

### 포트 매핑 예시 (port_offset=10000)

| 서비스 | 원본 | Import |
|--------|------|--------|
| blueprint-ai-bom-frontend | 3000 | **13000** |
| blueprint-ai-bom-backend | 5020 | 15020 |
| yolo-api | 5005 | 15005 |
| gateway-api | 8000 | 18000 |

### Import 스크립트 출력 예시

```
==========================================
  UI 접속 URL:
==========================================
  ★ http://localhost:13000

API endpoints:
  - imported-blueprint-ai-bom-backend: http://localhost:15020
  ...
```

---

## 📋 마지막 커밋 대비 변경 사항 요약

### 변경된 파일 (24개, +2,743줄)

#### 1. Blueprint AI BOM Backend (핵심 변경)

| 파일 | 변경 내용 |
|------|----------|
| `api_server.py` | Phase 2 라우터 등록 (project, template, export) |
| `session_router.py` | +861줄 - 워크플로우 세션, 이미지 관리, ZIP 업로드 API |
| `session_service.py` | +428줄 - create_locked_session, 이미지 CRUD, 진행률 계산 |
| `session.py` | +110줄 - ImageReviewStatus, SessionImage, SessionImageProgress |

#### 2. Blueprint AI BOM Frontend

| 파일 | 변경 내용 |
|------|----------|
| `App.tsx` | /projects, /customer 라우트 추가 |
| `WorkflowPage.tsx` | 이미지 개수 표시, onImagesAdded 핸들러 |
| `WorkflowSidebar.tsx` | +210줄 - 이미지 섹션, ZIP 업로드, 드래그앤드롭 |
| `types/index.ts` | +47줄 - Workflow, ImageReview 타입 |

#### 3. Web-UI (BlueprintFlow)

| 파일 | 변경 내용 |
|------|----------|
| `api.ts` | +228줄 - templateApi, workflowSessionApi |
| `BlueprintFlowBuilder.tsx` | Save/Load Template 버튼 추가 |
| `BlueprintFlowTemplates.tsx` | Deploy 버튼 추가 |
| `ExecutionStatusPanel.tsx` | 실행 상태 패널 개선 |

#### 4. YOLO API

| 파일 | 변경 내용 |
|------|----------|
| `model_registry.yaml` | +36줄 - Panasia 모델 등록 |
| `detection_router.py` | 모델 선택 로직 개선 |

### 새로 추가된 파일 (24개)

#### Backend 신규

| 파일 | 용도 |
|------|------|
| `routers/export_router.py` | Export API (Phase 2E) |
| `routers/project_router.py` | 프로젝트 관리 API |
| `routers/template_router.py` | 템플릿 관리 API |
| `schemas/export.py` | Export 스키마 (SelfContained 포함) |
| `schemas/project.py` | 프로젝트 스키마 |
| `schemas/template.py` | 템플릿 스키마 |
| `schemas/workflow_session.py` | 워크플로우 세션 스키마 (LockLevel 등) |
| `services/export_service.py` | 기본 Export 서비스 |
| `services/self_contained_export_service.py` | Docker 이미지 포함 Export ⭐ |
| `services/project_service.py` | 프로젝트 서비스 |
| `services/template_service.py` | 템플릿 서비스 |

#### Frontend 신규

| 파일 | 용도 |
|------|------|
| `pages/customer/` | 고객용 UI (Phase 2F) |
| `pages/project/` | 프로젝트 관리 UI (Phase 2D) |
| `components/ImageReviewCard.tsx` | 이미지 검토 카드 |
| `components/ImageReviewProgressBar.tsx` | 진행률 바 |
| `sections/ImageReviewSection.tsx` | 이미지 검토 섹션 |
| `DeployTemplateModal.tsx` | 템플릿 배포 모달 |
| `LoadTemplateModal.tsx` | 템플릿 로드 모달 |
| `SaveTemplateModal.tsx` | 템플릿 저장 모달 |

---

## ✅ 완료: Blueprint AI BOM Phase 2

**아키텍처 문서**: `archive/BLUEPRINT_ARCHITECTURE_V2.md` ⭐

### 핵심 개념

```
Template ──▶ Project ──▶ Session ──▶ Exported Session
(분석방법)    (고객+GT)   (다중이미지)   (고객 전달)
```

### Phase 2 완료 현황

| Phase | 작업 | 상태 |
|-------|------|------|
| **2A** | Template/Project 백엔드 | ✅ 완료 |
| **2B** | Save/Load Template | ✅ 완료 |
| **2C** | 이미지별 Human-in-the-Loop | ✅ 완료 |
| **2D** | Project 관리 UI | ✅ 완료 |
| **2E** | Export Session | ✅ 완료 |
| **2F** | Self-contained Export (Docker) | ✅ 완료 |
| **2G** | BlueprintFlow → BOM 연결 | ✅ 완료 |
| **2H** | 사이드바 이미지 관리 | ✅ 완료 |
| **2I** | Self-contained 프론트엔드 추가 | ✅ **완료** |

### Self-contained Export 현재 기능

```bash
# 현재 동작 (백엔드 + 프론트엔드)
POST /export/sessions/{id}/self-contained
→ ZIP 패키지 생성
  ├── manifest.json (port_offset, container_prefix)
  ├── session.json
  ├── README.md (Quick Start, UI URL 포함)
  ├── docker/
  │   ├── docker-compose.yml (포트 오프셋 적용)
  │   └── images/*.tar.gz
  └── scripts/
      ├── import.sh (UI URL 강조 표시)
      └── import.ps1

# 포트 매핑 예시 (offset=10000)
bom-frontend: 3000 → 13000 ★ UI 접속 URL
bom-backend:  5020 → 15020
yolo-api:     5005 → 15005
gateway-api:  8000 → 18000
```

---

## ✅ 완료: DSE Bearing 100점

**상세 계획**: `archive/DSE_BEARING_100_PLAN.md`

| Phase | 작업 | 상태 |
|-------|------|------|
| P0 Phase 1 | Title Block Parser | ✅ 완료 |
| P0 Phase 2 | Parts List 강화 | ✅ 완료 |
| P1 Phase 3 | 복합 치수 파서 | ✅ 완료 |
| P1 Phase 4 | BOM 자동 매칭 | ✅ 완료 |
| P2 Phase 5 | 견적 자동화 | ✅ 완료 |
| P2 Phase 6 | 통합 파이프라인 | ✅ 완료 |

---

## 📌 기타 작업

| 우선순위 | 작업 | 상태 |
|----------|------|------|
| ~~P0~~ | ~~Self-contained 프론트엔드 추가~~ | ✅ **완료** |
| ~~P1~~ | ~~web-ui(5173) Export 필요 여부 검토~~ | ✅ **완료** (미포함 결정) |
| ~~P2~~ | ~~Dimension Parser 강화 (복합 치수)~~ | ✅ **완료** |
| ~~P2~~ | ~~고객 프로파일 확장~~ | ✅ **완료** (8개 고객) |
| ~~P2~~ | ~~Gateway 테스트 400개+~~ | ✅ **완료** (425개 통과) |
| P3 | 시각화 기능 확장 | ⏳ 예정 |

---

## 🔴 다음 작업: 패턴 동기화

> **상세 문서**: `.todo/SYNC_PATTERNS.md`

### P0: Dimension Parser 동기화 (즉시)

| 소스 | 대상 | 상태 |
|------|------|------|
| `dimensionparser_executor.py` (21개 패턴) | `dimension_service.py` (3개) | ❌ 불일치 |

**누락 패턴**: 직경+공차, 역순 비대칭, 단방향 공차, 나사, 각도, 표면거칠기

### P1: 고객-모델 연동

| 작업 | 상태 |
|------|------|
| PANASIA 가격 데이터 추가 | ⏳ |
| 고객별 YOLO 모델 자동 선택 | ⏳ |

---

## 📂 TODO 파일 구조

```
.todo/
├── ACTIVE.md         # 현재 파일 (활성 작업)
├── BACKLOG.md        # 향후 작업 목록
├── SYNC_PATTERNS.md  # 패턴 동기화 추적 ⭐ NEW
├── COMPLETED.md      # 완료 아카이브
└── archive/          # 상세 문서
    └── BLUEPRINT_ARCHITECTURE_V2.md
```

---

*마지막 업데이트: 2026-01-24*
