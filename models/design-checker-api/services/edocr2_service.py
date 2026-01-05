"""
eDOCr2 Integration Service - P&ID 도면 OCR 및 치수/GD&T 추출
Engineering Drawing OCR (치수, GD&T, 텍스트 추출 특화)
"""
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# eDOCr2 API 설정
EDOCR2_API_URL = os.getenv("EDOCR2_API_URL", "http://edocr2-v2-api:5002")
EDOCR2_TIMEOUT = float(os.getenv("EDOCR2_TIMEOUT", "120"))


@dataclass
class Dimension:
    """치수 정보"""
    value: str
    tolerance: Optional[str] = None
    unit: str = "mm"
    bbox: list = field(default_factory=list)
    dim_type: str = "linear"  # linear, diameter, radius, angle
    confidence: float = 0.0


@dataclass
class GDTSymbol:
    """GD&T 기호 정보"""
    symbol: str
    gdt_type: str  # position, flatness, perpendicularity, etc.
    tolerance: Optional[str] = None
    datum: list = field(default_factory=list)
    bbox: list = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class TextBlock:
    """텍스트 블록"""
    text: str
    bbox: list = field(default_factory=list)
    confidence: float = 0.0
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0


@dataclass
class EDOCr2Result:
    """eDOCr2 API 응답 결과"""
    success: bool
    dimensions: list[Dimension] = field(default_factory=list)
    gdt_symbols: list[GDTSymbol] = field(default_factory=list)
    text_blocks: list[TextBlock] = field(default_factory=list)
    tables: list = field(default_factory=list)
    drawing_number: Optional[str] = None
    material: Optional[str] = None
    visualized_image: Optional[str] = None
    processing_time: float = 0.0
    error: Optional[str] = None


