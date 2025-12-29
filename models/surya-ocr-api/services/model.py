"""
Surya OCR Model Loading and Utilities
"""
import io
import base64
import logging
from typing import List, Dict, Optional

from PIL import Image, ImageDraw, ImageFont
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def load_surya_models():
    """Load Surya models (v0.17+ API)"""
    from .state import (
        get_surya_ocr,
        set_surya_ocr,
        set_surya_det,
        set_surya_layout,
    )

    if get_surya_ocr() is not None:
        return  # Already loaded

    logger.info("Loading Surya OCR models...")
    try:
        from surya.foundation import FoundationPredictor
        from surya.recognition import RecognitionPredictor
        from surya.detection import DetectionPredictor

        # Load predictors (new API in v0.17+)
        foundation_predictor = FoundationPredictor()
        det_predictor = DetectionPredictor()
        rec_predictor = RecognitionPredictor(foundation_predictor)

        surya_ocr = {
            "det_predictor": det_predictor,
            "rec_predictor": rec_predictor,
            "foundation_predictor": foundation_predictor,
        }
        set_surya_ocr(surya_ocr)
        set_surya_det(det_predictor)

        # Layout detection (optional)
        try:
            from surya.layout import LayoutPredictor
            layout_predictor = LayoutPredictor()
            set_surya_layout(layout_predictor)
        except Exception as e:
            logger.warning(f"Layout model not available: {e}")
            set_surya_layout(None)

        logger.info("Surya models loaded successfully")
    except ImportError as e:
        logger.error(f"Failed to import Surya: {e}")
        raise HTTPException(status_code=500, detail=f"Surya not installed: {e}")


def get_korean_font(size: int = 12) -> ImageFont.FreeTypeFont:
    """Load Korean-supporting font"""
    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def draw_overlay(image: Image.Image, texts: List[Dict]) -> str:
    """Draw OCR results on image and return as base64"""
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)

    # Load Korean font
    font = get_korean_font(12)

    # Colors (purple - Surya theme)
    box_color = (139, 92, 246)  # #8b5cf6
    text_color = (255, 255, 255)

    for text_item in texts:
        bbox = text_item.get("bbox", [])
        text = text_item.get("text", "")
        conf = text_item.get("confidence", 0)

        if len(bbox) >= 4:
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

            # Draw box
            draw.rectangle([x1, y1, x2, y2], outline=box_color, width=2)

            # Draw text label
            label = f"{text} ({conf:.0%})"
            text_bbox = draw.textbbox((x1, y1 - 15), label, font=font)
            draw.rectangle(text_bbox, fill=box_color)
            draw.text((x1, y1 - 15), label, fill=text_color, font=font)

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
