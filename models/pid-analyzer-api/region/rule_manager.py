"""
Rule Manager
YAML 파일 기반 규칙 저장/로드 관리

저자: Claude AI (Opus 4.5)
생성일: 2025-12-29
리팩토링: 2025-12-31
"""
import os
import yaml
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .models import (
    ExtractionPattern,
    RegionTextPattern,
    RegionCriteria,
    ExtractionRule,
)

logger = logging.getLogger(__name__)


class RuleManager:
    """규칙 관리자 - YAML 파일 기반 규칙 저장/로드"""

    def __init__(self, rules_file: str = None):
        if rules_file is None:
            # 기본 경로: 현재 디렉토리의 region_rules.yaml
            rules_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "region_rules.yaml"
            )

        self.rules_file = Path(rules_file)
        self.rules: Dict[str, ExtractionRule] = {}
        self._load_rules()

    def _load_rules(self):
        """YAML 파일에서 규칙 로드"""
        if not self.rules_file.exists():
            logger.info(f"Rules file not found: {self.rules_file}. Using defaults.")
            self._create_default_rules()
            return

        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data and "rules" in data:
                for rule_data in data["rules"]:
                    rule = ExtractionRule.from_dict(rule_data)
                    self.rules[rule.id] = rule

            logger.info(f"Loaded {len(self.rules)} rules from {self.rules_file}")

        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            self._create_default_rules()

    def _create_default_rules(self):
        """기본 규칙 생성"""
        # BWMS Valve Signal List 규칙
        bwms_valve_rule = ExtractionRule(
            id="valve_signal_bwms",
            name="Valve Signal List (BWMS)",
            description="SIGNAL FOR BWMS 영역 내 밸브 ID 추출",
            enabled=True,
            region_criteria=RegionCriteria(
                line_styles=["dashed", "dash_dot"],
                min_area=1000
            ),
            region_text_patterns=[
                RegionTextPattern(pattern="SIGNAL.*FOR.*BWMS", is_regex=True),
                RegionTextPattern(pattern="SIGNAL FOR BWMS"),
                RegionTextPattern(pattern="SIGNAL_FOR_BWMS"),
            ],
            extraction_patterns=[
                ExtractionPattern(
                    type="valve_tag",
                    regex=r"^(BWV|BAV|BCV|BBV|BXV|BSV|BFV|BRV)\d+[A-Z]?$",
                    description="BWMS 밸브 태그 (BWV, BAV, BCV 등)",
                    priority=10
                ),
                ExtractionPattern(
                    type="valve_tag",
                    regex=r"^(FCV|TCV|PCV|LCV|HCV|SCV|ACV)\d+[A-Z]?$",
                    description="일반 제어 밸브 태그",
                    priority=5
                ),
                ExtractionPattern(
                    type="valve_tag",
                    regex=r"^[A-Z]{2,4}-?\d{1,4}[A-Z]?$",
                    description="일반 밸브 태그 패턴",
                    priority=1
                ),
            ],
            output_type="excel",
            output_filename_template="Valve_Signal_List_{timestamp}",
            category="bwms",
            icon="valve",
            color="#ef4444"
        )

        # 일반 Signal 영역 규칙
        general_signal_rule = ExtractionRule(
            id="signal_region_general",
            name="Signal Region (General)",
            description="일반 SIGNAL 영역 내 태그 추출",
            enabled=True,
            region_criteria=RegionCriteria(
                line_styles=["dashed", "dash_dot", "dotted"],
                min_area=500
            ),
            region_text_patterns=[
                RegionTextPattern(pattern="SIGNAL", is_regex=False),
            ],
            extraction_patterns=[
                ExtractionPattern(
                    type="tag",
                    regex=r"^[A-Z]{1,5}-?\d{1,4}[A-Z]?$",
                    description="일반 태그 패턴",
                    priority=1
                ),
            ],
            output_type="list",
            category="general",
            icon="tag",
            color="#3b82f6"
        )

        # 알람 영역 규칙 (예시)
        alarm_rule = ExtractionRule(
            id="alarm_bypass",
            name="Alarm By-pass",
            description="ALARM BY-PASS 영역 내 밸브 추출",
            enabled=True,
            region_criteria=RegionCriteria(
                line_styles=["dashed", "dash_dot"],
                min_area=800
            ),
            region_text_patterns=[
                RegionTextPattern(pattern="ALARM.*BY-?PASS", is_regex=True),
                RegionTextPattern(pattern="ALARM BYPASS"),
            ],
            extraction_patterns=[
                ExtractionPattern(
                    type="valve_tag",
                    regex=r"^[A-Z]{2,4}-?\d{1,4}$",
                    description="알람 바이패스 밸브",
                    priority=5
                ),
            ],
            output_type="list",
            category="bwms",
            icon="bell",
            color="#f59e0b"
        )

        self.rules = {
            bwms_valve_rule.id: bwms_valve_rule,
            general_signal_rule.id: general_signal_rule,
            alarm_rule.id: alarm_rule,
        }

        # 기본 규칙 저장
        self.save_rules()

    def save_rules(self):
        """규칙을 YAML 파일로 저장"""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "rules": [rule.to_dict() for rule in self.rules.values()]
            }

            with open(self.rules_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            logger.info(f"Saved {len(self.rules)} rules to {self.rules_file}")

        except Exception as e:
            logger.error(f"Error saving rules: {e}")
            raise

    def get_rule(self, rule_id: str) -> Optional[ExtractionRule]:
        """규칙 조회"""
        return self.rules.get(rule_id)

    def get_all_rules(self) -> List[ExtractionRule]:
        """모든 규칙 조회"""
        return list(self.rules.values())

    def get_enabled_rules(self) -> List[ExtractionRule]:
        """활성화된 규칙만 조회"""
        return [r for r in self.rules.values() if r.enabled]

    def add_rule(self, rule: ExtractionRule) -> bool:
        """규칙 추가"""
        if rule.id in self.rules:
            logger.warning(f"Rule '{rule.id}' already exists")
            return False

        self.rules[rule.id] = rule
        self.save_rules()
        return True

    def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Optional[ExtractionRule]:
        """규칙 업데이트"""
        if rule_id not in self.rules:
            logger.warning(f"Rule '{rule_id}' not found")
            return None

        # ID는 변경 불가
        rule_data["id"] = rule_id

        updated_rule = ExtractionRule.from_dict(rule_data)
        self.rules[rule_id] = updated_rule
        self.save_rules()

        return updated_rule

    def delete_rule(self, rule_id: str) -> bool:
        """규칙 삭제"""
        if rule_id not in self.rules:
            return False

        del self.rules[rule_id]
        self.save_rules()
        return True

    def get_rules_by_category(self, category: str) -> List[ExtractionRule]:
        """카테고리별 규칙 조회"""
        return [r for r in self.rules.values() if r.category == category]
