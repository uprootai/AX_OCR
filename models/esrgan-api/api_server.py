"""
ESRGAN (Real-ESRGAN) API Server
PPT 슬라이드 9 [HOW-1] 전처리 고도화의 ESRGAN 업스케일링

저해상도/저품질 스캔 도면을 4x 업스케일링하여 OCR 정확도 향상
"""
import os
import io
import logging
import time
from datetime import datetime
from typing import Optional
import tempfile

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

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

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ESRGAN_API_PORT = int(os.getenv("ESRGAN_API_PORT", "5010"))
MODEL_PATH = os.getenv("ESRGAN_MODEL_PATH", "weights/RealESRGAN_x4plus.pth")
DEVICE = os.getenv("ESRGAN_DEVICE", "cuda" if torch and torch.cuda.is_available() else "cpu")

# Global model instance
upsampler = None

app = FastAPI(
    title="ESRGAN API",
    description="Real-ESRGAN 기반 이미지 업스케일링 API - 저품질 도면 전처리",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# Schemas
# =====================

class UpscaleResponse(BaseModel):
    success: bool
    original_size: dict
    upscaled_size: dict
    scale: int
    model: str
    device: str
    processing_time_ms: float
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    realesrgan_available: bool
    model_loaded: bool
    device: str
    timestamp: str


# =====================
# Model Loading
# =====================

def load_model():
    """Real-ESRGAN 모델 로드"""
    global upsampler

    if not REALESRGAN_AVAILABLE:
        logger.warning("Real-ESRGAN not installed, using fallback upscaling")
        return False

    try:
        logger.info(f"Loading Real-ESRGAN model on {DEVICE}")

        # RRDBNet 모델 정의 (x4 업스케일링)
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4
        )

        # 모델 가중치 경로 확인
        if os.path.exists(MODEL_PATH):
            model_path = MODEL_PATH
        else:
            # 기본 경로에서 찾기
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
                return False

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
        return True

    except Exception as e:
        logger.error(f"Failed to load Real-ESRGAN: {e}")
        return False


