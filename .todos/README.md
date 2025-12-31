# .todos - 작업 추적

> **최종 업데이트**: 2025-12-31 | **버전**: v20.0

---

## 현재 상태

```
시스템: AX POC v20.0
디자인 패턴: 100/100점 (목표 달성)
테스트: 329개 통과 (gateway 188, web-ui 141)
API: 18/18 healthy
최근 완료: 디자인 패턴 100점 달성 (P0-P2 리팩토링 완료)
```

---

## 핵심 변경사항 요약 (2025-12-31)

### 파일 분리 완료 (9개)

| 파일 | 이전 | 이후 | 분리 위치 |
|------|------|------|----------|
| gateway-api/api_server.py | 2,044줄 | 335줄 | routers/ (6개) |
| gateway-api/admin_router.py | 570줄 | 332줄 | docker, results, gpu_config |
| bwms_rules.py | 1,031줄 | 89줄 | bwms/ (8개) |
| api_server_edocr_v1.py | 1,068줄 | 97줄 | edocr_v1/ |
| region_extractor.py | 1,082줄 | 57줄 | region/ (5개) |
| Guide.tsx | 1,235줄 | 151줄 | guide/ |
| APIDetail.tsx | 1,197줄 | 248줄 | api-detail/ |
| NodePalette.tsx | 1,024줄 | 189줄 | node-palette/ |
| pid_features_router.py | 1,101줄 | 118줄 | pid_features/ (6개) |

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
| `2025-12-31_consistency_and_remaining_work.md` | **일관성 검토 및 남은 작업** | 🆕 신규 |
| `2025-12-31_architecture_discussion.md` | Builder vs AI BOM 아키텍처 논의 | 논의 필요 |
| `2025-12-31_post_commit_analysis.md` | 커밋 분석 후 일관성 작업 | ✅ 완료 |
| `2025-12-29_project_architecture_overview.md` | 프로젝트 아키텍처 개요 | 참조용 |
| `2025-12-29_next_steps_recommendation.md` | 향후 작업 권장사항 | ✅ MVP 완료 |
| `REMAINING_WORK_PLAN.md` | 전체 작업 계획 | ✅ v20.0 업데이트 |

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

## 다음 단계 (우선순위별)

### P1 - 단기 (1주)

1. **GTComparisonSection.tsx** 구현 - gt_comparison 기능 UI
2. **IndustryEquipmentSection.tsx** 구현 - industry_equipment_detection 기능 UI
3. 해당 백엔드 API 스텁 생성

### P2 - 중기 (2주)

1. 누락된 라우터 테스트 작성 (process, quote, download)
2. 분리된 모듈 테스트 작성 (bwms, edocr_v1, region)
3. SSOT 패턴 확장 (blueprint-ai-bom constants 분리)

### P3 - 장기 (1개월)

1. OpenAPI 문서 예시 추가
2. 성능 벤치마크 문서화
3. 아키텍처 다이어그램 업데이트

### 외부 의존

1. **TECHCROSS 1-4 Deviation List** - POR 문서 확보 시 진행

---

## 빠른 시작

```bash
# 일관성 검토 및 남은 작업
cat .todos/2025-12-31_consistency_and_remaining_work.md

# 프로젝트 아키텍처 개요
cat .todos/2025-12-29_project_architecture_overview.md

# TECHCROSS 요구사항 분석
cat .todos/TECHCROSS_요구사항_분석_20251229.md
```

---

## 디자인 패턴 점수

| 영역 | 점수 |
|------|------|
| 모듈 & 책임 분리 | 25/25 ✅ |
| 파일 크기 LLM 친화성 | 25/25 ✅ |
| 설정 관리 SSOT | 15/15 ✅ |
| 공통 패턴 | 15/15 ✅ |
| 테스트 & 문서 | 10/10 ✅ |
| 코드 중복 제거 | 10/10 ✅ |
| **총점** | **100/100** |

---

**Managed By**: Claude Code (Opus 4.5)
