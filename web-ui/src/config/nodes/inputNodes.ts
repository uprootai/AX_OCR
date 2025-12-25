/**
 * Input Nodes
 * 워크플로우 입력 노드 정의
 *
 * 2025-12-24: 기능 기반 재설계 (v2)
 * - drawing_type 파라미터 제거, features 체크박스만 사용
 * - features 기반 추천 노드 표시
 */

import type { NodeDefinition } from './types';

/**
 * 기능 목록 (Blueprint AI BOM이 제공하는 모든 기능)
 * ImageInput에서 선택하면 세션 UI에 해당 기능만 표시됨
 */
export const BOM_FEATURES = {
  symbol_detection: { label: '심볼 검출', hint: 'YOLO 노드 필요', icon: '🎯' },
  symbol_verification: { label: '심볼 검증 (승인/거부/수정)', hint: '', icon: '✅' },
  dimension_ocr: { label: '치수 OCR', hint: 'eDOCr2 노드 필요', icon: '📏' },
  dimension_verification: { label: '치수 검증 (승인/거부/수정)', hint: '', icon: '✅' },
  gt_comparison: { label: 'GT 비교 (정밀도/재현율)', hint: 'GT 파일 필요', icon: '📊' },
  bom_generation: { label: 'BOM 생성', hint: 'AI BOM 노드 필요', icon: '📋' },
  gdt_parsing: { label: 'GD&T 파싱', hint: 'SkinModel 노드 필요', icon: '📐' },
  // 단기 로드맵 기능 (2025-12-24)
  line_detection: { label: '선 검출', hint: 'Line Detector 노드 필요', icon: '📐' },
  pid_connectivity: { label: 'P&ID 연결성', hint: 'PID Analyzer 노드 필요', icon: '🔗' },
  title_block_ocr: { label: '표제란 OCR', hint: 'eDOCr2 노드 필요', icon: '📝' },
  // 중기 로드맵 기능 (2025-12-24)
  welding_symbol_parsing: { label: '용접 기호 파싱', hint: 'YOLO 학습 필요', icon: '🔩' },
  surface_roughness_parsing: { label: '표면 거칠기 파싱', hint: 'SkinModel 확장', icon: '🪨' },
  quantity_extraction: { label: '수량 추출', hint: 'eDOCr2 노드 필요', icon: '🔢' },
  balloon_matching: { label: '벌룬 번호 매칭', hint: 'YOLO + eDOCr2 필요', icon: '🎈' },
  // 장기 로드맵 기능 (2025-12-24)
  drawing_region_segmentation: { label: '도면 영역 세분화', hint: 'SAM/U-Net 모델 필요', icon: '🗺️' },
  notes_extraction: { label: '주석/노트 추출', hint: 'LLM 분류 필요', icon: '📋' },
  revision_comparison: { label: '리비전 비교', hint: 'SIFT/ORB 정합 필요', icon: '🔄' },
  vlm_auto_classification: { label: 'VLM 자동 분류', hint: 'VL API 필요', icon: '🤖' },
} as const;

export type BOMFeature = keyof typeof BOM_FEATURES;

/**
 * features 기반 추천 노드 매핑
 * 선택된 features에 따라 필요한 노드를 추천
 */
