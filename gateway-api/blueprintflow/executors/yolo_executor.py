"""
YOLO Node Executor
객체 검출 API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
from services import call_yolo_detect


class YoloExecutor(BaseNodeExecutor):
    """YOLO 객체 검출 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        YOLO 객체 검출 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - confidence: 신뢰도 임계값 (default: 0.5)
            - iou: IoU 임계값 (default: 0.45)
            - visualize: 시각화 이미지 생성 여부 (default: True)

        Returns:
            - detections: 검출 결과 리스트
            - total_detections: 총 검출 개수
            - visualized_image: 시각화 이미지 (base64)
        """
        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터 추출
        confidence = self.parameters.get("confidence", 0.25)
        iou = self.parameters.get("iou", 0.45)
        visualize = self.parameters.get("visualize", True)
        filename = self.parameters.get("filename", "workflow_image.jpg")
        imgsz = self.parameters.get("imgsz", 640)
        model_type = self.parameters.get("model_type", "engineering")
        task = self.parameters.get("task", "detect")

        # SAHI 파라미터 (P&ID 모델은 서버에서 자동 활성화)
        use_sahi = self.parameters.get("use_sahi", False)
        slice_height = self.parameters.get("slice_height", 512)
        slice_width = self.parameters.get("slice_width", 512)
        overlap_ratio = self.parameters.get("overlap_ratio", 0.25)

        # YOLO API 호출
        result = await call_yolo_detect(
            file_bytes=file_bytes,
            filename=filename,
            conf_threshold=confidence,
            iou_threshold=iou,
            imgsz=imgsz,
            visualize=visualize,
            model_type=model_type,
            task=task,
            use_sahi=use_sahi,
            slice_height=slice_height,
            slice_width=slice_width,
            overlap_ratio=overlap_ratio
        )

        return {
            "detections": result.get("detections", []),
            "total_detections": result.get("total_detections", 0),
            "visualized_image": result.get("visualized_image", ""),
            "model_used": result.get("model", "yolov11n"),
            "processing_time": result.get("processing_time", 0),
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # confidence 검증
        if "confidence" in self.parameters:
            conf = self.parameters["confidence"]
            if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
                return False, "confidence는 0~1 사이의 숫자여야 합니다"

        # iou 검증
        if "iou" in self.parameters:
            iou = self.parameters["iou"]
            if not isinstance(iou, (int, float)) or not (0 <= iou <= 1):
                return False, "iou는 0~1 사이의 숫자여야 합니다"

        # visualize 검증
        if "visualize" in self.parameters:
            if not isinstance(self.parameters["visualize"], bool):
                return False, "visualize는 boolean 값이어야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 이미지"
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
                    "description": "검출된 객체 목록"
                },
                "total_detections": {
                    "type": "integer",
                    "description": "총 검출 개수"
                },
                "visualized_image": {
                    "type": "string",
                    "description": "시각화 이미지 (base64)"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("yolo", YoloExecutor)
