"""Extract Ground Truth candidates from drawing title blocks via OCR.

Bearing drawing titles often contain dimension specs like:
- "T5 BEARING ASSY (460X260)" → OD~460+, W=260(?)
- "THRUST BEARING (515X440X250)" → OD=515, ID=440, W=250
- Part numbers with spec: "6030-2RS" → OD=225, ID=150, W=35

We use PaddleOCR to read title blocks and extract dimensional specs,
then cross-reference with v2 ensemble results.
"""
import json, re, time, os, requests
from pathlib import Path

os.environ.setdefault('PADDLEOCR_API_URL', 'http://localhost:5006')

DATA_DIR = Path('/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs')
OCR_URL = 'http://localhost:5006/api/v1/ocr'
V2_RESULTS = Path('/tmp/batch_ensemble_v2_results.json')

# Known GT
KNOWN_GT = {
    'TD0062037': {'od': 1036, 'id': 580, 'w': 200, 'source': 'manual'},
}

# Load v2 results
v2 = json.loads(V2_RESULTS.read_text()) if V2_RESULTS.exists() else {}

def _check(detected, gt_val, tol=5):
    """Check if detected value matches GT within tolerance."""
    if detected is None or gt_val is None:
        return False
    nums = re.findall(r'[\d.]+', str(detected))
    if not nums:
        return False
    return abs(float(nums[0]) - gt_val) <= tol

print(f'=== GT Extraction from Title Blocks ===\n')
png_files = sorted(DATA_DIR.glob('*.png'))

gt_candidates = {}
start = time.time()

for i, f in enumerate(png_files):
    try:
        with open(f, 'rb') as fh:
            resp = requests.post(OCR_URL, files={'file': fh}, timeout=20)
        if resp.status_code != 200:
            continue
        dets = resp.json().get('detections', [])
    except Exception:
        continue

    texts = [d['text'] for d in dets]
    full_text = ' '.join(texts)

    # Look for bearing spec patterns in title block
    specs = {}

    # Pattern 1: "BEARING ASSY (NNNxNNN)" or "(NNNxNNNxNNN)"
    m = re.search(r'\((\d{2,4})\s*[xX×]\s*(\d{2,4})\s*[xX×]\s*(\d{2,4})\)', full_text)
    if m:
        vals = sorted([int(m.group(1)), int(m.group(2)), int(m.group(3))], reverse=True)
        specs = {'od': vals[0], 'id': vals[1], 'w': vals[2], 'pattern': '3-dim'}

    if not specs:
        m = re.search(r'\((\d{2,4})\s*[xX×]\s*(\d{2,4})\)', full_text)
        if m:
            v1, v2_val = int(m.group(1)), int(m.group(2))
            specs = {'dims': sorted([v1, v2_val], reverse=True), 'pattern': '2-dim'}

    # Pattern 2: Bearing part number "NNNN-2RS" or "NNNN/NNN"
    m = re.search(r'\b(\d{3,5})[-/](\d{2,4})', full_text)
    if m and not specs:
        specs = {'part_ref': f'{m.group(1)}/{m.group(2)}', 'pattern': 'part-number'}

    # Pattern 3: Look for "OD" "ID" "W" labels near numbers
    for text in texts:
        if re.match(r'(?:O\.?D|OUTER)\s*[:=]?\s*(\d{2,4})', text, re.I):
            specs.setdefault('od', int(re.search(r'(\d{2,4})', text).group(1)))
        if re.match(r'(?:I\.?D|INNER|BORE)\s*[:=]?\s*(\d{2,4})', text, re.I):
            specs.setdefault('id', int(re.search(r'(\d{2,4})', text).group(1)))

    # Pattern 4: Title text like "T5 BEARING ASSY", "THRUST BEARING"
    bearing_type = None
    for text in texts:
        if 'BEARING' in text.upper():
            bearing_type = text.strip()
            break

    gt_candidates[f.stem] = {
        'specs': specs,
        'bearing_type': bearing_type,
        'n_texts': len(texts),
    }

    if (i + 1) % 20 == 0:
        print(f'  {i+1}/{len(png_files)} ({time.time()-start:.0f}s)')

elapsed = time.time() - start
print(f'\nDone in {elapsed:.0f}s\n')

# --- Analysis ---
has_specs = {k: v for k, v in gt_candidates.items() if v['specs']}
has_bearing = {k: v for k, v in gt_candidates.items() if v['bearing_type']}

print(f'Drawings with dimension specs: {len(has_specs)}/{len(gt_candidates)}')
print(f'Drawings with BEARING in title: {len(has_bearing)}/{len(gt_candidates)}')

# Show spec findings
print(f'\n=== Dimension Specs Found ===')
for name, v in sorted(has_specs.items()):
    spec = v['specs']
    bt = v['bearing_type'] or ''
    # Cross-reference with v2 result
    v2r = v2.get(name, {})
    v2_od = v2r.get('od', '—')
    v2_id = v2r.get('id', '—')
    v2_w = v2r.get('w', '—')
    print(f'  {name}: spec={spec} | title="{bt}"')
    print(f'    v2: OD={v2_od} ID={v2_id} W={v2_w}')

# Show bearing type titles
print(f'\n=== Bearing Types ===')
for name, v in sorted(has_bearing.items()):
    bt = v['bearing_type']
    spec = v['specs']
    print(f'  {name}: "{bt}" {spec if spec else ""}')

# Non-bearing candidates (no BEARING in title, no specs)
no_bearing = {k: v for k, v in gt_candidates.items()
              if not v['bearing_type'] and not v['specs']}
print(f'\n=== No bearing keyword, no specs: {len(no_bearing)} ===')
for name in sorted(no_bearing.keys()):
    v2r = v2.get(name, {})
    v2_od = v2r.get('od', '—')
    print(f'  {name}: v2 OD={v2_od}')

# Build GT from known + title specs
gt_final = dict(KNOWN_GT)
for name, v in has_specs.items():
    spec = v['specs']
    if 'od' in spec and 'id' in spec and 'w' in spec:
        gt_final[name] = {'od': spec['od'], 'id': spec['id'], 'w': spec['w'], 'source': 'title_3dim'}

print(f'\n=== Final GT: {len(gt_final)} drawings ===')
for name, gt in sorted(gt_final.items()):
    v2r = v2.get(name, {})
    od_match = '✅' if _check(v2r.get('od'), gt['od']) else '❌'
    id_match = '✅' if _check(v2r.get('id'), gt['id']) else '❌'
    w_match = '✅' if _check(v2r.get('w'), gt['w']) else '❌'
    print(f'  {name}: GT=({gt["od"]}/{gt["id"]}/{gt["w"]}) v2=({v2r.get("od","—")}/{v2r.get("id","—")}/{v2r.get("w","—")}) {od_match}{id_match}{w_match}')

# Save
Path('/tmp/gt_data.json').write_text(json.dumps(gt_final, indent=2, ensure_ascii=False))
Path('/tmp/gt_candidates.json').write_text(json.dumps(gt_candidates, indent=2, ensure_ascii=False))
print(f'\nSaved GT to /tmp/gt_data.json ({len(gt_final)} entries)')
print(f'Saved candidates to /tmp/gt_candidates.json')
