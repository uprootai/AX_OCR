"""
Title Block Parser Executor
도면 Title Block에서 도면번호, Rev, 품명, 재질 등 구조화된 정보 추출

내부 처리 방식:
1. Table Detector API로 Title Block 영역 검출
2. OCR로 텍스트 추출
3. 정규식 기반 필드 파싱
4. DSE Bearing 프로파일: dsebearing_parser 서비스 사용
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


class TitleBlockExecutor(BaseNodeExecutor):
    """Title Block Parser 실행기"""

    TABLE_DETECTOR_URL = "http://table-detector-api:5022"

    # Title Block 위치 프리셋 (이미지 비율 기준)
    POSITION_PRESETS = {
        "bottom_right": (0.5, 0.7, 1.0, 1.0),   # 우하단
        "bottom_left": (0.0, 0.7, 0.5, 1.0),    # 좌하단
        "top_right": (0.5, 0.0, 1.0, 0.3),      # 우상단
        "full": (0.0, 0.0, 1.0, 1.0),           # 전체
    }

    # 필드별 정규식 패턴
    FIELD_PATTERNS = {
        # 도면번호: TD0060700, TD0062018 등
        "drawing_number": [
            r"TD\d{7}",
            r"DWG\.?\s*NO\.?\s*[:.]?\s*([A-Z]{2}\d{7})",
            r"도면번호\s*[:.]?\s*([A-Z]{2}\d+)",
        ],
        # 리비전: Rev.A, REV B, A, B 등
        "revision": [
            r"REV\.?\s*([A-Z])\b",
            r"리비전\s*[:.]?\s*([A-Z])",
            r"\bR([A-Z])\b",
        ],
        # 품명: 영문 대문자 조합
        "part_name": [
            r"((?:BEARING|CASING|RING|PAD|BOLT|PIN|NUT|WASHER|SHIM|WEDGE|LINER|THRUST|ASSY)[\w\s\(\)]*)",
            r"품명\s*[:.]?\s*([\w\s\(\)]+)",
            r"PART\s*NAME\s*[:.]?\s*([\w\s\(\)]+)",
        ],
        # 재질: SF440A, SS400, SM490A 등
        "material": [
            r"\b(SF\d+[A-Z]?)\b",
            r"\b(SS\d+)\b",
            r"\b(SM\d+[A-Z]?)\b",
            r"\b(S45C(?:-N)?)\b",
            r"\b(SUS\d+)\b",
            r"\b(ASTM\s*[A-Z]\d+(?:\s*(?:GR\.?\s*\d+|NO\.?\s*\d+|B\d+))?)\b",
            r"\b(SCM\d+)\b",
            r"재질\s*[:.]?\s*([\w\d]+)",
            r"MAT(?:'?L|ERIAL)?\s*[:.]?\s*([\w\d]+)",
        ],
        # 중량: 882 kg, 1.5kg 등
        "weight": [
            r"(\d+(?:\.\d+)?)\s*(?:kg|KG)",
            r"중량\s*[:.]?\s*(\d+(?:\.\d+)?)",
            r"WEIGHT\s*[:.]?\s*(\d+(?:\.\d+)?)",
        ],
        # 축척: 1:1, 1:2, NTS 등
        "scale": [
            r"(\d+\s*:\s*\d+)",
            r"SCALE\s*[:.]?\s*(\d+\s*:\s*\d+)",
            r"(NTS|N\.T\.S\.)",
            r"척도\s*[:.]?\s*(\d+\s*:\s*\d+)",
        ],
        # 작성일: 2025.01.10, 2025-01-10 등
        "date": [
            r"(\d{4}[.\-/]\d{2}[.\-/]\d{2})",
            r"DATE\s*[:.]?\s*(\d{4}[.\-/]\d{2}[.\-/]\d{2})",
        ],
        # 작성자
        "author": [
            r"작성\s*[:.]?\s*([\w가-힣]+)",
            r"DRAWN\s*(?:BY)?\s*[:.]?\s*([\w]+)",
        ],
    }

    # 재질 정규화 매핑
    MATERIAL_NORMALIZATION = {
        "SF440": "SF440A",
        "SF-440A": "SF440A",
        "SS-400": "SS400",
        "SM-490A": "SM490A",
        "S45C-N": "S45C-N",
        "S45CN": "S45C-N",
        "ASTM B23": "ASTM B23 GR.2",
        "B23": "ASTM B23 GR.2",
    }

    def _crop_image(self, file_bytes: bytes, position: str) -> bytes:
        """Title Block 위치 기반 이미지 크롭"""
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

    def _extract_field(self, text: str, field: str) -> Optional[str]:
        """정규식으로 필드 추출"""
        patterns = self.FIELD_PATTERNS.get(field, [])

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 그룹이 있으면 첫 번째 그룹, 없으면 전체 매치
                value = match.group(1) if match.groups() else match.group(0)
                return value.strip()

        return None

    def _normalize_material(self, material: str) -> str:
        """재질 코드 정규화"""
        if not material:
            return material

        upper = material.upper().strip()

        # 정규화 매핑 확인
        for key, normalized in self.MATERIAL_NORMALIZATION.items():
            if key.upper() == upper or key.upper() in upper:
                return normalized

        return upper

    def _calculate_confidence(self, parsed_fields: Dict[str, Any], required_fields: List[str]) -> float:
        """파싱 신뢰도 계산"""
        if not required_fields:
            required_fields = ["drawing_number", "revision", "part_name", "material"]

        found = sum(1 for f in required_fields if parsed_fields.get(f))
        return found / len(required_fields)

    async def _detect_with_table_detector(
        self,
        file_bytes: bytes,
        ocr_engine: str
    ) -> Dict[str, Any]:
        """Table Detector API로 Title Block 검출 및 OCR"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=30.0)) as client:
            files = {"file": ("titleblock.png", file_bytes, "image/png")}
            data = {
                "mode": "analyze",
                "ocr_engine": ocr_engine,
                "borderless": "true",
                "confidence_threshold": "0.5",
                "min_confidence": "40",
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

    def _extract_text_from_tables(self, tables: List[Dict]) -> str:
        """테이블 결과에서 텍스트 추출"""
        texts = []

        for table in tables:
            # 헤더 추출
            headers = table.get("headers", [])
            if headers:
                texts.append(" ".join(str(h) for h in headers if h))

            # 데이터 추출
            data = table.get("data", [])
            for row in data:
                if isinstance(row, list):
                    texts.append(" ".join(str(cell) for cell in row if cell))
                elif isinstance(row, dict):
                    texts.append(" ".join(str(v) for v in row.values() if v))

        return " ".join(texts)

    def _parse_with_dse_bearing_service(self, raw_text: str, tables: List[Dict]) -> Dict[str, Any]:
        """DSE Bearing 파서 서비스로 Title Block 파싱"""
        try:
            from services.dsebearing_parser import get_parser

            parser = get_parser()

            # OCR 텍스트를 파서 입력 형식으로 변환
            ocr_texts = []
            for text in raw_text.split("\n"):
                if text.strip():
                    ocr_texts.append({"text": text.strip(), "confidence": 0.9})

            # 테이블 데이터에서도 텍스트 추출
            for table in tables:
                data = table.get("data", [])
                for row in data:
                    if isinstance(row, list):
                        for cell in row:
                            if cell and str(cell).strip():
                                ocr_texts.append({"text": str(cell).strip(), "confidence": 0.85})

            # 파싱 수행
            result = parser.parse_title_block(ocr_texts)

            logger.info(f"DSE Bearing 파서 결과: {result.drawing_number}, Rev.{result.revision}")

            return {
                "drawing_number": result.drawing_number,
                "revision": result.revision,
                "part_name": result.part_name,
                "material": result.material,
                "date": result.date,
                "scale": result.scale,
                "size": result.size,
                "sheet": result.sheet,
                "company": result.company,
            }

        except Exception as e:
            logger.error(f"DSE Bearing 파서 오류: {e}")
            return {}

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Title Block Parser 실행

        Parameters:
            - image: 도면 이미지 (base64 또는 PIL Image)
            - detection_method: 검출 방식 (auto, table_detector, template)
            - title_block_position: Title Block 위치
            - ocr_engine: OCR 엔진
            - company_template: 회사 템플릿
            - extract_fields: 추출할 필드 목록

        Returns:
            - title_block: 파싱된 필드 딕셔너리
            - drawing_number, revision, part_name, material 등 개별 필드
            - raw_text: OCR 원본 텍스트
            - confidence: 파싱 신뢰도
        """
        # 이전 노드 결과 패스스루
        passthrough_data = {
            "detections": inputs.get("detections", []),
            "tables": inputs.get("tables", []),
        }

        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터 추출
        detection_method = self.parameters.get("detection_method", "auto")
        position = self.parameters.get("title_block_position", "bottom_right")
        ocr_engine = self.parameters.get("ocr_engine", "paddle")
        profile = self.parameters.get("profile", "generic")  # bearing, dse, generic
        extract_fields = self.parameters.get("extract_fields", [
            "drawing_number", "revision", "part_name", "material"
        ])

        # Title Block 영역 크롭
        if position != "auto":
            cropped_bytes = self._crop_image(file_bytes, position)
        else:
            # auto: 우하단부터 시도
            cropped_bytes = self._crop_image(file_bytes, "bottom_right")

        # Table Detector로 OCR 수행
        table_result = await self._detect_with_table_detector(cropped_bytes, ocr_engine)

        if not table_result.get("success", False):
            # 실패 시 전체 이미지로 재시도
            table_result = await self._detect_with_table_detector(file_bytes, ocr_engine)

        # OCR 텍스트 추출
        raw_text = ""
        tables = []
        if table_result.get("success"):
            tables = table_result.get("tables", [])
            raw_text = self._extract_text_from_tables(tables)

        # 프로파일에 따른 파싱 방식 선택
        if profile in ["bearing", "dse", "dsebearing"]:
            # DSE Bearing 전용 파서 사용
            logger.info(f"DSE Bearing 프로파일로 Title Block 파싱: {profile}")
            parsed_fields = self._parse_with_dse_bearing_service(raw_text, tables)

            # DSE 파서가 실패하면 기본 파싱으로 폴백
            if not parsed_fields.get("drawing_number"):
                logger.warning("DSE 파서 결과 부족, 기본 파싱으로 폴백")
                for field in extract_fields:
                    if not parsed_fields.get(field):
                        value = self._extract_field(raw_text, field)
                        if field == "material" and value:
                            value = self._normalize_material(value)
                        parsed_fields[field] = value
        else:
            # 기본 정규식 기반 파싱
            parsed_fields = {}
            for field in extract_fields:
                value = self._extract_field(raw_text, field)

                # 재질 정규화
                if field == "material" and value:
                    value = self._normalize_material(value)

                parsed_fields[field] = value

        # 신뢰도 계산
        confidence = self._calculate_confidence(parsed_fields, extract_fields)

        # 원본 이미지 패스스루
        import base64
        original_image = inputs.get("image", "")
        if not original_image and file_bytes:
            original_image = base64.b64encode(file_bytes).decode("utf-8")

        output = {
            # Title Block 파싱 결과
            "title_block": parsed_fields,
            "drawing_number": parsed_fields.get("drawing_number"),
            "revision": parsed_fields.get("revision"),
            "part_name": parsed_fields.get("part_name"),
            "material": parsed_fields.get("material"),
            "weight": parsed_fields.get("weight"),
            "scale": parsed_fields.get("scale"),
            "raw_text": raw_text,
            "confidence": confidence,
            # 처리 정보
            "detection_method": detection_method,
            "ocr_engine": ocr_engine,
            "tables_found": len(table_result.get("tables", [])),
            # 원본 이미지 패스스루
            "image": original_image,
            # 이전 노드 결과 패스스루
            **passthrough_data,
        }

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # detection_method 검증
        if "detection_method" in self.parameters:
            method = self.parameters["detection_method"]
            if method not in ["auto", "table_detector", "template"]:
                return False, "detection_method는 'auto', 'table_detector', 'template' 중 하나여야 합니다"

        # ocr_engine 검증
        if "ocr_engine" in self.parameters:
            engine = self.parameters["ocr_engine"]
            if engine not in ["tesseract", "paddle", "easyocr"]:
                return False, "ocr_engine은 'tesseract', 'paddle', 'easyocr' 중 하나여야 합니다"

        # position 검증
        if "title_block_position" in self.parameters:
            pos = self.parameters["title_block_position"]
            valid_positions = list(self.POSITION_PRESETS.keys()) + ["auto"]
            if pos not in valid_positions:
                return False, f"title_block_position은 {valid_positions} 중 하나여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 도면 이미지"
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "title_block": {
                    "type": "object",
                    "description": "파싱된 Title Block 필드 딕셔너리"
                },
                "drawing_number": {
                    "type": "string",
                    "description": "도면번호 (예: TD0062018)"
                },
                "revision": {
                    "type": "string",
                    "description": "리비전 (예: A)"
                },
                "part_name": {
                    "type": "string",
                    "description": "품명"
                },
                "material": {
                    "type": "string",
                    "description": "재질"
                },
                "confidence": {
                    "type": "number",
                    "description": "파싱 신뢰도 (0-1)"
                },
                "raw_text": {
                    "type": "string",
                    "description": "OCR 원본 텍스트"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("titleblock", TitleBlockExecutor)
ExecutorRegistry.register("title_block", TitleBlockExecutor)
ExecutorRegistry.register("titleblock_parser", TitleBlockExecutor)
