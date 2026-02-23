"""Customer Onboarding - Configuration & Presets

프로젝트 타입별 고객 프리셋, OnboardConfig dataclass, YAML/JSON 로더.

Usage:
    from onboard_config import OnboardConfig, CUSTOMER_PRESETS, load_config
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger("onboard")


# ──────────────────────────────────────────────
# Project Type Presets (mirrors PROJECT_TYPE_PRESETS in project_service.py)
# ──────────────────────────────────────────────

PROJECT_TYPE_FEATURES = {
    "bom_quotation": {
        "drawing_type": "dimension_bom",
        "features": [
            "dimension_ocr",
            "table_extraction",
            "bom_generation",
            "title_block_ocr",
        ],
    },
    "pid_detection": {
        "drawing_type": "pid",
        "features": [
            "symbol_detection",
            "pid_connectivity",
            "gt_comparison",
        ],
    },
    "general": {
        "drawing_type": "auto",
        "features": [
            "symbol_detection",
            "dimension_ocr",
            "title_block_ocr",
        ],
    },
}


# ──────────────────────────────────────────────
# Customer Presets
# ──────────────────────────────────────────────

CUSTOMER_PRESETS = {
    "techcross_bwms": {
        "customer": "TECHCROSS",
        "project_type": "bom_quotation",
        "description": "TECHCROSS BWMS 도면 견적 프로젝트",
        "features": [
            "dimension_ocr",
            "table_extraction",
            "bom_generation",
            "title_block_ocr",
        ],
        "export_format": "pdf",
        "verify": True,
        "verify_item_type": "both",
    },
    "dse_bearing": {
        "customer": "DSE",
        "project_type": "bom_quotation",
        "description": "DSE Bearing 도면 견적 프로젝트",
        "features": [
            "dimension_ocr",
            "table_extraction",
            "bom_generation",
            "title_block_ocr",
        ],
        "export_format": "excel",
        "verify": True,
        "verify_item_type": "dimension",
    },
    "pid_standard": {
        "customer": "",
        "project_type": "pid_detection",
        "description": "P&ID 표준 분석 프로젝트",
        "features": [
            "symbol_detection",
            "pid_connectivity",
            "gt_comparison",
        ],
        "export_format": "pdf",
        "verify": True,
        "verify_item_type": "symbol",
    },
    "general_manufacturing": {
        "customer": "",
        "project_type": "general",
        "description": "일반 제조 도면 분석 프로젝트",
        "features": [
            "symbol_detection",
            "dimension_ocr",
            "title_block_ocr",
        ],
        "export_format": "pdf",
        "verify": False,
        "verify_item_type": "both",
    },
}


# ──────────────────────────────────────────────
# OnboardConfig Dataclass
# ──────────────────────────────────────────────

@dataclass
class OnboardConfig:
    """Onboarding pipeline configuration."""

    # Project info
    name: str = ""
    customer: str = ""
    project_type: str = "general"  # bom_quotation | pid_detection | general
    description: str = ""

    # BOM paths (bom_quotation only)
    bom_pdf_path: str = ""
    drawing_folder: str = ""

    # Analysis settings
    features: List[str] = field(default_factory=list)
    template_name: str = ""
    root_drawing_number: str = ""
    force_rerun: bool = False

    # Verification options
    verify: bool = False
    verify_item_type: str = "both"  # symbol | dimension | both
    verify_threshold: float = 0.9
    verify_l1_only: bool = False

    # Export settings
    export_format: str = "pdf"  # pdf | excel
    export_notes: str = ""

    # Control
    dry_run: bool = False
    resume_project_id: str = ""
    resume_from_step: int = 0
    api_base: str = "http://localhost:5020"
    verbose: bool = False

    # Preset
    preset: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────
# Config Loaders
# ──────────────────────────────────────────────

def load_config(path: str) -> OnboardConfig:
    """Load OnboardConfig from a YAML or JSON file.

    Preset fields are applied first, then file values override.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")

    raw: dict = {}
    if file_path.suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise ImportError("YAML 설정 파일을 사용하려면 pyyaml을 설치하세요: pip install pyyaml")
        with open(file_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    elif file_path.suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raise ValueError(f"지원하지 않는 설정 파일 형식입니다: {file_path.suffix} (yaml, json만 지원)")

    # Apply preset first
    config = OnboardConfig()
    preset_name = raw.pop("preset", "")
    if preset_name:
        _apply_preset(config, preset_name)

    # Override with file values
    for key, value in raw.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config


def config_from_args(args) -> OnboardConfig:
    """Convert argparse.Namespace → OnboardConfig."""
    config = OnboardConfig()

    # Apply preset first
    preset_name = getattr(args, "preset", "")
    if preset_name:
        _apply_preset(config, preset_name)

    # Override with CLI args (skip None/default values)
    arg_map = {
        "name": "name",
        "customer": "customer",
        "type": "project_type",
        "description": "description",
        "bom_pdf": "bom_pdf_path",
        "drawing_folder": "drawing_folder",
        "features": "features",
        "template": "template_name",
        "root_drawing": "root_drawing_number",
        "force_rerun": "force_rerun",
        "verify": "verify",
        "verify_item_type": "verify_item_type",
        "verify_threshold": "verify_threshold",
        "verify_l1_only": "verify_l1_only",
        "export_format": "export_format",
        "export_notes": "export_notes",
        "dry_run": "dry_run",
        "resume_project": "resume_project_id",
        "resume_from": "resume_from_step",
        "api_base": "api_base",
        "verbose": "verbose",
    }

    for arg_name, config_name in arg_map.items():
        value = getattr(args, arg_name, None)
        if value is not None and value != "" and value != []:
            setattr(config, config_name, value)

    return config


def _apply_preset(config: OnboardConfig, preset_name: str):
    """Apply a customer preset to config."""
    preset = CUSTOMER_PRESETS.get(preset_name)
    if not preset:
        available = ", ".join(CUSTOMER_PRESETS.keys())
        raise ValueError(f"알 수 없는 프리셋: '{preset_name}' (사용 가능: {available})")

    config.preset = preset_name
    config.customer = preset.get("customer", config.customer)
    config.project_type = preset.get("project_type", config.project_type)
    config.description = preset.get("description", config.description)
    config.features = preset.get("features", config.features)
    config.export_format = preset.get("export_format", config.export_format)
    config.verify = preset.get("verify", config.verify)
    config.verify_item_type = preset.get("verify_item_type", config.verify_item_type)


# ──────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────

def validate_config(config: OnboardConfig) -> List[str]:
    """Validate config and return list of error messages (empty = valid)."""
    errors: List[str] = []

    # Required fields
    if not config.name:
        errors.append("프로젝트 이름(--name)은 필수입니다")
    if not config.customer:
        errors.append("고객사명(--customer)은 필수입니다")

    # Project type
    valid_types = ("bom_quotation", "pid_detection", "general")
    if config.project_type not in valid_types:
        errors.append(f"프로젝트 타입이 유효하지 않습니다: {config.project_type} (허용: {valid_types})")

    # BOM-specific validation
    if config.project_type == "bom_quotation":
        if config.bom_pdf_path and not Path(config.bom_pdf_path).exists():
            errors.append(f"BOM PDF 파일을 찾을 수 없습니다: {config.bom_pdf_path}")
        if config.drawing_folder and not Path(config.drawing_folder).is_dir():
            errors.append(f"도면 폴더를 찾을 수 없습니다: {config.drawing_folder}")

    # Features validation
    valid_features = {
        "dimension_ocr", "table_extraction", "bom_generation",
        "title_block_ocr", "symbol_detection", "pid_connectivity",
        "gt_comparison",
    }
    for feat in config.features:
        if feat not in valid_features:
            errors.append(f"알 수 없는 feature: '{feat}' (허용: {sorted(valid_features)})")

    # Export format
    if config.export_format not in ("pdf", "excel"):
        errors.append(f"내보내기 형식이 유효하지 않습니다: {config.export_format} (허용: pdf, excel)")

    # Verify item type
    if config.verify and config.verify_item_type not in ("symbol", "dimension", "both"):
        errors.append(f"검증 항목 타입이 유효하지 않습니다: {config.verify_item_type}")

    # Resume validation
    if config.resume_from_step and not config.resume_project_id:
        errors.append("--resume-from은 --resume-project와 함께 사용해야 합니다")
    if config.resume_from_step < 0 or config.resume_from_step > 8:
        errors.append(f"resume-from 단계가 유효하지 않습니다: {config.resume_from_step} (0-8)")

    return errors


def list_presets() -> str:
    """Format preset list for display."""
    lines = [
        "Available Customer Presets:",
        "=" * 60,
    ]
    for name, preset in CUSTOMER_PRESETS.items():
        lines.append(f"\n  {name}")
        lines.append(f"    Customer:     {preset.get('customer', '-')}")
        lines.append(f"    Project Type: {preset['project_type']}")
        lines.append(f"    Features:     {', '.join(preset['features'])}")
        lines.append(f"    Export:       {preset.get('export_format', 'pdf')}")
        lines.append(f"    Verify:       {preset.get('verify', False)}")
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)
