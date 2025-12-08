"""
YOLO-PID Executor
P&ID 심볼 검출 API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
import httpx


class YoloPidExecutor(BaseNodeExecutor):
    """YOLO-PID 실행기 - P&ID 심볼 검출"""

    API_BASE_URL = "http://yolo-pid-api:5017"

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        YOLO-PID 심볼 검출 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - confidence: 신뢰도 임계값 (0.1-1.0)
            - iou: IoU 임계값 (0.1-1.0)
            - imgsz: 입력 이미지 크기 (320, 640, 1280)
            - visualize: 시각화

        Returns:
            - detections: 검출된 심볼 목록
            - statistics: 카테고리별 통계
            - visualization: 시각화 이미지 (base64)
        """
        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터 추출
        confidence = self.parameters.get("confidence", 0.25)
        iou = self.parameters.get("iou", 0.45)
        imgsz = self.parameters.get("imgsz", 640)
        visualize = self.parameters.get("visualize", True)
        filename = self.parameters.get("filename", "pid_image.jpg")

        # API 호출
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (filename, file_bytes, "image/jpeg")}
            data = {
                "confidence": str(confidence),
                "iou": str(iou),
                "imgsz": str(imgsz),
                "visualize": str(visualize).lower()
            }

            response = await client.post(
                f"{self.API_BASE_URL}/api/v1/process",
                files=files,
                data=data
            )

            if response.status_code != 200:
                raise Exception(f"YOLO-PID API 에러: {response.status_code} - {response.text}")

            result = response.json()

        if not result.get("success", False):
            raise Exception(f"YOLO-PID 실패: {result.get('error', 'Unknown error')}")

        data = result.get("data", {})
        visualization = data.get("visualization", "")
        return {
            "detections": data.get("detections", []),
            "statistics": data.get("statistics", {}),
            "visualized_image": visualization,  # 프론트엔드 호환 필드명
            "image": visualization,  # 대체 필드명
            "image_size": data.get("image_size", {}),
            "parameters": data.get("parameters", {}),
            "processing_time": result.get("processing_time", 0)
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # confidence 검증
        if "confidence" in self.parameters:
            conf = self.parameters["confidence"]
            if not isinstance(conf, (int, float)) or not (0.1 <= conf <= 1.0):
                return False, "confidence는 0.1~1.0 사이의 숫자여야 합니다"

        # iou 검증
        if "iou" in self.parameters:
            iou = self.parameters["iou"]
            if not isinstance(iou, (int, float)) or not (0.1 <= iou <= 1.0):
                return False, "iou는 0.1~1.0 사이의 숫자여야 합니다"

        # imgsz 검증
        if "imgsz" in self.parameters:
            imgsz = self.parameters["imgsz"]
            if imgsz not in [320, 640, 1280]:
                return False, "imgsz는 320, 640, 1280 중 하나여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 P&ID 이미지"
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "detections": {
                    "type": "array",
                    "description": "검출된 P&ID 심볼 목록"
                },
                "statistics": {
                    "type": "object",
                    "description": "카테고리별 통계"
                },
                "visualization": {
                    "type": "string",
                    "description": "시각화 이미지 (base64)"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("yolopid", YoloPidExecutor)
