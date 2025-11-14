"""
eDOCr2 API Server
공학 도면 OCR 처리 마이크로서비스

포트: 5002
기능: 도면에서 치수, GD&T, 텍스트 정보 추출
"""

import os
import sys
import json
import time
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add edocr2 to path
EDOCR2_PATH = Path("/app/edocr2").parent  # /app
sys.path.insert(0, str(EDOCR2_PATH))

# Import eDOCr2 components
try:
    import cv2
    import numpy as np
    from edocr2 import tools
    from edocr2.keras_ocr.recognition import Recognizer
    from edocr2.keras_ocr.detection import Detector
    import tensorflow as tf

    # Configure GPU memory growth
    gpus = tf.config.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)

    EDOCR2_AVAILABLE = True
    logger.info("✅ eDOCr2 modules loaded successfully")
except ImportError as e:
    EDOCR2_AVAILABLE = False
    logger.warning(f"⚠️ eDOCr2 modules not available: {e}")
    logger.warning("⚠️ API will return empty results until models are installed")

# Import GPU preprocessing
try:
    from gpu_preprocessing import get_preprocessor, GPU_AVAILABLE as GPU_PREPROCESS_AVAILABLE
    if GPU_PREPROCESS_AVAILABLE:
        logger.info("✅ GPU preprocessing enabled")
    else:
        logger.info("💻 GPU preprocessing not available, using CPU")
except ImportError as e:
    GPU_PREPROCESS_AVAILABLE = False
    logger.warning(f"⚠️ GPU preprocessing module not available: {e}")

