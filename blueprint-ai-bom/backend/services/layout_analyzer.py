"""Layout Analyzer Service - DocLayout-YOLO 기반

도면 레이아웃 분석을 위한 ML 기반 서비스
- DocLayout-YOLO 모델 활용 (YOLO 기반, 빠른 추론)
- 휴리스틱/VLM 대비 75-125x 빠른 속도
- GPU 사용량: ~4GB VRAM (RTX 3080 8GB 적합)

통합 일자: 2025-12-31
테스트 결과: rnd/experiments/doclayout_yolo/REPORT.md
"""

import os
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import torch
from PIL import Image

logger = logging.getLogger(__name__)

# 환경변수 설정
DOCLAYOUT_ENABLED = os.environ.get("DOCLAYOUT_ENABLED", "true").lower() == "true"
DOCLAYOUT_CONFIDENCE_THRESHOLD = float(os.environ.get("DOCLAYOUT_CONFIDENCE_THRESHOLD", "0.15"))
DOCLAYOUT_VLM_FALLBACK_THRESHOLD = float(os.environ.get("DOCLAYOUT_VLM_FALLBACK_THRESHOLD", "0.5"))
DOCLAYOUT_IMGSZ = int(os.environ.get("DOCLAYOUT_IMGSZ", "1024"))
DOCLAYOUT_DEVICE = os.environ.get("DOCLAYOUT_DEVICE", "cuda:0" if torch.cuda.is_available() else "cpu")


class DocLayoutClass(str, Enum):
    """DocLayout-YOLO 기본 클래스"""
    TITLE = "title"
    PLAIN_TEXT = "plain text"
    ABANDON = "abandon"
    FIGURE = "figure"
    FIGURE_CAPTION = "figure_caption"
    TABLE = "table"
    TABLE_CAPTION = "table_caption"
    TABLE_FOOTNOTE = "table_footnote"
    ISOLATE_FORMULA = "isolate_formula"
    FORMULA_CAPTION = "formula_caption"


# DocLayout 클래스 → 도면 영역 타입 매핑
DOCLAYOUT_TO_REGION_MAP = {
    "title": "TITLE_BLOCK",
    "plain text": "NOTES",
    "abandon": "OTHER",
    "figure": "MAIN_VIEW",
    "figure_caption": "NOTES",
    "table": "BOM_TABLE",
    "table_caption": "NOTES",
    "table_footnote": "NOTES",
    "isolate_formula": "OTHER",
    "formula_caption": "OTHER",
}


@dataclass
class LayoutDetection:
    """레이아웃 검출 결과"""
    class_name: str
    region_type: str  # 매핑된 도면 영역 타입
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2 (pixels)
    confidence: float
    source: str = "doclayout"


