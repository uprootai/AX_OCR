"""
PaddleOCR 2.x Inference Service
PP-OCRv4: CPU compatible, 80+ languages support
"""
import os
import logging
from typing import List, Optional, Any

import numpy as np

# PaddleOCR 2.x import
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None
    print("WARNING: PaddleOCR not installed. Install with: pip install paddleocr==2.8.1")

from models.schemas import TextDetection
from utils.helpers import bbox_to_position

logger = logging.getLogger(__name__)


class PaddleOCRService:
    """PaddleOCR 2.x inference service with PP-OCRv4"""

    def __init__(self):
        """Initialize PaddleOCR service"""
        self.model: Optional[Any] = None
        self.lang = os.getenv("OCR_LANG", "en")
        self.ocr_version = os.getenv("OCR_VERSION", "PP-OCRv4")

        # Device configuration
        self.use_gpu = os.getenv("USE_GPU", "false").lower() == "true"

        # Processing options
        self.use_angle_cls = os.getenv("USE_ANGLE_CLS", "true").lower() == "true"

        # Detection thresholds
        self.det_db_thresh = float(os.getenv("TEXT_DET_THRESH", "0.3"))
        self.det_db_box_thresh = float(os.getenv("TEXT_DET_BOX_THRESH", "0.6"))

    def load_model(self) -> bool:
        """
        Load PaddleOCR 2.x model (PP-OCRv4)

        Returns:
            True if model loaded successfully, False otherwise
        """
        if PaddleOCR is None:
            logger.error("PaddleOCR is not installed!")
            return False

        try:
            logger.info(f"Initializing PaddleOCR 2.x with:")
            logger.info(f"  - OCR Version: {self.ocr_version}")
            logger.info(f"  - Language: {self.lang}")
            logger.info(f"  - Use GPU: {self.use_gpu}")
            logger.info(f"  - Use Angle Classification: {self.use_angle_cls}")

            # PaddleOCR 2.x initialization
            self.model = PaddleOCR(
                use_angle_cls=self.use_angle_cls,
                lang=self.lang,
                use_gpu=self.use_gpu,
                det_db_thresh=self.det_db_thresh,
                det_db_box_thresh=self.det_db_box_thresh,
                show_log=False,  # Disable verbose logging
                ocr_version=self.ocr_version,
            )

            logger.info(f"PaddleOCR 2.x ({self.ocr_version}) model initialized successfully")
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
        Run OCR inference on image using PP-OCRv4

        Args:
            img_array: Image as numpy array (BGR format)
            min_confidence: Minimum confidence threshold for filtering results

        Returns:
            List of TextDetection objects
        """
        if self.model is None:
            raise RuntimeError("PaddleOCR model not loaded")

        # PaddleOCR 2.x uses ocr() method
        # Returns list of results for each image
        results = self.model.ocr(img_array, cls=self.use_angle_cls)

        logger.info(f"PaddleOCR results: {len(results) if results else 0} pages")

        detections = []

        if results and len(results) > 0:
            # Each result is a list of (bbox, (text, confidence)) for a page
            for page_result in results:
                if page_result is None:
                    continue
                detections.extend(self._parse_ocr_result(page_result, min_confidence))

        logger.info(f"Total detections after filtering: {len(detections)}")
        return detections

    def _parse_ocr_result(
        self,
        page_result: List,
        min_confidence: float
    ) -> List[TextDetection]:
        """
        Parse PaddleOCR 2.x result

        Args:
            page_result: List of (bbox, (text, confidence)) tuples
            min_confidence: Minimum confidence threshold

        Returns:
            List of TextDetection objects
        """
        detections = []

        try:
            for item in page_result:
                if item is None or len(item) < 2:
                    continue

                bbox_points = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text_info = item[1]    # (text, confidence)

                if text_info is None or len(text_info) < 2:
                    continue

                text = str(text_info[0])
                confidence = float(text_info[1])

                if confidence < min_confidence:
                    continue

                # Normalize bbox
                bbox = self._normalize_bbox(bbox_points)
                if bbox is None:
                    continue

                position = bbox_to_position(bbox)

                detection = TextDetection(
                    text=text,
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
            "version": "2.8.1",
            "ocr_version": self.ocr_version,
            "lang": self.lang,
            "use_gpu": self.use_gpu,
            "model_loaded": self.model is not None,
            "features": {
                "angle_cls": self.use_angle_cls,
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
