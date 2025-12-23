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

        # 파라미터 추출 (기본값은 nodeDefinitions.ts에서 정의됨)
        # self.parameters는 Frontend에서 전달된 값이므로 기본값 없이 직접 사용
        confidence = self.parameters["confidence"]
        iou = self.parameters["iou"]
        visualize = self.parameters["visualize"]
        filename = self.parameters.get("filename", "workflow_image.jpg")  # filename만 예외 (UI에 노출 안됨)
        imgsz = self.parameters["imgsz"]
        model_type = self.parameters["model_type"]
        task = self.parameters["task"]

        # SAHI 파라미터
        use_sahi = self.parameters["use_sahi"]
        slice_height = self.parameters["slice_height"]
        slice_width = self.parameters["slice_width"]
        overlap_ratio = self.parameters["overlap_ratio"]

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

        # 원본 이미지를 패스스루 (Blueprint AI BOM 등 후속 노드에서 필요)
        import base64
        original_image = inputs.get("image", "")
        if not original_image and file_bytes:
            # file_bytes가 있으면 base64로 인코딩
            original_image = base64.b64encode(file_bytes).decode("utf-8")

        output = {
            "image": original_image,  # 원본 이미지 패스스루
            "detections": result.get("detections", []),
            "total_detections": result.get("total_detections", 0),
            "visualized_image": result.get("visualized_image", ""),
            "model_used": result.get("model", "yolov11n"),
            "processing_time": result.get("processing_time", 0),
        }

        # drawing_type 패스스루 (BOM 세션 생성에 필요)
        if inputs.get("drawing_type"):
            output["drawing_type"] = inputs["drawing_type"]

        return output

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
