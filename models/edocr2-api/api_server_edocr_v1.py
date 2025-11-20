"""
eDOCr v1 API Server
공학 도면 OCR 처리 마이크로서비스 (eDOCr v1 실제 구현)

포트: 5001
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
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import markdown


def convert_to_serializable(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    import numpy as np

    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj


def transform_edocr_to_ui_format(dimension_dict, gdt_dict, infoblock_dict):
    """
    Transform eDOCr v1 output format to UI-compatible format

    eDOCr v1 format:
    - dimensions: [{'pred': {...}, 'bbox': [[x,y], ...], ...}, ...]
    - gdt: [{'pred': {...}, 'bbox': [[x,y], ...], ...}, ...]
    - text: {various keys with values}

    UI expected format:
    - dimensions: [{type, value, unit, tolerance, location: {x, y}}, ...]
    - gdt: [{type, value, datum, location: {x, y}}, ...]
    - text: {drawing_number, revision, title, material, notes, total_blocks}
    """
    import re

    # Transform dimensions
    ui_dimensions = []
    for dim in dimension_dict:
        try:
            pred = dim.get('pred', {})
            # eDOCr v1 uses 'box' not 'bbox'
            bbox = dim.get('box', dim.get('bbox', [[0, 0]]))

            # eDOCr v1 uses 'value' or 'nominal', not 'text'
            text = str(pred.get('value', pred.get('nominal', '0')))

            # Determine dimension type based on text patterns
            dim_type = 'linear'
            if 'Ø' in text or '⌀' in text:
                dim_type = 'diameter'
            elif 'R' in text[:2]:  # Radius at start
                dim_type = 'radius'

            # Extract numeric value
            value_match = re.search(r'[\d.]+', text.replace('Ø', '').replace('⌀', '').replace('R', ''))
            value = float(value_match.group()) if value_match else 0.0

            # Extract tolerance if present (e.g., "+0.1/-0.05" or "±0.1")
            tolerance = None
            if '+' in text or '±' in text:
                tolerance = text[text.find('+'):] if '+' in text else text[text.find('±'):]

            # Calculate bounding box dimensions
            bbox_info = {}
            if bbox and len(bbox) >= 4:
                x_coords = [pt[0] for pt in bbox if len(pt) >= 2]
                y_coords = [pt[1] for pt in bbox if len(pt) >= 2]
                if x_coords and y_coords:
                    bbox_info = {
                        'x': int(min(x_coords)),
                        'y': int(min(y_coords)),
                        'width': int(max(x_coords) - min(x_coords)),
                        'height': int(max(y_coords) - min(y_coords))
                    }

            if not bbox_info:
                bbox_info = {'x': 0, 'y': 0, 'width': 0, 'height': 0}

            ui_dimensions.append({
                'type': dim_type,
                'value': value,
                'unit': 'mm',  # Default unit for engineering drawings
                'tolerance': tolerance,
                'bbox': bbox_info
            })
        except Exception as e:
            logger.warning(f"Failed to transform dimension: {e}")
            continue

    # Transform GD&T
    ui_gdt = []
    for gdt in gdt_dict:
        try:
            pred = gdt.get('pred', {})
            # eDOCr v1 uses 'box' not 'bbox'
            bbox = gdt.get('box', gdt.get('bbox', [[0, 0]]))

            # eDOCr v1 uses 'value' or 'nominal', not 'text'
            text = str(pred.get('value', pred.get('nominal', '')))

            # Extract GD&T type (first symbol)
            gdt_type = text[0] if text else 'unknown'

            # Extract tolerance value
            value_match = re.search(r'[\d.]+', text)
            value = float(value_match.group()) if value_match else 0.0

            # Extract datum (capital letters)
            datum_match = re.search(r'[A-Z]', text[1:]) if len(text) > 1 else None
            datum = datum_match.group() if datum_match else None

            # Calculate bounding box dimensions
            bbox_info = {}
            if bbox and len(bbox) >= 4:
                x_coords = [pt[0] for pt in bbox if len(pt) >= 2]
                y_coords = [pt[1] for pt in bbox if len(pt) >= 2]
                if x_coords and y_coords:
                    bbox_info = {
                        'x': int(min(x_coords)),
                        'y': int(min(y_coords)),
                        'width': int(max(x_coords) - min(x_coords)),
                        'height': int(max(y_coords) - min(y_coords))
                    }

            if not bbox_info:
                bbox_info = {'x': 0, 'y': 0, 'width': 0, 'height': 0}

            ui_gdt.append({
                'type': gdt_type,
                'value': value,
                'datum': datum,
                'bbox': bbox_info
            })
        except Exception as e:
            logger.warning(f"Failed to transform GD&T: {e}")
            continue

    # Transform text/infoblock
    ui_text = {
        'drawing_number': None,
        'revision': None,
        'title': None,
        'material': None,
        'notes': [],
        'total_blocks': 0
    }

    if isinstance(infoblock_dict, dict):
        # eDOCr v1 infoblock format varies, try to extract common fields
        ui_text['drawing_number'] = infoblock_dict.get('drawing_number') or infoblock_dict.get('part_number')
        ui_text['revision'] = infoblock_dict.get('revision') or infoblock_dict.get('rev')
        ui_text['title'] = infoblock_dict.get('title') or infoblock_dict.get('drawing_title')
        ui_text['material'] = infoblock_dict.get('material') or infoblock_dict.get('mat')

        # Collect all other text as notes
        notes = []
        for key, value in infoblock_dict.items():
            if key not in ['drawing_number', 'part_number', 'revision', 'rev', 'title', 'drawing_title', 'material', 'mat']:
                if value:
                    notes.append(f"{key}: {value}")
        ui_text['notes'] = notes
        ui_text['total_blocks'] = len(infoblock_dict)

    return ui_dimensions, ui_gdt, ui_text

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# eDOCr v1 imports (will be available in Docker)
try:
    import cv2
    import numpy as np
    from skimage import io
    from pdf2image import convert_from_path
    import string

    # eDOCr v1 modules
    from eDOCr import tools
    from eDOCr.keras_ocr import tools as keras_tools

    EDOCR_AVAILABLE = True
    logger.info("✅ eDOCr v1 imports successful")
except ImportError as e:
    EDOCR_AVAILABLE = False
    logger.warning(f"⚠️ eDOCr v1 not available: {e}")

# Initialize FastAPI
app = FastAPI(
    title="eDOCr v1 API",
    description="Engineering Drawing OCR Service (eDOCr v1)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# Global models
model_infoblock = None
model_dimensions = None
model_gdts = None

# eDOCr v1 alphabets
GDT_symbols = '⏤⏥○⌭⌒⌓⏊∠⫽⌯⌖◎↗⌰'
FCF_symbols = 'ⒺⒻⓁⓂⓅⓈⓉⓊ'
Extra = '(),.+-±:/°"⌀'
alphabet_dimensions = string.digits + 'AaBCDRGHhMmnx' + Extra
alphabet_infoblock = string.digits + string.ascii_letters + ',.:-/'
alphabet_gdts = string.digits + ',.⌀ABCD' + GDT_symbols


@app.on_event("startup")
async def load_models():
    """Load eDOCr v1 models on startup"""
    global model_infoblock, model_dimensions, model_gdts

    # Configure GPU memory growth
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            for gpu in gpus:
                # Enable memory growth to avoid OOM errors
                tf.config.experimental.set_memory_growth(gpu, True)

                # Set memory limit to 3GB (sharing with v2 API)
                tf.config.set_logical_device_configuration(
                    gpu,
                    [tf.config.LogicalDeviceConfiguration(memory_limit=3072)]
                )
            logger.info(f"✅ Configured {len(gpus)} GPU(s) with 3GB memory limit and growth enabled")
        else:
            logger.warning("⚠️ No GPU found, running on CPU")
    except Exception as e:
        logger.warning(f"⚠️ GPU configuration failed: {e}, will use default settings")

    if not EDOCR_AVAILABLE:
        logger.warning("⚠️ eDOCr v1 not available - running in mock mode")
        return

    try:
        logger.info("Loading eDOCr v1 models...")

        # Models auto-download from GitHub Releases
        model_infoblock = keras_tools.download_and_verify(
            url="https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_infoblock.h5",
            filename="recognizer_infoblock.h5",
            sha256="e0a317e07ce75235f67460713cf1b559e02ae2282303eec4a1f76ef211fcb8e8",
        )

        model_dimensions = keras_tools.download_and_verify(
            url="https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_dimensions.h5",
            filename="recognizer_dimensions.h5",
            sha256="a1c27296b1757234a90780ccc831762638b9e66faf69171f5520817130e05b8f",
        )

        model_gdts = keras_tools.download_and_verify(
            url="https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_gdts.h5",
            filename="recognizer_gdts.h5",
            sha256="58acf6292a43ff90a344111729fc70cf35f0c3ca4dfd622016456c0b29ef2a46",
        )

        logger.info("✅ eDOCr v1 models loaded successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to load eDOCr v1 models: {e}")
        raise


# Pydantic models
class OCRRequest(BaseModel):
    extract_dimensions: bool = Field(True, description="치수 정보 추출 여부")
    extract_gdt: bool = Field(True, description="GD&T 정보 추출 여부")
    extract_text: bool = Field(True, description="텍스트 정보 추출 여부")
    visualize: bool = Field(False, description="시각화 이미지 생성 여부")
    remove_watermark: bool = Field(False, description="워터마크 제거 여부")
    cluster_threshold: int = Field(20, description="치수 클러스터링 임계값 (px)")


class EnhancedOCRRequest(BaseModel):
    """Enhanced OCR with performance improvement strategies"""
    extract_dimensions: bool = Field(True, description="치수 정보 추출 여부")
    extract_gdt: bool = Field(True, description="GD&T 정보 추출 여부")
    extract_text: bool = Field(True, description="텍스트 정보 추출 여부")
    visualize: bool = Field(False, description="시각화 이미지 생성 여부")
    remove_watermark: bool = Field(False, description="워터마크 제거 여부")
    cluster_threshold: int = Field(20, description="치수 클러스터링 임계값 (px)")
    strategy: str = Field("edgnet", description="Enhancement strategy: basic, edgnet, vl, hybrid")
    vl_provider: str = Field("openai", description="VL provider: openai, anthropic")


class Dimension(BaseModel):
    type: str
    value: float
    unit: str
    tolerance: Optional[str] = None
    location: Dict[str, float]


class GDT(BaseModel):
    type: str
    value: float
    datum: Optional[str] = None
    location: Dict[str, float]


class TextInfo(BaseModel):
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    title: Optional[str] = None
    material: Optional[str] = None
    notes: Optional[List[str]] = None
    total_blocks: int = 0


class OCRResult(BaseModel):
    dimensions: List[Dimension]
    gdt: List[GDT]
    text: TextInfo
    visualization_url: Optional[str] = None


class OCRResponse(BaseModel):
    status: str
    data: OCRResult
    processing_time: float
    file_id: str


# Helper functions
def allowed_file(filename: str) -> bool:
    """파일 확장자 검증"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_ocr_v1(
    file_path: Path,
    extract_dimensions: bool = True,
    extract_gdt: bool = True,
    extract_text: bool = True,
    visualize: bool = False,
    remove_watermark: bool = False,
    cluster_threshold: int = 20
) -> Dict[str, Any]:
    """
    eDOCr v1 실제 OCR 처리
    """
    if not EDOCR_AVAILABLE:
        # Fallback to mock if eDOCr not available
        logger.warning("eDOCr v1 not available, returning mock data")
        return {
            "dimensions": [],
            "gdt": [],
            "text": {
                "drawing_number": "MOCK-001",
                "revision": "A",
                "title": "eDOCr v1 not installed",
                "material": "Please install eDOCr v1",
                "notes": ["This is mock data - eDOCr v1 dependencies missing"],
                "total_blocks": 0
            }
        }

    try:
        logger.info(f"Processing with eDOCr v1: {file_path}")
        start_time = time.time()

        # Load image
        if file_path.suffix.lower() == '.pdf':
            images = convert_from_path(str(file_path))
            img = np.array(images[0])
        else:
            img = cv2.imread(str(file_path))

        logger.info(f"Image loaded: {img.shape}")

        # Remove watermark if requested
        if remove_watermark:
            logger.info("Removing watermark...")
            img = tools.watermark.handle(img)

        # Box detection
        logger.info("Detecting boxes...")
        class_list, img_boxes = tools.box_tree.findrect(img)

        # Process rectangles
        logger.info("Processing rectangles...")
        boxes_infoblock, gdt_boxes, cl_frame, process_img = tools.img_process.process_rect(class_list, img)

        # DEBUG: Log GDT boxes count
        logger.info(f"DEBUG: Found {len(gdt_boxes)} GDT boxes")
        if gdt_boxes:
            logger.info(f"DEBUG: First GDT box: {gdt_boxes[0] if len(gdt_boxes) > 0 else 'None'}")

        # Save processed image
        process_img_path = RESULTS_DIR / f"{file_path.stem}_process.jpg"
        io.imsave(str(process_img_path), process_img)
        logger.info(f"Processed image saved: {process_img_path}")

        # OCR infoblock
        if extract_text:
            logger.info("Processing infoblock...")
            infoblock_dict = tools.pipeline_infoblock.read_infoblocks(
                boxes_infoblock, img, alphabet_infoblock, model_infoblock
            )
        else:
            infoblock_dict = {}

        # OCR GD&T
        if extract_gdt:
            logger.info(f"Processing GD&T with {len(gdt_boxes)} boxes...")
            if not gdt_boxes:
                logger.warning("⚠️ No GDT boxes detected - GDT results will be empty")
            gdt_dict = tools.pipeline_gdts.read_gdtbox1(
                gdt_boxes, alphabet_gdts, model_gdts,
                alphabet_dimensions, model_dimensions
            )
            logger.info(f"DEBUG: GDT extraction returned {len(gdt_dict) if gdt_dict else 0} results")
        else:
            gdt_dict = []

        # OCR dimensions
        if extract_dimensions:
            logger.info("Processing dimensions...")
            dimension_dict = tools.pipeline_dimensions.read_dimensions(
                str(process_img_path), alphabet_dimensions, model_dimensions, cluster_threshold
            )
            # DEBUG: Log dimension_dict structure
            logger.info(f"DEBUG: dimension_dict type: {type(dimension_dict)}, length: {len(dimension_dict)}")
            if dimension_dict and len(dimension_dict) > 0:
                logger.info(f"DEBUG: First dimension keys: {dimension_dict[0].keys() if isinstance(dimension_dict[0], dict) else 'not a dict'}")
                logger.info(f"DEBUG: First dimension: {dimension_dict[0]}")
        else:
            dimension_dict = []

        # Keep original eDOCr format for visualization
        original_dimension_dict = dimension_dict
        original_gdt_dict = gdt_dict
        original_infoblock_dict = infoblock_dict

        # Convert numpy types to native Python types
        dimension_dict_converted = convert_to_serializable(dimension_dict) if extract_dimensions else []
        gdt_dict_converted = convert_to_serializable(gdt_dict) if extract_gdt else []
        infoblock_dict_converted = convert_to_serializable(infoblock_dict) if extract_text else {}

        # Transform to UI-compatible format
        logger.info(f"DEBUG: Before transform - dimension_dict_converted length: {len(dimension_dict_converted)}")
        if dimension_dict_converted and len(dimension_dict_converted) > 0:
            logger.info(f"DEBUG: First converted dimension: {dimension_dict_converted[0]}")

        ui_dimensions, ui_gdt, ui_text = transform_edocr_to_ui_format(
            dimension_dict_converted, gdt_dict_converted, infoblock_dict_converted
        )

        logger.info(f"DEBUG: After transform - ui_dimensions length: {len(ui_dimensions)}")
        if ui_dimensions and len(ui_dimensions) > 0:
            logger.info(f"DEBUG: First UI dimension: {ui_dimensions[0]}")

        # Format results
        result = {
            "dimensions": ui_dimensions,
            "gdt": ui_gdt,
            "text": ui_text
        }

        # Visualization
        if visualize:
            logger.info("Creating visualization...")
            color_palette = {
                'infoblock': (180, 220, 250),
                'gdts': (94, 204, 243),
                'dimensions': (93, 206, 175),
                'frame': (167, 234, 82),
                'flag': (241, 65, 36)
            }

            mask_img = tools.output.mask_the_drawing(
                img, original_infoblock_dict, original_gdt_dict, original_dimension_dict, cl_frame, color_palette
            )

            mask_path = RESULTS_DIR / f"{file_path.stem}_mask.jpg"
            io.imsave(str(mask_path), mask_img)
            result["visualization_url"] = f"/api/v1/visualization/{mask_path.name}"
            logger.info(f"Visualization saved: {mask_path}")

        # Save boxes image
        boxes_path = RESULTS_DIR / f"{file_path.stem}_boxes.jpg"
        io.imsave(str(boxes_path), img_boxes)

        # Save data (use original eDOCr format)
        tools.output.record_data(
            str(RESULTS_DIR), file_path.stem,
            original_infoblock_dict, original_gdt_dict, original_dimension_dict
        )

        processing_time = time.time() - start_time
        logger.info(f"✅ eDOCr v1 processing complete in {processing_time:.2f}s")

        return result

    except Exception as e:
        logger.error(f"❌ eDOCr v1 processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


# API Endpoints
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "eDOCr v1 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "edocr_available": EDOCR_AVAILABLE,
        "models_loaded": all([model_infoblock, model_dimensions, model_gdts]) if EDOCR_AVAILABLE else False
    }


