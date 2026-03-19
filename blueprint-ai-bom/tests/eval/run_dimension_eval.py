#!/usr/bin/env python3
"""Dimension Lab Eval Runner — OD/ID/W 분류 정확도 자동 검증 및 벤치마크.

Usage:
    python3 run_dimension_eval.py
    python3 run_dimension_eval.py --benchmark /tmp/dimension_eval_results.json
    python3 run_dimension_eval.py --cases custom_cases.json
    python3 run_dimension_eval.py --base-url http://remote:5020
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

DEFAULT_BASE_URL = "http://localhost:5020"
CASES_FILE = Path(__file__).parent / "dimension_eval_cases.json"
RESULTS_FILE = Path("/tmp/dimension_eval_results.json")
TOLERANCE = 0.5  # same as backend _value_matches

OCR_ENGINES = [
    "paddleocr", "edocr2", "easyocr", "trocr",
    "suryaocr", "doctr", "paddleocr_tiled",
]
METHOD_IDS = [
    "diameter_symbol", "dimension_type", "catalog", "composite_signal",
    "position_width", "session_ref", "tolerance_fit", "value_ranking",
    "heuristic", "full_pipeline",
]


def _val_match(extracted: Optional[str], gt: float) -> Optional[bool]:
    """Check if extracted value matches ground truth within tolerance."""
    if extracted is None:
        return None
    try:
        raw = extracted.lstrip("RrOoØø ").strip()
        ext = float(raw)
        if abs(ext - gt) < TOLERANCE:
            return True
        if extracted.upper().startswith("R") and not extracted.upper().startswith("RA"):
            if abs(ext * 2 - gt) < TOLERANCE:
                return True
        return False
    except (ValueError, AttributeError):
        return False


def _color(text: str, ok: Optional[bool]) -> str:
    if ok is True:
        return f"\033[92m{text}\033[0m"
    if ok is False:
        return f"\033[91m{text}\033[0m"
    return f"\033[90m{text}\033[0m"


async def run_case(client: httpx.AsyncClient, case: dict, base_url: str) -> dict:
    """Upload image, set GT, run full-compare, return scored result."""
    case_id, gt = case["case_id"], case["ground_truth"]
    image_path = Path(case["image_path"])
    t0 = time.time()

    if not image_path.exists():
        return {"case_id": case_id, "error": f"Image not found: {image_path}", "cells": []}

    # 1) Upload image
    with open(image_path, "rb") as f:
        resp = await client.post(
            f"{base_url}/sessions/upload",
            files={"file": (image_path.name, f, "image/png")},
            params={"drawing_type": "mechanical"},
            timeout=30,
        )
    if resp.status_code != 200:
        return {"case_id": case_id, "error": f"Upload failed: {resp.status_code}", "cells": []}
    session_id = resp.json()["session_id"]

    # 2) Set ground truth
    dummy_bbox = {"x1": 0, "y1": 0, "x2": 1, "y2": 1}
    gt_dims = [
        {"role": r, "value": str(gt[r]), "bbox": dummy_bbox}
        for r in ("od", "id", "w")
    ]
    await client.post(
        f"{base_url}/analysis/dimensions/{session_id}/ground-truth",
        json={"dimensions": gt_dims}, timeout=10,
    )

    # 3) Full compare (7 engines x 10 methods)
    resp = await client.post(
        f"{base_url}/analysis/dimensions/full-compare",
        json={"session_id": session_id, "ocr_engines": OCR_ENGINES,
              "confidence_threshold": 0.5},
        timeout=120,
    )
    elapsed_ms = round((time.time() - t0) * 1000, 1)
    if resp.status_code != 200:
        return {"case_id": case_id, "error": f"full-compare {resp.status_code}", "cells": []}

    data = resp.json()
    cells = []
    for cell in data.get("matrix", []):
        od_ok = _val_match(cell.get("od"), gt["od"])
        id_ok = _val_match(cell.get("id_val"), gt["id"])
        w_ok = _val_match(cell.get("width"), gt["w"])
        checks = [v for v in [od_ok, id_ok, w_ok] if v is not None]
        score = sum(1 for c in checks if c) / len(checks) if checks else 0.0
        cells.append({
            "engine": cell["engine"], "method": cell["method_id"],
            "od": cell.get("od"), "id_val": cell.get("id_val"),
            "width": cell.get("width"),
            "od_ok": od_ok, "id_ok": id_ok, "w_ok": w_ok,
            "score": round(score, 3),
        })

    return {
        "case_id": case_id, "session_id": session_id,
        "elapsed_ms": elapsed_ms,
        "engine_times": data.get("engine_times", {}),
        "cells": cells, "error": None,
    }


def aggregate(results: list) -> dict:
    """Compute per-method and per-engine accuracy."""
    method_stats: dict = {}
    engine_stats: dict = {}
    total_pass = total_cells = 0

    for r in results:
        for cell in r.get("cells", []):
            s = cell["score"]
            for key, bucket in [("method", method_stats), ("engine", engine_stats)]:
                k = cell[key]
                bucket.setdefault(k, {"sum": 0, "n": 0})
                bucket[k]["sum"] += s
                bucket[k]["n"] += 1
            if s == 1.0:
                total_pass += 1
            total_cells += 1

    def _acc(d: dict) -> dict:
        return {k: round(v["sum"] / v["n"], 3) if v["n"] else 0 for k, v in d.items()}

    return {
        "overall_accuracy": round(total_pass / total_cells, 3) if total_cells else 0,
        "total_cells": total_cells, "perfect_cells": total_pass,
        "method_accuracy": _acc(method_stats),
        "engine_accuracy": _acc(engine_stats),
    }


def print_report(results: list, agg: dict) -> None:
    print("\n" + "=" * 72)
    print("  Dimension Lab Eval Report")
    print("=" * 72)

    for r in results:
        cid = r["case_id"]
        if r.get("error"):
            print(f"\n  [{cid}] ERROR: {r['error']}")
            continue
        print(f"\n  [{cid}]  latency={r['elapsed_ms']}ms")
        by_method: dict = {}
        for cell in r["cells"]:
            by_method.setdefault(cell["method"], []).append(cell)
        for mth in METHOD_IDS:
            cells = by_method.get(mth, [])
            passes = sum(1 for c in cells if c["score"] == 1.0)
            print(f"    {mth:24s}  {passes}/{len(cells)}")

    # Aggregate per method
    print("\n" + "-" * 72)
    print("  Aggregate (per method)")
    for mth, acc in sorted(agg["method_accuracy"].items(), key=lambda x: -x[1]):
        print(f"    {mth:24s}  {acc:.1%}  {'#' * int(acc * 20)}")

    print("\n  Aggregate (per engine)")
    for eng, acc in sorted(agg["engine_accuracy"].items(), key=lambda x: -x[1]):
        print(f"    {eng:24s}  {acc:.1%}  {'#' * int(acc * 20)}")

    print(f"\n  Overall: {agg['overall_accuracy']:.1%} "
          f"({agg['perfect_cells']}/{agg['total_cells']} perfect cells)")
    print("=" * 72 + "\n")


def print_benchmark(current: dict, prev: dict) -> None:
    print("\n" + "=" * 72)
    print("  Benchmark Comparison (current vs previous)")
    print("=" * 72)

    c_agg, p_agg = current["aggregate"], prev.get("aggregate", {})
    c_o, p_o = c_agg.get("overall_accuracy", 0), p_agg.get("overall_accuracy", 0)
    d = c_o - p_o
    print(f"\n  Overall:  {p_o:.1%} -> {c_o:.1%}  ({'+' if d >= 0 else ''}{d:.1%})")

    print("\n  Per-method delta:")
    c_m, p_m = c_agg.get("method_accuracy", {}), p_agg.get("method_accuracy", {})
    for mth in sorted(set(list(c_m) + list(p_m))):
        cv, pv = c_m.get(mth, 0), p_m.get(mth, 0)
        delta = cv - pv
        sign = "+" if delta >= 0 else ""
        ok = True if delta > 0.001 else (False if delta < -0.001 else None)
        print(f"    {mth:24s}  {pv:.1%} -> {cv:.1%}  {_color(f'{sign}{delta:.1%}', ok)}")
    print("=" * 72 + "\n")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Dimension Lab Eval Runner")
    parser.add_argument("--cases", default=str(CASES_FILE), help="Eval cases JSON path")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend base URL")
    parser.add_argument("--benchmark", default=None, help="Previous results JSON for comparison")
    parser.add_argument("--output", default=str(RESULTS_FILE), help="Output results path")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    if not cases_path.exists():
        print(f"ERROR: Cases file not found: {cases_path}", file=sys.stderr)
        sys.exit(1)
    cases = json.loads(cases_path.read_text())
    print(f"Loaded {len(cases)} eval cases from {cases_path}")

    # Health check
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{args.base_url}/health", timeout=5)
            if r.status_code != 200:
                print(f"WARNING: Health check returned {r.status_code}", file=sys.stderr)
        except httpx.ConnectError:
            print(f"ERROR: Cannot connect to {args.base_url}", file=sys.stderr)
            sys.exit(1)

    # Run eval sequentially (avoid overloading OCR engines)
    results = []
    async with httpx.AsyncClient() as client:
        for i, case in enumerate(cases):
            print(f"  [{i+1}/{len(cases)}] Running {case['case_id']}...", end=" ", flush=True)
            result = await run_case(client, case, args.base_url)
            if result.get("error"):
                print(f"ERROR: {result['error']}")
            else:
                passes = sum(1 for c in result["cells"] if c["score"] == 1.0)
                print(f"done ({result['elapsed_ms']}ms, {passes}/{len(result['cells'])} perfect)")
            results.append(result)

    agg = aggregate(results)
    print_report(results, agg)

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "base_url": args.base_url, "cases_file": str(cases_path),
        "results": results, "aggregate": agg,
    }
    Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"Results saved to {args.output}")

    # Benchmark comparison
    if args.benchmark:
        prev_path = Path(args.benchmark)
        if prev_path.exists():
            print_benchmark(output, json.loads(prev_path.read_text()))
        else:
            print(f"WARNING: Benchmark file not found: {prev_path}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
