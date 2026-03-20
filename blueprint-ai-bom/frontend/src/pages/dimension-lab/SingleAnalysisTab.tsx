/**
 * SingleAnalysisTab — 개별 도면 분석 (GT + 방법 실행 + 결과)
 *
 * 기존 3-step 마법사를 제거하고, 한 화면에서 GT 설정/방법 실행/결과 확인이 가능.
 * - GT: 접이식 섹션 (저장된 경우 요약 배너)
 * - 방법: 카테고리 칩 + 전체 실행
 * - 결과: 매트릭스 + 상세 패널
 */
import { useState, useCallback, useEffect } from 'react';
import {
  Play, Loader2, AlertCircle, CheckCircle2, Zap,
  ChevronDown, ChevronRight,
} from 'lucide-react';
import { sessionApi, analysisApi } from '../../lib/api';
import type { FullCompareResponse, CellResult } from '../../lib/api';
import type { Session } from '../../types';
import type { GtAnnotation, MethodInfo } from './types';
import {
  ALL_ENGINES, ENGINE_LABELS, METHOD_INFO,
  CATEGORY_LABELS, CATEGORY_COLORS, ROLE_LABELS,
} from './types';
import { GroundTruthEditor } from './GroundTruthEditor';
import { AccuracyMatrix } from './AccuracyMatrix';
import { CellOverlay } from './CellOverlay';
import { MethodDetailPanel } from './MethodDetailPanel';

const categories = ['symbol', 'statistical', 'pipeline', 'geometry'] as const;