@app.post("/api/v1/ocr")  # Removed response_model to return raw eDOCr output
async def process_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="도면 파일 (PDF, PNG, JPG)"),
    extract_dimensions: bool = Form(True, description="치수 정보 추출"),
    extract_gdt: bool = Form(True, description="GD&T 정보 추출"),
    extract_text: bool = Form(True, description="텍스트 정보 추출"),
    visualize: bool = Form(False, description="시각화 이미지 생성"),
    remove_watermark: bool = Form(False, description="워터마크 제거"),
    cluster_threshold: int = Form(20, description="치수 클러스터링 임계값")
):
    """
    도면 OCR 처리 (eDOCr v1)

    - **file**: 도면 파일 (PDF, PNG, JPG)
    - **extract_dimensions**: 치수 정보 추출 여부
    - **extract_gdt**: GD&T 정보 추출 여부
    - **extract_text**: 텍스트 정보 추출 여부
    - **visualize**: 시각화 이미지 생성 여부
    - **remove_watermark**: 워터마크 제거 여부
    - **cluster_threshold**: 치수 클러스터링 임계값 (px)
    """
    start_time = time.time()

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_ext = file.filename.rsplit('.', 1)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # Save uploaded file
    file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        logger.info(f"📁 File saved: {file_path}")

        # Process OCR
        result = process_ocr_v1(
            file_path,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            visualize=visualize,
            remove_watermark=remove_watermark,
            cluster_threshold=cluster_threshold
        )

        processing_time = time.time() - start_time

        # Cleanup in background
        background_tasks.add_task(lambda: file_path.unlink(missing_ok=True))

        return {
            "status": "success",
            "data": result,
            "processing_time": processing_time,
            "file_id": file_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/visualization/{filename}")
async def get_visualization(filename: str):
    """시각화 이미지 반환"""
    file_path = RESULTS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Visualization not found")

    return FileResponse(file_path)


@app.post("/api/v1/ocr/enhanced")
async def ocr_enhanced(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    extract_dimensions: bool = Form(True),
    extract_gdt: bool = Form(True),
    extract_text: bool = Form(False),
    visualize: bool = Form(False),
    remove_watermark: bool = Form(False),
    cluster_threshold: int = Form(20),
    strategy: str = Form("edgnet"),
    vl_provider: str = Form("openai")
):
    """
    Enhanced OCR with performance improvement strategies

    **Strategies**:
    - `basic`: Original eDOCr (baseline) - 50% dimension, 0% GD&T
    - `edgnet`: EDGNet-enhanced - 60% dimension, 50% GD&T
    - `vl`: VL-powered - 85% dimension, 75% GD&T
    - `hybrid`: EDGNet + VL - 90% dimension, 80% GD&T
    """
    try:
        start_time = time.time()
        logger.info(f"🚀 Enhanced OCR: strategy={strategy}, provider={vl_provider}")

        # Save uploaded file
        file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = UPLOAD_DIR / file_id

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Run standard OCR
        ocr_result = process_ocr_v1(
            file_path,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            visualize=visualize,
            remove_watermark=remove_watermark,
            cluster_threshold=cluster_threshold
        )

        # Basic strategy: return as-is
        if strategy == 'basic':
            processing_time = time.time() - start_time
            background_tasks.add_task(lambda: file_path.unlink(missing_ok=True))

            return {
                "status": "success",
                "data": ocr_result,
                "processing_time": processing_time,
                "file_id": file_id,
                "enhancement": {
                    "strategy": "basic",
                    "description": "Original eDOCr",
                    "enhancements_applied": ["none"]
                }
            }

        # Enhanced strategies
        from enhancers import EnhancedOCRPipeline

        pipeline = EnhancedOCRPipeline(
            edgnet_url=os.getenv("EDGNET_URL", "http://edgnet-api:5002"),
            vl_provider=vl_provider,
            vl_api_key=os.getenv(f"{vl_provider.upper()}_API_KEY")
        )

        # Load image
        if file_path.suffix.lower() == '.pdf':
            from pdf2image import convert_from_path
            images = convert_from_path(str(file_path))
            img = np.array(images[0])
        else:
            img = cv2.imread(str(file_path))

        # Run enhancement
        enhancement_result = pipeline.run(
            strategy=strategy,
            image_path=file_path,
            img=img,
            original_gdt_boxes=[],
            original_gdt=ocr_result.get('gdt', [])
        )

        # Merge results
        ocr_result['gdt'] = enhancement_result['enhanced_gdt']

        processing_time = time.time() - start_time
        background_tasks.add_task(lambda: file_path.unlink(missing_ok=True))

        return {
            "status": "success",
            "data": ocr_result,
            "processing_time": processing_time,
            "file_id": file_id,
            "enhancement": {
                "strategy": enhancement_result['strategy'],
                "description": enhancement_result['description'],
                "enhancements_applied": enhancement_result['enhancements_applied'],
                "stats": enhancement_result['stats'],
                "enhancement_time": enhancement_result['processing_time']
            }
        }

    except Exception as e:
        logger.error(f"❌ Enhanced OCR failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/docs", response_class=HTMLResponse)
async def list_documentation():
    """
    List available documentation files
    """
    docs_dir = Path("/home/uproot/ax/poc")
    docs = [
        {
            "id": "user-guide",
            "title": "👤 사용자 가이드",
            "description": "일반 사용자를 위한 완전 가이드 - 시작하기, 기능 사용법, 실전 예제",
            "file": "USER_GUIDE.md"
        },
        {
            "id": "quick-reference",
            "title": "⚡ 빠른 참조 카드",
            "description": "30초 시작, 단축키, 문제 해결 - 인쇄해서 책상에 붙이세요!",
            "file": "QUICK_REFERENCE.md"
        },
        {
            "id": "implementation-status",
            "title": "구현 상태 보고서",
            "description": "현재 구현 상태, 테스트 결과, 다음 단계",
            "file": "IMPLEMENTATION_STATUS.md"
        },
        {
            "id": "enhancement-implementation",
            "title": "Enhancement 구현 가이드",
            "description": "상세 구현 내용, 아키텍처, 사용법",
            "file": "ENHANCEMENT_IMPLEMENTATION_SUMMARY.md"
        },
        {
            "id": "production-readiness",
            "title": "Production Readiness 분석",
            "description": "성능 분석, 개선 목표, 예상 효과",
            "file": "PRODUCTION_READINESS_ANALYSIS.md"
        },
        {
            "id": "contributing",
            "title": "기여 가이드",
            "description": "Git 워크플로우, 커밋 규칙, 코드 스타일",
            "file": "CONTRIBUTING.md"
        },
        {
            "id": "git-workflow",
            "title": "Git 워크플로우 가이드",
            "description": "상세 Git 명령어, 브랜치 전략",
            "file": "GIT_WORKFLOW.md"
        }
    ]

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>eDOCr Enhancement Documentation</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
                background: #f5f5f5;
            }
            h1 {
                color: #2563eb;
                border-bottom: 3px solid #2563eb;
                padding-bottom: 0.5rem;
            }
            .doc-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 1rem;
                margin-top: 2rem;
            }
            .doc-card {
                background: white;
                border-radius: 8px;
                padding: 1.5rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
                text-decoration: none;
                color: inherit;
                display: block;
            }
            .doc-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .doc-card h3 {
                margin: 0 0 0.5rem 0;
                color: #1e40af;
            }
            .doc-card p {
                margin: 0;
                color: #64748b;
                font-size: 0.9rem;
            }
            .back-link {
                display: inline-block;
                margin-top: 1rem;
                color: #2563eb;
                text-decoration: none;
            }
            .back-link:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>📚 eDOCr Enhancement Documentation</h1>
        <p>Enhanced OCR 시스템 구현 문서 모음</p>

        <div class="doc-grid">
    """

    for doc in docs:
        html += f"""
            <a href="/api/v1/docs/{doc['id']}" class="doc-card">
                <h3>{doc['title']}</h3>
                <p>{doc['description']}</p>
            </a>
        """

    html += """
        </div>
        <a href="/" class="back-link">← API 루트로 돌아가기</a>
    </body>
    </html>
    """

    return html


@app.get("/api/v1/docs/{doc_id}", response_class=HTMLResponse)
async def get_documentation(doc_id: str):
    """
    Get documentation as HTML

    Available docs:
    - user-guide: User guide for end users
    - quick-reference: Quick reference card
    - implementation-status: Implementation status report
    - enhancement-implementation: Enhancement implementation guide
    - production-readiness: Production readiness analysis
    - contributing: Contribution guidelines
    - git-workflow: Git workflow guide
    """
    docs_map = {
        "user-guide": "USER_GUIDE.md",
        "quick-reference": "QUICK_REFERENCE.md",
        "implementation-status": "IMPLEMENTATION_STATUS.md",
        "enhancement-implementation": "ENHANCEMENT_IMPLEMENTATION_SUMMARY.md",
        "production-readiness": "PRODUCTION_READINESS_ANALYSIS.md",
        "contributing": "CONTRIBUTING.md",
        "git-workflow": "GIT_WORKFLOW.md"
    }

    if doc_id not in docs_map:
        raise HTTPException(status_code=404, detail="Documentation not found")

    doc_path = Path("/home/uproot/ax/poc") / docs_map[doc_id]

    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Documentation file not found")

    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'codehilite']
        )

        # Wrap in nice HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{docs_map[doc_id]} - eDOCr Documentation</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 2rem;
                    line-height: 1.6;
                    background: #f9fafb;
                }}
                .content {{
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #1e40af;
                    border-bottom: 3px solid #2563eb;
                    padding-bottom: 0.5rem;
                }}
                h2 {{
                    color: #1e40af;
                    border-bottom: 2px solid #e5e7eb;
                    padding-bottom: 0.3rem;
                    margin-top: 2rem;
                }}
                h3 {{
                    color: #3b82f6;
                }}
                code {{
                    background: #f3f4f6;
                    padding: 0.2rem 0.4rem;
                    border-radius: 4px;
                    font-size: 0.9em;
                }}
                pre {{
                    background: #1e293b;
                    color: #e2e8f0;
                    padding: 1rem;
                    border-radius: 6px;
                    overflow-x: auto;
                }}
                pre code {{
                    background: none;
                    padding: 0;
                    color: inherit;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1rem 0;
                }}
                th, td {{
                    border: 1px solid #e5e7eb;
                    padding: 0.75rem;
                    text-align: left;
                }}
                th {{
                    background: #f3f4f6;
                    font-weight: 600;
                }}
                tr:nth-child(even) {{
                    background: #f9fafb;
                }}
                .back-link {{
                    display: inline-block;
                    margin-bottom: 1rem;
                    color: #2563eb;
                    text-decoration: none;
                    font-weight: 500;
                }}
                .back-link:hover {{
                    text-decoration: underline;
                }}
                blockquote {{
                    border-left: 4px solid #2563eb;
                    padding-left: 1rem;
                    margin-left: 0;
                    color: #64748b;
                }}
            </style>
        </head>
        <body>
            <a href="/api/v1/docs" class="back-link">← 문서 목록으로 돌아가기</a>
            <div class="content">
                {html_content}
            </div>
        </body>
        </html>
        """

        return html

    except Exception as e:
        logger.error(f"Failed to read documentation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
