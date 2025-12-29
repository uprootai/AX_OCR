"""
Upscale Router - ESRGAN Upscaling Endpoints
"""
import io
import time
import logging

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse

from schemas import UpscaleResponse
from services import (
    get_upsampler,
    fallback_upscale,
    is_pillow_available,
    get_device,
    PILLOW_AVAILABLE
)

# Conditional imports
if PILLOW_AVAILABLE:
    from PIL import Image
    import numpy as np
    import cv2

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["upscale"])


@router.get("/info")
async def get_info():
    """API info (BlueprintFlow metadata)"""
    return {
        "name": "ESRGAN Upscaler",
        "type": "esrgan",
        "category": "preprocessing",
        "description": "Real-ESRGAN based 4x image upscaling - preprocessing for low-quality scanned drawings",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "scale",
                "type": "select",
                "default": "4",
                "options": ["2", "4"],
                "description": "Upscale factor (2x or 4x)"
            },
            {
                "name": "denoise_strength",
                "type": "number",
                "default": 0.5,
                "min": 0,
                "max": 1,
                "step": 0.1,
                "description": "Denoise strength (0: none, 1: max)"
            },
            {
                "name": "face_enhance",
                "type": "boolean",
                "default": False,
                "description": "Face enhancement (not needed for drawings)"
            },
            {
                "name": "tile_size",
                "type": "number",
                "default": 0,
                "min": 0,
                "max": 1024,
                "step": 128,
                "description": "Tile size (0: no tiling, 512: for large images)"
            }
        ],
        "inputs": [
            {"name": "image", "type": "Image", "description": "Low-resolution input image"}
        ],
        "outputs": [
            {"name": "image", "type": "Image", "description": "4x upscaled image"}
        ],
        "notes": "Upscaling low-quality scanned drawings before OCR significantly improves accuracy."
    }


