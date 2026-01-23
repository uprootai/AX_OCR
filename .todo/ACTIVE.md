# 진행 중인 작업

> **마지막 업데이트**: 2026-01-22
> **현재 활성화된 작업 목록**

---

## 📊 프로젝트 상태 (2026-01-22 검증)

| 항목 | 결과 | 상세 |
|------|------|------|
| **테스트** | ✅ **693개** | web-ui 304, gateway 389 (+25 DSE) |
| **빌드** | ✅ 15.30s | TypeScript 오류 0개 |
| **ESLint** | ✅ 0 errors | 1 warning (minor) |
| **노드 정의** | ✅ **31개** | DSE Bearing 노드 포함 |
| **API 스펙** | ✅ **27개** | dsebearing.yaml 추가 |

---

## ✅ 완료: DSE Bearing 100점 달성

**상세 계획**: `archive/DSE_BEARING_100_PLAN.md`

### 목표
테이블/치수 추출 68점 → 100점 ✅ **달성**

### Phase 진행 상황

| Phase | 작업 | 기간 | 상태 |
|-------|------|------|------|
| **P0** Phase 1 | Title Block Parser | 3일 | ✅ **완료** |
| **P0** Phase 2 | Parts List 강화 | 2일 | ✅ **완료** |
| **P1** Phase 3 | 복합 치수 파서 | 2일 | ✅ **완료** (기본) |
| **P1** Phase 4 | BOM 자동 매칭 | 3일 | ✅ **완료** |
| **P2** Phase 5 | 견적 자동화 | 5일 | ✅ **완료** |
| **P2** Phase 6 | 통합 파이프라인 | 2일 | ✅ **완료** |

### 구현 내역

**API & 서비스**:
- `gateway-api/routers/dsebearing_router.py` - 전체 API 라우터
- `gateway-api/services/dsebearing_parser.py` - 도면 파싱 서비스
- `gateway-api/services/price_database.py` - 가격 DB (12개 재질)
- `gateway-api/services/customer_config.py` - 고객 설정 (DSE, DOOSAN)
- `gateway-api/services/quote_exporter.py` - Excel/PDF 출력

**BlueprintFlow**:
- `gateway-api/blueprintflow/executors/titleblock_executor.py`
- `gateway-api/blueprintflow/executors/partslist_executor.py`
- `gateway-api/blueprintflow/executors/dimensionparser_executor.py`
- `gateway-api/blueprintflow/executors/bommatcher_executor.py`
- `gateway-api/blueprintflow/executors/quotegenerator_executor.py`

**테스트**:
- `tests/unit/test_dsebearing_services.py` - 25개 단위 테스트
- `tests/e2e/test_dsebearing_pipeline.py` - E2E 파이프라인 테스트

**문서**:
- `gateway-api/api_specs/dsebearing.yaml` - 통합 API 스펙
- `apply-company/dsebearing/API_GUIDE.md` - 사용 가이드

---

## 🟡 현재 작업

| 우선순위 | 작업 | 상태 |
|----------|------|------|
| P2 | Dimension Parser 강화 (복합 치수) | ⏳ 진행 예정 |
| P2 | 고객 프로파일 확장 (DOOSAN 상세) | ⏳ 진행 예정 |
| P2 | Gateway 테스트 400개+ | ⏳ 진행 예정 |
| P3 | 시각화 기능 확장 | ⏳ 진행 예정 |

---

## 📂 TODO 파일 구조

```
.todo/
├── ACTIVE.md      # 현재 파일 (활성 작업)
├── BACKLOG.md     # 향후 작업 목록
├── COMPLETED.md   # 완료 아카이브
└── archive/       # 상세 문서
```

---

*마지막 업데이트: 2026-01-22*
