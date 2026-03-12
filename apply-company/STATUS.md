# 고객사 온보딩 현황 대시보드

> **최종 업데이트**: 2026-03-12
> **관리 범위**: 초기 3개사 + 향후 7개사 (AX 실증산단)

---

## 전체 현황

| # | 고객 | 업종 | 도면 유형 | Phase | 상태 | 납품 |
|---|------|------|-----------|-------|------|------|
| 1 | **파나시아** | 선박 BWMS | P&ID | 3 | 🟡 납품 대기 | ⬜ |
| 2 | **동서기연** | 터빈 베어링 | 기계 도면 | 3 | ✅ 완료 | ✅ |
| 3 | **테크로스** | 선박 BWMS/ECS | P&ID | 1 | 🔵 개발 착수 | ⬜ |
| 4~10 | 신규 7개사 | 미정 | 미정 | — | ⬜ 모집 중 | — |

## Phase 정의

| Phase | 기간 | 주요 활동 |
|-------|------|-----------|
| **1. 도면 분석** | 1~2주 | 샘플 수집 → 기존 모델 테스트 → 커버리지 측정 |
| **2. 모델 적응** | 2~4주 | YOLO 라벨링/학습, 전용 파서 생성, API 스캐폴딩 |
| **3. 검증 및 납품** | 1~2주 | GT 비교 F1≥90%, E2E 테스트, 납품 패키지 |

## 도구 체인

| 도구 | 용도 | 사용 시점 |
|------|------|-----------|
| `scripts/test_coverage.py` | 샘플 도면 커버리지 측정 | Phase 1 |
| `scripts/create_customer_api.py` | 전용 파서/라우터 스캐폴딩 | Phase 2 |
| `delivery-template/generate-package.sh` | 납품 패키지 생성 | Phase 3 |

## 고객별 상세

### 1. 파나시아 (panasia)

- **디렉토리**: `apply-company/panasia/`
- **YOLO 모델**: `models/yolo-api/models/panasia_yolo.pt` (27클래스)
- **다음 할 일**: `generate-package.sh`로 납품 패키지 생성
- **블로커**: 고객 전달 일정 미확정

### 2. 동서기연 (dsebearing)

- **디렉토리**: `apply-company/dsebearing/`
- **전용 파서**: `gateway-api/services/dsebearing_parser/` (7파일)
- **납품**: `blueprint-ai-bom/exports/dsebearing-delivery/` (326 BOM, ₩100M)
- **상태**: 2차 미팅 완료, 추가 요청 대기

### 3. 테크로스 (techcross)

- **디렉토리**: `apply-company/techloss/` (레거시명)
- **요구분석**: 60항목 체크리스트 완료
- **스캐폴딩**: `gateway-api/services/techcross_parser.py` 생성 완료 (stub)
- **다음 할 일**: YOLO P&ID 심볼 라벨링 + 파서 구현
- **블로커**: DWG 파일 처리 파이프라인 필요

---

## 참조

| 문서 | 위치 |
|------|------|
| 고객 디렉토리 템플릿 | `apply-company/_template/` |
| 납품 패키지 템플릿 | `blueprint-ai-bom/exports/delivery-template/` |
| 커스터마이징 가이드 | `scripts/create_customer_api.py --help` |
| 사용자 교육 자료 | `docs-site-starlight/.../user-guide/` |
