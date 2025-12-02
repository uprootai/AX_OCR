"""
TrOCR Executor
Microsoft Transformer OCR 실행기
"""
import os
import httpx
import logging
from typing import Dict, Any, Optional

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry
from .image_utils import prepare_image_for_api

logger = logging.getLogger(__name__)

TROCR_API_URL = os.getenv("TROCR_URL", "http://trocr-api:5009")


class TrocrExecutor(BaseNodeExecutor):
    """TrOCR 노드 실행기"""

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
        super().__init__(node_id, node_type, parameters)
        self.api_url = TROCR_API_URL
        self.logger.info(f"TrocrExecutor 생성: {node_id}")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """TrOCR 실행"""
        self.logger.info(f"TrOCR 실행 시작: {self.node_id}")

        try:
            # 이미지 준비
            file_bytes = prepare_image_for_api(inputs, context)

            # 파라미터 준비
            max_length = self.parameters.get("max_length", 64)
            num_beams = self.parameters.get("num_beams", 4)

            # API 호출
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                data = {
                    "max_length": str(max_length),
                    "num_beams": str(num_beams),
                }
                response = await client.post(
                    f"{self.api_url}/api/v1/ocr",
                    files=files,
                    data=data
                )

            if response.status_code != 200:
                raise Exception(f"TrOCR API 에러: {response.status_code} - {response.text}")

            result = response.json()
            self.logger.info(f"TrOCR 완료: {len(result.get('texts', []))}개 텍스트 검출")

            return {
                "texts": result.get("texts", []),
                "full_text": result.get("full_text", ""),
                "processing_time": result.get("processing_time_ms", 0),
                "raw_response": result,
            }

        except Exception as e:
            self.logger.error(f"TrOCR 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        max_length = self.parameters.get("max_length", 64)
        if not 16 <= max_length <= 256:
            return False, f"max_length는 16~256 범위여야 함: {max_length}"

        num_beams = self.parameters.get("num_beams", 4)
        if not 1 <= num_beams <= 10:
            return False, f"num_beams는 1~10 범위여야 함: {num_beams}"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image": {"type": "Image", "description": "OCR 처리할 이미지"}
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "texts": {"type": "array", "description": "검출된 텍스트 목록"},
                "full_text": {"type": "string", "description": "전체 텍스트"},
                "processing_time": {"type": "number", "description": "처리 시간 (ms)"},
            }
        }


# Executor 등록
ExecutorRegistry.register("trocr", TrocrExecutor)
