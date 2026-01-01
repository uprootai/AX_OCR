# Blueprint AI BOM - 작업 계획서

> **작성일**: 2025-12-26 | **최종 업데이트**: 2025-12-31 | **현재 버전**: v23.0

---

## 1. 현재 상태

```
    기능 구현 현황: 27/27 (100%)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✅

    시스템: AX POC v23.0
    빌드: ✅ 통과   API: 19/19 healthy
    테스트: 505개 통과 (gateway 364, web-ui 141)
    BlueprintFlow: 28개 노드
    디자인 패턴: 100/100점
    ESLint: 0 에러, 3 경고
```

---

## 2. 완료된 작업 (2025-12-31)

### BlueprintFlow 신규 노드 5개

| 노드 | 타입 | 설명 | 상태 |
|------|------|------|------|
| GT Comparison | `gtcomparison` | 검출 성능 평가 (Precision/Recall/F1) | ✅ 완료 |
| PDF Export | `pdfexport` | P&ID 분석 PDF 리포트 생성 | ✅ 완료 |
| Excel Export | `excelexport` | P&ID 분석 Excel 스프레드시트 | ✅ 완료 |
| PID Features | `pidfeatures` | TECHCROSS 통합 분석 (Valve/Equipment/Checklist) | ✅ 완료 |
| Verification Queue | `verificationqueue` | Human-in-the-Loop 검증 큐 관리 | ✅ 완료 |

### 디자인 패턴 100점 달성

| 항목 | 상태 |
|------|------|
| 9개 대형 파일 분리 | ✅ 완료 |
| SSOT 패턴 적용 (constants/) | ✅ 완료 |
| subprocess_utils.py 추출 | ✅ 완료 |
| 119개 라우터 테스트 추가 | ✅ 완료 |
| Response Model 네이밍 충돌 해결 | ✅ 완료 |

### E2E 테스트

| 항목 | 상태 |
|------|------|
| Gateway API 헬스체크 | ✅ 통과 |
| Web-UI 기본 기능 | ✅ 통과 |
| Blueprint AI BOM 워크플로우 | ✅ 통과 |

### 아키텍처 문서화

| 항목 | 상태 |
|------|------|
| system-architecture.md v3.0 | ✅ 완료 |
| 프로젝트 아키텍처 개요 | ✅ 완료 |
| OpenAPI 예시 추가 | ✅ 완료 |

---

## 3. TECHCROSS POC 현황 (v10.5)

### 고객 정보

```
┌─────────────────────────────────────────────────────────────────┐
│  회사: TECHCROSS (테크로스)                                      │
│  담당: 기본설계팀                                                │
│  제품: BWMS (Ballast Water Management System)                   │
│        - ECS: 직접 전기분해 방식                                 │
│        - HYCHLOR 2.0: 간접 전기분해 방식                        │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 1-2: MVP ✅ 완료

| 순위 | 기능 | 설명 | 상태 |
|------|------|------|------|
| 1 | P&ID 심볼/텍스트 인식 | BWMS 장비 8종, OCR | ✅ 완료 |
| 2 | Equipment List (1-3) | 장비 목록 Excel 출력 | ✅ 완료 |
| 3 | Valve Signal List (1-2) | 밸브 Signal 목록 Excel 출력 | ✅ 완료 |
| 4 | 체크리스트 검토 (1-1) | 설계 규칙 60개 검증 | ✅ 완료 |

### Phase 3: 확장 기능

| 순위 | 기능 | 설명 | 상태 |
|------|------|------|------|
| 5 | 체크리스트 UI | 60개 항목 표시, 승인 워크플로우 | ✅ 완료 |
| 6 | Deviation List (1-4) | POR 대비 편차 관리 | ⏳ POR 문서 대기 |
| 7 | PDF 리포트 | 검토 결과 종합 출력 | ✅ 완료 (2025-12-31) |

### 블로커

| 항목 | 상태 |
|------|------|
| Deviation POR 기준 | ⏳ 원본 문서 회신 대기 |

### MVP 범위 ✅ 완료

1. ✅ P&ID 업로드 → 심볼/텍스트 인식
2. ✅ Equipment List 자동 생성 (Excel)
3. ✅ Valve Signal List 자동 생성 (Excel)
4. ✅ 설계 규칙 60개 검증 (Human-in-the-Loop)

---

## 4. 장기 목록 (필요 시 구현)

기존 "중기 로드맵" 4개 기능은 실제 데이터를 보고 판단:

| 기능 | 필요 시점 | 비고 |
|------|----------|------|
| 용접 기호 파싱 | 기계 도면 케이스 | 학습 데이터 필요 |
| 표면 거칠기 파싱 | 기계 도면 케이스 | 학습 데이터 필요 |
| 수량 추출 | BOM 정확도 요구 시 | 정규식 기반 |
| 벌룬 매칭 | 조립도 케이스 | 지시선 추적 필요 |

---

## 5. 파일 분리 현황

| 파일 | Before | After | 감소율 |
|------|--------|-------|--------|
| gateway-api/api_server.py | 2,044줄 | 335줄 | 84% |
| Guide.tsx | 1,235줄 | 151줄 | 88% |
| APIDetail.tsx | 1,197줄 | 248줄 | 79% |
| pid_features_router.py | 1,101줄 | 118줄 | 89% |
| region_extractor.py | 1,082줄 | 57줄 | 95% |
| api_server_edocr_v1.py | 1,068줄 | 97줄 | 91% |
| bwms_rules.py | 1,031줄 | 89줄 | 91% |
| NodePalette.tsx | 1,024줄 | 189줄 | 82% |
| lib/api.ts | 1,806줄 | 401줄 | 78% |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2025-12-31 | v23.0: ESLint 에러 0개, 테스트 505개 (gateway 364, web-ui 141), Executor 단위 테스트 126개, Feature Definition 동기화 자동화, Executor 개발 가이드 |
| 2025-12-31 | v22.0: BlueprintFlow 5개 신규 노드 (GT Comparison, PDF/Excel Export, PID Features, Verification Queue), 28개 노드, 379개 테스트 |
| 2025-12-31 | PDF 리포트 생성 기능 추가 (18개 테스트 통과) |
| 2025-12-31 | v20.0: 디자인 패턴 100점, 아키텍처 v3.0, 400개+ 테스트 |
| 2025-12-31 | v18.0: TECHCROSS 1-1, 1-2, 1-3 완료, MVP 100% 완료 |
| 2025-12-26 | TECHCROSS POC 개발 우선순위 추가 |
