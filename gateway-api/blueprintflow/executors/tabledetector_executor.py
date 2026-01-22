"""
Table Detector Executor
테이블 검출 및 구조 추출 API 호출
"""
from typing import Dict, Any, Optional
import io

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
import httpx


class TableDetectorExecutor(BaseNodeExecutor):
    """Table Detector 실행기 - 테이블 검출 및 구조 추출"""

    API_BASE_URL = "http://table-detector-api:5022"

    # 자동 크롭 영역 프리셋 (DSE Bearing Parts List 위치 기반)
    CROP_PRESETS = {
        "right_upper": (0.6, 0.0, 1.0, 0.5),   # 우측 상단 40% × 50%
        "right_lower": (0.6, 0.5, 1.0, 1.0),   # 우측 하단
        "right_full": (0.6, 0.0, 1.0, 1.0),    # 우측 전체 40%
        "left_upper": (0.0, 0.0, 0.4, 0.5),    # 좌측 상단 40% × 50%
        "left_lower": (0.0, 0.5, 0.4, 1.0),    # 좌측 하단
        "upper_half": (0.0, 0.0, 1.0, 0.5),    # 상단 절반
        "full": (0.0, 0.0, 1.0, 1.0),          # 전체 이미지 (크롭 안함)
    }

    def _crop_image(self, file_bytes: bytes, crop_region: str) -> bytes:
        """이미지 자동 크롭"""
        from PIL import Image

        # 크롭 영역 설정
        if crop_region in self.CROP_PRESETS:
            x1_ratio, y1_ratio, x2_ratio, y2_ratio = self.CROP_PRESETS[crop_region]
        else:
            # 기본값: 전체 이미지
            return file_bytes

        # 이미지 로드
        img = Image.open(io.BytesIO(file_bytes))
        w, h = img.size

        # 크롭 좌표 계산
        x1 = int(w * x1_ratio)
        y1 = int(h * y1_ratio)
        x2 = int(w * x2_ratio)
        y2 = int(h * y2_ratio)

        # 크롭 실행
        cropped = img.crop((x1, y1, x2, y2))

        # 바이트로 변환
        output = io.BytesIO()
        cropped.save(output, format="PNG")
        return output.getvalue()

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Table Detector 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - mode: 처리 모드 (detect, extract, analyze)
            - ocr_engine: OCR 엔진 (tesseract, paddle, easyocr)
            - borderless: 테두리 없는 테이블 검출
            - confidence_threshold: 검출 신뢰도 임계값
            - min_confidence: OCR 최소 신뢰도
            - auto_crop: 자동 크롭 영역 (right_upper, right_lower, right_full, upper_half, full)

        Returns:
            - tables: 추출된 테이블 목록
            - regions: 검출된 테이블 영역 목록
            - tables_count: 추출된 테이블 개수
            - regions_count: 검출된 영역 개수
        """
        # 이전 노드에서 전달받은 데이터 보존
        passthrough_detections = inputs.get("detections", [])

        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 자동 크롭 적용 (DSE Bearing Parts List 검출률 향상)
        auto_crop = self.parameters.get("auto_crop", "full")
        if auto_crop and auto_crop != "full":
            file_bytes = self._crop_image(file_bytes, auto_crop)

        # 파라미터 추출
        mode = self.parameters.get("mode", "analyze")
        ocr_engine = self.parameters.get("ocr_engine", "tesseract")
        borderless = self.parameters.get("borderless", True)
        confidence_threshold = self.parameters.get("confidence_threshold", 0.7)
        min_confidence = self.parameters.get("min_confidence", 50)
        filename = self.parameters.get("filename", "table_image.png")

        # 엔드포인트 선택
        endpoint = "/api/v1/analyze"
        if mode == "detect":
            endpoint = "/api/v1/detect"
        elif mode == "extract":
            endpoint = "/api/v1/extract"

        # API 호출
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
            files = {"file": (filename, file_bytes, "image/png")}
            data = {
                "ocr_engine": ocr_engine,
                "borderless": str(borderless).lower(),
                "confidence_threshold": str(confidence_threshold),
                "min_confidence": str(min_confidence)
            }

            response = await client.post(
                f"{self.API_BASE_URL}{endpoint}",
                files=files,
                data=data
            )

            if response.status_code != 200:
                raise Exception(f"Table Detector API 에러: {response.status_code} - {response.text}")

            import orjson
            result = orjson.loads(response.content)

        if not result.get("success", False):
            raise Exception(f"Table Detector 실패: {result.get('error', 'Unknown error')}")

        # 원본 이미지 패스스루
        import base64
        original_image = inputs.get("image", "")
        if not original_image and file_bytes:
            original_image = base64.b64encode(file_bytes).decode("utf-8")

        output = {
            # Table Detector 결과
            "tables": result.get("tables", []),
            "regions": result.get("regions", []),
            "tables_count": result.get("tables_extracted", 0),
            "regions_count": result.get("regions_detected", 0),
            "image_size": result.get("image_size", {}),
            "processing_time": result.get("processing_time_ms", 0),
            # 원본 이미지 패스스루
            "image": original_image,
            # 패스스루: 이전 노드 결과
            "detections": passthrough_detections,
        }

        # drawing_type 패스스루
        if inputs.get("drawing_type"):
            output["drawing_type"] = inputs["drawing_type"]

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # mode 검증
        if "mode" in self.parameters:
            mode = self.parameters["mode"]
            if mode not in ["detect", "extract", "analyze"]:
                return False, "mode는 'detect', 'extract', 'analyze' 중 하나여야 합니다"

        # ocr_engine 검증
        if "ocr_engine" in self.parameters:
            engine = self.parameters["ocr_engine"]
            if engine not in ["tesseract", "paddle", "easyocr"]:
                return False, "ocr_engine은 'tesseract', 'paddle', 'easyocr' 중 하나여야 합니다"

        # auto_crop 검증
        if "auto_crop" in self.parameters:
            crop = self.parameters["auto_crop"]
            valid_crops = list(self.CROP_PRESETS.keys())
            if crop not in valid_crops:
                return False, f"auto_crop은 {valid_crops} 중 하나여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 테이블 포함 이미지"
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "tables": {
                    "type": "array",
                    "description": "추출된 테이블 목록 (headers, data, html)"
                },
                "regions": {
                    "type": "array",
                    "description": "검출된 테이블 영역 목록 (bounding boxes)"
                },
                "tables_count": {
                    "type": "number",
                    "description": "추출된 테이블 개수"
                },
                "regions_count": {
                    "type": "number",
                    "description": "검출된 영역 개수"
                },
                "image_size": {
                    "type": "object",
                    "description": "이미지 크기 (width, height)"
                },
                "processing_time": {
                    "type": "number",
                    "description": "처리 시간 (ms)"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("tabledetector", TableDetectorExecutor)
ExecutorRegistry.register("table_detector", TableDetectorExecutor)  # 언더스코어 버전도 지원
