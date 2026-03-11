#!/bin/bash
# Usage: cd docs-site && bash scripts/lint-docs.sh
# Docs quality lint script for AX POC documentation
# Errors (!) cause exit 1, warnings (?) are report-only.

set -euo pipefail

DOCS_DIR="docs"
STATIC_IMG_DIR="static/img"
ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Collect all doc files
mapfile -t DOC_FILES < <(find "$DOCS_DIR" -type f \( -name "*.md" -o -name "*.mdx" \) | sort)
TOTAL_DOCS=${#DOC_FILES[@]}

if [[ $TOTAL_DOCS -eq 0 ]]; then
  echo -e "${YELLOW}No documentation files found in ${DOCS_DIR}/${NC}"
  exit 0
fi

echo -e "${BOLD}${CYAN}=== AX POC Documentation Quality Lint ===${NC}"
echo -e "Scanning ${TOTAL_DOCS} documents...\n"

# --- 1. Frontmatter required fields (title, description) ---
echo -e "${BOLD}[1/5] Frontmatter required fields (title, description)${NC}"
FRONTMATTER_OK=0
FRONTMATTER_FAIL=0

for f in "${DOC_FILES[@]}"; do
  # Extract frontmatter block (between first --- and second ---)
  if head -1 "$f" | grep -q '^---'; then
    fm=$(sed -n '1,/^---$/{ /^---$/d; p }' "$f" | sed '1d')
    has_title=$(echo "$fm" | grep -c '^title:' || true)
    has_desc=$(echo "$fm" | grep -c '^description:' || true)
    if [[ $has_title -eq 0 || $has_desc -eq 0 ]]; then
      missing=""
      [[ $has_title -eq 0 ]] && missing="title"
      [[ $has_desc -eq 0 ]] && missing="${missing:+$missing, }description"
      echo -e "  ${RED}! ${f}${NC} — missing: ${missing}"
      FRONTMATTER_FAIL=$((FRONTMATTER_FAIL + 1))
      ERRORS=$((ERRORS + 1))
    else
      FRONTMATTER_OK=$((FRONTMATTER_OK + 1))
    fi
  else
    echo -e "  ${RED}! ${f}${NC} — no frontmatter block"
    FRONTMATTER_FAIL=$((FRONTMATTER_FAIL + 1))
    ERRORS=$((ERRORS + 1))
  fi
done

if [[ $FRONTMATTER_FAIL -eq 0 ]]; then
  echo -e "  ${GREEN}All ${FRONTMATTER_OK} documents have required frontmatter.${NC}"
fi
echo ""

# --- 2. Blockquote summary after H1 (warning only) ---
echo -e "${BOLD}[2/5] Blockquote summary after H1${NC}"
BQ_OK=0
BQ_MISS=0

for f in "${DOC_FILES[@]}"; do
  # Find first H1 line number, then check if next non-empty line starts with >
  h1_line=$(grep -n '^# ' "$f" | head -1 | cut -d: -f1 || true)
  if [[ -n "$h1_line" ]]; then
    # Check lines after H1 for a blockquote
    found_bq=false
    tail -n +"$((h1_line + 1))" "$f" | head -5 | while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      if [[ "$line" == ">"* ]]; then
        echo "FOUND"
        break
      else
        break
      fi
    done | grep -q "FOUND" && found_bq=true
    if $found_bq; then
      BQ_OK=$((BQ_OK + 1))
    else
      echo -e "  ${YELLOW}? ${f}${NC} — no blockquote summary after H1"
      BQ_MISS=$((BQ_MISS + 1))
      WARNINGS=$((WARNINGS + 1))
    fi
  else
    # No H1, skip
    BQ_OK=$((BQ_OK + 1))
  fi
done

if [[ $BQ_MISS -eq 0 ]]; then
  echo -e "  ${GREEN}All documents with H1 have blockquote summaries.${NC}"
fi
echo ""

# --- 3. Related docs section (warning only) ---
echo -e "${BOLD}[3/5] Related docs section${NC}"
RD_OK=0
RD_MISS=0

for f in "${DOC_FILES[@]}"; do
  if grep -q '^## .*관련 문서' "$f" 2>/dev/null || grep -q '^## Related' "$f" 2>/dev/null; then
    RD_OK=$((RD_OK + 1))
  else
    echo -e "  ${YELLOW}? ${f}${NC} — no '## 관련 문서' section"
    RD_MISS=$((RD_MISS + 1))
    WARNINGS=$((WARNINGS + 1))
  fi
done

if [[ $RD_MISS -eq 0 ]]; then
  echo -e "  ${GREEN}All documents have a related docs section.${NC}"
fi
echo ""

# --- 4. Image reference validation ---
echo -e "${BOLD}[4/5] Image reference validation${NC}"
IMG_OK=0
IMG_BROKEN=0

for f in "${DOC_FILES[@]}"; do
  # Match src="/docs/img/..." patterns
  while IFS= read -r match; do
    # Extract path: /docs/img/foo.png -> static/img/foo.png
    img_path=$(echo "$match" | sed 's|^/docs/img/|'"$STATIC_IMG_DIR"'/|')
    if [[ ! -f "$img_path" ]]; then
      echo -e "  ${RED}! ${f}${NC} — broken image: ${match} (expected: ${img_path})"
      IMG_BROKEN=$((IMG_BROKEN + 1))
      ERRORS=$((ERRORS + 1))
    else
      IMG_OK=$((IMG_OK + 1))
    fi
  done < <(grep -oP 'src="/docs/img/[^"]+' "$f" 2>/dev/null | sed 's|^src="||' || true)

  # Also check markdown image syntax ![alt](/docs/img/...)
  while IFS= read -r match; do
    img_path=$(echo "$match" | sed 's|^/docs/img/|'"$STATIC_IMG_DIR"'/|')
    if [[ ! -f "$img_path" ]]; then
      echo -e "  ${RED}! ${f}${NC} — broken image: ${match} (expected: ${img_path})"
      IMG_BROKEN=$((IMG_BROKEN + 1))
      ERRORS=$((ERRORS + 1))
    else
      IMG_OK=$((IMG_OK + 1))
    fi
  done < <(grep -oP '!\[[^\]]*\]\(/docs/img/[^)]+' "$f" 2>/dev/null | grep -oP '/docs/img/[^)]+' || true)
done

if [[ $IMG_BROKEN -eq 0 ]]; then
  echo -e "  ${GREEN}All image references are valid (${IMG_OK} checked).${NC}"
fi
echo ""

# --- 5. Document statistics report ---
echo -e "${BOLD}[5/5] Document Statistics${NC}"

# Tags count
TAGS_COUNT=0
for f in "${DOC_FILES[@]}"; do
  if head -1 "$f" | grep -q '^---'; then
    fm=$(sed -n '1,/^---$/{ /^---$/d; p }' "$f" | sed '1d')
    if echo "$fm" | grep -q '^tags:'; then
      TAGS_COUNT=$((TAGS_COUNT + 1))
    fi
  fi
done

# Average line count
TOTAL_LINES=0
for f in "${DOC_FILES[@]}"; do
  lines=$(wc -l < "$f")
  TOTAL_LINES=$((TOTAL_LINES + lines))
done
AVG_LINES=$((TOTAL_LINES / TOTAL_DOCS))

# Calculate percentages
FM_PCT=$((FRONTMATTER_OK * 100 / TOTAL_DOCS))
BQ_PCT=$((BQ_OK * 100 / TOTAL_DOCS))
RD_PCT=$((RD_OK * 100 / TOTAL_DOCS))
TAGS_PCT=$((TAGS_COUNT * 100 / TOTAL_DOCS))

echo ""
echo -e "${BOLD}${CYAN}=== Quality Report ===${NC}"
echo -e "| Metric                      | Value           |"
echo -e "|-----------------------------|-----------------|"
echo -e "| Total documents             | ${TOTAL_DOCS}              |"
echo -e "| Frontmatter compliance      | ${FM_PCT}% (${FRONTMATTER_OK}/${TOTAL_DOCS})   |"
echo -e "| Blockquote summary          | ${BQ_PCT}% (${BQ_OK}/${TOTAL_DOCS})   |"
echo -e "| Related docs section        | ${RD_PCT}% (${RD_OK}/${TOTAL_DOCS})   |"
echo -e "| Tags included               | ${TAGS_PCT}% (${TAGS_COUNT}/${TOTAL_DOCS})   |"
echo -e "| Average lines per doc       | ${AVG_LINES}              |"
echo -e "| Broken image references     | ${IMG_BROKEN}              |"
echo ""

# Final result
if [[ $ERRORS -gt 0 ]]; then
  echo -e "${RED}${BOLD}FAILED${NC}: ${ERRORS} error(s), ${WARNINGS} warning(s)"
  exit 1
else
  echo -e "${GREEN}${BOLD}PASSED${NC}: 0 errors, ${WARNINGS} warning(s)"
  exit 0
fi
