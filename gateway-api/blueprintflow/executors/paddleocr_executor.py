"""
PaddleOCR Node Executor
범용 OCR API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
from services import call_paddleocr


class PaddleocrExecutor(BaseNodeExecutor):
    """PaddleOCR 범용 OCR 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        PaddleOCR 범용 OCR 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - crop_regions: YOLO 검출 영역 (선택사항)

        Returns:
            - text_results: OCR 텍스트 결과
            - total_texts: 총 텍스트 개수
        """
        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터 추출
        filename = self.parameters.get("filename", "workflow_image.jpg")
        min_confidence = self.parameters.get("min_confidence", 0.3)
        det_db_thresh = self.parameters.get("det_db_thresh", 0.3)
        det_db_box_thresh = self.parameters.get("det_db_box_thresh", 0.5)
        use_angle_cls = self.parameters.get("use_angle_cls", True)
        visualize = self.parameters.get("visualize", True)  # 기본값을 True로 변경하여 시각화 활성화

        # PaddleOCR API 호출
        result = await call_paddleocr(
            file_bytes=file_bytes,
            filename=filename,
            min_confidence=min_confidence,
            det_db_thresh=det_db_thresh,
            det_db_box_thresh=det_db_box_thresh,
            use_angle_cls=use_angle_cls,
            visualize=visualize
        )

        # PaddleOCR API는 detections를 반환 (data 래핑 없음)
        detections = result.get("detections", [])

        output = {
            "texts": detections,
            "total_texts": result.get("total_texts", len(detections)),
            "model_used": "PaddleOCR",
            "processing_time": result.get("processing_time", 0),
        }

        # 시각화 이미지 추가 (있는 경우)
        if result.get("visualized_image"):
            output["visualized_image"] = result["visualized_image"]

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # PaddleOCR은 특별한 파라미터가 없음
        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 이미지"
                },
                "crop_regions": {
                    "type": "array",
                    "description": "YOLO 검출 영역 (선택사항)",
                    "items": {"type": "object"}
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "text_results": {
                    "type": "array",
                    "description": "OCR 텍스트 결과"
                },
                "total_texts": {
                    "type": "integer",
                    "description": "총 텍스트 개수"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("paddleocr", PaddleocrExecutor)
