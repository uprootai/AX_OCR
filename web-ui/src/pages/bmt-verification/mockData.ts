import type { CroppedView, ExtractedTag, MatchResult, VerificationSummary } from './types';

// ── Tags ──────────────────────────────────────────────────────────────

const TAG_V01: ExtractedTag = {
  id: 'tag-v01',
  tagCode: 'V01',
  partName: 'Gas Control Valve',
  confidence: 0.97,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 15, y: 20, w: 12, h: 6 },
};

const TAG_V02: ExtractedTag = {
  id: 'tag-v02',
  tagCode: 'V02',
  partName: 'Pilot Gas Valve',
  confidence: 0.95,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 55, y: 30, w: 12, h: 6 },
};

const TAG_V03: ExtractedTag = {
  id: 'tag-v03',
  tagCode: 'V03',
  partName: 'Double Block Valve',
  confidence: 0.96,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 20, y: 40, w: 12, h: 6 },
};

const TAG_V05: ExtractedTag = {
  id: 'tag-v05',
  tagCode: 'V05',
  partName: '(ref: V03)',
  confidence: 0.45,
  ocrEngine: 'Tesseract',
  boundingBox: { x: 60, y: 65, w: 12, h: 6 },
};

const TAG_V06: ExtractedTag = {
  id: 'tag-v06',
  tagCode: 'V06',
  partName: 'Gas Press. Control Valve',
  confidence: 0.92,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 45, y: 35, w: 12, h: 6 },
};

const TAG_V07: ExtractedTag = {
  id: 'tag-v07',
  tagCode: 'V07',
  partName: '(ref: V14)',
  confidence: 0.40,
  ocrEngine: 'Tesseract',
  boundingBox: { x: 75, y: 50, w: 12, h: 6 },
};

const TAG_V08: ExtractedTag = {
  id: 'tag-v08',
  tagCode: 'V08',
  partName: 'Safety Shut-off Valve',
  confidence: 0.94,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 55, y: 50, w: 12, h: 6 },
};

const TAG_V09: ExtractedTag = {
  id: 'tag-v09',
  tagCode: 'V09',
  partName: 'Safety Shut-off Valve (BH)',
  confidence: 0.93,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 35, y: 60, w: 12, h: 6 },
};

const TAG_PI02: ExtractedTag = {
  id: 'tag-pi02',
  tagCode: 'PI02',
  partName: 'Pressure Indicator',
  confidence: 0.88,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 70, y: 55, w: 12, h: 6 },
};

const TAG_B02: ExtractedTag = {
  id: 'tag-b02',
  tagCode: 'B02',
  partName: 'Structure',
  confidence: 0.91,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 30, y: 75, w: 12, h: 6 },
};

const TAG_PT01: ExtractedTag = {
  id: 'tag-pt01',
  tagCode: 'PT01',
  partName: 'Pressure Transmitter',
  confidence: 0.96,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 25, y: 30, w: 12, h: 6 },
};

const TAG_TT01: ExtractedTag = {
  id: 'tag-tt01',
  tagCode: 'TT01',
  partName: 'Temperature Transmitter',
  confidence: 0.95,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 55, y: 50, w: 12, h: 6 },
};

const TAG_FT01: ExtractedTag = {
  id: 'tag-ft01',
  tagCode: 'FT01',
  partName: 'Flow Meter',
  confidence: 0.94,
  ocrEngine: 'PaddleOCR',
  boundingBox: { x: 75, y: 25, w: 12, h: 6 },
};

// ── Cropped Views ─────────────────────────────────────────────────────

