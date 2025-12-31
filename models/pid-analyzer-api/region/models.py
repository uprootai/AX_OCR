"""
Region Data Models
영역 기반 텍스트 추출용 데이터 클래스

저자: Claude AI (Opus 4.5)
생성일: 2025-12-29
리팩토링: 2025-12-31
"""
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# =====================
# Data Classes
# =====================

@dataclass
class ExtractionPattern:
    """추출 패턴 정의"""
    type: str  # valve_tag, equipment_tag, label, etc.
    regex: str
    description: str = ""
    priority: int = 0

    def match(self, text: str) -> Optional[Dict[str, Any]]:
        """텍스트에서 패턴 매칭"""
        try:
            pattern = re.compile(self.regex, re.IGNORECASE)
            match = pattern.search(text)
            if match:
                return {
                    "matched_text": match.group(0),
                    "groups": match.groups() if match.groups() else [],
                    "type": self.type,
                    "pattern": self.regex
                }
        except re.error as e:
            logger.warning(f"Regex error in pattern '{self.regex}': {e}")
        return None


@dataclass
class RegionTextPattern:
    """영역 식별용 텍스트 패턴"""
    pattern: str
    case_insensitive: bool = True
    is_regex: bool = False

    def matches(self, text: str) -> bool:
        """텍스트가 패턴과 매칭되는지 확인"""
        try:
            if self.is_regex:
                flags = re.IGNORECASE if self.case_insensitive else 0
                return bool(re.search(self.pattern, text, flags))
            else:
                compare_text = text.lower() if self.case_insensitive else text
                compare_pattern = self.pattern.lower() if self.case_insensitive else self.pattern
                return compare_pattern in compare_text
        except Exception as e:
            logger.warning(f"Pattern match error: {e}")
            return False


@dataclass
class RegionCriteria:
    """영역 매칭 기준"""
    line_styles: List[str] = field(default_factory=lambda: ["dashed", "dash_dot"])
    min_area: int = 1000
    max_area: Optional[int] = None
    aspect_ratio_min: Optional[float] = None
    aspect_ratio_max: Optional[float] = None


@dataclass
class ExtractionRule:
    """추출 규칙 정의"""
    id: str
    name: str
    description: str = ""
    enabled: bool = True

    # 영역 매칭 기준
    region_criteria: RegionCriteria = field(default_factory=RegionCriteria)

    # 영역 식별용 텍스트 패턴 (이 텍스트가 있어야 해당 영역으로 인식)
    region_text_patterns: List[RegionTextPattern] = field(default_factory=list)

    # 추출할 패턴들
    extraction_patterns: List[ExtractionPattern] = field(default_factory=list)

    # 출력 설정
    output_type: str = "list"  # list, excel, json
    output_filename_template: str = "{rule_id}_{timestamp}"

    # 메타데이터 (UI용)
    category: str = "general"
    icon: str = "list"
    color: str = "#3b82f6"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (API 응답용)"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "region_criteria": {
                "line_styles": self.region_criteria.line_styles,
                "min_area": self.region_criteria.min_area,
                "max_area": self.region_criteria.max_area,
                "aspect_ratio_min": self.region_criteria.aspect_ratio_min,
                "aspect_ratio_max": self.region_criteria.aspect_ratio_max,
            },
            "region_text_patterns": [
                {"pattern": p.pattern, "case_insensitive": p.case_insensitive, "is_regex": p.is_regex}
                for p in self.region_text_patterns
            ],
            "extraction_patterns": [
                {"type": p.type, "regex": p.regex, "description": p.description, "priority": p.priority}
                for p in self.extraction_patterns
            ],
            "output_type": self.output_type,
            "output_filename_template": self.output_filename_template,
            "category": self.category,
            "icon": self.icon,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractionRule":
        """딕셔너리에서 생성"""
        region_criteria_data = data.get("region_criteria", {})
        region_criteria = RegionCriteria(
            line_styles=region_criteria_data.get("line_styles", ["dashed", "dash_dot"]),
            min_area=region_criteria_data.get("min_area", 1000),
            max_area=region_criteria_data.get("max_area"),
            aspect_ratio_min=region_criteria_data.get("aspect_ratio_min"),
            aspect_ratio_max=region_criteria_data.get("aspect_ratio_max"),
        )

        region_text_patterns = [
            RegionTextPattern(
                pattern=p.get("pattern", ""),
                case_insensitive=p.get("case_insensitive", True),
                is_regex=p.get("is_regex", False)
            )
            for p in data.get("region_text_patterns", [])
        ]

        extraction_patterns = [
            ExtractionPattern(
                type=p.get("type", "unknown"),
                regex=p.get("regex", ""),
                description=p.get("description", ""),
                priority=p.get("priority", 0)
            )
            for p in data.get("extraction_patterns", [])
        ]

        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Rule"),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            region_criteria=region_criteria,
            region_text_patterns=region_text_patterns,
            extraction_patterns=extraction_patterns,
            output_type=data.get("output_type", "list"),
            output_filename_template=data.get("output_filename_template", "{rule_id}_{timestamp}"),
            category=data.get("category", "general"),
            icon=data.get("icon", "list"),
            color=data.get("color", "#3b82f6"),
        )


@dataclass
class MatchedRegion:
    """매칭된 영역 정보"""
    region_id: int
    rule_id: str
    bbox: List[float]
    region_texts: List[str]  # 영역 식별에 사용된 텍스트
    extracted_items: List[Dict[str, Any]]  # 추출된 항목들
    confidence: float = 1.0
