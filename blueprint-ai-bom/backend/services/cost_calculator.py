"""Cost Calculator - 원가 계산 엔진 (배럴 모듈)

Phase 4: 치수 → +여유치 → 중량 → x단가 → +가공비 → 소계
Phase 5: 표준부품 카탈로그 가격 산출 (볼트/너트/와셔/핀/플러그)

Sub-modules:
  - material_calculator: 재료비 계산, 재질 정보 조회
  - machining_calculator: 가공비, 난이도 계수, 열처리/표면처리
  - weight_calculator: 중량 추정, 치수 추출
"""

import json
import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

from schemas.pricing_config import PricingConfig

# ── Sub-module re-exports (기존 import 경로 유지) ───────────────
from services.material_calculator import (  # noqa: F401
    apply_allowance,
    calculate_material_cost,
    _get_material_info,
    _calc_quantity_discount,
)
from services.machining_calculator import (  # noqa: F401
    _detect_part_type,
    _calc_difficulty_factor,
    calculate_machining_cost,
    _detect_treatments,
    _calc_treatment_cost,
)
from services.weight_calculator import (  # noqa: F401
    calculate_weight,
    calculate_weight_rectangular,
    estimate_weight_by_name,
    WEIGHT_ESTIMATES,
    _extract_dimensions_from_bom_data,
    _extract_dimensions_from_description,
    _extract_dimensions_from_size,
)

logger = logging.getLogger(__name__)


# ── 표준부품 카탈로그 (Phase 5) ──────────────────────────────────

@dataclass
class StandardPartSpec:
    part_type: str           # BOLT, NUT, WASHER, PIN, PLUG, CLIP
    diameter_mm: float = 0.0
    length_mm: float = 0.0
    pitch_mm: float = 0.0
    material_code: str = ""
    raw_size: str = ""


STANDARD_PART_KEYWORDS = {
    "HEX SOCKET HD BOLT": "BOLT", "HEX HD BOLT": "BOLT",
    "BUTTON HD SOCKET BOLT": "BOLT", "HEX SOCKET HD SCREW": "BOLT",
    "HEX NUT": "NUT",
    "SPRING WASHER": "WASHER", "NORD LOCK WASHER": "WASHER",
    "DOWEL PIN": "PIN", "LOCKING PIN": "PIN", "SET PIN": "PIN",
    "PIPE PLUG": "PLUG",
    "WIRE CLIP": "CLIP",
    "BOLT": "BOLT", "NUT": "NUT", "WASHER": "WASHER",
    "PIN": "PIN", "PLUG": "PLUG",
}

_catalog_cache: Optional[Dict] = None


class CostBreakdown:
    """단품 원가 내역"""
    def __init__(self):
        self.weight_kg: float = 0.0
        self.material_cost: float = 0.0
        self.machining_cost: float = 0.0
        self.treatment_cost: float = 0.0       # 열처리/표면처리 비용
        self.scrap_cost: float = 0.0           # 스크랩/절삭 손실
        self.setup_cost: float = 0.0           # 셋업비 (소량 고정비)
        self.inspection_cost: float = 0.0      # 검사비
        self.transport_cost: float = 0.0       # 포장/운송비
        self.subtotal: float = 0.0
        self.raw_dimensions: Optional[Dict[str, float]] = None
        self.original_dimensions: Optional[Dict[str, float]] = None  # 여유치 적용 전
        self.allowance_applied: bool = False
        self.difficulty_factor: float = 1.0     # 가공 난이도 계수
        self.treatments: List[str] = []         # 적용된 열처리/표면처리
        self.quantity_discount: float = 0.0     # 수량 할인율 (%)
        self.cost_source: str = "none"  # "calculated" | "estimated" | "standard_catalog" | "none"


# ── 표준부품 파싱 및 카탈로그 조회 ────────────────────────────────

def _is_standard_part(description: str) -> Optional[str]:
    """description 키워드 매칭 → 부품 타입 반환 (긴 키워드 우선)"""
    desc_upper = description.upper().strip()
    for keyword in sorted(STANDARD_PART_KEYWORDS.keys(), key=len, reverse=True):
        if keyword in desc_upper:
            return STANDARD_PART_KEYWORDS[keyword]
    return None


