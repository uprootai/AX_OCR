"""
eDOCr v2 API Server
공학 도면 OCR 처리 마이크로서비스 (eDOCr v2 - 고급 기능)

포트: 5002
기능: 도면에서 치수, GD&T, 텍스트, 테이블 정보 추출
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
from contextlib import asynccontextmanager

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


def transform_edocr2_to_ui_format(dimensions, gdt_results, tables, other_info, scale_x=1.0, scale_y=1.0, offset_x=0, offset_y=0):
    """
    Transform eDOCr v2 output format to UI-compatible format

    v2는 v1보다 더 상세한 데이터를 제공하므로 적절히 변환

    Args:
        scale_x, scale_y: Scale factors to convert from processed image to original image
        offset_x, offset_y: Frame offset to add to coordinates
    """
    import re

    # Transform dimensions
    ui_dimensions = []
    for dim in dimensions:
        try:
            # Handle both dict and list formats
            if isinstance(dim, dict):
                text = str(dim.get('text', '0'))
                tolerance = dim.get('tolerance') or dim.get('tol')
                bbox = dim.get('bbox', [[0, 0]])
            elif isinstance(dim, list) and len(dim) >= 2:
                text = str(dim[0]) if dim[0] else '0'
                tolerance = None
                bbox = dim[1] if len(dim) > 1 else [[0, 0]]
            else:
                continue

            dim_type = 'linear'
            if 'Ø' in text or '⌀' in text:
                dim_type = 'diameter'
            elif 'R' in text[:2]:
                dim_type = 'radius'

            value_match = re.search(r'[\d.]+', text.replace('Ø', '').replace('⌀', '').replace('R', ''))
            value = float(value_match.group()) if value_match else 0.0

            # Calculate bounding box dimensions and convert to original image coordinates
            bbox_info = {}
            if bbox and len(bbox) >= 4:
                x_coords = [pt[0] for pt in bbox if len(pt) >= 2]
                y_coords = [pt[1] for pt in bbox if len(pt) >= 2]
                if x_coords and y_coords:
                    # Apply scale and offset to convert to original image coordinates
                    min_x = min(x_coords) * scale_x + offset_x
                    min_y = min(y_coords) * scale_y + offset_y
                    max_x = max(x_coords) * scale_x + offset_x
                    max_y = max(y_coords) * scale_y + offset_y

                    bbox_info = {
                        'x': int(min_x),
                        'y': int(min_y),
                        'width': int(max_x - min_x),
                        'height': int(max_y - min_y)
                    }

            if not bbox_info:
                bbox_info = {'x': 0, 'y': 0, 'width': 0, 'height': 0}

            ui_dimensions.append({
                'type': dim_type,
                'value': value,
                'unit': 'mm',
                'tolerance': tolerance,
                'bbox': bbox_info,
                '_original_bbox': bbox,  # Keep original polygon bbox for visualization
                '_original_text': text   # Keep original text for visualization
            })
        except Exception as e:
            logger.warning(f"Failed to transform dimension: {e}")
            continue

    # Transform GD&T
    ui_gdt = []
    for gdt in gdt_results:
        try:
            # Handle both dict and list formats
            if isinstance(gdt, dict):
                text = str(gdt.get('text', ''))
                bbox = gdt.get('bbox', [[0, 0]])
            elif isinstance(gdt, list) and len(gdt) >= 2:
                text = str(gdt[0]) if gdt[0] else ''
                bbox = gdt[1] if len(gdt) > 1 else [[0, 0]]
            else:
                continue

            gdt_type = text[0] if text else 'unknown'
            value_match = re.search(r'[\d.]+', text)
            value = float(value_match.group()) if value_match else 0.0

            datum_match = re.search(r'[A-Z]', text[1:]) if len(text) > 1 else None
            datum = datum_match.group() if datum_match else None

            # Calculate bounding box dimensions and convert to original image coordinates
            bbox_info = {}
            if bbox and len(bbox) >= 4:
                x_coords = [pt[0] for pt in bbox if len(pt) >= 2]
                y_coords = [pt[1] for pt in bbox if len(pt) >= 2]
                if x_coords and y_coords:
                    # Apply scale and offset to convert to original image coordinates
                    min_x = min(x_coords) * scale_x + offset_x
                    min_y = min(y_coords) * scale_y + offset_y
                    max_x = max(x_coords) * scale_x + offset_x
                    max_y = max(y_coords) * scale_y + offset_y

                    bbox_info = {
                        'x': int(min_x),
                        'y': int(min_y),
                        'width': int(max_x - min_x),
                        'height': int(max_y - min_y)
                    }

            if not bbox_info:
                bbox_info = {'x': 0, 'y': 0, 'width': 0, 'height': 0}

            ui_gdt.append({
                'type': gdt_type,
                'value': value,
                'datum': datum,
                'bbox': bbox_info,
                '_original_bbox': bbox,  # Keep original polygon bbox for visualization
                '_original_text': text   # Keep original text for visualization
            })
        except Exception as e:
            logger.warning(f"Failed to transform GD&T: {e}")
            continue

    # Transform text/infoblock with table data
    # Handle both dict and list types for other_info
    if isinstance(other_info, dict):
        ui_text = {
            'drawing_number': other_info.get('drawing_number') or other_info.get('part_number'),
            'revision': other_info.get('revision') or other_info.get('rev'),
            'title': other_info.get('title') or other_info.get('drawing_title'),
            'material': other_info.get('material') or other_info.get('mat'),
            'notes': [],
            'total_blocks': len(other_info),
            'tables': []  # v2 특별 기능: 테이블 데이터
        }

        # Collect notes from dict
        notes = []
        for key, value in other_info.items():
            if key not in ['drawing_number', 'part_number', 'revision', 'rev', 'title', 'drawing_title', 'material', 'mat']:
                if value:
                    notes.append(f"{key}: {value}")
        ui_text['notes'] = notes
    else:
        # Handle list type (fallback)
        ui_text = {
            'drawing_number': None,
            'revision': None,
            'title': None,
            'material': None,
            'notes': [str(item) for item in other_info] if other_info else [],
            'total_blocks': len(other_info) if other_info else 0,
            'tables': []
        }

    # Add table information
    if tables:
        for table in tables:
            ui_text['tables'].append({
                'rows': len(table.get('data', [])),
                'cols': len(table.get('data', [[]])[0]) if table.get('data') else 0,
                'location': table.get('bbox', [0, 0, 100, 100])
            })

    return ui_dimensions, ui_gdt, ui_text


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# eDOCr v2 imports
try:
    import cv2
    import numpy as np
    from pdf2image import convert_from_path
    import tensorflow as tf

    # eDOCr v2 modules
    from edocr2 import tools
    from edocr2.keras_ocr.recognition import Recognizer
    from edocr2.keras_ocr.detection import Detector

    EDOCR2_AVAILABLE = True
    logger.info("✅ eDOCr v2 imports successful")
except ImportError as e:
    EDOCR2_AVAILABLE = False
    logger.warning(f"⚠️ eDOCr v2 not available: {e}")

# Directories
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# Global models
recognizer_gdt = None
recognizer_dim = None
detector = None
alphabet_dim = None


# =====================
# Lifespan
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global recognizer_gdt, recognizer_dim, detector, alphabet_dim

    # Startup
    logger.info("=" * 70)
    logger.info("🚀 eDOCr v2 API Server Starting...")
    logger.info("=" * 70)

    if not EDOCR2_AVAILABLE:
        logger.warning("⚠️ eDOCr v2 not available - running in mock mode")
    else:
        try:
            logger.info("Loading eDOCr v2 models...")

            # Configure GPU memory growth and limits
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                try:
                    for gpu in gpus:
                        # Enable memory growth to avoid OOM errors
                        tf.config.experimental.set_memory_growth(gpu, True)

                        # Set memory limit to 5GB (leaving room for v1 API)
                        tf.config.set_logical_device_configuration(
                            gpu,
                            [tf.config.LogicalDeviceConfiguration(memory_limit=5120)]
                        )
                    logger.info(f"✅ Configured {len(gpus)} GPU(s) with 5GB memory limit and growth enabled")
                except RuntimeError as e:
                    # GPU already initialized, memory growth must be set at program startup
                    logger.warning(f"⚠️ GPU configuration warning: {e}")
            else:
                logger.warning("⚠️ No GPU found, running on CPU")

            # Model paths
            gdt_model = str(MODELS_DIR / 'recognizer_gdts.keras')
            dim_model = str(MODELS_DIR / 'recognizer_dimensions_2.keras')

            # Load recognizers
            logger.info(f"Loading GDT recognizer from {gdt_model}")
            alphabet_gdt = tools.ocr_pipelines.read_alphabet(gdt_model)
            recognizer_gdt = Recognizer(alphabet=alphabet_gdt)
            recognizer_gdt.model.load_weights(gdt_model)

            logger.info(f"Loading Dimensions recognizer from {dim_model}")
            alphabet_dim = tools.ocr_pipelines.read_alphabet(dim_model)
            recognizer_dim = Recognizer(alphabet=alphabet_dim)
            recognizer_dim.model.load_weights(dim_model)

            # Load detector
            logger.info("Loading Detector")
            detector = Detector()

            logger.info("✅ eDOCr v2 models loaded successfully!")

        except Exception as e:
            logger.error(f"❌ Failed to load eDOCr v2 models: {e}")
            raise

    yield

    # Shutdown
    logger.info("👋 Shutting down eDOCr v2 API...")


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="eDOCr v2 API",
    description="Engineering Drawing OCR Service (eDOCr v2 - Advanced)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def allowed_file(filename: str) -> bool:
    """파일 확장자 검증"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_ocr_v2(
    file_path: Path,
    extract_dimensions: bool = True,
    extract_gdt: bool = True,
    extract_text: bool = True,
    extract_tables: bool = True,
    visualize: bool = False,
    language: str = 'eng',
    cluster_threshold: int = 20
) -> Dict[str, Any]:
    """
    eDOCr v2 실제 OCR 처리
    """
    if not EDOCR2_AVAILABLE:
        logger.warning("eDOCr v2 not available, returning mock data")
        return {
            "dimensions": [],
            "gdt": [],
            "text": {
                "drawing_number": "MOCK-002",
                "revision": "B",
                "title": "eDOCr v2 not installed",
                "material": "Please install eDOCr v2",
                "notes": ["This is mock data - eDOCr v2 dependencies missing"],
                "total_blocks": 0,
                "tables": []
            }
        }

    try:
        logger.info(f"Processing with eDOCr v2: {file_path}")
        start_time = time.time()

        # Load image
        if file_path.suffix.lower() == '.pdf':
            images = convert_from_path(str(file_path))
            img = np.array(images[0])
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, img = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            img = cv2.merge([img, img, img])
        else:
            img = cv2.imread(str(file_path))

        logger.info(f"Image loaded: {img.shape}")

        # Store original image dimensions for bbox coordinate conversion
        original_height, original_width = img.shape[:2]
        logger.info(f"Original image size: {original_width}x{original_height}")

        # Segmentation (v2 핵심 기능)
        logger.info("Performing advanced segmentation...")
        img_boxes, frame, gdt_boxes, tables, dim_boxes = tools.layer_segm.segment_img(
            img, autoframe=True, frame_thres=0.7, GDT_thres=0.02, binary_thres=127
        )

        logger.info(f"Segmentation complete: frame={frame is not None}, gdt_boxes={len(gdt_boxes) if gdt_boxes else 0}, tables={len(tables) if tables else 0}, dim_boxes={len(dim_boxes) if dim_boxes else 0}")

        # OCR Tables (v2 특별 기능)
        table_results = []
        process_img = img.copy()
        if extract_tables and tables:
            logger.info("Processing tables...")
            table_results, updated_tables, process_img = tools.ocr_pipelines.ocr_tables(
                tables, process_img, language
            )

        # OCR GD&T
        gdt_results = []
        if extract_gdt and gdt_boxes:
            logger.info("Processing GD&T...")
            gdt_results, updated_gdt_boxes, process_img = tools.ocr_pipelines.ocr_gdt(
                process_img, gdt_boxes, recognizer_gdt
            )

        # OCR Dimensions
        dimensions = []
        other_info = {}
        frame_offset_x = 0
        frame_offset_y = 0
        scale_x = 1.0
        scale_y = 1.0
        if extract_dimensions:
            logger.info("Processing dimensions...")
            if frame:
                frame_offset_x = frame.x
                frame_offset_y = frame.y
                process_img = process_img[frame.y : frame.y + frame.h, frame.x : frame.x + frame.w]
                logger.info(f"Cropped to frame: offset=({frame_offset_x}, {frame_offset_y}), size={process_img.shape}")

            # Store size before ocr_dimensions (which may resize)
            pre_ocr_height, pre_ocr_width = process_img.shape[:2]

            dimensions, other_info, process_img, dim_tess = tools.ocr_pipelines.ocr_dimensions(
                process_img, detector, recognizer_dim, alphabet_dim, frame, dim_boxes,
                cluster_thres=cluster_threshold, max_img_size=2048, language=language, backg_save=False
            )

            # Calculate scale factor if image was resized by ocr_dimensions
            post_ocr_height, post_ocr_width = process_img.shape[:2]
            scale_x = pre_ocr_width / post_ocr_width if post_ocr_width > 0 else 1.0
            scale_y = pre_ocr_height / post_ocr_height if post_ocr_height > 0 else 1.0
            logger.info(f"OCR dimensions scale: ({scale_x:.3f}, {scale_y:.3f}), pre={pre_ocr_width}x{pre_ocr_height}, post={post_ocr_width}x{post_ocr_height}")

        # Convert numpy types
        dimensions = convert_to_serializable(dimensions)
        gdt_results = convert_to_serializable(gdt_results)
        table_results = convert_to_serializable(table_results)
        other_info = convert_to_serializable(other_info)

        # Transform to UI format
        ui_dimensions, ui_gdt, ui_text = transform_edocr2_to_ui_format(
            dimensions, gdt_results, table_results, other_info,
            scale_x=scale_x, scale_y=scale_y,
            offset_x=frame_offset_x, offset_y=frame_offset_y
        )

        # Remove internal fields before sending response
        clean_dimensions = []
        for dim in ui_dimensions:
            clean_dim = {k: v for k, v in dim.items() if not k.startswith('_')}
            clean_dimensions.append(clean_dim)

        clean_gdt = []
        for gdt in ui_gdt:
            clean_g = {k: v for k, v in gdt.items() if not k.startswith('_')}
            clean_gdt.append(clean_g)

        result = {
            "dimensions": clean_dimensions,
            "gdt": clean_gdt,
            "text": ui_text
        }

        # Visualization
        visualization_path = None
        if visualize:
            logger.info("Creating visualization...")
            vis_img = img.copy()

            # Draw dimensions with index numbers (use ui_dimensions to ensure consistency)
            for idx, dim in enumerate(ui_dimensions):
                try:
                    # Get original bbox from ui_dimensions
                    bbox = dim.get('_original_bbox', [])

                    if bbox and len(bbox) >= 4:
                        pts = np.array(bbox, np.int32).reshape((-1, 1, 2))
                        cv2.polylines(vis_img, [pts], True, (0, 255, 0), 2)

                        # Draw index number in a circle
                        label = f"D{idx}"
                        label_pos = (bbox[0][0] - 25, bbox[0][1] - 10)
                        cv2.circle(vis_img, label_pos, 15, (0, 255, 0), -1)
                        cv2.putText(vis_img, label, (label_pos[0] - 10, label_pos[1] + 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

                        # Draw extracted text value in green
                        value = dim.get('value', '')
                        unit = dim.get('unit', '')
                        if value:
                            # Combine value and unit
                            text_value = f"{value}{unit}" if unit else str(value)
                            text_pos = (int(bbox[2][0] + 5), int(bbox[2][1]))
                            cv2.putText(vis_img, text_value, text_pos,
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                except Exception as e:
                    logger.warning(f"Failed to draw dimension: {e}")
                    continue

            # Draw GD&T with index numbers (use ui_gdt to ensure consistency)
            for idx, gdt in enumerate(ui_gdt):
                try:
                    # Get original bbox from ui_gdt
                    bbox = gdt.get('_original_bbox', [])

                    if bbox and len(bbox) >= 4:
                        pts = np.array(bbox, np.int32).reshape((-1, 1, 2))
                        cv2.polylines(vis_img, [pts], True, (255, 0, 0), 2)

                        # Draw index number in a circle
                        label = f"G{idx}"
                        label_pos = (bbox[0][0] - 25, bbox[0][1] - 10)
                        cv2.circle(vis_img, label_pos, 15, (255, 0, 0), -1)
                        cv2.putText(vis_img, label, (label_pos[0] - 10, label_pos[1] + 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                        # Draw extracted text value in blue
                        text_value = gdt.get('text', '')
                        if text_value:
                            text_pos = (bbox[2][0] + 5, bbox[2][1])
                            cv2.putText(vis_img, text_value, text_pos,
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                except Exception as e:
                    logger.warning(f"Failed to draw GD&T: {e}")
                    continue

            # Draw other_info boxes with index numbers
            if isinstance(other_info, list):
                for idx, item in enumerate(other_info):
                    try:
                        if isinstance(item, list) and len(item) >= 2:
                            text = str(item[0])[:30]  # Limit text length
                            bbox = item[1] if len(item) > 1 else []
                            if bbox and len(bbox) >= 4:
                                pts = np.array(bbox, np.int32).reshape((-1, 1, 2))
                                cv2.polylines(vis_img, [pts], True, (0, 0, 255), 2)

                                # Draw index number in a circle
                                label = f"T{idx}"
                                label_pos = (bbox[0][0] - 25, bbox[0][1] - 10)
                                cv2.circle(vis_img, label_pos, 15, (0, 0, 255), -1)
                                cv2.putText(vis_img, label, (label_pos[0] - 10, label_pos[1] + 5),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                                # Draw extracted text value in red
                                if text:
                                    text_pos = (bbox[2][0] + 5, bbox[2][1])
                                    cv2.putText(vis_img, text, text_pos,
                                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    except Exception as e:
                        logger.warning(f"Failed to draw text box: {e}")
                        continue

            # Save visualization
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{file_path.stem}_vis.jpg"
            visualization_path = Path("/app/results") / filename
            cv2.imwrite(str(visualization_path), vis_img)
            result['visualization'] = str(visualization_path.name)
            logger.info(f"Visualization saved: {visualization_path.name}")

        processing_time = time.time() - start_time
        logger.info(f"✅ eDOCr v2 processing complete in {processing_time:.2f}s")

        return result

    except Exception as e:
        logger.error(f"❌ eDOCr v2 processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


# API Endpoints
@app.get("/api/v2/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "eDOCr v2 API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "edocr2_available": EDOCR2_AVAILABLE,
        "models_loaded": all([recognizer_gdt, recognizer_dim, detector]) if EDOCR2_AVAILABLE else False
    }


@app.post("/api/v2/ocr")
async def process_drawing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="도면 파일 (PDF, PNG, JPG)"),
    extract_dimensions: bool = Form(True, description="치수 정보 추출"),
    extract_gdt: bool = Form(True, description="GD&T 정보 추출"),
    extract_text: bool = Form(True, description="텍스트 정보 추출"),
    extract_tables: bool = Form(True, description="테이블 정보 추출 (v2 전용)"),
    visualize: bool = Form(False, description="시각화 이미지 생성"),
    language: str = Form('eng', description="Tesseract 언어 코드"),
    cluster_threshold: int = Form(20, description="치수 클러스터링 임계값")
):
    """
    도면 OCR 처리 (eDOCr v2 - Advanced)

    - **file**: 도면 파일 (PDF, PNG, JPG)
    - **extract_dimensions**: 치수 정보 추출 여부
    - **extract_gdt**: GD&T 정보 추출 여부
    - **extract_text**: 텍스트 정보 추출 여부
    - **extract_tables**: 테이블 정보 추출 여부 (v2 전용)
    - **visualize**: 시각화 이미지 생성 여부
    - **language**: Tesseract OCR 언어 코드
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
        result = process_ocr_v2(
            file_path,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            extract_tables=extract_tables,
            visualize=visualize,
            language=language,
            cluster_threshold=cluster_threshold
        )

        processing_time = time.time() - start_time

        # Cleanup in background
        background_tasks.add_task(lambda: file_path.unlink(missing_ok=True))

        return {
            "status": "success",
            "data": result,
            "processing_time": processing_time,
            "file_id": file_id,
            "version": "v2"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/results/{filename}")
async def get_result_file(filename: str):
    """
    결과 파일 다운로드/조회

    - **filename**: 결과 파일명 (시각화 이미지 등)
    """
    file_path = Path("/app/results") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(str(file_path), media_type="image/jpeg")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)
