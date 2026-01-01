/**
 * Output Data Extractors
 * 노드 출력 데이터에서 배열/이미지 등을 추출하는 유틸리티
 */

/**
 * 배열 데이터 추출 유틸리티
 * 노드 출력에서 알려진 배열 필드를 추출
 */
export function extractArrayData(output: Record<string, unknown>): {
  field: string;
  data: unknown[];
  title: string;
}[] {
  const knownArrayFields: Record<string, string> = {
    // OCR
    'dimensions': '치수 목록',
    'gdt': 'GD&T 목록',
    'texts': '텍스트 목록',
    'text_results': '텍스트 결과',

    // Detection
    'detections': '검출 결과',
    'predictions': '예측 결과',

    // Line Detector
    'lines': '라인 목록',
    'intersections': '교차점 목록',

    // PID Analyzer
    'connections': '연결 관계',
    'bom': 'BOM (부품 목록)',
    'valve_list': '밸브 시그널 리스트',
    'equipment_list': '장비 목록',
    'ocr_instruments': 'OCR 계기 태그',

    // Design Checker
    'violations': '위반 항목',
    'warnings': '경고 항목',
    'recommendations': '권장 사항',
  };

  const results: { field: string; data: unknown[]; title: string }[] = [];

  for (const [field, title] of Object.entries(knownArrayFields)) {
    const value = output[field];
    if (Array.isArray(value) && value.length > 0) {
      results.push({ field, data: value, title });
    }
  }

  return results;
}

/**
 * 시각화 이미지 추출 유틸리티
 * 노드 출력에서 base64 이미지 필드를 추출
 */
export function extractVisualizationImages(output: Record<string, unknown>): {
  field: string;
  base64: string;
  title: string;
}[] {
  const visualizationFields: Record<string, string> = {
    'visualization': '결과 시각화',
    'visualized_image': '시각화 이미지',
    'annotated_image': '어노테이션 이미지',
    'result_image': '결과 이미지',
    'output_image': '출력 이미지',
    'image': '이미지',
    'segmentation_mask': '세그멘테이션 마스크',
    'upscaled_image': '업스케일 이미지',
    'enhanced_image': '향상된 이미지',
  };

  const results: { field: string; base64: string; title: string }[] = [];

  for (const [field, title] of Object.entries(visualizationFields)) {
    const value = output[field];
    if (typeof value === 'string' && value.length > 100) {
      // base64 이미지로 추정
      results.push({ field, base64: value, title });
    }
  }

  return results;
}
