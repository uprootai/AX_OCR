/**
 * Detection 관련 타입 정의
 * GT (Ground Truth) 비교 및 검출 결과 표시에 사용
 */

/** BBox 좌표 (x1, y1, x2, y2 형식) */
export interface BBoxCoords {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

/** BBox 좌표 (x, y, width, height 형식 - API 응답용) */
export interface BBoxDimensions {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** API 응답의 Detection 결과 */
export interface DetectionResult {
  class_name: string;
  confidence: number;
  bbox: BBoxDimensions | BBoxCoords;
  class_id?: number;
}

/** YOLO 포맷 GT 라벨 */
export interface GTLabel {
  class_id: number;
  class_name: string;
  bbox: BBoxCoords;
  // YOLO 원본 (정규화 좌표)
  normalized?: {
    cx: number;
    cy: number;
    w: number;
    h: number;
  };
}

/** TP 매칭 정보 */
export interface TPMatch {
  detection_idx: number;
  detection_bbox: BBoxCoords;
  detection_class: string;
  detection_confidence: number;
  gt_idx: number;
  gt_bbox: BBoxCoords;
  gt_class: string;
  iou: number;
  class_match: boolean;
}

/** FP (False Positive) 정보 */
export interface FPDetection {
  detection_idx: number;
  bbox: BBoxCoords;
  class_name: string;
  confidence: number;
}

/** FN (False Negative) 정보 */
export interface FNLabel {
  gt_idx: number;
  bbox: BBoxCoords;
  class_name: string;
}

/** GT 비교 메트릭 */
export interface GTMetrics {
  f1_score: number;
  precision: number;
  recall: number;
  tp: number;
  fp: number;
  fn: number;
}

/** GT 비교 결과 */
export interface GTCompareResult {
  gt_count: number;
  detection_count: number;
  tp_matches: TPMatch[];
  fp_detections: FPDetection[];
  fn_labels: FNLabel[];
  metrics: GTMetrics;
}

/** 필터 상태 */
export interface DetectionFilters {
  showTP: boolean;
  showFP: boolean;
  showFN: boolean;
}

/** 색상 설정 */
export interface ColorConfig {
  stroke: string;
  fill: string;
  label: string;
  dash?: number[];
}

/** TP/FP/FN 색상 팔레트 */
export const DETECTION_COLORS: Record<'TP' | 'FP' | 'FN', ColorConfig> = {
  TP: {
    stroke: '#22c55e',  // green-500
    fill: 'rgba(34, 197, 94, 0.1)',
    label: 'rgba(34, 197, 94, 0.9)',
  },
  FP: {
    stroke: '#ef4444',  // red-500
    fill: 'rgba(239, 68, 68, 0.1)',
    label: 'rgba(239, 68, 68, 0.9)',
  },
  FN: {
    stroke: '#eab308',  // yellow-500
    fill: 'rgba(234, 179, 8, 0.1)',
    label: 'rgba(234, 179, 8, 0.9)',
    dash: [5, 5],
  },
};

// === 유틸리티 함수 ===

/**
 * BBox 변환: dimensions → coords
 */
export const bboxToCoords = (bbox: BBoxDimensions): BBoxCoords => ({
  x1: bbox.x,
  y1: bbox.y,
  x2: bbox.x + bbox.width,
  y2: bbox.y + bbox.height,
});

/**
 * BBox 변환: coords → dimensions
 */
export const coordsToBbox = (coords: BBoxCoords): BBoxDimensions => ({
  x: coords.x1,
  y: coords.y1,
  width: coords.x2 - coords.x1,
  height: coords.y2 - coords.y1,
});

/**
 * BBox가 coords 형식인지 확인
 */
export const isBBoxCoords = (bbox: BBoxDimensions | BBoxCoords): bbox is BBoxCoords => {
  return 'x1' in bbox && 'y1' in bbox && 'x2' in bbox && 'y2' in bbox;
};

/**
 * BBox 정규화 (어떤 형식이든 coords로 변환)
 */
export const normalizeBBox = (bbox: BBoxDimensions | BBoxCoords): BBoxCoords => {
  if (isBBoxCoords(bbox)) {
    return bbox;
  }
  return bboxToCoords(bbox);
};

/**
 * IoU (Intersection over Union) 계산
 */
export const calculateIoU = (box1: BBoxCoords, box2: BBoxCoords): number => {
  const x1 = Math.max(box1.x1, box2.x1);
  const y1 = Math.max(box1.y1, box2.y1);
  const x2 = Math.min(box1.x2, box2.x2);
  const y2 = Math.min(box1.y2, box2.y2);

  const intersection = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);

  const area1 = (box1.x2 - box1.x1) * (box1.y2 - box1.y1);
  const area2 = (box2.x2 - box2.x1) * (box2.y2 - box2.y1);
  const union = area1 + area2 - intersection;

