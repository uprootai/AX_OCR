#!/usr/bin/env python3
"""앙상블 v6 평가 — SEC 메서드 기여도 측정

GT 7건 ASSY 도면에 대해:
1. run_ensemble() WITHOUT SEC (기존 v5)
2. run_ensemble() WITH SEC (v6)
→ OD/ID/W 정확도 비교

비ASSY 도면 10건 샘플에 대해:
→ SEC 비활성화 확인 (ASSY 아니면 SEC 스킵)
"""

import json
import re
import sys
import os

# 백엔드 모듈 임포트를 위한 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

GT = {
    "TD0062015": {"name": "T1", "od": 360, "id": 190, "w": 200,
                  "title": "T1 BEARING ASSY(360X190)"},
    "TD0062021": {"name": "T2", "od": 380, "id": 190, "w": 200,
                  "title": "T2 BEARING ASSY(380X190)"},
    "TD0062026": {"name": "T3", "od": 380, "id": 260, "w": 260,
                  "title": "T3 BEARING ASSY(380X260)"},
    "TD0062031": {"name": "T4", "od": 420, "id": 260, "w": 260,
                  "title": "T4 BEARING ASSY (420x260)"},
    "TD0062037": {"name": "T5", "od": 1036, "id": 580, "w": 200,
                  "title": "T5 BEARING ASSY(460x260)"},
    "TD0062050": {"name": "T8", "od": 500, "id": 260, "w": 200,
                  "title": "T8 BEARING ASSY 500x260"},
    "TD0062055": {"name": "Thrust", "od": 515, "id": 440, "w": 48,
                  "title": "THRUST BEARING ASSY(OD670XID440)"},
}

PNG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "dse_batch_test", "converted_pngs")


def _extract_num(val_str):
    if val_str is None:
        return None
    cleaned = re.sub(r"[ØøΦ⌀∅()R]", "", str(val_str))
    m = re.search(r"(\d+\.?\d*)", cleaned)
    if m:
        try:
            return float(m.group(1))
        except (ValueError, TypeError):
            return None
    return None


def _match(extracted, gt_val, tol=0.05):
    if extracted is None or gt_val is None:
        return False
    return abs(extracted - gt_val) / max(gt_val, 1) < tol


def run():
    from services.dimension_ensemble import run_ensemble

    print("=" * 90)
    print("  앙상블 v6 평가 — SEC 메서드 기여도")
    print("=" * 90)

    # v5 vs v6 비교
    v5_od = v5_id = v5_w = 0
    v6_od = v6_id = v6_w = 0
    total = 0

    for drawing_no, gt in GT.items():
        png_path = os.path.join(PNG_DIR, f"{drawing_no}.png")
        if not os.path.exists(png_path):
            print(f"\n  ⚠ {drawing_no} PNG 없음")
            continue

        total += 1
        print(f"\n{'─' * 70}")
        print(f"  {gt['name']} ({drawing_no})  GT: OD={gt['od']} ID={gt['id']} W={gt['w']}")

        # v5: SEC 없이 (drawing_title에 ASSY 안 넣음)
        try:
            r5 = run_ensemble(png_path, drawing_title="")
            r5_od = _extract_num(r5.get("od", {}).get("value"))
            r5_id = _extract_num(r5.get("id", {}).get("value"))
            r5_w = _extract_num(r5.get("w", {}).get("value"))
            r5_strategy = r5.get("strategy", "?")
            r5_methods = list(r5.get("method_results", {}).keys())
        except Exception as e:
            print(f"  v5 실패: {e}")
            r5_od = r5_id = r5_w = None
            r5_strategy = "error"
            r5_methods = []

        # v6: SEC 포함 (drawing_title에 ASSY 포함)
        try:
            r6 = run_ensemble(png_path, drawing_title=gt["title"])
            r6_od = _extract_num(r6.get("od", {}).get("value"))
            r6_id = _extract_num(r6.get("id", {}).get("value"))
            r6_w = _extract_num(r6.get("w", {}).get("value"))
            r6_strategy = r6.get("strategy", "?")
            r6_methods = list(r6.get("method_results", {}).keys())
            sec_result = r6.get("method_results", {}).get("SEC", {})
        except Exception as e:
            print(f"  v6 실패: {e}")
            r6_od = r6_id = r6_w = None
            r6_strategy = "error"
            r6_methods = []
            sec_result = {}

        # GT 비교
        v5_od_m = _match(r5_od, gt["od"])
        v5_id_m = _match(r5_id, gt["id"])
        v5_w_m = _match(r5_w, gt["w"])

        v6_od_m = _match(r6_od, gt["od"])
        v6_id_m = _match(r6_id, gt["id"])
        v6_w_m = _match(r6_w, gt["w"])

        v5_od += v5_od_m; v5_id += v5_id_m; v5_w += v5_w_m
        v6_od += v6_od_m; v6_id += v6_id_m; v6_w += v6_w_m

        m = lambda x: "✓" if x else "✗"

        print(f"  v5: OD={r5_od} ID={r5_id} W={r5_w}  [{r5_strategy}] methods={r5_methods}")
        print(f"      OD {m(v5_od_m)} | ID {m(v5_id_m)} | W {m(v5_w_m)}")
        print(f"  v6: OD={r6_od} ID={r6_id} W={r6_w}  [{r6_strategy}] methods={r6_methods}")
        print(f"      OD {m(v6_od_m)} | ID {m(v6_id_m)} | W {m(v6_w_m)}")
        if sec_result:
            print(f"  SEC: OD={sec_result.get('od')} ID={sec_result.get('id')} W={sec_result.get('w')}")

    # 요약
    print(f"\n{'=' * 90}")
    print(f"  GT {total}건 비교")
    print(f"  {'':15} {'OD':>8} {'ID':>8} {'W':>8}")
    print(f"  {'v5 (SEC 없음)':15} {f'{v5_od}/{total}':>8} {f'{v5_id}/{total}':>8} {f'{v5_w}/{total}':>8}")
    print(f"  {'v6 (SEC 포함)':15} {f'{v6_od}/{total}':>8} {f'{v6_id}/{total}':>8} {f'{v6_w}/{total}':>8}")
    print(f"{'=' * 90}")


if __name__ == "__main__":
    run()
