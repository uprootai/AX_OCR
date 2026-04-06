"""Shared backend configuration defaults."""

import os

APP_VERSION = os.getenv("BLUEPRINT_AI_BOM_VERSION", "10.6.0")
DEFAULT_CONFIDENCE_THRESHOLD = float(os.getenv("AX_DEFAULT_CONFIDENCE_THRESHOLD", "0.4"))
