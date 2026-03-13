/**
 * useDetectionData - 검출 결과 상태, GT 로드, 캔버스 그리기 훅
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import type { NodeStatus } from '../../../store/workflowStore';
import {
  type DetectionResult,
  type GTLabel,
  type GTCompareResult,
  type DetectionFilters,
  DETECTION_COLORS,
  parseYOLOFormat,
  compareWithGT,
  normalizeBBox,
} from '../../../types/detection';

export function useDetectionData(
  nodeStatus: NodeStatus,
  uploadedImage: string | null,
  uploadedFileName: string | null,
) {
  const [gtLabels, setGTLabels] = useState<GTLabel[] | null>(null);
  const [gtLoading, setGTLoading] = useState(false);
  const [, setGTError] = useState<string | null>(null);
  const [compareResult, setCompareResult] = useState<GTCompareResult | null>(null);
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const [filters, setFilters] = useState<DetectionFilters>({
    showTP: true,
    showFP: true,
    showFN: true,
  });
  const [showCanvas, setShowCanvas] = useState(true);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 검출 결과 추출
  const detections = useMemo(() => {
    const output = nodeStatus.output;
    if (!output) return [];
    return (output.detections as DetectionResult[]) || [];
  }, [nodeStatus.output]);

  // 평균 신뢰도 계산
  const avgConfidence = useMemo(() => {
    if (detections.length === 0) return 0;
    const sum = detections.reduce((acc, d) => acc + d.confidence, 0);
    return sum / detections.length;
  }, [detections]);

  // 이미지 크기 로드
  useEffect(() => {
    if (!uploadedImage) return;

    const img = new Image();
    img.onload = () => {
      setImageSize({ width: img.width, height: img.height });
    };
    img.src = uploadedImage;
  }, [uploadedImage]);

  // GT 파일 자동 로드 시도
  useEffect(() => {
    const loadGT = async () => {
      if (!uploadedFileName || !imageSize) return;

      const gtFileName = uploadedFileName.replace(/\.(png|jpg|jpeg|gif|bmp|webp)$/i, '.txt');

      const possiblePaths = [
        `/datasets/labels/${gtFileName}`,
        `/gt/${gtFileName}`,
        `/labels/${gtFileName}`,
        `/${gtFileName}`,
      ];

      setGTLoading(true);
      setGTError(null);

      for (const path of possiblePaths) {
        try {
          const response = await fetch(path);
          if (response.ok) {
            const content = await response.text();
            const labels = parseYOLOFormat(content, imageSize.width, imageSize.height);
            if (labels.length > 0) {
              setGTLabels(labels);
              setGTLoading(false);
              return;
            }
          }
        } catch {
          // 다음 경로 시도
        }
      }

      setGTLoading(false);
    };

    loadGT();
  }, [uploadedFileName, imageSize]);

  // GT 비교 수행
  useEffect(() => {
    if (!gtLabels || detections.length === 0) {
      setCompareResult(null);
      return;
    }

    const result = compareWithGT(detections, gtLabels, 0.5);
    setCompareResult(result);
  }, [detections, gtLabels]);

  // 캔버스 그리기
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx || !uploadedImage || !imageSize) return;

    const containerWidth = containerRef.current?.clientWidth || 340;
    const maxHeight = 300;
    const aspectRatio = imageSize.width / imageSize.height;

    let canvasWidth = containerWidth;
    let canvasHeight = containerWidth / aspectRatio;

    if (canvasHeight > maxHeight) {
      canvasHeight = maxHeight;
      canvasWidth = maxHeight * aspectRatio;
    }

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    const scaleX = canvasWidth / imageSize.width;
    const scaleY = canvasHeight / imageSize.height;

    const img = new Image();
    img.onload = () => {
      ctx.drawImage(img, 0, 0, canvasWidth, canvasHeight);

      if (compareResult) {
        // TP 그리기 (녹색)
        if (filters.showTP) {
          ctx.strokeStyle = DETECTION_COLORS.TP.stroke;
          ctx.fillStyle = DETECTION_COLORS.TP.fill;
          ctx.lineWidth = 2;
          ctx.setLineDash([]);

          for (const tp of compareResult.tp_matches) {
            const bbox = tp.detection_bbox;
            const x = bbox.x1 * scaleX;
            const y = bbox.y1 * scaleY;
            const w = (bbox.x2 - bbox.x1) * scaleX;
            const h = (bbox.y2 - bbox.y1) * scaleY;

            ctx.fillRect(x, y, w, h);
            ctx.strokeRect(x, y, w, h);

            ctx.fillStyle = DETECTION_COLORS.TP.label;
            ctx.font = 'bold 10px sans-serif';
            const label = `${tp.detection_class} ${(tp.detection_confidence * 100).toFixed(0)}%`;
            const textWidth = ctx.measureText(label).width;
            ctx.fillRect(x, y - 14, textWidth + 4, 14);
            ctx.fillStyle = 'white';
            ctx.fillText(label, x + 2, y - 3);
          }
        }

        // FP 그리기 (빨강)
        if (filters.showFP) {
          ctx.strokeStyle = DETECTION_COLORS.FP.stroke;
          ctx.fillStyle = DETECTION_COLORS.FP.fill;
          ctx.lineWidth = 2;
          ctx.setLineDash([]);

          for (const fp of compareResult.fp_detections) {
            const bbox = fp.bbox;
            const x = bbox.x1 * scaleX;
            const y = bbox.y1 * scaleY;
            const w = (bbox.x2 - bbox.x1) * scaleX;
            const h = (bbox.y2 - bbox.y1) * scaleY;

            ctx.fillRect(x, y, w, h);
            ctx.strokeRect(x, y, w, h);

            ctx.fillStyle = DETECTION_COLORS.FP.label;
            ctx.font = 'bold 10px sans-serif';
            const label = `FP: ${fp.class_name}`;
            const textWidth = ctx.measureText(label).width;
            ctx.fillRect(x, y - 14, textWidth + 4, 14);
            ctx.fillStyle = 'white';
            ctx.fillText(label, x + 2, y - 3);
          }
        }

        // FN 그리기 (노랑 점선)
        if (filters.showFN) {
          ctx.strokeStyle = DETECTION_COLORS.FN.stroke;
          ctx.fillStyle = DETECTION_COLORS.FN.fill;
          ctx.lineWidth = 2;
          ctx.setLineDash(DETECTION_COLORS.FN.dash || [5, 5]);

          for (const fn of compareResult.fn_labels) {
            const bbox = fn.bbox;
            const x = bbox.x1 * scaleX;
            const y = bbox.y1 * scaleY;
            const w = (bbox.x2 - bbox.x1) * scaleX;
            const h = (bbox.y2 - bbox.y1) * scaleY;

            ctx.fillRect(x, y, w, h);
            ctx.strokeRect(x, y, w, h);

            ctx.setLineDash([]);
            ctx.fillStyle = DETECTION_COLORS.FN.label;
            ctx.font = 'bold 10px sans-serif';
            const label = `FN: ${fn.class_name}`;
            const textWidth = ctx.measureText(label).width;
            ctx.fillRect(x, y - 14, textWidth + 4, 14);
            ctx.fillStyle = 'white';
            ctx.fillText(label, x + 2, y - 3);
            ctx.setLineDash(DETECTION_COLORS.FN.dash || [5, 5]);
          }
        }
      } else {
        // GT 없으면 검출 결과만 그리기 (파란색)
        ctx.strokeStyle = '#3b82f6';
        ctx.fillStyle = 'rgba(59, 130, 246, 0.1)';
        ctx.lineWidth = 2;
        ctx.setLineDash([]);

        for (const detection of detections) {
          const bbox = normalizeBBox(detection.bbox);
          const x = bbox.x1 * scaleX;
          const y = bbox.y1 * scaleY;
          const w = (bbox.x2 - bbox.x1) * scaleX;
          const h = (bbox.y2 - bbox.y1) * scaleY;

          ctx.fillRect(x, y, w, h);
          ctx.strokeRect(x, y, w, h);

          ctx.fillStyle = 'rgba(59, 130, 246, 0.9)';
          ctx.font = 'bold 10px sans-serif';
          const label = `${detection.class_name} ${(detection.confidence * 100).toFixed(0)}%`;
          const textWidth = ctx.measureText(label).width;
          ctx.fillRect(x, y - 14, textWidth + 4, 14);
          ctx.fillStyle = 'white';
          ctx.fillText(label, x + 2, y - 3);
        }
      }
    };
    img.src = uploadedImage;
  }, [uploadedImage, imageSize, compareResult, detections, filters]);

  // 캔버스 다시 그리기
  useEffect(() => {
    if (showCanvas) {
      drawCanvas();
    }
  }, [drawCanvas, showCanvas]);

  return {
    detections,
    avgConfidence,
    gtLoading,
    compareResult,
    filters,
    setFilters,
    showCanvas,
    setShowCanvas,
    canvasRef,
    containerRef,
  };
}
