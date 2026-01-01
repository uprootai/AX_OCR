"""
PaddleOCR 3.0 Inference Service
PP-OCRv5: 13% accuracy improvement, 106 languages support
"""
import os
import logging
from typing import List, Optional, Any

import numpy as np

# PaddleOCR import
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None
    print("WARNING: PaddleOCR not installed. Install with: pip install paddleocr>=3.0.0")

from models.schemas import TextDetection
from utils.helpers import bbox_to_position

logger = logging.getLogger(__name__)


class PaddleOCRService:
    """PaddleOCR 3.0 inference service with PP-OCRv5"""

    def __init__(self):
        """Initialize PaddleOCR service"""
        self.model: Optional[Any] = None
        self.lang = os.getenv("OCR_LANG", "en")
        self.ocr_version = os.getenv("OCR_VERSION", "PP-OCRv5")

        # Device configuration
        device = os.getenv("DEVICE", "cpu")
        if os.getenv("USE_GPU", "false").lower() == "true":
            device = "gpu:0"
        self.device = device

        # Processing options
        self.use_doc_orientation = os.getenv("USE_DOC_ORIENTATION", "false").lower() == "true"
        self.use_doc_unwarping = os.getenv("USE_DOC_UNWARPING", "false").lower() == "true"
        self.use_textline_orientation = os.getenv("USE_TEXTLINE_ORIENTATION", "true").lower() == "true"

        # Detection thresholds
        self.text_det_thresh = float(os.getenv("TEXT_DET_THRESH", "0.3"))
        self.text_det_box_thresh = float(os.getenv("TEXT_DET_BOX_THRESH", "0.6"))

    def load_model(self) -> bool:
        """
        Load PaddleOCR 3.0 model (PP-OCRv5)

        Returns:
            True if model loaded successfully, False otherwise
        """
        if PaddleOCR is None:
            logger.error("PaddleOCR is not installed!")
            return False

        try:
            logger.info(f"Initializing PaddleOCR 3.0 with:")
            logger.info(f"  - OCR Version: {self.ocr_version}")
            logger.info(f"  - Language: {self.lang}")
            logger.info(f"  - Device: {self.device}")
            logger.info(f"  - Text Line Orientation: {self.use_textline_orientation}")

            # PaddleOCR 3.0 initialization
            self.model = PaddleOCR(
                ocr_version=self.ocr_version,
                lang=self.lang,
                device=self.device,
                use_doc_orientation_classify=self.use_doc_orientation,
                use_doc_unwarping=self.use_doc_unwarping,
                use_textline_orientation=self.use_textline_orientation,
                text_det_thresh=self.text_det_thresh,
                text_det_box_thresh=self.text_det_box_thresh,
                text_recognition_batch_size=6,
            )

            logger.info("PaddleOCR 3.0 (PP-OCRv5) model initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            return False

    def predict(
        self,
        img_array: np.ndarray,
        min_confidence: float = 0.5
    ) -> List[TextDetection]:
        """
        Run OCR inference on image using PP-OCRv5

        Args:
            img_array: Image as numpy array (BGR format)
            min_confidence: Minimum confidence threshold for filtering results

        Returns:
            List of TextDetection objects
        """
        if self.model is None:
            raise RuntimeError("PaddleOCR model not loaded")

        # PaddleOCR 3.0 uses predict() method
        # Returns list of OCRResult objects
        results = self.model.predict(img_array)

        logger.info(f"PaddleOCR results: {len(results) if results else 0} pages")

        detections = []

        if results and len(results) > 0:
            # Each result is an OCRResult object for a page
            for ocr_result in results:
                detections.extend(self._parse_ocr_result(ocr_result, min_confidence))

        logger.info(f"Total detections after filtering: {len(detections)}")
        return detections

    def _parse_ocr_result(
        self,
        ocr_result: Any,
        min_confidence: float
    ) -> List[TextDetection]:
        """
        Parse PaddleOCR 3.0 OCRResult object

        Args:
            ocr_result: OCRResult object from PaddleOCR 3.0
            min_confidence: Minimum confidence threshold

        Returns:
            List of TextDetection objects
        """
        detections = []

        # Try different attribute access patterns for 3.x compatibility
        try:
            # Method 1: Direct attribute access (3.0+ preferred)
            if hasattr(ocr_result, 'rec_texts'):
                rec_texts = ocr_result.rec_texts
                rec_scores = ocr_result.rec_scores
                rec_polys = getattr(ocr_result, 'rec_polys', None) or getattr(ocr_result, 'dt_polys', [])
            # Method 2: Dict-like access
            elif hasattr(ocr_result, 'get'):
                rec_texts = ocr_result.get('rec_texts', [])
                rec_scores = ocr_result.get('rec_scores', [])
                rec_polys = ocr_result.get('rec_polys', ocr_result.get('dt_polys', []))
            # Method 3: Try __getitem__
            elif hasattr(ocr_result, '__getitem__'):
                rec_texts = ocr_result['rec_texts']
                rec_scores = ocr_result['rec_scores']
                rec_polys = ocr_result.get('rec_polys', ocr_result.get('dt_polys', []))
            else:
                logger.warning(f"Unknown OCRResult format: {type(ocr_result)}")
                return []

            logger.debug(f"Parsing {len(rec_texts)} text regions")

            for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                confidence = float(score)
                if confidence < min_confidence:
                    continue

                # Get polygon if available
                poly = rec_polys[i] if i < len(rec_polys) else None
                bbox = self._normalize_bbox(poly)

                if bbox is None:
                    continue

                position = bbox_to_position(bbox)

                detection = TextDetection(
                    text=str(text),
                    confidence=confidence,
                    bbox=bbox,
                    position=position
                )
                detections.append(detection)

        except Exception as e:
            logger.error(f"Error parsing OCR result: {e}")

        return detections

    def _normalize_bbox(self, poly: Any) -> Optional[List[List[float]]]:
        """
        Normalize polygon to bbox format [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

        Args:
            poly: Polygon from OCR result (various formats)

        Returns:
            Normalized bbox or None
        """
        if poly is None:
            return None

        try:
            # Convert numpy array to list
            if hasattr(poly, 'tolist'):
                bbox = poly.tolist()
            else:
                bbox = poly

            # Ensure correct format
            if isinstance(bbox, list) and len(bbox) > 0:
                # If flat array, convert to list of points
                if not isinstance(bbox[0], (list, tuple)):
                    bbox = [[float(bbox[i]), float(bbox[i+1])] for i in range(0, len(bbox), 2)]
                else:
                    # Ensure all values are floats
                    bbox = [[float(p[0]), float(p[1])] for p in bbox]

            return bbox

        except Exception as e:
            logger.error(f"Error normalizing bbox: {e}")
            return None

    def get_info(self) -> dict:
        """Get service information"""
        return {
            "version": "3.0.0",
            "ocr_version": self.ocr_version,
            "lang": self.lang,
            "device": self.device,
            "model_loaded": self.model is not None,
            "features": {
                "doc_orientation": self.use_doc_orientation,
                "doc_unwarping": self.use_doc_unwarping,
                "textline_orientation": self.use_textline_orientation
            }
        }


# Global OCR service instance
_ocr_service: Optional[PaddleOCRService] = None


def get_ocr_service() -> Optional[PaddleOCRService]:
    """Get global OCR service instance"""
    return _ocr_service


def set_ocr_service(service: Optional[PaddleOCRService]):
    """Set global OCR service instance"""
    global _ocr_service
    _ocr_service = service


def is_service_ready() -> bool:
    """Check if OCR service is ready"""
    return _ocr_service is not None and _ocr_service.model is not None
