"""
PaddleOCR Inference Service
"""
import os
import logging
from typing import List, Dict, Optional, Any

import numpy as np

# PaddleOCR import
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None
    print("WARNING: PaddleOCR not installed. Install with: pip install paddleocr")

from models.schemas import TextDetection
from utils.helpers import bbox_to_position

logger = logging.getLogger(__name__)


class PaddleOCRService:
    """PaddleOCR inference service"""

    def __init__(self):
        """Initialize PaddleOCR service"""
        self.model: Optional[Any] = None
        self.use_gpu = os.getenv("USE_GPU", "false").lower() == "true"
        self.use_angle_cls = os.getenv("USE_ANGLE_CLS", "true").lower() == "true"
        self.lang = os.getenv("OCR_LANG", "en")

    def load_model(self) -> bool:
        """
        Load PaddleOCR model

        Returns:
            True if model loaded successfully, False otherwise
        """
        if PaddleOCR is None:
            logger.error("PaddleOCR is not installed!")
            return False

        try:
            logger.info(f"Initializing PaddleOCR with GPU={self.use_gpu}, LANG={self.lang}, USE_ANGLE_CLS={self.use_angle_cls}")

            # PaddleOCR 3.x uses different parameter names
            self.model = PaddleOCR(
                use_textline_orientation=self.use_angle_cls,  # 텍스트 회전 감지
                lang=self.lang,  # 언어 설정
                # use_gpu is deprecated in 3.x, GPU is auto-detected
                text_det_thresh=0.3,  # 텍스트 검출 임계값
                text_det_box_thresh=0.5,  # 박스 임계값
                text_recognition_batch_size=6,  # 배치 크기
            )

            logger.info("PaddleOCR model initialized successfully")
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
        Run OCR inference on image

        Args:
            img_array: Image as numpy array (BGR format)
            min_confidence: Minimum confidence threshold for filtering results

        Returns:
            List of TextDetection objects
        """
        if self.model is None:
            raise RuntimeError("PaddleOCR model not loaded")

        # PaddleOCR 실행
        # NOTE: PaddleOCR 3.x returns list of OCRResult objects (dict-like)
        results = self.model.ocr(img_array)

        logger.info(f"PaddleOCR results type: {type(results)}, len: {len(results) if hasattr(results, '__len__') else 'N/A'}")

        # Handle PaddleOCR 3.x OCRResult format
        detections = []

        if results and len(results) > 0:
            # results is a list, typically with one OCRResult per page
            ocr_result = results[0]  # Get first page result

            # OCRResult is a dict-like object with keys: 'rec_texts', 'rec_scores', 'rec_polys'
            if hasattr(ocr_result, 'get'):
                rec_texts = ocr_result.get('rec_texts', [])
                rec_scores = ocr_result.get('rec_scores', [])
                rec_polys = ocr_result.get('rec_polys', ocr_result.get('dt_polys', []))

                logger.info(f"Detected {len(rec_texts)} text regions")

                # Zip together: polys, texts, scores
                for poly, text, score in zip(rec_polys, rec_texts, rec_scores):
                    # Convert numpy array to list of [x, y] points
                    if hasattr(poly, 'tolist'):
                        bbox = poly.tolist()
                    else:
                        bbox = poly

                    # Ensure bbox is in correct format [[x1,y1], [x2,y2], ...]
                    if isinstance(bbox, list) and len(bbox) > 0:
                        if not isinstance(bbox[0], list):
                            # Convert from flat array to list of points
                            bbox = [[float(bbox[i]), float(bbox[i+1])] for i in range(0, len(bbox), 2)]

                    # Filter by confidence
                    confidence = float(score)
                    if confidence < min_confidence:
                        continue

                    # Calculate position from bbox
                    position = bbox_to_position(bbox)

                    detection = TextDetection(
                        text=str(text),
                        confidence=confidence,
                        bbox=bbox,
                        position=position
                    )
                    detections.append(detection)
            else:
                logger.warning(f"Unexpected OCRResult format: {type(ocr_result)}")
        else:
            logger.warning("No OCR results returned")

        return detections


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
