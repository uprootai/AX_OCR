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
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn


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
            bbox = dim.get('bbox', [[0, 0]])

            # Extract text and parse value
            text = str(pred.get('text', '0'))

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

            # Get location from bbox (use first point)
            location = {
                'x': int(bbox[0][0]) if len(bbox) > 0 and len(bbox[0]) > 0 else 0,
                'y': int(bbox[0][1]) if len(bbox) > 0 and len(bbox[0]) > 1 else 0
            }

            ui_dimensions.append({
                'type': dim_type,
                'value': value,
                'unit': 'mm',  # Default unit for engineering drawings
                'tolerance': tolerance,
                'location': location
            })
        except Exception as e:
            logger.warning(f"Failed to transform dimension: {e}")
            continue

    # Transform GD&T
    ui_gdt = []
    for gdt in gdt_dict:
        try:
            pred = gdt.get('pred', {})
            bbox = gdt.get('bbox', [[0, 0]])

            text = str(pred.get('text', ''))

            # Extract GD&T type (first symbol)
            gdt_type = text[0] if text else 'unknown'

            # Extract tolerance value
            value_match = re.search(r'[\d.]+', text)
            value = float(value_match.group()) if value_match else 0.0

            # Extract datum (capital letters)
            datum_match = re.search(r'[A-Z]', text[1:]) if len(text) > 1 else None
            datum = datum_match.group() if datum_match else None

            location = {
                'x': int(bbox[0][0]) if len(bbox) > 0 and len(bbox[0]) > 0 else 0,
                'y': int(bbox[0][1]) if len(bbox) > 0 and len(bbox[0]) > 1 else 0
            }

            ui_gdt.append({
                'type': gdt_type,
                'value': value,
                'datum': datum,
                'location': location
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
            logger.info("Processing GD&T...")
            gdt_dict = tools.pipeline_gdts.read_gdtbox1(
                gdt_boxes, alphabet_gdts, model_gdts,
                alphabet_dimensions, model_dimensions
            )
        else:
            gdt_dict = []

        # OCR dimensions
        if extract_dimensions:
            logger.info("Processing dimensions...")
            dimension_dict = tools.pipeline_dimensions.read_dimensions(
                str(process_img_path), alphabet_dimensions, model_dimensions, cluster_threshold
            )
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
        ui_dimensions, ui_gdt, ui_text = transform_edocr_to_ui_format(
            dimension_dict_converted, gdt_dict_converted, infoblock_dict_converted
        )

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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
