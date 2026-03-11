# S01: 스타일 규칙 정의 + 검증 스크립트

> **상태**: ⬜ Todo
> **선행**: 없음
> **산출물**: `.claude/rules/docs-content-style.md`, `scripts/lint-style.sh`

---

## 목표

116개 문서에 일괄 적용할 스타일 규칙을 코드로 정의하고,
자동 검증 스크립트로 위반 사항을 탐지할 수 있게 한다.

## Tasks

### T01 스타일 규칙 파일 작성

**파일**: `.claude/rules/docs-content-style.md`

정의할 규칙:
1. **Frontmatter 필수 필드**: `title`, `description`, `tags`, `sidebar_position`
2. **H1 제목 패턴**: `# 한글 제목 (English Title)` 또는 `# English Title (한글 설명)`
3. **Blockquote**: H1 바로 다음 줄에 `>` 요약 1문장
4. **섹션 순서** (3종 템플릿):
   - Overview: 개요 → 아키텍처/구조 → 하위 페이지 → 관련 API → 관련 문서
   - Page: 접속 방법 → 탭/구조 → 상세 설명 → 관련 API → 관련 문서
   - API: 기본 정보 → 파라미터 → 응답 → 사용 예시 → 리소스 → 관련 문서
5. **표 형식**: 4종 (URL/권한/설명, 경로/페이지/설명/가이드, 탭/설명/주요동작, 기능/설명)
6. **관련 API**: 해당 파일에 `메서드 | 엔드포인트 | 설명` 표
7. **문체**: 운영/개발 톤, 마케팅 문구 금지

### T02 lint-style.sh 검증 스크립트 작성

**파일**: `docs-site-starlight/scripts/lint-style.sh`

검사 항목:
```bash
# 1. frontmatter 필수 필드 확인
grep -L "tags:" *.mdx → 누락 파일 목록

# 2. H1 패턴 확인
grep "^# " *.mdx | grep -v "(.*)" → 영어명 누락

# 3. blockquote 확인
# H1 다음 줄이 ">"로 시작하는지

# 4. 관련 문서 섹션 존재
grep -L "## 관련 문서" *.mdx → 누락

# 5. 관련 API 섹션 (대상 파일만)
# api-reference, analysis-pipeline, frontend/pages 하위

# 6. 파일 줄 수 (1000줄 초과 경고)
```

출력 형식:
```
[PASS] 95/115 files
[FAIL] 20/115 files
  - system-overview/index.mdx: missing tags, H1 pattern
  - frontend/routing.mdx: missing 관련 API
```

### T03 카테고리별 현황 리포트

`lint-style.sh --report` 옵션으로 카테고리별 준수율 표 생성:
```
| 카테고리 | 파일 수 | tags | H1 | blockquote | 섹션순서 | 관련API | 총점 |
|---------|--------|------|-----|-----------|---------|--------|------|
| system-overview | 6 | 0% | 33% | 100% | 50% | 17% | 40% |
```

### T04 검증 기준 문서화

- PASS: 모든 필수 규칙 충족
- WARN: 권장 규칙 미충족 (anchor, 표 형식)
- FAIL: 필수 규칙 위반 (tags, H1, blockquote, 관련 문서)

## 완료 조건

- [ ] `.claude/rules/docs-content-style.md` 존재
- [ ] `lint-style.sh` 실행 가능 + 현재 위반 사항 리포트 출력
- [ ] 리포트에서 카테고리별 현황 확인 가능
