/**
 * MethodDetailPanel — 선택한 방법의 추론 과정을 상세히 보여주는 패널
 *
 * 표시 내용:
 * 1. 방법 설명 + 엔진별 OD/ID/W 결과 요약
 * 2. 전체 치수 목록 (역할별 색상 하이라이트)
 * 3. 이미지 + 오버레이 (검출 bbox + GT)
 * 4. 기하학 디버그 레이어 (K/L/M/N)
 */
import { useState, useRef, useEffect } from 'react';
import { X, ChevronDown, ChevronUp } from 'lucide-react';
import { sessionApi } from '../../lib/api';
import type { FullCompareResponse, ClassifiedDim } from '../../lib/api';
import {
  ENGINE_LABELS, METHOD_LABELS, ROLE_COLORS, GEOMETRY_METHODS,
  METHOD_INFO, CATEGORY_COLORS,
} from './types';
import type { GtAnnotation, GeometryDebugInfo } from './types';
import { GeometryDebugOverlay } from './GeometryDebugOverlay';

const ROLE_COLOR_MAP: Record<string, string> = {
  outer_diameter: ROLE_COLORS.od,
  inner_diameter: ROLE_COLORS.id,
  length: ROLE_COLORS.w,
  other: '#9ca3af',
};

const ROLE_TAG: Record<string, string> = {
  outer_diameter: 'OD',
  inner_diameter: 'ID',
  length: 'W',
  other: '기타',
};

interface Props {
  methodId: string;
  result: FullCompareResponse;
  engines: string[];
  groundTruth: GtAnnotation[];
  onClose: () => void;
}

