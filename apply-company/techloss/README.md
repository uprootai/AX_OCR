# 테크로스 — 고객 프로젝트

> **고객 ID**: techcross
> **도면 유형**: P&ID (BWMS/ECS 설비)
> **디렉토리명**: `techloss` (레거시, 추후 `techcross`로 변경 가능)
> **담당자**: (확인 필요)

---

## 개요

| 항목 | 내용 |
|------|------|
| 업종 | 선박 평형수 처리 (BWMS), 전해 살균 시스템 (ECS) |
| 도면 유형 | P&ID (DWG → 구조화 → 규칙 검증) |
| 온보딩 시작일 | 2025-12 |
| 현재 Phase | Phase 1 완료 → Phase 2 미착수 |

## 요구사항 핵심 (60항목 중)

- AI 기반 도면 검토 (Drawn → AI 검토 → Approved)
- 자사 표준 심볼 라이브러리 기반 장비 인식
- 장비 간 상대적 위치 관계 파악
- 선급 기준 규칙 필터링 (P1)
- DWG 파일 우선 처리 (P0)

## 기존 자산

| 자산 | 위치 | 상태 |
|------|------|------|
| 요구사항 분석 (60항목) | `TECHLOSS_자료현황_2026-01-05.md` | ✅ |
| 시각적 설명 | `TECHLOSS_시각적_설명.md` | ✅ |
| E02 검증 보고서 | `E02-validation-report.md` | ✅ |
| 기본설계팀 계획서 | `기본설계팀 AI 활용한 도면 검토 계획.pptx` | ✅ |
| OCR 테스트 결과 | `ocr_test/` (16페이지 P&ID) | ✅ |
| Equipment List | `Equipment List 표준 파일/` (ECS, HYCHLOR) | ✅ |
| E2E 테스트 | `web-ui/e2e/api/techcross.spec.ts` | ✅ |
| 전용 파서/라우터 | 미생성 | ⬜ 필요 |
| 납품 패키지 | 미생성 | ⬜ 필요 |

## Phase 진행 상태

| Phase | 기간 | 상태 | 주요 산출물 |
|-------|------|------|------------|
| 1. 도면 분석 | 2025-12~2026-01 | ✅ 완료 | 요구분석 60항목, OCR 테스트 |
| 2. 모델 적응 | — | ⬜ 미착수 | YOLO P&ID + 전용 파서 필요 |
| 3. 검증 및 납품 | — | ⬜ | 납품 패키지 |

## TODO

- [ ] `create_customer_api.py --customer-id techcross --drawing-type pid` 실행
- [ ] YOLO P&ID 클래스 추가 라벨링 (테크로스 표준 심볼)
- [ ] DWG → PNG 변환 파이프라인 구축
- [ ] 전용 파서 개발 (Phase 2)
