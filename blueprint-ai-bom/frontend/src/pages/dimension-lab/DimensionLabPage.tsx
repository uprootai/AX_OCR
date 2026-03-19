/**
 * DimensionLabPage — OD/ID/W 추출 방법 비교
 *
 * 워크플로우:
 * 1. Ground Truth 어노테이션 (수동 bbox + 값)
 * 2. 방법 카드 — 설명 확인 후 개별 실행 또는 전체 실행
 * 3. 결과 매트릭스 (점진적 누적)
 */
import { useState, useCallback, useEffect } from 'react';
import {
  Ruler, ArrowLeft, Play, Loader2, AlertCircle,
  CheckCircle2, RotateCcw, Zap,
} from 'lucide-react';
import { sessionApi, analysisApi } from '../../lib/api';
import type { FullCompareResponse, CellResult } from '../../lib/api';
import type { Session } from '../../types';
import type { GtAnnotation, LabStep, MethodInfo } from './types';
import {
  ALL_ENGINES, ENGINE_LABELS, METHOD_INFO,
  CATEGORY_LABELS, CATEGORY_COLORS,
} from './types';
import { GroundTruthEditor } from './GroundTruthEditor';
import { AccuracyMatrix } from './AccuracyMatrix';
import { CellOverlay } from './CellOverlay';
import { MethodDetailPanel } from './MethodDetailPanel';

const STEPS: { key: LabStep; label: string; num: number }[] = [
  { key: 'annotate', label: 'Ground Truth', num: 1 },
  { key: 'running', label: '방법 선택', num: 2 },
  { key: 'results', label: '결과', num: 3 },
];

