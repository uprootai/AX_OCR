"""베어링 도메인 검증 규칙 — OD/ID/W 물리 제약 + 카탈로그 매칭

7가지 규칙:
1. od_gt_id       — OD > ID (물리 법칙)
2. value_range    — 치수는 0.1~3000mm 범위
3. w_ratio        — W는 OD의 5~80% 범위
4. od_id_ratio    — ID/OD 비율은 0.2~0.95
5. session_ref    — 세션명 기준값과 ±50% 이내
6. od_required    — OD가 최소 하나는 있어야 함
7. catalog_match  — ISO 355 카탈로그 매칭 (info)
"""

import re
import logging
from typing import List, Optional

from .engine import ValidationRule
from schemas.validation import ValidationVerdict, Severity

logger = logging.getLogger(__name__)

DOMAIN = "bearing"


def _parse_numeric(value) -> Optional[float]:
    """문자열/숫자 → float 변환"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r'[^\d.]', '', value)
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None
    return None


class OdGreaterThanId(ValidationRule):
    """OD > ID — 물리적으로 외경은 내경보다 커야 함"""

    rule_id = "bearing.od_gt_id"
    domain = DOMAIN
    description = "외경(OD)은 내경(ID)보다 커야 합니다"

    def evaluate(self, result: dict, context: dict) -> List[ValidationVerdict]:
        od = _parse_numeric(result.get("od"))
        id_ = _parse_numeric(result.get("id"))

        if od is None or id_ is None:
            return []

        if id_ >= od:
            return [ValidationVerdict(
                rule_id=self.rule_id,
                severity=Severity.ERROR,
                message=f"ID({id_}) >= OD({od}) — 물리적 불가능",
                field="id",
                actual_value=id_,
                expected_range=f"< {od}",
                correction_hint={"action": "swap", "fields": ["od", "id"]},
            )]
        return []


class ValueRange(ValidationRule):
    """치수 범위 — 0.1~3000mm"""

    rule_id = "bearing.value_range"
    domain = DOMAIN
    description = "치수는 0.1~3000mm 범위여야 합니다"

    MIN_VAL = 0.1
    MAX_VAL = 3000

    def evaluate(self, result: dict, context: dict) -> List[ValidationVerdict]:
        verdicts = []
        for field in ("od", "id", "width"):
            val = _parse_numeric(result.get(field))
            if val is None:
                continue
            if val < self.MIN_VAL or val > self.MAX_VAL:
                verdicts.append(ValidationVerdict(
                    rule_id=self.rule_id,
                    severity=Severity.ERROR,
                    message=f"{field}={val} — 범위 초과 ({self.MIN_VAL}~{self.MAX_VAL}mm)",
                    field=field,
                    actual_value=val,
                    expected_range=f"{self.MIN_VAL}~{self.MAX_VAL}",
                    correction_hint={"action": "nullify", "field": field},
                ))
        return verdicts


class WidthRatio(ValidationRule):
    """W/OD 비율 — W는 OD의 5~80%"""

    rule_id = "bearing.w_ratio"
    domain = DOMAIN
    description = "폭(W)은 외경(OD)의 5~80% 범위여야 합니다"

    def evaluate(self, result: dict, context: dict) -> List[ValidationVerdict]:
        od = _parse_numeric(result.get("od"))
        w = _parse_numeric(result.get("width"))

        if od is None or w is None or od == 0:
            return []

        ratio = w / od
        if ratio < 0.05 or ratio > 0.80:
            return [ValidationVerdict(
                rule_id=self.rule_id,
                severity=Severity.WARNING,
                message=f"W/OD 비율 {ratio:.2f} — 일반 범위(5~80%) 벗어남",
                field="width",
                actual_value=round(ratio, 3),
                expected_range="0.05~0.80",
            )]
        return []


class OdIdRatio(ValidationRule):
    """ID/OD 비율 — 0.2~0.95"""

    rule_id = "bearing.od_id_ratio"
    domain = DOMAIN
    description = "ID/OD 비율은 0.2~0.95 범위여야 합니다"

    def evaluate(self, result: dict, context: dict) -> List[ValidationVerdict]:
        od = _parse_numeric(result.get("od"))
        id_ = _parse_numeric(result.get("id"))

        if od is None or id_ is None or od == 0:
            return []

        ratio = id_ / od
        if ratio < 0.2 or ratio > 0.95:
            sev = Severity.ERROR if ratio > 1.0 else Severity.WARNING
            return [ValidationVerdict(
                rule_id=self.rule_id,
                severity=sev,
                message=f"ID/OD 비율 {ratio:.2f} — 범위(0.2~0.95) 벗어남",
                field="id",
                actual_value=round(ratio, 3),
                expected_range="0.2~0.95",
            )]
        return []


class SessionRefMatch(ValidationRule):
    """세션명 기준값 교차검증 — ±50% 이내"""

    rule_id = "bearing.session_ref"
    domain = DOMAIN
    description = "세션명 기준값과 ±50% 이내여야 합니다"

    def evaluate(self, result: dict, context: dict) -> List[ValidationVerdict]:
        session_name = context.get("session_name", "")
        if not session_name:
            return []

        from services.session_name_parser import parse_session_name_dimensions
        ref = parse_session_name_dimensions(session_name)

        verdicts = []
        for field, ref_key in [("od", "od"), ("id", "id")]:
            ref_val = ref.get(ref_key)
            actual = _parse_numeric(result.get(field))
            if ref_val is None or actual is None:
                continue
            if ref_val == 0:
                continue
            deviation = abs(actual - ref_val) / ref_val
            if deviation > 0.5:
                verdicts.append(ValidationVerdict(
                    rule_id=self.rule_id,
                    severity=Severity.WARNING,
                    message=(
                        f"{field}={actual} — 세션 기준({ref_val}) 대비 "
                        f"{deviation:.0%} 차이"
                    ),
                    field=field,
                    actual_value=actual,
                    expected_range=f"{ref_val * 0.5:.0f}~{ref_val * 1.5:.0f}",
                ))
        return verdicts


class OdRequired(ValidationRule):
    """OD 필수 — 치수가 있으면 OD도 있어야 함"""

    rule_id = "bearing.od_required"
    domain = DOMAIN
    description = "치수가 존재하면 OD가 분류되어야 합니다"

    def evaluate(self, result: dict, context: dict) -> List[ValidationVerdict]:
        dim_count = result.get("dimension_count", 0)
        od = result.get("od")

        if dim_count >= 3 and od is None:
            return [ValidationVerdict(
                rule_id=self.rule_id,
                severity=Severity.WARNING,
                message=f"치수 {dim_count}개 검출됐지만 OD 미분류",
                field="od",
            )]
        return []


class CatalogMatch(ValidationRule):
    """ISO 355 카탈로그 매칭 (info 레벨)"""

    rule_id = "bearing.catalog_match"
    domain = DOMAIN
    description = "ISO 355 / JIS B 1512 표준 베어링 치수와 매칭"

    def evaluate(self, result: dict, context: dict) -> List[ValidationVerdict]:
        od = _parse_numeric(result.get("od"))
        id_ = _parse_numeric(result.get("id"))

        if od is None or id_ is None:
            return []

        from services.opencv_classifier import _catalog_match_score
        score = _catalog_match_score(od, id_)

        if score > 0:
            return [ValidationVerdict(
                rule_id=self.rule_id,
                severity=Severity.INFO,
                message=f"OD={od}, ID={id_} — ISO 355 카탈로그 매칭됨",
                field="od",
            )]
        return []


def get_bearing_rules() -> List[ValidationRule]:
    """베어링 도메인 규칙 목록"""
    return [
        OdGreaterThanId(),
        ValueRange(),
        WidthRatio(),
        OdIdRatio(),
        SessionRefMatch(),
        OdRequired(),
        CatalogMatch(),
    ]
