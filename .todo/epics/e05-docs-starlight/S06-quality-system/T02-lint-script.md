# T02: 문서 린트 스크립트 작성

> **Story**: S06-quality-system
> **상태**: 🔄 진행 중 (WT3)
> **생성 파일**: `docs-site/scripts/lint-docs.sh`

## 검증 항목

| # | 검증 | 심각도 | 동작 |
|---|------|--------|------|
| 1 | `title` frontmatter 존재 | ❌ 에러 | exit 1 |
| 2 | `description` frontmatter 존재 | ❌ 에러 | exit 1 |
| 3 | H1 아래 blockquote 존재 | ⚠️ 경고 | 리포트만 |
| 4 | `## 관련 문서` 섹션 존재 | ⚠️ 경고 | 리포트만 |
| 5 | 이미지 참조 파일 존재 | ❌ 에러 | exit 1 |
| 6 | 문서 통계 리포트 | ℹ️ 정보 | 출력만 |

## 스크립트 구조

```bash
#!/bin/bash
# Usage: cd docs-site && bash scripts/lint-docs.sh
set -e
ERRORS=0
WARNINGS=0

# 1~5 검증 루프
# 6. 통계 출력
# 최종 결과 (ERRORS > 0이면 exit 1)
```

## 검증

- [ ] 스크립트 실행 성공
- [ ] 에러 항목 정상 감지
- [ ] 경고 항목 정상 감지
- [ ] 통계 리포트 출력
