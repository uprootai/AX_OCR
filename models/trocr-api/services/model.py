"""
TrOCR Model Loading and Configuration
"""
import os
import logging

logger = logging.getLogger(__name__)

# Hugging Face Transformers
try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    from PIL import Image
    import torch
    TROCR_AVAILABLE = True
except ImportError:
    TROCR_AVAILABLE = False
    TrOCRProcessor = None
    VisionEncoderDecoderModel = None
    Image = None
    torch = None

# Configuration
MODEL_NAME = os.getenv("TROCR_MODEL", "microsoft/trocr-base-printed")
DEVICE = os.getenv("TROCR_DEVICE", "cuda" if torch and torch.cuda.is_available() else "cpu")

# Model type mapping
MODEL_MAP = {
    "printed": "microsoft/trocr-base-printed",
    "handwritten": "microsoft/trocr-base-handwritten",
    "large-printed": "microsoft/trocr-large-printed",
    "large-handwritten": "microsoft/trocr-large-handwritten"
}


def is_trocr_available() -> bool:
    return TROCR_AVAILABLE


def get_device() -> str:
    return DEVICE


def get_model_name() -> str:
    return MODEL_NAME


def set_model_name(name: str):
    global MODEL_NAME
    MODEL_NAME = name


def load_model():
    """Load TrOCR model and processor"""
    if not TROCR_AVAILABLE:
        logger.warning("TrOCR dependencies not installed")
        return None, None

    try:
        logger.info(f"Loading TrOCR model: {MODEL_NAME} on {DEVICE}")
        processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
        model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
        model.to(DEVICE)
        model.eval()
        logger.info("TrOCR model loaded successfully")
        return processor, model
    except Exception as e:
        logger.error(f"Failed to load TrOCR model: {e}")
        return None, None


def clear_cuda_cache():
    """Clear CUDA memory cache"""
    if torch and torch.cuda.is_available():
        torch.cuda.empty_cache()