# Initialize FastAPI
app = FastAPI(
    title="eDOCr2 v2 API",
    description="Engineering Drawing OCR Service",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("/tmp/edocr2/uploads")
RESULTS_DIR = Path("/tmp/edocr2/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff'}


# =====================
# Pydantic Models
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class OCRRequest(BaseModel):
    extract_dimensions: bool = Field(True, description="치수 정보 추출 여부")
    extract_gdt: bool = Field(True, description="GD&T 정보 추출 여부")
    extract_text: bool = Field(True, description="텍스트 정보 추출 여부")
    use_vl_model: bool = Field(False, description="Vision Language 모델 사용 여부 (GPT-4o/Qwen2-VL)")
    visualize: bool = Field(False, description="시각화 이미지 생성 여부")
    use_gpu_preprocessing: bool = Field(True, description="GPU 전처리 사용 여부 (CLAHE, denoising)")


class DimensionData(BaseModel):
    value: float
    unit: str
    type: str
    tolerance: Optional[str] = None
    location: Optional[Dict[str, float]] = None


class GDTData(BaseModel):
    type: str
    value: float
    datum: Optional[str] = None
    location: Optional[Dict[str, float]] = None


class TextData(BaseModel):
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    title: Optional[str] = None
    material: Optional[str] = None
    notes: Optional[List[str]] = None


class OCRResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    processing_time: float
    file_id: str


# =====================
# Helper Functions
# =====================

def allowed_file(filename: str) -> bool:
    """파일 확장자 검증"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Global model variables (loaded once at startup)
_recognizer_gdt = None
_recognizer_dim = None
_detector = None
_models_loaded = False


def load_models():
    """Load eDOCr2 models at startup"""
    global _recognizer_gdt, _recognizer_dim, _detector, _models_loaded

    if _models_loaded:
        return

    if not EDOCR2_AVAILABLE:
        logger.warning("⚠️ eDOCr2 not available, skipping model loading")
        return

    try:
        logger.info("📦 Loading eDOCr2 models...")
        start_time = time.time()

        models_dir = EDOCR2_PATH / "edocr2" / "models"

        # Model paths
        gdt_model_path = models_dir / "recognizer_gdts.keras"
        dim_model_path = models_dir / "recognizer_dimensions_2.keras"

        # Check if models exist
        if not gdt_model_path.exists():
            logger.error(f"❌ GD&T model not found: {gdt_model_path}")
            logger.error("   Download from: https://github.com/javvi51/edocr2/releases/tag/download_recognizers")
            return

        if not dim_model_path.exists():
            logger.error(f"❌ Dimension model not found: {dim_model_path}")
            logger.error("   Download from: https://github.com/javvi51/edocr2/releases/tag/download_recognizers")
            return

        # Load GD&T recognizer
        logger.info(f"  Loading GD&T recognizer from {gdt_model_path}")
        alphabet_gdt = tools.ocr_pipelines.read_alphabet(str(gdt_model_path))
        _recognizer_gdt = Recognizer(alphabet=alphabet_gdt)
        _recognizer_gdt.model.load_weights(str(gdt_model_path))
        logger.info("  ✅ GD&T recognizer loaded")

        # Load dimension recognizer
        logger.info(f"  Loading dimension recognizer from {dim_model_path}")
        alphabet_dim = tools.ocr_pipelines.read_alphabet(str(dim_model_path))
        _recognizer_dim = Recognizer(alphabet=alphabet_dim)
        _recognizer_dim.model.load_weights(str(dim_model_path))
        logger.info("  ✅ Dimension recognizer loaded")

        # Load detector
        logger.info("  Loading detector")
        _detector = Detector()
        logger.info("  ✅ Detector loaded")

        _models_loaded = True
        elapsed = time.time() - start_time
        logger.info(f"✅ All models loaded successfully in {elapsed:.2f}s")

    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        import traceback
        traceback.print_exc()


def process_ocr(
    file_path: Path,
    extract_dimensions: bool = True,
    extract_gdt: bool = True,
    extract_text: bool = True,
    use_vl_model: bool = False,
    visualize: bool = False,
    use_gpu_preprocessing: bool = True
) -> Dict[str, Any]:
    """
    OCR 처리 로직 (실제 eDOCr2 파이프라인 사용)
    """
    try:
        logger.info(f"Processing file: {file_path}")
        logger.info(f"Options: dims={extract_dimensions}, gdt={extract_gdt}, text={extract_text}, vl={use_vl_model}, gpu_preproc={use_gpu_preprocessing}")

        if not EDOCR2_AVAILABLE:
            logger.warning("⚠️ eDOCr2 not available, returning empty results")
            return {
                "dimensions": [],
                "gdt": [],
                "text": {},
                "warning": "eDOCr2 modules not installed. Install dependencies: pip install -r requirements.txt"
            }

        if not _models_loaded:
            logger.warning("⚠️ Models not loaded, returning empty results")
            return {
                "dimensions": [],
                "gdt": [],
                "text": {},
                "warning": "eDOCr2 models not found. Download from GitHub Releases."
            }

        # Read image
        logger.info("  Reading image...")
        img = cv2.imread(str(file_path))
        if img is None:
            raise ValueError(f"Failed to read image: {file_path}")

        # GPU 전처리 적용
        if use_gpu_preprocessing and GPU_PREPROCESS_AVAILABLE:
            logger.info("  Applying GPU preprocessing...")
            preproc_start = time.time()

            preprocessor = get_preprocessor(use_gpu=True)

            # OCR용 전처리 (CLAHE + Gaussian blur, 이진화는 하지 않음)
            img_gray = preprocessor.preprocess_pipeline(
                img,
                apply_clahe=True,
                apply_blur=True,
                apply_threshold=False,  # eDOCr2에서 자체 이진화 수행
                clahe_params={"clip_limit": 3.0, "tile_grid_size": (8, 8)},
                blur_params={"kernel_size": 3, "sigma": 0.8}
            )

            # Grayscale을 BGR로 변환 (eDOCr2는 컬러 이미지 기대)
            if len(img_gray.shape) == 2:
                img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)

            preproc_time = time.time() - preproc_start
            logger.info(f"  GPU preprocessing completed in {preproc_time:.3f}s")

            # GPU 메모리 사용량 로깅
            if hasattr(preprocessor, 'get_gpu_memory_usage'):
                mem_usage = preprocessor.get_gpu_memory_usage()
                logger.info(f"  GPU memory used: {mem_usage['used_bytes'] / 1024**2:.1f} MB")

        language = 'eng'
        process_img = img.copy()

        # 1. Segmentation
        logger.info("  Running segmentation...")
        img_boxes, frame, gdt_boxes, tables, dim_boxes = tools.layer_segm.segment_img(
            img,
            autoframe=True,
            frame_thres=0.7,
            GDT_thres=0.02,
            binary_thres=127
        )
        logger.info(f"    Found: {len(gdt_boxes)} GD&T boxes, {len(dim_boxes)} dimension boxes, {len(tables)} tables")

        result = {
            "dimensions": [],
            "gdt": [],
            "text": {},
            "tables": []
        }

        # 2. OCR Tables
        if extract_text and tables:
            logger.info("  Processing tables...")
            table_results, updated_tables, process_img = tools.ocr_pipelines.ocr_tables(
                tables, process_img, language
            )
            result["tables"] = table_results
            logger.info(f"    Extracted {len(table_results)} tables")

        # 3. OCR GD&T
        if extract_gdt and gdt_boxes:
            logger.info("  Processing GD&T...")
            gdt_results, updated_gdt_boxes, process_img = tools.ocr_pipelines.ocr_gdt(
                process_img, gdt_boxes, _recognizer_gdt
            )

            # Convert to API format
            gdt_list = []
            for gdt_item in gdt_results:
                if isinstance(gdt_item, dict):
                    gdt_list.append({
                        "type": gdt_item.get("type", "unknown"),
                        "value": gdt_item.get("value", 0.0),
                        "datum": gdt_item.get("datum"),
                        "location": gdt_item.get("location")
                    })

            result["gdt"] = gdt_list
            logger.info(f"    Extracted {len(gdt_list)} GD&T symbols")

        # 4. OCR Dimensions
        if extract_dimensions:
            logger.info("  Processing dimensions...")
            if frame:
                process_img = process_img[frame.y : frame.y + frame.h, frame.x : frame.x + frame.w]

            dimensions, other_info, process_img, dim_tess = tools.ocr_pipelines.ocr_dimensions(
                process_img, _detector, _recognizer_dim,
                tools.ocr_pipelines.read_alphabet(str(EDOCR2_PATH / "edocr2" / "models" / "recognizer_dimensions_2.keras")),
                frame, dim_boxes,
                cluster_thres=20,
                max_img_size=1048,
                language=language,
                backg_save=False
            )

            # Convert to API format
            dim_list = []
            for dim_item in dimensions:
                if isinstance(dim_item, dict):
                    dim_list.append({
                        "value": dim_item.get("value", 0.0),
                        "unit": dim_item.get("unit", "mm"),
                        "type": dim_item.get("type", "linear"),
                        "tolerance": dim_item.get("tolerance"),
                        "location": dim_item.get("location")
                    })

            result["dimensions"] = dim_list
            logger.info(f"    Extracted {len(dim_list)} dimensions")

        # 5. Extract text info from tables
        if extract_text and result.get("tables"):
            text_info = {}
            for table in result["tables"]:
                if isinstance(table, dict):
                    # Try to extract common fields
                    for key, value in table.items():
                        key_lower = str(key).lower()
                        if "drawing" in key_lower or "number" in key_lower:
                            text_info["drawing_number"] = value
                        elif "rev" in key_lower:
                            text_info["revision"] = value
                        elif "title" in key_lower:
                            text_info["title"] = value
                        elif "material" in key_lower:
                            text_info["material"] = value

            result["text"] = text_info

        # 6. Visualization
        if visualize:
            logger.info("  Generating visualization...")
            # TODO: Save visualization image
            result["visualization_url"] = f"/api/v1/visualization/{file_path.name}"

        logger.info(f"✅ OCR completed: {len(result['dimensions'])} dims, {len(result['gdt'])} gdts")
        return result

    except Exception as e:
        logger.error(f"❌ OCR processing failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """오래된 파일 삭제"""
    try:
        current_time = time.time()
        for file_path in directory.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    file_path.unlink()
                    logger.info(f"Deleted old file: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")


# =====================
# Startup/Shutdown Events
# =====================

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    logger.info("🚀 Starting eDOCr2 API...")
    load_models()
    logger.info("✅ eDOCr2 API ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down eDOCr2 API...")


# =====================
# API Endpoints
# =====================

@app.get("/", response_model=HealthResponse)
async def root():
    """루트 엔드포인트"""
    return {
        "status": "online",
        "service": "eDOCr2 v2 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v2/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": "eDOCr2 v2 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v2/ocr", response_model=OCRResponse)
async def process_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="도면 파일 (PDF, PNG, JPG)"),
    extract_dimensions: bool = Form(True, description="치수 정보 추출"),
    extract_gdt: bool = Form(True, description="GD&T 정보 추출"),
    extract_text: bool = Form(True, description="텍스트 정보 추출"),
    use_vl_model: bool = Form(False, description="Vision Language 모델 사용"),
    visualize: bool = Form(False, description="시각화 이미지 생성"),
    use_gpu_preprocessing: bool = Form(True, description="GPU 전처리 사용")
):
    """
    도면 OCR 처리

    - **file**: 도면 파일 (PDF, PNG, JPG, JPEG, TIFF)
    - **extract_dimensions**: 치수 정보 추출 여부
    - **extract_gdt**: GD&T 정보 추출 여부
    - **extract_text**: 텍스트 정보 추출 여부
    - **use_vl_model**: Vision Language 모델 사용 여부 (느리지만 정확)
    - **visualize**: 시각화 이미지 생성 여부
    - **use_gpu_preprocessing**: GPU 전처리 사용 여부 (CLAHE, denoising)
    """
    start_time = time.time()

    # 파일 검증
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 파일 크기 체크
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # 파일 저장
    file_id = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded: {file_id} ({file_size / 1024:.2f} KB)")

        # OCR 처리
        ocr_result = process_ocr(
            file_path,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            use_vl_model=use_vl_model,
            visualize=visualize,
            use_gpu_preprocessing=use_gpu_preprocessing
        )

        processing_time = time.time() - start_time

        # 백그라운드 작업: 오래된 파일 삭제
        background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)

        return {
            "status": "success",
            "data": ocr_result,
            "processing_time": round(processing_time, 2),
            "file_id": file_id
        }

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/result/{file_id}")
async def get_result(file_id: str):
    """처리 결과 조회 (향후 비동기 처리용)"""
    result_path = RESULTS_DIR / f"{file_id}.json"

    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Result not found")

    with open(result_path, 'r') as f:
        result = json.load(f)

    return JSONResponse(content=result)


@app.delete("/api/v1/cleanup")
async def cleanup_files(max_age_hours: int = 24):
    """수동 파일 정리"""
    try:
        cleanup_old_files(UPLOAD_DIR, max_age_hours)
        cleanup_old_files(RESULTS_DIR, max_age_hours)
        return {"status": "success", "message": f"Cleaned up files older than {max_age_hours} hours"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Main
# =====================

if __name__ == "__main__":
    port = int(os.getenv("EDOCR2_PORT", 5001))
    workers = int(os.getenv("EDOCR2_WORKERS", 4))

    logger.info(f"Starting eDOCr2 API on port {port} with {workers} workers")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
