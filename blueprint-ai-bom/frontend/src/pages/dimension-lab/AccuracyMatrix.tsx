/**
 * AccuracyMatrix — 7 OCR 엔진 × 10 분류 방법 = 70 조합 정확도 매트릭스
 */
import { Check, X, Minus, Compass } from 'lucide-react';
import type { FullCompareResponse, CellResult } from '../../lib/api';
import { ENGINE_LABELS, METHOD_LABELS, ALL_ENGINES, ALL_METHODS, ROLE_COLORS, GEOMETRY_METHODS } from './types';

interface Props {
  result: FullCompareResponse;
  onSelectCell: (cell: CellResult) => void;
  selectedCell: CellResult | null;
}

function MatchIcon({ match }: { match: boolean | null }) {
  if (match === null) return <Minus className="w-3.5 h-3.5 text-gray-300" />;
  if (match) return <Check className="w-3.5 h-3.5 text-green-600" />;
  return <X className="w-3.5 h-3.5 text-red-500" />;
}

function ScoreCell({ score, od, id_val, width, od_match, id_match, w_match, selected, onClick }: {
  score: number;
  od: string | null;
  id_val: string | null;
  width: string | null;
  od_match: boolean | null;
  id_match: boolean | null;
  w_match: boolean | null;
  selected?: boolean;
  onClick?: () => void;
}) {
  const bg = score >= 1 ? 'bg-green-100 dark:bg-green-900/30'
    : score >= 0.67 ? 'bg-yellow-50 dark:bg-yellow-900/20'
    : score > 0 ? 'bg-orange-50 dark:bg-orange-900/20'
    : 'bg-red-50 dark:bg-red-900/20';

  return (
    <td
      className={`px-2 py-2 text-center border border-gray-200 dark:border-gray-700 ${bg} cursor-pointer hover:ring-2 hover:ring-blue-400 transition ${selected ? 'ring-2 ring-blue-600' : ''}`}
      onClick={onClick}
    >
      <div className="text-xs font-bold" style={{ color: score >= 1 ? '#16a34a' : score > 0 ? '#d97706' : '#dc2626' }}>
        {(score * 100).toFixed(0)}%
      </div>
      <div className="flex items-center justify-center gap-1 mt-0.5">
        {od_match !== undefined && (
          <span className="flex items-center gap-0.5" title={`OD: ${od || '—'}`}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: ROLE_COLORS.od }} />
            <MatchIcon match={od_match} />
          </span>
        )}
        {id_match !== undefined && (
          <span className="flex items-center gap-0.5" title={`ID: ${id_val || '—'}`}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: ROLE_COLORS.id }} />
            <MatchIcon match={id_match} />
          </span>
        )}
        {w_match !== undefined && (
          <span className="flex items-center gap-0.5" title={`W: ${width || '—'}`}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: ROLE_COLORS.w }} />
            <MatchIcon match={w_match} />
          </span>
        )}
      </div>
    </td>
  );
}

