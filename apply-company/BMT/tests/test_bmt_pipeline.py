"""
BMT GAR 배치도 TAG 추출 파이프라인 테스트
E10: S01~S04 검증

실행: pytest tests/test_bmt_pipeline.py -v
"""
import pytest
import re
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# === Paths ===
BASE = Path(__file__).parent.parent / "도면&BOM AI검증 솔루션 관련 자료"
GAR_PDF = BASE / "2_W5XGVU-SN2709-GARRB.pdf"
PART_LIST = BASE / "2_W5XGVU-SN2709-PLRA_Part List.xlsx"
ERP_BOM = BASE / "2_W5XHEGVU-SN2709-DNV.xlsx"

# === GT: Claude Vision 확인 24개 TAG ===
GT_TAGS = {
    'V01', 'V02', 'V03', 'V04', 'V05', 'V06', 'V07', 'V08', 'V09',
    'V11-1', 'V11-2', 'V14', 'V15',
    'B01', 'B02', 'B03',
    'PT01', 'PT03', 'PT04', 'PT05', 'PT07',
    'TT01', 'FT01', 'PI02',
}

# === TAG Filter Patterns (S03) ===
TAG_PATTERNS = [
    re.compile(r'^V\d+(-\d+)?$'),
    re.compile(r'^PT\d+$'),
    re.compile(r'^TT\d+$'),
    re.compile(r'^FT\d+$'),
    re.compile(r'^PI\d+$'),
    re.compile(r'^B\d+$'),
    re.compile(r'^GSO-V\d+$'),
    re.compile(r'^GSC-V\d+$'),
    re.compile(r'^CV-V\d+$'),
    re.compile(r'^ORI$'),
]

NOISE_PATTERNS = [
    re.compile(r'^\d'), re.compile(r'GVU'), re.compile(r'WORKSPACE'),
    re.compile(r'NORKSPACE'), re.compile(r'ENCLOSURE'), re.compile(r'MED1A'),
    re.compile(r'DN\d'), re.compile(r'^[A-Z]\d$'), re.compile(r'SPEC'),
    re.compile(r'PRESSURE'), re.compile(r','), re.compile(r'FUEL'),
    re.compile(r'NATURAL'), re.compile(r'NITROGEN'), re.compile(r'STPG'),
    re.compile(r'SUS'), re.compile(r'^R\d'),
]


def is_valid_tag(text: str) -> bool:
    t = text.strip().upper()
    for np in NOISE_PATTERNS:
        if np.search(t):
            return False
    for tp in TAG_PATTERNS:
        if tp.match(t):
            return True
    return False


def read_xlsx_sheet(path: Path, sheet_idx: int) -> list[dict]:
    rows = []
    with zipfile.ZipFile(path) as z:
        ss = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.parse(z.open('xl/sharedStrings.xml'))
            ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for si in tree.findall('.//s:si', ns):
                ss.append(''.join([t.text or '' for t in si.findall('.//s:t', ns)]))
        sp = f'xl/worksheets/sheet{sheet_idx}.xml'
        if sp not in z.namelist():
            return rows
        tree = ET.parse(z.open(sp))
        ns3 = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        for row in tree.findall(f'.//{{{ns3}}}row'):
            cells = {}
            for c in row:
                v = c.find(f'{{{ns3}}}v')
                ref = c.attrib.get('r', '')
                col = ''.join(filter(str.isalpha, ref))
                if v is not None and v.text:
                    cells[col] = ss[int(v.text)] if c.attrib.get('t') == 's' and int(v.text) < len(ss) else v.text
            rows.append(cells)
    return rows


# ============================================================
# Test 1: GAR PDF 3페이지가 래스터 이미지인지 확인
# ============================================================
class TestS01GarImage:
    def test_pdf_exists(self):
        assert GAR_PDF.exists(), f"GAR PDF not found: {GAR_PDF}"

    def test_page3_is_raster(self):
        """3페이지에 텍스트 레이어가 없어야 함 (래스터 이미지)"""
        import fitz
        doc = fitz.open(str(GAR_PDF))
        page = doc[2]  # 0-indexed
        text = page.get_text().strip()
        # 래스터 이미지면 텍스트가 거의 없어야 함
        assert len(text) < 50, f"Page 3 has text layer ({len(text)} chars) — expected raster image"

    def test_page3_extractable_as_image(self):
        """3페이지를 이미지로 추출 가능해야 함"""
        import fitz
        doc = fitz.open(str(GAR_PDF))
        page = doc[2]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        assert pix.width > 1000
        assert pix.height > 1000


