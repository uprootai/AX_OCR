#!/usr/bin/env python3
"""
DSE Bearing 순차 업로드 + 분석 (resume 지원)
각 도면을 하나씩 업로드 → 분석 → 결과 수집
"""

import requests
import json
import time
import sys
from pathlib import Path
from datetime import datetime

BOM_API = "http://localhost:5020"
PROJECT_ID = "b97237fd"
PNG_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs")
OUTPUT_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test")
RESULTS_FILE = OUTPUT_DIR / "results.json"
FEATURES = "dimension_ocr,table_extraction,bom_generation,title_block_ocr"

# Map PNG stem to category and full name
PDF_ROOT = Path("/home/uproot/ax/poc/apply-company/dsebearing/PJT/04_부품도면")
CATEGORIES = {
    "01_저널베어링": "Journal Bearing",
    "02_스러스트베어링": "Thrust Bearing",
    "03_체결부품": "Fastening Parts",
    "04_조정부품": "Adjustment Parts",
    "05_기타": "Others",
}


def build_pdf_map():
    """Build mapping from drawing number to PDF info."""
    mapping = {}
    for pdf in PDF_ROOT.rglob("*.pdf"):
        stem = pdf.stem.split(" ")[0]
        cat = pdf.parent.name
        mapping[stem] = {
            "full_name": pdf.stem,
            "category": cat,
            "category_en": CATEGORIES.get(cat, cat),
        }
    return mapping


def load_results():
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_results(results):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def wait_for_backend(max_wait=30):
    for _ in range(max_wait):
        try:
            r = requests.get(f"{BOM_API}/health", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def upload_and_analyze(png_path, pdf_info, idx, total):
    stem = png_path.stem
    result = {
        "index": idx,
        "drawing_number": stem,
        "full_name": pdf_info.get("full_name", stem),
        "category": pdf_info.get("category", "unknown"),
        "category_en": pdf_info.get("category_en", "unknown"),
        "png_size_kb": round(png_path.stat().st_size / 1024, 1),
        "timestamp": datetime.now().isoformat(),
    }

    print(f"[{idx}/{total}] {stem} ({result['category_en']})", flush=True)

    # Wait for backend to be ready
    if not wait_for_backend(60):
        result["error"] = "Backend not reachable"
        print(f"  ✗ Backend timeout", flush=True)
        return result

    # Upload
    try:
        url = f"{BOM_API}/sessions/upload"
        params = {
            "project_id": PROJECT_ID,
            "drawing_type": "mechanical",
            "features": FEATURES,
        }
        with open(png_path, "rb") as f:
            files = {"file": (png_path.name, f, "image/png")}
            resp = requests.post(url, params=params, files=files, timeout=120)

        if resp.status_code != 200:
            result["error"] = f"Upload {resp.status_code}: {resp.text[:200]}"
            print(f"  ✗ Upload failed: {resp.status_code}", flush=True)
            return result

        data = resp.json()
        session_id = data.get("session_id", "")
        result["session_id"] = session_id
        print(f"  ✓ Upload: {session_id[:8]}...", flush=True)
    except Exception as e:
        result["error"] = f"Upload: {str(e)[:200]}"
        print(f"  ✗ Upload: {e}", flush=True)
        return result

    # Analyze
    try:
        t0 = time.time()
        resp = requests.post(f"{BOM_API}/analysis/run/{session_id}", timeout=600)
        elapsed = time.time() - t0
        result["analysis_time_s"] = round(elapsed, 1)

        if resp.status_code != 200:
            result["error"] = f"Analysis {resp.status_code}: {resp.text[:200]}"
            print(f"  ✗ Analysis failed ({elapsed:.1f}s)", flush=True)
            return result

        analysis = resp.json()
        result["analysis_summary"] = {
            "dimensions": len(analysis.get("dimensions", [])),
            "detections": len(analysis.get("detections", [])),
            "processing_time_ms": analysis.get("processing_time_ms", 0),
            "errors": analysis.get("errors", []),
        }
        print(f"  ✓ Analysis: {elapsed:.1f}s", flush=True)
    except Exception as e:
        result["error"] = f"Analysis: {str(e)[:200]}"
        print(f"  ✗ Analysis: {e}", flush=True)
        return result

    # Get detail
    try:
        resp = requests.get(f"{BOM_API}/sessions/{session_id}", timeout=30)
        if resp.status_code == 200:
            detail = resp.json()
            dims = detail.get("dimensions", [])
            confs = [d.get("confidence", 0) for d in dims if "confidence" in d]
            avg_conf = sum(confs) / len(confs) if confs else 0

            result["metrics"] = {
                "status": detail.get("status", "?"),
                "dimensions_count": len(dims),
                "dimensions_avg_confidence": round(avg_conf * 100, 1),
                "texts_count": len(detail.get("texts", [])),
                "tables_count": len(detail.get("table_results", [])) if isinstance(detail.get("table_results"), list) else (1 if detail.get("table_results") else 0),
                "title_block_found": bool(detail.get("title_block")),
                "detections_count": len(detail.get("detections", [])),
            }
            m = result["metrics"]
            print(f"    치수={m['dimensions_count']}, 신뢰도={m['dimensions_avg_confidence']}%, "
                  f"텍스트={m['texts_count']}, 테이블={m['tables_count']}, "
                  f"TB={'Y' if m['title_block_found'] else 'N'}", flush=True)
    except Exception as e:
        print(f"  ⚠ Detail: {e}", flush=True)

    result["success"] = True
    return result


def main():
    pdf_map = build_pdf_map()
    pngs = sorted(PNG_DIR.glob("*.png"))
    print(f"Total PNGs: {len(pngs)}", flush=True)

    # Load existing results
    results = load_results()
    done = {r["drawing_number"] for r in results if r.get("success")}
    print(f"Already done: {len(done)}", flush=True)

    # Health check
    if not wait_for_backend(10):
        print("ERROR: Backend not reachable", flush=True)
        sys.exit(1)

    total = len(pngs)
    for idx, png in enumerate(pngs, 1):
        stem = png.stem
        if stem in done:
            print(f"[{idx}/{total}] {stem} — SKIP", flush=True)
            continue

        info = pdf_map.get(stem, {"full_name": stem, "category": "?", "category_en": "?"})
        result = upload_and_analyze(png, info, idx, total)
        results.append(result)
        save_results(results)

        # Small pause to let backend breathe
        time.sleep(1)

    # Summary
    success = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    print(f"\n{'='*60}", flush=True)
    print(f"DONE: {len(success)}/{len(results)} successful", flush=True)
    if failed:
        print(f"Failed: {[r['drawing_number'] for r in failed]}", flush=True)


if __name__ == "__main__":
    main()