export function AccuracyMatrix({ result, onSelectCell, selectedCell }: Props) {
  const engines = ALL_ENGINES.filter((e) => result.engine_times[e] !== undefined);
  const methods = ALL_METHODS;

  const getCell = (engine: string, method: string) =>
    result.matrix.find((c) => c.engine === engine && c.method_id === method);

  // 엔진별 평균 점수
  const engineAvg = (engine: string) => {
    const cells = methods.map((m) => getCell(engine, m)).filter(Boolean);
    if (!cells.length) return 0;
    return cells.reduce((sum, c) => sum + (c?.score ?? 0), 0) / cells.length;
  };

  // 방법별 평균 점수
  const methodAvg = (method: string) => {
    const cells = engines.map((e) => getCell(e, method)).filter(Boolean);
    if (!cells.length) return 0;
    return cells.reduce((sum, c) => sum + (c?.score ?? 0), 0) / cells.length;
  };

  // Ground Truth 요약
  const gt = result.ground_truth;
  const gtOd = gt.find((g) => g.role === 'od');
  const gtId = gt.find((g) => g.role === 'id');
  const gtW = gt.find((g) => g.role === 'w');

  return (
    <div className="space-y-4">
      {/* Ground Truth 요약 */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-800 rounded-xl shadow-sm border border-blue-200 dark:border-gray-700 p-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Ground Truth (정답)</h3>
        <div className="flex gap-6">
          {gtOd && (
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-xs font-bold text-white" style={{ backgroundColor: ROLE_COLORS.od }}>OD</span>
              <span className="text-lg font-bold text-gray-900 dark:text-white">{gtOd.value}</span>
            </div>
          )}
          {gtId && (
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-xs font-bold text-white" style={{ backgroundColor: ROLE_COLORS.id }}>ID</span>
              <span className="text-lg font-bold text-gray-900 dark:text-white">{gtId.value}</span>
            </div>
          )}
          {gtW && (
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-xs font-bold text-white" style={{ backgroundColor: ROLE_COLORS.w }}>W</span>
              <span className="text-lg font-bold text-gray-900 dark:text-white">{gtW.value}</span>
            </div>
          )}
        </div>
      </div>

      {/* 매트릭스 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 overflow-x-auto">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
          정확도 매트릭스 ({engines.length} 엔진 × {methods.length} 방법 = {engines.length * methods.length} 조합)
        </h3>

        <table className="w-full text-xs border-collapse">
          <thead>
            <tr>
              <th className="text-left px-2 py-2 border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 min-w-[100px]">
                엔진 ↓ \ 방법 →
              </th>
              {methods.map((m) => (
                <th key={m} className="px-2 py-2 border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 text-center whitespace-nowrap">
                  <span className="flex items-center justify-center gap-1">
                    {GEOMETRY_METHODS.includes(m) && <Compass className="w-3 h-3 text-cyan-500" />}
                    {METHOD_LABELS[m]?.split('. ')[1] || m}
                  </span>
                </th>
              ))}
              <th className="px-2 py-2 border border-gray-200 dark:border-gray-700 bg-blue-50 dark:bg-blue-900/20 text-center font-bold">
                평균
              </th>
            </tr>
          </thead>
          <tbody>
            {engines.map((engine) => (
              <tr key={engine}>
                <td className="px-2 py-2 border border-gray-200 dark:border-gray-700 font-medium text-gray-900 dark:text-white whitespace-nowrap">
                  {ENGINE_LABELS[engine] || engine}
                  <span className="block text-[10px] text-gray-400">
                    {(result.engine_times[engine] / 1000).toFixed(1)}s
                  </span>
                </td>
                {methods.map((method) => {
                  const cell = getCell(engine, method);
                  if (!cell) return <td key={method} className="px-2 py-2 text-center border border-gray-200 dark:border-gray-700 text-gray-300">—</td>;
                  return (
                    <ScoreCell
                      key={method}
                      score={cell.score}
                      selected={selectedCell?.engine === engine && selectedCell?.method_id === method}
                      onClick={() => onSelectCell(cell)}
                      od={cell.od}
                      id_val={cell.id_val}
                      width={cell.width}
                      od_match={cell.od_match}
                      id_match={cell.id_match}
                      w_match={cell.w_match}
                    />
                  );
                })}
                <td className="px-2 py-2 text-center border border-gray-200 dark:border-gray-700 bg-blue-50 dark:bg-blue-900/20 font-bold">
                  {(engineAvg(engine) * 100).toFixed(0)}%
                </td>
              </tr>
            ))}
            {/* 방법별 평균 행 */}
            <tr className="border-t-2 border-gray-300 dark:border-gray-600">
              <td className="px-2 py-2 border border-gray-200 dark:border-gray-700 font-bold bg-blue-50 dark:bg-blue-900/20">
                평균
              </td>
              {methods.map((method) => (
                <td key={method} className="px-2 py-2 text-center border border-gray-200 dark:border-gray-700 bg-blue-50 dark:bg-blue-900/20 font-bold">
                  {(methodAvg(method) * 100).toFixed(0)}%
                </td>
              ))}
              <td className="px-2 py-2 text-center border border-gray-200 dark:border-gray-700 bg-blue-100 dark:bg-blue-900/40 font-bold">
                {result.matrix.length > 0
                  ? (result.matrix.reduce((s, c) => s + c.score, 0) / result.matrix.length * 100).toFixed(0)
                  : 0}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 베스트/워스트 조합 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <BestWorstCard title="Best 조합 (Top 5)" items={[...result.matrix].sort((a, b) => b.score - a.score).slice(0, 5)} onSelect={onSelectCell} />
        <BestWorstCard title="Worst 조합 (Bottom 5)" items={[...result.matrix].sort((a, b) => a.score - b.score).slice(0, 5)} onSelect={onSelectCell} />
      </div>
    </div>
  );
}

function BestWorstCard({ title, items, onSelect }: { title: string; items: FullCompareResponse['matrix']; onSelect: (cell: CellResult) => void }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">{title}</h4>
      <div className="space-y-1.5">
        {items.map((cell, idx) => (
          <div
            key={idx}
            className="flex items-center gap-2 text-xs cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/30 rounded px-1 py-0.5 transition"
            onClick={() => onSelect(cell)}
          >
            <span className="font-bold text-gray-500 w-4">{idx + 1}.</span>
            <span className="text-gray-700 dark:text-gray-300 min-w-[80px]">{ENGINE_LABELS[cell.engine]}</span>
            <span className="text-gray-500">×</span>
            <span className="text-gray-700 dark:text-gray-300">{METHOD_LABELS[cell.method_id]}</span>
            <span className="ml-auto font-bold" style={{ color: cell.score >= 1 ? '#16a34a' : cell.score > 0 ? '#d97706' : '#dc2626' }}>
              {(cell.score * 100).toFixed(0)}%
            </span>
            <span className="text-gray-400 min-w-[90px] text-right">
              {cell.od || '—'} / {cell.id_val || '—'} / {cell.width || '—'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
