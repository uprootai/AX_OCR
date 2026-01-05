"""
YOLO Integration Service - P&ID 심볼 검출을 위한 YOLO API 연동
"""
import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# YOLO API 설정
YOLO_API_URL = os.getenv("YOLO_API_URL", "http://yolo-api:5005")
YOLO_TIMEOUT = float(os.getenv("YOLO_TIMEOUT", "60"))


@dataclass
class Detection:
    """YOLO 검출 결과"""
    class_name: str
    class_id: int
    confidence: float
    bbox: dict  # {x, y, width, height}
    center: list[float]  # [cx, cy]


@dataclass
class YOLOResult:
    """YOLO API 응답 결과"""
    success: bool
    detections: list[Detection]
    total_detections: int
    class_counts: dict[str, int]
    visualized_image: Optional[str]
    processing_time: float
    error: Optional[str] = None


# P&ID 심볼 → BWMS 장비 매핑
PID_SYMBOL_TO_EQUIPMENT = {
    # 밸브 타입
    "Valve": ["Valve", "Manual Valve"],
    "Valve Ball": ["Ball Valve", "BV"],
    "Valve Angle": ["Angle Valve"],
    "Control Valve": ["Control Valve", "CV"],
    "Control Valve Globe": ["Control Valve Globe", "CV"],
    "Control Valve Angle Choke": ["Control Valve Angle Choke"],
    "ESDV Valve Ball": ["ESDV", "Emergency Shutdown Valve", "ESD Valve"],
    "ESDV Valve Butterfly": ["ESDV", "Butterfly ESDV"],
    "ESDV Valve Slab Gate": ["ESDV", "Slab Gate ESDV"],
    "DB&BBV": ["Double Block and Bleed Valve", "DBB"],
    "DB&BBV + Valve Check": ["Double Block and Bleed Valve"],
    "DB&BPV": ["Double Block and Purge Valve"],
    "Deluge": ["Deluge Valve"],

    # 플랜지/연결
    "Flange Joint": ["Flange", "Flange Joint"],
    "Flange + Triangle": ["Flange"],
    "Flange Single T-Shape": ["Flange", "T-Joint"],
    "Barred Tee": ["Barred Tee", "Tee"],

    # 계기/센서
    "Sensor": ["Sensor", "Temperature Sensor", "Pressure Sensor", "TRO Sensor"],
    "Control": ["Controller", "Control System"],
    "Ultrasonic Flow Meter": ["Flow Meter", "FT", "UFM"],

    # 기타 장비
    "Reducer": ["Reducer", "Pipe Reducer"],
    "Rupture Disc": ["Rupture Disc", "RD"],
    "Spectacle Blind": ["Spectacle Blind", "SB"],
    "Line Blindspacer": ["Line Blind", "Blindspacer"],
    "Temporary Strainer": ["Strainer", "T-Strainer", "Temporary Strainer"],
    "Injector Point": ["Injection Point", "Chemical Injection"],
    "Exit to Atmosphere": ["Vent", "Atmospheric Vent"],

    # 식별자
    "Continuity Label": ["Tag", "Equipment Tag"],
    "Arrowhead": ["Flow Direction"],
    "Arrowhead + Triangle": ["Flow Direction"],
    "Triangle": ["Connection Point"],
    "Box": ["Equipment Block", "Text Block"],
}


