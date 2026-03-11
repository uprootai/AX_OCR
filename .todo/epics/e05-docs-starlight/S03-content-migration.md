# S03: 콘텐츠 마이그레이션

> **Phase**: 2 (S02 Go 판정 후)
> **예상 소요**: 2~3일
> **의존성**: S02

---

## 목표

기존 Docusaurus docs-site의 **100+ 페이지**를 Starlight 구조로 변환한다.
수작업을 최소화하고, 자동화 스크립트로 대부분을 처리한다.

## 마이그레이션 범위

### 페이지 인벤토리

| 카테고리 | 페이지 수 | 변환 난이도 | 비고 |
|---------|---------|-----------|------|
| 1. System Overview | 6 | 낮음 | 순수 MD + 표 |
| 2. Analysis Pipeline | 6 | 중간 | FlowDiagram 포함 |
| 3. BlueprintFlow | 6 | 중간 | FlowDiagram 포함 |
| 4. Agent Verification | 4 | 낮음 | |
| 5. BOM & Quoting | 5 | 낮음 | |
| 6. P&ID Analysis | 5 | 중간 | FlowDiagram 포함 |
| 7. Batch & Delivery | 5 | 낮음 | |
| 8. Quality Assurance | 6 | 낮음 | |
| 9. Frontend | 5 | 낮음 | |
| 10. DevOps | 5 | 낮음 | |
| 11. R&D Research | 15 | 낮음 | 순수 MD |
| 12. API Reference | 18 | 낮음 | 표 중심 |
| 13. Developer Guide | 7 | 낮음 | |
| 14. Deployment | 6 | 낮음 | |
| 15. Customer Cases | 9 | 중간 | FlowDiagram + 이미지 |
| **합계** | **~108** | | |

### 변환 유형별 분류

| 유형 | 페이지 수 | 자동화 가능 |
|------|---------|-----------|
| 순수 MD/표 (변환 불필요) | ~70 | ✅ 복사만 |
| FlowDiagram 포함 | ~25 | ⚠️ import 문 추가 필요 |
| SequenceDiagram 포함 | ~8 | ⚠️ import 문 추가 필요 |
| Docusaurus 전용 문법 | ~5 | ⚠️ 수동 변환 |

## 자동화 스크립트

### 변환이 필요한 항목

| Docusaurus 문법 | Starlight 대응 | 자동화 |
|----------------|---------------|--------|
| `:::tip` / `:::warning` / `:::danger` | Starlight `:::tip` / `:::caution` / `:::danger` | ✅ sed 변환 |
| `<FlowDiagram ... />` (글로벌) | `import FlowDiagram from '...'` + `<FlowDiagram client:load ... />` | ✅ 스크립트 |
| `<SequenceDiagram ... />` (글로벌) | import + `client:load` 추가 | ✅ 스크립트 |
| `sidebar_position` frontmatter | Starlight `sidebar.order` 또는 파일명 접두사 | ✅ 스크립트 |
| `{type: 'doc', id: '...'}` 사이드바 | `autogenerate` 또는 수동 배열 | ⚠️ 반수동 |
| `/docs/...` 내부 링크 | 상대 경로 또는 `/docs/...` 유지 | ✅ 검색/치환 |

### 마이그레이션 스크립트 구조

```bash
scripts/migrate-to-starlight.sh

# Step 1: 파일 복사
cp -r docs-site/docs/* docs-site-starlight/src/content/docs/

# Step 2: frontmatter 변환
# sidebar_position → sidebar.order (또는 제거)

# Step 3: FlowDiagram/SequenceDiagram import 삽입
# 글로벌 등록 → 명시적 import + client:load 추가

# Step 4: admonition 문법 변환
# :::warning → :::caution

# Step 5: 이미지 경로 변환
# /docs/img/... → /img/... (public/ 기준)

# Step 6: 내부 링크 검증
# 깨진 링크 리스트 생성
```

## 디렉토리 매핑

| Docusaurus | Starlight |
|-----------|-----------|
| `docs-site/docs/` | `docs-site-starlight/src/content/docs/` |
| `docs-site/static/img/` | `docs-site-starlight/public/img/` |
| `docs-site/src/components/` | `docs-site-starlight/src/components/` |
| `docs-site/src/css/custom.css` | `docs-site-starlight/src/styles/custom.css` |
| `docs-site/sidebars.ts` | `astro.config.mjs` sidebar 설정 |
| `docs-site/docusaurus.config.ts` | `astro.config.mjs` |

## 검증 절차

| 단계 | 검증 | 방법 |
|------|------|------|
| 1 | 빌드 성공 | `npm run build` |
| 2 | 페이지 수 일치 | `find ... -name "*.mdx" | wc -l` 비교 |
| 3 | 깨진 링크 0 | Starlight 빌드 경고 확인 |
| 4 | 이미지 렌더링 | 주요 페이지 스크린샷 비교 |
| 5 | FlowDiagram 동작 | customer-cases 페이지에서 확인 |

## 산출물

- [ ] `scripts/migrate-to-starlight.sh` 자동화 스크립트
- [ ] 108개 페이지 변환 완료
- [ ] 깨진 링크 0개 확인
- [ ] 전/후 빌드 시간 비교

---

*작성: Claude Code | 2026-03-11*
