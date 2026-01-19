"""
Helper Utilities

OCR-YOLO 매칭 등 기타 유틸리티 함수들
"""
import logging
from typing import Dict, List, Callable, Optional

logger = logging.getLogger(__name__)


def match_yolo_with_ocr(
    yolo_detections: List[Dict],
    ocr_dimensions: List[Dict],
    iou_threshold: float = 0.3,
    calculate_bbox_iou_func: Optional[Callable] = None
) -> List[Dict]:
    """
    YOLO 검출 결과와 OCR 치수 결과를 매칭

    Args:
        yolo_detections: YOLO 검출 목록 (bbox, class_name, confidence 포함)
        ocr_dimensions: OCR 치수 목록 (bbox or location, value 포함)
        iou_threshold: IoU 임계값 (기본 0.3)
        calculate_bbox_iou_func: IoU 계산 함수 (None이면 image_utils에서 import)

    Returns:
        value 필드가 추가된 YOLO 검출 목록
    """
    # IoU 계산 함수 import (순환 참조 방지)
    if calculate_bbox_iou_func is None:
        from .image_utils import calculate_bbox_iou
        calculate_bbox_iou_func = calculate_bbox_iou

    # Debug logging (only visible when DEBUG level is enabled)
    if ocr_dimensions:
        logger.debug(f"First OCR dimension keys: {list(ocr_dimensions[0].keys())}")
        logger.debug(f"First OCR dimension sample: {ocr_dimensions[0]}")

    if yolo_detections:
        logger.debug(f"First YOLO detection keys: {list(yolo_detections[0].keys())}")
        logger.debug(f"First YOLO bbox: {yolo_detections[0].get('bbox', {})}")

    matched_detections = []

    for idx, yolo_det in enumerate(yolo_detections):
        yolo_bbox = yolo_det.get('bbox', {})
        matched_value = None
        max_iou = 0.0
        best_ocr_idx = -1

        # OCR 결과와 매칭 시도
        for ocr_idx, ocr_dim in enumerate(ocr_dimensions):
            # OCR bbox 처리: bbox 필드가 있으면 사용, 없으면 location 폴리곤을 bbox로 변환
            ocr_bbox = ocr_dim.get('bbox')
            if not ocr_bbox and 'location' in ocr_dim:
                # location은 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] 형태의 폴리곤
                location = ocr_dim['location']
                if location and len(location) >= 2:
                    # 모든 점의 x, y 좌표에서 최소/최대값 추출
                    xs = [p[0] for p in location]
                    ys = [p[1] for p in location]
                    x_min, x_max = min(xs), max(xs)
                    y_min, y_max = min(ys), max(ys)
                    ocr_bbox = {
                        'x': x_min,
                        'y': y_min,
                        'width': x_max - x_min,
                        'height': y_max - y_min
                    }

            if not ocr_bbox:
                continue

            iou = calculate_bbox_iou_func(yolo_bbox, ocr_bbox)

            # IoU가 임계값 이상이고 최대값이면 매칭
            if iou > iou_threshold and iou > max_iou:
                max_iou = iou
                matched_value = ocr_dim.get('value', ocr_dim.get('text'))
                best_ocr_idx = ocr_idx

        # 매칭 결과 추가
        matched_det = yolo_det.copy()
        if matched_value:
            matched_det['value'] = matched_value
            matched_det['matched_iou'] = round(max_iou, 3)
            logger.debug(f"YOLO #{idx} matched with OCR #{best_ocr_idx}: value='{matched_value}', IoU={max_iou:.3f}")

        matched_detections.append(matched_det)

    return matched_detections
