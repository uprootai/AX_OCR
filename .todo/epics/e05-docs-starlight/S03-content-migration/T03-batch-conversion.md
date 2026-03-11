# T03: 배치 변환 실행 + 검증

> **Story**: S03-content-migration
> **상태**: ⬜ Todo (T02 완료 후)

## 작업 내용

T02 스크립트로 전체 108개 페이지 변환 실행.

## 실행 순서

1. 스크립트 실행: `bash scripts/migrate-to-starlight.sh`
2. 빌드 확인: `cd docs-site-starlight && npm run build`
3. 깨진 링크 수정 (수동)
4. 이미지 누락 수정 (수동)
5. 최종 빌드 확인

## 카테고리별 검증

| 카테고리 | 페이지 수 | 빌드 | 링크 | 이미지 |
|---------|---------|------|------|--------|
| System Overview | 6 | ⬜ | ⬜ | ⬜ |
| Analysis Pipeline | 6 | ⬜ | ⬜ | ⬜ |
| BlueprintFlow | 6 | ⬜ | ⬜ | ⬜ |
| Agent Verification | 4 | ⬜ | ⬜ | ⬜ |
| BOM & Quoting | 5 | ⬜ | ⬜ | ⬜ |
| P&ID Analysis | 5 | ⬜ | ⬜ | ⬜ |
| Batch & Delivery | 5 | ⬜ | ⬜ | ⬜ |
| Quality Assurance | 6 | ⬜ | ⬜ | ⬜ |
| Frontend | 5+ | ⬜ | ⬜ | ⬜ |
| DevOps | 5 | ⬜ | ⬜ | ⬜ |
| R&D Research | 15 | ⬜ | ⬜ | ⬜ |
| API Reference | 18 | ⬜ | ⬜ | ⬜ |
| Developer Guide | 7 | ⬜ | ⬜ | ⬜ |
| Deployment | 6 | ⬜ | ⬜ | ⬜ |
| Customer Cases | 9 | ⬜ | ⬜ | ⬜ |

## 산출물

- [ ] 108개 페이지 변환 완료
- [ ] 깨진 링크 0개
- [ ] 빌드 성공
