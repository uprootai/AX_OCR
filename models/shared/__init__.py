# Shared schemas and utilities for all API services
from .schemas import (
    StandardHealthResponse,
    create_health_response,
)
from .bbox_utils import (
    BBox,
    xywh_to_xyxy,
    xyxy_to_xywh,
    normalize_bbox,
    calculate_iou,
    match_boxes,
    calculate_metrics,
    convert_yolo_detections,
)

__all__ = [
    # Schemas
    "StandardHealthResponse",
    "create_health_response",
    # BBox utilities
    "BBox",
    "xywh_to_xyxy",
    "xyxy_to_xywh",
    "normalize_bbox",
    "calculate_iou",
    "match_boxes",
    "calculate_metrics",
    "convert_yolo_detections",
]