export const MOCK_VIEWS: CroppedView[] = [
  {
    id: 'view-front',
    viewName: 'FRONT VIEW',
    imagePath: '/images/bmt/gar-s02-front_view_upper.png',
    tags: [TAG_V01, TAG_V02, TAG_V06, TAG_V08],
  },
  {
    id: 'view-top',
    viewName: 'TOP VIEW',
    imagePath: '/images/bmt/e11-ocr-top_view.png',
    tags: [TAG_PT01, TAG_TT01, TAG_FT01],
  },
  {
    id: 'view-right',
    viewName: 'RIGHT VIEW',
    imagePath: '/images/bmt/gar-s02-right_a_view.png',
    tags: [TAG_V03, TAG_V05, TAG_V07],
  },
  {
    id: 'view-bottom',
    viewName: 'BOTTOM VIEW',
    imagePath: '/images/bmt/gar-s02-bottom_view.png',
    tags: [TAG_V09, TAG_PI02, TAG_B02],
  },
  {
    id: 'view-3d',
    viewName: '3D VIEW',
    imagePath: '/images/bmt/e11-ocr-3d_view.png',
    tags: [TAG_V01, TAG_V03, TAG_PT01],
  },
  {
    id: 'view-bottom-center',
    viewName: 'BOTTOM CENTER',
    imagePath: '/images/bmt/gar-s02-bottom_center.png',
    tags: [TAG_B02, TAG_V09],
  },
];

// ── Match Results ─────────────────────────────────────────────────────

