"""
eDOCr2 OCR Processing Service
"""
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
import numpy as np
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Add edocr2 to path
EDOCR2_PATH = Path("/app/edocr2").parent  # /app
sys.path.insert(0, str(EDOCR2_PATH))

# Import eDOCr2 components
try:
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
    tools = None
    Recognizer = None
    Detector = None

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


class EDOCr2Processor:
    """eDOCr2 OCR processor"""

    def __init__(self):
        """Initialize eDOCr2 processor"""
        self.recognizer_gdt: Optional[Any] = None
        self.recognizer_dim: Optional[Any] = None
        self.detector: Optional[Any] = None
        self.models_loaded = False
        self.edocr2_path = EDOCR2_PATH

    def load_models(self):
        """Load eDOCr2 models"""
        if self.models_loaded:
            return

        if not EDOCR2_AVAILABLE:
            logger.warning("⚠️ eDOCr2 not available, skipping model loading")
            return

        try:
            logger.info("📦 Loading eDOCr2 models...")
            start_time = time.time()

            models_dir = self.edocr2_path / "edocr2" / "models"

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
            self.recognizer_gdt = Recognizer(alphabet=alphabet_gdt)
            self.recognizer_gdt.model.load_weights(str(gdt_model_path))
            logger.info("  ✅ GD&T recognizer loaded")

            # Load dimension recognizer
            logger.info(f"  Loading dimension recognizer from {dim_model_path}")
            alphabet_dim = tools.ocr_pipelines.read_alphabet(str(dim_model_path))
            self.recognizer_dim = Recognizer(alphabet=alphabet_dim)
            self.recognizer_dim.model.load_weights(str(dim_model_path))
            logger.info("  ✅ Dimension recognizer loaded")

            # Load detector
            logger.info("  Loading detector")
            self.detector = Detector()
            logger.info("  ✅ Detector loaded")

            self.models_loaded = True
            elapsed = time.time() - start_time
            logger.info(f"✅ All models loaded successfully in {elapsed:.2f}s")

        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            import traceback
            traceback.print_exc()

    def process_ocr(
        self,
        file_path: Path,
        extract_dimensions: bool = True,
        extract_gdt: bool = True,
        extract_text: bool = True,
        use_vl_model: bool = False,
        visualize: bool = False,
        use_gpu_preprocessing: bool = False
    ) -> Dict[str, Any]:
        """
        Process OCR using eDOCr2 pipeline

        Args:
            file_path: Path to image file
            extract_dimensions: Extract dimension information
            extract_gdt: Extract GD&T information
            extract_text: Extract text information
            use_vl_model: Use Vision Language model
            visualize: Generate visualization
            use_gpu_preprocessing: Use GPU preprocessing

        Returns:
            OCR results dictionary
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

            if not self.models_loaded:
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

            # GPU preprocessing
            if use_gpu_preprocessing and GPU_PREPROCESS_AVAILABLE:
                logger.info("  Applying GPU preprocessing...")
                preproc_start = time.time()

                preprocessor = get_preprocessor(use_gpu=True)

                # OCR preprocessing (CLAHE + Gaussian blur, no binarization)
                img_gray = preprocessor.preprocess_pipeline(
                    img,
                    apply_clahe=True,
                    apply_blur=True,
                    apply_threshold=False,  # eDOCr2 does its own binarization
                    clahe_params={"clip_limit": 3.0, "tile_grid_size": (8, 8)},
                    blur_params={"kernel_size": 3, "sigma": 0.8}
                )

                # Convert grayscale to BGR (eDOCr2 expects color images)
                if len(img_gray.shape) == 2:
                    img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)

                preproc_time = time.time() - preproc_start
                logger.info(f"  GPU preprocessing completed in {preproc_time:.3f}s")

                # Log GPU memory usage
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
                "tables": [],
                "possible_text": []
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
                    process_img, gdt_boxes, self.recognizer_gdt
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
                    process_img, self.detector, self.recognizer_dim,
                    tools.ocr_pipelines.read_alphabet(str(self.edocr2_path / "edocr2" / "models" / "recognizer_dimensions_2.keras")),
                    frame, dim_boxes,
                    cluster_thres=20,
                    max_img_size=1048,
                    language=language,
                    backg_save=False
                )

                # Convert to API format
                dim_list = []
                possible_text_list = []

                # Process main dimensions (high confidence - contains digits)
                for dim_item in dimensions:
                    if isinstance(dim_item, dict):
                        dim_list.append({
                            "value": dim_item.get("value", 0.0),
                            "unit": dim_item.get("unit", "mm"),
                            "type": dim_item.get("type", "linear"),
                            "tolerance": dim_item.get("tolerance"),
                            "location": dim_item.get("location")
                        })
                    elif isinstance(dim_item, tuple) and len(dim_item) >= 2:
                        # Handle tuple format: (text, bbox)
                        text = str(dim_item[0]).strip()
                        if text:
                            dim_list.append({
                                "value": text,
                                "unit": "mm",
                                "type": "linear",
                                "tolerance": None,
                                "location": dim_item[1].tolist() if hasattr(dim_item[1], 'tolist') else dim_item[1]
                            })

                # Process other_info (lower confidence - may be text or misrecognized dimensions)
                for info_item in other_info:
                    if isinstance(info_item, tuple) and len(info_item) >= 2:
                        text = str(info_item[0]).strip()
                        # Apply improved filtering logic
                        if text and len(text) >= 2:
                            # Check if it could be a dimension or useful text
                            has_digit = any(c.isdigit() for c in text)
                            has_special = any(c in 'Ø±°φ⌀∅' for c in text)
                            has_alphanum = any(c.isalnum() for c in text)

                            if has_digit or has_special:
                                # Likely a dimension - add to main list
                                dim_list.append({
                                    "value": text,
                                    "unit": "mm",
                                    "type": "text_dimension",  # Mark as lower confidence
                                    "tolerance": None,
                                    "location": info_item[1].tolist() if hasattr(info_item[1], 'tolist') else info_item[1]
                                })
                            elif has_alphanum and len(text) >= 2:
                                # Text annotation or label - add to possible_text
                                possible_text_list.append({
                                    "text": text,
                                    "location": info_item[1].tolist() if hasattr(info_item[1], 'tolist') else info_item[1]
                                })

                result["dimensions"] = dim_list
                result["possible_text"] = possible_text_list
                logger.info(f"    Extracted {len(dim_list)} dimensions, {len(possible_text_list)} text annotations")

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
                result["visualization_url"] = f"/api/v1/visualization/{file_path.name}"

            logger.info(f"✅ OCR completed: {len(result['dimensions'])} dims, {len(result['gdt'])} gdts")
            return result

        except Exception as e:
            logger.error(f"❌ OCR processing failed: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


# Global processor instance
_processor: Optional[EDOCr2Processor] = None


def get_processor() -> EDOCr2Processor:
    """Get global processor instance"""
    global _processor
    if _processor is None:
        _processor = EDOCr2Processor()
    return _processor


def load_models():
    """Load models at startup"""
    processor = get_processor()
    processor.load_models()
