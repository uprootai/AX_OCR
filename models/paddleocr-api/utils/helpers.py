"""
Utility functions for PaddleOCR API
"""
import io
import base64
import logging
from typing import List, Dict, TYPE_CHECKING

import numpy as np
from PIL import Image
import cv2
from fastapi import HTTPException

if TYPE_CHECKING:
    from models.schemas import TextDetection

logger = logging.getLogger(__name__)


def image_to_numpy(image_bytes: bytes) -> np.ndarray:
    """
    Convert image bytes to numpy array

    Args:
        image_bytes: Image file bytes

    Returns:
        Numpy array in BGR format (OpenCV format)

    Raises:
        HTTPException: If image conversion fails
    """
    try:
        # Load as PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA to RGB if needed
        if image.mode == 'RGBA':
            image = image.convert('RGB')

        # Convert to numpy array
        img_array = np.array(image)

        # Convert RGB to BGR (OpenCV format)
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        return img_array

    except Exception as e:
        logger.error(f"Failed to convert image: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")


def bbox_to_position(bbox: List[List[float]]) -> Dict[str, float]:
    """
    Convert bounding box to position dictionary

    Args:
        bbox: Bounding box as [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

    Returns:
        Position dict with {x, y, width, height}
    """
    x_coords = [point[0] for point in bbox]
    y_coords = [point[1] for point in bbox]

    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)

    return {
        "x": x_min,
        "y": y_min,
        "width": x_max - x_min,
        "height": y_max - y_min
    }


def draw_ocr_results(img_array: np.ndarray, detections: List['TextDetection']) -> str:
    """
    Draw OCR detection results on image and return as base64

    Args:
        img_array: Image as numpy array (BGR format)
        detections: List of TextDetection objects

    Returns:
        Base64 encoded image with drawn bboxes and text
    """
    # Create copy to avoid modifying original
    vis_img = img_array.copy()

    # Draw each detection
    for detection in detections:
        bbox = detection.bbox
        text = detection.text
        confidence = detection.confidence

        # Convert bbox to integer points
        points = np.array(bbox, dtype=np.int32).reshape((-1, 1, 2))

        # Draw bounding box (cyan color)
        cv2.polylines(vis_img, [points], isClosed=True, color=(255, 255, 0), thickness=2)

        # Draw text label with background
        label = f"{text} ({confidence:.2f})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1

        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        # Draw filled rectangle for text background
        top_left = (int(bbox[0][0]), int(bbox[0][1]) - text_height - 5)
        bottom_right = (int(bbox[0][0]) + text_width, int(bbox[0][1]))
        cv2.rectangle(vis_img, top_left, bottom_right, (255, 255, 0), -1)

        # Draw text
        text_position = (int(bbox[0][0]), int(bbox[0][1]) - 5)
        cv2.putText(vis_img, label, text_position, font, font_scale, (0, 0, 0), thickness)

    # Convert to base64
    _, buffer = cv2.imencode('.jpg', vis_img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    return img_base64
