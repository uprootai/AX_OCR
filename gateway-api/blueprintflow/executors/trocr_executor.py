"""
TrOCR Executor
Microsoft Transformer OCR 실행기

참고: TrOCR은 단일 라인 인식 전용 모델로, 텍스트 검출(detection) 기능이 없습니다.
전체 이미지를 하나의 텍스트 라인으로 인식합니다.
"""
import os
import httpx
import logging
import base64
from io import BytesIO
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry
from .image_utils import prepare_image_for_api, decode_to_pil_image

logger = logging.getLogger(__name__)

TROCR_API_URL = os.getenv("TROCR_URL", "http://trocr-api:5009")


class TrocrExecutor(BaseNodeExecutor):
    """TrOCR 노드 실행기"""

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
        super().__init__(node_id, node_type, parameters)
        self.api_url = TROCR_API_URL
        self.logger.info(f"TrocrExecutor 생성: {node_id}")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """TrOCR 실행"""
        self.logger.info(f"TrOCR 실행 시작: {self.node_id}")

        try:
            # 이미지 준비
            file_bytes = prepare_image_for_api(inputs, context)

            # 파라미터 준비
            max_length = self.parameters.get("max_length", 64)
            num_beams = self.parameters.get("num_beams", 4)
            visualize = self.parameters.get("visualize", True)  # 시각화 기본 활성화

            # API 호출
            async with httpx.AsyncClient(timeout=180.0) as client:
                files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                data = {
                    "max_length": str(max_length),
                    "num_beams": str(num_beams),
                    "visualize": str(visualize).lower(),
                }
                response = await client.post(
                    f"{self.api_url}/api/v1/ocr",
                    files=files,
                    data=data
                )

            if response.status_code != 200:
                raise Exception(f"TrOCR API 에러: {response.status_code} - {response.text}")

            result = response.json()
            self.logger.info(f"TrOCR 완료: {len(result.get('texts', []))}개 텍스트 검출")

            # TrOCR은 bbox를 제공하지 않으므로 인식된 텍스트를 배너로 표시
            visualized_image = result.get("visualized_image", "")
            if not visualized_image and visualize:
                try:
                    full_text = result.get("full_text", "")
                    texts = result.get("texts", [])

                    # 모든 텍스트 수집
                    all_texts = []
                    if full_text:
                        all_texts.append(full_text)
                    for t in texts:
                        if isinstance(t, dict):
                            text = t.get("text", "")
                            conf = t.get("confidence", 0)
                            if text:
                                all_texts.append(f"{text} ({conf*100:.0f}%)" if conf else text)
                        elif isinstance(t, str) and t:
                            all_texts.append(t)

                    if all_texts:
                        visualized_image = self._create_text_banner(
                            file_bytes,
                            all_texts,
                            banner_color=(255, 128, 0),  # 주황색
                            text_color=(255, 255, 255),  # 흰색
                        )
                        self.logger.info(f"TrOCR 시각화 이미지 생성 완료 (배너 모드)")
                except Exception as viz_err:
                    self.logger.warning(f"시각화 생성 실패 (무시됨): {viz_err}")

            # 원본 이미지 패스스루 (후속 노드에서 필요)
            original_image = inputs.get("image", "")
            if not original_image and file_bytes:
                original_image = base64.b64encode(file_bytes).decode("utf-8")

            output = {
                "texts": result.get("texts", []),
                "full_text": result.get("full_text", ""),
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
            self.logger.error(f"TrOCR 실행 실패: {e}")
            raise

    def _create_text_banner(
        self,
        image_input,
        texts: list,
        banner_color: tuple = (255, 128, 0),
        text_color: tuple = (255, 255, 255),
    ) -> str:
        """
        이미지 상단에 인식된 텍스트를 배너로 표시

        Args:
            image_input: 원본 이미지 (bytes)
            texts: 인식된 텍스트 리스트
            banner_color: 배너 배경색
            text_color: 텍스트 색상

        Returns:
            Base64 인코딩된 이미지
        """
        img = decode_to_pil_image(image_input)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_width, img_height = img.size

        # 폰트 로드
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except (OSError, IOError):
            font = ImageFont.load_default()
            title_font = font

        # 배너 높이 계산
        line_height = 20
        banner_height = 30 + len(texts) * line_height

        # 새 이미지 생성 (원본 + 배너)
        new_img = Image.new('RGB', (img_width, img_height + banner_height), banner_color)
        new_img.paste(img, (0, banner_height))

        draw = ImageDraw.Draw(new_img)

        # 타이틀 그리기
        draw.text((10, 5), "TrOCR Results (No Detection - Recognition Only):", fill=text_color, font=title_font)

        # 인식된 텍스트 표시
        y_offset = 25
        for i, text in enumerate(texts[:5]):  # 최대 5개만 표시
            truncated = text[:80] + "..." if len(text) > 80 else text
            draw.text((10, y_offset + i * line_height), f"• {truncated}", fill=text_color, font=font)

        if len(texts) > 5:
            draw.text((10, y_offset + 5 * line_height), f"... and {len(texts) - 5} more", fill=text_color, font=font)

        # Base64로 인코딩
        buffer = BytesIO()
        new_img.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        max_length = self.parameters.get("max_length", 64)
        if not 16 <= max_length <= 256:
            return False, f"max_length는 16~256 범위여야 함: {max_length}"

        num_beams = self.parameters.get("num_beams", 4)
        if not 1 <= num_beams <= 10:
            return False, f"num_beams는 1~10 범위여야 함: {num_beams}"

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
                "processing_time": {"type": "number", "description": "처리 시간 (ms)"},
            }
        }


# Executor 등록
ExecutorRegistry.register("trocr", TrocrExecutor)
