"""
Table Detector Service
테이블 검출 및 구조 추출 서비스

Components:
1. Microsoft Table Transformer (TATR) - 테이블 영역 검출
2. img2table - 테이블 구조 인식 및 내용 추출
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import io

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Global model references
_tatr_model = None
_tatr_processor = None
_img2table_available = False


def initialize_models() -> Tuple[bool, bool]:
    """
    Initialize TATR and img2table models

    Returns:
        Tuple[bool, bool]: (tatr_loaded, img2table_ready)
    """
    global _tatr_model, _tatr_processor, _img2table_available

    tatr_loaded = False
    img2table_ready = False

    # Try loading TATR (optional - for better detection)
    try:
        from transformers import AutoModelForObjectDetection, AutoImageProcessor
        import torch

        logger.info("Loading Table Transformer (TATR) model...")
        _tatr_processor = AutoImageProcessor.from_pretrained(
            "microsoft/table-transformer-detection"
        )
        _tatr_model = AutoModelForObjectDetection.from_pretrained(
            "microsoft/table-transformer-detection"
        )
        _tatr_model.eval()

        # Move to GPU if available
        if torch.cuda.is_available():
            _tatr_model = _tatr_model.cuda()
            logger.info("TATR model loaded on GPU")
        else:
            logger.info("TATR model loaded on CPU")

        tatr_loaded = True
    except Exception as e:
        logger.warning(f"TATR model not loaded (optional): {e}")
        logger.info("Will use img2table's built-in detection")

    # Check img2table availability
    try:
        from img2table.document import Image as Img2TableImage
        from img2table.ocr import TesseractOCR
        _img2table_available = True
        img2table_ready = True
        logger.info("img2table library ready")
    except ImportError as e:
        logger.warning(f"img2table not available: {e}")
        # Try alternative OCR backends
        try:
            from img2table.document import Image as Img2TableImage
            _img2table_available = True
            img2table_ready = True
        except Exception:
            pass

    return tatr_loaded, img2table_ready


def detect_tables(
    image: Image.Image,
    confidence_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Detect table regions in an image using TATR

    Args:
        image: PIL Image
        confidence_threshold: Minimum confidence for detection

    Returns:
        List of detected table regions with bounding boxes
    """
    global _tatr_model, _tatr_processor

    if _tatr_model is None or _tatr_processor is None:
        # Fallback: return full image as potential table region
        logger.info("TATR not available, using full image")
        return [{
            "id": 0,
            "bbox": [0, 0, image.width, image.height],
            "confidence": 1.0,
            "label": "table"
        }]

    try:
        import torch

        # Process image
        inputs = _tatr_processor(images=image, return_tensors="pt")

        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        # Inference
        with torch.no_grad():
            outputs = _tatr_model(**inputs)

        # Post-process
        target_sizes = torch.tensor([image.size[::-1]])
        if torch.cuda.is_available():
            target_sizes = target_sizes.cuda()

        results = _tatr_processor.post_process_object_detection(
            outputs,
            threshold=confidence_threshold,
            target_sizes=target_sizes
        )[0]

        tables = []
        for idx, (score, label, box) in enumerate(zip(
            results["scores"].cpu().numpy(),
            results["labels"].cpu().numpy(),
            results["boxes"].cpu().numpy()
        )):
            tables.append({
                "id": idx,
                "bbox": box.tolist(),  # [x1, y1, x2, y2]
                "confidence": float(score),
                "label": _tatr_model.config.id2label.get(int(label), "table")
            })

        logger.info(f"Detected {len(tables)} tables")

        # Fallback: if no tables detected, use full image
        if len(tables) == 0:
            logger.info("No tables detected by TATR, using full image as fallback")
            return [{
                "id": 0,
                "bbox": [0, 0, image.width, image.height],
                "confidence": 0.5,
                "label": "table_fallback"
            }]

        return tables

    except Exception as e:
        logger.error(f"TATR detection failed: {e}")
        return [{
            "id": 0,
            "bbox": [0, 0, image.width, image.height],
            "confidence": 0.5,
            "label": "table"
        }]