class EDOCr2Service:
    """eDOCr2 API 연동 서비스"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or EDOCR2_API_URL
        self.timeout = EDOCR2_TIMEOUT

    async def extract_from_image(
        self,
        image_data: bytes,
        extract_dimensions: bool = True,
        extract_gdt: bool = True,
        extract_text: bool = True,
        use_vl_model: bool = False,
        visualize: bool = False,
        use_gpu_preprocessing: bool = False,
    ) -> EDOCr2Result:
        """
        이미지에서 치수, GD&T, 텍스트 추출

        Args:
            image_data: 이미지 바이트 데이터
            extract_dimensions: 치수 추출 활성화
            extract_gdt: GD&T 추출 활성화
            extract_text: 텍스트 추출 활성화
            use_vl_model: Vision Language 모델 사용 (더 정확하지만 느림)
            visualize: 시각화 이미지 생성
            use_gpu_preprocessing: GPU 전처리 사용

        Returns:
            EDOCr2Result: 추출 결과
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 멀티파트 폼 데이터 구성
                files = {"file": ("image.png", image_data, "image/png")}
                data = {
                    "extract_dimensions": str(extract_dimensions).lower(),
                    "extract_gdt": str(extract_gdt).lower(),
                    "extract_text": str(extract_text).lower(),
                    "use_vl_model": str(use_vl_model).lower(),
                    "visualize": str(visualize).lower(),
                    "use_gpu_preprocessing": str(use_gpu_preprocessing).lower(),
                }

                response = await client.post(
                    f"{self.base_url}/api/v2/ocr",
                    files=files,
                    data=data,
                )

                if response.status_code != 200:
                    return EDOCr2Result(
                        success=False,
                        error=f"eDOCr2 API error: {response.status_code} - {response.text[:200]}",
                    )

                result = response.json()

                if result.get("status") != "success":
                    return EDOCr2Result(
                        success=False,
                        processing_time=result.get("processing_time", 0),
                        error=result.get("message", "Unknown error"),
                    )

                # 응답 파싱
                data_part = result.get("data", {})

                # 치수 파싱
                dimensions = []
                for dim in data_part.get("dimensions", []):
                    dimensions.append(Dimension(
                        value=dim.get("value", ""),
                        tolerance=dim.get("tolerance"),
                        unit=dim.get("unit", "mm"),
                        bbox=dim.get("bbox", []),
                        dim_type=dim.get("type", "linear"),
                        confidence=dim.get("confidence", 0),
                    ))

                # GD&T 파싱 (eDOCr2는 'gdt' 키 사용)
                gdt_symbols = []
                for gdt in data_part.get("gdt_symbols", data_part.get("gdt", [])):
                    gdt_symbols.append(GDTSymbol(
                        symbol=gdt.get("symbol", ""),
                        gdt_type=gdt.get("type", ""),
                        tolerance=gdt.get("tolerance"),
                        datum=gdt.get("datum", []),
                        bbox=gdt.get("bbox", []),
                        confidence=gdt.get("confidence", 0),
                    ))

                # 텍스트 블록 파싱
                text_blocks = []

                # 1. text_blocks 키에서 파싱
                for text in data_part.get("text_blocks", []):
                    bbox = text.get("bbox", [])
                    text_blocks.append(TextBlock(
                        text=text.get("text", ""),
                        bbox=bbox,
                        confidence=text.get("confidence", 0),
                        x=bbox[0] if len(bbox) >= 4 else 0,
                        y=bbox[1] if len(bbox) >= 4 else 0,
                        width=bbox[2] - bbox[0] if len(bbox) >= 4 else 0,
                        height=bbox[3] - bbox[1] if len(bbox) >= 4 else 0,
                    ))

                # 2. tables 키에서 파싱 (eDOCr2 P&ID 응답 형식)
                for table in data_part.get("tables", []):
                    for item in table:
                        if isinstance(item, dict) and item.get("text"):
                            text_blocks.append(TextBlock(
                                text=item.get("text", ""),
                                bbox=[
                                    item.get("left", 0),
                                    item.get("top", 0),
                                    item.get("left", 0) + item.get("width", 0),
                                    item.get("top", 0) + item.get("height", 0)
                                ],
                                confidence=item.get("confidence", 0.9),
                                x=item.get("left", 0),
                                y=item.get("top", 0),
                                width=item.get("width", 0),
                                height=item.get("height", 0),
                            ))

                # 3. text 키에서 파싱 (dict 형태인 경우)
                text_data = data_part.get("text", {})
                if isinstance(text_data, dict):
                    for key, items in text_data.items():
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict) and item.get("text"):
                                    text_blocks.append(TextBlock(
                                        text=item.get("text", ""),
                                        bbox=[
                                            item.get("left", 0),
                                            item.get("top", 0),
                                            item.get("left", 0) + item.get("width", 0),
                                            item.get("top", 0) + item.get("height", 0)
                                        ],
                                        confidence=item.get("confidence", 0.9),
                                        x=item.get("left", 0),
                                        y=item.get("top", 0),
                                        width=item.get("width", 0),
                                        height=item.get("height", 0),
                                    ))

                return EDOCr2Result(
                    success=True,
                    dimensions=dimensions,
                    gdt_symbols=gdt_symbols,
                    text_blocks=text_blocks,
                    tables=data_part.get("tables", []),
                    drawing_number=data_part.get("drawing_number"),
                    material=data_part.get("material"),
                    visualized_image=data_part.get("visualized_image"),
                    processing_time=result.get("processing_time", 0),
                )

        except httpx.TimeoutException:
            return EDOCr2Result(
                success=False,
                error=f"eDOCr2 API timeout after {self.timeout}s",
            )
        except Exception as e:
            logger.error(f"eDOCr2 extraction error: {e}", exc_info=True)
            return EDOCr2Result(
                success=False,
                error=str(e),
            )

    def get_all_texts(self, result: EDOCr2Result) -> list[str]:
        """
        모든 텍스트 추출 (검증용)

        치수값, GD&T, 텍스트 블록 모두 포함
        """
        texts = []

        # 치수값 추가
        for dim in result.dimensions:
            texts.append(dim.value)
            if dim.tolerance:
                texts.append(dim.tolerance)

        # GD&T 추가
        for gdt in result.gdt_symbols:
            texts.append(gdt.symbol)
            if gdt.tolerance:
                texts.append(gdt.tolerance)
            texts.extend(gdt.datum)

        # 텍스트 블록 추가
        for text in result.text_blocks:
            texts.append(text.text)

        # 도면번호, 재질 추가
        if result.drawing_number:
            texts.append(result.drawing_number)
        if result.material:
            texts.append(result.material)

        return list(set(t for t in texts if t))

    def get_equipment_tags(
        self,
        result: EDOCr2Result,
        patterns: list[str] = None
    ) -> list[str]:
        """
        장비 태그 추출

        P&ID에서 자주 나타나는 장비 태그 패턴 매칭
        """
        import re

        # 기본 패턴: P&ID 장비 태그
        default_patterns = [
            r"[A-Z]{2,4}-\d{3,4}[A-Z]?",  # TRO-001A, PT-001
            r"[A-Z]{1,2}\d{3,4}[A-Z]?",    # V001, P001A
            r"\d{1,2}-[A-Z]{2,4}-\d{3,4}", # 1-PT-001
            r"ECS\s*\d*",                  # ECS, ECS1
            r"HYCHLOR\s*\d*",              # HYCHLOR
            r"TRO\s*SENSOR",               # TRO SENSOR
            r"BWMS",                       # BWMS
            r"UV\s*(UNIT|SYSTEM)",         # UV UNIT
            r"FILTER\s*(UNIT)?",           # FILTER, FILTER UNIT
        ]

        patterns = patterns or default_patterns
        tags = []

        all_texts = self.get_all_texts(result)

        for text in all_texts:
            for pattern in patterns:
                matches = re.findall(pattern, text.upper())
                tags.extend(matches)

        return list(set(tags))

    async def check_health(self) -> bool:
        """eDOCr2 API 상태 확인"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/v1/health")
                return response.status_code == 200
        except Exception:
            return False


# 싱글톤 인스턴스
edocr2_service = EDOCr2Service()
