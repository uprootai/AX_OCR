# T01: 표준 규칙 정의 문서 작성

> **Story**: S01-style-standards
> **상태**: ✅ 완료 (WT1에서 처리)
> **수정 파일**: `.claude/rules/docs-site.md`

## 완료 내용

`.claude/rules/docs-site.md` 에 아래 규칙 추가:

1. **Frontmatter 필수 필드**: `sidebar_position`, `title`, `description` 필수, `tags` 권장
2. **페이지 헤더 표준**: H1 아래 blockquote 요약 필수
3. **섹션 순서 표준**: 개요 → 구조 → 상세 → 설정 → API → 관련 문서
4. **표준 표 형식 4종**: Type A~D
5. **문체 규칙**: 건조한 운영/개발 문체, 숫자 명시, 추측 금지
6. **Anchor 기반 복합 문서**: `{#anchor-id}` 사용법

## 검증

- [x] `.claude/rules/docs-site.md` 에 규칙 추가됨
- [x] 기존 규칙과 충돌 없음
