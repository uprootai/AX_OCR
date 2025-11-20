export interface NodeParameter {
  name: string;
  type: 'number' | 'string' | 'boolean' | 'select';
  default: any;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  description: string;
}

export interface NodeDefinition {
  type: string;
  label: string;
  category: 'api' | 'control';
  color: string;
  icon: string;
  description: string;
  inputs: {
    name: string;
    type: string;
    description: string;
  }[];
  outputs: {
    name: string;
    type: string;
    description: string;
  }[];
  parameters: NodeParameter[];
  examples: string[];
}

export const nodeDefinitions: Record<string, NodeDefinition> = {
  yolo: {
    type: 'yolo',
    label: 'YOLO Detection',
    category: 'api',
    color: '#10b981',
    icon: 'Target',
    description: '기계 도면에서 용접 기호, 베어링, 기어 등 14가지 심볼을 자동으로 검출합니다. YOLO v11n 모델 기반.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '분석할 기계 도면 이미지 (JPG, PNG)',
      },
    ],
    outputs: [
      {
        name: 'detections',
        type: 'DetectionResult[]',
        description: '검출된 객체 목록 (bbox, class, confidence)',
      },
    ],
    parameters: [
      {
        name: 'confidence',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05,
        description: '검출 신뢰도 임계값 (낮을수록 더 많이 검출)',
      },
      {
        name: 'model',
        type: 'select',
        default: 'yolo11n',
        options: ['yolo11n', 'yolo11s', 'yolo11m'],
        description: '사용할 YOLO 모델 (n=빠름, m=정확)',
      },
    ],
    examples: [
      '도면 이미지 → YOLO → 14가지 심볼 자동 검출',
      '용접 기호, 베어링, 기어 등 기계 요소 인식',
    ],
  },
  edocr2: {
    type: 'edocr2',
    label: 'eDOCr2 Korean OCR',
    category: 'api',
    color: '#3b82f6',
    icon: 'FileText',
    description: '한국어 텍스트 인식 전문 OCR. 도면의 치수, 공차, 주석 등을 정확하게 읽습니다.',
    inputs: [
      {
        name: 'image',
        type: 'Image | DetectionResult[]',
        description: '전체 이미지 또는 YOLO 검출 결과',
      },
    ],
    outputs: [
      {
        name: 'text_results',
        type: 'OCRResult[]',
        description: '인식된 텍스트 (text, confidence, bbox)',
      },
    ],
    parameters: [],
    examples: [
      'YOLO 검출 → eDOCr2 → 한글/숫자 치수 인식',
      '공차 표기 (±0.05), 주석 텍스트 추출',
    ],
  },
  edgnet: {
    type: 'edgnet',
    label: 'EDGNet Segmentation',
    category: 'api',
    color: '#8b5cf6',
    icon: 'Network',
    description: '도면의 엣지를 세그멘테이션하여 선명하게 만듭니다. U-Net 기반 전처리.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '원본 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'segmented_image',
        type: 'Image',
        description: '엣지가 강조된 이미지',
      },
    ],
    parameters: [
      {
        name: 'threshold',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.1,
        description: '세그멘테이션 임계값',
      },
    ],
    examples: [
      '흐릿한 도면 → EDGNet → 선명한 윤곽선',
      'OCR 전처리로 인식률 향상',
    ],
  },
  skinmodel: {
    type: 'skinmodel',
    label: 'Tolerance Analysis',
    category: 'api',
    color: '#f59e0b',
    icon: 'Ruler',
    description: '인식된 치수 데이터를 분석하여 공차를 계산하고 제조 가능성을 평가합니다.',
    inputs: [
      {
        name: 'ocr_results',
        type: 'OCRResult[]',
        description: 'OCR로 추출된 치수 데이터',
      },
    ],
    outputs: [
      {
        name: 'tolerance_report',
        type: 'ToleranceReport',
        description: '공차 분석 결과 및 제조 견적',
      },
    ],
    parameters: [],
    examples: [
      'OCR 결과 → SkinModel → 공차 계산',
      '제조 난이도 평가 및 비용 추정',
    ],
  },
  paddleocr: {
    type: 'paddleocr',
    label: 'PaddleOCR',
    category: 'api',
    color: '#06b6d4',
    icon: 'FileSearch',
    description: '다국어 지원 OCR. 영어, 숫자 인식에 강점. eDOCr2의 대안으로 사용.',
    inputs: [
      {
        name: 'image',
        type: 'Image | DetectionResult[]',
        description: '전체 이미지 또는 검출 영역',
      },
    ],
    outputs: [
      {
        name: 'text_results',
        type: 'OCRResult[]',
        description: '인식된 텍스트',
      },
    ],
    parameters: [
      {
        name: 'lang',
        type: 'select',
        default: 'en',
        options: ['en', 'ch', 'korean'],
        description: '인식 언어',
      },
    ],
    examples: [
      '영문 도면 → PaddleOCR → 영어 텍스트 추출',
      'IF 노드로 eDOCr2 실패 시 대안으로 사용',
    ],
  },
  vl: {
    type: 'vl',
    label: 'Vision Language Model',
    category: 'api',
    color: '#ec4899',
    icon: 'Sparkles',
    description: 'GPT-4V 기반 비전 언어 모델. 도면을 이해하고 자연어로 설명합니다.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '분석할 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'description',
        type: 'string',
        description: '도면에 대한 자연어 설명',
      },
    ],
    parameters: [],
    examples: [
      '도면 이미지 → VL → "이 도면은 베어링 하우징입니다"',
      '복잡한 도면의 전체적인 이해',
    ],
  },
  if: {
    type: 'if',
    label: 'IF (Conditional)',
    category: 'control',
    color: '#ef4444',
    icon: 'GitBranch',
    description: '조건에 따라 워크플로우를 분기합니다. TRUE/FALSE 두 경로로 나뉩니다.',
    inputs: [
      {
        name: 'data',
        type: 'any',
        description: '조건 판단할 데이터',
      },
    ],
    outputs: [
      {
        name: 'true',
        type: 'any',
        description: '조건이 참일 때의 출력',
      },
      {
        name: 'false',
        type: 'any',
        description: '조건이 거짓일 때의 출력',
      },
    ],
    parameters: [
      {
        name: 'condition',
        type: 'string',
        default: 'confidence > 0.8',
        description: '판단 조건 (예: confidence > 0.8)',
      },
    ],
    examples: [
      'YOLO confidence > 0.8 → eDOCr2',
      'YOLO confidence < 0.8 → PaddleOCR (대안)',
    ],
  },
  loop: {
    type: 'loop',
    label: 'Loop (Iteration)',
    category: 'control',
    color: '#f97316',
    icon: 'Repeat',
    description: '배열의 각 요소에 대해 반복 처리합니다. YOLO 검출 결과를 하나씩 처리할 때 사용.',
    inputs: [
      {
        name: 'array',
        type: 'any[]',
        description: '반복할 배열 데이터',
      },
    ],
    outputs: [
      {
        name: 'item',
        type: 'any',
        description: '현재 반복 중인 항목',
      },
    ],
    parameters: [
      {
        name: 'iterator',
        type: 'string',
        default: 'detections',
        description: '반복할 배열 필드명',
      },
    ],
    examples: [
      'YOLO 10개 검출 → Loop → 각각 OCR 처리',
      '개별 심볼마다 다른 처리 적용',
    ],
  },
  merge: {
    type: 'merge',
    label: 'Merge (Combine)',
    category: 'control',
    color: '#14b8a6',
    icon: 'Merge',
    description: '여러 경로의 결과를 하나로 병합합니다. 병렬 처리 후 통합할 때 사용.',
    inputs: [
      {
        name: 'input1',
        type: 'any',
        description: '첫 번째 입력',
      },
      {
        name: 'input2',
        type: 'any',
        description: '두 번째 입력',
      },
      {
        name: 'input3',
        type: 'any',
        description: '세 번째 입력',
      },
    ],
    outputs: [
      {
        name: 'merged',
        type: 'any[]',
        description: '병합된 결과',
      },
    ],
    parameters: [],
    examples: [
      'eDOCr2 + PaddleOCR + VL → Merge → 통합 결과',
      '다양한 OCR 결과를 종합하여 정확도 향상',
    ],
  },
};

export function getNodeDefinition(type: string): NodeDefinition | undefined {
  return nodeDefinitions[type];
}
