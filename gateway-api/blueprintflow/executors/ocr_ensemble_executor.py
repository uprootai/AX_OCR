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

            # 파라미터 준비 (개별 가중치 파라미터)
            edocr2_weight = self.parameters.get("edocr2_weight", 0.40)
            paddleocr_weight = self.parameters.get("paddleocr_weight", 0.35)
            tesseract_weight = self.parameters.get("tesseract_weight", 0.15)
            trocr_weight = self.parameters.get("trocr_weight", 0.10)
            similarity_threshold = self.parameters.get("similarity_threshold", 0.7)
            engines = self.parameters.get("engines", "all")

            # API 호출 - 올바른 엔드포인트: /api/v1/ocr
            async with httpx.AsyncClient(timeout=180.0) as client:
                files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                data = {
                    "edocr2_weight": str(edocr2_weight),
                    "paddleocr_weight": str(paddleocr_weight),
                    "tesseract_weight": str(tesseract_weight),
                    "trocr_weight": str(trocr_weight),
                    "similarity_threshold": str(similarity_threshold),
                    "engines": engines if isinstance(engines, str) else ",".join(engines),
                }

                response = await client.post(
                    f"{self.api_url}/api/v1/ocr",
                    files=files,
                    data=data
                )

            if response.status_code != 200:
                raise Exception(f"OCR Ensemble API 에러: {response.status_code} - {response.text}")

            result = response.json()
            self.logger.info(f"OCR Ensemble 완료: {len(result.get('results', []))}개 텍스트 검출")

            return {
                "results": result.get("results", []),
                "texts": result.get("results", []),  # 호환성
                "full_text": result.get("full_text", ""),
                "engine_results": result.get("engine_results", {}),
                "engine_status": result.get("engine_status", {}),
                "weights_used": result.get("weights_used", {}),
                "processing_time": result.get("processing_time_ms", 0),
                "raw_response": result,
            }

        except Exception as e:
            self.logger.error(f"OCR Ensemble 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # 가중치 범위 검증
        for weight_name in ["edocr2_weight", "paddleocr_weight", "tesseract_weight", "trocr_weight"]:
            weight = self.parameters.get(weight_name, 0.25)
            if not 0 <= weight <= 1:
                return False, f"{weight_name}는 0~1 범위여야 함: {weight}"

        # 유사도 임계값 검증
        similarity = self.parameters.get("similarity_threshold", 0.7)
        if not 0.5 <= similarity <= 1:
            return False, f"similarity_threshold는 0.5~1 범위여야 함: {similarity}"

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
