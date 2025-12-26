/**
 * Detection Results Section
 * AI 검출 결과 섹션 컴포넌트
 */

import { useEffect, useRef } from 'react';
import { InfoTooltip } from '../../../components/Tooltip';
import { FEATURE_TOOLTIPS } from '../../../components/tooltipContent';
import type { Detection } from '../../../types';

interface GTMatch {
  detection_idx: number;
  gt_bbox: { x1: number; y1: number; x2: number; y2: number };
  gt_class: string;
  iou: number;
  class_match: boolean;
}

interface FNLabel {
  bbox: { x1: number; y1: number; x2: number; y2: number };
  class_name: string;
}

interface GTCompareResult {
  gt_count: number;
  tp_matches: GTMatch[];
  fn_labels: FNLabel[];
  metrics: {
    f1_score: number;
    precision: number;
    recall: number;
    tp: number;
    fp: number;
    fn: number;
  };
}

interface DetectionResultsSectionProps {
  detections: Detection[];
  imageData: string | null;
  imageSize: { width: number; height: number } | null;
  gtCompareResult: GTCompareResult | null;
  stats: {
    total: number;
    approved: number;
    rejected: number;
    pending: number;
    manual: number;
  };
}

export function DetectionResultsSection({
  detections,
  imageData,
  imageSize,
  gtCompareResult,
  stats,
}: DetectionResultsSectionProps) {
  const gtCanvasRef = useRef<HTMLCanvasElement>(null);
  const detCanvasRef = useRef<HTMLCanvasElement>(null);

  // Draw GT canvas
  useEffect(() => {
    const canvas = gtCanvasRef.current;
    if (!canvas || !imageData || !imageSize || !gtCompareResult) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      const parentWidth = canvas.parentElement?.clientWidth || 400;
      const scale = Math.min(parentWidth / img.width, 400 / img.height);
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // Collect all GT boxes
      const allGtBoxes: Array<{ bbox: { x1: number; y1: number; x2: number; y2: number }; class_name: string }> = [];
      gtCompareResult.tp_matches.forEach(match => {
        allGtBoxes.push({ bbox: match.gt_bbox, class_name: match.gt_class });
      });
      gtCompareResult.fn_labels.forEach(label => {
        allGtBoxes.push({ bbox: label.bbox, class_name: label.class_name });
      });

      // Draw GT boxes (GREEN)
      ctx.strokeStyle = '#22c55e';
      ctx.lineWidth = 3;
      ctx.font = 'bold 12px sans-serif';
      allGtBoxes.forEach((gt, idx) => {
        const x1 = gt.bbox.x1 * scale;
        const y1 = gt.bbox.y1 * scale;
        const w = (gt.bbox.x2 - gt.bbox.x1) * scale;
        const h = (gt.bbox.y2 - gt.bbox.y1) * scale;
        ctx.strokeRect(x1, y1, w, h);
        ctx.fillStyle = '#22c55e';
        ctx.fillRect(x1, y1 - 16, 30, 16);
        ctx.fillStyle = '#fff';
        ctx.fillText(`GT${idx + 1}`, x1 + 2, y1 - 4);
      });
    };
    img.src = imageData;
  }, [imageData, imageSize, gtCompareResult]);

  // Draw Detection canvas
  useEffect(() => {
    const canvas = detCanvasRef.current;
    if (!canvas || !imageData || !imageSize || !gtCompareResult) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      const parentWidth = canvas.parentElement?.clientWidth || 400;
      const scale = Math.min(parentWidth / img.width, 400 / img.height);
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // Draw Detection boxes (RED)
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 3;
      ctx.font = 'bold 12px sans-serif';
      detections.forEach((det, idx) => {
        const x1 = det.bbox.x1 * scale;
        const y1 = det.bbox.y1 * scale;
        const w = (det.bbox.x2 - det.bbox.x1) * scale;
        const h = (det.bbox.y2 - det.bbox.y1) * scale;
        ctx.strokeRect(x1, y1, w, h);
        ctx.fillStyle = '#ef4444';
        ctx.fillRect(x1, y1 - 16, 20, 16);
        ctx.fillStyle = '#fff';
        ctx.fillText(`${idx + 1}`, x1 + 4, y1 - 4);
      });
    };
    img.src = imageData;
  }, [imageData, imageSize, detections, gtCompareResult]);

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      {/* Title with inline metrics */}
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-1">
        🔍 AI 검출 결과
        <InfoTooltip content={FEATURE_TOOLTIPS.detectionResults.description} position="right" />
        {gtCompareResult && (
          <span className="text-base font-normal ml-2 flex items-center gap-1">
            파나시아 YOLOv11N - {stats.total}개 검출
            (<span className="inline-flex items-center">F1: {gtCompareResult.metrics.f1_score.toFixed(1)}%<InfoTooltip content={FEATURE_TOOLTIPS.f1Score.description} position="bottom" iconSize={12} /></span>,
            <span className="inline-flex items-center ml-1">정밀도: {gtCompareResult.metrics.precision.toFixed(1)}%<InfoTooltip content={FEATURE_TOOLTIPS.precision.description} position="bottom" iconSize={12} /></span>,
            <span className="inline-flex items-center ml-1">재현율: {gtCompareResult.metrics.recall.toFixed(1)}%<InfoTooltip content={FEATURE_TOOLTIPS.recall.description} position="bottom" iconSize={12} /></span>)
          </span>
        )}
      </h2>

      {/* GT 로드 상태 */}
      {gtCompareResult && (
        <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-3 mb-4">
          <p className="text-green-800 dark:text-green-200">
            ✅ Ground Truth 로드됨: {gtCompareResult.gt_count}개 라벨
          </p>
        </div>
      )}

      {/* GT vs Prediction Side by Side */}
      {imageData && imageSize && gtCompareResult && (
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Left: Ground Truth (Green boxes) */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <canvas ref={gtCanvasRef} className="w-full" />
            <p className="text-center py-2 text-sm font-medium text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/30">
              Ground Truth ({gtCompareResult.gt_count}개)
            </p>
          </div>

          {/* Right: Predictions (RED boxes) */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <canvas ref={detCanvasRef} className="w-full" />
            <p className="text-center py-2 text-sm font-medium text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/30">
              검출 결과 ({detections.length}개)
            </p>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
          <p className="text-sm text-gray-500">총 검출 수</p>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-blue-600">
            {detections.length > 0 ? (detections.reduce((sum, d) => sum + d.confidence, 0) / detections.length).toFixed(3) : '0.000'}
          </p>
          <p className="text-sm text-gray-500">평균 신뢰도</p>
        </div>
        {gtCompareResult ? (
          <>
            <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-green-600">{gtCompareResult.metrics.precision.toFixed(1)}%</p>
              <p className="text-sm text-gray-500">Precision</p>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-purple-600">{gtCompareResult.metrics.recall.toFixed(1)}%</p>
              <p className="text-sm text-gray-500">Recall</p>
            </div>
          </>
        ) : (
          <>
            <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-green-600">{stats.approved}</p>
              <p className="text-sm text-gray-500">승인</p>
            </div>
            <div className="bg-yellow-50 dark:bg-yellow-900/30 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
              <p className="text-sm text-gray-500">대기</p>
            </div>
          </>
        )}
      </div>

      {/* F1 Score highlight */}
      {gtCompareResult && (
        <div className="bg-green-100 dark:bg-green-900/50 border border-green-300 dark:border-green-700 rounded-lg p-3">
          <p className="text-green-800 dark:text-green-200 font-medium">
            🎯 F1 Score: {gtCompareResult.metrics.f1_score.toFixed(1)}%
            (TP:{gtCompareResult.metrics.tp}, FP:{gtCompareResult.metrics.fp}, FN:{gtCompareResult.metrics.fn})
          </p>
        </div>
      )}
    </section>
  );
}
