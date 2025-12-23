"""
DocTR Executor
DocTR 2단계 파이프라인 OCR 실행기 (Detection + Recognition)
"""
import os
import httpx
import logging
from typing import Dict, Any, Optional

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry
from .image_utils import prepare_image_for_api, draw_ocr_visualization

logger = logging.getLogger(__name__)

DOCTR_API_URL = os.getenv("DOCTR_URL", "http://doctr-api:5014")


class DoctrExecutor(BaseNodeExecutor):
    """DocTR OCR 노드 실행기"""

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
        super().__init__(node_id, node_type, parameters)
        self.api_url = DOCTR_API_URL
        self.logger.info(f"DoctrExecutor 생성: {node_id}")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """DocTR OCR 실행"""
        self.logger.info(f"DocTR OCR 실행 시작: {self.node_id}")

        try:
            # 이미지 준비
            file_bytes = prepare_image_for_api(inputs, context)

            # 파라미터 준비
            det_arch = self.parameters.get("det_arch", "db_resnet50")
            reco_arch = self.parameters.get("reco_arch", "crnn_vgg16_bn")
            straighten_pages = self.parameters.get("straighten_pages", False)
            export_as_xml = self.parameters.get("export_as_xml", False)
            visualize = self.parameters.get("visualize", True)

            # API 호출
            async with httpx.AsyncClient(timeout=180.0) as client:
                files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                data = {
                    "det_arch": det_arch,
                    "reco_arch": reco_arch,
                    "straighten_pages": str(straighten_pages).lower(),
                    "export_as_xml": str(export_as_xml).lower(),
                    "visualize": str(visualize).lower(),
                }
                response = await client.post(
                    f"{self.api_url}/api/v1/ocr",
                    files=files,
                    data=data
                )

            if response.status_code != 200:
                raise Exception(f"DocTR API 에러: {response.status_code} - {response.text}")

            result = response.json()
            data_result = result.get("data", result)
            texts = data_result.get("texts", [])
            self.logger.info(f"DocTR OCR 완료: {len(texts)}개 텍스트 검출")

            # API에서 시각화 이미지가 없으면 로컬에서 생성
            visualized_image = data_result.get("visualized_image", "")
            if not visualized_image and visualize:
                try:
                    # DocTR 결과를 직접 전달 (정규화 좌표 형식)
                    # draw_ocr_visualization이 [[x1,y1], [x2,y2]] 형식을 처리함
                    if texts:
                        visualized_image = draw_ocr_visualization(
                            file_bytes,
                            texts,  # 원본 texts 직접 전달
                            box_color=(16, 185, 129),  # 에메랄드
                            text_color=(0, 0, 200),
                        )
                        self.logger.info(f"DocTR 시각화 이미지 로컬 생성 완료: {len(texts)}개 박스")
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
                "pages": data_result.get("pages", []),
                "visualized_image": visualized_image,
                "image": original_image,  # 원본 이미지 패스스루
                "processing_time": result.get("processing_time_ms", 0),
                "raw_response": result,
            }

            # drawing_type 패스스루 (BOM 세션 생성에 필요)
            if inputs.get("drawing_type"):
                output["drawing_type"] = inputs["drawing_type"]

            return output

        except Exception as e:
            self.logger.error(f"DocTR OCR 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        valid_det_archs = ["db_resnet50", "db_mobilenet_v3_large", "linknet_resnet18"]
        det_arch = self.parameters.get("det_arch", "db_resnet50")
        if det_arch not in valid_det_archs:
            return False, f"지원하지 않는 det_arch: {det_arch}. 지원: {valid_det_archs}"

        valid_reco_archs = ["crnn_vgg16_bn", "crnn_mobilenet_v3_small", "master"]
        reco_arch = self.parameters.get("reco_arch", "crnn_vgg16_bn")
        if reco_arch not in valid_reco_archs:
            return False, f"지원하지 않는 reco_arch: {reco_arch}. 지원: {valid_reco_archs}"

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
                "pages": {"type": "array", "description": "페이지별 상세 결과"},
                "processing_time": {"type": "number", "description": "처리 시간 (ms)"},
            }
        }


# Executor 등록
ExecutorRegistry.register("doctr", DoctrExecutor)
