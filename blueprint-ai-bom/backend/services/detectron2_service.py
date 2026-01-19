"""Detectron2 Service - Instance Segmentation 서비스

Mask R-CNN 기반 인스턴스 세그멘테이션 서비스
- 27개 클래스 심볼 검출 + 픽셀 단위 마스킹
- YOLO 대비 정밀한 윤곽선 추출 가능
- 속도보다 정확도가 중요한 경우 사용

통합 일자: 2026-01-17
모델 경로: models/detectron2/model_final.pth
"""

import os
import uuid
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import numpy as np
import cv2
import torch

logger = logging.getLogger(__name__)

# Detectron2 설정
DETECTRON2_MODEL_PATH = os.environ.get(
    "DETECTRON2_MODEL_PATH",
    "/app/models/detectron2/model_final.pth"
)
DETECTRON2_DEVICE = os.environ.get(
    "DETECTRON2_DEVICE",
    "cuda:0" if torch.cuda.is_available() else "cpu"
)
DETECTRON2_CONFIDENCE_THRESHOLD = float(os.environ.get("DETECTRON2_CONFIDENCE", "0.5"))
DETECTRON2_NMS_THRESHOLD = float(os.environ.get("DETECTRON2_NMS", "0.5"))


class Detectron2Service:
    """Detectron2 기반 인스턴스 세그멘테이션 서비스"""

    # 클래스 매핑 (detection_service.py와 동일)
    CLASS_MAPPING = {
        0: "ARRESTER",
        1: "CB DS ASSY",
        2: "CT",
        3: "CVT",
        4: "DS ASSY",
        5: "ES 또는 EST",
        6: "GIS",
        7: "LA",
        8: "LS",
        9: "MOF",
        10: "NGR",
        11: "P.Fuse",
        12: "PI",
        13: "PT",
        14: "SA",
        15: "SPD",
        16: "T.C",
        17: "TR",
        18: "VT",
        19: "ㄷ형 분기",
        20: "단로기",
        21: "전동기",
        22: "전력퓨즈",
        23: "정류기",
        24: "차단기",
        25: "축전기",
        26: "피뢰기",
    }

    CLASS_DISPLAY_NAMES = {
        0: "피뢰기 (ARRESTER)",
        1: "CB DS 어셈블리",
        2: "변류기 (CT)",
        3: "용량성 변압기 (CVT)",
        4: "단로기 어셈블리 (DS)",
        5: "접지개폐기 (ES/EST)",
        6: "가스절연개폐기 (GIS)",
        7: "피뢰기 (LA)",
        8: "라인스위치 (LS)",
        9: "계기용변성기 (MOF)",
        10: "중성점접지저항 (NGR)",
        11: "전력퓨즈 (P.Fuse)",
        12: "전력량계 (PI)",
        13: "계기용변압기 (PT)",
        14: "피뢰기 (SA)",
        15: "서지보호장치 (SPD)",
        16: "접촉기 (T.C)",
        17: "변압기 (TR)",
        18: "전압변환기 (VT)",
        19: "ㄷ형 분기",
        20: "단로기",
        21: "전동기",
        22: "전력퓨즈",
        23: "정류기",
        24: "차단기",
        25: "축전기",
        26: "피뢰기",
    }

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or DETECTRON2_MODEL_PATH
        self.device = DETECTRON2_DEVICE
        self.model = None
        self.cfg = None
        self._initialized = False

        # 지연 로딩 - 실제 사용 시 초기화
        logger.info(f"[Detectron2Service] 생성됨 (model: {self.model_path}, device: {self.device})")

    def _initialize(self):
        """모델 초기화 (지연 로딩)"""
        if self._initialized:
            return True

        try:
            from detectron2.config import get_cfg
            from detectron2.engine import DefaultPredictor
            from detectron2 import model_zoo

            # Config 설정
            self.cfg = get_cfg()

            # Mask R-CNN R50-FPN 기본 설정
            self.cfg.merge_from_file(
                model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
            )

            # 커스텀 모델 설정
            self.cfg.MODEL.WEIGHTS = self.model_path
            self.cfg.MODEL.ROI_HEADS.NUM_CLASSES = 27  # background 제외 27개 클래스
            self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = DETECTRON2_CONFIDENCE_THRESHOLD
            self.cfg.MODEL.ROI_HEADS.NMS_THRESH_TEST = DETECTRON2_NMS_THRESHOLD
            self.cfg.MODEL.DEVICE = self.device

            # Predictor 생성
            self.model = DefaultPredictor(self.cfg)

            self._initialized = True
            logger.info(f"[Detectron2Service] 모델 로드 완료 (device: {self.device})")
            return True

        except ImportError as e:
            logger.error(f"[Detectron2Service] detectron2 미설치: {e}")
            logger.error("[Detectron2Service] 설치: pip install detectron2")
            return False

        except Exception as e:
            logger.error(f"[Detectron2Service] 초기화 실패: {e}")
            return False

    @property
    def is_available(self) -> bool:
        """모델 사용 가능 여부"""
        if not self._initialized:
            return self._initialize()
        return self._initialized and self.model is not None

    def detect(
        self,
        image_path: str,
        confidence: float = None,
        return_masks: bool = True,
        return_polygons: bool = True
    ) -> Dict[str, Any]:
        """
        이미지에서 인스턴스 세그멘테이션 실행

        Args:
            image_path: 이미지 파일 경로
            confidence: 신뢰도 임계값 (기본값: DETECTRON2_CONFIDENCE_THRESHOLD)
            return_masks: 마스크 반환 여부 (RLE 인코딩)
            return_polygons: 폴리곤 반환 여부 (SVG/Canvas 호환)

        Returns:
            Dict with detections, masks, polygons
        """
        start_time = time.time()

        if not self.is_available:
            raise RuntimeError("Detectron2 모델을 로드할 수 없습니다")

        # 신뢰도 임계값 업데이트
        if confidence and confidence != self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST:
            self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = confidence
            # Predictor 재생성 필요
            from detectron2.engine import DefaultPredictor
            self.model = DefaultPredictor(self.cfg)

        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")

        image_height, image_width = image.shape[:2]

        # 추론 실행
        outputs = self.model(image)

        # 결과 파싱
        instances = outputs["instances"].to("cpu")
        boxes = instances.pred_boxes.tensor.numpy() if instances.has("pred_boxes") else []
        scores = instances.scores.numpy() if instances.has("scores") else []
        classes = instances.pred_classes.numpy() if instances.has("pred_classes") else []
        masks = instances.pred_masks.numpy() if instances.has("pred_masks") else []

        detections = []

        for i in range(len(boxes)):
            class_id = int(classes[i])
            confidence_score = float(scores[i])
            bbox = boxes[i]  # x1, y1, x2, y2

            class_name = self.CLASS_MAPPING.get(class_id, f"class_{class_id}")
            display_name = self.CLASS_DISPLAY_NAMES.get(class_id, class_name)

            detection = {
                "id": str(uuid.uuid4()),
                "class_id": class_id,
                "class_name": class_name,
                "display_name": display_name,
                "confidence": confidence_score,
                "bbox": {
                    "x1": float(bbox[0]),
                    "y1": float(bbox[1]),
                    "x2": float(bbox[2]),
                    "y2": float(bbox[3]),
                },
                "model_id": "detectron2",
                "model_name": "Mask R-CNN (Detectron2)",
                "verification_status": "pending",
            }

            # 마스크 추가
            if return_masks and len(masks) > i:
                mask = masks[i]
                detection["mask"] = self._encode_mask_rle(mask)

            # 폴리곤 추가 (SVG/Canvas용)
            if return_polygons and len(masks) > i:
                mask = masks[i]
                polygons = self._mask_to_polygons(mask)
                detection["polygons"] = polygons

            detections.append(detection)

        processing_time = (time.time() - start_time) * 1000  # ms

        logger.info(f"[Detectron2Service] {len(detections)}개 검출 ({processing_time:.1f}ms)")

        return {
            "detections": detections,
            "total_count": len(detections),
            "model_id": "detectron2",
            "processing_time_ms": processing_time,
            "image_width": image_width,
            "image_height": image_height,
            "has_masks": return_masks,
            "has_polygons": return_polygons,
        }

    def _encode_mask_rle(self, mask: np.ndarray) -> Dict[str, Any]:
        """마스크를 RLE (Run-Length Encoding)로 인코딩"""
        # 바이너리 마스크를 flatten
        flat_mask = mask.flatten()

        # RLE 인코딩
        runs = []
        prev = 0
        count = 0

        for pixel in flat_mask:
            if pixel == prev:
                count += 1
            else:
                if count > 0:
                    runs.append(count)
                prev = pixel
                count = 1

        if count > 0:
            runs.append(count)

        return {
            "size": list(mask.shape),
            "counts": runs,
        }

    def _mask_to_polygons(
        self,
        mask: np.ndarray,
        simplify_tolerance: float = 1.0
    ) -> List[List[Tuple[float, float]]]:
        """마스크를 폴리곤(윤곽선)으로 변환"""
        # 바이너리 마스크를 uint8로 변환
        mask_uint8 = (mask * 255).astype(np.uint8)

        # 윤곽선 추출
        contours, _ = cv2.findContours(
            mask_uint8,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        polygons = []

        for contour in contours:
            # 윤곽선 단순화
            epsilon = simplify_tolerance * cv2.arcLength(contour, True) / 100
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # 최소 3점 이상인 경우만
            if len(approx) >= 3:
                polygon = [(float(pt[0][0]), float(pt[0][1])) for pt in approx]
                polygons.append(polygon)

        return polygons

    def _decode_mask_rle(self, rle: Dict[str, Any]) -> np.ndarray:
        """RLE 인코딩된 마스크를 디코딩"""
        size = rle["size"]
        counts = rle["counts"]

        flat_mask = []
        val = 0

        for count in counts:
            flat_mask.extend([val] * count)
            val = 1 - val

        return np.array(flat_mask).reshape(size)

    def get_class_names(self) -> List[str]:
        """사용 가능한 클래스 이름 목록"""
        return list(self.CLASS_MAPPING.values())

    def get_class_mapping(self) -> Dict[int, str]:
        """클래스 ID-이름 매핑"""
        return self.CLASS_MAPPING.copy()


# 싱글톤 인스턴스
_detectron2_service = None


def get_detectron2_service() -> Detectron2Service:
    """Detectron2 서비스 인스턴스 반환 (싱글톤)"""
    global _detectron2_service
    if _detectron2_service is None:
        _detectron2_service = Detectron2Service()
    return _detectron2_service
