"""
Gateway API Utilities

Image processing, filtering, progress tracking utilities
"""
from .progress import ProgressTracker, progress_store
from .filters import is_false_positive
from .image_utils import (
    pdf_to_image,
    calculate_bbox_iou,
    format_class_name,
    redraw_yolo_visualization,
    upscale_image_region,
    crop_bbox,
    CLASS_DISPLAY_NAMES
)
from .helpers import match_yolo_with_ocr
from .visualization import (
    create_ocr_visualization,
    create_edgnet_visualization,
    create_ensemble_visualization
)
from .spec_loader import (
    SpecLoader,
    add_meta_endpoint,
    get_api_registry,
    load_spec,
    get_spec_parameter
)
from .file_validator import (
    validate_file,
    validate_image_file,
    validate_extension,
    validate_magic_bytes,
    get_file_info,
    ALLOWED_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS
)

__all__ = [
    # Progress tracking
    "ProgressTracker",
    "progress_store",
    # Filters
    "is_false_positive",
    # Image processing
    "pdf_to_image",
    "calculate_bbox_iou",
    "format_class_name",
    "redraw_yolo_visualization",
    "upscale_image_region",
    "crop_bbox",
    "CLASS_DISPLAY_NAMES",
    # Helpers
    "match_yolo_with_ocr",
    # Visualization
    "create_ocr_visualization",
    "create_edgnet_visualization",
    "create_ensemble_visualization",
    # Spec loader
    "SpecLoader",
    "add_meta_endpoint",
    "get_api_registry",
    "load_spec",
    "get_spec_parameter",
    # File validation
    "validate_file",
    "validate_image_file",
    "validate_extension",
    "validate_magic_bytes",
    "get_file_info",
    "ALLOWED_EXTENSIONS",
    "ALLOWED_IMAGE_EXTENSIONS"
]
