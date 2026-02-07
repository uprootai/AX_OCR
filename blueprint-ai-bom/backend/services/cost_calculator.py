"""Cost Calculator - 원가 계산 엔진

Phase 4: 치수 → +여유치 → 중량 → x단가 → +가공비 → 소계
Phase 5: 표준부품 카탈로그 가격 산출 (볼트/너트/와셔/핀/플러그)
"""

import json
import math
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

from schemas.pricing_config import (
    PricingConfig,
    MaterialPrice,
    AllowanceRule,
    MachiningRate,
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
        self.subtotal: float = 0.0
        self.raw_dimensions: Optional[Dict[str, float]] = None
        self.cost_source: str = "none"  # "calculated" | "estimated" | "standard_catalog" | "none"


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


def apply_allowance(
    dimensions: Dict[str, float],
    rules: List[AllowanceRule],
) -> Dict[str, float]:
    """치수 + 여유치 → 소재 사이즈

    OD 670 + 10mm → 680
    ID 440 - 5mm → 435 (allowance_mm이 음수)
    Length 190 + 5mm → 195
    """
    rule_map = {r.dimension_type: r.allowance_mm for r in rules}
    result = {}

    for key, value in dimensions.items():
        normalized = key.lower()
        allowance = rule_map.get(normalized, 0.0)
        result[key] = value + allowance

    return result


def calculate_weight(
    od_mm: float,
    id_mm: float,
    length_mm: float,
    density: float = 7.85,
) -> float:
    """중공 원통 부피 → 중량 (kg)

    V = pi/4 * ((OD/10)^2 - (ID/10)^2) * (L/10)  [cm^3]
    W = V * density / 1000  [kg]
    """
    od_cm = od_mm / 10.0
    id_cm = id_mm / 10.0
    length_cm = length_mm / 10.0

    volume_cm3 = math.pi / 4.0 * (od_cm ** 2 - id_cm ** 2) * length_cm
    weight_kg = volume_cm3 * density / 1000.0

    return max(weight_kg, 0.0)


def calculate_material_cost(
    weight_kg: float,
    unit_price: float,
    quantity: int,
) -> float:
    """재료비 = 중량 x 단가 x 수량"""
    return weight_kg * unit_price * quantity


def calculate_machining_cost(
    part_type: str,
    rates: List[MachiningRate],
    quantity: int,
) -> float:
    """가공비 = 부품타입별 기본가공비 x 수량"""
    rate_map = {r.part_type.upper(): r.base_rate for r in rates}
    base_rate = rate_map.get(part_type.upper(), rate_map.get("DEFAULT", 40000))
    return base_rate * quantity


def _get_material_info(
    material: str,
    materials: List[MaterialPrice],
) -> MaterialPrice:
    """재질명으로 단가 정보 조회 (부분 매칭 지원)"""
    material_upper = material.upper().strip()

    # 정확한 매칭
    for m in materials:
        if m.material.upper() == material_upper:
            return m

    # 부분 매칭 (SS400이 "SS400 (KS)" 같은 형태에도 매칭)
    for m in materials:
        if m.material.upper() in material_upper or material_upper in m.material.upper():
            return m

    # 기본값
    for m in materials:
        if m.material.upper() == "DEFAULT":
            return m

    return MaterialPrice(material="DEFAULT", unit_price=5000, density=7.85)


def _detect_part_type(description: str) -> str:
    """부품명에서 부품 유형 추출"""
    desc_upper = description.upper()
    for keyword in ["PAD", "RING", "BEARING", "CASING", "HOUSING"]:
        if keyword in desc_upper:
            return keyword
    return "DEFAULT"


def _extract_dimensions_from_bom_data(
    bom_data: Dict[str, Any],
) -> Optional[Dict[str, float]]:
    """bom_data에서 치수 추출 (dimensions 필드)"""
    items = bom_data.get("items", [])
    for item in items:
        dims = item.get("dimensions")
        if dims and isinstance(dims, dict):
            od = dims.get("od") or dims.get("OD") or dims.get("외경")
            id_ = dims.get("id") or dims.get("ID") or dims.get("내경")
            length = dims.get("length") or dims.get("Length") or dims.get("길이")
            if od and id_:
                return {
                    "od": float(od),
                    "id": float(id_),
                    "length": float(length) if length else 100.0,
                }

    # summary에서 dimensions 찾기
    summary = bom_data.get("summary", {})
    dims = summary.get("dimensions")
    if dims and isinstance(dims, dict):
        od = dims.get("od") or dims.get("OD")
        id_ = dims.get("id") or dims.get("ID")
        length = dims.get("length") or dims.get("Length")
        if od and id_:
            return {
                "od": float(od),
                "id": float(id_),
                "length": float(length) if length else 100.0,
            }

    return None


def _extract_dimensions_from_description(description: str) -> Optional[Dict[str, float]]:
    """도면 설명에서 치수 추출 (예: "T1 BEARING ASSY(360X190)")"""
    patterns = [
        r'\((\d+)[xX×](\d+)\)',     # (360X190)
        r'(\d+)[xX×](\d+)',          # 360X190
        r'OD\s*(\d+).*ID\s*(\d+)',   # OD360 ID190
    ]
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                d1 = float(groups[0])
                d2 = float(groups[1])
                od = max(d1, d2)
                id_or_length = min(d1, d2)
                return {
                    "od": od,
                    "id": id_or_length * 0.6 if id_or_length < od * 0.5 else id_or_length,
                    "length": id_or_length if id_or_length < od * 0.5 else od * 0.3,
                }
    return None


# 부품명 기반 중량 추정 (치수 없을 때 폴백)
WEIGHT_ESTIMATES: Dict[str, float] = {
    "PAD": 5.0,
    "LINER PAD": 5.0,
    "THRUST PAD": 8.0,
    "RING": 25.0,
    "BEARING RING": 25.0,
    "CASING": 80.0,
    "BEARING CASING": 80.0,
    "THRUST CASING": 60.0,
    "HOUSING": 100.0,
    "BEARING": 50.0,
    "BEARING ASSY": 120.0,
    "THRUST BEARING": 80.0,
    "SHIM": 0.5,
    "SHIM PLATE": 0.5,
    "BOLT": 0.3,
    "NUT": 0.1,
    "WASHER": 0.05,
    "PIN": 0.2,
    "PLUG": 0.3,
    "NOZZLE": 1.0,
    "PIVOT": 0.5,
    "BUSHING": 2.0,
    "WEDGE": 3.0,
    "PLATE": 2.0,
    "LEVELING PLATE": 3.0,
    "COVER": 5.0,
    "CYLINDER": 10.0,
}


def estimate_weight_by_name(part_name: str) -> float:
    """치수 없을 때 부품명 기반 추정"""
    name_upper = part_name.upper().strip()

    # 정확한 매칭
    if name_upper in WEIGHT_ESTIMATES:
        return WEIGHT_ESTIMATES[name_upper]

    # 부분 매칭 (길이순 역정렬로 긴 키워드 우선)
    for keyword in sorted(WEIGHT_ESTIMATES.keys(), key=len, reverse=True):
        if keyword in name_upper:
            return WEIGHT_ESTIMATES[keyword]

    return 5.0  # 기본 추정 중량


def calculate_item_cost(
    session: Dict[str, Any],
    pricing_config: PricingConfig,
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
        dimensions = _extract_dimensions_from_description(description)

    if dimensions:
        # 여유치 적용
        raw_dims = apply_allowance(dimensions, pricing_config.allowances)
        breakdown.raw_dimensions = raw_dims

        # 중량 계산
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

    # 3. 가공비 계산
    breakdown.machining_cost = calculate_machining_cost(
        part_type, pricing_config.machining_rates, quantity
    )

    # 4. 소계
    breakdown.subtotal = breakdown.material_cost + breakdown.machining_cost

    logger.debug(
        f"[CostCalc] {description}: weight={breakdown.weight_kg:.2f}kg, "
        f"material=₩{breakdown.material_cost:,.0f}, "
        f"machining=₩{breakdown.machining_cost:,.0f}, "
        f"subtotal=₩{breakdown.subtotal:,.0f} ({breakdown.cost_source})"
    )

    return breakdown
