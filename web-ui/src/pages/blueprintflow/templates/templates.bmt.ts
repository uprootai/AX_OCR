import type { TemplateInfo } from './types';

export const bmtTemplates: TemplateInfo[] = [
  {
    nameKey: 'bmtGarTagExtraction',
    descKey: 'bmtGarTagExtractionDesc',
    useCaseKey: 'bmtGarTagExtractionUseCase',
    estimatedTime: '10-20s',
    accuracy: '95.8%',
    category: 'bmt',
    featured: true,
    sampleImage: '/samples/bmt_gar_layout.png',
    workflow: {
      name: 'BMT GVU: GAR 배치도 TAG 추출 + BOM 누락 확인',
      description: 'GVU 스키드 배치도(GAR) 이미지에서 장비 TAG(V01, PT01 등)를 OCR로 추출하고, Part List를 거쳐 ERP BOM 누락 여부를 자동 확인합니다. 뷰별 분리 → PaddleOCR → TAG 필터 → BOM 매칭 파이프라인.',
      nodes: [
        {
          id: 'imageinput_1',
          type: 'imageinput',
          label: 'GAR 배치도 입력',
          parameters: { features: ['ocr', 'layout_analysis'] },
          position: { x: 100, y: 200 },
        },
        {
          id: 'view_splitter_1',
          type: 'preprocessor',
          label: '뷰 영역 분리 (Top/Front/Right/A)',
          parameters: {
            operation: 'crop_regions',
            regions: [
              { name: 'bottom_view', bbox: [0, 0, 0.50, 0.45] },
              { name: 'front_view_upper', bbox: [0.40, 0, 1.0, 0.40] },
              { name: 'front_view_lower', bbox: [0.10, 0.62, 0.65, 0.88] },
              { name: 'bottom_center', bbox: [0.30, 0.75, 0.75, 0.98] },
              { name: 'right_a_view', bbox: [0.30, 0.30, 1.0, 0.70] },
            ],
          },
          position: { x: 350, y: 200 },
        },
        {
          id: 'paddleocr_1',
          type: 'paddleocr',
          label: 'PaddleOCR (뷰별)',
          parameters: { language: 'en', batch_mode: true },
          position: { x: 600, y: 200 },
        },
        {
          id: 'tag_filter_1',
          type: 'custom_script',
          label: 'TAG 필터링 (알파벳 규칙)',
          parameters: {
            script: 'tag_filter',
            tag_patterns: ['^V\\d+(-\\d+)?$', '^PT\\d+$', '^TT\\d+$', '^FT\\d+$', '^PI\\d+$', '^B\\d+$', '^GSO-V\\d+$', '^GSC-V\\d+$', '^CV-V\\d+$', '^ORI$'],
            noise_patterns: ['^\\d', 'GVU', 'WORKSPACE', 'ENCLOSURE', 'MED1A', 'DN\\d', 'SPEC', 'PRESSURE', ',', 'FUEL', 'NATURAL', 'NITROGEN', 'STPG', 'SUS'],
          },
          position: { x: 850, y: 100 },
        },
        {
          id: 'excel_lookup_1',
          type: 'custom_script',
          label: 'Part List 조회 (TAG→품목코드)',
          parameters: {
            script: 'excel_lookup',
            file: 'part_list.xlsx',
            valve_tag_col: 'B',
            valve_code_col: 'Y',
            sensor_tag_col: 'B',
            sensor_code_col: 'M',
          },
          position: { x: 850, y: 300 },
        },
        {
          id: 'bom_check_1',
          type: 'custom_script',
          label: 'ERP BOM 누락 확인',
          parameters: {
            script: 'bom_check',
            file: 'erp_bom.xlsx',
            code_col: 'C',
            level_col: 'A',
            level_filter: '.1',
          },
          position: { x: 1100, y: 200 },
        },
        {
          id: 'report_1',
          type: 'pdf_export',
          label: '누락 리포트 생성',
          parameters: { format: 'xlsx', sheets: ['Summary', 'TAG_Details', 'Mismatches'] },
          position: { x: 1350, y: 200 },
        },
      ],
      edges: [
        { id: 'e1', source: 'imageinput_1', target: 'view_splitter_1' },
        { id: 'e2', source: 'view_splitter_1', target: 'paddleocr_1' },
        { id: 'e3', source: 'paddleocr_1', target: 'tag_filter_1' },
        { id: 'e4', source: 'tag_filter_1', target: 'bom_check_1' },
        { id: 'e5', source: 'excel_lookup_1', target: 'bom_check_1' },
        { id: 'e6', source: 'bom_check_1', target: 'report_1' },
      ],
    },
  },
];
