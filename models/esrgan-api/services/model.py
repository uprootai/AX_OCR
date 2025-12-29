"""
ESRGAN Model Service
Model loading, inference, and image processing
"""
import os
import logging
from typing import Optional

# Real-ESRGAN
try:
    from PIL import Image
    import numpy as np
    import cv2
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    Image = None
    np = None
    cv2 = None

# Real-ESRGAN (optional - falls back to basic upscaling)
try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    import torch
    REALESRGAN_AVAILABLE = True
except ImportError:
    REALESRGAN_AVAILABLE = False
    torch = None

logger = logging.getLogger(__name__)

# Configuration
MODEL_PATH = os.getenv("ESRGAN_MODEL_PATH", "weights/RealESRGAN_x4plus.pth")
DEVICE = os.getenv("ESRGAN_DEVICE", "cuda" if torch and torch.cuda.is_available() else "cpu")


def load_model():
    """Load Real-ESRGAN model"""
    if not REALESRGAN_AVAILABLE:
        logger.warning("Real-ESRGAN not installed, using fallback upscaling")
        return None

    try:
        logger.info(f"Loading Real-ESRGAN model on {DEVICE}")

        # RRDBNet model definition (x4 upscaling)
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4
        )

        # Find model weights
        if os.path.exists(MODEL_PATH):
            model_path = MODEL_PATH
        else:
            # Search in default paths
            default_paths = [
                "weights/RealESRGAN_x4plus.pth",
                "/app/weights/RealESRGAN_x4plus.pth",
                os.path.expanduser("~/.cache/realesrgan/RealESRGAN_x4plus.pth")
            ]
            model_path = None
            for path in default_paths:
                if os.path.exists(path):
                    model_path = path
                    break

            if model_path is None:
                logger.warning("Model weights not found, will use fallback upscaling")
                return None

        upsampler = RealESRGANer(
            scale=4,
            model_path=model_path,
            model=model,
            tile=0,  # 0: no tile, 512: 512x512 tiles
            tile_pad=10,
            pre_pad=0,
            half=True if DEVICE == "cuda" else False,
            device=DEVICE
        )

        logger.info("Real-ESRGAN model loaded successfully")
        return upsampler

    except Exception as e:
        logger.error(f"Failed to load Real-ESRGAN: {e}")
        return None


def fallback_upscale(image, scale: int = 4):
    """
    Fallback upscaling (when Real-ESRGAN unavailable)
    Uses OpenCV INTER_LANCZOS4
    """
    if cv2 is None:
        raise RuntimeError("OpenCV not available")
    h, w = image.shape[:2]
    new_h, new_w = h * scale, w * scale
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)


def is_pillow_available() -> bool:
    """Check if Pillow is available"""
    return PILLOW_AVAILABLE


def is_realesrgan_available() -> bool:
    """Check if Real-ESRGAN is available"""
    return REALESRGAN_AVAILABLE


def get_device() -> str:
    """Get current device"""
    return DEVICE
