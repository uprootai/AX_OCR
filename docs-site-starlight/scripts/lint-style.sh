#!/usr/bin/env bash
# lint-style.sh — Docs content style compliance checker
# Usage: ./lint-style.sh [--report]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="$SCRIPT_DIR/../src/content/docs"

if [[ ! -d "$DOCS_DIR" ]]; then
  echo "ERROR: docs directory not found: $DOCS_DIR"
  exit 1
fi

SHOW_REPORT=false
if [[ "${1:-}" == "--report" ]]; then
  SHOW_REPORT=true
fi

# Directories that require 관련 API section
API_REQUIRED_DIRS="analysis-pipeline|blueprintflow|agent-verification|bom-generation|pid-analysis|batch-delivery|quality-assurance|frontend/pages|devops"
# Directories exempt from 관련 API requirement
API_EXEMPT_DIRS="research|api-reference|customer-cases"

total=0
pass=0
fail=0

declare -A cat_files
declare -A cat_tags
declare -A cat_h1
declare -A cat_bq
declare -A cat_related_docs
declare -A cat_related_api

violations=""

while IFS= read -r -d '' file; do
  total=$((total + 1))
  rel_path="${file#"$DOCS_DIR"/}"
  category="${rel_path%%/*}"

  # Initialize category counters
  if [[ -z "${cat_files[$category]+x}" ]]; then
    cat_files[$category]=0
    cat_tags[$category]=0
    cat_h1[$category]=0
    cat_bq[$category]=0
    cat_related_docs[$category]=0
    cat_related_api[$category]=0
  fi
  cat_files[$category]=$(( ${cat_files[$category]} + 1 ))

  file_violations=""

  # --- Extract frontmatter (first 30 lines, between --- markers) ---
  frontmatter=$(head -n 30 "$file" | sed -n '/^---$/,/^---$/p')

  # Check 1: tags in frontmatter
  has_tags=false
  if echo "$frontmatter" | grep -q '^tags:'; then
    has_tags=true
    cat_tags[$category]=$(( ${cat_tags[$category]} + 1 ))
  else
    file_violations="${file_violations}missing tags, "
  fi

  # Check 2: description in frontmatter
  has_desc=false
  if echo "$frontmatter" | grep -q '^description:'; then
    has_desc=true
  else
    file_violations="${file_violations}missing description, "
  fi

  # --- Find H1 line (first line starting with "# " after frontmatter) ---
  # Get the line number where the second --- appears (end of frontmatter)
  fm_end=$(head -n 30 "$file" | grep -n '^---$' | sed -n '2p' | cut -d: -f1)
  if [[ -z "$fm_end" ]]; then
    fm_end=0
  fi

  h1_line=""
  h1_lineno=0
  while IFS= read -r line; do
    h1_lineno=$((h1_lineno + 1))
    if [[ $h1_lineno -le $fm_end ]]; then
      continue
    fi
    if [[ "$line" =~ ^#\  ]]; then
      h1_line="$line"
      break
    fi
  done < "$file"

  # Check 3: H1 pattern — should contain parentheses
  has_h1=false
  if [[ -n "$h1_line" ]] && echo "$h1_line" | LC_ALL=en_US.UTF-8 grep -qP '\(.+\)'; then
    has_h1=true
    cat_h1[$category]=$(( ${cat_h1[$category]} + 1 ))
  else
    if [[ -z "$h1_line" ]]; then
      file_violations="${file_violations}missing H1, "
    else
      file_violations="${file_violations}H1 missing bilingual (parentheses), "
    fi
  fi

  # Check 4: Blockquote after H1 (check next 3 non-empty lines)
  has_bq=false
  if [[ $h1_lineno -gt 0 ]]; then
    for offset in 1 2 3; do
      check_line=$(sed -n "$((h1_lineno + offset))p" "$file")
      if [[ -z "$check_line" ]]; then
        continue
      fi
      if [[ "$check_line" =~ ^\> ]]; then
        has_bq=true
      fi
      break
    done
    if $has_bq; then
      cat_bq[$category]=$(( ${cat_bq[$category]} + 1 ))
    else
      file_violations="${file_violations}missing blockquote after H1, "
    fi
  else
    file_violations="${file_violations}missing blockquote (no H1), "
  fi

  # Check 5: 관련 문서 section
  has_related_docs=false
  if grep -q '^## 관련 문서' "$file"; then
    has_related_docs=true
    cat_related_docs[$category]=$(( ${cat_related_docs[$category]} + 1 ))
  else
    file_violations="${file_violations}missing 관련 문서, "
  fi

  # Check 6: 관련 API section (only for required directories)
  has_related_api=false
  needs_api=false

  # Check if path matches a required directory
  if echo "$rel_path" | grep -qE "^($API_REQUIRED_DIRS)(/|$)"; then
    needs_api=true
  fi

  if grep -q '^## 관련 API' "$file"; then
    has_related_api=true
    cat_related_api[$category]=$(( ${cat_related_api[$category]} + 1 ))
  elif $needs_api; then
    file_violations="${file_violations}missing 관련 API, "
  fi

  # Tally pass/fail
  if [[ -z "$file_violations" ]]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    # Remove trailing ", "
    file_violations="${file_violations%, }"
    violations="${violations}  ${rel_path}: ${file_violations}\n"
  fi

done < <(find "$DOCS_DIR" -type f \( -name '*.md' -o -name '*.mdx' \) -print0 | sort -z)

# --- Output ---
echo "=== Docs Style Lint Report ==="
echo "Total files: $total"
echo ""
echo "[PASS] $pass files fully compliant"
echo "[FAIL] $fail files with violations"

if [[ $fail -gt 0 ]]; then
  echo ""
  echo "Violations:"
  echo -e "$violations"
fi

# --- Category Summary (--report) ---
if $SHOW_REPORT; then
  echo "Category Summary:"
  printf "| %-24s | %5s | %4s | %3s | %3s | %8s | %7s | %5s |\n" \
    "Category" "Files" "tags" "H1" "bq" "관련문서" "관련API" "Score"
  printf "|%s|%s|%s|%s|%s|%s|%s|%s|\n" \
    "--------------------------" "-------" "------" "-----" "-----" "----------" "---------" "-------"

  for category in $(echo "${!cat_files[@]}" | tr ' ' '\n' | sort); do
    files=${cat_files[$category]}
    tags=${cat_tags[$category]}
    h1=${cat_h1[$category]}
    bq=${cat_bq[$category]}
    rd=${cat_related_docs[$category]}
    ra=${cat_related_api[$category]}

    # Score = average compliance across 5 checks (tags, h1, bq, related_docs, related_api)
    # related_api only counts if category requires it
    checks=4
    passed=$((tags + h1 + bq + rd))

    if echo "$category" | grep -qE "^($API_REQUIRED_DIRS)$"; then
      checks=5
      passed=$((passed + ra))
    fi

    if [[ $files -gt 0 && $checks -gt 0 ]]; then
      max=$((files * checks))
      score=$(( (passed * 100) / max ))
    else
      score=0
    fi

    printf "| %-24s | %5d | %4d | %3d | %3d | %8d | %7d | %4d%% |\n" \
      "$category" "$files" "$tags" "$h1" "$bq" "$rd" "$ra" "$score"
  done
fi

# Exit code
if [[ $fail -gt 0 ]]; then
  exit 1
fi
exit 0