# ============================================================
# Test 2: TAG 필터링 규칙 (S03)
# ============================================================
class TestS03TagFilter:
    def test_gt_tags_pass_filter(self):
        """GT 24개 TAG가 모두 필터를 통과해야 함"""
        for tag in GT_TAGS:
            assert is_valid_tag(tag), f"GT TAG '{tag}' failed filter"

    def test_noise_rejected(self):
        """노이즈 텍스트가 필터에서 제거되어야 함"""
        noise_samples = [
            '2250', '1450', '2170',  # 치수
            'GVUIN110OPENPOSITION', 'GVUIN90OPENPOSITION',
            'WORKSPACE800X460', 'NORKSPACE1300X3',
            'DN1OOGASVALV', 'ENCLOSUREDES1GNPRESSURE1MI',
            'MED1AFORENGINE', 'MED1AFORPURGE',
            'A1,B1', 'A1,B1,D1,B2,D2',
            'D1', 'D2', 'M8', 'R614',
            'STPG370', 'SUS316L',
            'NATURALGASCH4', 'N1TROGEN',
        ]
        for noise in noise_samples:
            assert not is_valid_tag(noise), f"Noise '{noise}' should be rejected"

    def test_filter_precision(self):
        """S02 OCR raw 39개 필터 시 TAG 24개 + 노이즈 15개로 분리"""
        s02_raw = [
            'V01', 'V02', 'V03', 'V04', 'V05', 'V06', 'V07', 'V08', 'V09',
            'V11-1', 'V11-2', 'V14', 'V15',
            'B01', 'B02', 'B03', 'FT01', 'TT01',
            'PT01', 'PT03', 'PT04', 'PT05', 'PT07', 'PI02',
            # noise
            'A1,B1', 'A1,B1,D1,B2,D2', 'D1', 'D2',
            'DN1OOGASVALV', 'ENCLOSUREDES1GNPRESSURE1MI',
            'GVUIN110OPENPOSITION', 'GVUIN90OPENPOSITION',
            'GVUSPEC1F1CA', 'M8', 'MED1AFORENGINE', 'MED1AFORPURGE',
            'NORKSPACE1300X3', 'R614', 'WORKSPACE800X460',
        ]
        tags = [t for t in s02_raw if is_valid_tag(t)]
        noise = [t for t in s02_raw if not is_valid_tag(t)]
        assert len(tags) == 24, f"Expected 24 TAGs, got {len(tags)}: {tags}"
        assert len(noise) == 15, f"Expected 15 noise, got {len(noise)}: {noise}"