export const FEATURE_NODE_RECOMMENDATIONS: Record<string, {
  nodes: string[];
  description: string;
}> = {
  symbol_detection: {
    nodes: ['yolo'],
    description: 'YOLO로 심볼/부품 검출',
  },
  dimension_ocr: {
    nodes: ['edocr2'],
    description: 'eDOCr2로 치수 인식',
  },
  bom_generation: {
    nodes: ['blueprint-ai-bom'],
    description: 'AI BOM으로 부품 목록 생성',
  },
  gdt_parsing: {
    nodes: ['skinmodel'],
    description: 'SkinModel로 공차 분석',
  },
  // 단기 로드맵 기능 (2025-12-24)
  line_detection: {
    nodes: ['line-detector'],
    description: 'Line Detector로 배관/연결선 검출',
  },
  pid_connectivity: {
    nodes: ['pid-analyzer', 'line-detector', 'yolo-pid'],
    description: 'P&ID 기기 연결 관계 분석',
  },
  title_block_ocr: {
    nodes: ['edocr2'],
    description: '표제란 메타데이터 추출 (도면번호, 리비전 등)',
  },
  // 중기 로드맵 기능 (2025-12-24)
  welding_symbol_parsing: {
    nodes: ['yolo', 'edocr2'],
    description: '용접 기호 검출 및 파싱 (타입, 크기, 깊이)',
  },
  surface_roughness_parsing: {
    nodes: ['yolo', 'edocr2', 'skinmodel'],
    description: '표면 거칠기 기호 파싱 (Ra, Rz 값)',
  },
  quantity_extraction: {
    nodes: ['edocr2'],
    description: '부품 수량 정보 자동 추출 (QTY, 수량 등)',
  },
  balloon_matching: {
    nodes: ['yolo', 'edocr2'],
    description: '벌룬 번호와 심볼 자동 매칭',
  },
  // 장기 로드맵 기능 (2025-12-24)
  drawing_region_segmentation: {
    nodes: ['edgnet'],
    description: 'SAM/U-Net으로 도면 뷰 영역 자동 구분',
  },
  notes_extraction: {
    nodes: ['edocr2', 'vl'],
    description: 'OCR + LLM으로 노트/주석 추출 및 분류',
  },
  revision_comparison: {
    nodes: [],
    description: 'SIFT/ORB 정합으로 리비전 간 변경점 감지',
  },
  vlm_auto_classification: {
    nodes: ['vl'],
    description: 'VLM으로 도면 타입 및 기능 자동 추천',
  },
};

/**
 * 추천 노드 목록 계산 (features 기반)
 */
export function getRecommendedNodes(features: string[]): string[] {
  const nodes = new Set<string>();
  for (const feature of features) {
    const rec = FEATURE_NODE_RECOMMENDATIONS[feature];
    if (rec) {
      rec.nodes.forEach(node => nodes.add(node));
    }
  }
  return Array.from(nodes);
}

