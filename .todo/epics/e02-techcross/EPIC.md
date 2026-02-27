# Epic: 테크로스 P&ID 자동 설계 검증 납품

> **ID**: E02
> **상태**: Active
> **기간**: 2026-02-27 ~ 2026-03-21
> **고객**: 테크로스 (TECHCROSS) — BWMS 기본설계팀

---

## 목적

테크로스 BWMS(선박평형수처리장치) P&ID 도면의 자동 설계 검증 시스템을 구축한다.
60개 항목 체크리스트 자동 검토 + Valve Signal List / Equipment List / Deviation List 자동 생성.

## 성공 기준 (Definition of Done)

- [ ] 샘플 P&ID 2장(ECS, HYCHLOR)으로 파이프라인 동작 확인
- [ ] BWMS 장비 태그 11종 OCR 인식률 90% 이상
- [ ] Equipment List + Valve Signal List Excel 자동 생성
- [ ] Design Checker BWMS 규칙 5개 이상 구현
- [ ] BlueprintFlow 테크로스 프리셋 템플릿 등록

## Story 목록

| ID | Story | 예상 | 상태 |
|----|-------|------|------|
| S01 | [샘플 P&ID 파이프라인 테스트](S01-pipeline-test.md) | 2h | ✅ Done |
| S02 | [BWMS 태그 패턴 인식](S02-bwms-tag-recognition.md) | 2h | ✅ Done |
| S03 | [Excel 출력 (Equipment + Valve Signal)](S03-excel-export.md) | 3h | ✅ Done |
| S04 | [Design Checker BWMS 규칙](S04-bwms-rules.md) | 4h | ✅ Done |
| S05 | [BlueprintFlow 테크로스 프리셋](S05-blueprintflow-preset.md) | 1h | ✅ Done |
| S06 | [E2E 검증 + 체크리스트 매핑](S06-e2e-validation.md) | 2h | ✅ Done |

## 기술 결정

- YOLO 모델 재학습은 이 Epic 범위 밖 (데이터 수집 필요 → E02-B로 분리 예정)
- BWMS 장비 인식: Phase 1은 OCR 태그 패턴 매칭 (정규식), Phase 2에서 YOLO 확장
- Excel 출력: openpyxl 사용 (이미 PID Analyzer에서 의존)
- 거리 계산: P&ID 스케일 수동 입력 → 추후 자동 감지

## 참조

- `apply-company/techloss/TECHLOSS_자료_정리.md` — 프로젝트 개요, BWMS 제품 정보
- `apply-company/techloss/TECHCROSS_POC_개발_우선순위.md` — 개발 우선순위
- `apply-company/techloss/TECHLOSS_미구현기능_평가.md` — 상세 Gap 분석
- `apply-company/techloss/ECS_vs_HYCHLOR_체크리스트_비교분석.md` — 체크리스트 비교
- `models/design-checker-api/` — Design Checker 소스
- `models/pid-analyzer-api/` — PID Analyzer 소스
