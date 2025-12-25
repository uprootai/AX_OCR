"""
YOLO-PID Executor
P&ID 심볼 검출 API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
import httpx


class YoloPidExecutor(BaseNodeExecutor):
    """YOLO-PID 실행기 - P&ID 심볼 검출"""

    API_BASE_URL = "http://yolo-pid-api:5017"

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        YOLO-PID 심볼 검출 실행 (SAHI Enhanced)

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - confidence: 신뢰도 임계값 (0.05-1.0)
            - slice_height: SAHI 슬라이스 높이 (256, 512, 768, 1024)
            - slice_width: SAHI 슬라이스 너비 (256, 512, 768, 1024)
            - overlap_ratio: 슬라이스 오버랩 비율 (0.1-0.5)
            - class_agnostic: Class-agnostic 모드
            - visualize: 시각화

        Returns:
            - detections: 검출된 심볼 목록
            - statistics: 카테고리별 통계
            - visualization: 시각화 이미지 (base64)
        """
        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # SAHI 파라미터 추출
        confidence = self.parameters.get("confidence", 0.10)
        slice_height = int(self.parameters.get("slice_height", 512))
        slice_width = int(self.parameters.get("slice_width", 512))
        overlap_ratio = self.parameters.get("overlap_ratio", 0.25)
        class_agnostic = self.parameters.get("class_agnostic", False)
        visualize = self.parameters.get("visualize", True)
        filename = self.parameters.get("filename", "pid_image.jpg")

        # API 호출 (SAHI 파라미터)
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (filename, file_bytes, "image/jpeg")}
            data = {
                "confidence": str(confidence),
                "slice_height": str(slice_height),
                "slice_width": str(slice_width),
                "overlap_ratio": str(overlap_ratio),
                "class_agnostic": str(class_agnostic).lower(),
                "visualize": str(visualize).lower()
            }

            response = await client.post(
                f"{self.API_BASE_URL}/api/v1/process",
                files=files,
                data=data
            )

            if response.status_code != 200:
                raise Exception(f"YOLO-PID API 에러: {response.status_code} - {response.text}")

            result = response.json()

        if not result.get("success", False):
            raise Exception(f"YOLO-PID 실패: {result.get('error', 'Unknown error')}")

        data = result.get("data", {})
        visualization = data.get("visualization", "")

        # 원본 이미지 패스스루 (후속 노드에서 필요)
        import base64
        original_image = inputs.get("image", "")
        if not original_image and file_bytes:
            original_image = base64.b64encode(file_bytes).decode("utf-8")

        output = {
            "detections": data.get("detections", []),
            "statistics": data.get("statistics", {}),
            "visualized_image": visualization,  # 프론트엔드 호환 필드명
            "image": original_image,  # 원본 이미지 패스스루 (visualization이 아닌 원본)
            "image_size": data.get("image_size", {}),
            "parameters": data.get("parameters", {}),
            "processing_time": result.get("processing_time", 0)
        }

        # drawing_type 패스스루 (BOM 세션 생성에 필요)
        if inputs.get("drawing_type"):
            output["drawing_type"] = inputs["drawing_type"]

        # features 패스스루 (세션 UI 동적 구성에 필요)
        if inputs.get("features"):
            output["features"] = inputs["features"]

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사 (SAHI 파라미터)"""
        # confidence 검증
        if "confidence" in self.parameters:
            conf = self.parameters["confidence"]
            if not isinstance(conf, (int, float)) or not (0.05 <= conf <= 1.0):
                return False, "confidence는 0.05~1.0 사이의 숫자여야 합니다"

        # slice_height 검증
        if "slice_height" in self.parameters:
            sh = int(self.parameters["slice_height"])
            if sh not in [256, 512, 768, 1024]:
                return False, "slice_height는 256, 512, 768, 1024 중 하나여야 합니다"

        # slice_width 검증
        if "slice_width" in self.parameters:
            sw = int(self.parameters["slice_width"])
            if sw not in [256, 512, 768, 1024]:
                return False, "slice_width는 256, 512, 768, 1024 중 하나여야 합니다"

        # overlap_ratio 검증
        if "overlap_ratio" in self.parameters:
            ratio = self.parameters["overlap_ratio"]
            if not isinstance(ratio, (int, float)) or not (0.1 <= ratio <= 0.5):
                return False, "overlap_ratio는 0.1~0.5 사이의 숫자여야 합니다"

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
                "detections": {
                    "type": "array",
                    "description": "검출된 P&ID 심볼 목록"
                },
                "statistics": {
                    "type": "object",
                    "description": "카테고리별 통계"
                },
                "visualization": {
                    "type": "string",
                    "description": "시각화 이미지 (base64)"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("yolopid", YoloPidExecutor)
