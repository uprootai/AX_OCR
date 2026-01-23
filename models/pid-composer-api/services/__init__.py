"""
PID Composer Services
"""
from .composer_service import (
    compose_layers,
    ComposerStyle,
    ComposerResult,
    LayerType
)
from .svg_generator import generate_svg_overlay
from .image_renderer import render_to_image
from .svg_common import (
    escape_html,
    create_svg_header,
    create_svg_footer,
    create_label_element,
    get_color,
    DEFAULT_COLORS,
)

__all__ = [
    "compose_layers",
    "ComposerStyle",
    "ComposerResult",
    "LayerType",
    "generate_svg_overlay",
    "render_to_image",
    # svg_common exports
    "escape_html",
    "create_svg_header",
    "create_svg_footer",
    "create_label_element",
    "get_color",
    "DEFAULT_COLORS",
]