class YOLOService:
    """YOLO API 연동 서비스"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or YOLO_API_URL
        self.timeout = YOLO_TIMEOUT

    async def detect_pid_symbols(
        self,
        image_data: bytes,
        model_type: str = "pid_class_aware",
        confidence: float = 0.1,
        iou: float = 0.45,
        use_sahi: bool = True,
        visualize: bool = True,
    ) -> YOLOResult:
        """
        P&ID 도면에서 심볼 검출

        Args:
            image_data: 이미지 바이트 데이터
            model_type: 모델 타입 (pid_class_aware, pid_symbol, pid_class_agnostic)
            confidence: 검출 신뢰도 임계값
            iou: NMS IoU 임계값
            use_sahi: SAHI 슬라이싱 사용 여부
            visualize: 시각화 이미지 생성 여부

        Returns:
            YOLOResult: 검출 결과
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 멀티파트 폼 데이터 구성
                files = {"file": ("image.png", image_data, "image/png")}
                data = {
                    "model_type": model_type,
                    "confidence": str(confidence),
                    "iou": str(iou),
                    "use_sahi": str(use_sahi).lower(),
                    "visualize": str(visualize).lower(),
                }

                # P&ID 모델용 SAHI 파라미터
                if use_sahi and model_type.startswith("pid"):
                    data["slice_height"] = "512"
                    data["slice_width"] = "512"
                    data["overlap_ratio"] = "0.25"

                response = await client.post(
                    f"{self.base_url}/api/v1/detect",
                    files=files,
                    data=data,
                )

                if response.status_code != 200:
                    return YOLOResult(
                        success=False,
                        detections=[],
                        total_detections=0,
                        class_counts={},
                        visualized_image=None,
                        processing_time=0,
                        error=f"YOLO API error: {response.status_code} - {response.text[:200]}",
                    )

                result = response.json()

                # 응답 파싱
                if result.get("status") != "success":
                    return YOLOResult(
                        success=False,
                        detections=[],
                        total_detections=0,
                        class_counts={},
                        visualized_image=None,
                        processing_time=result.get("processing_time", 0),
                        error=result.get("message", "Unknown error"),
                    )

                # 응답 파싱 - data가 없으면 최상위에서 읽기
                data_part = result.get("data", result)
                detections = []

                for det in data_part.get("detections", []):
                    bbox = det.get("bbox", {})
                    # bbox 형식 정규화: dict 또는 list 둘 다 처리
                    if isinstance(bbox, list):
                        bbox = {"x": bbox[0], "y": bbox[1], "width": bbox[2] - bbox[0], "height": bbox[3] - bbox[1]}

                    # center 계산 (없으면)
                    center = det.get("center")
                    if not center and bbox:
                        center = [bbox.get("x", 0) + bbox.get("width", 0) / 2,
                                  bbox.get("y", 0) + bbox.get("height", 0) / 2]

                    detections.append(Detection(
                        class_name=det.get("class_name", "unknown"),
                        class_id=det.get("class_id", -1),
                        confidence=det.get("confidence", 0),
                        bbox=bbox,
                        center=center or [0, 0],
                    ))

                # class_counts 생성
                class_counts = data_part.get("class_counts", {})
                if not class_counts:
                    class_counts = {}
                    for det in detections:
                        class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1

                return YOLOResult(
                    success=True,
                    detections=detections,
                    total_detections=data_part.get("total_detections", len(detections)),
                    class_counts=class_counts,
                    visualized_image=data_part.get("visualized_image"),
                    processing_time=result.get("processing_time", 0),
                )

        except httpx.TimeoutException:
            return YOLOResult(
                success=False,
                detections=[],
                total_detections=0,
                class_counts={},
                visualized_image=None,
                processing_time=0,
                error=f"YOLO API timeout after {self.timeout}s",
            )
        except Exception as e:
            logger.error(f"YOLO detection error: {e}", exc_info=True)
            return YOLOResult(
                success=False,
                detections=[],
                total_detections=0,
                class_counts={},
                visualized_image=None,
                processing_time=0,
                error=str(e),
            )

    def map_symbols_to_equipment(
        self,
        detections: list[Detection],
    ) -> dict[str, list[dict]]:
        """
        검출된 심볼을 BWMS 장비명으로 매핑

        Args:
            detections: YOLO 검출 결과

        Returns:
            장비명별 검출 목록
        """
        equipment_map = {}

        for det in detections:
            class_name = det.class_name

            # 심볼 → 장비 매핑
            equipment_names = PID_SYMBOL_TO_EQUIPMENT.get(class_name, [class_name])

            for eq_name in equipment_names:
                if eq_name not in equipment_map:
                    equipment_map[eq_name] = []

                equipment_map[eq_name].append({
                    "symbol_class": class_name,
                    "confidence": det.confidence,
                    "bbox": det.bbox,
                    "center": det.center,
                })

        return equipment_map

    def get_detected_equipment_list(
        self,
        detections: list[Detection],
        min_confidence: float = 0.3,
    ) -> list[str]:
        """
        검출된 장비 목록 반환 (중복 제거)

        Args:
            detections: YOLO 검출 결과
            min_confidence: 최소 신뢰도

        Returns:
            검출된 장비명 목록
        """
        equipment_set = set()

        for det in detections:
            if det.confidence < min_confidence:
                continue

            class_name = det.class_name
            equipment_names = PID_SYMBOL_TO_EQUIPMENT.get(class_name, [class_name])
            equipment_set.update(equipment_names)

        return sorted(list(equipment_set))

    def generate_ocr_texts_from_detections(
        self,
        detections: list[Detection],
    ) -> list[str]:
        """
        검출 결과를 OCR 텍스트 형식으로 변환
        (OCR 검증 엔드포인트와 호환)

        Args:
            detections: YOLO 검출 결과

        Returns:
            OCR 텍스트 목록 (equipment_mapping과 호환되는 형식)
        """
        texts = []

        for det in detections:
            # 심볼 클래스명 추가
            texts.append(det.class_name)

            # 매핑된 장비명 추가
            equipment_names = PID_SYMBOL_TO_EQUIPMENT.get(det.class_name, [])
            texts.extend(equipment_names)

        return list(set(texts))


# 싱글톤 인스턴스
yolo_service = YOLOService()
