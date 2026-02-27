# S01: 샘플 P&ID 파이프라인 테스트

> **Epic**: E02 — 테크로스 P&ID 자동 설계 검증
> **상태**: ✅ Done
> **예상**: 2h

---

## 설명

테크로스 샘플 P&ID(ECS, HYCHLOR) 2장을 현재 파이프라인(YOLO → Line Detector → OCR → PID Analyzer)으로 처리하여 기존 능력의 베이스라인을 확인한다.

## 완료 조건

- [ ] ECS 샘플 P&ID 파이프라인 실행 완료
- [ ] HYCHLOR 샘플 P&ID 파이프라인 실행 완료
- [ ] 각 단계별 결과 스크린샷 저장 (YOLO, Line, OCR, PID Analyzer)
- [ ] 인식률/누락 장비 목록 정리 → S02 입력으로 전달

## 변경 범위

| 파일 | 작업 |
|------|------|
| 신규 파일 없음 | 기존 API로 테스트만 수행 |
| `apply-company/techloss/test-results/` | 테스트 결과 저장 (신규 디렉토리) |

## 에이전트 지시

```
이 Story를 구현하세요.
- 샘플 P&ID 파일 위치 확인 (apply-company/techloss/ 하위)
- Playwright 브라우저로 BlueprintFlow에서 파이프라인 실행
- 또는 Playwright HTTP로 각 API 순차 호출
- 결과 스크린샷 + JSON 저장
- 인식/미인식 장비 목록 정리
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```

## 구현 노트

샘플 P&ID 파일명:
- ECS: `[PNID] REV.0 YZJ2023-1584_1585_NK_ECS1000Bx1_MIX.pdf`
- HYCHLOR: `[PNID] Rev.0 H1993A...HYCHLOR 2.0-3000 2SETS_LR.pdf`
