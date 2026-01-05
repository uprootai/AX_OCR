"""
Tag Extractor - 정규식 기반 장비 태그 추출
P&ID 도면 OCR 결과에서 TECHCROSS BWMS 장비 태그 식별
"""
import re
import logging
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTag:
    """추출된 태그 정보"""
    tag: str  # 원본 태그 (예: "ECU-01")
    tag_type: str  # 장비 유형 (예: "ECU")
    tag_number: Optional[str] = None  # 번호 (예: "01")
    full_text: str = ""  # OCR 전체 텍스트
    confidence: float = 0.0
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    product_type: str = "ALL"  # ECS, HYCHLOR, ALL


@dataclass
class ExtractionResult:
    """태그 추출 결과"""
    tags: list[ExtractedTag] = field(default_factory=list)
    tags_by_type: dict = field(default_factory=dict)
    total_texts: int = 0
    total_tags: int = 0
    product_type: str = "UNKNOWN"  # 자동 감지된 제품 유형


# TECHCROSS BWMS 장비 태그 패턴 정의
TAG_PATTERNS = {
    # ============================================================
    # ECS 전용 장비 (직접식 전기분해)
    # ============================================================
    "ECU": {
        "pattern": r"\bECU[-_\s]?\d*[A-Z]?\b|\bECU\s*\d+B\b",
        "description": "Electrolysis Chamber Unit (전기분해 챔버)",
        "product_type": "ECS",
        "priority": 1,
    },
    "PRU": {
        "pattern": r"\bPRU[-_\s]?\d*[A-Z]?\b",
        "description": "Power Rectifier Unit (정류기)",
        "product_type": "ECS",
        "priority": 1,
    },
    "MIXING": {
        "pattern": r"\bMIXING\s*S\.?W\.?\s*PUMP\b",
        "description": "Mixing Seawater Pump",
        "product_type": "ECS",
        "priority": 2,
    },

    # ============================================================
    # HYCHLOR 전용 장비 (간접식 전기분해)
    # ============================================================
    "HGU": {
        "pattern": r"\bHGU[-_]?\d*\b",
        "description": "Hypochlorite Generation Unit (염소 가스 발생기)",
        "product_type": "HYCHLOR",
        "priority": 1,
    },
    "DMU": {
        "pattern": r"\bDMU[-_]?\d*\b",
        "description": "Dosing & Mixing Unit (가스 분배)",
        "product_type": "HYCHLOR",
        "priority": 1,
    },
    "NIU": {
        "pattern": r"\bNIU[-_]?\d*\b",
        "description": "Neutralization Injection Unit",
        "product_type": "HYCHLOR",
        "priority": 1,
    },
    "SWH": {
        "pattern": r"\bSWH[-_]?\d*\b",
        "description": "Seawater Heater",
        "product_type": "HYCHLOR",
        "priority": 2,
    },
    "CIP": {
        "pattern": r"\bCIP[-_]?\d*\b",
        "description": "Cleaning In Place",
        "product_type": "HYCHLOR",
        "priority": 2,
    },

    # ============================================================
    # 공통 장비 (ECS & HYCHLOR)
    # ============================================================
    "FMU": {
        "pattern": r"\bFMU[-_\s]?\d*[A-Z]?\b",
        "description": "Flow Meter Unit (유량계)",
        "product_type": "ALL",
        "priority": 1,
    },
    "ANU": {
        "pattern": r"\bANU[-_]?\d*[A-Z]?\b",
        "description": "Automatic Neutralization Unit (중화제)",
        "product_type": "ALL",
        "priority": 1,
    },
    "TSU": {
        "pattern": r"\bTSU[-_]?[A-Z0-9]*\b",
        "description": "TRO Sensing Unit",
        "product_type": "ALL",
        "priority": 1,
    },
    "APU": {
        "pattern": r"\bAPU[-_\s]?\d*\b|NO\.\d+\s*APU",
        "description": "Auto Pump Unit (샘플링)",
        "product_type": "ALL",
        "priority": 1,
    },
    "GDS": {
        "pattern": r"\bGDS[-_]?\d*\b",
        "description": "Gas Detection System",
        "product_type": "ALL",
        "priority": 1,
    },
    "DTS": {
        "pattern": r"\bDTS[-_]?\d*\b",
        "description": "Data Transmission System",
        "product_type": "ALL",
        "priority": 2,
    },
    "EWU": {
        "pattern": r"\bEWU[-_]?\d*\b",
        "description": "Emergency Wash Unit",
        "product_type": "ALL",
        "priority": 2,
    },
    "FTS": {
        "pattern": r"\bFTS[-_]?\d*\b",
        "description": "Flow Transmitter System",
        "product_type": "ALL",
        "priority": 2,
    },
    "CPC": {
        "pattern": r"\bCPC[-_]?\d*\b",
        "description": "Control PC",
        "product_type": "ALL",
        "priority": 2,
    },
    "VLS": {
        "pattern": r"\bVLS[-_]?\d*\b",
        "description": "Valve Signal System",
        "product_type": "ALL",
        "priority": 2,
    },
    "CSU": {
        "pattern": r"\bCSU[-_]?\d*\b",
        "description": "Control Signal Unit",
        "product_type": "ALL",
        "priority": 2,
    },
    "RIO": {
        "pattern": r"\bRIO[-_]?\d*\b",
        "description": "Remote I/O",
        "product_type": "ALL",
        "priority": 2,
    },
    "DTU": {
        "pattern": r"\bDTU[-_]?\d*\b",
        "description": "Data Transfer Unit",
        "product_type": "ALL",
        "priority": 2,
    },
    "FTU": {
        "pattern": r"\bFTU[-_]?\d*\b",
        "description": "Filter Unit",
        "product_type": "ALL",
        "priority": 2,
    },
    "HEU": {
        "pattern": r"\bHEU[-_]?\d*\b",
        "description": "Heat Exchanger Unit",
        "product_type": "ALL",
        "priority": 2,
    },
    "VCU": {
        "pattern": r"\bVCU[-_]?\d*\b",
        "description": "Valve Control Unit",
        "product_type": "ALL",
        "priority": 2,
    },
    "PCU": {
        "pattern": r"\bPCU[-_]?\d*\b",
        "description": "Pump Control Unit",
        "product_type": "ALL",
        "priority": 2,
    },

    # ============================================================
    # Valve 태그
    # ============================================================
    "BWV": {
        "pattern": r"\bBWV[-_]?\d+\b",
        "description": "Ballast Water Valve",
        "product_type": "ALL",
        "priority": 1,
    },
    "FCV": {
        "pattern": r"\bFCV[-_]?\d+\b",
        "description": "Flow Control Valve",
        "product_type": "ALL",
        "priority": 1,
    },
    "PDE": {
        "pattern": r"\bPDE[-_]?\d*[A-Z]?\b",
        "description": "Power Distribution Equipment",
        "product_type": "ALL",
        "priority": 2,
    },

    # ============================================================
    # Sensor 태그
    # ============================================================
    "PT": {
        "pattern": r"\bPT[-_]?\d+\b",
        "description": "Pressure Transmitter",
        "product_type": "ALL",
        "priority": 2,
    },
    "FT": {
        "pattern": r"\bFT[-_]?\d+\b",
        "description": "Flow Transmitter",
        "product_type": "ALL",
        "priority": 2,
    },
    "TT": {
        "pattern": r"\bTT[-_]?\d+\b",
        "description": "Temperature Transmitter",
        "product_type": "ALL",
        "priority": 2,
    },
    "LT": {
        "pattern": r"\bLT[-_]?\d+\b",
        "description": "Level Transmitter",
        "product_type": "ALL",
        "priority": 2,
    },
    "FS": {
        "pattern": r"\bFS[-_]?\d+\b",
        "description": "Flow Switch",
        "product_type": "ALL",
        "priority": 2,
    },
}


