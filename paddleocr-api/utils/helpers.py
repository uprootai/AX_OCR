"""
Utility functions for PaddleOCR API
"""
import io
import logging
from typing import List, Dict

import numpy as np
from PIL import Image
import cv2
from fastapi import HTTPException

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
