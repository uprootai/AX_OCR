# T04: 품질 리포트 템플릿 생성

> **Story**: S06-quality-system
> **상태**: 🔄 진행 중 (WT3)
> **생성 파일**: `docs-site/scripts/QUALITY_REPORT_TEMPLATE.md`

## 템플릿 내용

```markdown
## 문서 품질 리포트

| 지표 | 값 |
|------|---|
| 총 문서 수 | N |
| frontmatter title 준수율 | N% |
| frontmatter description 준수율 | N% |
| blockquote 요약 준수율 | N% |
| 관련 문서 섹션 준수율 | N% |
| 깨진 이미지 참조 | N개 |
| tags 포함 비율 | N% |

### 라우트 문서화 (S05 완료 후)

| 지표 | 값 |
|------|---|
| 총 라우트 수 | N |
| 문서화된 라우트 수 | N |
| 상세 링크 수 | N |
| 누락 링크 수 | N |
```

## 검증

- [ ] 템플릿 파일 생성됨
- [ ] lint-docs.sh 실행 결과로 첫 리포트 생성 가능
