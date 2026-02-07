"""
SAHI Sliced Inference Service

대형 이미지에서 작은 객체를 검출하기 위한 슬라이싱 기법
"""
import logging
from typing import Dict, Any, List, Optional

import torch

logger = logging.getLogger(__name__)

# SAHI 캐시 (모델 경로별)
_sahi_model_cache: Dict[str, Any] = {}


def run_sahi_inference(
    model_path: str,
    image_path: str,
    confidence: float = 0.25,
    slice_height: int = 512,
    slice_width: int = 512,
    overlap_ratio: float = 0.25,
    class_names: Optional[Dict[int, str]] = None
) -> Optional[List]:
    """
    SAHI 슬라이싱 기반 추론

    대형 이미지에서 작은 객체를 검출하기 위한 슬라이싱 기법

    Args:
        model_path: YOLO 모델 파일 경로
        image_path: 이미지 파일 경로
        confidence: 신뢰도 임계값
        slice_height: 슬라이스 높이
        slice_width: 슬라이스 너비
        overlap_ratio: 슬라이스 오버랩 비율
        class_names: 클래스 ID → 이름 매핑 (data_yaml 오버라이드용)

    Returns:
        Detection 객체 목록 또는 실패 시 None
    """
    try:
        from sahi import AutoDetectionModel
        from sahi.predict import get_sliced_prediction

        # 캐시에서 SAHI 모델 가져오기 또는 생성
        if model_path not in _sahi_model_cache:
            logger.info(f"SAHI 모델 로딩: {model_path}")
            sahi_model = AutoDetectionModel.from_pretrained(
                model_type="yolov8",
                model_path=model_path,
                confidence_threshold=confidence,
                device="cuda:0" if torch.cuda.is_available() else "cpu"
            )
            _sahi_model_cache[model_path] = sahi_model
        else:
            sahi_model = _sahi_model_cache[model_path]
            # confidence 업데이트
            sahi_model.confidence_threshold = confidence

        # SAHI 슬라이싱 추론
        result = get_sliced_prediction(
            image_path,
            sahi_model,
            slice_height=slice_height,
            slice_width=slice_width,
            overlap_height_ratio=overlap_ratio,
            overlap_width_ratio=overlap_ratio,
            perform_standard_pred=True,
            postprocess_type="NMS",
            postprocess_match_threshold=0.5
        )

        # Detection 객체 형식으로 변환
        from models.schemas import Detection
        detections = []
        for i, pred in enumerate(result.object_prediction_list):
            bbox = pred.bbox.to_xyxy()
            x1, y1, x2, y2 = bbox

            # 클래스 ID 및 이름 추출
            cls_id = pred.category.id if pred.category else 0
            # class_names 오버라이드가 있으면 사용 (data_yaml 지원)
            if class_names and cls_id in class_names:
                cls_name = class_names[cls_id]
            else:
                cls_name = pred.category.name if pred.category else "object"

            # bbox를 Dict[str, int] 형식으로 변환 (schemas.py 스키마와 일치)
            detection = Detection(
                class_id=cls_id,
                class_name=cls_name,
                confidence=round(pred.score.value, 4),
                bbox={
                    'x': int(x1),
                    'y': int(y1),
                    'width': int(x2 - x1),
                    'height': int(y2 - y1)
                }
            )
            detections.append(detection)

        logger.info(f"SAHI 검출 완료: {len(detections)}개")
        return detections

    except ImportError:
        logger.warning("SAHI not installed, falling back to standard inference")
        return None
    except Exception as e:
        logger.error(f"SAHI inference error: {e}")
        import traceback
        traceback.print_exc()
        return None


def clear_sahi_cache():
    """SAHI 모델 캐시 클리어"""
    global _sahi_model_cache
    _sahi_model_cache.clear()
    logger.info("SAHI 캐시 클리어됨")
