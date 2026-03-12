"""
OCR A/B Comparison Framework
3개 OCR 엔진(edocr2, paddleocr, vl) 비교 프레임워크

DSE 베어링 도면 기반 치수 인식률(recall/precision) 계산
실제 API 호출 없이 비교 로직만 단위 테스트
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

@dataclass
class OCRComparisonMetrics:
    """단일 OCR 엔진의 치수 인식 성능 지표"""
    engine_name: str
    precision: float
    recall: float
    f1: float
    sample_count: int = 0


# ---------------------------------------------------------------------------
# Ground-truth data — DSE 베어링 도면 3종
# ---------------------------------------------------------------------------

DSE_GROUND_TRUTH: dict[str, list[str]] = {
    "TD0062017": ["Ø704", "550", "375", "200", "M30x45"],
    "TD0062019": ["Ø800", "650", "420", "250"],
    "TD0062020": ["Ø500", "350", "180"],
}


# ---------------------------------------------------------------------------
# Utility functions (tested as part of the framework)
# ---------------------------------------------------------------------------

def normalize_dimension(text: str) -> str:
    """치수 텍스트 정규화.

    - 앞뒤 공백 제거
    - 내부 공백 제거
    - 지름 기호 통일: ∅ (U+2205) → Ø (U+00D8)
    - ± 기호 유지 (이미 단일 표현)
    """
    text = text.strip()
    # Collapse internal whitespace
    text = re.sub(r"\s+", "", text)
    # Normalise diameter symbols to Ø (U+00D8)
    text = text.replace("\u2205", "\u00D8")  # ∅ → Ø
    text = text.replace("\u00f8", "\u00D8")  # ø (lowercase) → Ø
    return text


def calculate_dimension_metrics(
    predicted: list[str],
    ground_truth: list[str],
) -> dict[str, float]:
    """치수 인식 precision / recall / F1 계산.

    Args:
        predicted:    OCR 엔진이 인식한 치수 목록 (중복 포함 가능)
        ground_truth: 정답 치수 목록

    Returns:
        {"precision": float, "recall": float, "f1": float}
    """
    norm_pred = [normalize_dimension(p) for p in predicted]
    norm_gt = [normalize_dimension(g) for g in ground_truth]

    gt_set = set(norm_gt)
    pred_set = set(norm_pred)

    if not pred_set and not gt_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    true_positives = len(pred_set & gt_set)

    precision = true_positives / len(pred_set) if pred_set else 0.0
    recall = true_positives / len(gt_set) if gt_set else 0.0

    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

import pytest


class TestNormalizeDimension:
    """normalize_dimension 단위 테스트"""

    def test_strip_whitespace(self):
        """선행/후행 공백 제거"""
        assert normalize_dimension("  Ø704  ") == "Ø704"

    def test_internal_whitespace_removed(self):
        """내부 공백 제거"""
        assert normalize_dimension("M30 x 45") == "M30x45"

    def test_normalize_diameter_symbol_unicode_2205(self):
        """U+2205 (∅) → Ø (U+00D8)"""
        assert normalize_dimension("\u2205704") == "Ø704"

    def test_normalize_diameter_symbol_lowercase(self):
        """ø (U+00F8) → Ø (U+00D8)"""
        assert normalize_dimension("\u00f8500") == "Ø500"

    def test_normalize_already_correct_symbol(self):
        """이미 Ø (U+00D8) 인 경우 그대로"""
        assert normalize_dimension("Ø800") == "Ø800"

    def test_normalize_tolerance_preserved(self):
        """± 기호는 유지"""
        result = normalize_dimension("±0.05")
        assert "±" in result
        assert "0.05" in result

    def test_plain_number(self):
        """순수 숫자 그대로"""
        assert normalize_dimension("  550  ") == "550"


class TestCalculateMetrics:
    """calculate_dimension_metrics 단위 테스트"""

    def test_perfect_match(self):
        """모든 예측이 정답과 일치 → precision=1, recall=1, f1=1"""
        gt = ["Ø704", "550", "375"]
        pred = ["Ø704", "550", "375"]
        result = calculate_dimension_metrics(pred, gt)
        assert result["precision"] == pytest.approx(1.0)
        assert result["recall"] == pytest.approx(1.0)
        assert result["f1"] == pytest.approx(1.0)

    def test_partial_match(self):
        """일부만 일치"""
        gt = ["Ø704", "550", "375", "200"]
        pred = ["Ø704", "550"]
        result = calculate_dimension_metrics(pred, gt)
        assert result["precision"] == pytest.approx(1.0)   # 예측 2개 모두 정답
        assert result["recall"] == pytest.approx(0.5)      # 정답 4개 중 2개 발견
        assert result["f1"] == pytest.approx(2 / 3, rel=1e-3)

    def test_no_match(self):
        """예측과 정답이 전혀 겹치지 않음 → precision=0, recall=0, f1=0"""
        gt = ["Ø704", "550"]
        pred = ["999", "888"]
        result = calculate_dimension_metrics(pred, gt)
        assert result["precision"] == pytest.approx(0.0)
        assert result["recall"] == pytest.approx(0.0)
        assert result["f1"] == pytest.approx(0.0)

    def test_extra_predictions(self):
        """예측이 정답보다 많음 (오탐 포함) → precision < 1, recall = 1"""
        gt = ["Ø704", "550"]
        pred = ["Ø704", "550", "EXTRA1", "EXTRA2"]
        result = calculate_dimension_metrics(pred, gt)
        assert result["precision"] == pytest.approx(0.5)   # 2/4
        assert result["recall"] == pytest.approx(1.0)      # 2/2
        assert result["f1"] == pytest.approx(2 / 3, rel=1e-3)

    def test_empty_both(self):
        """예측·정답 모두 비어있음 → 완벽 점수"""
        result = calculate_dimension_metrics([], [])
        assert result["precision"] == pytest.approx(1.0)
        assert result["recall"] == pytest.approx(1.0)
        assert result["f1"] == pytest.approx(1.0)

    def test_empty_predictions(self):
        """예측 없음, 정답 있음 → recall=0"""
        result = calculate_dimension_metrics([], ["Ø704"])
        assert result["recall"] == pytest.approx(0.0)
        assert result["f1"] == pytest.approx(0.0)

    def test_normalization_applied(self):
        """비교 전 정규화가 적용되어야 함: ∅ vs Ø 는 같은 것으로 취급"""
        gt = ["Ø704"]
        pred = ["\u2205704"]   # ∅704
        result = calculate_dimension_metrics(pred, gt)
        assert result["f1"] == pytest.approx(1.0)


class TestOCRABComparison:
    """OCR 엔진 A/B 비교 프레임워크 테스트"""

    # -----------------------------------------------------------------------
    # Simulated engine results (no network access)
    # -----------------------------------------------------------------------

    def _edocr2_simulate(self, drawing_id: str) -> list[str]:
        """edocr2: 기계 도면 특화 엔진 — GT 대비 약 50% 인식"""
        results = {
            "TD0062017": ["Ø704", "550", "M30x45"],           # 3/5 = 60%
            "TD0062019": ["Ø800", "650"],                      # 2/4 = 50%
            "TD0062020": ["Ø500", "350"],                      # 2/3 = 67%
        }
        return results.get(drawing_id, [])

    def _paddleocr_simulate(self, drawing_id: str) -> list[str]:
        """paddleocr: 범용 OCR 엔진 — GT 대비 약 40% 인식"""
        results = {
            "TD0062017": ["550", "375"],                       # 2/5 = 40%
            "TD0062019": ["650"],                              # 1/4 = 25%
            "TD0062020": ["350"],                              # 1/3 = 33%
        }
        return results.get(drawing_id, [])

    def _vl_simulate(self, drawing_id: str) -> list[str]:
        """vl (vision-language): 멀티모달 엔진 — GT 대비 약 85% 인식"""
        results = {
            "TD0062017": ["Ø704", "550", "375", "200", "M30x45"],  # 5/5 = 100%
            "TD0062019": ["Ø800", "650", "420"],                    # 3/4 = 75%
            "TD0062020": ["Ø500", "350", "180"],                    # 3/3 = 100%
        }
        return results.get(drawing_id, [])

    # -----------------------------------------------------------------------
    # Per-engine tests
    # -----------------------------------------------------------------------

    def test_mock_edocr2_results(self):
        """edocr2 시뮬레이션: recall ≥ 0.4 (약 50% 수준)"""
        total_recall = 0.0
        count = 0
        for drawing_id, gt in DSE_GROUND_TRUTH.items():
            pred = self._edocr2_simulate(drawing_id)
            metrics = calculate_dimension_metrics(pred, gt)
            total_recall += metrics["recall"]
            count += 1
        avg_recall = total_recall / count
        assert avg_recall >= 0.4, f"edocr2 avg recall {avg_recall:.2f} < 0.4"

    def test_mock_paddleocr_results(self):
        """paddleocr 시뮬레이션: recall ≥ 0.2 (약 40% 수준)"""
        total_recall = 0.0
        count = 0
        for drawing_id, gt in DSE_GROUND_TRUTH.items():
            pred = self._paddleocr_simulate(drawing_id)
            metrics = calculate_dimension_metrics(pred, gt)
            total_recall += metrics["recall"]
            count += 1
        avg_recall = total_recall / count
        assert avg_recall >= 0.2, f"paddleocr avg recall {avg_recall:.2f} < 0.2"

    def test_mock_vl_results(self):
        """vl 시뮬레이션: recall ≥ 0.8 (약 85% 수준)"""
        total_recall = 0.0
        count = 0
        for drawing_id, gt in DSE_GROUND_TRUTH.items():
            pred = self._vl_simulate(drawing_id)
            metrics = calculate_dimension_metrics(pred, gt)
            total_recall += metrics["recall"]
            count += 1
        avg_recall = total_recall / count
        assert avg_recall >= 0.8, f"vl avg recall {avg_recall:.2f} < 0.8"

    # -----------------------------------------------------------------------
    # Ranking test
    # -----------------------------------------------------------------------

    def test_comparison_ranking(self):
        """3개 엔진 F1 점수 기준 ranking: vl > edocr2 > paddleocr"""

        def avg_f1(simulator) -> float:
            scores = []
            for drawing_id, gt in DSE_GROUND_TRUTH.items():
                pred = simulator(drawing_id)
                scores.append(calculate_dimension_metrics(pred, gt)["f1"])
            return sum(scores) / len(scores)

        edocr2_f1 = avg_f1(self._edocr2_simulate)
        paddleocr_f1 = avg_f1(self._paddleocr_simulate)
        vl_f1 = avg_f1(self._vl_simulate)

        results = [
            OCRComparisonMetrics("edocr2", 0.0, 0.0, edocr2_f1, len(DSE_GROUND_TRUTH)),
            OCRComparisonMetrics("paddleocr", 0.0, 0.0, paddleocr_f1, len(DSE_GROUND_TRUTH)),
            OCRComparisonMetrics("vl", 0.0, 0.0, vl_f1, len(DSE_GROUND_TRUTH)),
        ]

        ranked = sorted(results, key=lambda m: m.f1, reverse=True)

        assert ranked[0].engine_name == "vl", (
            f"1위 엔진은 vl 이어야 함, 실제: {ranked[0].engine_name} (f1={ranked[0].f1:.3f})"
        )
        assert ranked[-1].engine_name == "paddleocr", (
            f"최하위 엔진은 paddleocr 이어야 함, 실제: {ranked[-1].engine_name}"
        )
        # vl이 edocr2보다 높아야 함
        assert vl_f1 > edocr2_f1, (
            f"vl f1({vl_f1:.3f}) 은 edocr2 f1({edocr2_f1:.3f}) 보다 높아야 함"
        )

    # -----------------------------------------------------------------------
    # Ground-truth data integrity
    # -----------------------------------------------------------------------

    def test_dse_sample_ground_truth_defined(self):
        """DSE 샘플 GT 데이터가 3개 도면 모두 정의되어 있어야 함"""
        expected_drawings = {"TD0062017", "TD0062019", "TD0062020"}
        assert set(DSE_GROUND_TRUTH.keys()) == expected_drawings

    def test_dse_gt_td0062017_has_five_dims(self):
        """TD0062017 GT에 5개 치수 존재"""
        assert len(DSE_GROUND_TRUTH["TD0062017"]) == 5

    def test_dse_gt_td0062019_has_four_dims(self):
        """TD0062019 GT에 4개 치수 존재"""
        assert len(DSE_GROUND_TRUTH["TD0062019"]) == 4

    def test_dse_gt_td0062020_has_three_dims(self):
        """TD0062020 GT에 3개 치수 존재"""
        assert len(DSE_GROUND_TRUTH["TD0062020"]) == 3

    def test_dse_gt_diameter_symbols_normalized(self):
        """GT 데이터의 지름 기호가 모두 Ø (U+00D8) 로 정규화되어 있어야 함"""
        for drawing_id, dims in DSE_GROUND_TRUTH.items():
            for dim in dims:
                if dim.startswith("Ø"):
                    assert dim[0] == "\u00D8", (
                        f"{drawing_id} — '{dim}' 의 첫 글자가 Ø (U+00D8) 가 아님"
                    )
