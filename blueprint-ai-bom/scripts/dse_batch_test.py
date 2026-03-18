#!/usr/bin/env python3
"""
DSE Bearing 전체 도면 배치 업로드 + 분석 테스트
==============================================
87개 PDF → PNG 변환 → BOM 세션 업로드 → 분석 실행 → 결과 수집
"""

import fitz  # PyMuPDF
import requests
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime

# Config
BOM_API = "http://localhost:5020"
PROJECT_ID = "b97237fd"
PDF_ROOT = Path("/home/uproot/ax/poc/apply-company/dsebearing/PJT/04_부품도면")
OUTPUT_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test")
REPORT_PATH = OUTPUT_DIR / "experiment_report.md"
PNG_DIR = OUTPUT_DIR / "converted_pngs"
DPI = 200  # PNG conversion resolution

# Features matching existing sessions
FEATURES = "dimension_ocr,table_extraction,bom_generation,title_block_ocr"

# Categories
CATEGORIES = {
    "01_저널베어링": "Journal Bearing",
    "02_스러스트베어링": "Thrust Bearing",
    "03_체결부품": "Fastening Parts",
    "04_조정부품": "Adjustment Parts",
    "05_기타": "Others",
}


def setup_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)


def convert_pdf_to_png(pdf_path: Path) -> Path:
    """Convert first page of PDF to PNG."""
    stem = pdf_path.stem.split(" ")[0]  # TD0062017 part only
    png_path = PNG_DIR / f"{stem}.png"

    if png_path.exists():
        return png_path

    doc = fitz.open(str(pdf_path))
    page = doc[0]
    mat = fitz.Matrix(DPI / 72, DPI / 72)
    pix = page.get_pixmap(matrix=mat)
    pix.save(str(png_path))
    doc.close()
    return png_path


def upload_session(png_path: Path) -> dict:
    """Upload PNG to BOM API and create session."""
    url = f"{BOM_API}/sessions/upload"
    params = {
        "project_id": PROJECT_ID,
        "drawing_type": "mechanical",
        "features": FEATURES,
    }

    with open(png_path, "rb") as f:
        files = {"file": (png_path.name, f, "image/png")}
        resp = requests.post(url, params=params, files=files, timeout=60)

    if resp.status_code != 200:
        return {"error": resp.text, "status_code": resp.status_code}

    return resp.json()


def run_analysis(session_id: str) -> dict:
    """Run analysis on a session."""
    url = f"{BOM_API}/analysis/run/{session_id}"
    resp = requests.post(url, timeout=300)  # 5 min timeout per drawing

    if resp.status_code != 200:
        return {"error": resp.text, "status_code": resp.status_code}

    return resp.json()


def get_session_detail(session_id: str) -> dict:
    """Get detailed session results."""
    url = f"{BOM_API}/sessions/{session_id}"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        return {"error": resp.text}
    return resp.json()


def extract_metrics(detail: dict) -> dict:
    """Extract key metrics from session detail."""
    dims = detail.get("dimensions", [])
    texts = detail.get("texts", [])
    tables = detail.get("table_results", [])
    title = detail.get("title_block", {})
    detections = detail.get("detections", [])

    dim_confidences = [d.get("confidence", 0) for d in dims if "confidence" in d]
    avg_conf = sum(dim_confidences) / len(dim_confidences) if dim_confidences else 0

    return {
        "status": detail.get("status", "unknown"),
        "dimensions_count": len(dims),
        "dimensions_avg_confidence": round(avg_conf * 100, 1),
        "texts_count": len(texts),
        "tables_count": len(tables) if isinstance(tables, list) else (1 if tables else 0),
        "title_block_found": bool(title),
        "detections_count": len(detections),
        "drawing_type": detail.get("drawing_type", "unknown"),
        "features": detail.get("features", []),
    }


