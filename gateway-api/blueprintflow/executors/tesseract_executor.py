"""
Tesseract OCR Executor
Google Tesseract 기반 OCR 실행기
"""
import os
import httpx
import logging
from typing import Dict, Any, Optional

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry
from .image_utils import prepare_image_for_api

logger = logging.getLogger(__name__)

TESSERACT_API_URL = os.getenv("TESSERACT_URL", "http://tesseract-api:5008")


class TesseractExecutor(BaseNodeExecutor):
    """Tesseract OCR 노드 실행기"""

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
        super().__init__(node_id, node_type, parameters)
        self.api_url = TESSERACT_API_URL
        self.logger.info(f"TesseractExecutor 생성: {node_id}")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Tesseract OCR 실행"""
        self.logger.info(f"Tesseract OCR 실행 시작: {self.node_id}")

        try:
            # 이미지 준비
            file_bytes = prepare_image_for_api(inputs, context)

            # 파라미터 준비
            lang = self.parameters.get("lang", "eng")
            psm = self.parameters.get("psm", "3")
            oem = self.parameters.get("oem", "3")
            output_type = self.parameters.get("output_type", "data")

            # API 호출
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                data = {
                    "lang": lang,
                    "psm": psm,
                    "oem": oem,
                    "output_type": output_type,
                }
                response = await client.post(
                    f"{self.api_url}/api/v1/ocr",
                    files=files,
                    data=data
                )

            if response.status_code != 200:
                raise Exception(f"Tesseract API 에러: {response.status_code} - {response.text}")

            result = response.json()
            self.logger.info(f"Tesseract OCR 완료: {len(result.get('texts', []))}개 텍스트 검출")

            return {
                "texts": result.get("texts", []),
                "full_text": result.get("full_text", ""),
                "processing_time": result.get("processing_time_ms", 0),
                "raw_response": result,
            }

        except Exception as e:
            self.logger.error(f"Tesseract OCR 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        valid_langs = ["eng", "kor", "jpn", "chi_sim", "chi_tra", "deu", "fra"]
        lang = self.parameters.get("lang", "eng")
        if lang not in valid_langs:
            return False, f"지원하지 않는 언어: {lang}. 지원: {valid_langs}"
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
ExecutorRegistry.register("tesseract", TesseractExecutor)
