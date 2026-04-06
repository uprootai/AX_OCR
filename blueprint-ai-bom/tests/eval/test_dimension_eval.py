from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from run_dimension_eval import CASES_FILE, DEFAULT_BASE_URL, _resolve_case_image_path

pytestmark = pytest.mark.eval


def _healthcheck(base_url: str) -> bool:
    try:
        response = httpx.get(f"{base_url}/health", timeout=5.0)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


def test_dimension_eval_cli(tmp_path: Path) -> None:
    base_url = os.environ.get("DIMENSION_EVAL_BASE_URL", DEFAULT_BASE_URL)
    if not _healthcheck(base_url):
        pytest.skip(f"Dimension eval requires a running BOM backend API server: {base_url}")

    cases = json.loads(CASES_FILE.read_text())
    missing_images = [
        str(_resolve_case_image_path(case, CASES_FILE.parent))
        for case in cases
        if not _resolve_case_image_path(case, CASES_FILE.parent).exists()
    ]
    if missing_images:
        pytest.skip(f"Dimension eval assets are missing: {missing_images[0]}")

    output_path = tmp_path / "dimension_eval_results.json"
    script_path = Path(__file__).with_name("run_dimension_eval.py")
    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--base-url",
            base_url,
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert output_path.exists()