export function DimensionLabPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [step, setStep] = useState<LabStep>('annotate');
  const [annotations, setAnnotations] = useState<GtAnnotation[]>([]);
  const [gtSaved, setGtSaved] = useState(false);
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
    setResult(null);
    setStep('annotate');
    setCompletedMethods(new Set());

    analysisApi.getGroundTruth(selectedSessionId).then((gt) => {
      if (gt.dimensions.length > 0) {
        setAnnotations(gt.dimensions);
        setGtSaved(true);
      }
    }).catch(() => {});
  }, [selectedSessionId]);

  const handleGtSaved = useCallback(() => {
    setGtSaved(true);
  }, []);

  const toggleEngine = useCallback((engine: string) => {
    setSelectedEngines((prev) =>
      prev.includes(engine) ? prev.filter((e) => e !== engine) : [...prev, engine]
    );
  }, []);

  // 개별 방법 실행
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
        // 기존 결과에 새 방법 결과 병합
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
      setSelectedMethodId(methodId);  // 자동으로 상세 패널 열기
      setStep('results');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '실행 실패';
      setError(message);
    } finally {
      setIsRunning(false);
      setRunningMethod(null);
    }
  }, [selectedSessionId, selectedEngines, isRunning]);

  // 전체 실행
  const handleRunAll = useCallback(async () => {
    if (!selectedSessionId || selectedEngines.length === 0 || isRunning) return;
    setIsRunning(true);
    setRunningMethod('all');
    setError(null);

    try {
      const res = await analysisApi.fullCompare(selectedSessionId, selectedEngines);
      setResult(res);
      setCompletedMethods(new Set(METHOD_INFO.map((m) => m.id)));
      setSelectedMethodId(METHOD_INFO[0].id);  // 첫 번째 방법 상세 자동 열기
      setStep('results');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '전체 실행 실패';
      setError(message);
    } finally {
      setIsRunning(false);
      setRunningMethod(null);
    }
  }, [selectedSessionId, selectedEngines, isRunning]);

  const handleReset = useCallback(() => {
    setStep('annotate');
    setResult(null);
    setError(null);
    setSelectedCell(null);
    setSelectedMethodId(null);
    setCompletedMethods(new Set());
  }, []);

  const goToMethods = useCallback(() => {
    setStep('running');
  }, []);

  // 카테고리별 그룹핑
  const categories = ['symbol', 'statistical', 'pipeline', 'geometry'] as const;
  const grouped = categories.map((cat) => ({
    category: cat,
    methods: METHOD_INFO.filter((m) => m.category === cat),
  }));

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 border-b dark:border-gray-700">
        <div className="max-w-[1600px] mx-auto px-4 py-3 flex items-center gap-3">
          <a href="/bom/workflow" className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
            <ArrowLeft className="w-5 h-5" />
          </a>
          <Ruler className="w-6 h-6 text-blue-600" />
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">Dimension Lab</h1>
          <span className="text-sm text-gray-500">OD/ID/W 추출 정확도 비교</span>
          <a
            href="/bom/dimension-lab/batch-eval"
            className="ml-auto text-sm text-blue-600 hover:text-blue-800 transition"
          >
            배치 평가 &rarr;
          </a>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-4 py-4 space-y-4">
        {error && (
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-3 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        {/* 스텝 + 세션/엔진 선택 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-6 mb-4">
            {STEPS.map((s, idx) => (
              <div key={s.key} className="flex items-center gap-2">
                {idx > 0 && <div className="w-8 h-px bg-gray-300 dark:bg-gray-600" />}
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold cursor-pointer transition ${
                  step === s.key
                    ? 'bg-blue-600 text-white'
                    : (s.key === 'results' && result) || (s.key === 'annotate' && step !== 'annotate')
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-400'
                }`}
                  onClick={() => {
                    if (s.key === 'annotate') setStep('annotate');
                    else if (s.key === 'running' && gtSaved) setStep('running');
                    else if (s.key === 'results' && result) setStep('results');
                  }}
                >
                  {(s.key === 'results' && result) || (s.key === 'annotate' && step !== 'annotate')
                    ? <CheckCircle2 className="w-4 h-4" />
                    : s.num}
                </div>
                <span className={`text-sm font-medium ${step === s.key ? 'text-blue-600' : 'text-gray-500'}`}>
                  {s.label}
                </span>
              </div>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">세션</label>
              <select
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
                disabled={isRunning}
                className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white min-w-[250px]"
              >
                <option value="">선택...</option>
                {sessions.map((s) => (
                  <option key={s.session_id} value={s.session_id}>
                    {s.filename || s.session_id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </div>

            {gtSaved && step === 'annotate' && (
              <button
                onClick={goToMethods}
                className="px-4 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 text-sm font-medium transition ml-auto"
              >
                방법 선택으로 →
              </button>
            )}

            {(step === 'running' || step === 'results') && (
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
            )}

            {step === 'results' && (
              <button
                onClick={handleReset}
                className="px-3 py-1.5 bg-gray-500 text-white rounded-lg hover:bg-gray-600 flex items-center gap-2 text-sm font-medium transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                초기화
              </button>
            )}
          </div>
        </div>

        {/* Step 1: Ground Truth */}
        {step === 'annotate' && selectedSessionId && (
          <GroundTruthEditor
            sessionId={selectedSessionId}
            annotations={annotations}
            onChange={setAnnotations}
            onSaved={handleGtSaved}
          />
        )}

        {/* Step 2: 방법 카드 */}
        {step === 'running' && (
          <div className="space-y-4">
            {/* 전체 실행 버튼 */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                    분류 방법 선택
                  </h3>
                  <p className="text-xs text-gray-500 mt-1">
                    각 방법을 개별 실행하거나, 전체를 한 번에 실행할 수 있습니다.
                    {completedMethods.size > 0 && (
                      <span className="ml-2 text-green-600 font-medium">
                        {completedMethods.size}/{METHOD_INFO.length} 완료
                      </span>
                    )}
                  </p>
                </div>
                <button
                  onClick={handleRunAll}
                  disabled={isRunning}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 flex items-center gap-2 text-sm font-medium transition"
                >
                  {isRunning && runningMethod === 'all' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Zap className="w-4 h-4" />
                  )}
                  전체 실행 ({selectedEngines.length} 엔진 × 14 방법)
                </button>
              </div>
            </div>

            {/* 카테고리별 방법 카드 */}
            {grouped.map(({ category, methods }) => (
              <div key={category}>
                <div className="flex items-center gap-2 mb-2 px-1">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: CATEGORY_COLORS[category] }}
                  />
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    {CATEGORY_LABELS[category]}
                  </h4>
                  <span className="text-xs text-gray-400">({methods.length}개)</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {methods.map((m) => (
                    <MethodCard
                      key={m.id}
                      method={m}
                      isRunning={isRunning && runningMethod === m.id}
                      isCompleted={completedMethods.has(m.id)}
                      isDisabled={isRunning}
                      onRun={() => handleRunMethod(m.id)}
                      result={result}
                      engines={selectedEngines}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Step 3: Results */}
        {step === 'results' && result && (
          <>
            {/* 방법 카드 (축소) — 추가 실행 가능 */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                  방법 ({completedMethods.size}/{METHOD_INFO.length} 실행됨)
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setStep('running')}
                    className="px-3 py-1 text-xs text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition"
                  >
                    방법 상세 보기
                  </button>
                  {completedMethods.size < METHOD_INFO.length && (
                    <button
                      onClick={handleRunAll}
                      disabled={isRunning}
                      className="px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 text-xs font-medium transition"
                    >
                      {isRunning ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                      나머지 전체 실행
                    </button>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {METHOD_INFO.map((m) => {
                  const done = completedMethods.has(m.id);
                  const running = isRunning && runningMethod === m.id;
                  return (
                    <button
                      key={m.id}
                      onClick={() => {
                        if (done) {
                          setSelectedMethodId(m.id);
                        } else if (!isRunning) {
                          handleRunMethod(m.id);
                        }
                      }}
                      disabled={running}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium transition flex items-center gap-1 ${
                        selectedMethodId === m.id
                          ? 'bg-blue-600 text-white ring-2 ring-blue-300'
                          : done
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 cursor-pointer'
                          : running
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                          : 'bg-gray-100 text-gray-600 hover:bg-blue-50 hover:text-blue-600 dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-blue-900/20 cursor-pointer'
                      }`}
                    >
                      {running && <Loader2 className="w-3 h-3 animate-spin" />}
                      {done && <CheckCircle2 className="w-3 h-3" />}
                      {m.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {selectedMethodId && (
              <MethodDetailPanel
                methodId={selectedMethodId}
                result={result}
                engines={selectedEngines}
                groundTruth={annotations}
                onClose={() => setSelectedMethodId(null)}
              />
            )}

            {selectedCell && (
              <CellOverlay
                cell={selectedCell}
                result={result}
                groundTruth={annotations}
                onClose={() => setSelectedCell(null)}
              />
            )}
            <AccuracyMatrix
              result={result}
              onSelectCell={setSelectedCell}
              selectedCell={selectedCell}
            />
          </>
        )}

        {/* 빈 상태 */}
        {!selectedSessionId && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8 text-center">
            <Ruler className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-3">Dimension Lab</h3>
            <p className="text-sm text-gray-500 mb-4">
              도면에서 OD/ID/W를 가장 정확하게 추출하는 최적의 방법을 찾습니다.
            </p>
            <div className="p-4 bg-gray-50 dark:bg-gray-700/30 rounded-lg text-xs text-left max-w-lg mx-auto space-y-2">
              <div className="flex items-start gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shrink-0">1</span>
                <span className="text-gray-600 dark:text-gray-400"><strong>Ground Truth</strong> — 도면 위에 드래그로 OD/ID/W 정답 영역 표시</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shrink-0">2</span>
                <span className="text-gray-600 dark:text-gray-400"><strong>방법 선택</strong> — 14개 분류 방법 중 관심 있는 것만 개별 실행 (전체도 가능)</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shrink-0">3</span>
                <span className="text-gray-600 dark:text-gray-400"><strong>결과</strong> — 정확도 매트릭스 + 오버레이 비교. 추가 방법 언제든 실행 가능</span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

/** 개별 방법 카드 */
function MethodCard({ method, isRunning, isCompleted, isDisabled, onRun, result, engines }: {
  method: MethodInfo;
  isRunning: boolean;
  isCompleted: boolean;
  isDisabled: boolean;
  onRun: () => void;
  result: FullCompareResponse | null;
  engines: string[];
}) {
  // 이미 실행된 경우 평균 점수 표시
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
    <div
      className={`rounded-xl border p-3.5 transition cursor-pointer ${
        isCompleted
          ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
          : isRunning
          ? 'bg-blue-50 dark:bg-blue-900/10 border-blue-300 dark:border-blue-700 animate-pulse'
          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-md'
      }`}
      onClick={() => !isCompleted && !isDisabled && onRun()}
    >
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: CATEGORY_COLORS[method.category] }}
          />
          <span className="text-sm font-bold text-gray-900 dark:text-white">
            {method.label}
          </span>
        </div>
        {isRunning && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
        {isCompleted && avgScore !== null && (
          <span className={`text-sm font-bold ${
            avgScore >= 1 ? 'text-green-600' : avgScore > 0.5 ? 'text-yellow-600' : 'text-red-500'
          }`}>
            {(avgScore * 100).toFixed(0)}%
          </span>
        )}
        {isCompleted && avgScore === null && (
          <CheckCircle2 className="w-4 h-4 text-green-500" />
        )}
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
        {method.description}
      </p>
      {!isCompleted && !isRunning && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-blue-600 dark:text-blue-400 font-medium">
          <Play className="w-3 h-3" />
          클릭하여 실행
        </div>
      )}
    </div>
  );
}
