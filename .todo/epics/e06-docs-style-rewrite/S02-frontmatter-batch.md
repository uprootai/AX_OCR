# S02: Frontmatter 일괄 표준화

> **상태**: ⬜ Todo
> **선행**: S01 (tags 분류 체계)
> **산출물**: 115개 파일 frontmatter 업데이트

---

## 목표

모든 문서 파일의 frontmatter에 `tags` 필드를 추가하고,
`description`이 누락된 파일을 보완한다.

## Tasks

### T01 tags 분류 체계 정의

카테고리별 기본 태그 + 파일별 세부 태그:

| 카테고리 | 기본 태그 | 세부 태그 예시 |
|---------|----------|--------------|
| system-overview | `시스템`, `아키텍처` | `포트`, `기술스택`, `의사결정` |
| analysis-pipeline | `파이프라인`, `ML` | `YOLO`, `OCR`, `공차`, `VLM` |
| blueprintflow | `워크플로우`, `DAG` | `노드`, `템플릿`, `최적화` |
| agent-verification | `검증`, `에이전트` | `3단계`, `대시보드` |
| bom-generation | `BOM`, `견적` | `검출`, `가격`, `PDF` |
| pid-analysis | `P&ID`, `분석` | `심볼`, `배관`, `설계검증` |
| batch-delivery | `배치`, `납품` | `프로젝트`, `온보딩` |
| quality-assurance | `QA`, `품질` | `GT비교`, `피드백`, `OCR메트릭` |
| frontend | `프론트엔드`, `React` | `라우팅`, `상태관리`, `BOM UI` |
| devops | `DevOps`, `Docker` | `CI`, `CD`, `GPU` |
| api-reference | `API`, `마이크로서비스` | 각 서비스명 |
| research | `연구`, `R&D` | 각 기술명 |
| developer | `개발자`, `가이드` | `Git`, `API스펙`, `기여` |
| deployment | `배포`, `운영` | `설치`, `온프레미스`, `Docker` |
| customer-cases | `고객사례` | `동서기연`, `파나시아` |

### T02 일괄 추가 스크립트

`scripts/add-tags.mjs` 작성:
- frontmatter YAML 파싱 (gray-matter)
- 카테고리 경로 → 기본 태그 자동 매핑
- 파일 내용 키워드 → 세부 태그 추가
- dry-run 모드 지원

실행:
```bash
node scripts/add-tags.mjs --dry-run  # 미리보기
node scripts/add-tags.mjs            # 실행
```

### T03 검증

```bash
# 모든 파일에 tags 존재 확인
grep -rL "tags:" src/content/docs/ | wc -l  # → 0

# tags 형식 확인 (배열)
grep "tags:" src/content/docs/**/*.{md,mdx} | head -20
```

## 완료 조건

- [ ] 115/115 파일에 `tags: [...]` 존재
- [ ] 태그가 최소 2개 이상
- [ ] lint-style.sh tags 검사 PASS