def process_single(pdf_path: Path, idx: int, total: int) -> dict:
    """Process a single PDF: convert → upload → analyze → collect results."""
    stem = pdf_path.stem.split(" ")[0]
    full_name = pdf_path.stem
    category = pdf_path.parent.name

    result = {
        "index": idx,
        "drawing_number": stem,
        "full_name": full_name,
        "category": category,
        "category_en": CATEGORIES.get(category, category),
        "pdf_path": str(pdf_path),
        "timestamp": datetime.now().isoformat(),
    }

    print(f"\n[{idx}/{total}] {stem} ({CATEGORIES.get(category, category)})")

    # Step 1: Convert PDF → PNG
    try:
        png_path = convert_pdf_to_png(pdf_path)
        result["png_path"] = str(png_path)
        result["png_size_kb"] = round(png_path.stat().st_size / 1024, 1)
        print(f"  ✓ PDF→PNG: {result['png_size_kb']}KB")
    except Exception as e:
        result["error"] = f"PDF conversion failed: {e}"
        print(f"  ✗ PDF→PNG failed: {e}")
        return result

    # Step 2: Upload
    try:
        upload_resp = upload_session(png_path)
        if "error" in upload_resp:
            result["error"] = f"Upload failed: {upload_resp['error']}"
            print(f"  ✗ Upload failed: {upload_resp.get('status_code', '?')}")
            return result
        session_id = upload_resp.get("session_id", "")
        result["session_id"] = session_id
        print(f"  ✓ Upload: session={session_id[:8]}...")
    except Exception as e:
        result["error"] = f"Upload exception: {e}"
        print(f"  ✗ Upload exception: {e}")
        return result

    # Step 3: Analyze
    try:
        t0 = time.time()
        analysis_resp = run_analysis(session_id)
        elapsed = time.time() - t0
        result["analysis_time_s"] = round(elapsed, 1)

        if "error" in analysis_resp:
            result["error"] = f"Analysis failed: {analysis_resp['error']}"
            print(f"  ✗ Analysis failed ({elapsed:.1f}s)")
            return result

        result["analysis_raw"] = {
            "dimensions": len(analysis_resp.get("dimensions", [])),
            "detections": len(analysis_resp.get("detections", [])),
            "processing_time_ms": analysis_resp.get("processing_time_ms", 0),
            "errors": analysis_resp.get("errors", []),
        }
        print(f"  ✓ Analysis: {elapsed:.1f}s")
    except Exception as e:
        result["error"] = f"Analysis exception: {e}"
        print(f"  ✗ Analysis exception: {e}")
        return result

    # Step 4: Get detailed results
    try:
        detail = get_session_detail(session_id)
        if "error" not in detail:
            metrics = extract_metrics(detail)
            result["metrics"] = metrics
            print(f"    치수={metrics['dimensions_count']}, "
                  f"신뢰도={metrics['dimensions_avg_confidence']}%, "
                  f"텍스트={metrics['texts_count']}, "
                  f"테이블={metrics['tables_count']}, "
                  f"타이틀블록={'✓' if metrics['title_block_found'] else '✗'}")
    except Exception as e:
        print(f"  ⚠ Detail fetch failed: {e}")

    result["success"] = True
    return result


