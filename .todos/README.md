# .todos - 작업 추적

> **최종 업데이트**: 2025-12-31 | **버전**: v23.0

---

## 현재 상태

```
시스템: AX POC v23.0
디자인 패턴: 100/100점 (목표 달성)
테스트: 505개 통과 (gateway 364, web-ui 141)
BlueprintFlow: 28개 노드
ESLint: 0 에러, 3 경고
API: 19/19 healthy
최근 완료: ESLint 에러 0개 달성, Executor 테스트 126개 추가
```

---

## 핵심 성과 (2025-12-31)

### 디자인 패턴 100점 달성

| 영역 | 점수 |
|------|------|
| 모듈 & 책임 분리 | 25/25 |
| 파일 크기 LLM 친화성 | 25/25 |
| 설정 관리 SSOT | 15/15 |
| 공통 패턴 | 15/15 |
| 테스트 & 문서 | 10/10 |
| 코드 중복 제거 | 10/10 |
| **총점** | **100/100** |

### 파일 분리 완료 (9개)

| 파일 | 이전 | 이후 | 분리 위치 |
|------|------|------|----------|
| gateway-api/api_server.py | 2,044줄 | 335줄 | routers/ (8개) |
| bwms_rules.py | 1,031줄 | 89줄 | bwms/ (8개) |
| api_server_edocr_v1.py | 1,068줄 | 97줄 | edocr_v1/ |
| region_extractor.py | 1,082줄 | 57줄 | region/ (5개) |
| Guide.tsx | 1,235줄 | 151줄 | guide/ |
| APIDetail.tsx | 1,197줄 | 248줄 | api-detail/ |
| NodePalette.tsx | 1,024줄 | 189줄 | node-palette/ |
| pid_features_router.py | 1,101줄 | 118줄 | pid_features/ (6개) |
| lib/api.ts | 1,806줄 | 401줄 | 14개 파일 |

### 신규 SSOT 및 유틸리티

- `gateway-api/constants/` - DOCKER_SERVICE_MAPPING, GPU_ENABLED_SERVICES
- `gateway-api/utils/subprocess_utils.py` - 공통 subprocess 함수

---

## TECHCROSS POC 현황

### 요구사항 완료 현황

| 요구사항 | 기능 | 상태 | 구현 위치 |
|----------|------|------|----------|
| **1-1** | BWMS Checklist (60개 항목) | ✅ 완료 | `pid_features/checklist_router.py` |
| **1-2** | Valve Signal List | ✅ 완료 | `pid_features/valve_router.py` |
| **1-3** | Equipment List | ✅ 완료 | `pid_features/equipment_router.py` |
| **1-4** | Deviation List | ⏳ 보류 | POR 문서 필요 |

### 블로커

| 항목 | 상태 | 비고 |
|------|------|------|
| POR 원본 문서 | ⏳ 대기 | 1-4 Deviation List 구현에 필요 |

---

## 파일 목록

### 활성 문서

| 파일 | 용도 | 상태 |
|------|------|------|
| `2025-12-31_project_architecture_overview.md` | 프로젝트 아키텍처 개요 | ✅ 최신 |
| `2025-12-31_consistency_and_remaining_work.md` | 일관성 검토 및 남은 작업 | ✅ 최신 |
| `2025-12-31_playwright_e2e_testing.md` | E2E 테스트 결과 | ✅ 완료 |
| `2025-12-31_post_commit_analysis.md` | 커밋 분석 | ✅ 완료 |
| `REMAINING_WORK_PLAN.md` | 전체 작업 계획 | ✅ 업데이트 |

### TECHCROSS 관련

| 파일 | 용도 |
|------|------|
| `TECHCROSS_요구사항_분석_20251229.md` | 요구사항 심층 분석 |
| `TECHCROSS_개발_로드맵.md` | 전체 개발 계획 |
| `TECHCROSS_Phase1_즉시개발.md` | Phase 1 구현 가이드 |

### 아카이브 (archive/)

오래되었거나 완료된 문서들:
- `2025-12-14_export_architecture.md`
- `2025-12-19_blueprint_ai_bom_expansion_proposal.md`
- `2025-12-24_*` (v8 관련)
- `2025-12-29_*_consistency_*.md` (완료된 일관성 작업)

---

## 완료된 작업 요약

### P0-P2 리팩토링 (2025-12-31)
- [x] 9개 대형 파일 모두 분리 완료
- [x] SSOT 패턴 적용 (constants/)
- [x] subprocess_utils.py 공통 함수 추출
- [x] 119개 라우터 테스트 추가
- [x] Response Model 네이밍 충돌 해결

### API 스펙 업데이트 (2025-12-31)
- [x] yolo.yaml OpenAPI 예시 추가
- [x] pidanalyzer.yaml OpenAPI 예시 추가
- [x] edocr2.yaml OpenAPI 예시 추가

### E2E 테스트 (2025-12-31)
- [x] Gateway API 헬스체크 (18개 스펙, 51개 엔드포인트)
- [x] Web-UI 기본 기능 검증
- [x] Blueprint AI BOM 워크플로우 검증

### 아키텍처 문서 (2025-12-31)
- [x] system-architecture.md v3.0 업데이트
- [x] 19개 서비스 반영
- [x] 모듈화 패턴 다이어그램 추가

---

## 외부 의존

1. **TECHCROSS 1-4 Deviation List** - POR 문서 확보 시 진행

---

## 빠른 시작

```bash
# 프로젝트 아키텍처 개요
cat .todos/2025-12-31_project_architecture_overview.md

# E2E 테스트 결과
cat .todos/2025-12-31_playwright_e2e_testing.md

# TECHCROSS 요구사항 분석
cat .todos/TECHCROSS_요구사항_분석_20251229.md
```

---

**Managed By**: Claude Code (Opus 4.5)