def parse_standard_part_size(size: str, part_type: str) -> Optional[StandardPartSpec]:
    """BOM size 필드 파싱 → StandardPartSpec"""
    if not size:
        return None
    s = size.strip()

    # 볼트: M24X120L, M16x80
    if part_type == "BOLT":
        m = re.match(r'^M(\d+)\s*[xX×]\s*(\d+)\s*L?$', s)
        if m:
            return StandardPartSpec(
                part_type="BOLT", diameter_mm=float(m.group(1)),
                length_mm=float(m.group(2)), raw_size=s,
            )

    # 너트: M16x1.5p, M24X2.0P
    if part_type == "NUT":
        m = re.match(r'^M(\d+)\s*[xX×]\s*([\d.]+)\s*[pP]$', s)
        if m:
            return StandardPartSpec(
                part_type="NUT", diameter_mm=float(m.group(1)),
                pitch_mm=float(m.group(2)), raw_size=s,
            )
        # 너트: M16 (피치 없음)
        m = re.match(r'^M(\d+)$', s)
        if m:
            return StandardPartSpec(
                part_type="NUT", diameter_mm=float(m.group(1)), raw_size=s,
            )

    # Nord Lock 와셔: NL16SS, NL24
    if part_type == "WASHER":
        m = re.match(r'^NL(\d+)\s*(SS)?$', s, re.IGNORECASE)
        if m:
            return StandardPartSpec(
                part_type="WASHER", diameter_mm=float(m.group(1)),
                material_code=m.group(2) or "", raw_size=s,
            )
        # 스프링 와셔: "12 X 22 X ..." → 첫 숫자가 직경
        m = re.match(r'^(\d+)\s*[xX×]\s*(\d+)\s*[xX×]', s)
        if m:
            return StandardPartSpec(
                part_type="WASHER", diameter_mm=float(m.group(1)), raw_size=s,
            )

    # 핀: D24x57L, D10
    if part_type == "PIN":
        m = re.match(r'^D([\d.]+)\s*(?:[xX×]\s*([\d.]+)\s*L?)?$', s)
        if m:
            return StandardPartSpec(
                part_type="PIN", diameter_mm=float(m.group(1)),
                length_mm=float(m.group(2)) if m.group(2) else 0.0, raw_size=s,
            )
        # 셋핀: M36-3 X 19L
        m = re.match(r'^M(\d+)-([\d.]+)\s*[xX×]\s*(\d+)\s*L?$', s)
        if m:
            return StandardPartSpec(
                part_type="PIN", diameter_mm=float(m.group(1)),
                length_mm=float(m.group(3)), pitch_mm=float(m.group(2)),
                raw_size=s,
            )

    # 플러그: 0.25"NPT, 1/4"NPT
    if part_type == "PLUG":
        m = re.match(r'^([\d.]+)\s*["\u201c\u201d]?\s*NPT', s, re.IGNORECASE)
        if m:
            inch_val = float(m.group(1))
            # 인치 → mm 변환 (NPT 호칭경)
            npt_mm_map = {0.125: 6.4, 0.25: 10.3, 0.375: 13.7, 0.5: 21.3, 0.75: 27.0, 1.0: 33.4}
            mm = npt_mm_map.get(inch_val, inch_val * 25.4)
            return StandardPartSpec(
                part_type="PLUG", diameter_mm=mm, raw_size=s,
            )

    # 클립: 숫자 추출 시도
    if part_type == "CLIP":
        m = re.match(r'^[A-Za-z]*\s*(\d+)', s)
        if m:
            return StandardPartSpec(
                part_type="CLIP", diameter_mm=float(m.group(1)), raw_size=s,
            )

    # 일반 폴백: M숫자 패턴
    m = re.match(r'^M(\d+)', s)
    if m:
        return StandardPartSpec(
            part_type=part_type, diameter_mm=float(m.group(1)), raw_size=s,
        )

    return None


def _load_catalog() -> Dict:
    """표준부품 카탈로그 JSON 로드 (싱글톤 캐시)"""
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache

    catalog_path = Path(__file__).parent.parent / "data" / "standard_parts_catalog.json"
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            _catalog_cache = json.load(f)
    except FileNotFoundError:
        logger.warning(f"Standard parts catalog not found: {catalog_path}")
        _catalog_cache = {}
    return _catalog_cache


