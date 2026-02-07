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

    OD 670 + 5mm → 675
    ID 440 - 3mm → 437 (allowance_mm이 음수)
    Length 190 + 3mm → 193
    """
    rule_map = {r.dimension_type: r.allowance_mm for r in rules}
    result = {}

    for key, value in dimensions.items():
        normalized = key.lower()
        allowance = rule_map.get(normalized, 0.0)
        # ID=0 (솔리드 부품)은 ID 여유치 미적용
        if normalized == "id" and value == 0:
            allowance = 0.0
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


def calculate_weight_rectangular(
    l_mm: float, w_mm: float, t_mm: float, density: float = 7.85,
) -> float:
    """직사각형 블록/판재 중량 (kg)
    V = L × W × T [mm³ → cm³] / 1000 → kg
    """
    volume_cm3 = (l_mm / 10) * (w_mm / 10) * (t_mm / 10)
    return volume_cm3 * density / 1000.0


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
    weight_kg: float = 0.0,
    difficulty_factor: float = 1.0,
) -> float:
    """가공비 = 기본가공비 × 크기계수 × 난이도계수 × 수량"""
    rate_map = {r.part_type.upper(): r.base_rate for r in rates}
    base_rate = rate_map.get(part_type.upper(), rate_map.get("DEFAULT", 40000))

    # 중량 기반 크기계수 (5단계)
    if weight_kg < 1:
        size_factor = 0.3
    elif weight_kg < 10:
        size_factor = 0.5
    elif weight_kg < 50:
        size_factor = 1.0
    elif weight_kg < 200:
        size_factor = 1.5
    else:
        size_factor = 2.0

    return base_rate * size_factor * difficulty_factor * quantity


def _get_material_info(
    material: str,
    materials: List[MaterialPrice],
) -> MaterialPrice:
    """재질명으로 단가 정보 조회 (부분 매칭 + 접미사 제거)"""
    material_upper = material.upper().strip()

    # 정확한 매칭
    for m in materials:
        if m.material.upper() == material_upper:
            return m

    # 접미사 제거 후 재매칭 (+QT, +N, +Q.T, OR EQV 등)
    cleaned = re.sub(r'[\+\s]*(Q\.?T|QT|N|OR\s+EQV).*$', '', material_upper).strip()
    if cleaned != material_upper:
        for m in materials:
            if m.material.upper() == cleaned:
                return m

    # 부분 매칭 (SS400이 "SS400 (KS)" 같은 형태에도 매칭)
    for m in materials:
        if m.material.upper() in material_upper or material_upper in m.material.upper():
            return m

    # 기본값
    for m in materials:
        if m.material.upper() == "DEFAULT":
            return m

    return MaterialPrice(material="DEFAULT", unit_price=1500, density=7.85)


def _detect_part_type(description: str) -> str:
    """부품명에서 부품 유형 추출 (긴 키워드 우선 매칭)"""
    desc_upper = description.upper()
    # 긴 키워드 먼저 (BEARING RING → BEARING, SHIM PLATE → SHIM)
    _PART_KEYWORDS = [
        "BEARING CASING", "BEARING RING", "BEARING",
        "THRUST CASING", "CASING",
        "HOUSING",
        "LEVELING PLATE", "SHIM PLATE", "LOCKING PLATE",
        "THRUST PAD", "LINER PAD", "ANTI WEAR PAD", "PAD",
        "SEAL RING", "RING",
        "WEDGE", "NOZZLE", "BUSHING", "PIVOT", "COVER",
        "SHAFT", "PLATE", "SHIM",
    ]
    for keyword in _PART_KEYWORDS:
        if keyword in desc_upper:
            return keyword
    return "DEFAULT"


# 가공 난이도 키워드 → 추가 계수 (누적)
_DIFFICULTY_KEYWORDS: Dict[str, float] = {
    "KEYWAY": 0.3,      # 키홈 가공
    "KEY WAY": 0.3,
    "GROOVE": 0.2,      # 홈 가공
    "THREAD": 0.2,      # 나사 가공
    "TAPPING": 0.2,
    "GRINDING": 0.3,    # 연삭 가공
    "LAPPING": 0.4,     # 래핑 (정밀)
    "BORING": 0.2,      # 보링 가공
    "SLOT": 0.15,       # 슬롯
    "HOLE": 0.1,        # 홀 가공
    "CHAMFER": 0.05,    # 면취
    "ASSY": 0.15,       # 조립 공수
    "ASSEMBLY": 0.15,
}


def _calc_difficulty_factor(
    description: str, material: str,
    dimensions: Optional[Dict[str, float]] = None,
) -> float:
    """부품 설명 + 재질 + 치수에서 가공 난이도 계수 산출 (기본 1.0)"""
    desc_upper = description.upper()
    mat_upper = material.upper()

    factor = 1.0

    # 키워드별 누적 가산
    for keyword, add in _DIFFICULTY_KEYWORDS.items():
        if keyword in desc_upper:
            factor += add

    # 난삭재 가산
    if "SUS" in mat_upper or "STAINLESS" in mat_upper:
        factor += 0.3
    elif "SCM" in mat_upper or "SNCM" in mat_upper:
        factor += 0.15
    elif "BABBITT" in mat_upper:
        factor += 0.2

    # 치수 기반 가산 (원형 부품)
    if dimensions:
        od = dimensions.get("od", 0)
        id_ = dimensions.get("id", 0)
        if od > 0 and id_ > 0:
            wall_ratio = id_ / od  # 벽두께 비율
            if wall_ratio > 0.85:       # 극박 (벽 7.5% 미만)
                factor += 0.4
            elif wall_ratio > 0.75:     # 박벽 (벽 12.5% 미만)
                factor += 0.2
        # 대형 부품 (OD > 800mm)
        if od > 800:
            factor += 0.15

    return min(factor, 3.0)  # 상한 3배


# 열처리/표면처리 단가 (KRW/kg)
_TREATMENT_COSTS: Dict[str, float] = {
    "QT": 800,           # 조질 (담금질+뜨임)
    "Q.T": 800,
    "QUENCHING": 800,
    "TEMPERING": 500,
    "NORMALIZING": 400,  # 노멀라이징
    "CARBURIZING": 1200, # 침탄
    "NITRIDING": 1500,   # 질화
    "INDUCTION": 1000,   # 고주파 열처리
    "CHROME": 2000,      # 크롬 도금
    "HARD CHROME": 2500,
    "SPRAY": 3000,       # 용사 코팅
    "BABBITT LINING": 5000,  # 배빗 라이닝
}


def _detect_treatments(description: str, material: str) -> List[str]:
    """재질명 + 설명에서 열처리/표면처리 항목 검출 (긴 키워드 우선, 중복 제거)"""
    combined = f"{material} {description}".upper()
    found = []
    # 긴 키워드 우선 매칭 (HARD CHROME > CHROME)
    for treatment in sorted(_TREATMENT_COSTS.keys(), key=len, reverse=True):
        if treatment in combined:
            # 이미 상위 키워드가 잡혔으면 하위 키워드 스킵
            if any(treatment in existing for existing in found):
                continue
            found.append(treatment)
    return found


def _calc_treatment_cost(treatments: List[str], weight_kg: float, quantity: int) -> float:
    """열처리/표면처리 비용 합산"""
    total = 0.0
    for t in treatments:
        rate = _TREATMENT_COSTS.get(t, 0)
        total += rate * weight_kg * quantity
    return total


def _calc_quantity_discount(quantity: int) -> float:
    """수량 구간별 할인율 (%)"""
    if quantity >= 100:
        return 15.0
    elif quantity >= 50:
        return 10.0
    elif quantity >= 10:
        return 5.0
    return 0.0


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


def _extract_dimensions_from_size(size: str) -> Optional[Dict[str, float]]:
    """metadata.size 필드에서 치수 추출

    지원 패턴:
      - OD670XID440X29.5T  → od=670, id=440, length=29.5
      - OD873.6 x ID 518.5 x 297.5 → od=873.6, id=518.5, length=297.5
      - ID460xOD1020x450   → od=1020, id=460, length=450
      - 1300 X ID 846 X 240L → od=1300, id=846, length=240
      - OD510xID402.6X 260L → od=510, id=402.6, length=260
      - OD40X12 / D75x20L  → solid round (id=0)
      - 180x190x22          → rectangular → 가장 큰 2값으로 od/length
    """
    if not size or not size.strip():
        return None

    s = size.strip().upper()

    # 볼트/너트/파이프피팅은 스킵 (표준부품 카탈로그에서 처리)
    if re.match(r'^M\d', s) or 'NPT' in s:
        return None

    # 숫자 패턴 (정수 or 소수, T/L 접미사 허용)
    _N = r'(\d+(?:\.\d+)?)'
    # 구분자 (x, X, × 앞뒤 공백 허용)
    _SEP = r'\s*[xX×]\s*'

    od, id_, length = None, None, None

    # 패턴 1: OD + ID + 길이/두께
    m = re.search(rf'OD\s*{_N}{_SEP}ID\s*{_N}{_SEP}{_N}', s)
    if m:
        od, id_, length = float(m.group(1)), float(m.group(2)), float(m.group(3))

    # 패턴 2: ID + OD + 길이 (역순)
    if od is None:
        m = re.search(rf'ID\s*{_N}{_SEP}OD\s*{_N}{_SEP}{_N}', s)
        if m:
            id_, od, length = float(m.group(1)), float(m.group(2)), float(m.group(3))

    # 패턴 3: 숫자 X ID 숫자 X 숫자L (OD prefix 없이)
    if od is None:
        m = re.search(rf'{_N}{_SEP}ID\s*{_N}{_SEP}{_N}', s)
        if m:
            od, id_, length = float(m.group(1)), float(m.group(2)), float(m.group(3))

    # 패턴 4: OD + 길이만 (solid round, ID 없음)
    if od is None:
        m = re.search(rf'OD\s*{_N}{_SEP}{_N}', s)
        if m:
            od, id_, length = float(m.group(1)), 0.0, float(m.group(2))

    # 패턴 5: D + 길이 (solid round bar)
    if od is None:
        m = re.search(rf'D{_N}{_SEP}{_N}', s)
        if m:
            od, id_, length = float(m.group(1)), 0.0, float(m.group(2))

    # 패턴 6: 3개 숫자 (OD/ID prefix 없음 → 직사각형 판재/블록)
    if od is None:
        m = re.search(rf'{_N}{_SEP}{_N}{_SEP}{_N}', s)
        if m:
            vals = sorted([float(m.group(1)), float(m.group(2)), float(m.group(3))], reverse=True)
            return {
                "l": vals[0], "w": vals[1], "t": vals[2],
                "shape": "rectangular",
            }

    if od is not None and od > 0:
        return {
            "od": od,
            "id": id_ or 0.0,
            "length": length or 100.0,
            "shape": "round",
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