export const MOCK_MATCH_RESULTS: MatchResult[] = [
  {
    id: 'match-v01',
    tag: TAG_V01,
    partListCode: 'FB2F29-R64A-A111-36L-EXT-GVU-DNV',
    erpBomCode: 'FB2F29-R64A-A111-36L-EXT-GVU-DNV',
    erpBomName: 'Gas Control Valve',
    drawingQty: 1,
    erpQty: 1,
    verdict: 'exact',
    severity: 'OK',
    detail: '도면 Part No.와 ERP BOM이 완전히 일치합니다.',
  },
  {
    id: 'match-v02',
    tag: TAG_V02,
    partListCode: 'FB2F23-R16A-P010-36L-DNV',
    erpBomCode: 'FB2F23-R16A-P010-36L-DNV',
    erpBomName: 'Pilot Gas Valve',
    drawingQty: 1,
    erpQty: 1,
    verdict: 'exact',
    severity: 'OK',
    detail: '도면 Part No.와 ERP BOM이 완전히 일치합니다.',
  },
  {
    id: 'match-v03',
    tag: TAG_V03,
    partListCode: 'DB219-R64A-P111-36L-GVU-DNV',
    erpBomCode: 'DB219-R64A-P111-36L-GVU-DNV',
    erpBomName: 'Double Block Valve',
    drawingQty: 1,
    erpQty: 1,
    verdict: 'exact',
    severity: 'OK',
    detail: '도면 Part No.와 ERP BOM이 완전히 일치합니다.',
  },
  {
    id: 'match-v06',
    tag: TAG_V06,
    partListCode: 'GPCV-RDN50PN16-VARIBELL',
    erpBomCode: 'GPCV-RDN50PN16-DNV-VARIBELL',
    erpBomName: 'Gas Press. Control Valve',
    drawingQty: 1,
    erpQty: 1,
    verdict: 'fuzzy',
    severity: 'REVIEW',
    detail: '선급코드 "DNV" 누락 — 도면에는 GPCV-RDN50PN16-VARIBELL, BOM에는 GPCV-RDN50PN16-DNV-VARIBELL로 등록되어 있습니다.',
  },
  {
    id: 'match-v08',
    tag: TAG_V08,
    partListCode: 'SBV220-S12-CE-DNV',
    erpBomCode: 'SBV220-S12-CE-DNV',
    erpBomName: 'Safety Shut-off Valve',
    drawingQty: 1,
    erpQty: 1,
    verdict: 'exact',
    severity: 'OK',
    detail: '도면 Part No.와 ERP BOM이 완전히 일치합니다.',
  },
  {
    id: 'match-v09',
    tag: TAG_V09,
    partListCode: 'SBV210-S12M-BH',
    erpBomCode: 'SBV210-S12M-BH',
    erpBomName: 'Safety Shut-off Valve (BH)',
    drawingQty: 1,
    erpQty: 1,
    verdict: 'exact',
    severity: 'OK',
    detail: '도면 Part No.와 ERP BOM이 완전히 일치합니다.',
  },
  {
    id: 'match-pi02',
    tag: TAG_PI02,
    partListCode: 'PI-DH-MAX331',
    erpBomCode: 'PI-DH-MAX311',
    erpBomName: 'Pressure Indicator',
    drawingQty: 1,
    erpQty: 1,
    verdict: 'fuzzy',
    severity: 'CRITICAL',
    detail: '모델번호 오타 의심 — 도면 "MAX331" vs BOM "MAX311". 숫자 1자리 차이로 오타 가능성이 높습니다. 확인 필요.',
  },
  {
    id: 'match-b02',
    tag: TAG_B02,
    partListCode: 'Structure',
    erpBomCode: '',
    erpBomName: '',
    drawingQty: 1,
    erpQty: 0,
    verdict: 'drawing_only',
    severity: 'WARN',
    detail: '도면에는 "Structure"로 표기되어 있으나, ERP BOM에 해당 품목이 존재하지 않습니다 (BOM 누락).',
  },
  {
    id: 'match-pt01',
    tag: TAG_PT01,
    partListCode: 'PT-MBS4201-4308G-DANFOSS',
    erpBomCode: 'PT-MBS4201-4308G-DANFOSS',
    erpBomName: 'Pressure Transmitter',
    drawingQty: 1,
    erpQty: 1,
    verdict: 'exact',
    severity: 'OK',
    detail: '도면 Part No.와 ERP BOM이 완전히 일치합니다.',
  },
  {
    id: 'match-tt01',
    tag: TAG_TT01,
    partListCode: 'TT-MBT5252-9110-DANFOSS',
    erpBomCode: 'TT-MBT5252-9110-DANFOSS',
    erpBomName: 'Temperature Transmitter',
    drawingQty: 1,
    erpQty: 1,
    verdict: 'exact',
    severity: 'OK',
    detail: '도면 Part No.와 ERP BOM이 완전히 일치합니다.',
  },
  {
    id: 'match-ft01',
    tag: TAG_FT01,
    partListCode: 'FM-GVU-HANHWA',
    erpBomCode: 'FM-GVU-HANHWA',
    erpBomName: 'Flow Meter',
    drawingQty: 1,
    erpQty: 1,
    verdict: 'exact',
    severity: 'OK',
    detail: '도면 Part No.와 ERP BOM이 완전히 일치합니다.',
  },
  {
    id: 'match-v05',
    tag: TAG_V05,
    partListCode: '',
    erpBomCode: '',
    erpBomName: '',
    drawingQty: 0,
    erpQty: 0,
    verdict: 'manual',
    severity: 'REVIEW',
    detail: 'V05는 "ref: V03"으로 참조 표기만 존재하며, 독립 Part No.가 없습니다. 수작업 확인이 필요합니다.',
  },
  {
    id: 'match-v07',
    tag: TAG_V07,
    partListCode: '',
    erpBomCode: '',
    erpBomName: '',
    drawingQty: 0,
    erpQty: 0,
    verdict: 'manual',
    severity: 'REVIEW',
    detail: 'V07은 "ref: V14"로 참조 표기만 존재하며, 독립 Part No.가 없습니다. 수작업 확인이 필요합니다.',
  },
];

// ── Summary ───────────────────────────────────────────────────────────

export const MOCK_SUMMARY: VerificationSummary = {
  total: MOCK_MATCH_RESULTS.length,
  approved: 0,
  rejected: 0,
  edited: 0,
  pending: MOCK_MATCH_RESULTS.length,
  matchRate: Math.round(
    (MOCK_MATCH_RESULTS.filter((r) => r.verdict === 'exact').length / MOCK_MATCH_RESULTS.length) * 100,
  ),
};
