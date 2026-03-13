"""
Dimension Parser — 정규식 패턴 정의
DIMENSION_PATTERNS, GDT_PATTERNS 상수
"""
from typing import List, Tuple, Callable


# 치수 패턴 정의 (순서 중요 - 더 구체적인 패턴 먼저)
DIMENSION_PATTERNS: List[Tuple[str, str, Callable]] = [
    # OD670×ID440 (외경×내경)
    (
        r"OD\s*(\d+\.?\d*)\s*[×xX]\s*ID\s*(\d+\.?\d*)",
        "bearing_od_id",
        lambda m: {
            "outer_diameter": float(m.group(1)),
            "inner_diameter": float(m.group(2)),
            "dimension_type": "bearing"
        }
    ),
    # ID440×OD670 (내경×외경)
    (
        r"ID\s*(\d+\.?\d*)\s*[×xX]\s*OD\s*(\d+\.?\d*)",
        "bearing_id_od",
        lambda m: {
            "inner_diameter": float(m.group(1)),
            "outer_diameter": float(m.group(2)),
            "dimension_type": "bearing"
        }
    ),
    # 1100×ID680×200L (폭×내경×길이)
    (
        r"(\d+\.?\d*)\s*[×xX]\s*ID\s*(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)\s*L",
        "bearing_w_id_l",
        lambda m: {
            "width": float(m.group(1)),
            "inner_diameter": float(m.group(2)),
            "length": float(m.group(3)),
            "dimension_type": "bearing"
        }
    ),
    # OD670×200L (외경×길이)
    (
        r"OD\s*(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)\s*L",
        "bearing_od_l",
        lambda m: {
            "outer_diameter": float(m.group(1)),
            "length": float(m.group(2)),
            "dimension_type": "bearing"
        }
    ),
    # ========== 복합 치수 패턴 ==========
    # Φ50±0.05 (직경 + 대칭 공차)
    (
        r"[ØφΦ⌀]\s*(\d+\.?\d*)\s*[±]\s*(\d+\.?\d*)",
        "diameter_symmetric_tolerance",
        lambda m: {
            "diameter": float(m.group(1)),
            "value": float(m.group(1)),
            "tolerance": f"±{m.group(2)}",
            "tolerance_upper": float(m.group(2)),
            "tolerance_lower": -float(m.group(2)),
            "dimension_type": "diameter"
        }
    ),
    # Φ50+0.05/-0.02 (직경 + 비대칭 공차)
    (
        r"[ØφΦ⌀]\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)",
        "diameter_asymmetric_tolerance",
        lambda m: {
            "diameter": float(m.group(1)),
            "value": float(m.group(1)),
            "tolerance": f"+{m.group(2)}/-{m.group(3)}",
            "tolerance_upper": float(m.group(2)),
            "tolerance_lower": -float(m.group(3)),
            "dimension_type": "diameter"
        }
    ),
    # Φ50-0.02+0.05 (직경 + 역순 비대칭 공차)
    (
        r"[ØφΦ⌀]\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)",
        "diameter_asymmetric_reverse",
        lambda m: {
            "diameter": float(m.group(1)),
            "value": float(m.group(1)),
            "tolerance": f"+{m.group(3)}/-{m.group(2)}",
            "tolerance_upper": float(m.group(3)),
            "tolerance_lower": -float(m.group(2)),
            "dimension_type": "diameter"
        }
    ),
    # Ø25H7 또는 ⌀25H7 (직경 + 공차등급)
    (
        r"[ØφΦ⌀]\s*(\d+\.?\d*)\s*([A-Z][a-z]?\d+)?",
        "diameter_tolerance",
        lambda m: {
            "diameter": float(m.group(1)),
            "tolerance": m.group(2) if m.group(2) else None,
            "fit_class": m.group(2) if m.group(2) else None,
            "dimension_type": "diameter"
        }
    ),
    # 50.0±0.1 (대칭 공차)
    (
        r"(\d+\.?\d*)\s*[±]\s*(\d+\.?\d*)",
        "symmetric_tolerance",
        lambda m: {
            "value": float(m.group(1)),
            "tolerance": f"±{m.group(2)}",
            "tolerance_upper": float(m.group(2)),
            "tolerance_lower": -float(m.group(2)),
            "dimension_type": "linear"
        }
    ),
    # 50.0 +0.1/-0.05 (비대칭 공차 - 슬래시 구분)
    (
        r"(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)",
        "asymmetric_tolerance",
        lambda m: {
            "value": float(m.group(1)),
            "tolerance": f"+{m.group(2)}/-{m.group(3)}",
            "tolerance_upper": float(m.group(2)),
            "tolerance_lower": -float(m.group(3)),
            "dimension_type": "linear"
        }
    ),
    # 50.0-0.02+0.05 (역순 비대칭 공차)
    (
        r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)",
        "asymmetric_reverse",
        lambda m: {
            "value": float(m.group(1)),
            "tolerance": f"+{m.group(3)}/-{m.group(2)}",
            "tolerance_upper": float(m.group(3)),
            "tolerance_lower": -float(m.group(2)),
            "dimension_type": "linear"
        }
    ),
    # 50 +0.05/0 (단방향 공차 - 위만)
    (
        r"(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*0(?!\d)",
        "unilateral_upper",
        lambda m: {
            "value": float(m.group(1)),
            "tolerance": f"+{m.group(2)}/0",
            "tolerance_upper": float(m.group(2)),
            "tolerance_lower": 0.0,
            "dimension_type": "linear"
        }
    ),
    # 50 0/-0.05 (단방향 공차 - 아래만)
    (
        r"(\d+\.?\d*)\s*0\s*/\s*-\s*(\d+\.?\d*)",
        "unilateral_lower",
        lambda m: {
            "value": float(m.group(1)),
            "tolerance": f"0/-{m.group(2)}",
            "tolerance_upper": 0.0,
            "tolerance_lower": -float(m.group(2)),
            "dimension_type": "linear"
        }
    ),
    # ========== 신규 패턴 ==========
    # M10×1.5 (나사 치수)
    (
        r"M\s*(\d+\.?\d*)(?:\s*[×xX]\s*(\d+\.?\d*))?",
        "thread",
        lambda m: {
            "value": float(m.group(1)),
            "thread_pitch": float(m.group(2)) if m.group(2) else None,
            "dimension_type": "thread"
        }
    ),
    # 45° (각도)
    (
        r"(\d+\.?\d*)\s*°",
        "angle",
        lambda m: {
            "value": float(m.group(1)),
            "unit": "degree",
            "dimension_type": "angle"
        }
    ),
    # Ra 3.2, Ra3.2 (표면 거칠기)
    (
        r"Ra\s*(\d+\.?\d*)",
        "surface_roughness",
        lambda m: {
            "value": float(m.group(1)),
            "unit": "um",
            "dimension_type": "surface_roughness"
        }
    ),
    # H7, h6, g6 등 (공차 등급만)
    (
        r"\b([A-Z][a-z]?)(\d+)\b",
        "fit_class",
        lambda m: {
            "fit_class": f"{m.group(1)}{m.group(2)}",
            "tolerance": f"{m.group(1)}{m.group(2)}",
            "dimension_type": "fit"
        }
    ),
    # 360×190 (일반 치수)
    (
        r"(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)",
        "general_dimension",
        lambda m: {
            "width": float(m.group(1)),
            "height": float(m.group(2)),
            "dimension_type": "general"
        }
    ),
    # R25 (반지름)
    (
        r"R\s*(\d+\.?\d*)",
        "radius",
        lambda m: {
            "value": float(m.group(1)),
            "dimension_type": "radius"
        }
    ),
    # C2 또는 C2×45° (챔퍼)
    (
        r"C\s*(\d+\.?\d*)(?:\s*[×xX]\s*(\d+\.?\d*)\s*°)?",
        "chamfer",
        lambda m: {
            "value": float(m.group(1)),
            "dimension_type": "chamfer"
        }
    ),
]

# GD&T 기호 패턴
GDT_PATTERNS = [
    (r"[⌀ØφΦ]", "diameter", "직경"),
    (r"⊥", "perpendicularity", "직각도"),
    (r"//", "parallelism", "평행도"),
    (r"○", "circularity", "진원도"),
    (r"⌭", "cylindricity", "원통도"),
    (r"—", "flatness", "평면도"),
    (r"∠", "angularity", "경사도"),
    (r"↗", "position", "위치도"),
    (r"⊙", "concentricity", "동심도"),
    (r"⌓", "symmetry", "대칭도"),
    (r"↺", "runout", "흔들림"),
    (r"⌰", "total_runout", "총 흔들림"),
]