def extract_table_content(
    image: Image.Image,
    ocr_engine: str = "tesseract",
    borderless: bool = True,
    min_confidence: int = 50
) -> List[Dict[str, Any]]:
    """
    Extract table structure and content using img2table

    Args:
        image: PIL Image
        ocr_engine: OCR engine to use ('tesseract', 'paddle', 'easyocr')
        borderless: Detect borderless tables
        min_confidence: Minimum OCR confidence

    Returns:
        List of extracted tables with structure and content
    """
    global _img2table_available

    if not _img2table_available:
        return [{
            "error": "img2table not available",
            "tables": []
        }]

    try:
        from img2table.document import Image as Img2TableImage

        # Get OCR engine
        ocr = _get_ocr_engine(ocr_engine)

        # Save image to bytes for img2table
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # Create img2table Image object
        img2table_doc = Img2TableImage(src=img_bytes)

        # Extract tables
        tables = img2table_doc.extract_tables(
            ocr=ocr,
            borderless_tables=borderless,
            min_confidence=min_confidence
        )

        # Convert to serializable format
        result = []
        for idx, table in enumerate(tables):
            table_data = {
                "id": idx,
                "bbox": table.bbox if hasattr(table, 'bbox') else None,
                "rows": len(table.df) if hasattr(table, 'df') else 0,
                "cols": len(table.df.columns) if hasattr(table, 'df') else 0,
                "headers": table.df.columns.tolist() if hasattr(table, 'df') else [],
                "data": table.df.values.tolist() if hasattr(table, 'df') else [],
                "html": table.df.to_html() if hasattr(table, 'df') else "",
                "dataframe_dict": table.df.to_dict() if hasattr(table, 'df') else {}
            }
            result.append(table_data)

        logger.info(f"Extracted {len(result)} tables")
        return result

    except Exception as e:
        logger.error(f"Table extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return [{
            "error": str(e),
            "tables": []
        }]


def analyze_tables(
    image: Image.Image,
    ocr_engine: str = "tesseract",
    borderless: bool = True,
    confidence_threshold: float = 0.7,
    min_confidence: int = 50
) -> Dict[str, Any]:
    """
    Full pipeline: detect tables and extract content

    Args:
        image: PIL Image
        ocr_engine: OCR engine to use
        borderless: Detect borderless tables
        confidence_threshold: TATR detection threshold
        min_confidence: OCR minimum confidence

    Returns:
        Complete analysis with regions and content
    """
    # Step 1: Detect table regions
    regions = detect_tables(image, confidence_threshold)

    # Step 2: Extract content from each region
    all_tables = []

    for region in regions:
        bbox = region.get("bbox")
        if bbox:
            # Crop region
            x1, y1, x2, y2 = [int(v) for v in bbox]
            cropped = image.crop((x1, y1, x2, y2))
        else:
            cropped = image

        # Extract tables from region
        tables = extract_table_content(
            cropped,
            ocr_engine=ocr_engine,
            borderless=borderless,
            min_confidence=min_confidence
        )

        for table in tables:
            table["region_id"] = region["id"]
            table["region_bbox"] = bbox
            table["region_confidence"] = region.get("confidence", 1.0)
            all_tables.append(table)

    return {
        "image_size": {"width": image.width, "height": image.height},
        "regions_detected": len(regions),
        "tables_extracted": len(all_tables),
        "regions": regions,
        "tables": all_tables
    }


def _get_ocr_engine(engine_name: str):
    """Get OCR engine instance"""
    try:
        if engine_name == "paddle":
            from img2table.ocr import PaddleOCR
            return PaddleOCR(lang="korean")
        elif engine_name == "easyocr":
            from img2table.ocr import EasyOCR
            return EasyOCR(lang=["ko", "en"])
        elif engine_name == "tesseract":
            from img2table.ocr import TesseractOCR
            return TesseractOCR(lang="kor+eng")
        else:
            # Default to Tesseract
            from img2table.ocr import TesseractOCR
            return TesseractOCR(lang="kor+eng")
    except ImportError as e:
        logger.warning(f"OCR engine {engine_name} not available: {e}")
        # Try fallback
        try:
            from img2table.ocr import TesseractOCR
            return TesseractOCR()
        except Exception:
            return None