class LayoutAnalyzer:
    """DocLayout-YOLO 기반 레이아웃 분석기"""

    def __init__(self):
        self.model = None
        self.model_path = None
        self._initialized = False

        if DOCLAYOUT_ENABLED:
            self._initialize_model()

    def _initialize_model(self):
        """모델 초기화 (지연 로딩)"""
        if self._initialized:
            return

        try:
            from doclayout_yolo import YOLOv10
            from huggingface_hub import hf_hub_download

            # 모델 다운로드 (캐시됨)
            logger.info("[LayoutAnalyzer] DocLayout-YOLO 모델 다운로드 중...")
            self.model_path = hf_hub_download(
                repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
                filename="doclayout_yolo_docstructbench_imgsz1024.pt",
            )

            # 모델 로드
            logger.info(f"[LayoutAnalyzer] 모델 로드 중: {self.model_path}")
            self.model = YOLOv10(self.model_path)

            self._initialized = True
            logger.info(f"[LayoutAnalyzer] 초기화 완료 (device: {DOCLAYOUT_DEVICE})")

        except ImportError as e:
            logger.warning(f"[LayoutAnalyzer] doclayout-yolo 미설치: {e}")
            logger.warning("[LayoutAnalyzer] 설치: pip install doclayout-yolo")
            self._initialized = False

        except Exception as e:
            logger.error(f"[LayoutAnalyzer] 초기화 실패: {e}")
            self._initialized = False

    @property
    def is_available(self) -> bool:
        """모델 사용 가능 여부"""
        return self._initialized and self.model is not None

    def detect(
        self,
        image_path: str,
        conf_threshold: float = None,
        imgsz: int = None
    ) -> List[LayoutDetection]:
        """
        이미지에서 레이아웃 영역 검출

        Args:
            image_path: 이미지 파일 경로
            conf_threshold: 신뢰도 임계값 (기본값: DOCLAYOUT_CONFIDENCE_THRESHOLD)
            imgsz: 추론 이미지 크기 (기본값: DOCLAYOUT_IMGSZ)

        Returns:
            List[LayoutDetection]: 검출된 영역 목록
        """
        if not self.is_available:
            logger.warning("[LayoutAnalyzer] 모델 사용 불가, 빈 결과 반환")
            return []

        conf_threshold = conf_threshold or DOCLAYOUT_CONFIDENCE_THRESHOLD
        imgsz = imgsz or DOCLAYOUT_IMGSZ

        try:
            # 추론 실행
            results = self.model.predict(
                image_path,
                imgsz=imgsz,
                conf=conf_threshold,
                device=DOCLAYOUT_DEVICE,
            )

            detections = []

            if results and len(results) > 0:
                for det in results[0].boxes:
                    cls_id = int(det.cls)
                    cls_name = self.model.names.get(cls_id, f"class_{cls_id}")
                    confidence = float(det.conf)
                    bbox = tuple(det.xyxy[0].tolist())

                    # 도면 영역 타입으로 매핑
                    region_type = DOCLAYOUT_TO_REGION_MAP.get(cls_name, "OTHER")

                    detections.append(LayoutDetection(
                        class_name=cls_name,
                        region_type=region_type,
                        bbox=bbox,
                        confidence=confidence,
                        source="doclayout"
                    ))

            logger.info(f"[LayoutAnalyzer] {len(detections)}개 영역 검출")
            return detections

        except Exception as e:
            logger.error(f"[LayoutAnalyzer] 검출 실패: {e}")
            return []

    def detect_with_image(
        self,
        image: Image.Image,
        conf_threshold: float = None,
        imgsz: int = None
    ) -> List[LayoutDetection]:
        """
        PIL Image에서 직접 레이아웃 영역 검출

        Args:
            image: PIL Image 객체
            conf_threshold: 신뢰도 임계값
            imgsz: 추론 이미지 크기

        Returns:
            List[LayoutDetection]: 검출된 영역 목록
        """
        if not self.is_available:
            return []

        conf_threshold = conf_threshold or DOCLAYOUT_CONFIDENCE_THRESHOLD
        imgsz = imgsz or DOCLAYOUT_IMGSZ

        try:
            import numpy as np

            # PIL -> numpy array
            img_array = np.array(image)

            # 추론 실행
            results = self.model.predict(
                img_array,
                imgsz=imgsz,
                conf=conf_threshold,
                device=DOCLAYOUT_DEVICE,
            )

            detections = []

            if results and len(results) > 0:
                for det in results[0].boxes:
                    cls_id = int(det.cls)
                    cls_name = self.model.names.get(cls_id, f"class_{cls_id}")
                    confidence = float(det.conf)
                    bbox = tuple(det.xyxy[0].tolist())

                    region_type = DOCLAYOUT_TO_REGION_MAP.get(cls_name, "OTHER")

                    detections.append(LayoutDetection(
                        class_name=cls_name,
                        region_type=region_type,
                        bbox=bbox,
                        confidence=confidence,
                        source="doclayout"
                    ))

            return detections

        except Exception as e:
            logger.error(f"[LayoutAnalyzer] 검출 실패: {e}")
            return []

    def needs_vlm_fallback(self, detections: List[LayoutDetection]) -> bool:
        """
        VLM 폴백이 필요한지 확인

        조건:
        - 검출 결과 없음
        - 모든 검출의 신뢰도가 임계값 미만
        - 필수 영역(MAIN_VIEW, TITLE_BLOCK) 미검출

        Args:
            detections: 검출 결과 목록

        Returns:
            bool: VLM 폴백 필요 여부
        """
        if not detections:
            return True

        # 신뢰도 확인
        avg_confidence = sum(d.confidence for d in detections) / len(detections)
        if avg_confidence < DOCLAYOUT_VLM_FALLBACK_THRESHOLD:
            return True

        # 필수 영역 확인
        region_types = {d.region_type for d in detections}
        required_types = {"MAIN_VIEW"}  # 최소 메인 뷰는 있어야 함

        if not required_types.issubset(region_types):
            return True

        return False

    def get_stats(self, detections: List[LayoutDetection]) -> Dict[str, Any]:
        """검출 통계 반환"""
        if not detections:
            return {"total": 0, "by_class": {}, "by_region": {}}

        by_class = {}
        by_region = {}

        for det in detections:
            by_class[det.class_name] = by_class.get(det.class_name, 0) + 1
            by_region[det.region_type] = by_region.get(det.region_type, 0) + 1

        return {
            "total": len(detections),
            "by_class": by_class,
            "by_region": by_region,
            "avg_confidence": sum(d.confidence for d in detections) / len(detections),
        }


# 싱글톤 인스턴스 (지연 초기화)
_layout_analyzer = None


def get_layout_analyzer() -> LayoutAnalyzer:
    """레이아웃 분석기 인스턴스 반환 (싱글톤)"""
    global _layout_analyzer
    if _layout_analyzer is None:
        _layout_analyzer = LayoutAnalyzer()
    return _layout_analyzer
