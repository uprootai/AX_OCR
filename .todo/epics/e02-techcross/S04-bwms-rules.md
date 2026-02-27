# S04: Design Checker BWMS 규칙 구현

> **Epic**: E02 — 테크로스 P&ID 자동 설계 검증
> **상태**: ⬜ Todo
> **예상**: 4h
> **의존**: S02 (BWMS 장비 인식 필요)

---

## 설명

Design Checker의 기존 BWMS 규칙 7개 + 검증 파이프라인을 실행 가능하게 만든다.
**S01 발견**: 규칙 7개(BWMS-001,004,005,006,007,008,009) 이미 등록됨.
`/check/bwms`는 `symbols` JSON 필요, `/pipeline/validate`는 타임아웃.

## 완료 조건

- [ ] `/pipeline/validate` 타임아웃 원인 파악 + 수정
- [ ] `/check/bwms`에 YOLO+OCR 결과 연동 테스트
- [ ] 샘플 P&ID로 BWMS 규칙 7개 중 3개 이상 판정 결과 확인
- [ ] 체크리스트 템플릿 연동 (`/checklist/upload`) 테스트

## 변경 범위

| 파일 | 작업 |
|------|------|
| `models/design-checker-api/bwms_rules.py` | **신규** — BWMS 규칙 5개 |
| `models/design-checker-api/rule_loader.py` | 수정 — BWMS 규칙 등록 |
| `models/design-checker-api/tests/test_bwms_rules.py` | **신규** — 단위 테스트 |

## 에이전트 지시

```
이 Story를 구현하세요.
- 기존 rule_loader.py 패턴을 따라 BWMS 규칙 모듈 추가
- 각 규칙은 (detection_results, ocr_results, line_results) → [Violation] 시그니처
- 위치 관계 판단: bounding box 좌표 비교 (upstream = x좌표 작은 쪽)
- 용량 비교 (BWMS-007): OCR에서 수치 추출 후 비율 계산
- 거리 계산 규칙 (BWMS-002, 003, 006)은 이 Story 범위 밖
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```

## 구현 노트

참조 문서: `apply-company/techloss/TECHLOSS_미구현기능_평가.md`

Phase 2 (추후):
- BWMS-002: TSU-APU 거리 ≥ 5m, 높이 ≥ 2m
- BWMS-003: ANU/NIU Injection ≥ 10m
- BWMS-006: Min 거리 5D (파이프 직경 × 5)
- BWMS-009: HYCHLOR 필터 위치 검증
