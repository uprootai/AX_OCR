"""
VL (Vision Language) Node Executor
Vision-Language 모델 API 호출 (Claude, GPT-4V)
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api


class VLExecutor(BaseNodeExecutor):
    """Vision Language 모델 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        VL 모델 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - prompt: VL 모델에 전달할 프롬프트 (default: task에 따라 결정)
            - task: VL 작업 타입 (extract_info, extract_dimensions, infer_manufacturing, generate_qc)
            - model: 모델 선택 (claude, gpt4v)
            - temperature: 생성 temperature (0-1, default: 0.0)

        Returns:
            - result: VL 모델 응답
            - task: 실행된 작업 타입
        """
        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터 추출
        task = self.parameters.get("task", "extract_info")
        model = self.parameters.get("model", "claude")
        temperature = self.parameters.get("temperature", 0.0)
        prompt = self.parameters.get("prompt", None)
        filename = self.parameters.get("filename", "workflow_image.jpg")

        # task에 따른 기본 프롬프트 설정
        if not prompt:
            prompt_map = {
                "extract_info": "도면에서 정보 블록(제목란, 부품 정보 등)을 추출하세요.",
                "extract_dimensions": "도면에서 치수 정보를 추출하세요.",
                "infer_manufacturing": "도면을 분석하여 적합한 제조 공정을 추론하세요.",
                "generate_qc": "도면 기반으로 품질 검사 체크리스트를 생성하세요."
            }
            prompt = prompt_map.get(task, "도면을 분석하세요.")

        # VL API 호출 (서비스 함수 import 필요)
        # 현재는 간단한 구조로 구현, 실제로는 services.vl_service를 사용해야 함
        try:
            # services 모듈에서 VL API 호출 함수 동적 import
            from services.vl_service import call_vl_api

            result = await call_vl_api(
                file_bytes=file_bytes,
                filename=filename,
                prompt=prompt,
                model=model,
                temperature=temperature,
                task=task
            )

            return {
                "result": result.get("result", ""),
                "task": task,
                "model_used": result.get("model_used", model),
                "processing_time": result.get("processing_time", 0),
            }

        except ImportError:
            # VL API 서비스가 없는 경우 mock 응답 반환
            return {
                "result": f"[VL Mock] Task: {task}, Model: {model}, Temperature: {temperature}",
                "task": task,
                "model_used": model,
                "processing_time": 0,
                "warning": "VL API service not available - returning mock response"
            }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # task 검증
        if "task" in self.parameters:
            valid_tasks = ["extract_info", "extract_dimensions", "infer_manufacturing", "generate_qc"]
            if self.parameters["task"] not in valid_tasks:
                return False, f"task는 {valid_tasks} 중 하나여야 합니다"

        # model 검증
        if "model" in self.parameters:
            valid_models = ["claude", "gpt4v"]
            if self.parameters["model"] not in valid_models:
                return False, f"model은 {valid_models} 중 하나여야 합니다"

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
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "VL 모델 응답 결과"
                },
                "task": {
                    "type": "string",
                    "description": "실행된 작업 타입"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("vl", VLExecutor)
