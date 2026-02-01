"""
Table Detector Executor
테이블 검출 및 구조 추출 API 호출 (multi-crop + 품질 필터 지원)
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

    # 자동 크롭 영역 프리셋
    CROP_PRESETS = {
        # 도면 특화 영역 (BOM backend 검증 완료)
        "title_block": (0.55, 0.65, 1.0, 1.0),       # 우하단 타이틀 블록
        "revision_table": (0.55, 0.0, 1.0, 0.20),     # 우상단 리비전 테이블
        "parts_list_right": (0.60, 0.20, 1.0, 0.65),  # 우측 부품표
        # 일반 영역
        "right_upper": (0.6, 0.0, 1.0, 0.5),          # 우측 상단 40% × 50%
        "right_lower": (0.6, 0.5, 1.0, 1.0),          # 우측 하단
        "right_full": (0.6, 0.0, 1.0, 1.0),           # 우측 전체 40%
        "left_upper": (0.0, 0.0, 0.4, 0.5),           # 좌측 상단 40% × 50%
        "left_lower": (0.0, 0.5, 0.4, 1.0),           # 좌측 하단
        "upper_half": (0.0, 0.0, 1.0, 0.5),           # 상단 절반
        "full": (0.0, 0.0, 1.0, 1.0),                 # 전체 이미지 (크롭 안함)
    }

    @staticmethod
    def _is_quality_table(table: dict, max_empty_ratio: float = 0.7) -> bool:
        """빈 셀 비율 기반 품질 필터"""
        data = table.get("data", [])
        if not data:
            return False
        rows = table.get("rows", len(data))
        cols = table.get("cols", len(data[0]) if data else 0)
        if rows < 2 or cols < 2:
            return False
        total, empty = 0, 0
        for row in data:
            for cell in row:
                total += 1
                if not cell or (isinstance(cell, str) and not cell.strip()):
                    empty += 1
        return total > 0 and (empty / total) <= max_empty_ratio

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

    async def _call_api(
        self,
        file_bytes: bytes,
        endpoint: str,
        ocr_engine: str,
        borderless: bool,
        confidence_threshold: float,
        min_confidence: int,
        filename: str,
    ) -> Optional[dict]:
        """단일 영역에 대한 Table Detector API 호출"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
                files = {"file": (filename, file_bytes, "image/png")}
                data = {
                    "ocr_engine": ocr_engine,
                    "borderless": str(borderless).lower(),
                    "confidence_threshold": str(confidence_threshold),
                    "min_confidence": str(min_confidence),
                }

                response = await client.post(
                    f"{self.API_BASE_URL}{endpoint}",
                    files=files,
                    data=data,
                )

                if response.status_code != 200:
                    return None

                import orjson
                result = orjson.loads(response.content)

                if not result.get("success", False):
                    return None

                return result
        except Exception:
            return None

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Table Detector 실행 (multi-crop 지원)

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - mode: 처리 모드 (detect, extract, analyze)
            - ocr_engine: OCR 엔진 (tesseract, paddle, easyocr)
            - borderless: 테두리 없는 테이블 검출
            - confidence_threshold: 검출 신뢰도 임계값
            - min_confidence: OCR 최소 신뢰도
            - crop_regions: 크롭 영역 리스트 (multi-crop)
            - auto_crop: 자동 크롭 영역 (하위호환, 단일값)
            - enable_quality_filter: 품질 필터 활성화
            - max_empty_ratio: 최대 빈 셀 비율

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

        # crop_regions (리스트) — 하위호환: auto_crop (단일값)
        crop_regions = self.parameters.get("crop_regions", None)
        if not crop_regions:
            auto_crop = self.parameters.get("auto_crop", "full")
            crop_regions = [auto_crop]

        enable_quality_filter = self.parameters.get("enable_quality_filter", True)
        max_empty_ratio = self.parameters.get("max_empty_ratio", 0.7)

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

        # Multi-crop 루프
        all_tables = []
        all_regions = []
        total_time = 0
        errors = []

        for region_name in crop_regions:
            # 크롭 적용
            if region_name != "full":
                cropped = self._crop_image(file_bytes, region_name)
            else:
                cropped = file_bytes

            result = await self._call_api(
                cropped, endpoint, ocr_engine, borderless,
                confidence_threshold, min_confidence, filename,
            )

            if result is None:
                errors.append(f"영역 '{region_name}' API 호출 실패")
                continue

            # 테이블에 source_region 태그 + 품질 필터
            for table in result.get("tables", []):
                table["source_region"] = region_name
                if enable_quality_filter and not self._is_quality_table(table, max_empty_ratio):
                    continue
                all_tables.append(table)

            all_regions.extend(result.get("regions", []))
            total_time += result.get("processing_time_ms", 0)

        # 모든 영역 실패 시 에러
        if not all_tables and not all_regions and errors:
            raise Exception(f"Table Detector 모든 영역 실패: {'; '.join(errors)}")

        # 원본 이미지 패스스루
        import base64
        original_image = inputs.get("image", "")
        if not original_image and file_bytes:
            original_image = base64.b64encode(file_bytes).decode("utf-8")

        output = {
            # Table Detector 결과
            "tables": all_tables,
            "regions": all_regions,
            "tables_count": len(all_tables),
            "regions_count": len(all_regions),
            "image_size": {},
            "processing_time": total_time,
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

        # crop_regions 검증 (리스트)
        valid_crops = list(self.CROP_PRESETS.keys())
        if "crop_regions" in self.parameters:
            regions = self.parameters["crop_regions"]
            if not isinstance(regions, list):
                return False, "crop_regions는 리스트여야 합니다"
            for region in regions:
                if region not in valid_crops:
                    return False, f"crop_regions의 '{region}'은 유효하지 않습니다. 유효값: {valid_crops}"

        # auto_crop 검증 (하위호환)
        if "auto_crop" in self.parameters:
            crop = self.parameters["auto_crop"]
            if crop not in valid_crops:
                return False, f"auto_crop은 {valid_crops} 중 하나여야 합니다"

        # max_empty_ratio 검증
        if "max_empty_ratio" in self.parameters:
            ratio = self.parameters["max_empty_ratio"]
            if not isinstance(ratio, (int, float)) or ratio < 0.1 or ratio > 1.0:
                return False, "max_empty_ratio는 0.1~1.0 사이여야 합니다"

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
