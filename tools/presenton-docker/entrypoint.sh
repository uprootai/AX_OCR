#!/usr/bin/env bash
set -euo pipefail

TARGET_ROOT="${TARGET_ROOT:-/workspace/startup}"
PRESENTATION_DIR="${TARGET_ROOT}/presentation"

PPTX_SCRIPT="${PRESENTATION_DIR}/generate_pptx.py"
DOCX_SCRIPT="${PRESENTATION_DIR}/generate_실증보고서.py"

if [[ ! -d "${PRESENTATION_DIR}" ]]; then
  echo "[ERROR] presentation directory not found: ${PRESENTATION_DIR}" >&2
  exit 1
fi

run_pptx() {
  if [[ ! -f "${PPTX_SCRIPT}" ]]; then
    echo "[ERROR] missing script: ${PPTX_SCRIPT}" >&2
    exit 1
  fi
  echo "[INFO] Generating PPTX..."
  python "${PPTX_SCRIPT}"
}

run_docx() {
  if [[ ! -f "${DOCX_SCRIPT}" ]]; then
    echo "[ERROR] missing script: ${DOCX_SCRIPT}" >&2
    exit 1
  fi
  echo "[INFO] Generating DOCX..."
  python "${DOCX_SCRIPT}"
}

case "${1:-all}" in
  all)
    run_pptx
    run_docx
    ;;
  pptx)
    run_pptx
    ;;
  docx)
    run_docx
    ;;
  shell)
    exec bash
    ;;
  *)
    echo "Usage: [all|pptx|docx|shell]" >&2
    exit 2
    ;;
esac