def fallback_upscale(image: np.ndarray, scale: int = 4) -> np.ndarray:
    """
    폴백 업스케일링 (Real-ESRGAN 사용 불가 시)
    OpenCV의 INTER_LANCZOS4 사용
    """
    h, w = image.shape[:2]
    new_h, new_w = h * scale, w * scale
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로드 시도"""
    load_model()


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="ESRGAN API",
        version="1.0.0",
        realesrgan_available=REALESRGAN_AVAILABLE,
        model_loaded=upsampler is not None,
        device=DEVICE,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "name": "ESRGAN Upscaler",
        "type": "esrgan",
        "category": "preprocessing",
        "description": "Real-ESRGAN 기반 4x 이미지 업스케일링 - 저품질 스캔 도면 전처리",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "scale",
                "type": "select",
                "default": "4",
                "options": ["2", "4"],
                "description": "업스케일 배율 (2x 또는 4x)"
            },
            {
                "name": "denoise_strength",
                "type": "number",
                "default": 0.5,
                "min": 0,
                "max": 1,
                "step": 0.1,
                "description": "노이즈 제거 강도 (0: 없음, 1: 최대)"
            },
            {
                "name": "face_enhance",
                "type": "boolean",
                "default": False,
                "description": "얼굴 향상 (도면에는 불필요)"
            },
            {
                "name": "tile_size",
                "type": "number",
                "default": 0,
                "min": 0,
                "max": 1024,
                "step": 128,
                "description": "타일 크기 (0: 타일 없음, 512: 대용량 이미지용)"
            }
        ],
        "inputs": [
            {"name": "image", "type": "Image", "description": "저해상도 입력 이미지"}
        ],
        "outputs": [
            {"name": "image", "type": "Image", "description": "4x 업스케일된 이미지"}
        ],
        "notes": "저품질 스캔 도면을 업스케일링한 후 OCR을 수행하면 정확도가 크게 향상됩니다."
    }


@app.post("/api/v1/upscale")
async def upscale_image(
    file: UploadFile = File(...),
    scale: int = Form(default=4),
    denoise_strength: float = Form(default=0.5),
    tile_size: int = Form(default=0),
    output_format: str = Form(default="png")
):
    """
    이미지 업스케일링

    Args:
        file: 입력 이미지
        scale: 업스케일 배율 (2 또는 4)
        denoise_strength: 노이즈 제거 강도 (0-1)
        tile_size: 타일 크기 (큰 이미지 처리용, 0=타일 없음)
        output_format: 출력 형식 (png, jpg)
    """
    if not PILLOW_AVAILABLE:
        raise HTTPException(status_code=503, detail="Image processing libraries not available")

    start_time = time.time()

    try:
        # 이미지 로드
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        # RGB 변환
        if img.mode != "RGB":
            img = img.convert("RGB")

        original_size = {"width": img.size[0], "height": img.size[1]}

        # numpy 배열로 변환 (BGR for OpenCV)
        img_np = np.array(img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # 업스케일링
        if upsampler is not None:
            # Real-ESRGAN 사용
            try:
                output, _ = upsampler.enhance(img_bgr, outscale=scale)
                method = "Real-ESRGAN"
            except Exception as e:
                logger.warning(f"Real-ESRGAN failed, using fallback: {e}")
                output = fallback_upscale(img_bgr, scale)
                method = "Lanczos4 (fallback)"
        else:
            # 폴백 업스케일링
            output = fallback_upscale(img_bgr, scale)
            method = "Lanczos4 (fallback)"

        # 노이즈 제거 (선택적)
        if denoise_strength > 0:
            h = int(denoise_strength * 10)  # 0-10 범위
            output = cv2.fastNlMeansDenoisingColored(output, None, h, h, 7, 21)

        # RGB로 변환
        output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
        output_img = Image.fromarray(output_rgb)

        upscaled_size = {"width": output_img.size[0], "height": output_img.size[1]}
        processing_time = (time.time() - start_time) * 1000

        # 이미지 인코딩
        img_buffer = io.BytesIO()
        if output_format.lower() == "jpg" or output_format.lower() == "jpeg":
            output_img.save(img_buffer, format="JPEG", quality=95)
            media_type = "image/jpeg"
        else:
            output_img.save(img_buffer, format="PNG")
            media_type = "image/png"

        img_buffer.seek(0)

        logger.info(f"업스케일 완료: {original_size} → {upscaled_size}, {method}, {processing_time:.1f}ms")

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
        logger.error(f"업스케일 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/upscale/info", response_model=UpscaleResponse)
async def upscale_image_with_info(
    file: UploadFile = File(...),
    scale: int = Form(default=4),
    denoise_strength: float = Form(default=0.5)
):
    """
    이미지 업스케일링 (메타데이터만 반환, 이미지 저장하지 않음)
    테스트 및 정보 확인용
    """
    if not PILLOW_AVAILABLE:
        return UpscaleResponse(
            success=False,
            original_size={"width": 0, "height": 0},
            upscaled_size={"width": 0, "height": 0},
            scale=scale,
            model="N/A",
            device=DEVICE,
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
            device=DEVICE,
            processing_time_ms=processing_time
        )

    except Exception as e:
        return UpscaleResponse(
            success=False,
            original_size={"width": 0, "height": 0},
            upscaled_size={"width": 0, "height": 0},
            scale=scale,
            model="N/A",
            device=DEVICE,
            processing_time_ms=(time.time() - start_time) * 1000,
            error=str(e)
        )


@app.post("/api/v1/enhance")
async def enhance_drawing(
    file: UploadFile = File(...),
    upscale: bool = Form(default=True),
    denoise: bool = Form(default=True),
    sharpen: bool = Form(default=True),
    contrast: bool = Form(default=True)
):
    """
    도면 전용 향상 파이프라인

    PPT 슬라이드 9의 전처리 파이프라인:
    1. ESRGAN 업스케일링
    2. 노이즈 제거
    3. 샤프닝
    4. 대비 조정 (CLAHE)
    """
    if not PILLOW_AVAILABLE:
        raise HTTPException(status_code=503, detail="Image processing not available")

    start_time = time.time()

    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        if img.mode != "RGB":
            img = img.convert("RGB")

        img_np = np.array(img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # 1. 업스케일링
        if upscale:
            if upsampler:
                img_bgr, _ = upsampler.enhance(img_bgr, outscale=2)  # 2x만 적용 (속도)
            else:
                img_bgr = fallback_upscale(img_bgr, 2)

        # 2. 노이즈 제거
        if denoise:
            img_bgr = cv2.fastNlMeansDenoisingColored(img_bgr, None, 5, 5, 7, 21)

        # 3. 샤프닝
        if sharpen:
            kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
            img_bgr = cv2.filter2D(img_bgr, -1, kernel)

        # 4. CLAHE (대비 향상)
        if contrast:
            lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            img_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # 결과 인코딩
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        output_img = Image.fromarray(img_rgb)

        img_buffer = io.BytesIO()
        output_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        processing_time = (time.time() - start_time) * 1000
        logger.info(f"도면 향상 완료: {processing_time:.1f}ms")

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
        logger.error(f"도면 향상 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting ESRGAN API on port {ESRGAN_API_PORT}")
    logger.info(f"Device: {DEVICE}")
    logger.info(f"Real-ESRGAN available: {REALESRGAN_AVAILABLE}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=ESRGAN_API_PORT,
        log_level="info"
    )
