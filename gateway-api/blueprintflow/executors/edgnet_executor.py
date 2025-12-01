"""
EDGNet Node Executor
엣지 세그멘테이션 API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
from services import call_edgnet_segment


class EdgnetExecutor(BaseNodeExecutor):
    """EDGNet 엣지 세그멘테이션 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        EDGNet 엣지 세그멘테이션 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - crop_regions: YOLO 검출 영역 (선택사항)

        Returns:
            - segments: 세그멘테이션 결과
            - total_segments: 총 세그먼트 개수
            - visualized_image: 시각화 이미지 (base64)
        """
        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터 추출
        filename = self.parameters.get("filename", "workflow_image.jpg")
        visualize = self.parameters.get("visualize", True)
        num_classes = self.parameters.get("num_classes", 3)
        save_graph = self.parameters.get("save_graph", False)
        model = self.parameters.get("model", "unet")  # unet 또는 graphsage

        # EDGNet API 호출
        result = await call_edgnet_segment(
            file_bytes=file_bytes,
            filename=filename,
            visualize=visualize,
            num_classes=num_classes,
            save_graph=save_graph,
            model=model
        )

        # UNet과 GraphSAGE는 다른 응답 형식
        if model == "unet":
            # UNet 응답 형식
            data = result.get("data", {})
            return {
                "segments": [],  # UNet은 세그먼트 목록 대신 마스크 제공
                "total_segments": 1,  # 단일 마스크
                "mask_shape": data.get("mask_shape", []),
                "edge_pixel_count": data.get("edge_pixel_count", 0),
                "edge_percentage": data.get("edge_percentage", 0),
                "visualized_image": data.get("visualized_image", ""),
                "model_used": "UNet",
                "processing_time": result.get("processing_time", 0),
            }
        else:
            # GraphSAGE 응답 형식
            return {
                "segments": result.get("data", {}).get("segments", []),
                "total_segments": len(result.get("data", {}).get("segments", [])),
                "visualized_image": result.get("data", {}).get("visualized_image", ""),
                "model_used": result.get("model_used", "GraphSAGE"),
                "processing_time": result.get("processing_time", 0),
            }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # EDGNet은 특별한 파라미터가 없음
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
                "segments": {
                    "type": "array",
                    "description": "세그멘테이션 결과"
                },
                "total_segments": {
                    "type": "integer",
                    "description": "총 세그먼트 개수"
                },
                "visualized_image": {
                    "type": "string",
                    "description": "시각화 이미지 (base64)"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("edgnet", EdgnetExecutor)
