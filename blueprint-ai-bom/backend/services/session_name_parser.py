"""세션명 파싱 + OD/ID/W 검증 보정

BOM PDF에서 추출된 세션명에 포함된 치수 정보를 파싱하고,
OCR 분류 결과와 교차 검증하여 보정한다.

패턴:
- "스러스트베어링 ASSY (OD670×ID440)" → OD=670, ID=440
- "T8 저널베어링 ASSY (500×260)" → OD=500, W=260
"""

import re
import logging
from typing import List, Optional, Tuple

from schemas.dimension import Dimension, MaterialRole

logger = logging.getLogger(__name__)


def parse_session_name_dimensions(session_name: str) -> dict:
    """세션명에서 OD/ID/W 파싱 — BOM PDF에서 이미 추출된 정보

    패턴:
    - "스러스트베어링 ASSY (OD670×ID440)" → OD=670, ID=440
    - "T8 저널베어링 ASSY (500×260)" → OD=500, W=260
    """
    result = {"od": None, "id": None, "w": None, "pattern": None}
    if not session_name:
        return result

    # 패턴 1: OD숫자×ID숫자 (명시적)
    m = re.search(r'OD\s*(\d+)\s*[×xX]\s*ID\s*(\d+)', session_name)
    if m:
        result["od"] = float(m.group(1))
        result["id"] = float(m.group(2))
        result["pattern"] = "explicit_OD_ID"
        return result

    # 패턴 2: (숫자×숫자) — 괄호 안 두 수 (저널베어링 관례: 큰=OD, 작은=W)
    m = re.search(r'\((\d+)\s*[×xX]\s*(\d+)\)', session_name)
    if m:
        v1, v2 = float(m.group(1)), float(m.group(2))
        result["od"] = max(v1, v2)
        result["w"] = min(v1, v2)
        result["pattern"] = "parenthesized_pair"
        return result

    return result


def validate_with_session_ref(
    dimensions: List[Dimension],
    ref: dict,
    parse_numeric_fn,
    is_noise_fn,
) -> List[Dimension]:
    """세션명 기준값으로 OCR 분류 결과 검증/보정

    기준값(BOM PDF에서 파싱)이 있으면:
    - 현재 OD가 기준 OD와 ±30% 이상 차이 → 기준값에 가장 가까운 치수로 교체
    - 현재 ID가 기준 ID와 ±30% 이상 차이 → 기준값에 가장 가까운 치수로 교체
    - OD/ID 미분류 상태면 기준값에 가장 가까운 치수를 배정
    """
    result = list(dimensions)
    ref_od = ref.get("od")
    ref_id = ref.get("id")

    if not ref_od and not ref_id:
        return result

    # 현재 분류 확인
    cur_od_idx = next(
        (i for i, d in enumerate(result)
         if d.material_role == MaterialRole.OUTER_DIAMETER),
        None,
    )
    cur_id_idx = next(
        (i for i, d in enumerate(result)
         if d.material_role == MaterialRole.INNER_DIAMETER),
        None,
    )

    # 모든 치수의 숫자값 추출 (노이즈 필터링)
    values = []
    for i, d in enumerate(result):
        v = parse_numeric_fn(d.value)
        if v and v > 1 and v < 5000 and not is_noise_fn(d.value):
            values.append((i, v))

    if not values:
        return result

    def _find_closest(target, exclude_indices=None):
        """기준값에 가장 가까운 치수 인덱스 찾기"""
        exclude = exclude_indices or set()
        candidates = [(i, v) for i, v in values if i not in exclude]
        if not candidates:
            return None, None
        best = min(candidates, key=lambda x: abs(x[1] - target))
        # 기준값 대비 ±50% 이내만 허용
        if abs(best[1] - target) / target > 0.5:
            return None, None
        return best

    # OD 검증/보정
    if ref_od:
        if cur_od_idx is not None:
            cur_od_val = parse_numeric_fn(result[cur_od_idx].value)
            if cur_od_val and abs(cur_od_val - ref_od) / ref_od > 0.3:
                best_i, best_v = _find_closest(ref_od)
                if best_i is not None and best_i != cur_od_idx:
                    logger.info(
                        f"세션명 보정: OD {cur_od_val} → {best_v} "
                        f"(기준={ref_od})"
                    )
                    result[cur_od_idx] = result[cur_od_idx].model_copy(
                        update={"material_role": None}
                    )
                    result[best_i] = result[best_i].model_copy(
                        update={"material_role": MaterialRole.OUTER_DIAMETER}
                    )
                    cur_od_idx = best_i
        else:
            best_i, best_v = _find_closest(ref_od)
            if best_i is not None:
                logger.info(f"세션명 기반 OD 배정: {best_v} (기준={ref_od})")
                result[best_i] = result[best_i].model_copy(
                    update={"material_role": MaterialRole.OUTER_DIAMETER}
                )
                cur_od_idx = best_i

    # ID 검증/보정
    if ref_id:
        exclude = {cur_od_idx} if cur_od_idx is not None else set()
        if cur_id_idx is not None:
            cur_id_val = parse_numeric_fn(result[cur_id_idx].value)
            if cur_id_val and abs(cur_id_val - ref_id) / ref_id > 0.3:
                best_i, best_v = _find_closest(ref_id, exclude)
                if best_i is not None and best_i != cur_id_idx:
                    logger.info(
                        f"세션명 보정: ID {cur_id_val} → {best_v} "
                        f"(기준={ref_id})"
                    )
                    result[cur_id_idx] = result[cur_id_idx].model_copy(
                        update={"material_role": None}
                    )
                    result[best_i] = result[best_i].model_copy(
                        update={"material_role": MaterialRole.INNER_DIAMETER}
                    )
        else:
            best_i, best_v = _find_closest(ref_id, exclude)
            if best_i is not None:
                logger.info(f"세션명 기반 ID 배정: {best_v} (기준={ref_id})")
                result[best_i] = result[best_i].model_copy(
                    update={"material_role": MaterialRole.INNER_DIAMETER}
                )

    return result