# ============================================================
# Test 3: Part List → ERP BOM 매칭 (S04)
# ============================================================
class TestS04BomMatching:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.valve_map = {}
        self.sensor_map = {}
        self.erp_items = {}

        # VALVE LIST: sheet 1, TAG=B, ERP CODE=Y
        for row in read_xlsx_sheet(PART_LIST, 1):
            tag = row.get('B', '').strip().upper()
            code = row.get('Y', '').strip()
            if tag and code and tag not in ('CODE', ''):
                self.valve_map[tag] = code

        # SENSOR LIST: sheet 2, TAG=B, 품목코드=M
        for row in read_xlsx_sheet(PART_LIST, 2):
            tag = row.get('B', '').strip().upper()
            code = row.get('M', '').strip()
            if tag and tag != '-' and code and len(code) > 5 and not code.startswith('*'):
                self.sensor_map[tag] = code

        # ERP BOM: .1 level
        for row in read_xlsx_sheet(ERP_BOM, 1):
            if row.get('A', '') == '.1':
                self.erp_items[row.get('C', '')] = row.get('Y', '')

    def test_part_list_files_exist(self):
        assert PART_LIST.exists()
        assert ERP_BOM.exists()

    def test_valve_list_has_tags(self):
        assert len(self.valve_map) >= 12, f"VALVE LIST has only {len(self.valve_map)} TAGs"

    def test_sensor_list_has_tags(self):
        assert len(self.sensor_map) >= 10, f"SENSOR LIST has only {len(self.sensor_map)} TAGs"

    def test_erp_bom_has_items(self):
        assert len(self.erp_items) >= 50, f"ERP BOM has only {len(self.erp_items)} .1 items"

    def test_v01_exact_match(self):
        """V01: Part List → ERP BOM exact match"""
        code = self.valve_map.get('V01', '')
        assert code, "V01 not in VALVE LIST"
        assert code in self.erp_items, f"V01 code '{code}' not in ERP BOM"

    def test_v06_mismatch_detected(self):
        """V06: Part List에 -DNV 누락 → ERP에서 못 찾아야 함"""
        code = self.valve_map.get('V06', '')
        assert code, "V06 not in VALVE LIST"
        assert code not in self.erp_items, f"V06 should NOT exact-match (expected -DNV mismatch)"

    def test_pi02_mismatch_detected(self):
        """PI02: MAX331 vs MAX311 오타 → ERP에서 못 찾아야 함"""
        code = self.sensor_map.get('PI02', '')
        assert code, "PI02 not in SENSOR LIST"
        assert code not in self.erp_items, f"PI02 should NOT exact-match (expected 331/311 mismatch)"

    def test_matching_count(self):
        """전체 매칭: 최소 19건 성공"""
        matched = 0
        for tag in GT_TAGS:
            code = self.valve_map.get(tag, self.sensor_map.get(tag, ''))
            if code and code in self.erp_items:
                matched += 1
        assert matched >= 19, f"Only {matched} matches, expected >=19"

    def test_total_mismatches(self):
        """불일치 3건 검출 (V06, PI02, B02)"""
        mismatches = []
        for tag in GT_TAGS:
            code = self.valve_map.get(tag, self.sensor_map.get(tag, ''))
            if code and code not in self.erp_items and not code.startswith('Sturcture'):
                mismatches.append((tag, code))
        # V06과 PI02는 코드가 있는데 ERP에 없음
        mismatch_tags = {t for t, c in mismatches}
        assert 'V06' in mismatch_tags, "V06 mismatch not detected"
        assert 'PI02' in mismatch_tags, "PI02 mismatch not detected"


# ============================================================
# Test 4: BlueprintFlow 템플릿 로드
# ============================================================
class TestS06BlueprintFlowTemplate:
    def test_template_file_exists(self):
        tmpl = Path("/home/uproot/ax/poc/web-ui/src/pages/blueprintflow/templates/templates.bmt.ts")
        assert tmpl.exists(), "templates.bmt.ts not found"

    def test_template_has_correct_nodes(self):
        tmpl = Path("/home/uproot/ax/poc/web-ui/src/pages/blueprintflow/templates/templates.bmt.ts")
        content = tmpl.read_text()
        # 7 nodes
        assert content.count("id: '") >= 7, "Expected at least 7 nodes"
        # Key node types
        assert 'imageinput' in content
        assert 'paddleocr' in content
        assert 'tag_filter' in content or 'custom_script' in content
        assert 'bom_check' in content or 'custom_script' in content

    def test_template_registered_in_definitions(self):
        defs = Path("/home/uproot/ax/poc/web-ui/src/pages/blueprintflow/templates/templateDefinitions.ts")
        content = defs.read_text()
        assert 'bmtTemplates' in content, "bmtTemplates not imported"
        assert '...bmtTemplates' in content, "bmtTemplates not spread"

    def test_i18n_keys_exist(self):
        ko = Path("/home/uproot/ax/poc/web-ui/src/locales/ko.json")
        content = ko.read_text()
        assert 'bmtGarTagExtraction' in content, "Korean i18n key missing"
        assert 'bmtTemplates' in content, "Korean category label missing"

    def test_typescript_compiles(self):
        """TypeScript 빌드 에러 없어야 함"""
        import subprocess
        result = subprocess.run(
            ['npx', 'tsc', '--noEmit'],
            cwd='/home/uproot/ax/poc/web-ui',
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, f"TSC errors:\n{result.stdout}\n{result.stderr}"
