"""
DocTR Model Loading and Utilities
"""
import io
import base64
import logging
from typing import List, Dict

from PIL import Image, ImageDraw
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def load_doctr_model():
    """Load DocTR model"""
    from .state import get_doctr_model, set_doctr_model

    if get_doctr_model() is not None:
        return  # Already loaded

    logger.info("Loading DocTR model...")
    try:
        from doctr.io import DocumentFile
        from doctr.models import ocr_predictor

        # Load pretrained model
        doctr_model = {
            "predictor": ocr_predictor(pretrained=True),
            "DocumentFile": DocumentFile,
        }
        set_doctr_model(doctr_model)
        logger.info("DocTR model loaded successfully")
    except ImportError as e:
        logger.error(f"Failed to import DocTR: {e}")
        raise HTTPException(status_code=500, detail=f"DocTR not installed: {e}")


def draw_overlay(image: Image.Image, texts: List[Dict]) -> str:
    """Draw OCR results on image and return as base64"""
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    width, height = image.size

    # Colors (cyan - DocTR theme)
    box_color = (14, 165, 233)  # #0ea5e9
    text_color = (255, 255, 255)

    for text_item in texts:
        bbox = text_item.get("bbox", [])
        text = text_item.get("text", "")
        conf = text_item.get("confidence", 0)

        if len(bbox) >= 2:
            # DocTR bbox is normalized [[x1,y1], [x2,y2]] or (x1,y1,x2,y2)
            if isinstance(bbox[0], (list, tuple)):
                x1 = int(bbox[0][0] * width)
                y1 = int(bbox[0][1] * height)
                x2 = int(bbox[1][0] * width)
                y2 = int(bbox[1][1] * height)
            else:
                x1 = int(bbox[0] * width)
                y1 = int(bbox[1] * height)
                x2 = int(bbox[2] * width) if len(bbox) > 2 else x1
                y2 = int(bbox[3] * height) if len(bbox) > 3 else y1

            # Draw box
            draw.rectangle([x1, y1, x2, y2], outline=box_color, width=2)

            # Draw text label
            label = f"{text[:15]}{'...' if len(text) > 15 else ''} ({conf:.0%})"
            label_y = max(0, y1 - 15)
            text_bbox = draw.textbbox((x1, label_y), label)
            draw.rectangle(text_bbox, fill=box_color)
            draw.text((x1, label_y), label, fill=text_color)

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
