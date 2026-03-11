# T04: 나머지 카테고리에 표준 적용

> **Story**: S01-style-standards
> **상태**: ⬜ Todo
> **우선순위**: 낮음 (Phase 1 완료 후 단계적 적용)

## 대상 카테고리 (미적용)

| 카테고리 | 페이지 수 | 예상 소요 |
|---------|---------|----------|
| 2. Analysis Pipeline | 6 | 30분 |
| 3. BlueprintFlow | 6 | 30분 |
| 4. Agent Verification | 4 | 20분 |
| 5. BOM & Quoting | 5 | 25분 |
| 6. P&ID Analysis | 5 | 25분 |
| 7. Batch & Delivery | 5 | 25분 |
| 8. Quality Assurance | 6 | 30분 |
| 9. Frontend | 5 | 25분 |
| 10. DevOps | 5 | 25분 |
| 11. R&D Research | 15 | 45분 |
| 12. API Reference | 18 | 50분 |
| 13. Developer Guide | 7 | 30분 |
| 14. Deployment | 6 | 30분 |
| **합계** | **~93** | **~6시간** |

## 적용 체크리스트 (각 파일)

- [ ] `description` frontmatter 존재 확인 (없으면 추가)
- [ ] H1 아래 blockquote 요약 존재 확인 (없으면 추가)
- [ ] 마지막에 `## 관련 문서` 섹션 존재 확인 (없으면 추가)
- [ ] 마케팅 문체 → 운영/개발 문체 변환
- [ ] 빌드 성공 확인

## 실행 방식

- 카테고리별 워크트리 에이전트로 병렬 처리 가능
- 각 에이전트는 자신의 카테고리만 수정
- 충돌 가능성: 없음 (각각 별도 디렉토리)
