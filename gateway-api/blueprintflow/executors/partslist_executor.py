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
from typing import Dict, Any, Optional, List
import re
import io
import logging

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
import httpx

logger = logging.getLogger(__name__)


class PartsListExecutor(BaseNodeExecutor):
    """Parts List Parser 실행기"""

    TABLE_DETECTOR_URL = "http://table-detector-api:5022"

    # 표준 헤더 매핑 (다양한 변형 → 표준 이름)
    HEADER_ALIASES = {
        "no": ["NO", "NO.", "번호", "#", "SEQ", "ITEM", "ITEM NO", "ITEM NO."],
        "part_name": ["PART NAME", "NAME", "품명", "부품명", "DESCRIPTION", "DESC", "PART"],
        "material": ["MAT'L", "MATL", "MAT", "MATERIAL", "재질", "재료", "SPEC"],
        "quantity": ["Q'TY", "QTY", "QUANTITY", "수량", "EA", "PCS"],
        "remarks": ["REMARKS", "REMARK", "비고", "NOTE", "NOTES"],
        "drawing_no": ["DWG NO", "DWG NO.", "DRAWING NO", "도면번호", "DWG"],
        "weight": ["WEIGHT", "WT", "중량", "무게", "KG"],
        "specification": ["SPEC", "SPECIFICATION", "규격", "SIZE"],
    }

    # 재질 정규화 매핑
    MATERIAL_NORMALIZATION = {
        # SF 계열
        "SF440": "SF440A",
        "SF-440A": "SF440A",
        "SF 440A": "SF440A",
        "SF440-A": "SF440A",
        # SS 계열
        "SS-400": "SS400",
        "SS 400": "SS400",
        # SM 계열
        "SM-490A": "SM490A",
        "SM 490A": "SM490A",
        "SM490": "SM490A",
        # S45C 계열
        "S45C-N": "S45C-N",
        "S45CN": "S45C-N",
        "S-45C": "S45C",
        # ASTM 계열
        "B23": "ASTM B23 GR.2",
        "ASTM B23": "ASTM B23 GR.2",
        "ASTM B-23": "ASTM B23 GR.2",
        "BABBITT": "ASTM B23 GR.2",
        # SUS 계열
        "SUS-304": "SUS304",
        "SUS 304": "SUS304",
        # SCM 계열
        "SCM-440": "SCM440",
        "SCM 440": "SCM440",
    }

    # Parts List 위치 프리셋 (이미지 비율 기준)
    POSITION_PRESETS = {
        "top_left": (0.0, 0.0, 0.5, 0.4),
        "top_right": (0.5, 0.0, 1.0, 0.4),
        "bottom_left": (0.0, 0.6, 0.5, 1.0),
        "bottom_right": (0.5, 0.6, 1.0, 1.0),
        "full": (0.0, 0.0, 1.0, 1.0),
    }

    def _normalize_header(self, header: str) -> str:
        """헤더를 표준 이름으로 정규화"""
        header_upper = header.upper().strip()

        for standard, aliases in self.HEADER_ALIASES.items():
            if header_upper in [a.upper() for a in aliases]:
                return standard

        # 부분 매칭 시도
        for standard, aliases in self.HEADER_ALIASES.items():
            for alias in aliases:
                if alias.upper() in header_upper or header_upper in alias.upper():
                    return standard

        return header.lower().replace(" ", "_").replace("'", "")

    def _normalize_material(self, material: str) -> str:
        """재질 코드 정규화"""
        if not material:
            return material

        upper = material.upper().strip()

        # 정규화 매핑 확인
        for key, normalized in self.MATERIAL_NORMALIZATION.items():
            if key.upper() == upper or key.upper() in upper:
                return normalized

        # 패턴 기반 정규화
        # SF 패턴
        sf_match = re.match(r"SF[- ]?(\d+)[- ]?([A-Z])?", upper)
        if sf_match:
            num = sf_match.group(1)
            grade = sf_match.group(2) or "A"
            return f"SF{num}{grade}"

        # SS 패턴
        ss_match = re.match(r"SS[- ]?(\d+)", upper)
        if ss_match:
            return f"SS{ss_match.group(1)}"

        # SM 패턴
        sm_match = re.match(r"SM[- ]?(\d+)[- ]?([A-Z])?", upper)
        if sm_match:
            num = sm_match.group(1)
            grade = sm_match.group(2) or "A"
            return f"SM{num}{grade}"

        return upper

    def _parse_quantity(self, qty_str: str) -> int:
        """수량 문자열을 숫자로 변환"""
        if not qty_str:
            return 1

        # 숫자만 추출
        numbers = re.findall(r"\d+", str(qty_str))
        if numbers:
            return int(numbers[0])
        return 1

    def _crop_image(self, file_bytes: bytes, position: str) -> bytes:
        """Parts List 위치 기반 이미지 크롭"""
        from PIL import Image

        if position not in self.POSITION_PRESETS or position == "full":
            return file_bytes

        x1_ratio, y1_ratio, x2_ratio, y2_ratio = self.POSITION_PRESETS[position]

        img = Image.open(io.BytesIO(file_bytes))
        w, h = img.size

        x1 = int(w * x1_ratio)
        y1 = int(h * y1_ratio)
        x2 = int(w * x2_ratio)
        y2 = int(h * y2_ratio)

        cropped = img.crop((x1, y1, x2, y2))

        output = io.BytesIO()
        cropped.save(output, format="PNG")
        return output.getvalue()

    async def _detect_tables(
        self,
        file_bytes: bytes,
        ocr_engine: str
    ) -> Dict[str, Any]:
        """Table Detector API로 테이블 검출"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
            files = {"file": ("partslist.png", file_bytes, "image/png")}
            data = {
                "mode": "analyze",
                "ocr_engine": ocr_engine,
                "borderless": "false",  # Parts List는 보통 테두리 있음
                "confidence_threshold": "0.6",
                "min_confidence": "60",
                "output_format": "json",
            }

            response = await client.post(
                f"{self.TABLE_DETECTOR_URL}/api/v1/analyze",
                files=files,
                data=data
            )

            if response.status_code != 200:
                return {"success": False, "error": f"Table Detector 오류: {response.status_code}"}

            import orjson
            return orjson.loads(response.content)

    def _find_parts_list_table(self, tables: List[Dict]) -> Optional[Dict]:
        """Parts List 테이블 찾기 (헤더 기반)"""
        parts_list_keywords = ["NO", "PART", "NAME", "MAT", "Q'TY", "QTY", "품명", "재질", "수량"]

        best_table = None
        best_score = 0

        for table in tables:
            headers = table.get("headers", [])
            if not headers:
                continue

            # 헤더 매칭 점수 계산
            score = 0
            for header in headers:
                header_upper = str(header).upper()
                for keyword in parts_list_keywords:
                    if keyword in header_upper:
                        score += 1
                        break

            # 최소 2개 이상 매칭되어야 Parts List로 간주
            if score >= 2 and score > best_score:
                best_score = score
                best_table = table

        return best_table

    def _parse_parts_list(
        self,
        table: Dict,
        normalize_headers: bool,
        normalize_material: bool
    ) -> Dict[str, Any]:
        """테이블 데이터를 Parts List로 파싱"""
        raw_headers = table.get("headers", [])
        raw_data = table.get("data", [])

        # 헤더 정규화
        if normalize_headers:
            headers = [self._normalize_header(str(h)) for h in raw_headers]
        else:
            headers = [str(h).lower().replace(" ", "_") for h in raw_headers]

        # 데이터 파싱
        parts = []
        for row in raw_data:
            if isinstance(row, list):
                # 리스트 형태의 행
                part = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        header = headers[i]
                        value_str = str(value).strip() if value else ""

                        # 재질 정규화
                        if header == "material" and normalize_material:
                            value_str = self._normalize_material(value_str)

                        # 수량 파싱
                        if header == "quantity":
                            part[header] = self._parse_quantity(value_str)
                        elif header == "no":
                            try:
                                part[header] = int(re.sub(r"[^\d]", "", value_str) or "0")
                            except ValueError:
                                part[header] = 0
                        else:
                            part[header] = value_str

                # 유효한 부품인지 확인 (part_name이 있어야 함)
                if part.get("part_name") or part.get("material"):
                    parts.append(part)

            elif isinstance(row, dict):
                # 딕셔너리 형태의 행
                part = {}
                for key, value in row.items():
                    header = self._normalize_header(str(key)) if normalize_headers else str(key).lower()
                    value_str = str(value).strip() if value else ""

                    if header == "material" and normalize_material:
                        value_str = self._normalize_material(value_str)

                    if header == "quantity":
                        part[header] = self._parse_quantity(value_str)
                    elif header == "no":
                        try:
                            part[header] = int(re.sub(r"[^\d]", "", value_str) or "0")
                        except ValueError:
                            part[header] = 0
                    else:
                        part[header] = value_str

                if part.get("part_name") or part.get("material"):
                    parts.append(part)

        return {
            "headers": headers,
            "parts": parts,
            "parts_count": len(parts),
        }

    def _calculate_confidence(self, parsed: Dict[str, Any], expected_headers: List[str]) -> float:
        """파싱 신뢰도 계산"""
        if not parsed.get("parts"):
            return 0.0

        headers = parsed.get("headers", [])
        parts = parsed.get("parts", [])

        # 헤더 매칭 점수
        header_score = sum(1 for h in expected_headers if h in headers) / len(expected_headers)

        # 데이터 완성도 점수
        data_scores = []
        for part in parts:
            filled = sum(1 for h in expected_headers if part.get(h))
            data_scores.append(filled / len(expected_headers))

        data_score = sum(data_scores) / len(data_scores) if data_scores else 0

        return (header_score * 0.4 + data_score * 0.6)

    def _parse_with_dse_bearing_service(self, tables: List[Dict]) -> Dict[str, Any]:
        """
        DSE Bearing 파서 서비스로 Parts List 파싱

        Args:
            tables: Table Detector 결과 테이블 목록

        Returns:
            파싱된 Parts List 데이터
        """
        try:
            from services.dsebearing_parser import get_parser

            parser = get_parser()

            # 테이블 데이터 준비
            table_data = []
            for table in tables:
                data = table.get("data", [])
                headers = table.get("headers", [])

                # 헤더가 있으면 첫 행으로 추가
                if headers:
                    table_data.append(headers)

                # 데이터 행 추가
                for row in data:
                    if isinstance(row, list):
                        table_data.append(row)
                    elif isinstance(row, dict):
                        # cells 형식 처리
                        cells = row.get("cells", [])
                        if cells:
                            row_data = [""] * 10  # 최대 10개 컬럼
                            for cell in cells:
                                if isinstance(cell, dict):
                                    col = cell.get("col", 0)
                                    text = cell.get("text", "")
                                    if col < 10:
                                        row_data[col] = text
                            table_data.append([c for c in row_data if c])

            # DSE Bearing 파서로 파싱 (table_data와 ocr_texts 모두 전달)
            items = parser.parse_parts_list(ocr_texts=[], table_data=table_data)

            # 결과 변환 (parse_parts_list는 List[PartsListItem] 반환)
            parts = []
            for item in items:
                part = {
                    "no": item.no,
                    "part_name": item.description,
                    "material": item.material,
                    "quantity": item.qty,
                }
                if item.weight:
                    part["weight"] = item.weight
                if item.size_dwg_no:
                    part["drawing_no"] = item.size_dwg_no
                if item.remark:
                    part["remarks"] = item.remark
                parts.append(part)

            headers = ["no", "part_name", "material", "quantity"]
            if any(p.get("weight") for p in parts):
                headers.append("weight")
            if any(p.get("drawing_no") for p in parts):
                headers.append("drawing_no")
            if any(p.get("remarks") for p in parts):
                headers.append("remarks")

            # 신뢰도 계산 (파싱된 항목 수 기반)
            confidence = min(0.95, 0.7 + len(parts) * 0.05) if parts else 0.0

            return {
                "parts_list": {
                    "headers": headers,
                    "parts": parts,
                },
                "parts": parts,
                "parts_count": len(parts),
                "headers": headers,
                "confidence": confidence,
                "parser": "dse_bearing",
            }

        except Exception as e:
            logger.error(f"DSE Bearing 파서 오류: {e}")
            return {}

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
                cropped_bytes = self._crop_image(file_bytes, position)
            else:
                cropped_bytes = file_bytes

            # Table Detector로 테이블 검출
            table_result = await self._detect_tables(cropped_bytes, ocr_engine)

            if not table_result.get("success", False) and table_result.get("tables") is None:
                # 실패 시 전체 이미지로 재시도
                table_result = await self._detect_tables(file_bytes, ocr_engine)

            tables = table_result.get("tables", [])

        # DSE Bearing 프로파일인 경우 전용 파서 사용
        if profile in ("bearing", "dse", "dsebearing"):
            logger.info(f"DSE Bearing 프로파일 사용: {profile}")
            dse_result = self._parse_with_dse_bearing_service(tables)

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
        parts_list_table = self._find_parts_list_table(tables)

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
        parsed = self._parse_parts_list(
            parts_list_table,
            normalize_headers,
            normalize_material
        )

        # 신뢰도 계산
        confidence = self._calculate_confidence(parsed, expected_headers)

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
            valid_positions = list(self.POSITION_PRESETS.keys()) + ["auto"]
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
