/**
 * Detection Results Section
 * AI 검출 결과 섹션 컴포넌트
 * - GT 비교 모드: Canvas 기반 bbox 시각화
 * - 일반 모드: IntegratedOverlay (Polygon/Mask 지원)
 */

import { useEffect, useRef, useState } from 'react';
import { CheckCircle } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import { FEATURE_TOOLTIPS } from '../../../components/tooltipContent';
import { IntegratedOverlay } from '../../../components/IntegratedOverlay';
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
  const simpleCanvasRef = useRef<HTMLCanvasElement>(null);
  const unifiedCanvasRef = useRef<HTMLCanvasElement>(null);

  // Detectron2 polygon/mask 데이터 존재 여부 확인
  const hasPolygonData = detections.some(d => d.polygons && d.polygons.length > 0);
  const hasMaskData = detections.some(d => d.mask && d.mask.counts && d.mask.counts.length > 0);
  const hasDetectron2Data = hasPolygonData || hasMaskData;

  // 뷰 모드: 'overlay' (IntegratedOverlay) or 'canvas' (기존 Canvas) or 'unified' (TP/FP/FN 통합)
  const [viewMode, setViewMode] = useState<'overlay' | 'canvas' | 'unified'>(
    hasDetectron2Data ? 'overlay' : 'canvas'
  );

  // TP/FP/FN 필터 상태
  const [showTP, setShowTP] = useState(true);
  const [showFP, setShowFP] = useState(true);
  const [showFN, setShowFN] = useState(true);

  // 클래스 하이라이트 상태
  const [selectedClassName, setSelectedClassName] = useState<string | null>(null);

  // 클래스별 검출 수 계산
  const classCounts = detections.reduce((acc, d) => {
    const className = d.class_name;
    acc[className] = (acc[className] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // 클래스 목록 (검출 수 내림차순)
  const sortedClasses = Object.entries(classCounts).sort((a, b) => b[1] - a[1]);

  // Draw GT canvas (병렬 비교 모드)
  useEffect(() => {
    const canvas = gtCanvasRef.current;
    // viewMode가 'canvas'일 때만 그리기
    if (!canvas || !imageData || !imageSize || !gtCompareResult || viewMode !== 'canvas') return;

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
  }, [imageData, imageSize, gtCompareResult, viewMode]);

  // Draw Detection canvas (병렬 비교 모드)
  useEffect(() => {
    const canvas = detCanvasRef.current;
    // viewMode가 'canvas'일 때만 그리기
    if (!canvas || !imageData || !imageSize || !gtCompareResult || viewMode !== 'canvas') return;

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
  }, [imageData, imageSize, detections, gtCompareResult, viewMode]);

  // Draw unified TP/FP/FN canvas
  useEffect(() => {
    const canvas = unifiedCanvasRef.current;
    if (!canvas || !imageData || !imageSize || !gtCompareResult || viewMode !== 'unified') return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      const parentWidth = canvas.parentElement?.clientWidth || 800;
      const scale = Math.min(parentWidth / img.width, 600 / img.height);
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      ctx.lineWidth = 3;
      ctx.font = 'bold 11px sans-serif';

      // TP matches에서 매칭된 detection 인덱스 수집
      const tpDetectionIndices = new Set(gtCompareResult.tp_matches.map(m => m.detection_idx));

      // 1. Draw FN (Yellow) - 미검출 GT
      if (showFN) {
        gtCompareResult.fn_labels.forEach((fn) => {
          const x1 = fn.bbox.x1 * scale;
          const y1 = fn.bbox.y1 * scale;
          const w = (fn.bbox.x2 - fn.bbox.x1) * scale;
          const h = (fn.bbox.y2 - fn.bbox.y1) * scale;

          // 점선 스타일
          ctx.setLineDash([5, 5]);
          ctx.strokeStyle = '#eab308';
          ctx.strokeRect(x1, y1, w, h);
          ctx.setLineDash([]);

          // 라벨 배경
          const label = `FN: ${fn.class_name}`;
          const textWidth = ctx.measureText(label).width;
          ctx.fillStyle = 'rgba(234, 179, 8, 0.9)';
          ctx.fillRect(x1, y1 - 18, textWidth + 8, 18);
          ctx.fillStyle = '#000';
          ctx.fillText(label, x1 + 4, y1 - 5);
        });
      }

      // 2. Draw FP (Red) - 오검출
      if (showFP) {
        detections.forEach((det, idx) => {
          if (tpDetectionIndices.has(idx)) return; // TP는 건너뛰기

          const x1 = det.bbox.x1 * scale;
          const y1 = det.bbox.y1 * scale;
          const w = (det.bbox.x2 - det.bbox.x1) * scale;
          const h = (det.bbox.y2 - det.bbox.y1) * scale;

          ctx.strokeStyle = '#ef4444';
          ctx.strokeRect(x1, y1, w, h);

          const label = `FP: ${det.class_name}`;
          const textWidth = ctx.measureText(label).width;
          ctx.fillStyle = 'rgba(239, 68, 68, 0.9)';
          ctx.fillRect(x1, y1 - 18, textWidth + 8, 18);
          ctx.fillStyle = '#fff';
          ctx.fillText(label, x1 + 4, y1 - 5);
        });
      }

      // 3. Draw TP (Green) - 정답
      if (showTP) {
        gtCompareResult.tp_matches.forEach((match) => {
          const det = detections[match.detection_idx];
          if (!det) return;

          const x1 = det.bbox.x1 * scale;
          const y1 = det.bbox.y1 * scale;
          const w = (det.bbox.x2 - det.bbox.x1) * scale;
          const h = (det.bbox.y2 - det.bbox.y1) * scale;

          ctx.strokeStyle = '#22c55e';
          ctx.strokeRect(x1, y1, w, h);

          const iouText = `${(match.iou * 100).toFixed(0)}%`;
          const label = `TP: ${det.class_name} (IoU ${iouText})`;
          const textWidth = ctx.measureText(label).width;
          ctx.fillStyle = 'rgba(34, 197, 94, 0.9)';
          ctx.fillRect(x1, y1 - 18, textWidth + 8, 18);
          ctx.fillStyle = '#fff';
          ctx.fillText(label, x1 + 4, y1 - 5);
        });
      }
    };
    img.src = imageData;
  }, [imageData, imageSize, gtCompareResult, detections, viewMode, showTP, showFP, showFN]);

  // Draw simple canvas (no GT comparison)
  useEffect(() => {
    const canvas = simpleCanvasRef.current;
    if (!canvas || !imageData || !imageSize || gtCompareResult || viewMode !== 'canvas') return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      const parentWidth = canvas.parentElement?.clientWidth || 600;
      const scale = Math.min(parentWidth / img.width, 500 / img.height);
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // Draw Detection boxes with class-based colors
      const colors = [
        '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#22c55e',
        '#14b8a6', '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6',
      ];

      ctx.font = 'bold 11px sans-serif';
      detections.forEach((det) => {
        const isSelected = selectedClassName === null || det.class_name === selectedClassName;
        const color = colors[det.class_id % colors.length];
        const x1 = det.bbox.x1 * scale;
        const y1 = det.bbox.y1 * scale;
        const w = (det.bbox.x2 - det.bbox.x1) * scale;
        const h = (det.bbox.y2 - det.bbox.y1) * scale;

        // Draw box (선택되지 않은 클래스는 반투명)
        ctx.globalAlpha = isSelected ? 1 : 0.2;
        ctx.lineWidth = isSelected ? 3 : 1;
        ctx.strokeStyle = color;
        ctx.strokeRect(x1, y1, w, h);

        // Draw label background (선택된 것만)
        if (isSelected) {
          const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`;
          const textWidth = ctx.measureText(label).width;
          ctx.fillStyle = color;
          ctx.fillRect(x1, y1 - 16, textWidth + 6, 16);

          // Draw label text
          ctx.fillStyle = '#fff';
          ctx.fillText(label, x1 + 3, y1 - 4);
        }
        ctx.globalAlpha = 1;
      });
    };
    img.src = imageData;
  }, [imageData, imageSize, detections, gtCompareResult, viewMode, selectedClassName]);

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

      {/* GT 로드 완료 상태 배지 */}
      {gtCompareResult && (
        <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-3 mb-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-green-800 dark:text-green-200 font-medium">
              Ground Truth: {gtCompareResult.gt_count}개 라벨
            </span>
          </div>
        </div>
      )}

      {/* Detectron2 데이터 알림 및 뷰 모드 토글 */}
      {hasDetectron2Data && (
        <div className="bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-800 rounded-lg p-3 mb-4 flex items-center justify-between">
          <p className="text-indigo-800 dark:text-indigo-200">
            🎭 Detectron2 데이터 포함: {hasPolygonData ? 'Polygon ' : ''}{hasMaskData ? 'Mask' : ''}
          </p>
          <div className="flex items-center gap-2">
            <span className="text-sm text-indigo-600 dark:text-indigo-300">뷰 모드:</span>
            <button
              onClick={() => setViewMode('overlay')}
              className={`px-3 py-1 text-sm rounded-l-lg border ${
                viewMode === 'overlay'
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
              }`}
            >
              오버레이
            </button>
            <button
              onClick={() => setViewMode('canvas')}
              className={`px-3 py-1 text-sm rounded-r-lg border-t border-r border-b ${
                viewMode === 'canvas'
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
              }`}
            >
              기본
            </button>
          </div>
        </div>
      )}

      {/* IntegratedOverlay 뷰 (Detectron2 Polygon/Mask 시각화) */}
      {imageData && imageSize && viewMode === 'overlay' && !gtCompareResult && (
        <div className="mb-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <IntegratedOverlay
            imageData={imageData}
            imageSize={imageSize}
            detections={detections}
            maxWidth="100%"
            maxHeight="500px"
          />
          <p className="text-center py-2 text-sm font-medium text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/30">
            Detectron2 검출 결과 ({detections.length}개) - 레이어 토글은 이미지 오른쪽 상단
          </p>
        </div>
      )}

      {/* Simple Canvas 뷰 (GT 없을 때 기본 뷰) */}
      {imageData && imageSize && viewMode === 'canvas' && !gtCompareResult && (
        <div className="mb-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <canvas ref={simpleCanvasRef} className="w-full" />
          <p className="text-center py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-900/30">
            검출 결과 ({detections.length}개)
          </p>
        </div>
      )}

      {/* GT 비교 뷰 모드 선택 */}
      {imageData && imageSize && gtCompareResult && (
        <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">GT 비교 뷰:</span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setViewMode('unified')}
              className={`px-3 py-1.5 text-sm rounded-l-lg border transition-colors ${
                viewMode === 'unified'
                  ? 'bg-purple-600 text-white border-purple-600'
                  : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50'
              }`}
            >
              🎯 통합 (TP/FP/FN)
            </button>
            <button
              onClick={() => setViewMode('canvas')}
              className={`px-3 py-1.5 text-sm rounded-r-lg border-t border-r border-b transition-colors ${
                viewMode === 'canvas'
                  ? 'bg-purple-600 text-white border-purple-600'
                  : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50'
              }`}
            >
              📊 병렬 비교
            </button>
          </div>
        </div>
      )}

      {/* Unified TP/FP/FN 오버레이 뷰 */}
      {imageData && imageSize && gtCompareResult && viewMode === 'unified' && (
        <div className="mb-4">
          {/* 필터 버튼 */}
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm text-gray-600 dark:text-gray-400">표시:</span>
            <button
              onClick={() => setShowTP(!showTP)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                showTP
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400 border border-green-300 dark:border-green-700'
                  : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500 border border-gray-300 dark:border-gray-600'
              }`}
            >
              <span className={`w-3 h-3 rounded ${showTP ? 'bg-green-500' : 'bg-gray-300'}`} />
              TP ({gtCompareResult.metrics.tp})
            </button>
            <button
              onClick={() => setShowFP(!showFP)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                showFP
                  ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400 border border-red-300 dark:border-red-700'
                  : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500 border border-gray-300 dark:border-gray-600'
              }`}
            >
              <span className={`w-3 h-3 rounded ${showFP ? 'bg-red-500' : 'bg-gray-300'}`} />
              FP ({gtCompareResult.metrics.fp})
            </button>
            <button
              onClick={() => setShowFN(!showFN)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                showFN
                  ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400 border border-yellow-300 dark:border-yellow-700'
                  : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500 border border-gray-300 dark:border-gray-600'
              }`}
            >
              <span className={`w-3 h-3 rounded ${showFN ? 'bg-yellow-500' : 'bg-gray-300'}`} />
              FN ({gtCompareResult.metrics.fn})
            </button>
          </div>

          {/* 통합 캔버스 */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <canvas ref={unifiedCanvasRef} className="w-full" />
            <div className="flex items-center justify-between px-4 py-2 bg-purple-50 dark:bg-purple-900/30">
              <p className="text-sm font-medium text-purple-700 dark:text-purple-300">
                TP/FP/FN 통합 오버레이
              </p>
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-green-500 rounded" /> TP (정답)
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-red-500 rounded" /> FP (오검출)
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-yellow-500 rounded border border-dashed border-yellow-600" /> FN (미검출)
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* GT vs Prediction Side by Side */}
      {imageData && imageSize && gtCompareResult && viewMode === 'canvas' && (
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

      {/* 클래스 필터 (클릭하여 하이라이트) */}
      {sortedClasses.length > 0 && !gtCompareResult && (
        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              클래스별 검출 (클릭하여 하이라이트):
            </span>
            {selectedClassName && (
              <button
                onClick={() => setSelectedClassName(null)}
                className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 rounded-lg text-gray-700 dark:text-gray-200"
              >
                전체 보기
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {sortedClasses.map(([className, count]) => {
              const isSelected = selectedClassName === className;
              return (
                <button
                  key={className}
                  onClick={() => setSelectedClassName(isSelected ? null : className)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    isSelected
                      ? 'bg-primary-600 text-white ring-2 ring-primary-400'
                      : 'bg-white dark:bg-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-500 border border-gray-200 dark:border-gray-500'
                  }`}
                >
                  {className} <span className={isSelected ? 'text-primary-200' : 'text-gray-500 dark:text-gray-400'}>({count})</span>
                </button>
              );
            })}
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
