"""자기수정 루프 — 검증 실패 시 자동 보정 시도

CorrectionStrategy 패턴:
1. swap    — ID > OD 이면 교환
2. nullify — 범위 초과 값 제거
3. fallback_od — OD 미분류 시 최대값 배정

validate_and_correct()가 진입점:
  검증 → (실패 시) 보정 → 재검증 → ... (최대 3회)
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any

from schemas.validation import (
    ValidationReport, ValidationVerdict, CorrectionRecord,
    Severity, QualityGrade,
)
from .engine import get_engine

logger = logging.getLogger(__name__)

MAX_CORRECTION_ITERATIONS = 3


class CorrectionStrategy(ABC):
    """자동 보정 전략 기본 클래스"""

    name: str = ""

    @abstractmethod
    def can_handle(self, verdict: ValidationVerdict) -> bool:
        """이 전략이 해당 verdict를 처리할 수 있는지"""
        ...

    @abstractmethod
    def correct(
        self, result: dict, verdict: ValidationVerdict, context: dict
    ) -> Optional[dict]:
        """보정 적용 — 새 result dict 반환, 실패 시 None"""
        ...


class SwapOdId(CorrectionStrategy):
    """ID > OD 일 때 둘을 교환"""

    name = "swap_od_id"

    def can_handle(self, verdict: ValidationVerdict) -> bool:
        hint = verdict.correction_hint or {}
        return hint.get("action") == "swap"

    def correct(
        self, result: dict, verdict: ValidationVerdict, context: dict
    ) -> Optional[dict]:
        od, id_ = result.get("od"), result.get("id")
        if od is None or id_ is None:
            return None
        new_result = dict(result)
        new_result["od"] = id_
        new_result["id"] = od
        logger.info(f"자동 보정: OD↔ID 교환 ({od} ↔ {id_})")
        return new_result


class NullifyOutOfRange(CorrectionStrategy):
    """범위 초과 값을 None으로 제거"""

    name = "nullify_out_of_range"

    def can_handle(self, verdict: ValidationVerdict) -> bool:
        hint = verdict.correction_hint or {}
        return hint.get("action") == "nullify"

    def correct(
        self, result: dict, verdict: ValidationVerdict, context: dict
    ) -> Optional[dict]:
        field = (verdict.correction_hint or {}).get("field") or verdict.field
        if not field:
            return None
        new_result = dict(result)
        old_val = new_result.get(field)
        new_result[field] = None
        logger.info(f"자동 보정: {field}={old_val} → None (범위 초과)")
        return new_result


class FallbackOdFromMax(CorrectionStrategy):
    """OD 미분류 시 가장 큰 치수를 OD로 배정"""

    name = "fallback_od_from_max"

    def can_handle(self, verdict: ValidationVerdict) -> bool:
        return verdict.rule_id == "bearing.od_required"

    def correct(
        self, result: dict, verdict: ValidationVerdict, context: dict
    ) -> Optional[dict]:
        dims = result.get("dimensions", [])
        if not dims:
            return None

        best_val = 0
        best_dim = None
        for d in dims:
            val = _parse_dim_value(d)
            if val and val > best_val:
                best_val = val
                best_dim = d

        if best_dim is None or best_val <= 0:
            return None

        new_result = dict(result)
        new_result["od"] = str(best_val)
        logger.info(f"자동 보정: 최대치수 {best_val}을 OD로 배정")
        return new_result


def _parse_dim_value(dim: dict) -> Optional[float]:
    """치수 dict에서 숫자값 추출"""
    val_str = dim.get("value", "")
    if not val_str:
        return None
    cleaned = re.sub(r'[^\d.]', '', str(val_str))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


# 기본 보정 전략 목록
DEFAULT_STRATEGIES: List[CorrectionStrategy] = [
    SwapOdId(),
    NullifyOutOfRange(),
    FallbackOdFromMax(),
]


def validate_and_correct(
    result: dict,
    context: dict,
    domain: str = "bearing",
    strategies: Optional[List[CorrectionStrategy]] = None,
    max_iterations: int = MAX_CORRECTION_ITERATIONS,
) -> Tuple[dict, ValidationReport]:
    """검증 + 자기수정 루프

    1. 검증 실행
    2. error가 있으면 보정 시도
    3. 재검증 (최대 max_iterations 회)
    4. 최종 결과 + 누적 리포트 반환

    Returns:
        (보정된 result, 최종 ValidationReport)
    """
    engine = get_engine()
    strats = strategies or DEFAULT_STRATEGIES

    cumulative_corrections: List[CorrectionRecord] = []
    current = dict(result)

    for iteration in range(1, max_iterations + 1):
        report = engine.validate(current, context, domain=domain)

        if report.error_count == 0:
            # 이전 보정 이력 포함
            report.corrections = cumulative_corrections
            report.iteration_count = iteration
            return current, report

        # error verdict에 대해 보정 시도
        corrected_this_round = False
        for verdict in report.verdicts:
            if verdict.severity != Severity.ERROR:
                continue

            for strat in strats:
                if not strat.can_handle(verdict):
                    continue

                before_snapshot = {
                    k: current.get(k) for k in ("od", "id", "width")
                }
                new_result = strat.correct(current, verdict, context)

                if new_result is not None:
                    after_snapshot = {
                        k: new_result.get(k) for k in ("od", "id", "width")
                    }
                    cumulative_corrections.append(CorrectionRecord(
                        rule_id=verdict.rule_id,
                        strategy=strat.name,
                        before=before_snapshot,
                        after=after_snapshot,
                    ))
                    current = new_result
                    corrected_this_round = True
                    break  # 다음 verdict로

        if not corrected_this_round:
            # 보정할 수 없는 에러 → 루프 종료
            break

    # 최종 검증
    final_report = engine.validate(current, context, domain=domain)
    final_report.corrections = cumulative_corrections
    final_report.iteration_count = max_iterations

    return current, final_report
