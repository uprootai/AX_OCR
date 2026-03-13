import type { TemplateInfo } from './types';

export const panasiaTemplates: TemplateInfo[] = [
  // ============ PANASIA TEMPLATES ============
  {
    nameKey: 'panasiaMcpPanelBom',
    descKey: 'panasiaMcpPanelBomDesc',
    useCaseKey: 'panasiaMcpPanelBomUseCase',
    estimatedTime: '10-15s',
    accuracy: '95%',
    category: 'panasia',
    featured: true,
    sampleImage: '/samples/sample7_mcp_panel_body.jpg',
    sampleGT: '/samples/gt/sample7_mcp_panel_body.txt',
    workflow: {
      name: 'PANASIA: MCP Panel 심볼 검출 + GT 비교',
      description: 'MCP Panel 도면에서 27종 전력 설비 심볼 검출 → GT와 비교 → Human-in-the-Loop 검증 → BOM 내보내기. 라인 연결성 분석 없이 심볼만 집중.',
      nodes: [
        { id: 'imageinput_1', type: 'imageinput', label: 'MCP Panel 도면 입력', parameters: { features: ['symbol_detection', 'symbol_verification', 'gt_comparison'] }, position: { x: 100, y: 200 } },
        { id: 'yolo_1', type: 'yolo', label: '파나시아 심볼 검출 (27종)', parameters: { model_type: 'panasia', confidence: 0.40, iou: 0.5, imgsz: 1024 }, position: { x: 400, y: 200 } },
        { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'GT 비교 + 검증 (AI BOM)', parameters: { drawing_type: 'electrical_panel' }, position: { x: 700, y: 200 } },
      ],
      edges: [
        { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
        { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
        { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
      ],
    },
  },
];