class TagExtractor:
    """태그 추출기"""

    def __init__(self, patterns: dict = None):
        self.patterns = patterns or TAG_PATTERNS
        self._compile_patterns()

    def _compile_patterns(self):
        """정규식 패턴 컴파일"""
        self._compiled = {}
        for tag_type, config in self.patterns.items():
            self._compiled[tag_type] = re.compile(
                config["pattern"],
                re.IGNORECASE
            )

    def extract_from_ocr_results(
        self,
        ocr_results: list,
        min_confidence: float = 0.5
    ) -> ExtractionResult:
        """
        OCR 결과에서 태그 추출

        Args:
            ocr_results: OCRResult 리스트 또는 dict 리스트
            min_confidence: 최소 신뢰도

        Returns:
            ExtractionResult
        """
        extracted_tags = []
        tags_by_type = defaultdict(list)
        ecs_score = 0
        hychlor_score = 0

        for ocr in ocr_results:
            # dict 또는 dataclass 처리
            if isinstance(ocr, dict):
                text = ocr.get("text", "")
                confidence = ocr.get("confidence", 0.0)
                x = ocr.get("x", ocr.get("position", {}).get("x", 0))
                y = ocr.get("y", ocr.get("position", {}).get("y", 0))
                width = ocr.get("width", ocr.get("position", {}).get("width", 0))
                height = ocr.get("height", ocr.get("position", {}).get("height", 0))
            else:
                text = getattr(ocr, "text", "")
                confidence = getattr(ocr, "confidence", 0.0)
                x = getattr(ocr, "x", 0)
                y = getattr(ocr, "y", 0)
                width = getattr(ocr, "width", 0)
                height = getattr(ocr, "height", 0)

            if confidence < min_confidence:
                continue

            # 각 패턴으로 검색
            for tag_type, regex in self._compiled.items():
                match = regex.search(text)
                if match:
                    tag_value = match.group(0).upper()
                    config = self.patterns[tag_type]

                    # 번호 추출
                    number_match = re.search(r"\d+", tag_value)
                    tag_number = number_match.group(0) if number_match else None

                    tag = ExtractedTag(
                        tag=tag_value,
                        tag_type=tag_type,
                        tag_number=tag_number,
                        full_text=text,
                        confidence=confidence,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        product_type=config["product_type"]
                    )

                    extracted_tags.append(tag)
                    tags_by_type[tag_type].append(tag)

                    # 제품 유형 스코어링
                    if config["product_type"] == "ECS":
                        ecs_score += config["priority"]
                    elif config["product_type"] == "HYCHLOR":
                        hychlor_score += config["priority"]

        # 제품 유형 자동 감지
        if ecs_score > hychlor_score and ecs_score > 0:
            product_type = "ECS"
        elif hychlor_score > ecs_score and hychlor_score > 0:
            product_type = "HYCHLOR"
        else:
            product_type = "UNKNOWN"

        result = ExtractionResult(
            tags=extracted_tags,
            tags_by_type=dict(tags_by_type),
            total_texts=len(ocr_results),
            total_tags=len(extracted_tags),
            product_type=product_type
        )

        logger.info(
            f"Extracted {result.total_tags} tags from {result.total_texts} texts, "
            f"product_type={result.product_type}"
        )

        return result

    def extract_from_texts(
        self,
        texts: list[str],
    ) -> ExtractionResult:
        """
        텍스트 목록에서 태그 추출 (단순화된 버전)

        Args:
            texts: 텍스트 문자열 리스트

        Returns:
            ExtractionResult
        """
        # 텍스트를 OCR 결과 형식으로 변환 후 기존 메소드 사용
        ocr_results = [
            {"text": text, "confidence": 1.0, "x": 0, "y": 0, "width": 0, "height": 0}
            for text in texts if text
        ]
        return self.extract_from_ocr_results(ocr_results, min_confidence=0.0)

    def get_unique_equipment(
        self,
        extraction_result: ExtractionResult
    ) -> dict[str, list[str]]:
        """
        중복 제거된 장비 목록 반환

        Returns:
            {"ECU": ["ECU", "ECU 1000B"], "FMU": ["FMU"], ...}
        """
        unique = {}
        for tag_type, tags in extraction_result.tags_by_type.items():
            unique[tag_type] = list(set(t.tag for t in tags))
        return unique

    def check_equipment_exists(
        self,
        extraction_result: ExtractionResult,
        equipment_type: str
    ) -> tuple[bool, list[ExtractedTag]]:
        """
        특정 장비가 도면에 존재하는지 확인

        Args:
            extraction_result: 추출 결과
            equipment_type: 장비 유형 (예: "ECU", "FMU")

        Returns:
            (존재 여부, 검출된 태그 리스트)
        """
        tags = extraction_result.tags_by_type.get(equipment_type.upper(), [])
        return len(tags) > 0, tags

    def find_equipment_near(
        self,
        extraction_result: ExtractionResult,
        target_tag: ExtractedTag,
        search_type: str,
        max_distance: float = 500.0
    ) -> list[ExtractedTag]:
        """
        특정 장비 근처에 있는 다른 장비 찾기

        Args:
            extraction_result: 추출 결과
            target_tag: 기준 장비
            search_type: 찾을 장비 유형
            max_distance: 최대 거리 (픽셀)

        Returns:
            근처에 있는 태그 리스트
        """
        nearby = []
        search_tags = extraction_result.tags_by_type.get(search_type.upper(), [])

        for tag in search_tags:
            distance = (
                (tag.x - target_tag.x) ** 2 +
                (tag.y - target_tag.y) ** 2
            ) ** 0.5

            if distance <= max_distance:
                nearby.append(tag)

        return nearby


# 싱글톤 인스턴스
tag_extractor = TagExtractor()
