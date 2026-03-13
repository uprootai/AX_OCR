"""
Parts List Parser Executor
도면 Parts List 테이블에서 부품번호, 품명, 재질, 수량 등 구조화된 정보 추출

내부 처리 방식:
1. Table Detector API로 테이블 검출
2. 헤더 정규화 (fuzzy matching)
3. 재질 코드 정규화
4. 구조화된 Parts List 출력

프로파일 지원:
- bearing/dse: DSE Bearing 특화 파싱 (dsebearing_parser 서비스 사용)
- 기본: 범용 Parts List 파싱
"""
from typing import Dict, Any, Optional
import logging

from ..base_executor import BaseNodeExecutor
from ..executor_registry import ExecutorRegistry
from ..image_utils import prepare_image_for_api

from .constants import POSITION_PRESETS
from .normalizers import crop_image
from .table_detection import detect_tables, find_parts_list_table
from .parser import parse_parts_list, calculate_confidence, parse_with_dse_bearing_service

logger = logging.getLogger(__name__)


class PartsListExecutor(BaseNodeExecutor):
    """Parts List Parser 실행기"""

    # 클래스 상수 (레거시 접근 호환)
    TABLE_DETECTOR_URL = "http://table-detector-api:5022"
    POSITION_PRESETS = POSITION_PRESETS

    def _normalize_header(self, header: str) -> str:
        """헤더를 표준 이름으로 정규화 (레거시 호환)"""
        from .normalizers import normalize_header
        return normalize_header(header)

    def _normalize_material(self, material: str) -> str:
        """재질 코드 정규화 (레거시 호환)"""
        from .normalizers import normalize_material
        return normalize_material(material)

    def _parse_quantity(self, qty_str: str) -> int:
        """수량 문자열을 숫자로 변환 (레거시 호환)"""
        from .normalizers import parse_quantity
        return parse_quantity(qty_str)

    def _crop_image(self, file_bytes: bytes, position: str) -> bytes:
        """Parts List 위치 기반 이미지 크롭 (레거시 호환)"""
        return crop_image(file_bytes, position)

    async def _detect_tables(self, file_bytes: bytes, ocr_engine: str) -> Dict[str, Any]:
        """Table Detector API로 테이블 검출 (레거시 호환)"""
        return await detect_tables(file_bytes, ocr_engine)

    def _find_parts_list_table(self, tables) -> Any:
        """Parts List 테이블 찾기 (레거시 호환)"""
        return find_parts_list_table(tables)

    def _parse_parts_list(
        self,
        table: Dict,
        normalize_headers: bool,
        normalize_material: bool,
    ) -> Dict[str, Any]:
        """테이블 데이터를 Parts List로 파싱 (레거시 호환)"""
        return parse_parts_list(table, normalize_headers, normalize_material)

    def _calculate_confidence(self, parsed: Dict[str, Any], expected_headers) -> float:
        """파싱 신뢰도 계산 (레거시 호환)"""
        return calculate_confidence(parsed, expected_headers)

    def _parse_with_dse_bearing_service(self, tables) -> Dict[str, Any]:
        """DSE Bearing 파서 서비스로 Parts List 파싱 (레거시 호환)"""
        return parse_with_dse_bearing_service(tables)

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parts List Parser 실행

        Parameters:
            - image: 도면 이미지 (base64 또는 PIL Image)
            - tables: Table Detector 결과 (선택)
            - table_position: Parts List 위치
            - ocr_engine: OCR 엔진
            - normalize_material: 재질 정규화 여부
            - normalize_headers: 헤더 정규화 여부
            - expected_headers: 예상 헤더 목록

        Returns:
            - parts_list: 파싱된 Parts List 데이터
            - parts: 부품 목록 배열
            - parts_count: 추출된 부품 개수
            - headers: 정규화된 헤더 목록
            - raw_tables: 원본 테이블 데이터
            - confidence: 추출 신뢰도
        """
        # 이전 노드 결과 패스스루
        passthrough_data = {
            "detections": inputs.get("detections", []),
            "title_block": inputs.get("title_block", {}),
        }

        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터 추출
        position = self.parameters.get("table_position", "auto")
        ocr_engine = self.parameters.get("ocr_engine", "paddle")
        normalize_material = self.parameters.get("normalize_material", True)
        normalize_headers = self.parameters.get("normalize_headers", True)
        expected_headers = self.parameters.get("expected_headers", [
            "no", "part_name", "material", "quantity"
        ])

        # 프로파일 확인 (DSE Bearing 특화 처리)
        profile = self.parameters.get("profile", "").lower()

        # 기존 테이블 결과가 있으면 재사용
        tables = inputs.get("tables", [])

        if not tables:
            # 위치 기반 크롭 (auto가 아닌 경우)
            if position != "auto":
                cropped_bytes = crop_image(file_bytes, position)
            else:
                cropped_bytes = file_bytes

            # Table Detector로 테이블 검출
            table_result = await detect_tables(cropped_bytes, ocr_engine)

            if not table_result.get("success", False) and table_result.get("tables") is None:
                # 실패 시 전체 이미지로 재시도
                table_result = await detect_tables(file_bytes, ocr_engine)

            tables = table_result.get("tables", [])

        # DSE Bearing 프로파일인 경우 전용 파서 사용
        if profile in ("bearing", "dse", "dsebearing"):
            logger.info(f"DSE Bearing 프로파일 사용: {profile}")
            dse_result = parse_with_dse_bearing_service(tables)

            if dse_result and dse_result.get("parts"):
                # 원본 이미지 패스스루
                import base64
                original_image = inputs.get("image", "")
                if not original_image and file_bytes:
                    original_image = base64.b64encode(file_bytes).decode("utf-8")

                return {
                    **dse_result,
                    "raw_tables": tables,
                    "ocr_engine": ocr_engine,
                    "tables_found": len(tables),
                    "image": original_image,
                    **passthrough_data,
                }
            else:
                logger.warning("DSE Bearing 파서 결과 없음, 범용 파서로 폴백")

        # Parts List 테이블 찾기
        parts_list_table = find_parts_list_table(tables)

        if not parts_list_table:
            # Parts List를 찾지 못한 경우
            return {
                "parts_list": {"headers": [], "parts": []},
                "parts": [],
                "parts_count": 0,
                "headers": [],
                "raw_tables": tables,
                "confidence": 0.0,
                "error": "Parts List 테이블을 찾을 수 없습니다",
                "ocr_engine": ocr_engine,
                # 원본 이미지 패스스루
                "image": inputs.get("image", ""),
                **passthrough_data,
            }

        # Parts List 파싱
        parsed = parse_parts_list(
            parts_list_table,
            normalize_headers,
            normalize_material,
        )

        # 신뢰도 계산
        confidence = calculate_confidence(parsed, expected_headers)

        # 원본 이미지 패스스루
        import base64
        original_image = inputs.get("image", "")
        if not original_image and file_bytes:
            original_image = base64.b64encode(file_bytes).decode("utf-8")

        output = {
            # Parts List 파싱 결과
            "parts_list": {
                "headers": parsed["headers"],
                "parts": parsed["parts"],
            },
            "parts": parsed["parts"],
            "parts_count": parsed["parts_count"],
            "headers": parsed["headers"],
            "raw_tables": tables,
            "confidence": confidence,
            # 처리 정보
            "ocr_engine": ocr_engine,
            "tables_found": len(tables),
            # 원본 이미지 패스스루
            "image": original_image,
            # 이전 노드 결과 패스스루
            **passthrough_data,
        }

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # ocr_engine 검증
        if "ocr_engine" in self.parameters:
            engine = self.parameters["ocr_engine"]
            if engine not in ["tesseract", "paddle", "easyocr"]:
                return False, "ocr_engine은 'tesseract', 'paddle', 'easyocr' 중 하나여야 합니다"

        # position 검증
        if "table_position" in self.parameters:
            pos = self.parameters["table_position"]
            valid_positions = list(POSITION_PRESETS.keys()) + ["auto"]
            if pos not in valid_positions:
                return False, f"table_position은 {valid_positions} 중 하나여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 도면 이미지"
                },
                "tables": {
                    "type": "array",
                    "description": "Table Detector 결과 (선택)"
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "parts_list": {
                    "type": "object",
                    "description": "파싱된 Parts List 데이터"
                },
                "parts": {
                    "type": "array",
                    "description": "부품 목록 배열"
                },
                "parts_count": {
                    "type": "number",
                    "description": "추출된 부품 개수"
                },
                "headers": {
                    "type": "array",
                    "description": "정규화된 헤더 목록"
                },
                "confidence": {
                    "type": "number",
                    "description": "추출 신뢰도 (0-1)"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("partslist", PartsListExecutor)
ExecutorRegistry.register("parts_list", PartsListExecutor)
ExecutorRegistry.register("partslist_parser", PartsListExecutor)