export function MethodDetailPanel({ methodId, result, engines, groundTruth, onClose }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [scale, setScale] = useState(1);
  const [selectedEngine, setSelectedEngine] = useState(engines[0] || '');
  const [showGt, setShowGt] = useState(true);
  const [showGeoDebug, setShowGeoDebug] = useState(true);
  const [expandedDims, setExpandedDims] = useState(true);

  const methodInfo = METHOD_INFO.find((m) => m.id === methodId);

  // 이 방법의 모든 엔진 결과
  const cells = result.matrix.filter((c) => c.method_id === methodId && engines.includes(c.engine));
  const selectedCell = cells.find((c) => c.engine === selectedEngine) || cells[0];

  const hasGeoDebug = GEOMETRY_METHODS.includes(methodId) && selectedCell?.geometry_debug;

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

  // 치수 분류: OD/ID/W vs other vs unclassified
  const keyDims = selectedCell?.classified_dims.filter(
    (d) => d.role && d.role !== 'other',
  ) || [];
  const otherDims = selectedCell?.classified_dims.filter(
    (d) => d.role === 'other' || !d.role,
  ) || [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-800 px-5 py-3 border-b border-gray-200 dark:border-gray-600">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {methodInfo && (
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: CATEGORY_COLORS[methodInfo.category] }}
              />
            )}
            <h3 className="text-base font-bold text-gray-900 dark:text-white">
              {METHOD_LABELS[methodId] || methodId}
            </h3>
            {selectedCell && (
              <span className={`text-sm font-bold px-2 py-0.5 rounded ${
                selectedCell.score >= 1 ? 'bg-green-100 text-green-700' :
                selectedCell.score > 0 ? 'bg-yellow-100 text-yellow-700' :
                'bg-red-100 text-red-700'
              }`}>
                {(selectedCell.score * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <X className="w-5 h-5" />
          </button>
        </div>
        {methodInfo && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5 leading-relaxed">
            {methodInfo.description}
          </p>
        )}
      </div>

      <div className="p-4 space-y-4">
        {/* 엔진별 결과 요약 + 엔진 선택 */}
        <div>
          <h4 className="text-xs font-semibold text-gray-500 mb-2">엔진별 결과 (클릭하여 상세 보기)</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
            {cells.map((cell) => (
              <button
                key={cell.engine}
                onClick={() => setSelectedEngine(cell.engine)}
                className={`rounded-lg border p-2 text-left transition ${
                  cell.engine === selectedEngine
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-600 hover:border-blue-300'
                }`}
              >
                <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {ENGINE_LABELS[cell.engine] || cell.engine}
                </div>
                <div className="flex items-center gap-1.5 text-[11px]">
                  <span className={cell.od_match ? 'text-green-600 font-bold' : 'text-red-400'}>
                    OD:{cell.od || '—'}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-[11px]">
                  <span className={cell.id_match ? 'text-green-600 font-bold' : 'text-red-400'}>
                    ID:{cell.id_val || '—'}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-[11px]">
                  <span className={cell.w_match ? 'text-green-600 font-bold' : 'text-red-400'}>
                    W:{cell.width || '—'}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* 추론 과정: 핵심 치수 */}
        {selectedCell && (
          <div>
            <h4 className="text-xs font-semibold text-gray-500 mb-2">
              추론 과정 — {ENGINE_LABELS[selectedEngine]}
            </h4>

            {/* 선택된 OD/ID/W */}
            {keyDims.length > 0 ? (
              <div className="bg-blue-50 dark:bg-blue-900/10 rounded-lg p-3 mb-3">
                <div className="text-xs font-semibold text-blue-700 dark:text-blue-400 mb-2">
                  이 방법이 선택한 핵심 치수
                </div>
                <div className="space-y-1.5">
                  {keyDims.map((dim, idx) => (
                    <DimRow key={idx} dim={dim} isKey />
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-red-50 dark:bg-red-900/10 rounded-lg p-3 mb-3">
                <div className="text-xs text-red-600 dark:text-red-400">
                  이 방법으로 OD/ID/W를 식별하지 못했습니다.
                </div>
              </div>
            )}

            {/* 나머지 치수 (접이식) */}
            <div className="border rounded-lg border-gray-200 dark:border-gray-600">
              <button
                onClick={() => setExpandedDims(!expandedDims)}
                className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition"
              >
                <span>전체 치수 목록 ({selectedCell.classified_dims.length}개)</span>
                {expandedDims ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
              {expandedDims && (
                <div className="border-t border-gray-200 dark:border-gray-600 max-h-64 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead className="bg-gray-50 dark:bg-gray-700/50 sticky top-0">
                      <tr>
                        <th className="px-2 py-1.5 text-left text-gray-500">값</th>
                        <th className="px-2 py-1.5 text-left text-gray-500">역할</th>
                        <th className="px-2 py-1.5 text-right text-gray-500">신뢰도</th>
                        <th className="px-2 py-1.5 text-right text-gray-500">위치</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedCell.classified_dims.map((dim, idx) => {
                        const isKey = dim.role && dim.role !== 'other' && dim.role !== null;
                        return (
                          <tr key={idx} className={isKey ? 'bg-blue-50/50 dark:bg-blue-900/10 font-medium' : ''}>
                            <td className="px-2 py-1 text-gray-900 dark:text-white">{dim.value}</td>
                            <td className="px-2 py-1">
                              {dim.role ? (
                                <span
                                  className="px-1.5 py-0.5 rounded text-[10px] font-bold text-white"
                                  style={{ backgroundColor: ROLE_COLOR_MAP[dim.role] || '#9ca3af' }}
                                >
                                  {ROLE_TAG[dim.role] || dim.role}
                                </span>
                              ) : (
                                <span className="text-gray-300">—</span>
                              )}
                            </td>
                            <td className="px-2 py-1 text-right text-gray-500">{(dim.confidence * 100).toFixed(0)}%</td>
                            <td className="px-2 py-1 text-right text-gray-400 font-mono text-[10px]">
                              {dim.bbox ? `${Math.round(dim.bbox.x1)},${Math.round(dim.bbox.y1)}` : '—'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 이미지 오버레이 */}
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h4 className="text-xs font-semibold text-gray-500">도면 오버레이</h4>
            <label className="flex items-center gap-1 text-[11px] text-gray-400">
              <input type="checkbox" checked={showGt} onChange={(e) => setShowGt(e.target.checked)} className="rounded w-3 h-3" />
              GT
            </label>
            {hasGeoDebug && (
              <label className="flex items-center gap-1 text-[11px] text-gray-400">
                <input type="checkbox" checked={showGeoDebug} onChange={(e) => setShowGeoDebug(e.target.checked)} className="rounded w-3 h-3" />
                기하학 디버그
              </label>
            )}
          </div>
          <div ref={containerRef} className="relative w-full overflow-auto border border-gray-200 dark:border-gray-700 rounded-lg">
            {imageUrl ? (
              <div className="relative" style={{ width: '100%', height: scaledHeight }}>
                <img src={imageUrl} alt="Drawing" className="w-full h-auto" style={{ display: 'block', pointerEvents: 'none' }} />
                <svg
                  className="absolute top-0 left-0 w-full"
                  style={{ height: scaledHeight }}
                  viewBox={`0 0 ${result.image_width} ${result.image_height}`}
                  preserveAspectRatio="xMinYMin meet"
                >
                  {/* GT (점선) */}
                  {showGt && groundTruth.map((gt, idx) => {
                    const color = ROLE_COLORS[gt.role as keyof typeof ROLE_COLORS] || '#888';
                    return (
                      <g key={`gt-${idx}`}>
                        <rect
                          x={gt.bbox.x1} y={gt.bbox.y1}
                          width={gt.bbox.x2 - gt.bbox.x1} height={gt.bbox.y2 - gt.bbox.y1}
                          fill="none" stroke={color} strokeWidth={2} strokeDasharray="8,4" opacity={0.6}
                        />
                        <rect x={gt.bbox.x1} y={gt.bbox.y2 + 2} width={80} height={16} fill={color} opacity={0.5} rx={3} />
                        <text x={gt.bbox.x1 + 3} y={gt.bbox.y2 + 14} fill="white" fontSize={11} fontWeight="bold">
                          GT {gt.role.toUpperCase()}: {gt.value}
                        </text>
                      </g>
                    );
                  })}

                  {/* 핵심 치수 (OD/ID/W) — 실선 + 라벨 */}
                  {keyDims.map((dim, idx) => {
                    if (!dim.bbox) return null;
                    const color = ROLE_COLOR_MAP[dim.role!] || '#888';
                    const label = ROLE_TAG[dim.role!] || dim.role;
                    return (
                      <g key={`key-${idx}`}>
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

                  {/* 기타 치수 — 얇은 테두리 */}
                  {otherDims.slice(0, 30).map((dim, idx) => {
                    if (!dim.bbox) return null;
                    return (
                      <g key={`other-${idx}`}>
                        <rect
                          x={dim.bbox.x1} y={dim.bbox.y1}
                          width={dim.bbox.x2 - dim.bbox.x1} height={dim.bbox.y2 - dim.bbox.y1}
                          fill="none" stroke="#9ca3af" strokeWidth={1} opacity={0.4}
                          strokeDasharray="4,2"
                        />
                        <text
                          x={dim.bbox.x1 + 2} y={dim.bbox.y2 + 10}
                          fill="#9ca3af" fontSize={9} opacity={0.6}
                        >
                          {dim.value}
                        </text>
                      </g>
                    );
                  })}
                </svg>

                {/* 기하학 디버그 */}
                {hasGeoDebug && showGeoDebug && (
                  <GeometryDebugOverlay
                    debug={selectedCell!.geometry_debug as GeometryDebugInfo}
                    imageWidth={result.image_width}
                    imageHeight={result.image_height}
                    scaledHeight={scaledHeight}
                  />
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-48 text-gray-400 text-sm">이미지 로딩...</div>
            )}
          </div>
        </div>

        {/* 범례 */}
        <div className="flex flex-wrap items-center gap-4 text-[10px] text-gray-400 px-1">
          <span className="flex items-center gap-1">
            <span className="w-6 h-0.5 border-t-2 border-dashed" style={{ borderColor: '#ef4444' }} /> GT (점선)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-6 h-3 rounded" style={{ backgroundColor: '#ef4444', opacity: 0.3 }} /> OD 검출
          </span>
          <span className="flex items-center gap-1">
            <span className="w-6 h-3 rounded" style={{ backgroundColor: '#3b82f6', opacity: 0.3 }} /> ID 검출
          </span>
          <span className="flex items-center gap-1">
            <span className="w-6 h-3 rounded" style={{ backgroundColor: '#22c55e', opacity: 0.3 }} /> W 검출
          </span>
          <span className="flex items-center gap-1">
            <span className="w-6 h-0.5 border-t border-dashed" style={{ borderColor: '#9ca3af' }} /> 기타 치수 (회색)
          </span>
        </div>
      </div>
    </div>
  );
}

function DimRow({ dim, isKey }: { dim: ClassifiedDim; isKey?: boolean }) {
  const color = dim.role ? (ROLE_COLOR_MAP[dim.role] || '#9ca3af') : '#9ca3af';
  const label = dim.role ? (ROLE_TAG[dim.role] || dim.role) : '미분류';

  return (
    <div className={`flex items-center gap-3 px-2 py-1 rounded ${isKey ? 'bg-white/60 dark:bg-gray-800/40' : ''}`}>
      <span
        className="px-1.5 py-0.5 rounded text-[10px] font-bold text-white min-w-[28px] text-center"
        style={{ backgroundColor: color }}
      >
        {label}
      </span>
      <span className="text-sm font-mono font-bold text-gray-900 dark:text-white">{dim.value}</span>
      <span className="text-xs text-gray-400">conf: {(dim.confidence * 100).toFixed(0)}%</span>
      {dim.bbox && (
        <span className="text-[10px] text-gray-300 font-mono ml-auto">
          ({Math.round(dim.bbox.x1)}, {Math.round(dim.bbox.y1)})
        </span>
      )}
    </div>
  );
}
