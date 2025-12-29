"""
EasyOCR Model Loading and Utilities
"""
import os
import io
import base64
import logging
from typing import List, Dict

from PIL import Image, ImageDraw
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Configuration
USE_GPU = os.getenv("EASYOCR_GPU", "true").lower() == "true"


def get_use_gpu() -> bool:
    return USE_GPU


def get_easyocr_reader(languages: List[str], gpu: bool = True):
    """Get cached EasyOCR Reader"""
    from .state import get_readers, add_reader
    import easyocr

    lang_key = "_".join(sorted(languages))
    readers = get_readers()

    if lang_key not in readers:
        logger.info(f"Loading EasyOCR reader for languages: {languages}, GPU: {gpu}")
        try:
            reader = easyocr.Reader(languages, gpu=gpu)
            add_reader(lang_key, reader)
            logger.info(f"EasyOCR reader loaded for: {languages}")
        except Exception as e:
            logger.error(f"Failed to load EasyOCR: {e}")
            raise HTTPException(status_code=500, detail=f"EasyOCR load failed: {e}")

    return get_readers()[lang_key]


def draw_overlay(image: Image.Image, texts: List[Dict]) -> str:
    """Draw OCR results on image and return as base64"""
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)

    # Colors (green - EasyOCR theme)
    box_color = (34, 197, 94)  # #22c55e
    text_color = (255, 255, 255)

    for text_item in texts:
        bbox = text_item.get("bbox", [])
        text = text_item.get("text", "")
        conf = text_item.get("confidence", 0)

        if bbox and len(bbox) >= 4:
            # EasyOCR bbox is polygon [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            points = [(int(p[0]), int(p[1])) for p in bbox]

            # Draw polygon
            draw.polygon(points, outline=box_color)

            # Thick border
            for i in range(len(points)):
                draw.line([points[i], points[(i+1) % len(points)]], fill=box_color, width=2)

            # Draw text label
            label = f"{text[:15]}{'...' if len(text) > 15 else ''} ({conf:.0%})"
            label_y = max(0, min(p[1] for p in points) - 15)
            label_x = min(p[0] for p in points)
            text_bbox = draw.textbbox((label_x, label_y), label)
            draw.rectangle(text_bbox, fill=box_color)
            draw.text((label_x, label_y), label, fill=text_color)

    # Convert to Base64
    buffer = io.BytesIO()
    overlay.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()


def is_gpu_available() -> bool:
    """Check if GPU is available"""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False
