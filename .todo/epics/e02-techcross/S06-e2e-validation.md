# S06: E2E 검증 + 체크리스트 매핑

> **Epic**: E02 — 테크로스 P&ID 자동 설계 검증
> **상태**: ⬜ Todo
> **예상**: 2h
> **의존**: S01~S05 전체

---

## 설명

모든 Story를 통합하여 테크로스 샘플 P&ID로 E2E 파이프라인을 실행한다.
60개 체크리스트 중 자동화 가능 항목을 매핑하고, 검증 결과 리포트를 생성한다.

## 완료 조건

- [ ] ECS 샘플: 전체 파이프라인 → Excel 3종 출력
- [ ] HYCHLOR 샘플: 전체 파이프라인 → Excel 3종 출력
- [ ] 60개 체크리스트 중 자동화 커버리지 집계 (목표: 30%+)
- [ ] 검증 결과 정리 (`apply-company/techloss/E02-validation-report.md`)
- [ ] 미자동화 항목 → E02-Phase2 백로그로 이관

## 변경 범위

| 파일 | 작업 |
|------|------|
| `apply-company/techloss/E02-validation-report.md` | **신규** — 검증 결과 |
| `.todo/BACKLOG.md` | E02-Phase2 항목 추가 (필요 시) |

## 에이전트 지시

```
이 Story를 구현하세요.
- Playwright 브라우저로 BlueprintFlow 테크로스 프리셋 실행
- ECS → HYCHLOR 순서로 각각 전체 파이프라인 실행
- 각 단계 스크린샷 + 결과 JSON 저장
- Excel 출력물 3종 (Equipment, Valve Signal, Checklist) 검증
- 60개 체크리스트 기준으로 자동/수동/N/A 분류
- 검증 리포트 작성 + ACTIVE.md 갱신
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```
