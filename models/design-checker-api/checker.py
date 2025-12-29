"""
Design Checker - P&ID 설계 검증기
설계 규칙 검사 로직 구현
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional

from schemas import (
    RuleViolation, ViolationLocation, CheckSummary, DesignCheckResult
)
from constants import DESIGN_RULES, RuleCategory
from bwms_rules import bwms_checker

logger = logging.getLogger(__name__)


class DesignChecker:
    """P&ID 설계 검증기"""

    def __init__(self):
        self.rules = DESIGN_RULES

    def check_connectivity(
        self,
        symbols: List[Dict],
        connections: List[Dict]
    ) -> List[RuleViolation]:
        """연결 관련 규칙 검사"""
        violations = []

        # 연결된 심볼 ID 집합 (문자열로 통일)
        connected_symbols = set()
        for conn in connections:
            connected_symbols.add(str(conn.get("source_id", "")))
            connected_symbols.add(str(conn.get("target_id", "")))

        # CONN-002: 미연결 심볼 검출
        for symbol in symbols:
            symbol_id = str(symbol.get("id", ""))
            if symbol_id not in connected_symbols:
                rule = self.rules["CONN-002"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=rule["description"],
                    location=ViolationLocation(
                        x=symbol.get("x", 0),
                        y=symbol.get("y", 0),
                        width=symbol.get("width"),
                        height=symbol.get("height")
                    ),
                    affected_elements=[symbol_id],
                    suggestion=f"심볼 '{symbol.get('label', symbol_id)}'을 배관 라인에 연결하세요."
                ))

        # CONN-003: 중복 연결 검출
        connection_pairs = {}
        for conn in connections:
            pair = tuple(sorted([str(conn.get("source_id", "")), str(conn.get("target_id", ""))]))
            if pair in connection_pairs:
                rule = self.rules["CONN-003"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=rule["description"],
                    affected_elements=list(pair),
                    suggestion="중복된 연결 중 하나를 제거하세요."
                ))
            connection_pairs[pair] = conn

        return violations

    def check_labeling(
        self,
        symbols: List[Dict]
    ) -> List[RuleViolation]:
        """라벨링 관련 규칙 검사"""
        violations = []

        # 태그 번호 수집 (중복 검사용)
        tag_numbers = {}

        # 태그 필요 심볼 타입
        requires_tag = {"valve", "pump", "instrument", "transmitter", "controller", "indicator"}

        for symbol in symbols:
            symbol_id = str(symbol.get("id", ""))
            symbol_type = str(symbol.get("type", "")).lower()
            tag = symbol.get("tag_number", "")

            # LBL-001: 태그번호 누락
            if symbol_type in requires_tag and not tag:
                rule = self.rules["LBL-001"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=rule["description"],
                    location=ViolationLocation(
                        x=symbol.get("x", 0),
                        y=symbol.get("y", 0)
                    ),
                    affected_elements=[symbol_id],
                    suggestion=f"{symbol_type} 심볼에 태그번호를 추가하세요."
                ))

            # 태그 번호 중복 체크용 수집
            if tag:
                if tag in tag_numbers:
                    tag_numbers[tag].append(symbol_id)
                else:
                    tag_numbers[tag] = [symbol_id]

        # LBL-002: 중복 태그번호
        for tag, symbol_ids in tag_numbers.items():
            if len(symbol_ids) > 1:
                rule = self.rules["LBL-002"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=f"태그번호 '{tag}'가 {len(symbol_ids)}개 심볼에서 중복 사용됨",
                    affected_elements=symbol_ids,
                    suggestion="각 심볼에 고유한 태그번호를 부여하세요."
                ))

        return violations

    def check_symbols(
        self,
        symbols: List[Dict]
    ) -> List[RuleViolation]:
        """심볼 관련 규칙 검사"""
        violations = []

        # SYM-002: 심볼 중첩 검출
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                if self._check_overlap(sym1, sym2):
                    rule = self.rules["SYM-002"]
                    violations.append(RuleViolation(
                        rule_id=rule["id"],
                        rule_name=rule["name"],
                        rule_name_en=rule["name_en"],
                        category=rule["category"].value,
                        severity=rule["severity"].value,
                        standard=rule["standard"],
                        description=rule["description"],
                        location=ViolationLocation(
                            x=sym1.get("x", 0),
                            y=sym1.get("y", 0),
                            elements=[str(sym1.get("id", "")), str(sym2.get("id", ""))]
                        ),
                        affected_elements=[str(sym1.get("id", "")), str(sym2.get("id", ""))],
                        suggestion="중첩된 심볼을 분리하세요."
                    ))

        return violations

    def check_safety(
        self,
        symbols: List[Dict],
        connections: List[Dict]
    ) -> List[RuleViolation]:
        """안전 관련 규칙 검사"""
        violations = []

        # 심볼 타입별 분류
        pressure_vessels = [s for s in symbols if str(s.get("type", "")) in ["tank", "vessel", "drum", "column"]]
        safety_valves = [s for s in symbols if "safety" in str(s.get("type", "")).lower() or "psv" in str(s.get("tag_number", "")).upper()]
        control_valves = [s for s in symbols if str(s.get("type", "")) in ["control_valve", "globe_valve"] or "cv" in str(s.get("tag_number", "")).lower()]

        # 연결 그래프 구축 (문자열 ID 사용)
        connection_graph = {}
        for conn in connections:
            src = str(conn.get("source_id", ""))
            tgt = str(conn.get("target_id", ""))
            if src not in connection_graph:
                connection_graph[src] = []
            connection_graph[src].append(tgt)

        # SAF-001: 압력용기에 안전밸브 확인
        safety_valve_ids = {str(s.get("id", "")) for s in safety_valves}
        for vessel in pressure_vessels:
            vessel_id = str(vessel.get("id", ""))
            # 연결된 심볼 중 안전밸브가 있는지 확인
            connected_ids = connection_graph.get(vessel_id, [])
            has_safety_valve = any(cid in safety_valve_ids for cid in connected_ids)

            if not has_safety_valve:
                rule = self.rules["SAF-001"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=rule["description"],
                    location=ViolationLocation(
                        x=vessel.get("x", 0),
                        y=vessel.get("y", 0)
                    ),
                    affected_elements=[vessel_id],
                    suggestion=f"압력용기 '{vessel.get('label', vessel_id)}'에 안전밸브(PSV)를 추가하세요."
                ))

        # SAF-003: 제어밸브 바이패스 확인 (Info 레벨)
        for cv in control_valves:
            cv_id = str(cv.get("id", ""))
            # 간단한 바이패스 검사 (실제로는 더 복잡한 그래프 분석 필요)
            connected_count = len(connection_graph.get(cv_id, []))
            if connected_count < 3:  # 바이패스가 있으면 최소 3개 연결
                rule = self.rules["SAF-003"]
                violations.append(RuleViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    category=rule["category"].value,
                    severity=rule["severity"].value,
                    standard=rule["standard"],
                    description=rule["description"],
                    location=ViolationLocation(
                        x=cv.get("x", 0),
                        y=cv.get("y", 0)
                    ),
                    affected_elements=[cv_id],
                    suggestion="유지보수를 위해 바이패스 라인 추가를 권장합니다."
                ))

        return violations

    def _check_overlap(self, sym1: Dict, sym2: Dict) -> bool:
        """두 심볼의 중첩 여부 확인"""
        x1, y1 = sym1.get("x", 0), sym1.get("y", 0)
        w1, h1 = sym1.get("width", 50), sym1.get("height", 50)
        x2, y2 = sym2.get("x", 0), sym2.get("y", 0)
        w2, h2 = sym2.get("width", 50), sym2.get("height", 50)

        # AABB 충돌 검사
        return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

    def check_bwms(
        self,
        symbols: List[Dict],
        connections: List[Dict],
        lines: Optional[List[Dict]] = None,
        texts: Optional[List[Dict]] = None,
        enabled_rules: Optional[List[str]] = None
    ) -> List[RuleViolation]:
        """BWMS 전용 규칙 검사"""
        violations = []

        try:
            bwms_violations, summary = bwms_checker.run_all_checks(
                symbols=symbols,
                connections=connections,
                lines=lines,
                texts=texts,
                enabled_rules=enabled_rules
            )

            # BWMSViolation을 RuleViolation으로 변환
            for bv in bwms_violations:
                violations.append(RuleViolation(
                    rule_id=bv.rule_id,
                    rule_name=bv.rule_name,
                    rule_name_en=bv.rule_name_en,
                    category=RuleCategory.BWMS.value,
                    severity=bv.severity,
                    standard=bv.standard,
                    description=bv.description,
                    location=ViolationLocation(**bv.location) if bv.location else None,
                    affected_elements=bv.affected_elements,
                    suggestion=bv.suggestion
                ))

            logger.info(f"BWMS check: {summary.get('equipment_found', 0)} equipment, {len(violations)} violations")

        except Exception as e:
            logger.error(f"BWMS check error: {e}")

        return violations

    def run_all_checks(
        self,
        symbols: List[Dict],
        connections: List[Dict],
        lines: Optional[List[Dict]] = None,
        texts: Optional[List[Dict]] = None,
        include_bwms: bool = True
    ) -> DesignCheckResult:
        """모든 설계 규칙 검사 실행"""
        all_violations = []

        # 각 카테고리별 검사 실행
        all_violations.extend(self.check_connectivity(symbols, connections))
        all_violations.extend(self.check_labeling(symbols))
        all_violations.extend(self.check_symbols(symbols))
        all_violations.extend(self.check_safety(symbols, connections))

        # BWMS 규칙 검사 (선택적)
        if include_bwms:
            all_violations.extend(self.check_bwms(symbols, connections, lines, texts))

        # 요약 생성
        errors = sum(1 for v in all_violations if v.severity == "error")
        warnings = sum(1 for v in all_violations if v.severity == "warning")
        info_count = sum(1 for v in all_violations if v.severity == "info")

        by_category = {}
        for v in all_violations:
            cat = v.category
            by_category[cat] = by_category.get(cat, 0) + 1

        # 준수율 계산 (오류 가중치 높게)
        total_weight = len(symbols) * 10 if symbols else 10
        violation_weight = errors * 3 + warnings * 1 + info_count * 0.2
        compliance_score = max(0, min(100, 100 - (violation_weight / total_weight * 100)))

        summary = CheckSummary(
            total_violations=len(all_violations),
            errors=errors,
            warnings=warnings,
            info=info_count,
            by_category=by_category,
            compliance_score=round(compliance_score, 1)
        )

        return DesignCheckResult(
            violations=all_violations,
            summary=summary,
            rules_checked=len(self.rules),
            checked_at=datetime.now().isoformat()
        )


# Global checker instance
design_checker = DesignChecker()
