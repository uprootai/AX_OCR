"""
Visualization utilities for eDOCr2 v2 API

Updated to match actual data format from ocr_processor.py:
- dimensions: uses 'location' field (array format: [[x1,y1], [x2,y2], ...] or [x,y,w,h])
- gdt: uses 'gdt' key (not 'gdt_symbols')
- tables/possible_text: for text annotations
"""
import cv2
import base64
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def parse_location(location: Any) -> Optional[Tuple[int, int, int, int]]:
    """
    Parse location field to (x, y, width, height) format

    Handles various formats:
    - [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] (polygon)
    - [x, y, w, h] (rectangle)
    - {'x': x, 'y': y, 'width': w, 'height': h} (dict)
    """
    if location is None:
        return None

    try:
        # Handle dict format
        if isinstance(location, dict):
            x = int(location.get('x', 0))
            y = int(location.get('y', 0))
            w = int(location.get('width', 0))
            h = int(location.get('height', 0))
            if w > 0 and h > 0:
                return (x, y, w, h)
            return None

        # Handle list/array format
        if isinstance(location, (list, np.ndarray)):
            arr = np.array(location)

            # Polygon format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            if arr.ndim == 2 and arr.shape[0] >= 4 and arr.shape[1] == 2:
                x_min = int(np.min(arr[:, 0]))
                y_min = int(np.min(arr[:, 1]))
                x_max = int(np.max(arr[:, 0]))
                y_max = int(np.max(arr[:, 1]))
                return (x_min, y_min, x_max - x_min, y_max - y_min)

            # Rectangle format: [x, y, w, h]
            if arr.ndim == 1 and len(arr) == 4:
                return (int(arr[0]), int(arr[1]), int(arr[2]), int(arr[3]))

            # 2-point format: [x1, y1, x2, y2]
            if arr.ndim == 1 and len(arr) >= 4:
                x1, y1, x2, y2 = int(arr[0]), int(arr[1]), int(arr[2]), int(arr[3])
                return (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))

        return None
    except Exception as e:
        logger.debug(f"Failed to parse location: {location}, error: {e}")
        return None