  return union > 0 ? intersection / union : 0;
};

/**
 * YOLO 클래스 매핑 (class_id → class_name)
 * 파나시아 모델 기준
 */
export const YOLO_CLASS_NAMES: Record<number, string> = {
  0: 'dimension',
  1: 'text',
  2: 'table',
  3: 'symbol',
  4: 'line',
  5: 'arrow',
  6: 'title_block',
  7: 'revision_block',
  8: 'bom_table',
  9: 'gdt_frame',
  10: 'weld_symbol',
  11: 'surface_finish',
  12: 'note',
  13: 'leader',
  14: 'centerline',
};

/**
 * YOLO 포맷 파싱 (정규화 좌표 → 픽셀 좌표)
 */
export const parseYOLOFormat = (
  content: string,
  imageWidth: number,
  imageHeight: number
): GTLabel[] => {
  const lines = content.trim().split('\n');
  const labels: GTLabel[] = [];

  for (const line of lines) {
    const parts = line.trim().split(/\s+/);
    if (parts.length < 5) continue;

    const class_id = parseInt(parts[0], 10);
    const cx = parseFloat(parts[1]); // 중심 x (정규화)
    const cy = parseFloat(parts[2]); // 중심 y (정규화)
    const w = parseFloat(parts[3]);  // 너비 (정규화)
    const h = parseFloat(parts[4]);  // 높이 (정규화)

    // 정규화 좌표 → 픽셀 좌표
    const x1 = (cx - w / 2) * imageWidth;
    const y1 = (cy - h / 2) * imageHeight;
    const x2 = (cx + w / 2) * imageWidth;
    const y2 = (cy + h / 2) * imageHeight;

    labels.push({
      class_id,
      class_name: YOLO_CLASS_NAMES[class_id] || `class_${class_id}`,
      bbox: { x1, y1, x2, y2 },
      normalized: { cx, cy, w, h },
    });
  }

  return labels;
};

/**
 * GT 비교 수행
 */
export const compareWithGT = (
  detections: DetectionResult[],
  gtLabels: GTLabel[],
  iouThreshold: number = 0.5
): GTCompareResult => {
  const normalizedDetections = detections.map((d) => ({
    ...d,
    bbox: normalizeBBox(d.bbox),
  }));

  const matchedGTIndices = new Set<number>();
  const matchedDetectionIndices = new Set<number>();
  const tp_matches: TPMatch[] = [];

  // 각 detection에 대해 가장 높은 IoU를 가진 GT 찾기
  for (let di = 0; di < normalizedDetections.length; di++) {
    const detection = normalizedDetections[di];
    let bestIoU = 0;
    let bestGTIdx = -1;

    for (let gi = 0; gi < gtLabels.length; gi++) {
      if (matchedGTIndices.has(gi)) continue;

      const iou = calculateIoU(detection.bbox as BBoxCoords, gtLabels[gi].bbox);
      if (iou > bestIoU) {
        bestIoU = iou;
        bestGTIdx = gi;
      }
    }

    if (bestIoU >= iouThreshold && bestGTIdx >= 0) {
      matchedGTIndices.add(bestGTIdx);
      matchedDetectionIndices.add(di);
      tp_matches.push({
        detection_idx: di,
        detection_bbox: detection.bbox as BBoxCoords,
        detection_class: detection.class_name,
        detection_confidence: detection.confidence,
        gt_idx: bestGTIdx,
        gt_bbox: gtLabels[bestGTIdx].bbox,
        gt_class: gtLabels[bestGTIdx].class_name,
        iou: bestIoU,
        class_match: detection.class_name === gtLabels[bestGTIdx].class_name,
      });
    }
  }

  // FP: 매칭되지 않은 detection
  const fp_detections: FPDetection[] = normalizedDetections
    .filter((_, idx) => !matchedDetectionIndices.has(idx))
    .map((d, idx) => {
      const originalIdx = normalizedDetections.findIndex(
        (nd, i) => !matchedDetectionIndices.has(i) && nd === d
      );
      return {
        detection_idx: originalIdx >= 0 ? originalIdx : idx,
        bbox: d.bbox as BBoxCoords,
        class_name: d.class_name,
        confidence: d.confidence,
      };
    });

  // FN: 매칭되지 않은 GT
  const fn_labels: FNLabel[] = gtLabels
    .filter((_, idx) => !matchedGTIndices.has(idx))
    .map((gt) => ({
      gt_idx: gtLabels.findIndex((g, i) => !matchedGTIndices.has(i) && g === gt),
      bbox: gt.bbox,
      class_name: gt.class_name,
    }));

  // 메트릭 계산
  const tp = tp_matches.length;
  const fp = fp_detections.length;
  const fn = fn_labels.length;
  const precision = tp + fp > 0 ? tp / (tp + fp) : 0;
  const recall = tp + fn > 0 ? tp / (tp + fn) : 0;
  const f1_score = precision + recall > 0 ? 2 * (precision * recall) / (precision + recall) : 0;

  return {
    gt_count: gtLabels.length,
    detection_count: detections.length,
    tp_matches,
    fp_detections,
    fn_labels,
    metrics: {
      f1_score,
      precision,
      recall,
      tp,
      fp,
      fn,
    },
  };
};
