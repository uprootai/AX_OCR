"""ValidationEngine — 도메인 독립적 검증 엔진

레지스트리 패턴: 도메인별 규칙을 등록하고, 결과에 대해 일괄 평가.
베어링 OD/ID/W는 하나의 도메인이며, 향후 P&ID·GD&T 등 추가 가능.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from schemas.validation import (
    ValidationVerdict, ValidationReport, Severity,
)

logger = logging.getLogger(__name__)


class ValidationRule(ABC):
    """검증 규칙 기본 클래스"""

    rule_id: str = ""
    domain: str = ""
    description: str = ""

    @abstractmethod
    def evaluate(
        self, result: dict, context: dict
    ) -> List[ValidationVerdict]:
        """결과를 평가하여 0개 이상의 Verdict 반환"""
        ...


class ValidationEngine:
    """도메인별 규칙을 관리하고 결과를 검증하는 엔진"""

    def __init__(self):
        self._rules: Dict[str, List[ValidationRule]] = {}

    def register(self, rule: ValidationRule):
        domain = rule.domain
        if domain not in self._rules:
            self._rules[domain] = []
        self._rules[domain].append(rule)
        logger.debug(f"규칙 등록: {rule.rule_id} (도메인: {domain})")

    def register_many(self, rules: List[ValidationRule]):
        for rule in rules:
            self.register(rule)

    def validate(
        self,
        result: dict,
        context: dict,
        domain: Optional[str] = None,
    ) -> ValidationReport:
        """결과를 검증하여 리포트 생성

        domain이 None이면 등록된 모든 도메인의 규칙 적용.
        """
        report = ValidationReport()

        domains = [domain] if domain else list(self._rules.keys())

        for d in domains:
            rules = self._rules.get(d, [])
            for rule in rules:
                try:
                    verdicts = rule.evaluate(result, context)
                    for v in verdicts:
                        report.add_verdict(v)
                except Exception as e:
                    logger.warning(f"규칙 {rule.rule_id} 평가 실패: {e}")

        return report

    def get_rules(self, domain: str) -> List[ValidationRule]:
        return self._rules.get(domain, [])

    @property
    def domains(self) -> List[str]:
        return list(self._rules.keys())


# 싱글턴 엔진 + 기본 규칙 자동 등록
_engine: Optional[ValidationEngine] = None


def get_engine() -> ValidationEngine:
    """글로벌 ValidationEngine 인스턴스 (lazy init + 기본 규칙 등록)"""
    global _engine
    if _engine is None:
        _engine = ValidationEngine()
        _register_default_rules(_engine)
    return _engine


def _register_default_rules(engine: ValidationEngine):
    """기본 도메인 규칙 등록"""
    try:
        from .rules_bearing import get_bearing_rules
        engine.register_many(get_bearing_rules())
        logger.info(f"베어링 검증 규칙 {len(get_bearing_rules())}개 등록")
    except ImportError:
        logger.warning("베어링 검증 규칙 모듈 로드 실패")
