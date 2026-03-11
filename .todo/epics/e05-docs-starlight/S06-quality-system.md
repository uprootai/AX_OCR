# S06: 문서 품질 검증 체계

> **Phase**: 1 (즉시 시작 가능)
> **예상 소요**: 0.5~1일
> **의존성**: S01

---

## 목표

문서 작성/수정 시 자동으로 품질을 검증하는 체계를 구축한다.
**링크 깨짐, 표준 미준수, 숫자 불일치**를 빌드 시점에 잡는다.

## 검증 항목

| # | 검증 | 현재 상태 | 목표 |
|---|------|---------|------|
| 1 | 깨진 내부 링크 | `onBrokenLinks: 'warn'` (무시됨) | **빌드 실패** |
| 2 | 깨진 마크다운 링크 | `onBrokenMarkdownLinks: 'warn'` | **빌드 실패** |
| 3 | frontmatter 필수 필드 | 검증 없음 | `title`, `description` 필수 |
| 4 | blockquote 요약 | 검증 없음 | H1 아래 blockquote 존재 확인 |
| 5 | 관련 문서 섹션 | 검증 없음 | 마지막 섹션에 `## 관련 문서` 존재 |
| 6 | 이미지 파일 존재 | 빌드 시 확인 안됨 | 참조 이미지 존재 확인 |

## 구현 방안

### 1. Docusaurus 빌드 설정 강화 (즉시)

```typescript
// docusaurus.config.ts
onBrokenLinks: 'throw',        // warn → throw
onBrokenMarkdownLinks: 'throw', // warn → throw
```

### 2. 린트 스크립트 (신규)

```bash
# scripts/lint-docs.sh

#!/bin/bash
set -e

ERRORS=0

echo "=== 문서 품질 검증 ==="

# 1. frontmatter 필수 필드 확인
echo "[1/5] frontmatter 검증..."
for f in $(find docs -name "*.mdx" -o -name "*.md"); do
  if ! grep -q "^title:" "$f"; then
    echo "  ❌ title 누락: $f"
    ERRORS=$((ERRORS + 1))
  fi
  if ! grep -q "^description:" "$f"; then
    echo "  ❌ description 누락: $f"
    ERRORS=$((ERRORS + 1))
  fi
done

# 2. blockquote 요약 확인 (H1 아래)
echo "[2/5] blockquote 요약 검증..."
for f in $(find docs -name "*.mdx" -o -name "*.md"); do
  # frontmatter 이후 첫 H1 다음에 > 로 시작하는 줄이 있는지
  awk '/^---$/{c++; next} c==2{p=1} p && /^# /{h=1; next} h && /^$/{next} h && /^>/{found=1; exit} h{exit}
    END{if(h && !found) exit 1}' "$f" 2>/dev/null || {
    echo "  ⚠️  blockquote 누락: $f"
  }
done

# 3. 관련 문서 섹션 확인
echo "[3/5] 관련 문서 섹션 검증..."
for f in $(find docs -name "*.mdx" -o -name "*.md"); do
  if ! grep -q "^## 관련 문서" "$f"; then
    echo "  ⚠️  관련 문서 섹션 누락: $f"
  fi
done

# 4. 이미지 참조 검증
echo "[4/5] 이미지 참조 검증..."
for f in $(find docs -name "*.mdx" -o -name "*.md"); do
  grep -oP 'src="(/docs/img/[^"]+)"' "$f" | while read -r img; do
    img_path="static${img#/docs}"
    if [ ! -f "$img_path" ]; then
      echo "  ❌ 이미지 없음: $img_path (참조: $f)"
      ERRORS=$((ERRORS + 1))
    fi
  done
done

# 5. 문서 수 리포트
echo "[5/5] 문서 통계..."
TOTAL=$(find docs -name "*.mdx" -o -name "*.md" | wc -l)
WITH_TAGS=$(grep -rl "^tags:" docs | wc -l)
echo "  총 문서: $TOTAL"
echo "  tags 포함: $WITH_TAGS / $TOTAL"

echo ""
if [ $ERRORS -gt 0 ]; then
  echo "❌ $ERRORS개 오류 발견"
  exit 1
else
  echo "✅ 품질 검증 통과"
fi
```

### 3. 빌드 파이프라인 통합

```json
// package.json
{
  "scripts": {
    "lint:docs": "bash scripts/lint-docs.sh",
    "prebuild": "npm run lint:docs",
    "build": "docusaurus build"
  }
}
```

### 4. Claude Code Hook 통합

```bash
# .claude/hooks/post-edit-docs.sh
# docs-site/ 하위 파일 편집 후 자동 실행

FILE="$1"
if [[ "$FILE" == *"docs-site/docs/"* ]]; then
  cd docs-site
  bash scripts/lint-docs.sh 2>&1 | head -20
fi
```

## 정기 리포트 형식

문서 작성 완료 시 아래 체크리스트로 보고:

```markdown
## 문서 품질 리포트

| 지표 | 값 |
|------|---|
| 총 라우트 수 | N |
| 문서화된 라우트 수 | N |
| 총 문서 수 | N |
| 상세 링크 수 | N |
| 누락 링크 수 | 0 |
| 새로 만든 문서 수 | N |
| 공용 문서 anchor 수 | N |
| frontmatter 준수율 | 100% |
| blockquote 준수율 | N% |
```

## 산출물

- [ ] `docusaurus.config.ts` — `onBrokenLinks: 'throw'`
- [ ] `scripts/lint-docs.sh` — 문서 린트 스크립트
- [ ] `package.json` — prebuild에 lint 통합
- [ ] 품질 리포트 템플릿

## 완료 기준

- [ ] 빌드 시 깨진 링크 자동 감지 (throw)
- [ ] lint-docs.sh 스크립트 동작 확인
- [ ] 현재 문서 기준 품질 리포트 1회 생성

---

*작성: Claude Code | 2026-03-11*
