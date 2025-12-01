"""
OCR Ensemble Executor
다중 OCR 엔진 앙상블 실행기
"""
import os
import httpx
import logging
from typing import Dict, Any, Optional

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry
from .image_utils import prepare_image_for_api

logger = logging.getLogger(__name__)

OCR_ENSEMBLE_API_URL = os.getenv("OCR_ENSEMBLE_URL", "http://ocr-ensemble-api:5011")


class OcrEnsembleExecutor(BaseNodeExecutor):
    """OCR 앙상블 노드 실행기"""

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
        super().__init__(node_id, node_type, parameters)
        self.api_url = OCR_ENSEMBLE_API_URL
        self.logger.info(f"OcrEnsembleExecutor 생성: {node_id}")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """OCR 앙상블 실행"""
        self.logger.info(f"OCR Ensemble 실행 시작: {self.node_id}")

        try:
            # 이미지 준비
            file_bytes = prepare_image_for_api(inputs, context)

            # 파라미터 준비
            engines = self.parameters.get("engines", ["edocr2", "paddleocr", "tesseract", "trocr"])
            weights = self.parameters.get("weights", {
                "edocr2": 0.4,
                "paddleocr": 0.35,
                "tesseract": 0.15,
                "trocr": 0.10
            })
            voting_method = self.parameters.get("voting_method", "weighted")
            confidence_threshold = self.parameters.get("confidence_threshold", 0.5)

            # API 호출
            async with httpx.AsyncClient(timeout=180.0) as client:
                files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                data = {
                    "engines": ",".join(engines) if isinstance(engines, list) else engines,
                    "voting_method": voting_method,
                    "confidence_threshold": str(confidence_threshold),
                }
                # weights를 JSON으로 전달
                if weights:
                    import json
                    data["weights"] = json.dumps(weights)

                response = await client.post(
                    f"{self.api_url}/api/v1/ocr/ensemble",
                    files=files,
                    data=data
                )

            if response.status_code != 200:
                raise Exception(f"OCR Ensemble API 에러: {response.status_code} - {response.text}")

            result = response.json()
            self.logger.info(f"OCR Ensemble 완료: {len(result.get('texts', []))}개 텍스트 검출")

            return {
                "texts": result.get("texts", []),
                "full_text": result.get("full_text", ""),
                "confidence_scores": result.get("confidence_scores", {}),
                "engine_results": result.get("engine_results", {}),
                "voting_method": voting_method,
                "processing_time": result.get("processing_time_ms", 0),
                "raw_response": result,
            }

        except Exception as e:
            self.logger.error(f"OCR Ensemble 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        valid_engines = ["edocr2", "paddleocr", "tesseract", "trocr"]
        engines = self.parameters.get("engines", valid_engines)

        if isinstance(engines, list):
            for engine in engines:
                if engine not in valid_engines:
                    return False, f"지원하지 않는 OCR 엔진: {engine}. 지원: {valid_engines}"

        valid_voting = ["weighted", "majority", "confidence"]
        voting_method = self.parameters.get("voting_method", "weighted")
        if voting_method not in valid_voting:
            return False, f"지원하지 않는 투표 방식: {voting_method}. 지원: {valid_voting}"

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
                "confidence_scores": {"type": "object", "description": "신뢰도 점수"},
                "engine_results": {"type": "object", "description": "각 엔진별 결과"},
                "voting_method": {"type": "string", "description": "사용된 투표 방식"},
                "processing_time": {"type": "number", "description": "처리 시간 (ms)"},
            }
        }


# Executor 등록
ExecutorRegistry.register("ocr_ensemble", OcrEnsembleExecutor)
