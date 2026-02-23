"""Detection Service - 검출 서비스 (전기 패널 도면 BOM 전용)

지원 백엔드:
- YOLO (기본): yolo-api 호출, 빠른 검출 (~40ms)
- Detectron2: 로컬 Mask R-CNN, 인스턴스 세그멘테이션 (~200-500ms)

BlueprintFlow Builder와 동일한 모델과 파라미터를 사용합니다.
"""

import uuid
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from schemas.typed_dicts import PricingInfo, BBoxDict, DetectionDict
import json
import os
import httpx
import mimetypes

from schemas.detection import DetectionConfig, Detection, BoundingBox, VerificationStatus, DetectionBackend
from services.utils.pricing_utils import load_pricing_db, get_pricing_info
from services.detectron2_service import get_detectron2_service

logger = logging.getLogger(__name__)


# yolo-api 주소 (Docker 네트워크 내부)
YOLO_API_URL = os.getenv("YOLO_API_URL", "http://yolo-api:5005")


class DetectionService:
    """YOLO 기반 전기 패널 도면 검출 서비스 (yolo-api 호출)"""

    # 전력 설비 단선도 클래스 매핑 (bom_detector.pt 실제 클래스)
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

    # 간단한 클래스 이름 (표시용)
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

    # 모델별 기본 설정
    MODEL_CONFIGS = {
        "panasia": {
            "name": "파나시아 MCP Panel 심볼 (27종)",
            "confidence": 0.40,
            "iou": 0.50,
            "imgsz": 1024,
            "use_sahi": False,
        },
        "bom_detector": {
            "name": "전력 설비 단선도 YOLOv11N",
            "confidence": 0.40,
            "iou": 0.50,
            "imgsz": 1024,
            "use_sahi": False,
        },
        "pid_symbol": {
            "name": "P&ID 심볼 (60종)",
            "confidence": 0.10,  # P&ID는 낮은 신뢰도 권장
            "iou": 0.45,
            "imgsz": 1024,
            "use_sahi": True,  # SAHI 자동 활성화
        },
        "pid_class_aware": {
            "name": "P&ID 분류 (32종)",
            "confidence": 0.10,
            "iou": 0.45,
            "imgsz": 1024,
            "use_sahi": True,
        },
        "pid_class_agnostic": {
            "name": "P&ID 범용",
            "confidence": 0.10,
            "iou": 0.45,
            "imgsz": 1024,
            "use_sahi": True,
        },
        "engineering": {
            "name": "기계도면 심볼",
            "confidence": 0.50,
            "iou": 0.45,
            "imgsz": 640,
            "use_sahi": False,
        },
    }

    # 기본 모델 설정 (하위 호환성)
    MODEL_NAME = "파나시아 MCP Panel 심볼 (panasia)"
    MODEL_SETTINGS = {
        "confidence": 0.40,
        "iou": 0.50,
        "imgsz": 1024,
        "model_type": "panasia"  # classExamples와 매칭되는 클래스명 출력
    }

    def __init__(self, model_path: Optional[Path] = None, pricing_db_path: Optional[str] = None):
        # yolo-api 호출 방식으로 변경 - 로컬 모델 로드 불필요
        self.pricing_db = load_pricing_db(pricing_db_path or "/app/classes_info_with_pricing.json")
        logger.info(f"DetectionService 초기화 완료 (yolo-api: {YOLO_API_URL})")

    def get_pricing_info(self, class_name: str) -> PricingInfo:
        """클래스별 가격 정보 조회"""
        return get_pricing_info(self.pricing_db, class_name)

    def detect(
        self,
        image_path: str,
        config: Optional[DetectionConfig] = None
    ) -> Dict[str, Any]:
        """이미지에서 객체 검출

        지원 백엔드:
        - yolo (기본): yolo-api 호출, 빠른 검출 (~40ms)
        - detectron2: 로컬 Mask R-CNN, 인스턴스 세그멘테이션 (~200-500ms)

        지원 모델 (YOLO):
        - bom_detector: 전력 설비 단선도 (27종)
        - pid_symbol: P&ID 심볼 (60종) - BWMS P&ID 권장
        - pid_class_aware: P&ID 분류 (32종)
        - pid_class_agnostic: P&ID 범용 (1종)
        - engineering: 기계도면 심볼 (14종)
        """
        import cv2
        import time

        if config is None:
            config = DetectionConfig()

        # Detectron2 백엔드 선택 시
        if config.backend == DetectionBackend.DETECTRON2:
            return self._detect_with_detectron2(image_path, config)

        # 모델 타입 결정 (config에서 지정하거나 기본값 사용)
        model_type = getattr(config, 'model_type', None) or self.MODEL_SETTINGS["model_type"]
        model_config = self.MODEL_CONFIGS.get(model_type, self.MODEL_CONFIGS["bom_detector"])

        # 파라미터 설정 (config 값 우선, 없으면 모델별 기본값)
        confidence = config.confidence if config.confidence else model_config["confidence"]
        iou_threshold = config.iou_threshold if config.iou_threshold else model_config["iou"]
        imgsz = getattr(config, 'imgsz', None) or model_config["imgsz"]
        use_sahi = getattr(config, 'use_sahi', None)
        if use_sahi is None:
            use_sahi = model_config.get("use_sahi", False)

        logger.info(f"검출 시작: model={model_type}, conf={confidence}, sahi={use_sahi}")

        start_time = time.time()

        # 이미지 정보 확인
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")

        image_height, image_width = image.shape[:2]

        logger.debug(f"yolo-api 호출: model={model_type}, conf={confidence}, iou={iou_threshold}, imgsz={imgsz}, sahi={use_sahi}")

        detections = []

        try:
            # yolo-api 호출
            with open(image_path, 'rb') as f:
                file_bytes = f.read()

            filename = Path(image_path).name
            content_type = mimetypes.guess_type(filename)[0] or "image/png"

            with httpx.Client(timeout=120.0) as client:
                files = {"file": (filename, file_bytes, content_type)}
                data = {
                    "conf_threshold": confidence,
                    "iou_threshold": iou_threshold,
                    "imgsz": imgsz,
                    "visualize": "false",
                    "model_type": model_type,
                    "task": "detect",
                    "use_sahi": "true" if use_sahi else "false",
                    "slice_height": 512,
                    "slice_width": 512,
                    "overlap_ratio": 0.25
                }

                response = client.post(
                    f"{YOLO_API_URL}/api/v1/detect",
                    files=files,
                    data=data
                )

            if response.status_code == 200:
                yolo_response = response.json()
                raw_detections = yolo_response.get("detections", [])

                logger.info(f"yolo-api 응답: {len(raw_detections)}개 검출")

                # yolo-api 응답을 우리 형식으로 변환
                for det in raw_detections:
                    class_id = det.get("class_id", 0)

                    # 클래스 이름 및 가격 정보
                    # bom_detector 모델은 우리 매핑 사용, 다른 모델은 YOLO 응답 사용
                    if model_type == "bom_detector":
                        class_name = self.CLASS_MAPPING.get(class_id, det.get("class_name", f"class_{class_id}"))
                        display_name = self.CLASS_DISPLAY_NAMES.get(class_id, class_name)
                    else:
                        class_name = det.get("class_name", f"class_{class_id}")
                        display_name = class_name
                    pricing_info = self.get_pricing_info(class_name)

                    # bbox 변환 (yolo-api는 x,y,width,height 또는 x1,y1,x2,y2 형식)
                    bbox = det.get("bbox", {})
                    if isinstance(bbox, dict):
                        # x,y,width,height 형식 (yolo-api 기본)
                        if "width" in bbox and "height" in bbox:
                            x = bbox.get("x", 0)
                            y = bbox.get("y", 0)
                            w = bbox.get("width", 0)
                            h = bbox.get("height", 0)
                            x1, y1 = x, y
                            x2, y2 = x + w, y + h
                        # x1,y1,x2,y2 형식
                        else:
                            x1 = bbox.get("x1", 0)
                            y1 = bbox.get("y1", 0)
                            x2 = bbox.get("x2", 0)
                            y2 = bbox.get("y2", 0)
                    elif isinstance(bbox, list) and len(bbox) == 4:
                        x1, y1, x2, y2 = bbox
                    else:
                        x1, y1, x2, y2 = 0, 0, 0, 0

                    detection = {
                        "id": str(uuid.uuid4()),
                        "class_id": class_id,
                        "class_name": class_name,
                        "display_name": display_name,
                        "confidence": det.get("confidence", 0.0),
                        "bbox": {
                            "x1": int(x1),
                            "y1": int(y1),
                            "x2": int(x2),
                            "y2": int(y2),
                        },
                        "model_id": model_type,
                        "model_name": model_config.get("name", model_type),
                        "verification_status": VerificationStatus.PENDING.value,
                        "pricing": pricing_info,
                    }
                    detections.append(detection)
            else:
                logger.error(f"yolo-api 오류: {response.status_code} - {response.text}")
                raise Exception(f"yolo-api failed: {response.text}")

        except httpx.ConnectError as e:
            logger.error(f"yolo-api 연결 실패: {e}")
            raise Exception(f"Cannot connect to yolo-api at {YOLO_API_URL}")
        except Exception as e:
            logger.error(f"검출 오류: {e}")
            raise

        # 도면 마진/제목란/리비전 영역 심볼 confidence 페널티
        # 표준 도면: 제목란(하단우측), 리비전블록(상단우측), 외곽 마진
        for det in detections:
            bbox = det["bbox"]
            cx = (bbox["x1"] + bbox["x2"]) / 2
            cy = (bbox["y1"] + bbox["y2"]) / 2
            xr = cx / image_width if image_width else 0
            yr = cy / image_height if image_height else 0
            in_margin = (
                xr > 0.65 and yr > 0.85           # 하단우측 제목란
                or xr > 0.75 and yr < 0.15         # 상단우측 리비전블록 (보수적)
                or yr < 0.03 or yr > 0.97           # 상하단 외곽 마진
                or xr < 0.03 or xr > 0.97           # 좌우 외곽 마진
            )
            if in_margin:
                det["confidence"] *= 0.5
                logger.info(
                    f"마진 영역 페널티: {det['class_name']} "
                    f"conf {det['confidence'] / 0.5:.2f} → {det['confidence']:.2f} "
                    f"pos=({xr:.1%},{yr:.1%})"
                )

        processing_time = (time.time() - start_time) * 1000  # ms

        return {
            "detections": detections,
            "total_count": len(detections),
            "model_id": model_type,
            "processing_time_ms": processing_time,
            "image_width": image_width,
            "image_height": image_height,
        }

    def _detect_with_detectron2(
        self,
        image_path: str,
        config: DetectionConfig
    ) -> Dict[str, Any]:
        """Detectron2를 사용한 인스턴스 세그멘테이션

        Args:
            image_path: 이미지 파일 경로
            config: 검출 설정

        Returns:
            검출 결과 (마스크/폴리곤 포함)
        """
        detectron2_service = get_detectron2_service()

        if not detectron2_service.is_available:
            raise RuntimeError(
                "Detectron2를 사용할 수 없습니다. "
                "detectron2 설치 확인: pip install detectron2"
            )

        # Detectron2 검출 실행
        result = detectron2_service.detect(
            image_path=image_path,
            confidence=config.confidence,
            return_masks=config.return_masks,
            return_polygons=config.return_polygons,
        )

        # 가격 정보 추가
        for detection in result["detections"]:
            class_name = detection["class_name"]
            detection["pricing"] = self.get_pricing_info(class_name)

        logger.info(
            f"Detectron2 검출 완료: {result['total_count']}개, "
            f"{result['processing_time_ms']:.1f}ms"
        )

        return result

    def add_manual_detection(
        self,
        class_name: str,
        bbox: Dict[str, float],
        confidence: float = 1.0,
        model_id: str = "manual"
    ) -> Dict[str, Any]:
        """수동 검출 추가 (YOLO에서 가져온 검출도 이 메서드 사용)"""
        # 클래스 이름으로 ID 찾기
        class_id = -1
        display_name = class_name
        for cid, cname in self.CLASS_MAPPING.items():
            if cname == class_name:
                class_id = cid
                display_name = self.CLASS_DISPLAY_NAMES.get(cid, class_name)
                break

        pricing_info = self.get_pricing_info(class_name)

        return {
            "id": str(uuid.uuid4()),
            "class_id": class_id,
            "class_name": class_name,
            "display_name": display_name,
            "confidence": confidence,
            "bbox": bbox,
            "model_id": model_id,
            "verification_status": VerificationStatus.MANUAL.value,
            "pricing": pricing_info,
        }

    def get_class_names(self) -> List[str]:
        """사용 가능한 클래스 이름 목록"""
        return list(self.CLASS_MAPPING.values())

    def get_display_names(self) -> List[str]:
        """표시용 클래스 이름 목록"""
        return list(self.CLASS_DISPLAY_NAMES.values())

    def get_class_mapping(self) -> Dict[int, str]:
        """클래스 ID-이름 매핑"""
        return self.CLASS_MAPPING.copy()

    def get_all_pricing(self) -> Dict[str, PricingInfo]:
        """전체 가격 데이터베이스"""
        return self.pricing_db.copy()
