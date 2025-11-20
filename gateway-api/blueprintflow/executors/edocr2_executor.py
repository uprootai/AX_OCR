"""
eDOCr2 Node Executor
차원 OCR API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
from services import call_edocr2_ocr


class Edocr2Executor(BaseNodeExecutor):
    """eDOCr2 차원 OCR 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        eDOCr2 차원 OCR 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - crop_regions: YOLO 검출 영역 (선택사항)

        Returns:
            - dimensions: 추출된 차원 정보 리스트
            - total_dimensions: 총 차원 개수
            - text: 추출된 텍스트 정보
        """
        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # crop_regions 추출 (YOLO 결과로부터) - 현재는 사용하지 않음
        # crop_regions = inputs.get("crop_regions") or inputs.get("detections")

        filename = self.parameters.get("filename", "workflow_image.jpg")

        # eDOCr2 API 호출
        result = await call_edocr2_ocr(
            file_bytes=file_bytes,
            filename=filename,
            extract_dimensions=True,
            extract_gdt=True,
            extract_text=True
        )

        return {
            "dimensions": result.get("dimensions", []),
            "total_dimensions": len(result.get("dimensions", [])),
            "text": result.get("text", {}),
            "model_used": result.get("model", "eDOCr2-v2"),
            "processing_time": result.get("processing_time", 0),
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # eDOCr2는 특별한 파라미터가 없음
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
                "dimensions": {
                    "type": "array",
                    "description": "추출된 차원 정보"
                },
                "total_dimensions": {
                    "type": "integer",
                    "description": "총 차원 개수"
                },
                "text": {
                    "type": "object",
                    "description": "추출된 텍스트 정보"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("edocr2", Edocr2Executor)
