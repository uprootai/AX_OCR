# 백로그 (향후 작업)

> 마지막 업데이트: 2026-01-24
> 미래 작업 및 참조 문서

---

## 📊 현재 상태 요약

| 항목 | 값 |
|------|-----|
| **테스트** | 693개 (web-ui 304, gateway 389) |
| **빌드** | ✅ 15.30s |
| **ESLint** | 0 errors, 1 warning |
| **노드 정의** | 31개 |
| **API 서비스** | 21개 |

---

## ✅ 완료: Self-contained Export 프론트엔드 추가

> **완료일**: 2026-01-24
> **담당 파일**: `blueprint-ai-bom/backend/services/self_contained_export_service.py`

### 구현 완료 내역

| # | 작업 | 상태 |
|---|------|------|
| 1 | `SERVICE_PORT_MAP`에 프론트엔드 3000 추가 | ✅ |
| 2 | `BACKEND_TO_FRONTEND_MAP` 추가 (자동 포함) | ✅ |
| 3 | `FRONTEND_SERVICES` 집합 추가 | ✅ |
| 4 | `detect_required_services()` 프론트엔드 자동 포함 | ✅ |
| 5 | `generate_docker_compose()` 프론트엔드 처리 (포트 80) | ✅ |
| 6 | Import 스크립트 UI URL 강조 | ✅ |
| 7 | README.md Quick Start 섹션 추가 | ✅ |
| 8 | 로직 테스트 검증 | ✅ |

### 결과

- 백엔드 포함 시 프론트엔드 **자동 포함**
- Import 후 `http://localhost:13000` (offset=10000) 으로 UI 접속 가능
- Import 스크립트에서 UI URL 강조 표시

---

## 📋 P1: web-ui (BlueprintFlow) Export 검토

**우선순위**: P1
**예상 작업량**: 4시간

### 검토 필요 사항

| 질문 | 현재 | 결정 필요 |
|------|------|----------|
| web-ui도 Export 필요? | ❌ 미포함 | 검토 필요 |
| 고객이 워크플로우 편집 필요? | N/A | 요구사항 확인 |
| web-ui 없이 BOM만 사용 가능? | ✅ 가능 | - |

### 선택지

1. **web-ui 미포함 (현재)**
   - 장점: 패키지 크기 작음
   - 단점: 고객이 워크플로우 수정 불가

2. **web-ui 포함**
   - 장점: 고객이 워크플로우 수정 가능
   - 단점: 패키지 크기 증가, 복잡도 증가

3. **옵션으로 제공**
   - `include_web_ui: bool` 파라미터 추가
   - 고객 요구에 따라 선택

---

## 📋 P2: 기타 향후 작업

### 1. 시각화 기능 확장

**우선순위**: P3
**진행 상태**: 일부 완료

| 기능 | 상태 |
|------|------|
| ConfidenceDistributionChart | ✅ 완료 |
| 인터랙티브 심볼 선택 | ⏳ 계획됨 |
| 레이어 토글 | ⏳ 계획됨 |

### 2. 테스트 커버리지 확대

**우선순위**: P2

| 영역 | 현재 | 목표 |
|------|------|------|
| Gateway API | 389개 | 400개+ |
| Web-UI | 304개 | 350개+ |
| E2E | ~50개 | 100개+ |

### 3. Dimension Parser 강화

**우선순위**: P2

- 복합 치수 (예: `Φ50±0.05`)
- 공차 범위 파싱
- 단위 변환 (mm ↔ inch)

### 4. 고객 프로파일 확장

**우선순위**: P2

| 고객 | 현재 | 추가 필요 |
|------|------|----------|
| DSE Bearing | ✅ 완료 | - |
| DOOSAN | 기본 | 상세 설정 |
| PANASIA | 기본 | 상세 설정 |

---

## ✅ 완료된 백로그 항목

| 작업 | 완료일 | 상세 |
|------|--------|------|
| **Self-contained Export 프론트엔드** | 2026-01-24 | Phase 2I 완료, UI URL 자동 포함 |
| DSE Bearing 100점 | 2026-01-22 | 6 Phase 전체 완료 |
| Blueprint AI BOM Phase 2 | 2026-01-24 | 2A~2I 완료 |
| Self-contained Export (백엔드) | 2026-01-24 | 포트 오프셋 기능 포함 |
| MODEL_DEFAULTS 패턴 확장 | 2026-01-19 | 19개 API 적용 |
| Toast 마이그레이션 | 2026-01-16 | 12개 파일 완료 |

---

## 📅 로드맵

| 분기 | 작업 | 우선순위 | 상태 |
|------|------|----------|------|
| Q1 2026 | DSE Bearing 100점 | P1 | ✅ 완료 |
| Q1 2026 | Blueprint AI BOM Phase 2 | P1 | ✅ 완료 |
| Q1 2026 | Self-contained 프론트엔드 | P0 | ✅ 완료 |
| Q2 2026 | 시각화 기능 확장 | P3 | ⏳ 계획됨 |
| Q2 2026 | Gateway 서비스 분리 | P3 | ⏳ 계획됨 |

---

## 📚 참조 문서

| 문서 | 위치 |
|------|------|
| 새 API 추가 가이드 | `.claude/skills/api-creation-guide.md` |
| 모듈화 가이드 | `.claude/skills/modularization-guide.md` |
| Phase 2 아키텍처 | `.todo/archive/BLUEPRINT_ARCHITECTURE_V2.md` |
| DSE Bearing 계획 | `.todo/archive/DSE_BEARING_100_PLAN.md` |

---

*마지막 업데이트: 2026-01-24*
