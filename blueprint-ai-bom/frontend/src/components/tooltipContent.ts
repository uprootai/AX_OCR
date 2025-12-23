/**
 * 기능별 툴팁 내용 정의
 * Tooltip.tsx에서 분리 - Fast Refresh 호환성
 */

export const FEATURE_TOOLTIPS = {
  // 참조 도면 섹션
  referenceDrawing: {
    title: '📐 참조 도면',
    description: '업로드된 도면 이미지 정보입니다. 이미지 크기, 검출된 심볼 수, 검증 현황을 확인할 수 있습니다.',
  },
  imageSize: {
    title: '이미지 크기',
    description: '도면 이미지의 가로 × 세로 픽셀 해상도입니다.',
  },
  detectionCount: {
    title: '검출 수',
    description: 'YOLO 모델이 도면에서 검출한 심볼의 총 개수입니다.',
  },
  approvedCount: {
    title: '승인 수',
    description: '사용자가 검증하여 승인한 심볼의 개수입니다. BOM에 포함됩니다.',
  },

  // VLM 도면 분류
  vlmClassifier: {
    title: 'VLM 도면 분류',
    description: 'Vision-Language 모델을 사용하여 도면의 종류를 자동으로 분류합니다. 기계 부품도, P&ID, 조립도, 전기 회로도, 건축 도면 등을 구분할 수 있습니다.',
  },
  autoClassify: {
    title: '자동 분류',
    description: 'Local VL 모델을 사용하여 도면 타입을 자동으로 분석합니다. GPU가 필요합니다.',
  },
  manualClassify: {
    title: '수동 분류',
    description: '도면 타입을 직접 선택합니다. 자동 분류가 정확하지 않을 때 사용하세요.',
  },

  // AI 검출 결과
  detectionResults: {
    title: '🔍 AI 검출 결과',
    description: 'YOLO 모델이 도면에서 검출한 심볼 목록입니다. Ground Truth와 비교하여 정확도를 측정합니다.',
  },
  groundTruth: {
    title: 'Ground Truth (GT)',
    description: '사전에 라벨링된 정답 데이터입니다. 검출 결과와 비교하여 모델 성능(Precision, Recall, F1)을 측정합니다.',
  },
  precision: {
    title: 'Precision (정밀도)',
    description: '검출된 결과 중 실제로 맞는 비율입니다. FP(오검출)가 적을수록 높습니다. 계산식: TP / (TP + FP)',
  },
  recall: {
    title: 'Recall (재현율)',
    description: '실제 존재하는 심볼 중 검출된 비율입니다. FN(미검출)이 적을수록 높습니다. 계산식: TP / (TP + FN)',
  },
  f1Score: {
    title: 'F1 Score',
    description: 'Precision과 Recall의 조화 평균입니다. 두 지표의 균형을 나타냅니다. 계산식: 2 × (P × R) / (P + R)',
  },
  confidence: {
    title: '신뢰도 (Confidence)',
    description: '모델이 해당 검출에 대해 확신하는 정도입니다. 0~100% 사이의 값으로, 높을수록 신뢰할 수 있습니다.',
  },

  // 심볼 검증
  symbolVerification: {
    title: '✅ 심볼 검증 및 수정',
    description: '검출된 심볼을 하나씩 확인하고 승인/거부/수정합니다. Human-in-the-Loop 방식으로 정확도를 높입니다.',
  },
  approveAll: {
    title: '전체 승인',
    description: '현재 페이지의 모든 검출 결과를 한 번에 승인합니다.',
  },
  rejectAll: {
    title: '전체 거부',
    description: '현재 페이지의 모든 검출 결과를 한 번에 거부합니다. 거부된 항목은 BOM에 포함되지 않습니다.',
  },
  showGT: {
    title: 'GT 이미지 표시',
    description: 'Ground Truth 바운딩박스를 도면 위에 오버레이로 표시합니다. 녹색으로 표시됩니다.',
  },
  showReference: {
    title: '참조 이미지 표시',
    description: '각 심볼 클래스의 참조 이미지를 표시합니다. 심볼 식별에 도움이 됩니다.',
  },
  manualLabel: {
    title: '수작업 라벨 추가',
    description: '모델이 놓친 심볼을 직접 추가합니다. 도면을 클릭하여 바운딩박스를 그리고 클래스를 선택합니다.',
  },
  editDetection: {
    title: '검출 수정',
    description: '검출된 심볼의 클래스명이나 바운딩박스를 수정합니다.',
  },

  // 선 검출
  lineDetection: {
    title: '📐 선 검출',
    description: '도면의 선을 분석하여 치수선, 배관, 신호선 등을 자동으로 분류합니다. Phase 2 관계 추출에 사용됩니다.',
  },

  // 치수 OCR
  dimensionOCR: {
    title: '📏 치수 OCR',
    description: '도면의 치수 텍스트를 인식합니다. 100mm, Ø50 등의 치수값을 추출하고 단위와 공차를 파싱합니다.',
  },

  // 치수-객체 관계
  dimensionRelation: {
    title: '🔗 치수-객체 관계',
    description: '치수와 심볼 간의 관계를 추출합니다. 치수선 분석, 연장선 추적, 근접성 기반으로 자동 연결하고, 수동으로 수정할 수 있습니다.',
  },
  manualLink: {
    title: '수동 연결',
    description: '치수를 특정 심볼에 수동으로 연결합니다. 자동 추출이 정확하지 않을 때 사용하세요.',
  },
  deleteRelation: {
    title: '관계 삭제',
    description: '잘못된 관계를 삭제합니다. 삭제된 관계는 BOM 생성 시 반영되지 않습니다.',
  },

  // BOM 관련
  verificationComplete: {
    title: '검증 완료',
    description: '심볼 검증을 완료하고 BOM을 생성합니다. 승인된 심볼만 BOM에 포함됩니다.',
  },
  bomGeneration: {
    title: 'BOM 생성 및 내보내기',
    description: '검증된 심볼을 기반으로 BOM(Bill of Materials)을 생성합니다. Excel, CSV, JSON 형식으로 내보낼 수 있습니다.',
  },
  exportFormat: {
    title: '내보내기 형식',
    description: 'Excel(.xlsx): 표준 스프레드시트, CSV: 텍스트 기반, JSON: 개발자용 데이터 형식',
  },
  generateBOM: {
    title: 'BOM 생성',
    description: '승인된 심볼을 집계하여 BOM을 생성합니다. 동일 심볼은 수량으로 합산됩니다.',
  },

  // 세션 관리
  sessionManagement: {
    title: '세션 관리',
    description: '작업 세션을 관리합니다. 각 도면은 고유한 세션 ID를 가지며, 세션에는 검출 결과, 검증 상태, BOM 데이터가 저장됩니다.',
  },
};
