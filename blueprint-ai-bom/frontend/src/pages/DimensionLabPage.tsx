/**
 * DimensionLabPage - OD/ID/W 추출 방법 비교 페이지
 *
 * 두 가지 비교 모드:
 * 1. 방법론 비교: 같은 OCR 결과에 분류 방법 7개를 독립 적용
 * 2. OCR 엔진 비교: 다른 OCR 엔진으로 치수 추출 + 분류
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { Ruler, Loader2, AlertCircle, Play, ArrowLeft, CircleDot, Circle, MoveHorizontal, CheckCircle2 } from 'lucide-react';
import { sessionApi, analysisApi } from '../lib/api';
import type { MethodCompareResponse } from '../lib/api';
import type { Session } from '../types';

// 방법별 색상 (10개)
const METHOD_COLORS: Record<string, string> = {
  diameter_symbol: '#ef4444',
  dimension_type: '#f97316',
  catalog: '#22c55e',
  composite_signal: '#3b82f6',
  position_width: '#a855f7',
  session_ref: '#ec4899',
  tolerance_fit: '#eab308',
  value_ranking: '#06b6d4',
  heuristic: '#14b8a6',
  full_pipeline: '#6366f1',
};

// ==================== 방법론 비교 결과 ====================

function MethodComparisonTable({ result }: { result: MethodCompareResponse }) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
          OD / ID / W — 방법별 비교
        </h3>
        <div className="text-xs text-gray-400">
          OCR: {result.ocr_engine} | {(result.ocr_time_ms / 1000).toFixed(1)}s | 치수 {result.total_dims}개
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b-2 border-gray-200 dark:border-gray-600">
              <th className="text-left py-2.5 px-3 text-gray-500 dark:text-gray-400 font-medium w-8">#</th>
              <th className="text-left py-2.5 px-3 text-gray-500 dark:text-gray-400 font-medium">분류 방법</th>
              <th className="text-center py-2.5 px-3 font-medium">
                <span className="inline-flex items-center gap-1 text-red-600"><CircleDot className="w-3.5 h-3.5" /> OD (외경)</span>
              </th>
              <th className="text-center py-2.5 px-3 font-medium">
                <span className="inline-flex items-center gap-1 text-blue-600"><Circle className="w-3.5 h-3.5" /> ID (내경)</span>
              </th>
              <th className="text-center py-2.5 px-3 font-medium">
                <span className="inline-flex items-center gap-1 text-green-600"><MoveHorizontal className="w-3.5 h-3.5" /> W (폭)</span>
              </th>
              <th className="text-left py-2.5 px-3 text-gray-500 dark:text-gray-400 font-medium">설명</th>
            </tr>
          </thead>
          <tbody>
            {result.method_results.map((mr, idx) => {
              const color = METHOD_COLORS[mr.method_id] || '#888';
              return (
                <tr key={mr.method_id} className="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/20">
                  <td className="py-3 px-3">
                    <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white" style={{ backgroundColor: color }}>
                      {String.fromCharCode(65 + idx)}
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <div className="font-medium text-gray-900 dark:text-white text-sm">{mr.method_name}</div>
                  </td>
                  <td className="py-3 px-3 text-center">
                    {mr.od ? (
                      <div>
                        <span className="text-xl font-bold text-red-600">{mr.od}</span>
                        <div className="text-[10px] text-gray-400">{(mr.od_confidence * 100).toFixed(0)}%</div>
                      </div>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-center">
                    {mr.id_val ? (
                      <div>
                        <span className="text-xl font-bold text-blue-600">{mr.id_val}</span>
                        <div className="text-[10px] text-gray-400">{(mr.id_confidence * 100).toFixed(0)}%</div>
                      </div>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-center">
                    {mr.width ? (
                      <div>
                        <span className="text-xl font-bold text-green-600">{mr.width}</span>
                        <div className="text-[10px] text-gray-400">{(mr.width_confidence * 100).toFixed(0)}%</div>
                      </div>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-xs text-gray-500 dark:text-gray-400 max-w-xs">
                    {mr.description}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

// ==================== 이미지 오버레이 ====================

function MethodImageOverlay({
  result, selectedMethod, onSelectMethod,
}: {
  result: MethodCompareResponse;
  selectedMethod: string | null;
  onSelectMethod: (id: string | null) => void;
}) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    if (!result.session_id) return;
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
  const activeMethods = selectedMethod
    ? result.method_results.filter((m) => m.method_id === selectedMethod)
    : result.method_results;

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      {/* 방법 선택 버튼 */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">오버레이:</span>
        <button
          onClick={() => onSelectMethod(null)}
          className={`px-2.5 py-1 rounded-full text-xs font-medium border transition ${
            !selectedMethod ? 'bg-gray-800 text-white border-gray-800' : 'border-gray-300 text-gray-500'
          }`}
        >
          전체
        </button>
        {result.method_results.map((mr, idx) => {
          const color = METHOD_COLORS[mr.method_id] || '#888';
          const active = selectedMethod === mr.method_id;
          const hasDims = mr.classified_dims.filter((d) => d.role && d.role !== 'other').length > 0;
          return (
            <button
              key={mr.method_id}
              onClick={() => onSelectMethod(active ? null : mr.method_id)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium border transition flex items-center gap-1.5 ${
                active ? 'text-white' : hasDims ? 'hover:opacity-100' : 'opacity-40 hover:opacity-60'
              }`}
              style={{
                borderColor: color,
                color: active ? 'white' : color,
                backgroundColor: active ? color : 'transparent',
              }}
            >
              <span className="w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold"
                style={{ backgroundColor: active ? 'rgba(255,255,255,0.3)' : color, color: active ? 'white' : 'white' }}
              >
                {String.fromCharCode(65 + idx)}
              </span>
              {mr.method_name.split(' ')[0]}
            </button>
          );
        })}
      </div>

      {/* 이미지 + 오버레이 */}
      <div ref={containerRef} className="relative w-full overflow-auto border border-gray-200 dark:border-gray-700 rounded-lg">
        {imageUrl ? (
          <div className="relative" style={{ width: '100%', height: scaledHeight }}>
            <img src={imageUrl} alt="Drawing" className="w-full h-auto" style={{ display: 'block' }} />
            <svg
              className="absolute top-0 left-0 w-full"
              style={{ height: scaledHeight }}
              viewBox={`0 0 ${result.image_width} ${result.image_height}`}
              preserveAspectRatio="xMinYMin meet"
            >
              {/* 원본 치수 (회색 점선) */}
              {result.raw_dimensions.map((rd) => (
                <g key={`raw-${rd.id}`}>
                  <rect x={rd.bbox.x1} y={rd.bbox.y1} width={rd.bbox.x2 - rd.bbox.x1} height={rd.bbox.y2 - rd.bbox.y1}
                    fill="none" stroke="#9ca3af" strokeWidth={1} opacity={0.25} strokeDasharray="3,3" />
                  <text x={rd.bbox.x1} y={rd.bbox.y1 - 3} fill="#9ca3af" fontSize={10} opacity={0.35}>{rd.value}</text>
                </g>
              ))}

              {/* 방법별 분류된 치수 — 각 방법은 고유 색상 + offset으로 겹침 방지 */}
              {activeMethods.map((mr, mIdx) => {
                const color = METHOD_COLORS[mr.method_id] || '#888';
                const letter = String.fromCharCode(65 + result.method_results.indexOf(mr));
                // 전체 모드: 방법마다 bbox를 바깥으로 확장하여 겹침 구분
                const expand = selectedMethod ? 0 : (mIdx + 1) * 6;

                return mr.classified_dims
                  .filter((d) => d.role && d.role !== 'other' && d.bbox)
                  .map((d, dIdx) => {
                    const roleLabel = d.role === 'outer_diameter' ? 'OD' : d.role === 'inner_diameter' ? 'ID' : 'W';
                    const sw = selectedMethod ? 3 : 2.5;
                    return (
                      <g key={`${mr.method_id}-${dIdx}`} opacity={selectedMethod ? 1 : 0.85}>
                        <rect
                          x={d.bbox!.x1 - expand} y={d.bbox!.y1 - expand}
                          width={d.bbox!.x2 - d.bbox!.x1 + expand * 2}
                          height={d.bbox!.y2 - d.bbox!.y1 + expand * 2}
                          fill="none"
                          stroke={color} strokeWidth={sw}
                          rx={expand > 0 ? 4 : 0}
                        />
                        {/* 라벨 배경 */}
                        <rect
                          x={d.bbox!.x1 - expand} y={d.bbox!.y1 - expand - 18}
                          width={selectedMethod ? 120 : 55} height={16}
                          fill={color} rx={3}
                        />
                        <text
                          x={d.bbox!.x1 - expand + 3} y={d.bbox!.y1 - expand - 6}
                          fill="white" fontSize={11} fontWeight="bold"
                        >
                          {selectedMethod
                            ? `${d.value} [${roleLabel}] ${(d.confidence * 100).toFixed(0)}%`
                            : `${letter} ${roleLabel} ${d.value}`}
                        </text>
                      </g>
                    );
                  });
              })}
            </svg>
          </div>
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-400">이미지 로딩...</div>
        )}
      </div>

      {/* 범례 */}
      {!selectedMethod && (
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs">
          {result.method_results.map((mr, idx) => {
            const color = METHOD_COLORS[mr.method_id] || '#888';
            const hasDims = mr.classified_dims.filter((d) => d.role && d.role !== 'other').length > 0;
            if (!hasDims) return null;
            return (
              <div key={mr.method_id} className="flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold text-white" style={{ backgroundColor: color }}>
                  {String.fromCharCode(65 + idx)}
                </span>
                <span className="text-gray-600 dark:text-gray-400">{mr.method_name}</span>
                <span className="text-gray-400">
                  ({[mr.od && 'OD', mr.id_val && 'ID', mr.width && 'W'].filter(Boolean).join('/')})
                </span>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

// ==================== 방법별 상세 분류 결과 ====================

function MethodDetails({ result }: { result: MethodCompareResponse }) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">방법별 분류 상세</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {result.method_results.map((mr, idx) => {
          const color = METHOD_COLORS[mr.method_id] || '#888';
          const odDims = mr.classified_dims.filter((d) => d.role === 'outer_diameter');
          const idDims = mr.classified_dims.filter((d) => d.role === 'inner_diameter');
          const wDims = mr.classified_dims.filter((d) => d.role === 'length');

          return (
            <div key={mr.method_id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white" style={{ backgroundColor: color }}>
                  {String.fromCharCode(65 + idx)}
                </div>
                <span className="text-sm font-medium text-gray-900 dark:text-white">{mr.method_name}</span>
              </div>

              <div className="space-y-1.5 text-xs">
                {/* OD */}
                <div className="flex items-center gap-2">
                  <span className="w-8 text-red-600 font-medium">OD:</span>
                  {odDims.length > 0 ? (
                    <div className="flex gap-1.5 flex-wrap">
                      {odDims.map((d, i) => (
                        <span key={i} className="px-1.5 py-0.5 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded font-mono">
                          {d.value} <span className="text-red-400">({(d.confidence * 100).toFixed(0)}%)</span>
                        </span>
                      ))}
                    </div>
                  ) : <span className="text-gray-300">미검출</span>}
                </div>

                {/* ID */}
                <div className="flex items-center gap-2">
                  <span className="w-8 text-blue-600 font-medium">ID:</span>
                  {idDims.length > 0 ? (
                    <div className="flex gap-1.5 flex-wrap">
                      {idDims.map((d, i) => (
                        <span key={i} className="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded font-mono">
                          {d.value} <span className="text-blue-400">({(d.confidence * 100).toFixed(0)}%)</span>
                        </span>
                      ))}
                    </div>
                  ) : <span className="text-gray-300">미검출</span>}
                </div>

                {/* W */}
                <div className="flex items-center gap-2">
                  <span className="w-8 text-green-600 font-medium">W:</span>
                  {wDims.length > 0 ? (
                    <div className="flex gap-1.5 flex-wrap">
                      {wDims.map((d, i) => (
                        <span key={i} className="px-1.5 py-0.5 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded font-mono">
                          {d.value} <span className="text-green-400">({(d.confidence * 100).toFixed(0)}%)</span>
                        </span>
                      ))}
                    </div>
                  ) : <span className="text-gray-300">미검출</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ==================== 방법 일치도 매트릭스 ====================

function ConsensusSection({ result }: { result: MethodCompareResponse }) {
  const methods = result.method_results;
  // OD/ID/W 각각에 대해 방법들이 같은 값을 내는지
  const odValues = methods.map((m) => m.od).filter(Boolean);
  const idValues = methods.map((m) => m.id_val).filter(Boolean);
  const wValues = methods.map((m) => m.width).filter(Boolean);

  const mostCommon = (arr: (string | null | undefined)[]) => {
    const filtered = arr.filter(Boolean) as string[];
    if (filtered.length === 0) return null;
    const counts: Record<string, number> = {};
    filtered.forEach((v) => { counts[v] = (counts[v] || 0) + 1; });
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return sorted[0];
  };

  const odConsensus = mostCommon(odValues);
  const idConsensus = mostCommon(idValues);
  const wConsensus = mostCommon(wValues);

  return (
    <section className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-800 rounded-xl shadow-sm border border-blue-200 dark:border-gray-700 p-4">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">합의 결과 (Consensus)</h3>
      <div className="grid grid-cols-3 gap-4">
        {/* OD */}
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">OD (외경)</div>
          {odConsensus ? (
            <>
              <div className="text-2xl font-bold text-red-600">{odConsensus[0]}</div>
              <div className="flex items-center justify-center gap-1 mt-1">
                {odConsensus[1] >= methods.length * 0.5 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                ) : (
                  <AlertCircle className="w-3.5 h-3.5 text-yellow-500" />
                )}
                <span className="text-xs text-gray-500">{odConsensus[1]}/{methods.filter((m) => m.od).length} 방법 일치</span>
              </div>
            </>
          ) : <div className="text-gray-300 text-lg">—</div>}
        </div>

        {/* ID */}
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">ID (내경)</div>
          {idConsensus ? (
            <>
              <div className="text-2xl font-bold text-blue-600">{idConsensus[0]}</div>
              <div className="flex items-center justify-center gap-1 mt-1">
                {idConsensus[1] >= methods.filter((m) => m.id_val).length * 0.5 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                ) : (
                  <AlertCircle className="w-3.5 h-3.5 text-yellow-500" />
                )}
                <span className="text-xs text-gray-500">{idConsensus[1]}/{methods.filter((m) => m.id_val).length} 방법 일치</span>
              </div>
            </>
          ) : <div className="text-gray-300 text-lg">—</div>}
        </div>

        {/* W */}
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">W (폭)</div>
          {wConsensus ? (
            <>
              <div className="text-2xl font-bold text-green-600">{wConsensus[0]}</div>
              <div className="flex items-center justify-center gap-1 mt-1">
                {wConsensus[1] >= methods.filter((m) => m.width).length * 0.5 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                ) : (
                  <AlertCircle className="w-3.5 h-3.5 text-yellow-500" />
                )}
                <span className="text-xs text-gray-500">{wConsensus[1]}/{methods.filter((m) => m.width).length} 방법 일치</span>
              </div>
            </>
          ) : <div className="text-gray-300 text-lg">—</div>}
        </div>
      </div>
    </section>
  );
}

// ==================== Main Page ====================

export function DimensionLabPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [ocrEngine, setOcrEngine] = useState('paddleocr');
  const [confidence, setConfidence] = useState(0.5);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MethodCompareResponse | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<string | null>(null);

  useEffect(() => {
    sessionApi.list(100).then((data) => {
      setSessions(Array.isArray(data) ? data : []);
    }).catch(() => {});
  }, []);

  const handleRun = useCallback(async () => {
    if (!selectedSessionId) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await analysisApi.compareMethods(selectedSessionId, ocrEngine, confidence);
      setResult(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '비교 실행 실패';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [selectedSessionId, ocrEngine, confidence]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 border-b dark:border-gray-700">
        <div className="max-w-[1600px] mx-auto px-4 py-3 flex items-center gap-3">
          <a href="/bom/workflow" className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
            <ArrowLeft className="w-5 h-5" />
          </a>
          <Ruler className="w-6 h-6 text-blue-600" />
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">Dimension Lab</h1>
          <span className="text-sm text-gray-500 dark:text-gray-400">OD/ID/W 분류 방법론 비교</span>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-4 py-4 space-y-4">
        {error && (
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-3 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        {/* Controls */}
        <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">세션</label>
              <select
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white min-w-[200px]"
              >
                <option value="">선택...</option>
                {sessions.map((s) => (
                  <option key={s.session_id} value={s.session_id}>
                    {s.filename || s.session_id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">OCR 엔진</label>
              <select
                value={ocrEngine}
                onChange={(e) => setOcrEngine(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white"
              >
                <option value="paddleocr">PaddleOCR (PP-OCRv5)</option>
                <option value="paddleocr_tiled">PaddleOCR Tiled (타일 분할)</option>
                <option value="edocr2">eDOCr2 (도면 전용)</option>
                <option value="easyocr">EasyOCR</option>
                <option value="trocr">TrOCR (인쇄체)</option>
                <option value="suryaocr">SuryaOCR</option>
                <option value="doctr">DocTR (ResNet50)</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">신뢰도</label>
              <input type="range" min={0} max={1} step={0.05} value={confidence} onChange={(e) => setConfidence(Number(e.target.value))} className="w-20" />
              <span className="text-sm text-gray-600 dark:text-gray-400 w-8">{confidence.toFixed(2)}</span>
            </div>

            <button
              onClick={handleRun}
              disabled={isLoading || !selectedSessionId}
              className="px-4 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm font-medium transition"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              방법론 비교 실행
            </button>
          </div>
        </section>

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-2" />
            <span className="text-gray-600 dark:text-gray-400">OCR 실행 + 10개 분류 방법 적용 중...</span>
          </div>
        )}

        {result && !isLoading && (
          <>
            <ConsensusSection result={result} />
            <MethodComparisonTable result={result} />
            <MethodImageOverlay result={result} selectedMethod={selectedMethod} onSelectMethod={setSelectedMethod} />
            <MethodDetails result={result} />
          </>
        )}

        {!result && !isLoading && (
          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8 text-center">
            <Ruler className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-3">OD/ID/W 분류 방법론 비교</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              동일한 OCR 결과에 10개 분류 방법을 각각 독립 적용하여,<br />
              어떤 방법이 OD/ID/W를 가장 정확하게 찾는지 비교합니다.
            </p>
            <div className="p-4 bg-gray-50 dark:bg-gray-700/30 rounded-lg text-xs text-left max-w-2xl mx-auto">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div><span className="inline-block w-5 h-5 rounded-full bg-red-500 text-white text-center text-[10px] leading-5 mr-1.5">A</span> Ø 기호 + 크기 규칙</div>
                <div><span className="inline-block w-5 h-5 rounded-full bg-orange-500 text-white text-center text-[10px] leading-5 mr-1.5">B</span> dimension_type 기반</div>
                <div><span className="inline-block w-5 h-5 rounded-full bg-green-500 text-white text-center text-[10px] leading-5 mr-1.5">C</span> 베어링 카탈로그 매칭</div>
                <div><span className="inline-block w-5 h-5 rounded-full bg-blue-500 text-white text-center text-[10px] leading-5 mr-1.5">D</span> 복합 시그널 ID 추정</div>
                <div><span className="inline-block w-5 h-5 rounded-full bg-purple-500 text-white text-center text-[10px] leading-5 mr-1.5">E</span> 위치 기반 W 분류</div>
                <div><span className="inline-block w-5 h-5 rounded-full bg-pink-500 text-white text-center text-[10px] leading-5 mr-1.5">F</span> 세션명 기준값 검증</div>
                <div><span className="inline-block w-5 h-5 rounded-full bg-yellow-500 text-white text-center text-[10px] leading-5 mr-1.5">G</span> 공차/끼워맞춤 기반</div>
                <div><span className="inline-block w-5 h-5 rounded-full bg-cyan-500 text-white text-center text-[10px] leading-5 mr-1.5">H</span> 값 크기 순위 (통계)</div>
                <div><span className="inline-block w-5 h-5 rounded-full bg-teal-500 text-white text-center text-[10px] leading-5 mr-1.5">I</span> 휴리스틱 규칙 (fallback)</div>
                <div><span className="inline-block w-5 h-5 rounded-full bg-indigo-500 text-white text-center text-[10px] leading-5 mr-1.5">J</span> 전체 파이프라인 (프로덕션)</div>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
