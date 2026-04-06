"""Dimension ensemble orchestrator."""

import ast
import logging

import cv2
import numpy as np

from services.dimension_ensemble_parts.common import (
    _apply_soft_filter,
    _extract_num,
    _run_s06_yolo_ocr,
    _vote_best,
)
from services.dimension_ensemble_parts.section_scan import (
    _run_section_scan,
    _scan_side_view,
)

logger = logging.getLogger(__name__)


def run_ensemble(image_path: str, drawing_title: str = "") -> dict:
    """다중 방법론 앙상블 실행."""
    import services.geometry_guided_extractor as gg
    from services.geometry_guided_extractor_parts import classification as gg_classification

    img = cv2.imread(image_path)
    if img is None:
        return {"od": None, "id": None, "w": None, "error": "Image load failed"}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    layout_info = None
    try:
        from services.layout_detector import detect_layout

        layout_info = detect_layout(image_path)
        if layout_info and not layout_info["is_bearing"]:
            logger.info(f"Layout: 비베어링 판정 → 스킵 ({image_path})")
            return {
                "od": None,
                "id": None,
                "w": None,
                "method_results": {},
                "strategy": "layout_skip",
                "layout": {"is_bearing": False, "regions": layout_info["regions"]},
            }
    except ImportError:
        logger.debug("layout_detector not available, skipping layout step")
    except Exception as exc:
        logger.debug(f"Layout detection skipped: {exc}")

    method_results = {}

    captured_dims = []
    captured_circles = {}
    original_classify = gg_classification._classify_by_circle_proximity

    def capturing_classify(dims, circles, dim_lines, *args, **kwargs):
        captured_dims.extend(dims)
        captured_circles.update({"circles": circles, "dim_lines": dim_lines})
        return original_classify(dims, circles, dim_lines, *args, **kwargs)

    gg_classification._classify_by_circle_proximity = capturing_classify
    try:
        k_result = gg.extract_by_geometry(image_path)
        method_results["K"] = {
            "od": k_result["od"]["value"] if k_result.get("od") else None,
            "id": k_result["id"]["value"] if k_result.get("id") else None,
            "w": k_result["w"]["value"] if k_result.get("w") else None,
        }
    except Exception as exc:
        logger.warning(f"K method failed: {exc}")
        method_results["K"] = {"od": None, "id": None, "w": None}
    finally:
        gg_classification._classify_by_circle_proximity = original_classify

    if drawing_title:
        from services.session_name_parser import parse_session_name_dimensions

        ref = parse_session_name_dimensions(drawing_title)
        ref_od = ref.get("od")
        ref_id = ref.get("id")
        ref_w = ref.get("w")
        k = method_results.get("K", {})

        if ref_od or ref_id:
            logger.info(
                f"세션명 힌트: OD={ref_od}, ID={ref_id}, W={ref_w} "
                f"(pattern={ref.get('pattern')})"
            )

            k_od = k.get("od")
            k_id = k.get("id")

            def _close(a, b, tol=0.3):
                if a is None or b is None:
                    return False
                try:
                    return abs(float(a) - float(b)) / max(float(b), 1) <= tol
                except (ValueError, TypeError):
                    return False

            if ref_od and (not k_od or not _close(k_od, ref_od)):
                best_od = None
                best_dist = float("inf")
                for dim in captured_dims:
                    try:
                        import re as _re

                        val_str = str(dim.get("value", ""))
                        val_str = _re.sub(r"^[ØøΦ⌀∅]\s*", "", val_str)
                        val_str = _re.sub(r"[()]", "", val_str)
                        match = _re.match(r"(\d+\.?\d*)", val_str)
                        if match:
                            value = float(match.group(1))
                            dist = abs(value - ref_od)
                            if dist < best_dist and dist / ref_od < 0.15:
                                best_dist = dist
                                best_od = val_str.strip()
                    except (ValueError, TypeError):
                        pass
                if best_od:
                    method_results["K"]["od"] = best_od
                    logger.info(f"K 외경 보정: {k_od} → {best_od} (힌트 {ref_od})")
                elif ref_od:
                    method_results["K"]["od"] = str(int(ref_od))
                    logger.info(f"K 외경 힌트 직접 사용: {ref_od}")

            if ref_id and (not k_id or not _close(k_id, ref_id)):
                best_id = None
                best_dist = float("inf")
                for dim in captured_dims:
                    try:
                        import re as _re

                        val_str = str(dim.get("value", ""))
                        val_str = _re.sub(r"^[ØøΦ⌀∅]\s*", "", val_str)
                        val_str = _re.sub(r"[()]", "", val_str)
                        match = _re.match(r"(\d+\.?\d*)", val_str)
                        if match:
                            value = float(match.group(1))
                            dist = abs(value - ref_id)
                            if dist < best_dist and dist / ref_id < 0.15:
                                best_dist = dist
                                best_id = val_str.strip()
                    except (ValueError, TypeError):
                        pass
                if best_id:
                    method_results["K"]["id"] = best_id
                    logger.info(f"K 내경 보정: {k_id} → {best_id} (힌트 {ref_id})")
                elif ref_id:
                    method_results["K"]["id"] = str(int(ref_id))
                    logger.info(f"K 내경 힌트 직접 사용: {ref_id}")

            if ref_w and not k.get("w"):
                method_results["K"]["w"] = str(int(ref_w))
                logger.info(f"K 폭 힌트 직접 사용: {ref_w}")

    exclude_bboxes = layout_info["exclude_bboxes"] if layout_info else []
    dims_for_sub = []
    excluded_count = 0
    for dim in captured_dims:
        bbox_raw = dim.get("bbox", {})
        if isinstance(bbox_raw, str):
            try:
                bbox_raw = ast.literal_eval(bbox_raw)
            except Exception:
                continue
        if not isinstance(bbox_raw, dict):
            continue
        if exclude_bboxes:
            try:
                from services.layout_detector import is_in_exclude_zone

                if is_in_exclude_zone(bbox_raw, exclude_bboxes):
                    excluded_count += 1
                    continue
            except ImportError:
                pass
        dims_for_sub.append(
            {
                "value": dim.get("value", ""),
                "confidence": float(dim.get("confidence", 0.5)),
                "bbox": bbox_raw,
            }
        )

    if excluded_count > 0:
        logger.info(
            f"Layout filter: {excluded_count} dims excluded from notes/table zones"
        )

    outer_circle = None
    circles_list = captured_circles.get("circles", [])
    if isinstance(circles_list, list):
        for circle in circles_list:
            if isinstance(circle, dict) and circle.get("role") == "outer":
                outer_circle = (circle["cx"], circle["cy"], circle["r"])
                break

    if not dims_for_sub:
        try:
            from services.dimension_service import DimensionService

            svc = DimensionService()
            fallback_result = svc.extract_dimensions(
                image_path,
                ocr_engines=["edocr2"],
                confidence_threshold=0.3,
            )
            for dim in fallback_result.get("dimensions", []):
                value = dim.get("value", "")
                confidence = dim.get("confidence", 0.5)
                bbox = dim.get("bbox")
                if not isinstance(bbox, dict):
                    continue
                dims_for_sub.append(
                    {
                        "value": str(value),
                        "confidence": float(confidence),
                        "bbox": bbox,
                    }
                )
            if dims_for_sub:
                logger.info(f"Fallback OCR: {len(dims_for_sub)} dims for S01/S02")
        except Exception as exc:
            logger.warning(f"Fallback OCR failed: {exc}")

    if dims_for_sub:
        try:
            from services.arrowhead_detector import run_arrowhead_pipeline

            s01 = run_arrowhead_pipeline(gray, dims_for_sub, outer_circle=outer_circle)
            method_results["S01"] = {
                "od": s01["od"]["value"] if s01.get("od") else None,
                "id": s01["id"]["value"] if s01.get("id") else None,
                "w": s01["w"]["value"] if s01.get("w") else None,
            }
        except Exception as exc:
            logger.warning(f"S01 failed: {exc}")
            method_results["S01"] = {"od": None, "id": None, "w": None}

        try:
            from services.dimension_text_first import extract_text_first

            oc_arr = np.array(outer_circle) if outer_circle else None
            s02 = extract_text_first(dims_for_sub, gray, outer_circle=oc_arr)
            method_results["S02"] = {
                "od": s02["od"]["value"] if s02.get("od") else None,
                "id": s02["id"]["value"] if s02.get("id") else None,
                "w": s02["w"]["value"] if s02.get("w") else None,
            }
        except Exception as exc:
            logger.warning(f"S02 failed: {exc}")
            method_results["S02"] = {"od": None, "id": None, "w": None}

    s06_model_path = "/tmp/yolo_s06_ocr/dim_detect_v2/weights/best.pt"
    try:
        import os

        if os.path.exists(s06_model_path):
            s06_result = _run_s06_yolo_ocr(image_path, s06_model_path)
            if any(s06_result.get(key) for key in ("od", "id", "w")):
                method_results["S06"] = s06_result
    except Exception as exc:
        logger.warning(f"S06 failed: {exc}")

    if "ASSY" in drawing_title.upper():
        try:
            sec_result = _run_section_scan(image_path, drawing_title)
            if any(sec_result.get(key) for key in ("od", "id", "w")):
                method_results["SEC"] = sec_result
                logger.info(f"SEC result: {sec_result}")
        except Exception as exc:
            logger.warning(f"SEC method failed: {exc}")

    if "ASSY" in drawing_title.upper():
        try:
            sec_views = method_results.get("SEC", {}).get("views", {})
            side_region = sec_views.get("auxiliary_view")
            if side_region:
                side_w = _scan_side_view(
                    image_path,
                    side_region,
                    hint_od=_extract_num(method_results.get("SEC", {}).get("od")),
                    hint_id=_extract_num(method_results.get("SEC", {}).get("id")),
                )
                if side_w:
                    method_results["SIDE"] = {
                        "od": None,
                        "id": None,
                        "w": f"{side_w:.0f}",
                    }
                    logger.info(f"SIDE view W: {side_w}")
        except Exception as exc:
            logger.warning(f"SIDE view scan failed: {exc}")

    k_result = method_results.get("K", {})
    k_od = _extract_num(k_result.get("od"))
    k_id = _extract_num(k_result.get("id"))
    k_w = _extract_num(k_result.get("w"))

    k_plausible = (
        k_od is not None
        and k_id is not None
        and k_w is not None
        and k_od > k_id > k_w
    )

    if k_plausible:
        od_votes = [_extract_num(method.get("od")) for method in method_results.values()]
        id_votes = [_extract_num(method.get("id")) for method in method_results.values()]
        w_votes = [_extract_num(method.get("w")) for method in method_results.values()]
    else:
        od_votes = [
            _extract_num(method.get("od"))
            for method_key, method in method_results.items()
            if method_key != "K"
        ]
        id_votes = [
            _extract_num(method.get("id"))
            for method_key, method in method_results.items()
            if method_key != "K"
        ]
        w_votes = [
            _extract_num(method.get("w"))
            for method_key, method in method_results.items()
            if method_key != "K"
        ]

    vote_od = _vote_best(od_votes)
    vote_id = _vote_best(id_votes)
    vote_w = _vote_best(w_votes)

    sec_result = method_results.get("SEC", {})
    sec_od = _extract_num(sec_result.get("od"))
    sec_id = _extract_num(sec_result.get("id"))
    sec_w = _extract_num(sec_result.get("w"))
    is_assy = "ASSY" in drawing_title.upper()

    sec_id_ok = (
        sec_id is not None
        and sec_od is not None
        and sec_od * 0.20 < sec_id < sec_od * 0.95
    )

    if is_assy and (sec_od or sec_id):
        final_od = sec_od

        k_od_override = False
        if k_plausible and k_od and sec_od and abs(sec_od - k_od) / max(k_od, 1) > 0.15:
            for method_key, method_value in method_results.items():
                if method_key in ("K", "SEC"):
                    continue
                mv_od = _extract_num(method_value.get("od"))
                if mv_od and abs(mv_od - k_od) / max(k_od, 1) < 0.05:
                    k_od_override = True
                    break
            if k_od_override:
                final_od, final_id, final_w = k_od, k_id, k_w
                logger.info(f"K-override: K plausible + corroborated → OD={k_od}")

        if not k_od_override and final_od and vote_od:
            if abs(final_od - vote_od) / max(vote_od, 1) > 0.30:
                supporters = sum(1 for vote in od_votes if vote and abs(vote - vote_od) <= 5.0)
                if supporters >= 2:
                    final_od = vote_od
                    logger.info(
                        f"Vote-override OD: SEC={sec_od} → vote={vote_od} "
                        f"({supporters} supporters)"
                    )

        if not k_od_override:
            sec_id_ok_final = (
                sec_id is not None
                and final_od is not None
                and final_od * 0.20 < sec_id < final_od * 0.95
            )
            final_id = sec_id if sec_id_ok_final else (k_id if k_id else vote_id)

            if final_od and final_od != sec_od and k_id and sec_id:
                k_ratio = k_id / final_od
                sec_ratio = sec_id / final_od
                k_typical = 0.30 < k_ratio < 0.90
                sec_typical = 0.30 < sec_ratio < 0.90
                if k_typical and not sec_typical:
                    final_id = k_id
                    logger.info(
                        f"K-ID preferred: ratio {k_ratio:.2f} vs SEC {sec_ratio:.2f}"
                    )

        if not k_od_override:
            side_w = _extract_num(method_results.get("SIDE", {}).get("w"))
            if side_w and not sec_w:
                final_w = side_w
                logger.info(f"SIDE-fill W: {side_w} (SEC W 없음)")
            elif (
                side_w
                and sec_w
                and final_id
                and abs(side_w - final_id) / max(final_id, 1) < 0.05
            ):
                final_w = side_w
                logger.info(
                    f"SIDE-override W: SEC={sec_w} → SIDE={side_w} "
                    f"(matches ID={final_id})"
                )
            else:
                final_w = sec_w if sec_w else (k_w if k_w else vote_w)

        strategy = "sec_priority"
        logger.info(f"SEC-priority: OD={final_od} ID={final_id} W={final_w}")
    elif k_plausible:
        final_od, final_id, final_w = k_od, k_id, k_w
        strategy = "k_priority"
    elif k_od is not None and k_id is not None:
        final_od, final_id = k_od, k_id
        final_w = k_w if k_w is not None else vote_w
        strategy = "k_partial"
    else:
        final_od, final_id, final_w = vote_od, vote_id, vote_w
        strategy = "vote_fallback"

    def _agreement(votes, consensus):
        if consensus is None:
            return 0.0
        valid = [vote for vote in votes if vote is not None]
        return (
            sum(1 for vote in valid if abs(vote - consensus) <= 5.0)
            / max(len(valid), 1)
        )

    result = {
        "od": {"value": f"Ø{final_od:.0f}" if final_od else None},
        "id": {"value": f"{final_id:.0f}" if final_id else None},
        "w": {"value": f"{final_w:.0f}" if final_w else None},
        "method_results": method_results,
        "strategy": strategy,
        "consensus": {
            "od_agreement": round(_agreement(od_votes, final_od), 2),
            "id_agreement": round(_agreement(id_votes, final_id), 2),
            "w_agreement": round(_agreement(w_votes, final_w), 2),
        },
    }
    if layout_info:
        result["layout"] = {
            "is_bearing": layout_info["is_bearing"],
            "excluded_dims": excluded_count,
        }
    return _apply_soft_filter(result, drawing_title)
