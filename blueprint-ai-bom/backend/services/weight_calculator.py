"""Weight Calculator - 중량 추정 및 치수 추출

Functions:
  - calculate_weight: 중공 원통 중량 (kg)
  - calculate_weight_rectangular: 직사각형 블록/판재 중량 (kg)
  - estimate_weight_by_name: 부품명 기반 중량 추정 (폴백)
  - _extract_dimensions_from_bom_data: bom_data에서 치수 추출
  - _extract_dimensions_from_description: 도면 설명에서 치수 추출
  - _extract_dimensions_from_size: metadata.size 필드에서 치수 추출
"""

import math
import re
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


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
