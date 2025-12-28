/**
 * Segmentation Nodes
 * 이미지 세그멘테이션 및 라인 검출 노드 정의
 */

import type { NodeDefinition } from './types';

export const segmentationNodes: Record<string, NodeDefinition> = {
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
        description: '📏 검출된 라인 목록 (시작점, 끝점, 타입, 스타일)',
      },
      {
        name: 'intersections',
        type: 'Point[]',
        description: '⭕ 라인 교차점 목록',
      },
      {
        name: 'regions',
        type: 'Region[]',
        description: '📦 점선 박스 영역 목록 (SIGNAL FOR BWMS 등)',
      },
      {
        name: 'line_stats',
        type: 'object',
        description: '📊 라인/영역 통계 (총 개수, 타입별 분포)',
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
        name: 'detect_regions',
        type: 'boolean',
        default: false,
        description: '📦 점선 박스 영역 검출 (SIGNAL FOR BWMS 등)',
      },
      {
        name: 'region_line_styles',
        type: 'string',
        default: 'dashed,dash_dot',
        description: '영역 검출에 사용할 라인 스타일 (쉼표 구분: dashed, dash_dot, dotted)',
      },
      {
        name: 'min_region_area',
        type: 'number',
        default: 5000,
        min: 1000,
        max: 100000,
        step: 1000,
        description: '최소 영역 크기 (픽셀²). 작은 영역 필터링',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: '검출 결과 시각화 생성',
      },
      {
        name: 'visualize_regions',
        type: 'boolean',
        default: true,
        description: '검출된 영역 시각화 포함',
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
      '📦 detect_regions를 활성화하면 점선 박스 영역(SIGNAL FOR BWMS 등)을 자동 검출합니다',
      '🎨 classify_styles로 실선/점선/일점쇄선 등 라인 스타일을 분류할 수 있습니다',
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
};
