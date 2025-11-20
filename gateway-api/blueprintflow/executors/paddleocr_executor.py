"""
PaddleOCR Node Executor
범용 OCR API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import extract_image_input, decode_to_pil_image
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
        # 이미지 준비 (PIL Image로 변환)
        image_input = extract_image_input(inputs, context)
        image = decode_to_pil_image(image_input)

        # crop_regions 추출 (YOLO 결과로부터)
        crop_regions = inputs.get("crop_regions") or inputs.get("detections")

        # PaddleOCR API 호출
        result = await call_paddleocr(
            image=image,
            crop_regions=crop_regions
        )

        return {
            "text_results": result.get("data", {}).get("text_results", []),
            "total_texts": len(result.get("data", {}).get("text_results", [])),
            "model_used": result.get("model_used", "PaddleOCR"),
            "processing_time": result.get("processing_time", 0),
        }

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
