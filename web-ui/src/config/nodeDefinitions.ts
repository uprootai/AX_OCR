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
  category: 'input' | 'api' | 'control';
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
  imageinput: {
    type: 'imageinput',
    label: 'Image Input',
    category: 'input',
    color: '#f97316',
    icon: 'Image',
    description: '워크플로우의 시작점. 업로드된 이미지를 다른 노드로 전달합니다.',
    inputs: [],
    outputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 업로드된 도면 이미지',
      },
    ],
    parameters: [],
    examples: [
      '모든 워크플로우의 시작점으로 사용',
      'YOLO, eDOCr2 등 API 노드의 입력 소스',
      '이미지 업로드 후 자동으로 데이터 제공',
    ],
  },
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
        description: '📄 도면 이미지 파일 (JPG, PNG 등)',
      },
    ],
    outputs: [
      {
        name: 'detections',
        type: 'DetectionResult[]',
        description: '🎯 검출된 심볼 목록 (위치, 종류, 신뢰도 포함)',
      },
    ],
    parameters: [
      {
        name: 'model_type',
        type: 'select',
        default: 'symbol-detector-v1',
        options: [
          'symbol-detector-v1',
          'dimension-detector-v1',
          'gdt-detector-v1',
          'text-region-detector-v1',
          'yolo11n-general',
        ],
        description: '용도별 특화 모델 (심볼 vs 치수 vs GD&T vs 텍스트 영역)',
      },
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
        name: 'iou_threshold',
        type: 'number',
        default: 0.45,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'NMS IoU 임계값 (겹치는 박스 제거 기준)',
      },
      {
        name: 'imgsz',
        type: 'select',
        default: '640',
        options: ['320', '640', '1280'],
        description: '입력 이미지 크기 (작음=빠름, 큼=정확)',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: '검출 결과 시각화 이미지 생성',
      },
      {
        name: 'task',
        type: 'select',
        default: 'detect',
        options: ['detect', 'segment'],
        description: '작업 종류 (박스 검출 vs 세그멘테이션)',
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
        description: '📄 도면 이미지 또는 🎯 YOLO 검출 영역',
      },
    ],
    outputs: [
      {
        name: 'text_results',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록 (내용, 위치, 정확도)',
      },
    ],
    parameters: [
      {
        name: 'version',
        type: 'select',
        default: 'ensemble',
        options: ['v1', 'v2', 'ensemble'],
        description: 'eDOCr 버전 (v1: 5001, v2: 5002, ensemble: 가중 평균 0.6/0.4)',
      },
      {
        name: 'extract_dimensions',
        type: 'boolean',
        default: true,
        description: '치수 정보 추출 (φ476, 10±0.5, R20 등)',
      },
      {
        name: 'extract_gdt',
        type: 'boolean',
        default: true,
        description: 'GD&T 정보 추출 (평행도, 직각도, 위치도 등)',
      },
      {
        name: 'extract_text',
        type: 'boolean',
        default: true,
        description: '텍스트 정보 추출 (도면 번호, 재질, 주석 등)',
      },
      {
        name: 'use_vl_model',
        type: 'boolean',
        default: false,
        description: 'Vision Language 모델 보조 (느리지만 정확, +2초)',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: false,
        description: 'OCR 결과 시각화 이미지 생성',
      },
      {
        name: 'use_gpu_preprocessing',
        type: 'boolean',
        default: false,
        description: 'GPU 전처리 활성화 (CLAHE, denoising, +15% 정확도)',
      },
    ],
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
        description: '📄 흐릿하거나 복잡한 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'segmented_image',
        type: 'Image',
        description: '✨ 윤곽선이 선명해진 처리된 이미지',
      },
    ],
    parameters: [
      {
        name: 'model',
        type: 'select',
        default: 'graphsage',
        options: ['graphsage', 'unet'],
        description: '세그멘테이션 모델 (GraphSAGE: 빠름, UNet: 정확)',
      },
      {
        name: 'num_classes',
        type: 'select',
        default: '3',
        options: ['2', '3'],
        description: '분류 클래스 수 (2: Text/Non-text, 3: Contour/Text/Dimension)',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: '세그멘테이션 결과 시각화 생성',
      },
      {
        name: 'save_graph',
        type: 'boolean',
        default: false,
        description: '그래프 구조 JSON 저장 (디버깅용)',
      },
      {
        name: 'vectorize',
        type: 'boolean',
        default: false,
        description: '도면 벡터화 (DXF 출력용, Bezier 곡선)',
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
        description: '📝 OCR이 읽은 치수 및 공차 텍스트 (예: "50±0.1")',
      },
    ],
    outputs: [
      {
        name: 'tolerance_report',
        type: 'ToleranceReport',
        description: '📊 제조 가능 여부, 난이도, 예상 비용 분석 결과',
      },
    ],
    parameters: [
      {
        name: 'material',
        type: 'select',
        default: 'steel',
        options: ['aluminum', 'steel', 'stainless', 'titanium', 'plastic'],
        description: '재질 선택 (공차 계산에 영향)',
      },
      {
        name: 'manufacturing_process',
        type: 'select',
        default: 'machining',
        options: ['machining', 'casting', '3d_printing', 'welding', 'sheet_metal'],
        description: '제조 공정 (공차 허용 범위 결정)',
      },
      {
        name: 'correlation_length',
        type: 'number',
        default: 1.0,
        min: 0.1,
        max: 10.0,
        step: 0.1,
        description: 'Random Field 상관 길이 (불확실성 모델링, 기본값 1.0)',
      },
      {
        name: 'task',
        type: 'select',
        default: 'tolerance',
        options: ['tolerance', 'validate', 'manufacturability'],
        description: '분석 작업 (공차 예측 vs GD&T 검증 vs 제조성 분석)',
      },
    ],
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
        description: '📄 도면 이미지 또는 🎯 특정 검출 영역',
      },
    ],
    outputs: [
      {
        name: 'text_results',
        type: 'OCRResult[]',
        description: '📝 인식된 영문/숫자 텍스트 목록',
      },
    ],
    parameters: [
      {
        name: 'lang',
        type: 'select',
        default: 'en',
        options: ['en', 'ch', 'korean', 'japan', 'french'],
        description: '인식 언어',
      },
      {
        name: 'det_db_thresh',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.05,
        description: '텍스트 검출 임계값 (낮을수록 더 많이 검출)',
      },
      {
        name: 'det_db_box_thresh',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05,
        description: '박스 임계값 (높을수록 정확한 박스만)',
      },
      {
        name: 'use_angle_cls',
        type: 'boolean',
        default: true,
        description: '회전된 텍스트 감지 여부 (90도, 180도, 270도)',
      },
      {
        name: 'min_confidence',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05,
        description: '최소 신뢰도 (이 값 이하는 필터링)',
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
        description: '📄 이해하고 싶은 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'description',
        type: 'string',
        description: '💬 도면 내용을 자연어로 설명한 텍스트',
      },
    ],
    parameters: [
      {
        name: 'model',
        type: 'select',
        default: 'claude-3-5-sonnet-20241022',
        options: ['claude-3-5-sonnet-20241022', 'gpt-4o', 'gpt-4-turbo-2024-04-09', 'gemini-1.5-pro'],
        description: 'Vision Language 모델 선택 (Claude: 정확, GPT-4o: 빠름)',
      },
      {
        name: 'task',
        type: 'select',
        default: 'extract_info_block',
        options: ['extract_info_block', 'extract_dimensions', 'infer_manufacturing_process', 'generate_qc_checklist'],
        description: 'VL 작업 종류 (Info Block vs 치수 vs 제조공정 vs QC)',
      },
      {
        name: 'query_fields',
        type: 'string',
        default: '["name", "part number", "material", "scale", "weight"]',
        description: '추출할 정보 필드 (Info Block 작업 시, JSON 배열)',
      },
      {
        name: 'temperature',
        type: 'number',
        default: 0.0,
        min: 0,
        max: 1,
        step: 0.1,
        description: '생성 다양성 (0=정확/일관성, 1=창의적/다양)',
      },
    ],
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
        description: '🔍 조건을 확인할 데이터 (예: YOLO 결과)',
      },
    ],
    outputs: [
      {
        name: 'true',
        type: 'any',
        description: '✅ 조건 만족 시 → 다음 노드로 전달',
      },
      {
        name: 'false',
        type: 'any',
        description: '❌ 조건 불만족 시 → 대안 노드로 전달',
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
        description: '🔁 반복할 목록 (예: YOLO가 찾은 10개 심볼)',
      },
    ],
    outputs: [
      {
        name: 'item',
        type: 'any',
        description: '➡️ 현재 처리 중인 한 개 항목 (예: 1번째 심볼)',
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
        description: '🔵 첫 번째 결과 (예: eDOCr2 OCR)',
      },
      {
        name: 'input2',
        type: 'any',
        description: '🟢 두 번째 결과 (예: PaddleOCR)',
      },
      {
        name: 'input3',
        type: 'any',
        description: '🟡 세 번째 결과 (예: VL 설명)',
      },
    ],
    outputs: [
      {
        name: 'merged',
        type: 'any[]',
        description: '📦 모든 결과를 합친 통합 데이터',
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

/**
 * 커스텀 API를 노드 정의로 변환합니다.
 * localStorage의 customAPIs를 읽어서 동적으로 nodeDefinitions에 추가합니다.
 */
export function getAllNodeDefinitions(): Record<string, NodeDefinition> {
  // 기본 노드 정의
  const allDefinitions = { ...nodeDefinitions };

  // 커스텀 API 로드
  try {
    const customAPIsJSON = localStorage.getItem('custom-apis-storage');
    if (customAPIsJSON) {
      const storage = JSON.parse(customAPIsJSON);
      const customAPIs = storage.state?.customAPIs || [];

      // 각 커스텀 API를 노드 정의로 변환
      customAPIs.forEach((api: any) => {
        if (api.enabled) {
          allDefinitions[api.id] = {
            type: api.id,
            label: api.displayName,
            category: api.category,
            color: api.color,
            icon: api.icon,
            description: api.description,
            inputs: api.inputs || [
              {
                name: 'input',
                type: 'any',
                description: '📥 입력 데이터',
              },
            ],
            outputs: api.outputs || [
              {
                name: 'output',
                type: 'any',
                description: '📤 출력 데이터',
              },
            ],
            parameters: api.parameters || [],
            examples: [],
          };
        }
      });
    }
  } catch (error) {
    console.error('Failed to load custom API node definitions:', error);
  }

  return allDefinitions;
}