def _lookup_catalog_price(spec: StandardPartSpec) -> Optional[float]:
    """카탈로그에서 단가 조회. 반환: 개당 단가 (KRW)"""
    catalog = _load_catalog()
    part_data = catalog.get(spec.part_type)
    if not part_data:
        return None

    prices = part_data.get("prices", {})

    # 직경 키 결정
    if spec.part_type == "PLUG":
        dia_key = f"NPT_{spec.diameter_mm}"
    else:
        dia_key = f"M{int(spec.diameter_mm)}"

    entry = prices.get(dia_key)

    # 정확한 키 없으면 가장 가까운 직경 사용
    if not entry and prices:
        def _extract_num(k: str) -> float:
            m = re.search(r'[\d.]+', k)
            return float(m.group()) if m else 0
        closest = min(prices.keys(), key=lambda k: abs(_extract_num(k) - spec.diameter_mm))
        entry = prices[closest]
        logger.debug(f"[Catalog] {dia_key} not found, using closest: {closest}")

    if not entry:
        return None

    base = entry.get("base_price", 0)
    per_mm = entry.get("per_mm", 0)
    unit_price = base + per_mm * spec.length_mm

    return unit_price


def _try_standard_catalog(
    description: str, size: str, quantity: int,
) -> Optional[CostBreakdown]:
    """표준부품 카탈로그 통합 조회 → CostBreakdown 또는 None"""
    part_type = _is_standard_part(description)
    if not part_type:
        return None

    spec = parse_standard_part_size(size, part_type)
    if not spec:
        return None

    unit_price = _lookup_catalog_price(spec)
    if unit_price is None:
        return None

    breakdown = CostBreakdown()
    breakdown.material_cost = unit_price * quantity  # 구매비
    breakdown.machining_cost = 0                     # 가공 불필요
    breakdown.subtotal = breakdown.material_cost
    breakdown.cost_source = "standard_catalog"

    logger.debug(
        f"[Catalog] {description} | size={size} → {spec.part_type} "
        f"d={spec.diameter_mm}mm L={spec.length_mm}mm | "
        f"₩{unit_price:,.0f}/ea × {quantity} = ₩{breakdown.subtotal:,.0f}"
    )

    return breakdown


# ── 메인 오케스트레이터 ──────────────────────────────────────────

