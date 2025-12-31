"""
eDOCr v1 OCR Service
OCR 처리 비즈니스 로직
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import HTTPException

from ..utils import (
    convert_to_serializable,
    transform_edocr_to_ui_format,
    UPLOAD_DIR,
    RESULTS_DIR,
    ALPHABET_DIMENSIONS,
    ALPHABET_INFOBLOCK,
    ALPHABET_GDTS
)

logger = logging.getLogger(__name__)


class OCRService:
    """eDOCr v1 OCR processing service"""

    def __init__(self):
        self.model_infoblock = None
        self.model_dimensions = None
        self.model_gdts = None
        self.edocr_available = False

        # Try to import eDOCr dependencies
        self._init_dependencies()

    def _init_dependencies(self):
        """Initialize eDOCr dependencies"""
        try:
            import cv2
            import numpy as np
            from skimage import io
            from pdf2image import convert_from_path

            # eDOCr v1 modules
            from eDOCr import tools
            from eDOCr.keras_ocr import tools as keras_tools

            self.cv2 = cv2
            self.np = np
            self.io = io
            self.convert_from_path = convert_from_path
            self.tools = tools
            self.keras_tools = keras_tools

            self.edocr_available = True
            logger.info("eDOCr v1 dependencies loaded successfully")
        except ImportError as e:
            self.edocr_available = False
            logger.warning(f"eDOCr v1 not available: {e}")

    def load_models(self):
        """Load eDOCr v1 models (called during app startup)"""
        if not self.edocr_available:
            logger.warning("eDOCr v1 not available - running in mock mode")
            return

        try:
            logger.info("Loading eDOCr v1 models...")

            # Models auto-download from GitHub Releases
            self.model_infoblock = self.keras_tools.download_and_verify(
                url="https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_infoblock.h5",
                filename="recognizer_infoblock.h5",
                sha256="e0a317e07ce75235f67460713cf1b559e02ae2282303eec4a1f76ef211fcb8e8",
            )

            self.model_dimensions = self.keras_tools.download_and_verify(
                url="https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_dimensions.h5",
                filename="recognizer_dimensions.h5",
                sha256="a1c27296b1757234a90780ccc831762638b9e66faf69171f5520817130e05b8f",
            )

            self.model_gdts = self.keras_tools.download_and_verify(
                url="https://github.com/javvi51/eDOCr/releases/download/v1.0.0/recognizer_gdts.h5",
                filename="recognizer_gdts.h5",
                sha256="58acf6292a43ff90a344111729fc70cf35f0c3ca4dfd622016456c0b29ef2a46",
            )

            logger.info("eDOCr v1 models loaded successfully!")

        except Exception as e:
            logger.error(f"Failed to load eDOCr v1 models: {e}")
            raise

    def configure_gpu(self):
        """Configure GPU memory settings"""
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
                logger.info(f"Configured {len(gpus)} GPU(s) with 3GB memory limit")
            else:
                logger.warning("No GPU found, running on CPU")
        except Exception as e:
            logger.warning(f"GPU configuration failed: {e}")

    @property
    def models_loaded(self) -> bool:
        """Check if all models are loaded"""
        return all([self.model_infoblock, self.model_dimensions, self.model_gdts])

    def process_ocr(
        self,
        file_path: Path,
        extract_dimensions: bool = True,
        extract_gdt: bool = True,
        extract_text: bool = True,
        visualize: bool = False,
        remove_watermark: bool = False,
        cluster_threshold: int = 20
    ) -> Dict[str, Any]:
        """
        Process OCR using eDOCr v1

        Args:
            file_path: Path to input image/PDF
            extract_dimensions: Extract dimension information
            extract_gdt: Extract GD&T information
            extract_text: Extract text/infoblock
            visualize: Generate visualization image
            remove_watermark: Remove watermark before processing
            cluster_threshold: Dimension clustering threshold (px)

        Returns:
            Dict with dimensions, gdt, text, and optional visualization_url
        """
        if not self.edocr_available:
            # Fallback to mock if eDOCr not available
            logger.warning("eDOCr v1 not available, returning mock data")
            return self._get_mock_result()

        try:
            logger.info(f"Processing with eDOCr v1: {file_path}")
            start_time = time.time()

            # Load image
            if file_path.suffix.lower() == '.pdf':
                images = self.convert_from_path(str(file_path))
                img = self.np.array(images[0])
            else:
                img = self.cv2.imread(str(file_path))

            logger.info(f"Image loaded: {img.shape}")

            # Remove watermark if requested
            if remove_watermark:
                logger.info("Removing watermark...")
                img = self.tools.watermark.handle(img)

            # Box detection
            logger.info("Detecting boxes...")
            class_list, img_boxes = self.tools.box_tree.findrect(img)

            # Process rectangles
            logger.info("Processing rectangles...")
            boxes_infoblock, gdt_boxes, cl_frame, process_img = self.tools.img_process.process_rect(class_list, img)

            logger.info(f"Found {len(gdt_boxes)} GDT boxes")

            # Save processed image
            process_img_path = RESULTS_DIR / f"{file_path.stem}_process.jpg"
            self.io.imsave(str(process_img_path), process_img)

            # OCR infoblock
            if extract_text:
                logger.info("Processing infoblock...")
                infoblock_dict = self.tools.pipeline_infoblock.read_infoblocks(
                    boxes_infoblock, img, ALPHABET_INFOBLOCK, self.model_infoblock
                )
            else:
                infoblock_dict = {}

            # OCR GD&T
            if extract_gdt:
                logger.info(f"Processing GD&T with {len(gdt_boxes)} boxes...")
                gdt_dict = self.tools.pipeline_gdts.read_gdtbox1(
                    gdt_boxes, ALPHABET_GDTS, self.model_gdts,
                    ALPHABET_DIMENSIONS, self.model_dimensions
                )
                logger.info(f"GDT extraction returned {len(gdt_dict) if gdt_dict else 0} results")
            else:
                gdt_dict = []

            # OCR dimensions
            if extract_dimensions:
                logger.info("Processing dimensions...")
                dimension_dict = self.tools.pipeline_dimensions.read_dimensions(
                    str(process_img_path), ALPHABET_DIMENSIONS, self.model_dimensions, cluster_threshold
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
                result["visualization_url"] = self._create_visualization(
                    img, file_path.stem, original_infoblock_dict,
                    original_gdt_dict, original_dimension_dict, cl_frame
                )

            # Save boxes image
            boxes_path = RESULTS_DIR / f"{file_path.stem}_boxes.jpg"
            self.io.imsave(str(boxes_path), img_boxes)

            # Save data (use original eDOCr format)
            self.tools.output.record_data(
                str(RESULTS_DIR), file_path.stem,
                original_infoblock_dict, original_gdt_dict, original_dimension_dict
            )

            processing_time = time.time() - start_time
            logger.info(f"eDOCr v1 processing complete in {processing_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"eDOCr v1 processing failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    def _create_visualization(
        self,
        img,
        file_stem: str,
        infoblock_dict,
        gdt_dict,
        dimension_dict,
        cl_frame
    ) -> str:
        """Create visualization image and return URL"""
        logger.info("Creating visualization...")
        color_palette = {
            'infoblock': (180, 220, 250),
            'gdts': (94, 204, 243),
            'dimensions': (93, 206, 175),
            'frame': (167, 234, 82),
            'flag': (241, 65, 36)
        }

        mask_img = self.tools.output.mask_the_drawing(
            img, infoblock_dict, gdt_dict, dimension_dict, cl_frame, color_palette
        )

        mask_path = RESULTS_DIR / f"{file_stem}_mask.jpg"
        self.io.imsave(str(mask_path), mask_img)
        logger.info(f"Visualization saved: {mask_path}")

        return f"/api/v1/visualization/{mask_path.name}"

    def _get_mock_result(self) -> Dict[str, Any]:
        """Return mock result when eDOCr is not available"""
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


# Singleton instance
ocr_service = OCRService()
