"""
Surya OCR Executor
Surya OCR 실행기 (90+ 언어 지원, 레이아웃 분석)
"""
import os
import httpx
import logging
from typing import Dict, Any, Optional

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry
from .image_utils import prepare_image_for_api, draw_ocr_visualization

logger = logging.getLogger(__name__)

SURYA_API_URL = os.getenv("SURYA_URL", "http://surya-ocr-api:5013")


class SuryaOcrExecutor(BaseNodeExecutor):
    """Surya OCR 노드 실행기"""

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
        super().__init__(node_id, node_type, parameters)
        self.api_url = SURYA_API_URL
        self.logger.info(f"SuryaOcrExecutor 생성: {node_id}")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Surya OCR 실행"""
        self.logger.info(f"Surya OCR 실행 시작: {self.node_id}")

        try:
            # 이미지 준비
            file_bytes = prepare_image_for_api(inputs, context)

            # 파라미터 준비
            languages = self.parameters.get("languages", "ko,en")
            detect_layout = self.parameters.get("detect_layout", False)
            visualize = self.parameters.get("visualize", True)

            # API 호출
            async with httpx.AsyncClient(timeout=180.0) as client:
                files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                data = {
                    "languages": languages,
                    "detect_layout": str(detect_layout).lower(),
                    "visualize": str(visualize).lower(),
                }
                response = await client.post(
                    f"{self.api_url}/api/v1/ocr",
                    files=files,
                    data=data
                )

            if response.status_code != 200:
                raise Exception(f"Surya API 에러: {response.status_code} - {response.text}")

            result = response.json()
            data_result = result.get("data", result)
            texts = data_result.get("texts", [])
            self.logger.info(f"Surya OCR 완료: {len(texts)}개 텍스트 검출")

            # API에서 시각화 이미지 가져오기 (Surya API는 overlay_image 키 사용)
            visualized_image = data_result.get("overlay_image", "") or data_result.get("visualized_image", "")
            if not visualized_image and visualize:
                try:
                    if texts:
                        visualized_image = draw_ocr_visualization(
                            file_bytes,
                            texts,
                            box_color=(139, 92, 246),  # 보라색 (Surya 테마)
                            text_color=(255, 255, 255),
                        )
                        self.logger.info(f"Surya 시각화 이미지 로컬 생성 완료: {len(texts)}개 박스")
                except Exception as viz_err:
                    self.logger.warning(f"시각화 생성 실패 (무시됨): {viz_err}")

            # 원본 이미지 패스스루 (후속 노드에서 필요)
            import base64
            original_image = inputs.get("image", "")
            if not original_image and file_bytes:
                original_image = base64.b64encode(file_bytes).decode("utf-8")

            output = {
                "texts": texts,
                "full_text": data_result.get("full_text", ""),
                "visualized_image": visualized_image,
                "image": original_image,  # 원본 이미지 패스스루
                "processing_time": result.get("processing_time_ms", 0),
                "raw_response": result,
            }

            # drawing_type 패스스루 (BOM 세션 생성에 필요)
            if inputs.get("drawing_type"):
                output["drawing_type"] = inputs["drawing_type"]

            # features 패스스루 (세션 UI 동적 구성에 필요)
            if inputs.get("features"):
                output["features"] = inputs["features"]

            return output

        except Exception as e:
            self.logger.error(f"Surya OCR 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
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
                "visualized_image": {"type": "string", "description": "시각화 이미지 (base64)"},
                "processing_time": {"type": "number", "description": "처리 시간 (ms)"},
            }
        }


# Executor 등록
ExecutorRegistry.register("suryaocr", SuryaOcrExecutor)