def calculate_item_cost(
    session: Dict[str, Any],
    pricing_config: PricingConfig,
    features: Optional[List[str]] = None,
) -> CostBreakdown:
    """단품 전체 원가 계산

    1. 치수 있으면 → 여유치 → 중량 계산
    2. 치수 없으면 → 부품명 기반 추정
    3. 재료비 + 가공비 → 소계
    """
    breakdown = CostBreakdown()

    metadata = session.get("metadata") or {}
    bom_data = session.get("bom_data") or {}
    material = metadata.get("material", "")
    description = metadata.get("bom_description", "")
    quantity = metadata.get("bom_quantity", 1)

    if not material and not description:
        return breakdown

    # Phase 5: 표준부품 카탈로그 조회 (볼트/너트/와셔/핀 등)
    size = metadata.get("size") or ""
    catalog_result = _try_standard_catalog(description, size, quantity)
    if catalog_result:
        return catalog_result

    # 재질 정보 조회
    material_info = _get_material_info(material, pricing_config.materials)
    part_type = _detect_part_type(description)

    # 1. 치수 데이터 탐색
    dimensions = _extract_dimensions_from_bom_data(bom_data)

    if not dimensions:
        size = metadata.get("size") or ""
        dimensions = _extract_dimensions_from_size(size)

    if not dimensions:
        dimensions = _extract_dimensions_from_description(description)

    if dimensions:
        shape = dimensions.pop("shape", "round")
        breakdown.original_dimensions = dict(dimensions)

        skip_allowance = features is not None and "no_material_allowance" in features

        if shape == "rectangular":
            l, w, t = dimensions["l"], dimensions["w"], dimensions["t"]
            if not skip_allowance:
                l += 3; w += 3; t += 3  # 판재 여유치: 각 변 +3mm
                breakdown.allowance_applied = True
            breakdown.raw_dimensions = {"l": l, "w": w, "t": t, "shape": "rectangular"}
            breakdown.weight_kg = calculate_weight_rectangular(l, w, t, material_info.density)
        else:
            # 기존 원형 로직 (OD/ID/Length + apply_allowance)
            if not skip_allowance:
                raw_dims = apply_allowance(dimensions, pricing_config.allowances)
                breakdown.allowance_applied = True
            else:
                raw_dims = dict(dimensions)
            breakdown.raw_dimensions = raw_dims
            od = raw_dims.get("od", 0)
            id_ = raw_dims.get("id", 0)
            length = raw_dims.get("length", 100)
            breakdown.weight_kg = calculate_weight(od, id_, length, material_info.density)

        breakdown.cost_source = "calculated"
    else:
        # 폴백: 부품명 기반 추정
        breakdown.weight_kg = estimate_weight_by_name(description)
        breakdown.cost_source = "estimated"

    # 2. 재료비 계산
    breakdown.material_cost = calculate_material_cost(
        breakdown.weight_kg, material_info.unit_price, quantity
    )

    # 2-1. 스크랩율 (절삭 손실) 가산
    is_rect = (breakdown.raw_dimensions or {}).get("shape") == "rectangular"
    scrap_rate = pricing_config.scrap_rate_rect if is_rect else pricing_config.scrap_rate_round
    breakdown.scrap_cost = breakdown.material_cost * scrap_rate / 100
    breakdown.material_cost += breakdown.scrap_cost

    # 2-2. 수량 할인
    breakdown.quantity_discount = _calc_quantity_discount(quantity)
    if breakdown.quantity_discount > 0:
        breakdown.material_cost *= (1 - breakdown.quantity_discount / 100)

    # 3. 가공비 계산 (크기계수 × 난이도계수)
    breakdown.difficulty_factor = _calc_difficulty_factor(
        description, material, dimensions=breakdown.raw_dimensions,
    )
    breakdown.machining_cost = calculate_machining_cost(
        part_type, pricing_config.machining_rates, quantity,
        weight_kg=breakdown.weight_kg,
        difficulty_factor=breakdown.difficulty_factor,
    )

    # 3-1. 셋업비 (소량 생산 시 고정비)
    if quantity <= pricing_config.setup_qty_threshold:
        breakdown.setup_cost = pricing_config.setup_cost

    # 4. 열처리/표면처리 비용
    breakdown.treatments = _detect_treatments(description, material)
    breakdown.treatment_cost = _calc_treatment_cost(
        breakdown.treatments, breakdown.weight_kg, quantity,
    )

    # 5. 소계 (마진 반영)
    base_subtotal = (
        breakdown.material_cost * (1 + pricing_config.material_margin / 100)
        + breakdown.machining_cost * (1 + pricing_config.labor_margin / 100)
        + breakdown.treatment_cost
        + breakdown.setup_cost
    )

    # 5-1. 검사비 (소계 대비 %)
    breakdown.inspection_cost = base_subtotal * pricing_config.inspection_rate / 100

    # 5-2. 운송비 (중량 기반)
    breakdown.transport_cost = (
        breakdown.weight_kg * quantity * pricing_config.transport_per_kg
    )

    breakdown.subtotal = (
        base_subtotal + breakdown.inspection_cost + breakdown.transport_cost
    )

    logger.debug(
        f"[CostCalc] {description}: weight={breakdown.weight_kg:.2f}kg, "
        f"material=₩{breakdown.material_cost:,.0f} (scrap={scrap_rate}%), "
        f"machining=₩{breakdown.machining_cost:,.0f} (diff={breakdown.difficulty_factor:.1f}), "
        f"treatment=₩{breakdown.treatment_cost:,.0f} {breakdown.treatments}, "
        f"setup=₩{breakdown.setup_cost:,.0f}, inspect=₩{breakdown.inspection_cost:,.0f}, "
        f"transport=₩{breakdown.transport_cost:,.0f}, "
        f"subtotal=₩{breakdown.subtotal:,.0f} ({breakdown.cost_source})"
    )

    return breakdown
