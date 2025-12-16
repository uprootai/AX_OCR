"""Detection Service - YOLO 검출 서비스 (전기 패널 도면 BOM 전용)"""

import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import os

from schemas.detection import DetectionConfig, Detection, BoundingBox, VerificationStatus


class DetectionService:
    """YOLO 기반 전기 패널 도면 검출 서비스"""

    # 전기 패널 부품 클래스 매핑 (DrawingBOMExtractor classes.txt 기반)
    CLASS_MAPPING = {
        0: "10_BUZZER_HY-256-2(AC220V)_p01",
        1: "11_HUB-8PORT_Alt 1. EDS-208A(HUB)_p01",
        2: "13_SWITCHING MODE POWER SUPPLY_TRIO-PS-1AC-24DC-5(SMPS1)_p01",
        3: "14_SWITCHING MODE POWER SUPPLY_TRIO-PS-1AC-24DC-10(SMPS2)_p01",
        4: "16_DISCONNECTING SWITCH_(SW1)_p01",
        5: "17_POWER OUTLET(CONCENT)_(PO)_p01",
        6: "18_PILOT LAMP(GREEN)_MRP-NA0G_p01",
        7: "19_AUXILIARY RELAY(1a1b)_PLC-RSC-230UC-21_p01",
        8: "2,3,4,5_CIRCUIT BREAKER_BK63H 2P_p01",
        9: "20,32_CPU1513-1PN_6ES7513-1AL01-0AB0) PLC CPU_p01",
        10: "21_CPU1214C AC-DC-RLY_6ES7214-1BG40-0XB0(PLC CPU)_p01",
        11: "22_CM1214 RS422-485_6ES7241-1CH32-0XB0(PLC RS422-485)_p01",
        12: "23,37_CM1243-5 PROFIBUS DP_6GK7243-5DX30-0XE0(PLC DP)_p01",
        13: "24,25_GRAPHIC PANEL_6AV7240-3MC07-0HA0(GP)_p01",
        14: "26_TERMINAL BLOCK(32A)_ST4_p01",
        15: "27_TERMINAL BLOCK(24A)_ST2.5_p01",
        16: "28_SM1231 AI8 x 13bit_6ES7231-4HF32-0XB0(PLC AI)_p01",
        17: "29_SM1232 AO4 x 14bit_6ES7232-4HD32-0XB0(PLC AO)_p01",
        18: "30_SM1221 DI16 x 24VDC_6ES7221-1BH32-0XB0(PLC DI 1)_p01",
        19: "31_SM1222 DO16 x RLY_6ES7222-1HH32-0XB0(PLC DO 1)_p01",
        20: "34_BUS INTERFACE_BI(BUS INTERFACE)_p01",
        21: "35_VALVE CONTROL UNIT_EHS-CM3_p01",
        22: "38_I-I CONVERTOR_PAS-200(I-I CONVERTER)_p01",
        23: "39_SELECTOR SWITCH_MRS-N2A2(2STAGE)_p01",
        24: "6_TRANSFORMER_MST600VA",
        25: "8_NOISE FILTER_WYFS06T1A (6A)(NF1)_p01",
        26: "9,9-1_EMERGENCY BUTTON_MRE-NR1R_p01",
    }

    # 간단한 클래스 이름 (표시용)
    CLASS_DISPLAY_NAMES = {
        0: "BUZZER",
        1: "HUB-8PORT",
        2: "SMPS (5A)",
        3: "SMPS (10A)",
        4: "DISCONNECTING SWITCH",
        5: "POWER OUTLET",
        6: "PILOT LAMP (GREEN)",
        7: "AUXILIARY RELAY",
        8: "CIRCUIT BREAKER",
        9: "PLC CPU (1513)",
        10: "PLC CPU (1214C)",
        11: "PLC RS422-485",
        12: "PLC PROFIBUS DP",
        13: "GRAPHIC PANEL",
        14: "TERMINAL BLOCK (32A)",
        15: "TERMINAL BLOCK (24A)",
        16: "PLC AI",
        17: "PLC AO",
        18: "PLC DI",
        19: "PLC DO",
        20: "BUS INTERFACE",
        21: "VALVE CONTROL UNIT",
        22: "I-I CONVERTER",
        23: "SELECTOR SWITCH",
        24: "TRANSFORMER",
        25: "NOISE FILTER",
        26: "EMERGENCY BUTTON",
    }

    # 파나시아 전용 모델 설정 (Streamlit과 동일하게 imgsz=1024)
    MODEL_NAME = "파나시아 YOLOv11N"
    MODEL_SETTINGS = {
        "confidence": 0.40,
        "iou": 0.50,
        "imgsz": 1024  # Streamlit과 동일
    }

    def __init__(self, model_path: Optional[Path] = None, pricing_db_path: Optional[str] = None):
        # 파나시아 전용 모델 경로 (yolo_v11n)
        self.model_path = model_path or Path("/app/models/yolo/v11n/best.pt")
        self.model = None
        self.pricing_db = {}
        self._load_model()
        self._load_pricing_db(pricing_db_path or "/app/classes_info_with_pricing.json")

    def _load_model(self):
        """YOLO 모델 로드"""
        if self.model_path and self.model_path.exists():
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(self.model_path))
                print(f"✅ YOLO 모델 로드 성공: {self.model_path}")
            except Exception as e:
                print(f"❌ 모델 로드 실패: {e}")
                self.model = None
        else:
            print(f"⚠️ 모델 파일 없음: {self.model_path}")

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
        """이미지에서 전기 패널 부품 검출 (파나시아 YOLOv11N)"""
        import cv2
        import time

        if config is None:
            config = DetectionConfig()

        # 파나시아 설정 적용 (Streamlit과 동일)
        confidence = config.confidence if config.confidence else self.MODEL_SETTINGS["confidence"]
        iou_threshold = config.iou_threshold if config.iou_threshold else self.MODEL_SETTINGS["iou"]
        # imgsz는 config에서 가져오거나 기본값 1024 사용 (Streamlit과 동일)
        imgsz = getattr(config, 'imgsz', None) or self.MODEL_SETTINGS["imgsz"]

        start_time = time.time()

        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")

        image_height, image_width = image.shape[:2]

        # 32의 배수로 맞춤
        imgsz = (imgsz // 32) * 32

        detections = []

        if self.model is not None:
            print(f"🔧 파나시아 YOLOv11N 검출: 신뢰도={confidence}, IoU={iou_threshold}, imgsz={imgsz}")

            # YOLO 검출 실행 (파나시아 최적화 설정)
            results = self.model(
                image_path,
                conf=confidence,
                iou=iou_threshold,
                imgsz=imgsz,
                device=config.device or "cpu"
            )

            # 결과 파싱
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        class_id = int(box.cls[0])
                        det_conf = float(box.conf[0])
                        xyxy = box.xyxy[0].tolist()

                        # 클래스 이름 및 가격 정보
                        class_name = self.CLASS_MAPPING.get(class_id, f"class_{class_id}")
                        display_name = self.CLASS_DISPLAY_NAMES.get(class_id, class_name)
                        pricing_info = self.get_pricing_info(class_name)

                        detection = {
                            "id": str(uuid.uuid4()),
                            "class_id": class_id,
                            "class_name": class_name,
                            "display_name": display_name,
                            "confidence": det_conf,
                            "bbox": {
                                "x1": int(xyxy[0]),
                                "y1": int(xyxy[1]),
                                "x2": int(xyxy[2]),
                                "y2": int(xyxy[3]),
                            },
                            "model_id": "panasia_yolo",
                            "model_name": self.MODEL_NAME,
                            "verification_status": VerificationStatus.PENDING.value,
                            "pricing": pricing_info,
                        }
                        detections.append(detection)
        else:
            print("⚠️ YOLO 모델이 로드되지 않아 검출을 수행할 수 없습니다")

        processing_time = (time.time() - start_time) * 1000  # ms

        return {
            "detections": detections,
            "total_count": len(detections),
            "model_id": config.model_id,
            "processing_time_ms": processing_time,
            "image_width": image_width,
            "image_height": image_height,
        }

    def add_manual_detection(
        self,
        class_name: str,
        bbox: Dict[str, float],
        model_id: str = "manual"
    ) -> Dict[str, Any]:
        """수동 검출 추가"""
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
            "confidence": 1.0,  # 수동 검출은 신뢰도 100%
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
