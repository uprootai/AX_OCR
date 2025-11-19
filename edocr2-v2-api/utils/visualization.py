"""
Visualization utilities for eDOCr2 v2 API
"""
import cv2
import base64
import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


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

        # Draw dimensions with bright lime green
        dimensions = ocr_results.get('dimensions', [])
        for dim in dimensions:
            bbox = dim.get('bbox')
            value = dim.get('value', '')
            confidence = dim.get('confidence', 0)

            if bbox:
                x = bbox.get('x', 0)
                y = bbox.get('y', 0)
                width = bbox.get('width', 0)
                height = bbox.get('height', 0)

                # Bright lime green for high visibility
                box_color = (50, 255, 50)

                # Draw thicker rectangle
                cv2.rectangle(overlay, (x, y), (x + width, y + height), box_color, 3)

                # Add filled semi-transparent overlay
                temp_overlay = overlay.copy()
                cv2.rectangle(temp_overlay, (x, y), (x + width, y + height), box_color, -1)
                cv2.addWeighted(temp_overlay, 0.15, overlay, 0.85, 0, overlay)

                # Draw text with enhanced background
                text = f"{value} ({confidence:.2f})"
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

        # Draw GD&T symbols with bright blue/cyan
        gdt_symbols = ocr_results.get('gdt_symbols', [])
        for gdt in gdt_symbols:
            bbox = gdt.get('bbox')
            symbol = gdt.get('symbol', '')

            if bbox:
                x = bbox.get('x', 0)
                y = bbox.get('y', 0)
                width = bbox.get('width', 0)
                height = bbox.get('height', 0)

                # Bright cyan for GD&T
                gdt_color = (255, 200, 0)

                # Draw thicker rectangle
                cv2.rectangle(overlay, (x, y), (x + width, y + height), gdt_color, 3)

                # Add semi-transparent fill
                temp_overlay = overlay.copy()
                cv2.rectangle(temp_overlay, (x, y), (x + width, y + height), gdt_color, -1)
                cv2.addWeighted(temp_overlay, 0.15, overlay, 0.85, 0, overlay)

                # Draw symbol label with background
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                thickness = 1

                (text_width, text_height), _ = cv2.getTextSize(symbol, font, font_scale, thickness)
                bg_y = max(y - text_height - 8, 0)

                cv2.rectangle(overlay, (x, bg_y), (x + text_width + 4, y - 2), gdt_color, -1)

                text_pos = (x + 2, y - 4)
                cv2.putText(overlay, symbol, text_pos, font, font_scale, (0, 0, 0), thickness + 1)
                cv2.putText(overlay, symbol, text_pos, font, font_scale, (255, 255, 255), thickness)

        # Draw text blocks with bright yellow
        text_blocks = ocr_results.get('text_blocks', [])
        for text_block in text_blocks[:10]:  # Limit to first 10 to avoid clutter
            bbox = text_block.get('bbox')

            if bbox:
                x = bbox.get('x', 0)
                y = bbox.get('y', 0)
                width = bbox.get('width', 0)
                height = bbox.get('height', 0)

                # Bright yellow for text blocks
                text_color = (0, 255, 255)

                # Draw thinner rectangle for text blocks
                cv2.rectangle(overlay, (x, y), (x + width, y + height), text_color, 2)

                # Add very light semi-transparent fill
                temp_overlay = overlay.copy()
                cv2.rectangle(temp_overlay, (x, y), (x + width, y + height), text_color, -1)
                cv2.addWeighted(temp_overlay, 0.08, overlay, 0.92, 0, overlay)

        # Add summary info
        summary = f"OCR: {len(dimensions)} dims, {len(gdt_symbols)} GD&T, {len(text_blocks)} text"
        cv2.rectangle(overlay, (5, 5), (600, 30), (0, 0, 0), -1)
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

        logger.info(f"Created OCR visualization with {len(dimensions)} dimensions")
        return img_base64

    except Exception as e:
        logger.error(f"Failed to create OCR visualization: {e}")
        return None
