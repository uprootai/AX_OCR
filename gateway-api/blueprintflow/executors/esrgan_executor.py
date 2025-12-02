"""
ESRGAN Executor
Real-ESRGAN 이미지 업스케일링 실행기
"""
import os
import httpx
import logging
from typing import Dict, Any, Optional

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry
from .image_utils import prepare_image_for_api

logger = logging.getLogger(__name__)

ESRGAN_API_URL = os.getenv("ESRGAN_URL", "http://esrgan-api:5010")


class EsrganExecutor(BaseNodeExecutor):
    """ESRGAN 이미지 업스케일러 노드 실행기"""

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
        super().__init__(node_id, node_type, parameters)
        self.api_url = ESRGAN_API_URL
        self.logger.info(f"EsrganExecutor 생성: {node_id}")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """ESRGAN 업스케일링 실행"""
        self.logger.info(f"ESRGAN 실행 시작: {self.node_id}")

        try:
            # 이미지 준비
            file_bytes = prepare_image_for_api(inputs, context)

            # 파라미터 준비
            scale = self.parameters.get("scale", 4)
            denoise_strength = self.parameters.get("denoise_strength", 0.5)
            tile_size = self.parameters.get("tile_size", 0)
            output_format = self.parameters.get("output_format", "png")

            # API 호출
            async with httpx.AsyncClient(timeout=180.0) as client:
                files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                data = {
                    "scale": str(scale),
                    "denoise_strength": str(denoise_strength),
                    "tile_size": str(tile_size),
                    "output_format": output_format,
                }
                response = await client.post(
                    f"{self.api_url}/api/v1/upscale",
                    files=files,
                    data=data
                )

            if response.status_code != 200:
                raise Exception(f"ESRGAN API 에러: {response.status_code} - {response.text}")

            # 응답이 이미지인 경우 처리
            content_type = response.headers.get("content-type", "")

            if "image" in content_type:
                # 업스케일된 이미지 바이트 반환
                self.logger.info(f"ESRGAN 완료: 이미지 업스케일 성공")
                # 헤더에서 메타정보 추출
                processing_time = response.headers.get("X-Processing-Time-Ms", "0")
                method = response.headers.get("X-Method", "Real-ESRGAN")
                return {
                    "image": response.content,  # BlueprintFlow 출력 형식에 맞춤
                    "upscaled_image": response.content,
                    "scale": scale,
                    "method": method,
                    "content_type": content_type,
                    "processing_time": float(processing_time),
                }
            else:
                # JSON 응답인 경우
                result = response.json()
                self.logger.info(f"ESRGAN 완료: {result.get('message', 'success')}")
                return {
                    "image": result.get("image_base64"),
                    "upscaled_image": result.get("image_base64"),
                    "scale": scale,
                    "processing_time": result.get("processing_time_ms", 0),
                    "raw_response": result,
                }

        except Exception as e:
            self.logger.error(f"ESRGAN 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        valid_scales = [2, 4]
        scale = self.parameters.get("scale", 4)
        if isinstance(scale, str):
            scale = int(scale)
        if scale not in valid_scales:
            return False, f"지원하지 않는 스케일: {scale}. 지원: {valid_scales}"

        denoise_strength = self.parameters.get("denoise_strength", 0.5)
        if not 0 <= denoise_strength <= 1:
            return False, f"denoise_strength는 0~1 범위여야 함: {denoise_strength}"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image": {"type": "Image", "description": "업스케일할 이미지"}
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "upscaled_image": {"type": "Image", "description": "업스케일된 이미지"},
                "scale": {"type": "number", "description": "업스케일 배율"},
                "model": {"type": "string", "description": "사용된 모델"},
                "processing_time": {"type": "number", "description": "처리 시간 (ms)"},
            }
        }


# Executor 등록
ExecutorRegistry.register("esrgan", EsrganExecutor)
