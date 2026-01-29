/**
 * DetectionResultCard - 검출 결과 + GT 비교 통합 표시 컴포넌트
 *
 * 기능:
 * 1. 검출 결과 요약 (개수, 평균 신뢰도)
 * 2. GT 자동 매칭 및 로드
 * 3. GT 비교 결과 표시 (F1/Precision/Recall)
 * 4. TP/FP/FN 통합 캔버스
 * 5. 필터 토글
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Eye, EyeOff, Loader2 } from 'lucide-react';
import type { NodeStatus } from '../../store/workflowStore';
import {
  type DetectionResult,
  type GTLabel,
  type GTCompareResult,
  type DetectionFilters,
  DETECTION_COLORS,
  parseYOLOFormat,
  compareWithGT,
  normalizeBBox,
} from '../../types/detection';

interface DetectionResultCardProps {
  nodeStatus: NodeStatus;
  uploadedImage: string | null;
  uploadedFileName: string | null;
}

// === 서브컴포넌트: 메트릭 카드 ===
interface MetricCardProps {
  label: string;
  value: number;
  color: string;
}

const MetricCard = ({ label, value, color }: MetricCardProps) => (
  <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
    <div className={`text-lg font-bold ${color}`}>
      {(value * 100).toFixed(1)}%
    </div>
    <div className="text-[10px] text-gray-500 dark:text-gray-400">{label}</div>
  </div>
);

// === 서브컴포넌트: 필터 체크박스 ===
interface FilterCheckboxProps {
  label: string;
  icon: string;
  count: number;
  checked: boolean;
  onChange: (checked: boolean) => void;
  color: string;
}

const FilterCheckbox = ({ label, icon, count, checked, onChange, color }: FilterCheckboxProps) => (
  <label
    className={`flex items-center gap-1 px-2 py-1 rounded cursor-pointer transition-colors ${
      checked ? 'bg-gray-100 dark:bg-gray-700' : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
    }`}
  >
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
      className="w-3 h-3 rounded"
    />
    <span className="text-xs">{icon}</span>
    <span className={`text-xs font-medium ${color}`}>{label}: {count}</span>
  </label>
);

// === 메인 컴포넌트 ===
export default function DetectionResultCard({
  nodeStatus,
  uploadedImage,
  uploadedFileName,
}: DetectionResultCardProps) {
  // State
  const [gtLabels, setGTLabels] = useState<GTLabel[] | null>(null);
  const [gtLoading, setGTLoading] = useState(false);
  // gtError는 향후 에러 표시용으로 사용될 수 있음
  const [, setGTError] = useState<string | null>(null);
  const [compareResult, setCompareResult] = useState<GTCompareResult | null>(null);
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const [filters, setFilters] = useState<DetectionFilters>({
    showTP: true,
    showFP: true,
    showFN: true,
  });
  const [showCanvas, setShowCanvas] = useState(true);

  // Refs
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

      // 파일명에서 GT 경로 추출 (image.png → image.txt)
      const gtFileName = uploadedFileName.replace(/\.(png|jpg|jpeg|gif|bmp|webp)$/i, '.txt');

      // 여러 경로 시도
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
      // GT 없음은 에러가 아님 - 그냥 표시하지 않음
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

    // 컨테이너 크기에 맞춰 캔버스 크기 계산
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

    // 배경 이미지 그리기
    const img = new Image();
    img.onload = () => {
      ctx.drawImage(img, 0, 0, canvasWidth, canvasHeight);

      // GT 비교 결과가 있으면 TP/FP/FN 그리기
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

            // 라벨
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

            // 라벨
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

            // 라벨
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

          // 라벨
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

  // 검출 결과 없으면 표시하지 않음
  if (detections.length === 0 && !nodeStatus.output) {
    return null;
  }

  return (
    <div className="space-y-3">
      {/* 검출 결과 요약 */}
      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-lg">🎯</span>
            <span className="font-medium text-blue-700 dark:text-blue-300">
              AI 검출 결과
            </span>
          </div>
          {nodeStatus.elapsedSeconds && (
            <span className="text-xs text-gray-500">
              {nodeStatus.elapsedSeconds.toFixed(1)}s
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-600 dark:text-gray-400">검출:</span>
            <span className="font-bold text-blue-600 dark:text-blue-400">
              {detections.length}개
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-600 dark:text-gray-400">신뢰도:</span>
            <span className="font-bold text-blue-600 dark:text-blue-400">
              {(avgConfidence * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* GT 비교 섹션 (GT가 있는 경우만) */}
      {gtLoading && (
        <div className="flex items-center gap-2 text-xs text-gray-500 p-2">
          <Loader2 className="w-3 h-3 animate-spin" />
          GT 파일 검색 중...
        </div>
      )}

      {compareResult && (
        <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">📊</span>
              <span className="font-medium text-purple-700 dark:text-purple-300">
                GT 비교
              </span>
            </div>
            <span className="text-xs text-gray-500">
              {compareResult.gt_count}개 라벨
            </span>
          </div>

          {/* 메트릭 카드 */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <MetricCard
              label="Precision"
              value={compareResult.metrics.precision}
              color="text-green-600 dark:text-green-400"
            />
            <MetricCard
              label="Recall"
              value={compareResult.metrics.recall}
              color="text-blue-600 dark:text-blue-400"
            />
            <MetricCard
              label="F1"
              value={compareResult.metrics.f1_score}
              color="text-purple-600 dark:text-purple-400"
            />
          </div>

          {/* TP/FP/FN 요약 */}
          <div className="flex items-center justify-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-green-500" />
              <span className="text-green-600 dark:text-green-400 font-medium">
                TP: {compareResult.metrics.tp}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <XCircle className="w-3 h-3 text-red-500" />
              <span className="text-red-600 dark:text-red-400 font-medium">
                FP: {compareResult.metrics.fp}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-yellow-500" />
              <span className="text-yellow-600 dark:text-yellow-400 font-medium">
                FN: {compareResult.metrics.fn}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 필터 & 캔버스 토글 */}
      {(detections.length > 0 || compareResult) && uploadedImage && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              {compareResult && (
                <>
                  <FilterCheckbox
                    label="TP"
                    icon="✅"
                    count={compareResult.metrics.tp}
                    checked={filters.showTP}
                    onChange={(checked) => setFilters((f) => ({ ...f, showTP: checked }))}
                    color="text-green-600 dark:text-green-400"
                  />
                  <FilterCheckbox
                    label="FP"
                    icon="❌"
                    count={compareResult.metrics.fp}
                    checked={filters.showFP}
                    onChange={(checked) => setFilters((f) => ({ ...f, showFP: checked }))}
                    color="text-red-600 dark:text-red-400"
                  />
                  <FilterCheckbox
                    label="FN"
                    icon="⚠️"
                    count={compareResult.metrics.fn}
                    checked={filters.showFN}
                    onChange={(checked) => setFilters((f) => ({ ...f, showFN: checked }))}
                    color="text-yellow-600 dark:text-yellow-400"
                  />
                </>
              )}
            </div>
            <button
              onClick={() => setShowCanvas(!showCanvas)}
              className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              {showCanvas ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
              {showCanvas ? '숨기기' : '보기'}
            </button>
          </div>

          {/* 캔버스 */}
          {showCanvas && (
            <div
              ref={containerRef}
              className="rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-800"
            >
              <canvas
                ref={canvasRef}
                className="w-full h-auto"
                style={{ maxHeight: '300px' }}
              />
            </div>
          )}
        </div>
      )}

      {/* JSON 미리보기 (접기/펼치기) */}
      {nodeStatus.output && (
        <details className="text-xs">
          <summary className="cursor-pointer text-blue-600 dark:text-blue-400 hover:underline">
            JSON 데이터 보기
          </summary>
          <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-auto max-h-40 border border-gray-200 dark:border-gray-700">
            {JSON.stringify(nodeStatus.output, null, 2).slice(0, 2000)}
            {JSON.stringify(nodeStatus.output).length > 2000 && '...'}
          </pre>
        </details>
      )}
    </div>
  );
}
