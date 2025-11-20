"""
Utility functions for YOLO API
"""
from typing import List, Dict
import cv2
import numpy as np

# Class name mappings
CLASS_NAMES = {
    0: 'diameter_dim',
    1: 'linear_dim',
    2: 'radius_dim',
    3: 'angular_dim',
    4: 'chamfer_dim',
    5: 'tolerance_dim',
    6: 'reference_dim',
    7: 'flatness',
    8: 'cylindricity',
    9: 'position',
    10: 'perpendicularity',
    11: 'parallelism',
    12: 'surface_roughness',
    13: 'text_block'
}

CLASS_DISPLAY_NAMES = {
    'diameter_dim': 'Diameter (Ø)',
    'linear_dim': 'Linear Dim',
    'radius_dim': 'Radius (R)',
    'angular_dim': 'Angular',
    'chamfer_dim': 'Chamfer',
    'tolerance_dim': 'Tolerance',
    'reference_dim': 'Reference',
    'flatness': 'Flatness (⏥)',
    'cylindricity': 'Cylindricity (⌭)',
    'position': 'Position (⌖)',
    'perpendicularity': 'Perpendicular (⊥)',
    'parallelism': 'Parallel (∥)',
    'surface_roughness': 'Roughness (Ra)',
    'text_block': 'Text'
}


def format_class_name(class_name: str) -> str:
    """
    Convert class name to human-readable format

    Args:
        class_name: Internal class name

    Returns:
        Human-readable class name
    """
    return CLASS_DISPLAY_NAMES.get(class_name, class_name)


def calculate_iou(det1, det2) -> float:
    """
    Calculate IoU between two bounding boxes

    Args:
        det1: First detection object with bbox dict
        det2: Second detection object with bbox dict

    Returns:
        IoU value (0-1)
    """
    x1_1 = det1.bbox['x']
    y1_1 = det1.bbox['y']
    x2_1 = x1_1 + det1.bbox['width']
    y2_1 = y1_1 + det1.bbox['height']

    x1_2 = det2.bbox['x']
    y1_2 = det2.bbox['y']
    x2_2 = x1_2 + det2.bbox['width']
    y2_2 = y1_2 + det2.bbox['height']

    # Intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    if x2_i < x1_i or y2_i < y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)

    # Union
    area1 = det1.bbox['width'] * det1.bbox['height']
    area2 = det2.bbox['width'] * det2.bbox['height']
    union = area1 + area2 - intersection

    if union == 0:
        return 0.0

    return intersection / union


def draw_detections_on_image(image: np.ndarray, detections: List) -> np.ndarray:
    """
    Draw detection results on image with legend

    Args:
        image: numpy array (BGR)
        detections: List of Detection objects

    Returns:
        Annotated image
    """
    annotated_img = image.copy()

    # Define colors (BGR)
    colors = {
        'dimension': (255, 100, 0),     # Blue
        'gdt': (0, 255, 100),           # Green
        'surface': (0, 165, 255),       # Orange
        'text': (255, 255, 0)           # Cyan
    }

    for det in detections:
        bbox = det.bbox
        x1 = bbox['x']
        y1 = bbox['y']
        x2 = x1 + bbox['width']
        y2 = y1 + bbox['height']

        # Select color
        if det.class_id <= 6:
            color = colors['dimension']
        elif det.class_id <= 11:
            color = colors['gdt']
        elif det.class_id == 12:
            color = colors['surface']
        else:
            color = colors['text']

        # Draw box
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)

        # Draw label with OCR value if available
        display_name = format_class_name(det.class_name)
        if det.value:
            label = f"{display_name}: {det.value} ({det.confidence:.2f})"
        else:
            label = f"{display_name} ({det.confidence:.2f})"

        (label_w, label_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )

        # Label background
        cv2.rectangle(
            annotated_img,
            (x1, y1 - label_h - 12),
            (x1 + label_w + 10, y1),
            color,
            -1
        )

        # Label text
        cv2.putText(
            annotated_img,
            label,
            (x1 + 5, y1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

    # Add legend
    legend_height = 140
    legend_width = 280
    legend_x = 10
    legend_y = 10

    # Legend background
    overlay = annotated_img.copy()
    cv2.rectangle(overlay, (legend_x, legend_y),
                  (legend_x + legend_width, legend_y + legend_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, annotated_img, 0.3, 0, annotated_img)

    # Legend border
    cv2.rectangle(annotated_img, (legend_x, legend_y),
                  (legend_x + legend_width, legend_y + legend_height), (255, 255, 255), 2)

    # Legend title
    cv2.putText(annotated_img, "Detection Classes", (legend_x + 10, legend_y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Legend items
    legend_items = [
        ("Dimensions", colors['dimension']),
        ("GD&T Symbols", colors['gdt']),
        ("Surface Roughness", colors['surface']),
        ("Text Blocks", colors['text'])
    ]

    y_offset = legend_y + 50
    for label, color in legend_items:
        # Color box
        cv2.rectangle(annotated_img, (legend_x + 10, y_offset - 10),
                     (legend_x + 30, y_offset + 5), color, -1)
        cv2.rectangle(annotated_img, (legend_x + 10, y_offset - 10),
                     (legend_x + 30, y_offset + 5), (255, 255, 255), 1)
        # Label
        cv2.putText(annotated_img, label, (legend_x + 40, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 25

    return annotated_img
