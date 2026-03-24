"""Test enhanced ensemble (K+S01+S02+S06) on T5 and batch."""
import os
import sys
import json
import time

# Docker 내부 호스트명 → localhost로 매핑 (호스트에서 실행 시)
os.environ.setdefault('PADDLEOCR_API_URL', 'http://localhost:5006')
os.environ.setdefault('EASYOCR_API_URL', 'http://localhost:5007')
os.environ.setdefault('TROCR_API_URL', 'http://localhost:5008')
os.environ.setdefault('SURYAOCR_API_URL', 'http://localhost:5009')
os.environ.setdefault('EDOCR2_API_URL', 'http://localhost:5002')
os.environ.setdefault('LINE_DETECTOR_API_URL', 'http://localhost:5004')

sys.path.insert(0, '/home/uproot/ax/poc/blueprint-ai-bom/backend')

from services.dimension_ensemble import run_ensemble
from pathlib import Path

DATA_DIR = Path('/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs')

# Single test: T5
print('=== T5 (TD0062037) — GT: OD=Ø1036, ID=580, W=200 ===')
t5 = DATA_DIR / 'TD0062037.png'
result = run_ensemble(str(t5))
print(f'OD: {result["od"]["value"] if result.get("od") else "—"}')
print(f'ID: {result["id"]["value"] if result.get("id") else "—"}')
print(f'W:  {result["w"]["value"] if result.get("w") else "—"}')
print(f'Methods: {list(result.get("method_results", {}).keys())}')
for m, r in result.get("method_results", {}).items():
    print(f'  {m}: OD={r.get("od")} ID={r.get("id")} W={r.get("w")}')
print(f'Consensus: {result.get("consensus", {})}')

# Batch test
print('\n=== Batch test (87 drawings) ===')
png_files = sorted(DATA_DIR.glob('*.png'))
results = {}
start = time.time()

for i, f in enumerate(png_files):
    try:
        r = run_ensemble(str(f))
        results[f.stem] = {
            "od": r["od"]["value"] if r.get("od") and r["od"].get("value") else None,
            "id": r["id"]["value"] if r.get("id") and r["id"].get("value") else None,
            "w": r["w"]["value"] if r.get("w") and r["w"].get("value") else None,
            "methods": list(r.get("method_results", {}).keys()),
            "has_s06": "S06" in r.get("method_results", {}),
        }
    except Exception as e:
        results[f.stem] = {"od": None, "id": None, "w": None, "error": str(e)}
    if (i + 1) % 20 == 0:
        elapsed = time.time() - start
        print(f'  {i+1}/{len(png_files)} ({elapsed:.0f}s)')

elapsed = time.time() - start

# Stats
has_od = sum(1 for r in results.values() if r.get("od"))
has_id = sum(1 for r in results.values() if r.get("id"))
has_w = sum(1 for r in results.values() if r.get("w"))
has_all = sum(1 for r in results.values() if r.get("od") and r.get("id") and r.get("w"))
has_s06 = sum(1 for r in results.values() if r.get("has_s06"))

print(f'\nResults ({elapsed:.0f}s total, {elapsed/len(png_files):.1f}s/drawing):')
print(f'  OD detected: {has_od}/87 ({has_od/87*100:.0f}%)')
print(f'  ID detected: {has_id}/87 ({has_id/87*100:.0f}%)')
print(f'  W detected:  {has_w}/87 ({has_w/87*100:.0f}%)')
print(f'  All 3:       {has_all}/87 ({has_all/87*100:.0f}%)')
print(f'  S06 contributed: {has_s06}/87')

# Compare with previous ensemble
prev_path = Path('/tmp/batch_ensemble_results.json')
if prev_path.exists():
    prev = json.loads(prev_path.read_text())
    prev_all = sum(1 for r in prev.values() if r.get("od") and r.get("id") and r.get("w"))
    print(f'\n  Previous (K+S01+S02): {prev_all}/87 ({prev_all/87*100:.0f}%)')
    print(f'  Current (K+S01+S02+S06): {has_all}/87 ({has_all/87*100:.0f}%)')
    print(f'  Improvement: +{has_all - prev_all}')

# Save
out_path = Path('/tmp/batch_ensemble_v2_results.json')
out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(f'\nSaved to {out_path}')