@router.post("/upscale")
async def upscale_image(
    file: UploadFile = File(...),
    scale: int = Form(default=4),
    denoise_strength: float = Form(default=0.5),
    tile_size: int = Form(default=0),
    output_format: str = Form(default="png")
):
    """
    Upscale image

    Args:
        file: Input image
        scale: Upscale factor (2 or 4)
        denoise_strength: Denoise strength (0-1)
        tile_size: Tile size for large images (0=no tiling)
        output_format: Output format (png, jpg)
    """
    if not is_pillow_available():
        raise HTTPException(status_code=503, detail="Image processing libraries not available")

    start_time = time.time()
    upsampler = get_upsampler()

    try:
        # Load image
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        # Convert to RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        original_size = {"width": img.size[0], "height": img.size[1]}

        # Convert to numpy array (BGR for OpenCV)
        img_np = np.array(img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # Upscaling
        if upsampler is not None:
            # Use Real-ESRGAN
            try:
                output, _ = upsampler.enhance(img_bgr, outscale=scale)
                method = "Real-ESRGAN"
            except Exception as e:
                logger.warning(f"Real-ESRGAN failed, using fallback: {e}")
                output = fallback_upscale(img_bgr, scale)
                method = "Lanczos4 (fallback)"
        else:
            # Fallback upscaling
            output = fallback_upscale(img_bgr, scale)
            method = "Lanczos4 (fallback)"

        # Denoise (optional)
        if denoise_strength > 0:
            h = int(denoise_strength * 10)  # 0-10 range
            output = cv2.fastNlMeansDenoisingColored(output, None, h, h, 7, 21)

        # Convert to RGB
        output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
        output_img = Image.fromarray(output_rgb)

        upscaled_size = {"width": output_img.size[0], "height": output_img.size[1]}
        processing_time = (time.time() - start_time) * 1000

        # Encode image
        img_buffer = io.BytesIO()
        if output_format.lower() in ("jpg", "jpeg"):
            output_img.save(img_buffer, format="JPEG", quality=95)
            media_type = "image/jpeg"
        else:
            output_img.save(img_buffer, format="PNG")
            media_type = "image/png"

        img_buffer.seek(0)

        logger.info(f"Upscale complete: {original_size} → {upscaled_size}, {method}, {processing_time:.1f}ms")

        return StreamingResponse(
            img_buffer,
            media_type=media_type,
            headers={
                "X-Original-Width": str(original_size["width"]),
                "X-Original-Height": str(original_size["height"]),
                "X-Upscaled-Width": str(upscaled_size["width"]),
                "X-Upscaled-Height": str(upscaled_size["height"]),
                "X-Scale": str(scale),
                "X-Method": method,
                "X-Processing-Time-Ms": str(int(processing_time))
            }
        )

    except Exception as e:
        logger.error(f"Upscale error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upscale/info", response_model=UpscaleResponse)
async def upscale_image_with_info(
    file: UploadFile = File(...),
    scale: int = Form(default=4),
    denoise_strength: float = Form(default=0.5)
):
    """
    Upscale image (returns metadata only, no image saved)
    For testing and info checking
    """
    device = get_device()
    upsampler = get_upsampler()

    if not is_pillow_available():
        return UpscaleResponse(
            success=False,
            original_size={"width": 0, "height": 0},
            upscaled_size={"width": 0, "height": 0},
            scale=scale,
            model="N/A",
            device=device,
            processing_time_ms=0,
            error="Image processing not available"
        )

    start_time = time.time()

    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        original_size = {"width": img.size[0], "height": img.size[1]}
        upscaled_size = {"width": img.size[0] * scale, "height": img.size[1] * scale}

        processing_time = (time.time() - start_time) * 1000

        return UpscaleResponse(
            success=True,
            original_size=original_size,
            upscaled_size=upscaled_size,
            scale=scale,
            model="Real-ESRGAN" if upsampler else "Lanczos4",
            device=device,
            processing_time_ms=processing_time
        )

    except Exception as e:
        return UpscaleResponse(
            success=False,
            original_size={"width": 0, "height": 0},
            upscaled_size={"width": 0, "height": 0},
            scale=scale,
            model="N/A",
            device=device,
            processing_time_ms=(time.time() - start_time) * 1000,
            error=str(e)
        )


@router.post("/enhance")
async def enhance_drawing(
    file: UploadFile = File(...),
    upscale: bool = Form(default=True),
    denoise: bool = Form(default=True),
    sharpen: bool = Form(default=True),
    contrast: bool = Form(default=True)
):
    """
    Drawing-specific enhancement pipeline

    PPT Slide 9 preprocessing pipeline:
    1. ESRGAN upscaling
    2. Denoising
    3. Sharpening
    4. Contrast adjustment (CLAHE)
    """
    if not is_pillow_available():
        raise HTTPException(status_code=503, detail="Image processing not available")

    start_time = time.time()
    upsampler = get_upsampler()

    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        if img.mode != "RGB":
            img = img.convert("RGB")

        img_np = np.array(img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # 1. Upscaling
        if upscale:
            if upsampler:
                img_bgr, _ = upsampler.enhance(img_bgr, outscale=2)  # 2x only (speed)
            else:
                img_bgr = fallback_upscale(img_bgr, 2)

        # 2. Denoising
        if denoise:
            img_bgr = cv2.fastNlMeansDenoisingColored(img_bgr, None, 5, 5, 7, 21)

        # 3. Sharpening
        if sharpen:
            kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
            img_bgr = cv2.filter2D(img_bgr, -1, kernel)

        # 4. CLAHE (contrast enhancement)
        if contrast:
            lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            img_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # Encode result
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        output_img = Image.fromarray(img_rgb)

        img_buffer = io.BytesIO()
        output_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Drawing enhancement complete: {processing_time:.1f}ms")

        return StreamingResponse(
            img_buffer,
            media_type="image/png",
            headers={
                "X-Processing-Time-Ms": str(int(processing_time)),
                "X-Upscale": str(upscale),
                "X-Denoise": str(denoise),
                "X-Sharpen": str(sharpen),
                "X-Contrast": str(contrast)
            }
        )

    except Exception as e:
        logger.error(f"Drawing enhancement error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