export function SingleAnalysisTab() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [annotations, setAnnotations] = useState<GtAnnotation[]>([]);
  const [gtSaved, setGtSaved] = useState(false);
  const [gtExpanded, setGtExpanded] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [runningMethod, setRunningMethod] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FullCompareResponse | null>(null);
  const [selectedEngines, setSelectedEngines] = useState<string[]>([...ALL_ENGINES]);
  const [selectedCell, setSelectedCell] = useState<CellResult | null>(null);
  const [selectedMethodId, setSelectedMethodId] = useState<string | null>(null);
  const [completedMethods, setCompletedMethods] = useState<Set<string>>(new Set());

  useEffect(() => {
    sessionApi.list(100).then((data) => {
      setSessions(Array.isArray(data) ? data : []);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedSessionId) return;
    setAnnotations([]);
    setGtSaved(false);
    setGtExpanded(false);
    setResult(null);
    setCompletedMethods(new Set());
    setSelectedMethodId(null);
    setSelectedCell(null);

    analysisApi.getGroundTruth(selectedSessionId).then((gt) => {
      if (gt.dimensions.length > 0) {
        setAnnotations(gt.dimensions);
        setGtSaved(true);
      } else {
        setGtExpanded(true);
      }
    }).catch(() => { setGtExpanded(true); });
  }, [selectedSessionId]);

  const handleGtSaved = useCallback(() => {
    setGtSaved(true);
    setGtExpanded(false);
  }, []);

  const toggleEngine = useCallback((engine: string) => {
    setSelectedEngines((prev) =>
      prev.includes(engine) ? prev.filter((e) => e !== engine) : [...prev, engine]
    );
  }, []);

  const handleRunMethod = useCallback(async (methodId: string) => {
    if (!selectedSessionId || selectedEngines.length === 0 || isRunning) return;
    setIsRunning(true);
    setRunningMethod(methodId);
    setError(null);

    try {
      const res = await analysisApi.fullCompare(
        selectedSessionId, selectedEngines, 0.5, [methodId],
      );
      setResult((prev) => {
        if (!prev) return res;
        const existingMethods = new Set(prev.matrix.map((c) => `${c.engine}:${c.method_id}`));
        const newCells = res.matrix.filter(
          (c) => !existingMethods.has(`${c.engine}:${c.method_id}`),
        );
        return {
          ...prev,
          matrix: [...prev.matrix, ...newCells],
          engine_times: { ...prev.engine_times, ...res.engine_times },
          total_methods: prev.total_methods + (newCells.length > 0 ? 1 : 0),
        };
      });
      setCompletedMethods((prev) => new Set([...prev, methodId]));
      setSelectedMethodId(methodId);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '실행 실패');
    } finally {
      setIsRunning(false);
      setRunningMethod(null);
    }
  }, [selectedSessionId, selectedEngines, isRunning]);

  const handleRunAll = useCallback(async () => {
    if (!selectedSessionId || selectedEngines.length === 0 || isRunning) return;
    setIsRunning(true);
    setRunningMethod('all');
    setError(null);

    try {
      const res = await analysisApi.fullCompare(selectedSessionId, selectedEngines);
      setResult(res);
      setCompletedMethods(new Set(METHOD_INFO.map((m) => m.id)));
      setSelectedMethodId(METHOD_INFO[0].id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '전체 실행 실패');
    } finally {
      setIsRunning(false);
      setRunningMethod(null);
    }
  }, [selectedSessionId, selectedEngines, isRunning]);

  const grouped = categories.map((cat) => ({
    category: cat,
    methods: METHOD_INFO.filter((m) => m.category === cat),
  }));

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-3 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* 세션 + 엔진 선택 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">세션</label>
            <select
              value={selectedSessionId}
              onChange={(e) => setSelectedSessionId(e.target.value)}
              disabled={isRunning}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white min-w-[300px]"
            >
              <option value="">도면을 선택하세요...</option>
              {sessions.map((s) => (
                <option key={s.session_id} value={s.session_id}>
                  {s.filename || s.session_id.slice(0, 8)}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">엔진:</span>
            {ALL_ENGINES.map((eng) => (
              <label key={eng} className="flex items-center gap-1 text-xs">
                <input
                  type="checkbox"
                  checked={selectedEngines.includes(eng)}
                  onChange={() => toggleEngine(eng)}
                  disabled={isRunning}
                  className="rounded"
                />
                {ENGINE_LABELS[eng]}
              </label>
            ))}
          </div>
        </div>
      </div>

      {!selectedSessionId && <EmptyState />}

      {selectedSessionId && (
        <>
          {/* GT 섹션 — 접이식 */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setGtExpanded(!gtExpanded)}
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition rounded-xl"
            >
              <div className="flex items-center gap-3">
                {gtExpanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                <span className="text-sm font-semibold text-gray-900 dark:text-white">Ground Truth</span>
                {gtSaved && (
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                    {annotations.map((a) => (
                      <span key={a.role} className="px-2 py-0.5 rounded text-xs font-mono font-bold" style={{ backgroundColor: `${a.role === 'od' ? '#fecaca' : a.role === 'id' ? '#bfdbfe' : '#bbf7d0'}`, color: a.role === 'od' ? '#dc2626' : a.role === 'id' ? '#2563eb' : '#16a34a' }}>
                        {ROLE_LABELS[a.role]}={a.value}
                      </span>
                    ))}
                  </div>
                )}
                {!gtSaved && <span className="text-xs text-amber-600">미설정 — 클릭하여 설정</span>}
              </div>
            </button>
            {gtExpanded && (
              <div className="px-4 pb-4">
                <GroundTruthEditor
                  sessionId={selectedSessionId}
                  annotations={annotations}
                  onChange={setAnnotations}
                  onSaved={handleGtSaved}
                />
              </div>
            )}
          </div>

          {/* 방법 선택 + 실행 */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                  분류 방법
                  {completedMethods.size > 0 && (
                    <span className="ml-2 text-green-600 text-xs font-normal">
                      {completedMethods.size}/{METHOD_INFO.length} 완료
                    </span>
                  )}
                </h3>
              </div>
              <button
                onClick={handleRunAll}
                disabled={isRunning || selectedEngines.length === 0}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 flex items-center gap-2 text-sm font-medium transition"
              >
                {isRunning && runningMethod === 'all' ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Zap className="w-4 h-4" />
                )}
                전체 실행 ({selectedEngines.length}×14)
              </button>
            </div>

            {/* 카테고리별 칩 */}
            <div className="space-y-2">
              {grouped.map(({ category, methods }) => (
                <div key={category} className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-medium text-gray-500 w-16 shrink-0 flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[category] }} />
                    {CATEGORY_LABELS[category]}
                  </span>
                  {methods.map((m) => (
                    <MethodChip
                      key={m.id}
                      method={m}
                      isRunning={isRunning && runningMethod === m.id}
                      isCompleted={completedMethods.has(m.id)}
                      isSelected={selectedMethodId === m.id}
                      isDisabled={isRunning}
                      result={result}
                      engines={selectedEngines}
                      onRun={() => handleRunMethod(m.id)}
                      onSelect={() => setSelectedMethodId(m.id)}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* 결과 영역 */}
          {selectedMethodId && result && (
            <MethodDetailPanel
              methodId={selectedMethodId}
              result={result}
              engines={selectedEngines}
              groundTruth={annotations}
              onClose={() => setSelectedMethodId(null)}
            />
          )}

          {selectedCell && result && (
            <CellOverlay
              cell={selectedCell}
              result={result}
              groundTruth={annotations}
              onClose={() => setSelectedCell(null)}
            />
          )}

          {result && (
            <AccuracyMatrix
              result={result}
              onSelectCell={setSelectedCell}
              selectedCell={selectedCell}
            />
          )}
        </>
      )}
    </div>
  );
}

/** 방법 칩 */
function MethodChip({ method, isRunning, isCompleted, isSelected, isDisabled, result, engines, onRun, onSelect }: {
  method: MethodInfo;
  isRunning: boolean;
  isCompleted: boolean;
  isSelected: boolean;
  isDisabled: boolean;
  result: FullCompareResponse | null;
  engines: string[];
  onRun: () => void;
  onSelect: () => void;
}) {
  let avgScore: number | null = null;
  if (isCompleted && result) {
    const cells = result.matrix.filter(
      (c) => c.method_id === method.id && engines.includes(c.engine),
    );
    if (cells.length > 0) {
      avgScore = cells.reduce((s, c) => s + c.score, 0) / cells.length;
    }
  }

  return (
    <button
      onClick={() => isCompleted ? onSelect() : !isDisabled && onRun()}
      disabled={isRunning}
      title={method.description}
      className={`px-2.5 py-1 rounded-full text-xs font-medium transition flex items-center gap-1 ${
        isSelected
          ? 'bg-blue-600 text-white ring-2 ring-blue-300'
          : isCompleted
          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 hover:bg-green-200 cursor-pointer'
          : isRunning
          ? 'bg-blue-100 text-blue-700 animate-pulse'
          : 'bg-gray-100 text-gray-600 hover:bg-blue-50 hover:text-blue-600 dark:bg-gray-700 dark:text-gray-400 cursor-pointer'
      }`}
    >
      {isRunning && <Loader2 className="w-3 h-3 animate-spin" />}
      {isCompleted && !isRunning && <CheckCircle2 className="w-3 h-3" />}
      {!isCompleted && !isRunning && <Play className="w-2.5 h-2.5" />}
      {method.label}
      {avgScore !== null && (
        <span className={`ml-0.5 ${avgScore >= 1 ? 'text-green-600' : avgScore > 0.5 ? 'text-yellow-600' : 'text-red-500'}`}>
          {(avgScore * 100).toFixed(0)}%
        </span>
      )}
    </button>
  );
}

function EmptyState() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8 text-center">
      <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">개별 분석</h3>
      <p className="text-sm text-gray-500">
        도면을 선택하면 Ground Truth 설정 → 14개 방법 실행 → 정확도 매트릭스를 확인할 수 있습니다.
      </p>
    </div>
  );
}
