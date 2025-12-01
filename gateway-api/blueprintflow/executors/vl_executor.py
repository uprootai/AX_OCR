"""
VL (Vision Language) Node Executor
Vision-Language 모델 API 호출 (Claude, GPT-4V)
"""
from typing import Dict, Any, Optional
import httpx

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api


class VLExecutor(BaseNodeExecutor):
    """Vision Language 모델 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        VL 모델 실행

        Inputs:
            - image: base64 인코딩된 이미지
            - text (선택사항): 질문/프롬프트 (TextInput에서 연결)

        Parameters:
            - model: 모델 선택 (claude-3-5-sonnet-20241022, gpt-4o 등)
            - temperature: 생성 temperature (0-1, default: 0.0)

        Returns:
            - mode: 'vqa' (질문-답변) 또는 'captioning' (이미지 설명)
            - answer: 질문에 대한 답변 (VQA 모드)
            - caption: 이미지 설명 (캡셔닝 모드)
            - confidence: 신뢰도
        """
        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터 추출
        model = self.parameters.get("model", "blip-base")
        temperature = self.parameters.get("temperature", 0.0)

        # ✅ 핵심: inputs에서 text 가져오기 (TextInput 노드에서 연결됨)
        prompt = inputs.get("text", None)

        # VL API 호출 (/api/v1/analyze 엔드포인트 사용)
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                data = {
                    "model": model,
                    "temperature": temperature,
                }

                # ✅ prompt가 있으면 추가 (VQA 모드)
                if prompt:
                    data["prompt"] = prompt

                response = await client.post(
                    "http://vl-api:5004/api/v1/analyze",
                    files=files,
                    data=data
                )

            if response.status_code == 200:
                result = response.json()

                # 출력 구조화
                output = {
                    "mode": result.get("mode", "captioning"),
                    "model_used": result.get("model_used", model),
                    "processing_time": result.get("processing_time", 0),
                    "confidence": result.get("confidence", 1.0),
                }

                # VQA 모드
                if result.get("mode") == "vqa":
                    output["answer"] = result.get("answer", "")
                    output["question"] = result.get("question", prompt)
                # 캡셔닝 모드
                else:
                    output["caption"] = result.get("caption", "")

                return output

            else:
                raise Exception(f"VL API 호출 실패: {response.status_code} - {response.text}")

        except Exception as e:
            self.logger.error(f"VL API 호출 실패: {e}")
            # Fallback: mock 응답
            return {
                "mode": "error",
                "caption": f"VL API 오류: {str(e)}",
                "confidence": 0.0,
                "model_used": model,
                "processing_time": 0,
            }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # temperature 검증
        if "temperature" in self.parameters:
            temp = self.parameters["temperature"]
            if not isinstance(temp, (int, float)) or not (0 <= temp <= 1):
                return False, "temperature는 0~1 사이의 숫자여야 합니다"

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
                "text": {
                    "type": "string",
                    "description": "질문/프롬프트 (선택사항)"
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "분석 모드 ('vqa' 또는 'captioning')"
                },
                "answer": {
                    "type": "string",
                    "description": "질문에 대한 답변 (VQA 모드)"
                },
                "caption": {
                    "type": "string",
                    "description": "이미지 설명 (캡셔닝 모드)"
                },
                "confidence": {
                    "type": "number",
                    "description": "답변 신뢰도"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("vl", VLExecutor)
