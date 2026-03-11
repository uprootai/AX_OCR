"""Spec cache tests for APIRegistry."""

import time
from pathlib import Path
from unittest.mock import patch

import api_registry
import yaml

from api_registry import APIRegistry


def _write_spec(spec_file: Path, name: str):
    spec_file.write_text(
        f"""
apiVersion: v1
kind: APISpec
metadata:
  id: test-api
  name: {name}
  version: 1.0.0
  port: 5000
server:
  endpoint: /api/v1/process
  method: POST
blueprintflow:
  category: detection
  color: "#10b981"
  icon: Box
""".strip(),
        encoding="utf-8",
    )


def test_get_all_specs_uses_cache_until_files_change(tmp_path):
    original_spec_dir = api_registry.SPEC_DIR
    api_registry.SPEC_DIR = tmp_path

    try:
        spec_file = tmp_path / "test-api.yaml"
        _write_spec(spec_file, "Initial API")
        registry = APIRegistry()

        with patch("api_registry.yaml.safe_load", wraps=yaml.safe_load) as mock_safe_load:
            first_specs = registry.get_all_specs()
            second_specs = registry.get_all_specs()

            assert first_specs["test-api"]["metadata"]["name"] == "Initial API"
            assert second_specs["test-api"]["metadata"]["name"] == "Initial API"
            assert mock_safe_load.call_count == 1

            time.sleep(0.001)
            _write_spec(spec_file, "Updated API")

            refreshed_specs = registry.get_all_specs()

            assert refreshed_specs["test-api"]["metadata"]["name"] == "Updated API"
            assert mock_safe_load.call_count == 2
    finally:
        api_registry.SPEC_DIR = original_spec_dir