def create_ocr_visualization(
    image_path: str,
    ocr_results: Dict[str, Any]
) -> Optional[str]:
    """
    Create visualization for OCR results

    Args:
        image_path: Path to the image file
        ocr_results: OCR results with dimensions

    Returns:
        Base64 encoded visualization image
    """
    try:
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Failed to read image: {image_path}")
            return None

        # Create overlay with alpha blending
        overlay = img.copy()
        drawn_count = {"dimensions": 0, "gdt": 0, "text": 0}

        # Draw dimensions with bright lime green
        dimensions = ocr_results.get('dimensions', [])
        for dim in dimensions:
            # Try 'location' first (actual format), then 'bbox' (legacy)
            location = dim.get('location') or dim.get('bbox')
            value = dim.get('value', '')
            confidence = dim.get('confidence', 1.0)
            dim_type = dim.get('type', '')

            bbox = parse_location(location)
            if bbox:
                x, y, width, height = bbox

                # Bright lime green for high visibility
                box_color = (50, 255, 50)

                # Draw thicker rectangle
                cv2.rectangle(overlay, (x, y), (x + width, y + height), box_color, 3)

                # Add filled semi-transparent overlay
                temp_overlay = overlay.copy()
                cv2.rectangle(temp_overlay, (x, y), (x + width, y + height), box_color, -1)
                cv2.addWeighted(temp_overlay, 0.15, overlay, 0.85, 0, overlay)

                # Draw text with enhanced background
                if isinstance(confidence, (int, float)):
                    text = f"{value} ({confidence:.2f})"
                else:
                    text = str(value)

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2

                # Get text size
                (text_width, text_height), baseline = cv2.getTextSize(
                    text, font, font_scale, thickness
                )

                # Draw background with padding
                padding = 4
                bg_y = max(y - text_height - padding * 2, 0)
                cv2.rectangle(
                    overlay,
                    (x - padding, bg_y),
                    (x + text_width + padding, y - padding),
                    (0, 180, 0),
                    -1
                )

                # Draw text with white outline for better visibility
                text_pos = (x, y - padding - 2)
                # Black outline
                cv2.putText(overlay, text, text_pos, font, font_scale, (0, 0, 0), thickness + 2)
                # White text
                cv2.putText(overlay, text, text_pos, font, font_scale, (255, 255, 255), thickness)

                drawn_count["dimensions"] += 1

        # Draw GD&T symbols with bright blue/cyan
        # Support both 'gdt' (actual) and 'gdt_symbols' (legacy)
        gdt_symbols = ocr_results.get('gdt', []) or ocr_results.get('gdt_symbols', [])
        for gdt in gdt_symbols:
            location = gdt.get('location') or gdt.get('bbox')
            symbol = gdt.get('type', '') or gdt.get('symbol', '')
            value = gdt.get('value', '')

            bbox = parse_location(location)
            if bbox:
                x, y, width, height = bbox

                # Bright cyan for GD&T
                gdt_color = (255, 200, 0)

                # Draw thicker rectangle
                cv2.rectangle(overlay, (x, y), (x + width, y + height), gdt_color, 3)

                # Add semi-transparent fill
                temp_overlay = overlay.copy()
                cv2.rectangle(temp_overlay, (x, y), (x + width, y + height), gdt_color, -1)
                cv2.addWeighted(temp_overlay, 0.15, overlay, 0.85, 0, overlay)

                # Draw symbol label with background
                display_text = f"{symbol}: {value}" if value else symbol
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                thickness = 1

                (text_width, text_height), _ = cv2.getTextSize(display_text, font, font_scale, thickness)
                bg_y = max(y - text_height - 8, 0)

                cv2.rectangle(overlay, (x, bg_y), (x + text_width + 4, y - 2), gdt_color, -1)

                text_pos = (x + 2, y - 4)
                cv2.putText(overlay, display_text, text_pos, font, font_scale, (0, 0, 0), thickness + 1)
                cv2.putText(overlay, display_text, text_pos, font, font_scale, (255, 255, 255), thickness)

                drawn_count["gdt"] += 1

        # Draw text annotations (possible_text, tables, text_blocks)
        text_items = (
            ocr_results.get('possible_text', []) +
            ocr_results.get('text_blocks', [])
        )
        for text_item in text_items[:20]:  # Limit to first 20 to avoid clutter
            location = text_item.get('location') or text_item.get('bbox')
            text_value = text_item.get('text', '')

            bbox = parse_location(location)
            if bbox:
                x, y, width, height = bbox

                # Bright yellow for text blocks
                text_color = (0, 255, 255)

                # Draw thinner rectangle for text blocks
                cv2.rectangle(overlay, (x, y), (x + width, y + height), text_color, 2)

                # Add very light semi-transparent fill
                temp_overlay = overlay.copy()
                cv2.rectangle(temp_overlay, (x, y), (x + width, y + height), text_color, -1)
                cv2.addWeighted(temp_overlay, 0.08, overlay, 0.92, 0, overlay)

                drawn_count["text"] += 1

        # Add summary info
        summary = f"eDOCr2: {drawn_count['dimensions']} dims, {drawn_count['gdt']} GD&T, {drawn_count['text']} text"
        cv2.rectangle(overlay, (5, 5), (500, 30), (0, 0, 0), -1)
        cv2.putText(
            overlay,
            summary,
            (10, 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1
        )

        # Encode to base64
        _, buffer = cv2.imencode('.jpg', overlay)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        logger.info(f"Created OCR visualization: {drawn_count}")
        return img_base64

    except Exception as e:
        logger.error(f"Failed to create OCR visualization: {e}")
        import traceback
        traceback.print_exc()
        return None
