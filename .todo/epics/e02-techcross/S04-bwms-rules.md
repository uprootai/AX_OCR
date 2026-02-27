# S04: Design Checker BWMS 규칙 실행

> **Epic**: E02 — 테크로스 P&ID 자동 설계 검증
> **상태**: ✅ Done
> **예상**: 4h (실제 1h — 이미 96개 규칙 구현됨)
> **의존**: S02 ✅, S03 ✅

---

## 설명

Design Checker의 기존 BWMS 규칙 + 검증 파이프라인을 실제 P&ID 데이터로 실행 가능 확인.
**S01 발견**: 규칙 7개(BWMS-001~009) + 동적 규칙 89개 이미 등록됨.

## 완료 조건

- [x] `/check/bwms`에 YOLO+OCR 결과 연동 테스트
- [x] 샘플 P&ID로 BWMS 규칙 96개 검사, 1건 위반 감지
- [x] 체크리스트 템플릿 (`/checklist/template`) 다운로드 확인
- [ ] `/pipeline/validate` 타임아웃 → YOLO 서비스 다운으로 미테스트 (코드 문제 아님)

## 테스트 결과

| 항목 | 결과 |
|------|------|
| 장비 인식 | 5/6 (TSU, ANU, ECU, EWU, APU) — TRO 식별자 미매칭 |
| 규칙 검사 | 96개 (builtin 7 + dynamic 89) |
| 위반 감지 | 1건 — BWMS-006 TSU-APU 거리 제한 |
| 응답 시간 | < 1초 |
| 체크리스트 템플릿 | ✅ 13열 Excel (Rule ID~Product) |

## 구현 노트

- **코드 변경 없음** — Design Checker API는 이미 완전히 구현되어 있었음
- `/check/bwms` 입력: `symbols` (YOLO/Equipment), `texts` (OCR), `connections` (optional)
- 위반 감지 정확도는 입력 데이터 품질에 의존 (YOLO bbox 정확도, OCR 인식률)
- `/pipeline/validate`는 YOLO→OCR→Check 전체 파이프라인 실행 (YOLO 서비스 필요)

### 규칙 카테고리

| 카테고리 | 개수 | 예시 |
|----------|------|------|
| Builtin (BWMS-xxx) | 7 | 장비 위치, 순서, 거리, 용량 |
| Common (COM-xxx) | 19 | 기본 설계, Retrofit, Class별 |
| ECS (ECS-xxx) | 35 | Ballast Pump, ECU, FMU, ANU, DTS |
| HYCHLOR (HYC-xxx) | 24 | SWH, HGU, DMU, NIU, CIP |
| Class-specific | 11 | ABS, DNV, KR, LR 규칙 |
