"""Detection Service - YOLO 검출 서비스 (전기 패널 도면 BOM 전용)

yolo-api를 호출하여 일관된 검출 결과를 보장합니다.
BlueprintFlow Builder와 동일한 모델과 파라미터를 사용합니다.
"""

import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import os
import httpx
import mimetypes

from schemas.detection import DetectionConfig, Detection, BoundingBox, VerificationStatus


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

    # 전력 설비 단선도 모델 설정
    MODEL_NAME = "전력 설비 단선도 YOLOv11N (bom_detector)"
    MODEL_SETTINGS = {
        "confidence": 0.40,
        "iou": 0.50,
        "imgsz": 1024,
        "model_type": "bom_detector"  # yolo-api 모델 타입
    }

    def __init__(self, model_path: Optional[Path] = None, pricing_db_path: Optional[str] = None):
        # yolo-api 호출 방식으로 변경 - 로컬 모델 로드 불필요
        self.pricing_db = {}
        self._load_pricing_db(pricing_db_path or "/app/classes_info_with_pricing.json")
        print(f"✅ DetectionService 초기화 완료 (yolo-api: {YOLO_API_URL})")

    def _load_pricing_db(self, pricing_db_path: str):
        """가격 데이터베이스 로드"""
        if os.path.exists(pricing_db_path):
            try:
                with open(pricing_db_path, 'r', encoding='utf-8') as f:
                    self.pricing_db = json.load(f)
                print(f"✅ 가격 DB 로드 성공: {len(self.pricing_db)} 항목")
            except Exception as e:
                print(f"❌ 가격 DB 로드 실패: {e}")
        else:
            print(f"⚠️ 가격 DB 파일 없음: {pricing_db_path}")

    def get_pricing_info(self, class_name: str) -> Dict[str, Any]:
        """클래스별 가격 정보 조회"""
        return self.pricing_db.get(class_name, {
            "모델명": "N/A",
            "비고": "",
            "단가": 0,
            "공급업체": "미정",
            "리드타임": 0
        })

    def detect(
        self,
        image_path: str,
        config: Optional[DetectionConfig] = None
    ) -> Dict[str, Any]:
        """이미지에서 전기 패널 부품 검출 (yolo-api 호출)

        BlueprintFlow Builder와 동일한 yolo-api를 사용하여
        일관된 검출 결과를 보장합니다.
        """
        import cv2
        import time

        if config is None:
            config = DetectionConfig()

        # 파라미터 설정 (BlueprintFlow nodeDefinitions.ts와 동일)
        confidence = config.confidence if config.confidence else self.MODEL_SETTINGS["confidence"]
        iou_threshold = config.iou_threshold if config.iou_threshold else self.MODEL_SETTINGS["iou"]
        imgsz = getattr(config, 'imgsz', None) or self.MODEL_SETTINGS["imgsz"]
        model_type = self.MODEL_SETTINGS["model_type"]

        start_time = time.time()

        # 이미지 정보 확인
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")

        image_height, image_width = image.shape[:2]

        print(f"🔧 yolo-api 호출: model={model_type}, conf={confidence}, iou={iou_threshold}, imgsz={imgsz}")

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
                    "use_sahi": "false",
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

                print(f"✅ yolo-api 응답: {len(raw_detections)}개 검출")

                # yolo-api 응답을 우리 형식으로 변환
                for det in raw_detections:
                    class_id = det.get("class_id", 0)

                    # 클래스 이름 및 가격 정보
                    class_name = self.CLASS_MAPPING.get(class_id, det.get("class_name", f"class_{class_id}"))
                    display_name = self.CLASS_DISPLAY_NAMES.get(class_id, class_name)
                    pricing_info = self.get_pricing_info(class_name)

                    # bbox 변환 (yolo-api는 x1,y1,x2,y2 형식)
                    bbox = det.get("bbox", {})
                    if isinstance(bbox, dict):
                        x1, y1, x2, y2 = bbox.get("x1", 0), bbox.get("y1", 0), bbox.get("x2", 0), bbox.get("y2", 0)
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
                        "model_name": self.MODEL_NAME,
                        "verification_status": VerificationStatus.PENDING.value,
                        "pricing": pricing_info,
                    }
                    detections.append(detection)
            else:
                print(f"❌ yolo-api 오류: {response.status_code} - {response.text}")
                raise Exception(f"yolo-api failed: {response.text}")

        except httpx.ConnectError as e:
            print(f"❌ yolo-api 연결 실패: {e}")
            raise Exception(f"Cannot connect to yolo-api at {YOLO_API_URL}")
        except Exception as e:
            print(f"❌ 검출 오류: {e}")
            raise

        processing_time = (time.time() - start_time) * 1000  # ms

        return {
            "detections": detections,
            "total_count": len(detections),
            "model_id": model_type,
            "processing_time_ms": processing_time,
            "image_width": image_width,
            "image_height": image_height,
        }

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

    def get_all_pricing(self) -> Dict[str, Any]:
        """전체 가격 데이터베이스"""
        return self.pricing_db.copy()
