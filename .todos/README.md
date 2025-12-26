# .todos - 작업 추적

> **최종 업데이트**: 2025-12-26 | **버전**: v9.1

---

## 현재 상태

```
    기능: 16/20 (80%)   빌드: ✅ 통과   API: 18/18
```

---

## 즉시 필요

| 항목 | 설명 |
|------|------|
| 단위 테스트 3개 | active_learning, session, verification |
| ESLint 에러 4개 | 기존 코드 수정 |

---

## 장기 (필요 시)

4개 기능은 실제 데이터 보고 판단:

| 기능 | 조건 |
|------|------|
| 용접 기호 파싱 | 기계 도면 케이스 |
| 표면 거칠기 파싱 | 기계 도면 케이스 |
| 수량 추출 | BOM 정확도 요구 시 |
| 벌룬 매칭 | 조립도 케이스 |

---

## TECHCROSS 프로젝트

**회사**: TECHCROSS (테크로스) - BWMS 제조사

**요구사항**:
- P&ID BWMS 장비 인식 (8종)
- 설계 규칙 검증 (9개)
- 체크리스트 자동화 (60개)
- 출력물 생성 (Valve/Equipment List)

**AX POC 대응**:
- YOLO-PID, Line Detector, PID Analyzer ✅ 있음
- BWMS 전용 규칙/UI 확장 📋 추가 필요

**상세**: [REMAINING_WORK_PLAN.md](./REMAINING_WORK_PLAN.md)

**자료 위치**: `apply-company/techloss/`

---

## 파일 목록

| 파일 | 용도 |
|------|------|
| `REMAINING_WORK_PLAN.md` | 작업 계획 + TECHCROSS 요약 |
| `2025-12-24_blueprint_ai_bom_feature_roadmap.md` | 기능 로드맵 참조 |
| `2025-12-24_v8_post_commit_tasks.md` | 테스트 목록 |
| `2025-12-19_blueprint_ai_bom_expansion_proposal.md` | 확장 제안 참조 |
| `2025-12-14_export_architecture.md` | Export 아키텍처 참조 |