def generate_report(results: list):
    """Generate experiment report in markdown."""
    total = len(results)
    success = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    # Aggregate stats
    total_dims = sum(r.get("metrics", {}).get("dimensions_count", 0) for r in success)
    total_texts = sum(r.get("metrics", {}).get("texts_count", 0) for r in success)
    total_tables = sum(r.get("metrics", {}).get("tables_count", 0) for r in success)
    title_blocks = sum(1 for r in success if r.get("metrics", {}).get("title_block_found"))
    avg_time = sum(r.get("analysis_time_s", 0) for r in success) / len(success) if success else 0
    total_time = sum(r.get("analysis_time_s", 0) for r in success)

    confidences = [r.get("metrics", {}).get("dimensions_avg_confidence", 0) for r in success if r.get("metrics", {}).get("dimensions_count", 0) > 0]
    overall_avg_conf = sum(confidences) / len(confidences) if confidences else 0

    # Category breakdown
    cat_stats = {}
    for r in results:
        cat = r.get("category_en", "Unknown")
        if cat not in cat_stats:
            cat_stats[cat] = {"total": 0, "success": 0, "dims": 0, "texts": 0, "tables": 0, "time": 0, "confs": []}
        cat_stats[cat]["total"] += 1
        if r.get("success"):
            cat_stats[cat]["success"] += 1
            m = r.get("metrics", {})
            cat_stats[cat]["dims"] += m.get("dimensions_count", 0)
            cat_stats[cat]["texts"] += m.get("texts_count", 0)
            cat_stats[cat]["tables"] += m.get("tables_count", 0)
            cat_stats[cat]["time"] += r.get("analysis_time_s", 0)
            if m.get("dimensions_count", 0) > 0:
                cat_stats[cat]["confs"].append(m.get("dimensions_avg_confidence", 0))

    report = f"""# DSE Bearing 전체 도면 배치 분석 실험 보고서

> 동서기연 터빈 베어링 87개 부품도면 전수 분석 결과

**실험일시**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**프로젝트**: b97237fd (동서기연 베어링 자료 분석)
**분석 기능**: dimension_ocr, table_extraction, bom_generation, title_block_ocr

---

## 1. 전체 요약

| 항목 | 값 |
|------|-----|
| 전체 도면 수 | {total}개 |
| 성공 | {len(success)}개 ({len(success)/total*100:.1f}%) |
| 실패 | {len(failed)}개 ({len(failed)/total*100:.1f}%) |
| 총 추출 치수 | {total_dims}개 |
| 총 추출 텍스트 | {total_texts}개 |
| 총 추출 테이블 | {total_tables}개 |
| 타이틀블록 검출 | {title_blocks}/{len(success)} ({title_blocks/len(success)*100:.1f}%) |
| 평균 치수 신뢰도 | {overall_avg_conf:.1f}% |
| 평균 분석 시간 | {avg_time:.1f}초 |
| 총 분석 시간 | {total_time:.0f}초 ({total_time/60:.1f}분) |

---

## 2. 카테고리별 분석

| 카테고리 | 도면 수 | 성공 | 치수 | 텍스트 | 테이블 | 평균 신뢰도 | 총 시간 |
|---------|--------|------|------|--------|--------|-----------|--------|
"""

    for cat_name in ["Journal Bearing", "Thrust Bearing", "Fastening Parts", "Adjustment Parts", "Others"]:
        s = cat_stats.get(cat_name, {"total": 0, "success": 0, "dims": 0, "texts": 0, "tables": 0, "time": 0, "confs": []})
        avg_c = sum(s["confs"]) / len(s["confs"]) if s["confs"] else 0
        report += f"| {cat_name} | {s['total']} | {s['success']} | {s['dims']} | {s['texts']} | {s['tables']} | {avg_c:.1f}% | {s['time']:.0f}s |\n"

    report += f"""
---

## 3. 개별 도면 상세 결과

| # | 도면번호 | 카테고리 | 치수 | 신뢰도 | 텍스트 | 테이블 | TB | 시간 | 상태 |
|---|---------|---------|------|--------|--------|--------|---|------|------|
"""

    for r in results:
        idx = r["index"]
        dn = r["drawing_number"]
        cat = r.get("category_en", "?")[:8]
        if r.get("success"):
            m = r.get("metrics", {})
            dims = m.get("dimensions_count", 0)
            conf = m.get("dimensions_avg_confidence", 0)
            texts = m.get("texts_count", 0)
            tables = m.get("tables_count", 0)
            tb = "Y" if m.get("title_block_found") else "N"
            t = r.get("analysis_time_s", 0)
            report += f"| {idx} | {dn} | {cat} | {dims} | {conf:.0f}% | {texts} | {tables} | {tb} | {t:.1f}s | ✅ |\n"
        else:
            err = r.get("error", "unknown")[:40]
            report += f"| {idx} | {dn} | {cat} | - | - | - | - | - | - | ❌ {err} |\n"

    # Failures section
    if failed:
        report += f"""
---

## 4. 실패 분석

| # | 도면번호 | 원인 |
|---|---------|------|
"""
        for r in failed:
            report += f"| {r['index']} | {r['drawing_number']} | {r.get('error', 'unknown')} |\n"

    # Distribution analysis
    dim_counts = [r.get("metrics", {}).get("dimensions_count", 0) for r in success]
    if dim_counts:
        report += f"""
---

## 5. 치수 추출 분포

| 구간 | 도면 수 |
|------|--------|
| 0개 (치수 없음) | {sum(1 for d in dim_counts if d == 0)} |
| 1~10개 | {sum(1 for d in dim_counts if 1 <= d <= 10)} |
| 11~30개 | {sum(1 for d in dim_counts if 11 <= d <= 30)} |
| 31~50개 | {sum(1 for d in dim_counts if 31 <= d <= 50)} |
| 51~80개 | {sum(1 for d in dim_counts if 51 <= d <= 80)} |
| 81개 이상 | {sum(1 for d in dim_counts if d > 80)} |
"""

    # Top/Bottom performers
    by_dims = sorted(success, key=lambda r: r.get("metrics", {}).get("dimensions_count", 0), reverse=True)
    if by_dims:
        report += f"""
---

## 6. 치수 추출 TOP 10

| # | 도면번호 | 이름 | 치수 수 | 신뢰도 |
|---|---------|------|--------|--------|
"""
        for i, r in enumerate(by_dims[:10], 1):
            m = r.get("metrics", {})
            report += f"| {i} | {r['drawing_number']} | {r['full_name'][:50]} | {m.get('dimensions_count', 0)} | {m.get('dimensions_avg_confidence', 0):.0f}% |\n"

    # Low confidence items
    low_conf = [r for r in success if r.get("metrics", {}).get("dimensions_count", 0) > 0 and r.get("metrics", {}).get("dimensions_avg_confidence", 0) < 70]
    if low_conf:
        report += f"""
---

## 7. 저신뢰도 도면 (70% 미만)

| 도면번호 | 이름 | 치수 수 | 신뢰도 |
|---------|------|--------|--------|
"""
        for r in sorted(low_conf, key=lambda x: x.get("metrics", {}).get("dimensions_avg_confidence", 0)):
            m = r.get("metrics", {})
            report += f"| {r['drawing_number']} | {r['full_name'][:50]} | {m.get('dimensions_count', 0)} | {m.get('dimensions_avg_confidence', 0):.1f}% |\n"

    report += f"""
---

## 8. 결론

- 전체 {total}개 도면 중 {len(success)}개 성공 ({len(success)/total*100:.1f}%)
- 총 {total_dims}개 치수 자동 추출, 평균 신뢰도 {overall_avg_conf:.1f}%
- 총 분석 시간 {total_time/60:.1f}분 (평균 {avg_time:.1f}초/도면)
- 타이틀블록 검출률 {title_blocks/len(success)*100:.1f}%

---

*Generated by dse_batch_test.py — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print(f"Report saved to: {REPORT_PATH}")


def main():
    setup_dirs()

    # Collect all PDFs
    pdfs = sorted(PDF_ROOT.rglob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs in {PDF_ROOT}")

    # Check API health
    try:
        resp = requests.get(f"{BOM_API}/health", timeout=5)
        print(f"BOM API health: {resp.status_code}")
    except Exception as e:
        print(f"ERROR: BOM API not reachable: {e}")
        sys.exit(1)

    # Load previous results (resume support)
    results_file = OUTPUT_DIR / "results.json"
    existing = {}
    if results_file.exists():
        with open(results_file, "r", encoding="utf-8") as f:
            prev = json.load(f)
            for r in prev:
                if r.get("success"):
                    existing[r["drawing_number"]] = r

    print(f"Resuming: {len(existing)} already successful, skipping those")

    # Process each PDF
    results = list(existing.values())
    for idx, pdf in enumerate(pdfs, 1):
        stem = pdf.stem.split(" ")[0]
        if stem in existing:
            print(f"[{idx}/{len(pdfs)}] {stem} — SKIP (already done)")
            continue
        result = process_single(pdf, idx, len(pdfs))
        results.append(result)

        # Save intermediate results
        with open(OUTPUT_DIR / "results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    # Generate report
    generate_report(results)

    # Print summary
    success = sum(1 for r in results if r.get("success"))
    print(f"\n{'='*60}")
    print(f"DONE: {success}/{len(results)} successful")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
