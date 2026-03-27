/**
 * CellOverlay — 선택한 엔진×방법 조합의 검출 결과를 도면 위에 오버레이
 */
import { useState, useRef, useEffect } from 'react';
import { X } from 'lucide-react';
import { sessionApi } from '../../lib/api';
import type { CellResult, FullCompareResponse } from '../../lib/api';
import { ENGINE_LABELS, METHOD_LABELS, ROLE_COLORS, GEOMETRY_METHODS } from './types';
import type { GtAnnotation, GeometryDebugInfo } from './types';
import { GeometryDebugOverlay } from './GeometryDebugOverlay';
import { ZoomableContainer } from '../../components/ZoomableContainer';

const ROLE_COLOR_MAP: Record<string, string> = {
  outer_diameter: ROLE_COLORS.od,
  inner_diameter: ROLE_COLORS.id,
  length: ROLE_COLORS.w,
};

const ROLE_LABEL_MAP: Record<string, string> = {
  outer_diameter: 'OD',
  inner_diameter: 'ID',
  length: 'W',
};

interface Props {
  cell: CellResult;
  result: FullCompareResponse;
  groundTruth: GtAnnotation[];
  onClose: () => void;
}

export function CellOverlay({ cell, result, groundTruth, onClose }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [scale, setScale] = useState(1);
  const [showGt, setShowGt] = useState(true);
  const [showGeoDebug, setShowGeoDebug] = useState(true);

  const hasGeoDebug = GEOMETRY_METHODS.includes(cell.method_id) && cell.geometry_debug;

  useEffect(() => {
    let cancelled = false;
    sessionApi.getImage(result.session_id).then(({ image_base64, mime_type }) => {
      if (!cancelled) setImageUrl(`data:${mime_type};base64,${image_base64}`);
    });
    return () => { cancelled = true; };
  }, [result.session_id]);

  useEffect(() => {
    if (!containerRef.current || !result.image_width) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) setScale(entry.contentRect.width / result.image_width);
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [result.image_width]);

  const scaledHeight = result.image_height * scale;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            {ENGINE_LABELS[cell.engine]} × {METHOD_LABELS[cell.method_id]}
          </h3>
          <span className="text-xs font-bold px-2 py-0.5 rounded" style={{
            backgroundColor: cell.score >= 1 ? '#dcfce7' : cell.score > 0 ? '#fef9c3' : '#fee2e2',
            color: cell.score >= 1 ? '#16a34a' : cell.score > 0 ? '#ca8a04' : '#dc2626',
          }}>
            {(cell.score * 100).toFixed(0)}%
          </span>
          <div className="flex items-center gap-3 text-xs">
            <span>OD: <strong className={cell.od_match ? 'text-green-600' : 'text-red-500'}>{cell.od || '—'}</strong></span>
            <span>ID: <strong className={cell.id_match ? 'text-green-600' : 'text-red-500'}>{cell.id_val || '—'}</strong></span>
            <span>W: <strong className={cell.w_match ? 'text-green-600' : 'text-red-500'}>{cell.width || '—'}</strong></span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-xs text-gray-500">
            <input type="checkbox" checked={showGt} onChange={(e) => setShowGt(e.target.checked)} className="rounded" />
            Ground Truth 표시
          </label>
          {hasGeoDebug && (
            <label className="flex items-center gap-1.5 text-xs text-gray-500">
              <input type="checkbox" checked={showGeoDebug} onChange={(e) => setShowGeoDebug(e.target.checked)} className="rounded" />
              기하학 디버그
            </label>
          )}
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* 이미지 + 오버레이 */}
      <ZoomableContainer initialZoom={100} minZoom={25} maxZoom={300} className="border border-gray-200 dark:border-gray-700 rounded-lg">
      <div ref={containerRef} className="relative w-full">
        {imageUrl ? (
          <div className="relative" style={{ width: '100%', height: scaledHeight }}>
            <img src={imageUrl} alt="Drawing" className="w-full h-auto" style={{ display: 'block', pointerEvents: 'none' }} />
            <svg
              className="absolute top-0 left-0 w-full"
              style={{ height: scaledHeight }}
              viewBox={`0 0 ${result.image_width} ${result.image_height}`}
              preserveAspectRatio="xMinYMin meet"
            >
              {/* Ground Truth (점선) */}
              {showGt && groundTruth.map((gt, idx) => {
                const color = ROLE_COLORS[gt.role as keyof typeof ROLE_COLORS] || '#888';
                return (
                  <g key={`gt-${idx}`}>
                    <rect
                      x={gt.bbox.x1} y={gt.bbox.y1}
                      width={gt.bbox.x2 - gt.bbox.x1} height={gt.bbox.y2 - gt.bbox.y1}
                      fill="none" stroke={color} strokeWidth={2} strokeDasharray="8,4" opacity={0.6}
                    />
                    <rect x={gt.bbox.x1} y={gt.bbox.y2 + 2} width={70} height={16} fill={color} opacity={0.5} rx={3} />
                    <text x={gt.bbox.x1 + 3} y={gt.bbox.y2 + 14} fill="white" fontSize={11} fontWeight="bold">
                      GT {gt.role.toUpperCase()}: {gt.value}
                    </text>
                  </g>
                );
              })}

              {/* 검출 결과 (실선) */}
              {cell.classified_dims.map((dim, idx) => {
                if (!dim.bbox || !dim.role) return null;
                const color = ROLE_COLOR_MAP[dim.role] || '#888';
                const label = ROLE_LABEL_MAP[dim.role] || dim.role;
                return (
                  <g key={`det-${idx}`}>
                    <rect
                      x={dim.bbox.x1} y={dim.bbox.y1}
                      width={dim.bbox.x2 - dim.bbox.x1} height={dim.bbox.y2 - dim.bbox.y1}
                      fill={color} fillOpacity={0.15}
                      stroke={color} strokeWidth={3} rx={4}
                    />
                    <rect
                      x={dim.bbox.x1} y={dim.bbox.y1 - 22}
                      width={Math.max(90, dim.value.length * 9 + 60)} height={20}
                      fill={color} rx={4}
                    />
                    <text x={dim.bbox.x1 + 4} y={dim.bbox.y1 - 7} fill="white" fontSize={12} fontWeight="bold">
                      {label}: {dim.value} ({(dim.confidence * 100).toFixed(0)}%)
                    </text>
                  </g>
                );
              })}
            </svg>
            {/* Geometry Debug Overlay */}
            {hasGeoDebug && showGeoDebug && (
              <GeometryDebugOverlay
                debug={cell.geometry_debug as GeometryDebugInfo}
                imageWidth={result.image_width}
                imageHeight={result.image_height}
                scaledHeight={scaledHeight}
              />
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-400">이미지 로딩...</div>
        )}
      </div>
      </ZoomableContainer>

      {/* 범례 */}
      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-8 h-0.5 border-t-2 border-dashed" style={{ borderColor: ROLE_COLORS.od }} /> GT (점선)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-8 h-3 rounded" style={{ backgroundColor: ROLE_COLORS.od, opacity: 0.3 }} /> 검출 (실선)
        </span>
        <span className="ml-4">검출된 치수: {cell.classified_dims.length}개</span>
      </div>
    </div>
  );
}
