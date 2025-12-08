"""
Line Detector Executor
P&ID 라인(배관/신호선) 검출 API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
import httpx


class LineDetectorExecutor(BaseNodeExecutor):
    """Line Detector 실행기 - P&ID 라인 검출"""

    API_BASE_URL = "http://line-detector-api:5016"

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Line Detector 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - method: 검출 방식 (lsd, hough, combined)
            - merge_lines: 공선 라인 병합
            - classify_types: 라인 유형 분류
            - find_intersections: 교차점 검출
            - visualize: 시각화

        Returns:
            - lines: 검출된 라인 목록
            - intersections: 교차점 목록
            - statistics: 통계
            - visualization: 시각화 이미지 (base64)
            - detections: 이전 노드(YOLO-PID)에서 전달받은 심볼 검출 결과 (패스스루)
        """
        # 이전 노드에서 전달받은 detections 보존 (YOLO-PID → Line Detector → PID Analyzer 순차 파이프라인 지원)
        passthrough_detections = inputs.get("detections", [])
        passthrough_symbols = inputs.get("symbols", [])

        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터 추출
        method = self.parameters.get("method", "lsd")
        merge_lines = self.parameters.get("merge_lines", True)
        classify_types = self.parameters.get("classify_types", True)
        find_intersections = self.parameters.get("find_intersections", True)
        visualize = self.parameters.get("visualize", True)
        filename = self.parameters.get("filename", "pid_image.jpg")

        # API 호출
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (filename, file_bytes, "image/jpeg")}
            data = {
                "method": method,
                "merge_lines": str(merge_lines).lower(),
                "classify_types": str(classify_types).lower(),
                "find_intersections": str(find_intersections).lower(),
                "visualize": str(visualize).lower()
            }

            response = await client.post(
                f"{self.API_BASE_URL}/api/v1/process",
                files=files,
                data=data
            )

            if response.status_code != 200:
                raise Exception(f"Line Detector API 에러: {response.status_code} - {response.text}")

            result = response.json()

        if not result.get("success", False):
            raise Exception(f"Line Detector 실패: {result.get('error', 'Unknown error')}")

        data = result.get("data", {})
        return {
            # Line Detector 결과
            "lines": data.get("lines", []),
            "intersections": data.get("intersections", []),
            "statistics": data.get("statistics", {}),
            "visualized_image": data.get("visualization", ""),  # 프론트엔드 호환 필드명
            "image": data.get("visualization", ""),  # 대체 필드명
            "method": data.get("method", method),
            "image_size": data.get("image_size", {}),
            "processing_time": result.get("processing_time", 0),
            # 패스스루: 이전 노드(YOLO-PID)의 결과를 다음 노드(PID Analyzer)로 전달
            "detections": passthrough_detections,
            "symbols": passthrough_symbols,
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # method 검증
        if "method" in self.parameters:
            method = self.parameters["method"]
            if method not in ["lsd", "hough", "combined"]:
                return False, "method는 'lsd', 'hough', 'combined' 중 하나여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 P&ID 이미지"
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "lines": {
                    "type": "array",
                    "description": "검출된 라인 목록"
                },
                "intersections": {
                    "type": "array",
                    "description": "교차점 목록"
                },
                "statistics": {
                    "type": "object",
                    "description": "라인 통계"
                },
                "visualization": {
                    "type": "string",
                    "description": "시각화 이미지 (base64)"
                },
                "detections": {
                    "type": "array",
                    "description": "패스스루: 이전 노드(YOLO-PID)의 심볼 검출 결과"
                },
                "symbols": {
                    "type": "array",
                    "description": "패스스루: 이전 노드의 심볼 결과"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("linedetector", LineDetectorExecutor)
