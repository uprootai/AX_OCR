"""
eDOCr2 Node Executor
차원 OCR API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
from services import call_edocr2_ocr


class Edocr2Executor(BaseNodeExecutor):
    """eDOCr2 차원 OCR 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        eDOCr2 차원 OCR 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - crop_regions: YOLO 검출 영역 (선택사항)

        Returns:
            - dimensions: 추출된 차원 정보 리스트
            - total_dimensions: 총 차원 개수
            - text: 추출된 텍스트 정보
        """
        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # crop_regions 추출 (YOLO 결과로부터) - 현재는 사용하지 않음
        # crop_regions = inputs.get("crop_regions") or inputs.get("detections")

        filename = self.parameters.get("filename", "workflow_image.jpg")

        # 파라미터 추출
        version = self.parameters.get("version", "v2")
        language = self.parameters.get("language", "eng")
        cluster_threshold = self.parameters.get("cluster_threshold", 20)
        extract_dimensions = self.parameters.get("extract_dimensions", True)
        extract_gdt = self.parameters.get("extract_gdt", True)
        extract_text = self.parameters.get("extract_text", True)
        extract_tables = self.parameters.get("extract_tables", True)
        visualize = self.parameters.get("visualize", True)  # 기본값을 True로 변경하여 시각화 활성화

        # eDOCr2 API 호출
        result = await call_edocr2_ocr(
            file_bytes=file_bytes,
            filename=filename,
            version=version,
            extract_dimensions=extract_dimensions,
            extract_gdt=extract_gdt,
            extract_text=extract_text,
            extract_tables=extract_tables,
            visualize=visualize,
            language=language,
            cluster_threshold=cluster_threshold
        )

        output = {
            "dimensions": result.get("dimensions", []),
            "total_dimensions": len(result.get("dimensions", [])),
            "text": result.get("text", {}),
            "model_used": result.get("model", "eDOCr2-v2"),
            "processing_time": result.get("processing_time", 0),
        }

        # 시각화 이미지 추가 (있는 경우)
        if result.get("visualized_image"):
            output["visualized_image"] = result["visualized_image"]

        # 원본 이미지 패스스루 (BOM 등 후속 노드에서 사용)
        if inputs.get("image"):
            output["image"] = inputs["image"]

        # drawing_type 패스스루 (BOM 세션 생성에 필요)
        if inputs.get("drawing_type"):
            output["drawing_type"] = inputs["drawing_type"]

        # features 패스스루 (세션 UI 동적 구성에 필요)
        if inputs.get("features"):
            output["features"] = inputs["features"]

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # eDOCr2는 특별한 파라미터가 없음
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
                "crop_regions": {
                    "type": "array",
                    "description": "YOLO 검출 영역 (선택사항)",
                    "items": {"type": "object"}
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "dimensions": {
                    "type": "array",
                    "description": "추출된 차원 정보"
                },
                "total_dimensions": {
                    "type": "integer",
                    "description": "총 차원 개수"
                },
                "text": {
                    "type": "object",
                    "description": "추출된 텍스트 정보"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("edocr2", Edocr2Executor)
