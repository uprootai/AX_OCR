# .todos - 작업 추적

> **최종 업데이트**: 2025-12-26 | **버전**: v9.2

---

## 현재 상태

```
    기능: 16/20 (80%)   빌드: ✅ 통과   API: 18/18
```

---

## TECHCROSS POC (진행 중)

### MVP 범위 (2주)

| 순위 | 기능 | 상태 |
|------|------|------|
| 1 | P&ID 심볼/텍스트 인식 (BWMS 8종) | 📋 |
| 2 | Equipment List 자동 생성 | 📋 |
| 3 | Valve Signal List 자동 생성 | 📋 |
| 4 | 기본 설계 규칙 3개 검증 | 📋 |

### 블로커

- 체크리스트 xlsm 손상 → 파일 재요청 완료
- BWMS 심볼 학습 데이터 → 샘플 도면 라벨링 필요

### 상세

- [개발 우선순위](../apply-company/techloss/TECHCROSS_POC_개발_우선순위.md)
- [질문 목록 (이메일용)](../apply-company/techloss/TECHCROSS_질문목록_이메일용.md)

---

## 즉시 필요 (Blueprint AI BOM)

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

## 파일 목록

| 파일 | 용도 |
|------|------|
| `REMAINING_WORK_PLAN.md` | 작업 계획 + TECHCROSS POC 상세 |
| `2025-12-24_blueprint_ai_bom_feature_roadmap.md` | 기능 로드맵 참조 |
| `2025-12-24_v8_post_commit_tasks.md` | 테스트 목록 |
| `2025-12-19_blueprint_ai_bom_expansion_proposal.md` | 확장 제안 참조 |
| `2025-12-14_export_architecture.md` | Export 아키텍처 참조 |
