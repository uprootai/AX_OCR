import type { TemplateInfo } from './types';

export const aiTemplates: TemplateInfo[] = [
  // ============ AI TEMPLATES ============
  {
    nameKey: 'vlAssisted',
    descKey: 'vlAssistedDesc',
    useCaseKey: 'vlAssistedUseCase',
    estimatedTime: '12-18s',
    accuracy: '96%',
    category: 'ai',
    workflow: {
      name: 'VL-Assisted Analysis',
      description: 'AI BOM Human-in-the-Loop with Vision-Language AI for intelligent drawing understanding',
      nodes: [
        { id: 'imageinput_1', type: 'imageinput', label: 'Drawing Input', parameters: {}, position: { x: 100, y: 150 } },
        { id: 'textinput_1', type: 'textinput', label: 'Analysis Prompt', parameters: { text: 'Analyze this engineering drawing and extract all dimensions' }, position: { x: 100, y: 300 } },
        { id: 'vl_1', type: 'vl', label: 'VL Model Analysis', parameters: {}, position: { x: 400, y: 200 } },
        { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.4 }, position: { x: 650, y: 200 } },
        { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: {}, position: { x: 900, y: 200 } },
      ],
      edges: [
        { id: 'e1', source: 'imageinput_1', target: 'vl_1' },
        { id: 'e2', source: 'textinput_1', target: 'vl_1' },
        { id: 'e3', source: 'vl_1', target: 'yolo_1' },
        { id: 'e4', source: 'imageinput_1', target: 'aibom_1' },
        { id: 'e5', source: 'yolo_1', target: 'aibom_1' },
      ],
    },
  },
  {
    nameKey: 'knowledgeEnhanced',
    descKey: 'knowledgeEnhancedDesc',
    useCaseKey: 'knowledgeEnhancedUseCase',
    estimatedTime: '15-20s',
    accuracy: '95%',
    category: 'ai',
    workflow: {
      name: 'AI-Enhanced Analysis',
      description: 'AI BOM Human-in-the-Loop with Vision-Language AI for context-aware analysis',
      nodes: [
        { id: 'imageinput_1', type: 'imageinput', label: 'Drawing Input', parameters: {}, position: { x: 100, y: 150 } },
        { id: 'textinput_1', type: 'textinput', label: 'Query', parameters: { text: 'Explain the GD&T symbols and tolerances in this drawing' }, position: { x: 100, y: 300 } },
        { id: 'yolo_1', type: 'yolo', label: 'Symbol Detection', parameters: { confidence: 0.4 }, position: { x: 350, y: 150 } },
        { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: {}, position: { x: 550, y: 150 } },
        { id: 'vl_1', type: 'vl', label: 'VL Context Analysis', parameters: {}, position: { x: 350, y: 300 } },
        { id: 'edocr2_1', type: 'edocr2', label: 'OCR', parameters: {}, position: { x: 750, y: 150 } },
        { id: 'merge_1', type: 'merge', label: 'Contextualized Results', parameters: {}, position: { x: 1000, y: 200 } },
      ],
      edges: [
        { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
        { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
        { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
        { id: 'e4', source: 'imageinput_1', target: 'vl_1' },
        { id: 'e5', source: 'textinput_1', target: 'vl_1' },
        { id: 'e6', source: 'aibom_1', target: 'edocr2_1' },
        { id: 'e7', source: 'edocr2_1', target: 'merge_1' },
        { id: 'e8', source: 'vl_1', target: 'merge_1' },
      ],
    },
  },
];