export const inputNodes: Record<string, NodeDefinition> = {
  imageinput: {
    type: 'imageinput',
    label: 'Image Input',
    category: 'input',
    color: '#f97316',
    icon: 'Image',
    description: '워크플로우의 시작점. 업로드된 이미지를 다른 노드로 전달합니다. 활성화할 기능을 선택하면 필요한 노드를 추천합니다.',
    inputs: [],
    outputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 업로드된 도면 이미지',
      },
      {
        name: 'features',
        type: 'string[]',
        description: '🔧 활성화된 기능 목록',
      },
    ],
    parameters: [
      {
        name: 'features',
        type: 'checkboxGroup',
        default: ['dimension_ocr', 'dimension_verification', 'gt_comparison'],  // 기본값: 치수 도면
        options: [
          { value: 'symbol_detection', label: '심볼 검출', hint: 'YOLO 노드 추천', icon: '🎯', description: 'YOLO 딥러닝 모델을 사용하여 도면 내 심볼(부품, 기호, 마크 등)을 자동으로 검출합니다. 14가지 심볼 클래스를 지원합니다.' },
          { value: 'symbol_verification', label: '심볼 검증 (승인/거부/수정)', hint: '', icon: '✅', description: '검출된 심볼을 사람이 검토하고 승인/거부/수정할 수 있는 Human-in-the-Loop 기능입니다. 검증된 데이터는 모델 재학습에 활용됩니다.' },
          { value: 'dimension_ocr', label: '치수 OCR', hint: 'eDOCr2 노드 추천', icon: '📏', description: 'eDOCr2 엔진으로 도면의 치수 텍스트(길이, 각도, 공차 등)를 인식합니다. 한국어/영어 혼합 지원, 98% 이상의 정확도.' },
          { value: 'dimension_verification', label: '치수 검증 (승인/거부/수정)', hint: '', icon: '✅', description: 'OCR로 인식된 치수 값을 검토하고 수정할 수 있습니다. 오인식된 값을 직접 수정하여 정확한 BOM 생성에 기여합니다.' },
          { value: 'gt_comparison', label: 'GT 비교 (정밀도/재현율)', hint: 'GT 파일 필요', icon: '📊', description: 'Ground Truth(정답 데이터)와 검출 결과를 비교하여 정밀도(Precision), 재현율(Recall), F1 스코어를 계산합니다.' },
          { value: 'bom_generation', label: 'BOM 생성', hint: 'AI BOM 노드 추천', icon: '📋', description: '검증된 심볼과 치수 데이터를 기반으로 Bill of Materials(부품 목록)를 자동 생성합니다. Excel, CSV, JSON 형식으로 내보내기 가능.' },
          { value: 'gdt_parsing', label: 'GD&T 파싱', hint: 'SkinModel 노드 추천', icon: '📐', description: '기하공차(GD&T) 기호를 파싱합니다. 위치도, 평행도, 직각도 등 14가지 기하특성과 데이텀 참조를 추출합니다.' },
          // 단기 로드맵 기능 (2025-12-24)
          { value: 'line_detection', label: '선 검출', hint: 'Line Detector 노드 추천', icon: '📐', description: '도면의 선(실선, 점선, 쇄선 등)을 검출하고 유형을 분류합니다. 치수선, 중심선, 외형선을 구분하여 관계 분석에 활용됩니다.' },
          { value: 'pid_connectivity', label: 'P&ID 연결성', hint: 'PID Analyzer 노드 추천', icon: '🔗', description: 'P&ID(배관계장도) 도면에서 기기 간 연결 관계를 분석합니다. 밸브, 펌프, 탱크 등의 연결 토폴로지를 추출합니다.' },
          { value: 'title_block_ocr', label: '표제란 OCR', hint: '도면번호/리비전 추출', icon: '📝', description: '도면 표제란(Title Block)에서 도면번호, 리비전, 작성일, 스케일 등 메타데이터를 자동 추출합니다.' },
          // 중기 로드맵 기능 (2025-12-24)
          { value: 'welding_symbol_parsing', label: '용접 기호 파싱', hint: '용접 타입/크기 추출', icon: '🔩', description: 'AWS/ISO 표준 용접 기호를 파싱합니다. 용접 타입(필렛, 맞대기 등), 크기, 깊이, 위치(화살표측/반대측)를 추출합니다.' },
          { value: 'surface_roughness_parsing', label: '표면 거칠기 파싱', hint: 'Ra/Rz 값 추출', icon: '🪨', description: '표면 거칠기 기호에서 Ra, Rz, Rq 값과 가공 방법, 방향성 패턴을 추출합니다. 제거/비제거 가공 여부도 판별합니다.' },
          { value: 'quantity_extraction', label: '수량 추출', hint: 'QTY/수량 패턴 인식', icon: '🔢', description: '도면 또는 BOM 테이블에서 부품 수량(QTY, EA, 개 등) 정보를 자동 추출합니다. 정규식 패턴과 위치 기반 분석을 결합합니다.' },
          { value: 'balloon_matching', label: '벌룬 번호 매칭', hint: '부품번호-심볼 연결', icon: '🎈', description: '도면의 벌룬(풍선) 번호와 해당 심볼을 자동 매칭합니다. 부품번호와 실제 부품 위치를 연결하여 BOM 생성에 활용됩니다.' },
          // 장기 로드맵 기능 (2025-12-24)
          { value: 'drawing_region_segmentation', label: '도면 영역 세분화', hint: '뷰 영역 자동 구분', icon: '🗺️', description: 'SAM/U-Net 모델로 도면의 뷰 영역(정면도, 측면도, 단면도, 상세도, 표제란)을 자동 구분합니다. 각 영역별 독립 분석이 가능해집니다.' },
          { value: 'notes_extraction', label: '주석/노트 추출', hint: '재료/공차/열처리 추출', icon: '📋', description: 'OCR과 LLM을 결합하여 도면 노트 영역에서 재료 사양, 일반 공차, 열처리 조건, 도장 사양 등을 추출하고 카테고리별로 분류합니다.' },
          { value: 'revision_comparison', label: '리비전 비교', hint: '도면 변경점 감지', icon: '🔄', description: 'SIFT/ORB 특징점 매칭으로 두 리비전 간 변경점을 자동 감지합니다. 추가/수정/삭제된 심볼, 치수, 주석을 하이라이트 표시합니다.' },
          { value: 'vlm_auto_classification', label: 'VLM 자동 분류', hint: '도면 타입 AI 분류', icon: '🤖', description: 'Vision-Language 모델이 도면을 분석하여 타입(기계도면, 전기도면, P&ID 등), 산업 분야, 복잡도를 자동 분류하고 적합한 기능을 추천합니다.' },
        ],
        description: '🔧 활성화 기능',
        tooltip: '세션 UI에 표시될 기능들을 선택합니다. 선택한 기능에 맞는 노드가 추천됩니다.',
      },
    ],
    examples: [
      '모든 워크플로우의 시작점으로 사용',
      'YOLO, eDOCr2 등 API 노드의 입력 소스',
      '이미지 업로드 후 자동으로 데이터 제공',
      '기능 선택 → 추천 노드 확인 → 파이프라인 구성',
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
};
