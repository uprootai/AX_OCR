export interface NodeParameter {
  name: string;
  type: 'number' | 'string' | 'boolean' | 'select' | 'textarea';
  default: string | number | boolean;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  description: string;
  placeholder?: string;
}

export interface RecommendedInput {
  from: string;
  field: string;
  reason: string;
}

export interface NodeDefinition {
  type: string;
  label: string;
  category: 'input' | 'detection' | 'ocr' | 'segmentation' | 'preprocessing' | 'analysis' | 'knowledge' | 'ai' | 'control';
  color: string;
  icon: string;
  description: string;
  deprecated?: boolean;
  deprecatedMessage?: string;
  inputs: {
    name: string;
    type: string;
    description: string;
    optional?: boolean;
  }[];
  outputs: {
    name: string;
    type: string;
    description: string;
  }[];
  parameters: NodeParameter[];
  examples: string[];
  usageTips?: string[];
  recommendedInputs?: RecommendedInput[];
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
  textinput: {
    type: 'textinput',
    label: 'Text Input',
    category: 'input',
    color: '#8b5cf6',
    icon: 'Type',
    description: '텍스트 입력 노드. 사용자가 직접 입력한 텍스트를 다른 노드로 전달합니다.',
    inputs: [],
    outputs: [
      {
        name: 'text',
        type: 'string',
        description: '📝 사용자가 입력한 텍스트',
      },
      {
        name: 'length',
        type: 'number',
        description: '📏 텍스트 길이 (문자 수)',
      },
    ],
    parameters: [
      {
        name: 'text',
        type: 'string',
        default: '',
        description: '입력할 텍스트 내용 (최대 10,000자)',
      },
    ],
    examples: [
      'Text-to-Image API의 프롬프트 입력',
      'LLM API의 질문/명령어 입력',
      '검색어, 키워드 등 텍스트 기반 API 입력',
    ],
    usageTips: [
      '💡 이미지가 아닌 텍스트 기반 API와 연결 시 사용',
      '💡 최대 10,000자까지 입력 가능',
      '💡 여러 줄 입력 지원 (줄바꿈 포함)',
    ],
  },
  yolo: {
    type: 'yolo',
    label: 'YOLO (통합)',
    category: 'detection',
    color: '#10b981',
    icon: 'Target',
    description: '통합 YOLO API - 기계도면(14종) 및 P&ID(60종) 심볼을 검출합니다. 모델 선택으로 용도에 맞게 사용하세요.',
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
        default: 'engineering',
        options: [
          'engineering',
          'pid_symbol',
          'pid_class_agnostic',
          'pid_class_aware',
          'bom_detector',
        ],
        description: '모델 선택: engineering(기계도면 14종), pid_symbol(P&ID 60종), bom_detector(BOM 27종)',
      },
      {
        name: 'confidence',
        type: 'number',
        default: 0.25,
        min: 0.05,
        max: 1,
        step: 0.05,
        description: '검출 신뢰도 임계값 (P&ID는 0.1 권장)',
      },
      {
        name: 'iou',
        type: 'number',
        default: 0.45,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'NMS IoU 임계값 (겹치는 박스 제거 기준)',
      },
      {
        name: 'imgsz',
        type: 'number',
        default: 640,
        min: 320,
        max: 3520,
        step: 32,
        description: '입력 이미지 크기 (bom_detector는 3520 권장)',
      },
      {
        name: 'use_sahi',
        type: 'boolean',
        default: false,
        description: 'SAHI 슬라이싱 활성화 (P&ID 모델은 자동 활성화)',
      },
      {
        name: 'slice_height',
        type: 'number',
        default: 512,
        min: 256,
        max: 2048,
        step: 128,
        description: 'SAHI 슬라이스 높이 (작을수록 정밀)',
      },
      {
        name: 'slice_width',
        type: 'number',
        default: 512,
        min: 256,
        max: 2048,
        step: 128,
        description: 'SAHI 슬라이스 너비 (작을수록 정밀)',
      },
      {
        name: 'overlap_ratio',
        type: 'number',
        default: 0.25,
        min: 0.1,
        max: 0.5,
        step: 0.05,
        description: 'SAHI 슬라이스 오버랩 비율',
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
      '도면 이미지 → YOLO (engineering) → 14가지 기계 심볼 검출',
      '도면 이미지 → YOLO (pid_symbol) → 60가지 P&ID 심볼 검출',
      '제어판 도면 → YOLO (bom_detector) → 27가지 전장 부품 검출 → BOM 생성',
    ],
    usageTips: [
      '기계도면: model_type=engineering, confidence=0.25',
      'P&ID: model_type=pid_symbol, confidence=0.1 (SAHI 자동)',
      'BOM: model_type=bom_detector, confidence=0.25 (전기 제어판 부품)',
      '검출된 영역을 eDOCr2나 PaddleOCR의 입력으로 사용하면 해당 영역만 정밀 분석할 수 있습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면 이미지를 입력받아 심볼과 텍스트 영역을 검출합니다',
      },
    ],
  },
  edocr2: {
    type: 'edocr2',
    label: 'eDOCr2 Korean OCR',
    category: 'ocr',
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
        default: 'v2',
        options: ['v1', 'v2', 'ensemble'],
        description: 'eDOCr 버전 (v1: 5001, v2: 5002, ensemble: 가중 평균 0.6/0.4)',
      },
      {
        name: 'language',
        type: 'select',
        default: 'eng',
        options: ['eng', 'kor', 'jpn', 'chi_sim'],
        description: '인식 언어 (eng: 영어, kor: 한국어, jpn: 일본어, chi_sim: 중국어)',
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
        name: 'extract_tables',
        type: 'boolean',
        default: true,
        description: '표 정보 추출 (BOM, 치수 표 등)',
      },
      {
        name: 'cluster_threshold',
        type: 'number',
        default: 20,
        min: 5,
        max: 100,
        step: 5,
        description: '텍스트 클러스터링 임계값 (픽셀 단위)',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,  // BlueprintFlow에서는 기본적으로 시각화 활성화
        description: 'OCR 결과 시각화 이미지 생성',
      },
    ],
    examples: [
      'YOLO 검출 → eDOCr2 → 한글/숫자 치수 인식',
      '공차 표기 (±0.05), 주석 텍스트 추출',
    ],
    usageTips: [
      '한국어가 포함된 도면은 language=kor로 설정하세요',
      'YOLO의 검출 영역을 입력으로 받으면 특정 영역만 정밀 분석할 수 있습니다',
      'visualize=true로 설정하면 인식된 텍스트의 위치를 시각적으로 확인할 수 있습니다',
      '⭐ SkinModel 노드와 연결 시 텍스트 위치 정보가 자동으로 활용되어 치수 매칭 정확도가 향상됩니다',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO가 검출한 텍스트 영역만 정밀 분석하여 처리 속도와 정확도를 높입니다',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면 이미지에서 모든 텍스트를 추출합니다',
      },
    ],
  },
  edgnet: {
    type: 'edgnet',
    label: 'EDGNet Segmentation',
    category: 'segmentation',
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
        default: 'unet',
        options: ['unet', 'graphsage'],
        description: '세그멘테이션 모델 (UNet: 정확/안정적, GraphSAGE: 빠름/실험적)',
      },
      {
        name: 'num_classes',
        type: 'number',
        default: 3,
        min: 2,
        max: 3,
        step: 1,
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
    usageTips: [
      '스캔 품질이 낮거나 흐릿한 도면은 EDGNet으로 전처리 후 OCR을 수행하세요',
      'visualize=true로 설정하면 세그멘테이션 결과를 시각적으로 확인할 수 있습니다',
      '처리된 이미지를 eDOCr2나 PaddleOCR의 입력으로 사용하면 텍스트 인식률이 향상됩니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '흐릿하거나 복잡한 원본 도면 이미지를 선명하게 만듭니다',
      },
    ],
  },
  skinmodel: {
    type: 'skinmodel',
    label: 'Tolerance Analysis',
    category: 'analysis',
    color: '#f59e0b',
    icon: 'Ruler',
    description: '인식된 치수 데이터를 분석하여 공차를 계산하고 제조 가능성을 평가합니다.',
    inputs: [
      {
        name: 'dimensions',
        type: 'Dimension[]',
        description: '📝 OCR에서 추출된 치수 데이터 (예: [{nominal: 50, tolerance: 0.1}])',
        optional: true,
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
        name: 'dimensions_manual',
        type: 'textarea',
        default: '',
        description: '수동 치수 입력 (JSON 배열). 예: [{"value": 50, "tolerance": 0.1, "type": "length", "unit": "mm"}]',
        placeholder: '[{"value": 50, "tolerance": 0.1, "type": "length"}]',
      },
      {
        name: 'material_type',
        type: 'select',
        default: 'steel',
        options: ['aluminum', 'steel', 'plastic', 'composite'],
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
    usageTips: [
      '⭐ eDOCr2의 출력을 입력으로 받으면 텍스트 위치 정보가 자동으로 활용됩니다',
      '위치 정보 덕분에 치수와 공차가 정확히 매칭되어 분석 정확도가 크게 향상됩니다',
      '💡 OCR 연결 없이 테스트하려면 dimensions_manual에 JSON을 직접 입력하세요',
      'material_type과 manufacturing_process를 정확히 설정하면 더 정확한 제조성 평가를 받을 수 있습니다',
    ],
    recommendedInputs: [
      {
        from: 'edocr2',
        field: 'text_results',
        reason: '⭐ 텍스트 위치 정보(bbox)를 활용해 치수와 공차를 정확히 매칭합니다. 이것이 핵심 패턴입니다!',
      },
      {
        from: 'paddleocr',
        field: 'text_results',
        reason: 'PaddleOCR 결과도 위치 정보를 포함하므로 활용 가능합니다',
      },
    ],
  },
  paddleocr: {
    type: 'paddleocr',
    label: 'PaddleOCR',
    category: 'ocr',
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
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: 'OCR 결과 시각화 이미지 생성 (바운딩 박스 + 텍스트)',
      },
    ],
    examples: [
      '영문 도면 → PaddleOCR → 영어 텍스트 추출',
      'IF 노드로 eDOCr2 실패 시 대안으로 사용',
    ],
    usageTips: [
      '영문/숫자가 많은 도면은 eDOCr2 대신 PaddleOCR을 사용하면 더 정확합니다',
      '✨ visualize=true로 설정하면 인식된 텍스트의 바운딩 박스와 위치를 시각적으로 확인할 수 있습니다',
      'IF 노드와 함께 사용하여 eDOCr2 실패 시 자동 fallback으로 활용할 수 있습니다',
      'SkinModel과 연결 시 텍스트 위치 정보가 자동으로 활용되어 치수 분석 정확도가 향상됩니다',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO가 검출한 텍스트 영역만 정밀 분석하여 처리 속도를 높입니다',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면에서 영문/숫자 텍스트를 추출합니다',
      },
      {
        from: 'edgnet',
        field: 'segmented_image',
        reason: '전처리된 선명한 이미지에서 텍스트를 인식하면 정확도가 향상됩니다',
      },
    ],
  },
  vl: {
    type: 'vl',
    label: 'Vision Language Model',
    category: 'ai',
    color: '#ec4899',
    icon: 'Sparkles',
    description: '이미지와 텍스트를 함께 이해하는 Vision-Language 모델. 이미지에 대한 질문-답변(VQA) 또는 일반 분석 수행.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 분석할 도면 이미지',
      },
      {
        name: 'text',
        type: 'string',
        description: '❓ 질문 또는 분석 요청 (선택사항)',
      },
    ],
    outputs: [
      {
        name: 'mode',
        type: 'string',
        description: '🔍 분석 모드 (vqa: 질문-답변, captioning: 일반 설명)',
      },
      {
        name: 'answer',
        type: 'string',
        description: '💬 질문에 대한 답변 (VQA 모드)',
      },
      {
        name: 'caption',
        type: 'string',
        description: '📝 이미지 설명 (캡셔닝 모드)',
      },
      {
        name: 'confidence',
        type: 'number',
        description: '📊 답변 신뢰도 (0-1)',
      },
    ],
    parameters: [
      {
        name: 'model',
        type: 'select',
        default: 'claude-3-5-sonnet-20241022',
        options: ['claude-3-5-sonnet-20241022', 'gpt-4o', 'gpt-4-turbo'],
        description: 'Vision Language 모델 선택 (Claude: 정확/도면 특화, GPT-4o: 빠름)',
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
      'ImageInput + TextInput("치수 추출") → VL → 정확한 치수 정보',
      'ImageInput만 → VL → 일반적인 도면 설명',
      '용접 기호 찾기, 공차 정보 추출 등 특정 질문',
    ],
    usageTips: [
      '💡 TextInput과 함께 사용하면 훨씬 정확한 정보를 얻을 수 있습니다 (정확도 30% → 90%)',
      '💡 프롬프트 없이 사용 시: 일반 이미지 캡셔닝 모드',
      '💡 프롬프트와 함께 사용 시: 질문-답변(VQA) 모드로 자동 전환',
      '💡 "이 도면의 치수를 알려줘", "용접 기호를 모두 찾아줘" 같은 구체적 질문 가능',
      'Claude 모델은 도면 분석에 특화되어 있고, GPT-4o는 처리 속도가 빠릅니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '분석할 도면 이미지를 제공합니다',
      },
      {
        from: 'textinput',
        field: 'text',
        reason: '⭐ 특정 질문이나 분석 요청을 전달하여 정확도를 크게 향상시킵니다',
      },
      {
        from: 'edgnet',
        field: 'segmented_image',
        reason: '선명하게 처리된 이미지에서 더 정확한 분석 결과를 얻을 수 있습니다',
      },
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
  knowledge: {
    type: 'knowledge',
    label: 'Knowledge Engine',
    category: 'knowledge',
    color: '#9333ea',
    icon: 'Database',
    description: 'Neo4j 그래프DB + RAG 기반 도메인 지식 엔진. 유사 부품 검색, ISO/ASME 규격 검증, 비용 추정 지원.',
    inputs: [
      {
        name: 'ocr_results',
        type: 'OCRResult[]',
        description: '📝 OCR 결과 (치수, 공차, 재질 정보 포함)',
      },
      {
        name: 'query',
        type: 'string',
        description: '🔍 검색 쿼리 (예: "SUS304 Ø50 H7")',
      },
    ],
    outputs: [
      {
        name: 'similar_parts',
        type: 'SimilarPart[]',
        description: '🔎 유사 부품 목록 (과거 제조 이력, 비용 정보 포함)',
      },
      {
        name: 'validation_result',
        type: 'ValidationResult',
        description: '✅ ISO/ASME 규격 검증 결과',
      },
      {
        name: 'cost_estimate',
        type: 'CostEstimate',
        description: '💰 비용 추정 결과 (유사 부품 기반)',
      },
    ],
    parameters: [
      {
        name: 'search_mode',
        type: 'select',
        default: 'hybrid',
        options: ['graph', 'vector', 'hybrid'],
        description: '검색 모드 (graph: Neo4j 그래프, vector: FAISS 벡터, hybrid: 가중 결합)',
      },
      {
        name: 'graph_weight',
        type: 'number',
        default: 0.6,
        min: 0,
        max: 1,
        step: 0.1,
        description: 'Hybrid 모드에서 GraphRAG 가중치 (나머지는 VectorRAG)',
      },
      {
        name: 'top_k',
        type: 'number',
        default: 5,
        min: 1,
        max: 20,
        step: 1,
        description: '반환할 유사 부품 수',
      },
      {
        name: 'validate_standards',
        type: 'boolean',
        default: true,
        description: 'ISO/ASME 규격 자동 검증 활성화',
      },
      {
        name: 'include_cost',
        type: 'boolean',
        default: true,
        description: '유사 부품 기반 비용 추정 포함',
      },
      {
        name: 'material_filter',
        type: 'select',
        default: 'all',
        options: ['all', 'steel', 'stainless', 'aluminum', 'plastic', 'composite'],
        description: '재질 필터 (유사 부품 검색 시)',
      },
    ],
    examples: [
      'eDOCr2 OCR → Knowledge → 유사 부품 5개 검색',
      'TextInput("M10 H7") → Knowledge → ISO 규격 검증',
      '과거 제조 이력 기반 비용 추정',
    ],
    usageTips: [
      '⭐ eDOCr2나 PaddleOCR의 결과를 입력하면 치수/공차/재질 정보를 자동으로 추출합니다',
      '💡 Hybrid 모드가 가장 정확합니다 (GraphRAG 60% + VectorRAG 40%)',
      '💡 ISO 1101, ISO 286-2, ASME Y14.5 등 주요 규격을 자동 검증합니다',
      '💡 과거 유사 부품 제조 이력을 활용해 정확한 비용을 추정합니다',
      '💡 TextInput과 연결하여 직접 쿼리 검색도 가능합니다',
    ],
    recommendedInputs: [
      {
        from: 'edocr2',
        field: 'text_results',
        reason: '⭐ OCR 결과에서 치수, 공차, 재질 정보를 추출하여 유사 부품을 검색합니다',
      },
      {
        from: 'paddleocr',
        field: 'text_results',
        reason: 'PaddleOCR 결과도 동일하게 활용 가능합니다',
      },
      {
        from: 'textinput',
        field: 'text',
        reason: '직접 검색 쿼리를 입력하여 유사 부품을 검색합니다',
      },
      {
        from: 'skinmodel',
        field: 'tolerance_report',
        reason: '공차 분석 결과를 활용해 더 정밀한 유사 부품 검색이 가능합니다',
      },
    ],
  },
  tesseract: {
    type: 'tesseract',
    label: 'Tesseract OCR',
    category: 'ocr',
    color: '#059669',
    icon: 'ScanText',
    description: 'Google Tesseract 기반 OCR. 문서 텍스트 인식, 다국어 지원.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 또는 문서 이미지',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
    ],
    parameters: [
      {
        name: 'lang',
        type: 'select',
        default: 'eng',
        options: ['eng', 'kor', 'jpn', 'chi_sim', 'eng+kor'],
        description: '인식 언어',
      },
      {
        name: 'psm',
        type: 'select',
        default: '3',
        options: ['0', '1', '3', '4', '6', '7', '11', '12', '13'],
        description: 'Page Segmentation Mode (3: 자동, 6: 단일 블록)',
      },
      {
        name: 'output_type',
        type: 'select',
        default: 'data',
        options: ['string', 'data'],
        description: '출력 형식 (string: 텍스트만, data: 위치정보 포함)',
      },
    ],
    examples: [
      'ImageInput → Tesseract → 영문 도면 텍스트 추출',
      'OCR Ensemble의 구성 엔진 (15% 가중치)',
    ],
    usageTips: [
      '💡 다국어 도면은 lang=eng+kor로 설정하세요',
      '💡 OCR Ensemble과 함께 사용하면 정확도가 향상됩니다',
      '💡 psm=6은 단일 텍스트 블록에 적합합니다',
    ],
  },
  trocr: {
    type: 'trocr',
    label: 'TrOCR',
    category: 'ocr',
    color: '#7c3aed',
    icon: 'Wand2',
    description: 'Microsoft TrOCR (Transformer OCR). Scene Text Recognition에 강점.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 텍스트 라인 이미지 (크롭 권장)',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트',
      },
    ],
    parameters: [
      {
        name: 'model_type',
        type: 'select',
        default: 'printed',
        options: ['printed', 'handwritten'],
        description: '모델 타입 (printed: 인쇄체, handwritten: 필기체)',
      },
      {
        name: 'max_length',
        type: 'number',
        default: 64,
        min: 16,
        max: 256,
        step: 16,
        description: '최대 출력 길이',
      },
      {
        name: 'num_beams',
        type: 'number',
        default: 4,
        min: 1,
        max: 10,
        step: 1,
        description: 'Beam Search 빔 수 (높을수록 정확, 느림)',
      },
    ],
    examples: [
      'YOLO 검출 영역 → TrOCR → 개별 텍스트 인식',
      'OCR Ensemble의 구성 엔진 (10% 가중치)',
    ],
    usageTips: [
      '💡 단일 텍스트 라인 이미지에 최적화되어 있습니다',
      '💡 전체 문서는 YOLO로 텍스트 영역 검출 후 개별 처리 권장',
      '💡 손글씨 스타일 텍스트에 handwritten 모델 사용',
    ],
  },
  esrgan: {
    type: 'esrgan',
    label: 'ESRGAN Upscaler',
    category: 'preprocessing',
    color: '#dc2626',
    icon: 'Maximize2',
    description: 'Real-ESRGAN 기반 4x 이미지 업스케일링. 저품질 스캔 도면 전처리.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 저해상도 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'image',
        type: 'Image',
        description: '✨ 4x 업스케일된 고해상도 이미지',
      },
    ],
    parameters: [
      {
        name: 'scale',
        type: 'select',
        default: '4',
        options: ['2', '4'],
        description: '업스케일 배율',
      },
      {
        name: 'denoise_strength',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.1,
        description: '노이즈 제거 강도 (0: 없음, 1: 최대)',
      },
    ],
    examples: [
      '저품질 스캔 → ESRGAN → 고해상도 → OCR',
      '흐릿한 도면 → ESRGAN 2x → EDGNet → eDOCr2',
    ],
    usageTips: [
      '💡 저품질 스캔 도면에 먼저 적용하면 OCR 정확도가 크게 향상됩니다',
      '💡 scale=2로도 충분한 경우가 많습니다 (4x는 처리 시간 증가)',
      '💡 denoise_strength를 높이면 노이즈가 줄어들지만 디테일도 손실될 수 있습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '저해상도 원본 도면을 업스케일링합니다',
      },
    ],
  },
  ocr_ensemble: {
    type: 'ocr_ensemble',
    label: 'OCR Ensemble',
    category: 'ocr',
    color: '#0891b2',
    icon: 'Layers',
    description: '4개 OCR 엔진 가중 투표 앙상블 (eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%)',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'results',
        type: 'EnsembleResult[]',
        description: '📝 앙상블 결과 (가중 투표 기반)',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
      {
        name: 'engine_results',
        type: 'object',
        description: '🔍 각 엔진별 원본 결과',
      },
    ],
    parameters: [
      {
        name: 'edocr2_weight',
        type: 'number',
        default: 0.40,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'eDOCr2 가중치 (기본 40%)',
      },
      {
        name: 'paddleocr_weight',
        type: 'number',
        default: 0.35,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'PaddleOCR 가중치 (기본 35%)',
      },
      {
        name: 'tesseract_weight',
        type: 'number',
        default: 0.15,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'Tesseract 가중치 (기본 15%)',
      },
      {
        name: 'trocr_weight',
        type: 'number',
        default: 0.10,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'TrOCR 가중치 (기본 10%)',
      },
      {
        name: 'similarity_threshold',
        type: 'number',
        default: 0.7,
        min: 0.5,
        max: 1,
        step: 0.05,
        description: '텍스트 유사도 임계값 (결과 그룹화 기준)',
      },
    ],
    examples: [
      'ImageInput → OCR Ensemble → 최고 정확도 OCR 결과',
      'ESRGAN → OCR Ensemble → 저품질 도면도 정확히 인식',
    ],
    usageTips: [
      '⭐ 단일 OCR 엔진보다 훨씬 높은 정확도를 제공합니다',
      '💡 가중치를 조정하여 특정 엔진에 더 높은 신뢰도 부여 가능',
      '💡 여러 엔진이 동의하는 결과는 신뢰도가 더 높습니다',
      '💡 처리 시간이 단일 엔진보다 길지만 정확도가 훨씬 높습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면에서 4개 OCR 엔진으로 텍스트를 추출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '⭐ 업스케일된 이미지로 OCR 정확도를 극대화합니다',
      },
      {
        from: 'edgnet',
        field: 'segmented_image',
        reason: '전처리된 이미지에서 더 정확한 결과를 얻습니다',
      },
    ],
  },
  suryaocr: {
    type: 'suryaocr',
    label: 'Surya OCR',
    category: 'ocr',
    color: '#8b5cf6',
    icon: 'ScanText',
    description: 'Surya OCR - 90+ 언어 지원, 레이아웃 분석, 높은 정확도. 기계 도면에 최적화.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 또는 문서 이미지',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록 (bbox 포함)',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
      {
        name: 'layout',
        type: 'LayoutElement[]',
        description: '📐 레이아웃 요소 (선택적)',
      },
    ],
    parameters: [
      {
        name: 'languages',
        type: 'string',
        default: 'ko,en',
        description: '인식 언어 (쉼표 구분, 90+ 언어 지원)',
      },
      {
        name: 'detect_layout',
        type: 'boolean',
        default: false,
        description: '레이아웃 분석 활성화 (테이블, 단락 감지)',
      },
    ],
    examples: [
      'ImageInput → Surya OCR → 다국어 도면 텍스트 추출',
      'ESRGAN → Surya OCR → 고정밀 OCR',
    ],
    usageTips: [
      '⭐ 기계 도면 OCR에서 가장 높은 정확도를 제공합니다',
      '💡 90+ 언어를 지원하여 다국어 도면에 적합합니다',
      '💡 detect_layout=true로 테이블/단락 구조 분석 가능',
      '💡 DocTR, EasyOCR보다 기술 도면에서 정확도가 높습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면에서 텍스트를 추출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '⭐ 업스케일된 이미지로 OCR 정확도를 극대화합니다',
      },
    ],
  },
  doctr: {
    type: 'doctr',
    label: 'DocTR',
    category: 'ocr',
    color: '#0ea5e9',
    icon: 'FileText',
    description: 'DocTR (Document Text Recognition) - 문서 OCR 특화, 정규화된 bbox 출력.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 문서 또는 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록 (정규화 bbox)',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
    ],
    parameters: [
      {
        name: 'det_arch',
        type: 'select',
        default: 'db_resnet50',
        options: ['db_resnet50', 'db_mobilenet_v3_large', 'linknet_resnet18'],
        description: '텍스트 검출 모델 아키텍처',
      },
      {
        name: 'reco_arch',
        type: 'select',
        default: 'crnn_vgg16_bn',
        options: ['crnn_vgg16_bn', 'crnn_mobilenet_v3_small', 'master', 'sar_resnet31'],
        description: '텍스트 인식 모델 아키텍처',
      },
      {
        name: 'straighten_pages',
        type: 'boolean',
        default: false,
        description: '기울어진 페이지 자동 보정',
      },
      {
        name: 'export_as_xml',
        type: 'boolean',
        default: false,
        description: 'XML 형식으로 내보내기',
      },
    ],
    examples: [
      'ImageInput → DocTR → 문서 텍스트 추출',
      '기울어진 스캔 → DocTR (straighten=true) → 보정된 OCR',
    ],
    usageTips: [
      '💡 문서 OCR에 특화되어 있으며 정확한 bbox를 제공합니다',
      '💡 straighten_pages=true로 기울어진 스캔 보정 가능',
      '💡 db_resnet50이 가장 정확하고, db_mobilenet이 가장 빠릅니다',
      '💡 기계 도면보다는 일반 문서에 더 적합합니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '문서 이미지에서 텍스트를 추출합니다',
      },
    ],
  },
  easyocr: {
    type: 'easyocr',
    label: 'EasyOCR',
    category: 'ocr',
    color: '#22c55e',
    icon: 'Languages',
    description: 'EasyOCR - 80+ 언어 지원, CPU 친화적, 한국어 지원 우수.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 또는 문서 이미지',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
    ],
    parameters: [
      {
        name: 'languages',
        type: 'string',
        default: 'ko,en',
        description: '인식 언어 (쉼표 구분, ko/en/ja/ch_sim 등)',
      },
      {
        name: 'detail',
        type: 'boolean',
        default: true,
        description: '상세 결과 (bbox 포함)',
      },
      {
        name: 'paragraph',
        type: 'boolean',
        default: false,
        description: '문단 단위로 결합',
      },
      {
        name: 'batch_size',
        type: 'number',
        default: 1,
        min: 1,
        max: 32,
        step: 1,
        description: '배치 크기 (높을수록 빠름, 메모리 증가)',
      },
    ],
    examples: [
      'ImageInput → EasyOCR → 한국어 도면 텍스트 추출',
      'CPU 환경에서 빠른 OCR 처리',
    ],
    usageTips: [
      '💡 CPU에서도 빠르게 동작하여 GPU 없는 환경에 적합합니다',
      '💡 80+ 언어를 지원하며 한국어 인식이 우수합니다',
      '💡 paragraph=true로 문단 단위 텍스트 결합 가능',
      '⚠️ 작은 글자나 기술 용어는 Surya OCR보다 정확도가 낮을 수 있습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '다국어 도면에서 텍스트를 추출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '저해상도 이미지 업스케일 후 OCR 정확도 향상',
      },
    ],
  },
  // =====================
  // P&ID Analysis APIs
  // =====================
  linedetector: {
    type: 'linedetector',
    label: 'Line Detector',
    category: 'segmentation',
    color: '#0d9488',
    icon: 'Minus',
    description: 'P&ID 도면에서 배관 라인과 신호선을 검출합니다. LSD(Line Segment Detector) + Hough Transform 기반.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 P&ID 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'lines',
        type: 'Line[]',
        description: '📏 검출된 라인 목록 (시작점, 끝점, 타입)',
      },
      {
        name: 'intersections',
        type: 'Point[]',
        description: '⭕ 라인 교차점 목록',
      },
      {
        name: 'line_stats',
        type: 'object',
        description: '📊 라인 통계 (총 개수, 타입별 분포)',
      },
    ],
    parameters: [
      {
        name: 'method',
        type: 'select',
        default: 'combined',
        options: ['lsd', 'hough', 'combined'],
        description: '검출 방법 (lsd: 정밀, hough: 빠름, combined: 최고 정확도)',
      },
      {
        name: 'min_length',
        type: 'number',
        default: 0,
        min: 0,
        max: 500,
        step: 10,
        description: '최소 라인 길이 (픽셀). 짧은 라인 필터링. 0=필터링 안함',
      },
      {
        name: 'max_lines',
        type: 'number',
        default: 0,
        min: 0,
        max: 5000,
        step: 100,
        description: '최대 라인 수 제한. 긴 라인 우선. 0=제한 없음',
      },
      {
        name: 'merge_threshold',
        type: 'number',
        default: 10,
        min: 5,
        max: 50,
        step: 5,
        description: '동일선상 라인 병합 거리 (픽셀)',
      },
      {
        name: 'classify_types',
        type: 'boolean',
        default: true,
        description: '라인 타입 분류 (배관 vs 신호선)',
      },
      {
        name: 'classify_colors',
        type: 'boolean',
        default: true,
        description: '🎨 색상 기반 라인 분류 (공정/냉각/증기/신호선 등)',
      },
      {
        name: 'classify_styles',
        type: 'boolean',
        default: true,
        description: '📐 스타일 분류 (실선/점선/점점선)',
      },
      {
        name: 'detect_intersections',
        type: 'boolean',
        default: true,
        description: '교차점 검출 활성화',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: '검출 결과 시각화 생성',
      },
    ],
    examples: [
      'ImageInput → Line Detector → 배관 라인 검출',
      'Line Detector → PID Analyzer → 연결 관계 분석',
    ],
    usageTips: [
      '⭐ YOLO-PID와 함께 사용하면 심볼과 라인의 연결 관계를 분석할 수 있습니다',
      '💡 combined 방법이 가장 정확하지만 처리 시간이 더 깁니다',
      '💡 min_length를 높이면 노이즈가 줄어들지만 짧은 라인을 놓칠 수 있습니다',
      '💡 P&ID Analyzer의 입력으로 사용하여 심볼 간 연결성을 분석합니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: 'P&ID 도면 이미지에서 라인을 검출합니다',
      },
      {
        from: 'edgnet',
        field: 'segmented_image',
        reason: '전처리된 이미지에서 더 정확한 라인 검출이 가능합니다',
      },
    ],
  },
  yolopid: {
    type: 'yolopid',
    label: '[DEPRECATED] YOLO-PID',
    category: 'detection',
    color: '#6b7280',
    icon: 'CircuitBoard',
    deprecated: true,
    deprecatedMessage: '통합 YOLO API 사용: YOLO 노드에서 model_type=pid_symbol 선택',
    description: '⚠️ DEPRECATED - YOLO 노드의 model_type=pid_symbol 사용 권장. P&ID 심볼 검출.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 P&ID 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'symbols',
        type: 'PIDSymbol[]',
        description: '🔧 검출된 P&ID 심볼 목록 (위치, 종류, 신뢰도)',
      },
      {
        name: 'symbol_counts',
        type: 'object',
        description: '📊 심볼 타입별 개수',
      },
    ],
    parameters: [
      {
        name: 'confidence',
        type: 'number',
        default: 0.10,
        min: 0.05,
        max: 0.50,
        step: 0.05,
        description: '신뢰도 임계값 (낮을수록 더 많은 심볼 검출)',
      },
      {
        name: 'slice_height',
        type: 'select',
        default: '512',
        options: ['256', '512', '768', '1024', '4096'],
        description: 'SAHI 슬라이스 높이 (4096=슬라이스 없음, 가장 빠름)',
      },
      {
        name: 'slice_width',
        type: 'select',
        default: '512',
        options: ['256', '512', '768', '1024', '4096'],
        description: 'SAHI 슬라이스 너비 (4096=슬라이스 없음)',
      },
      {
        name: 'overlap_ratio',
        type: 'number',
        default: 0.25,
        min: 0.1,
        max: 0.5,
        step: 0.05,
        description: '슬라이스 오버랩 비율 (높을수록 경계 누락↓)',
      },
      {
        name: 'class_agnostic',
        type: 'boolean',
        default: false,
        description: 'Class-agnostic 모드 (true=모든 심볼을 Symbol로, false=32클래스 분류)',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: '검출 결과 시각화 생성',
      },
    ],
    examples: [
      'ImageInput → YOLO-PID → 밸브, 펌프, 계기 검출',
      'YOLO-PID + Line Detector → PID Analyzer → 연결 분석',
    ],
    usageTips: [
      '⭐ SAHI 기반으로 대형 P&ID 도면에서 작은 심볼도 정확히 검출',
      '💡 32종의 P&ID 심볼을 분류합니다 (밸브, 펌프, 계기, 열교환기 등)',
      '💡 슬라이스 크기를 256으로 설정하면 최정밀 검출, 1024는 빠른 검출',
      '💡 confidence를 낮추면 더 많은 심볼을 검출하지만 오탐 가능성 증가',
      '💡 Line Detector와 함께 사용하여 PID Analyzer로 연결 관계를 분석하세요',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: 'P&ID 도면 이미지에서 심볼을 검출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '저해상도 P&ID 도면 업스케일 후 검출 정확도 향상',
      },
    ],
  },
  pidanalyzer: {
    type: 'pidanalyzer',
    label: 'P&ID Analyzer',
    category: 'analysis',
    color: '#7c3aed',
    icon: 'Network',
    description: 'P&ID 심볼과 라인을 분석하여 연결 관계, BOM, 밸브 시그널 리스트, 장비 목록을 생성합니다.',
    inputs: [
      {
        name: 'symbols',
        type: 'PIDSymbol[]',
        description: '🔧 YOLO-PID가 검출한 심볼 목록',
      },
      {
        name: 'lines',
        type: 'Line[]',
        description: '📏 Line Detector가 검출한 라인 목록',
      },
    ],
    outputs: [
      {
        name: 'connections',
        type: 'Connection[]',
        description: '🔗 심볼 간 연결 관계 그래프',
      },
      {
        name: 'bom',
        type: 'BOMEntry[]',
        description: '📋 BOM (Bill of Materials) 부품 목록',
      },
      {
        name: 'valve_signal_list',
        type: 'ValveSignal[]',
        description: '🎛️ 밸브 시그널 리스트',
      },
      {
        name: 'equipment_list',
        type: 'Equipment[]',
        description: '⚙️ 장비 목록',
      },
    ],
    parameters: [
      {
        name: 'analysis_type',
        type: 'select',
        default: 'full',
        options: ['connectivity', 'bom', 'valve_signals', 'equipment', 'full'],
        description: '분석 유형 (full: 전체 분석)',
      },
      {
        name: 'connection_threshold',
        type: 'number',
        default: 50,
        min: 20,
        max: 200,
        step: 10,
        description: '심볼-라인 연결 거리 임계값 (픽셀)',
      },
      {
        name: 'enable_ocr',
        type: 'boolean',
        default: true,
        description: '🔤 OCR 기반 계기 태그 검출 (FC, TI, LC, PC 등)',
      },
      {
        name: 'generate_bom',
        type: 'boolean',
        default: true,
        description: '📋 BOM (Bill of Materials) 생성',
      },
      {
        name: 'generate_valve_list',
        type: 'boolean',
        default: true,
        description: '🎛️ 밸브 시그널 리스트 생성',
      },
      {
        name: 'generate_equipment_list',
        type: 'boolean',
        default: true,
        description: '⚙️ 장비 리스트 생성',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: '📊 연결 그래프 시각화',
      },
    ],
    examples: [
      'YOLO-PID + Line Detector → PID Analyzer → BOM 생성',
      'PID Analyzer → Design Checker → 설계 오류 검출',
    ],
    usageTips: [
      '⭐ YOLO-PID와 Line Detector의 결과를 함께 입력해야 정확한 분석이 가능합니다',
      '💡 BOM 생성으로 도면에서 부품 목록을 자동 추출합니다',
      '💡 밸브 시그널 리스트로 제어 시스템 연동 정보를 추출합니다',
      '💡 Design Checker와 연결하여 설계 오류를 자동 검출할 수 있습니다',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: '⭐ YOLO (model_type=pid_symbol)로 검출된 심볼의 연결 관계를 분석합니다',
      },
      {
        from: 'linedetector',
        field: 'lines',
        reason: '⭐ 라인 정보로 심볼 간 연결성을 파악합니다',
      },
    ],
  },
  designchecker: {
    type: 'designchecker',
    label: 'Design Checker',
    category: 'analysis',
    color: '#ef4444',
    icon: 'ShieldCheck',
    description: 'P&ID 설계 오류 검출 및 규정 검증. ISO 10628, ISA 5.1 등 표준 준수 여부 확인.',
    inputs: [
      {
        name: 'symbols',
        type: 'PIDSymbol[]',
        description: '🔧 P&ID 심볼 목록',
      },
      {
        name: 'connections',
        type: 'Connection[]',
        description: '🔗 심볼 연결 관계',
      },
    ],
    outputs: [
      {
        name: 'violations',
        type: 'Violation[]',
        description: '⚠️ 검출된 규칙 위반 목록',
      },
      {
        name: 'summary',
        type: 'CheckSummary',
        description: '📊 검사 결과 요약 (오류/경고/정보 개수)',
      },
      {
        name: 'compliance_score',
        type: 'number',
        description: '✅ 규정 준수율 (0-100%)',
      },
    ],
    parameters: [
      {
        name: 'categories',
        type: 'select',
        default: 'all',
        options: ['all', 'connectivity', 'symbol', 'labeling', 'specification', 'standard', 'safety'],
        description: '검사할 규칙 카테고리',
      },
      {
        name: 'severity_threshold',
        type: 'select',
        default: 'info',
        options: ['error', 'warning', 'info'],
        description: '보고할 최소 심각도',
      },
    ],
    examples: [
      'PID Analyzer → Design Checker → 설계 오류 리포트',
      'YOLO-PID → Design Checker → 심볼 규격 검증',
    ],
    usageTips: [
      '⭐ 20+ 설계 규칙을 자동으로 검사합니다 (연결, 심볼, 라벨링, 사양, 표준, 안전)',
      '💡 ISO 10628, ISA 5.1, ASME, IEC 61511 등 주요 표준 지원',
      '💡 compliance_score로 전체 설계 품질을 수치화합니다',
      '💡 severity_threshold를 error로 설정하면 중요한 오류만 표시됩니다',
      '⚠️ 압력용기 안전밸브 누락, 태그번호 중복 등 중요 오류를 검출합니다',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO (model_type=pid_symbol)로 검출된 심볼의 규격 준수 여부를 검사합니다',
      },
      {
        from: 'pidanalyzer',
        field: 'connections',
        reason: '⭐ 심볼 연결 관계를 분석하여 설계 오류를 검출합니다',
      },
    ],
  },
  'blueprint-ai-bom': {
    type: 'blueprint-ai-bom',
    label: 'Blueprint AI BOM',
    category: 'analysis',
    color: '#8b5cf6',
    icon: 'FileSpreadsheet',
    description: 'AI 기반 도면 분석 및 BOM 생성. Human-in-the-Loop 검증 UI를 통해 검출 결과를 확인하고 부품 명세서를 생성합니다.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 분석할 도면 이미지',
      },
      {
        name: 'detections',
        type: 'DetectionResult[]',
        description: '🎯 사전 검출된 객체 (없으면 내부 YOLO 실행)',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'bom_data',
        type: 'BOMData',
        description: '📊 생성된 BOM 데이터 (품목별 수량, 단가, 합계)',
      },
      {
        name: 'items',
        type: 'BOMItem[]',
        description: '📋 BOM 항목 목록',
      },
      {
        name: 'summary',
        type: 'BOMSummary',
        description: '💰 BOM 요약 (총 수량, 소계, 부가세, 합계)',
      },
      {
        name: 'approved_count',
        type: 'number',
        description: '✅ 승인된 검출 수',
      },
      {
        name: 'export_url',
        type: 'string',
        description: '📥 BOM 다운로드 URL',
      },
    ],
    parameters: [
      {
        name: 'confidence',
        type: 'number',
        default: 0.7,
        min: 0.1,
        max: 1,
        step: 0.05,
        description: '검출 신뢰도 임계값',
      },
      {
        name: 'auto_approve_threshold',
        type: 'number',
        default: 0.95,
        min: 0.8,
        max: 1,
        step: 0.01,
        description: '자동 승인 임계값 (이상이면 자동 승인)',
      },
      {
        name: 'export_format',
        type: 'select',
        default: 'excel',
        options: ['excel', 'csv', 'json', 'pdf'],
        description: '내보내기 형식',
      },
      {
        name: 'skip_verification',
        type: 'boolean',
        default: false,
        description: 'Human-in-the-Loop 검증 건너뛰기',
      },
    ],
    examples: [
      '도면 이미지 → YOLO 검출 → Blueprint AI BOM → Excel BOM',
      'YOLO 검출 결과 → Blueprint AI BOM (검증) → BOM 생성',
    ],
    usageTips: [
      '⭐ Human-in-the-Loop: skip_verification=false로 수동 검증',
      '💡 자동화: skip_verification=true, auto_approve_threshold=0.95',
      '💡 27개 산업용 부품 클래스 지원 (valve, pipe, pump, bolt 등)',
      '💡 검증 UI에서 바운딩 박스 수정, 클래스 변경, 승인/반려 가능',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO 검출 결과를 BOM 검증 입력으로 사용합니다',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: '원본 도면 이미지를 업로드합니다',
      },
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
      customAPIs.forEach((api) => {
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
