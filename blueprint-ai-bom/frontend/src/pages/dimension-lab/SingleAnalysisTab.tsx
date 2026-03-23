/**
 * SingleAnalysisTab — 개별 도면 분석 (GT + 방법 실행 + 결과)
 *
 * 기존 3-step 마법사를 제거하고, 한 화면에서 GT 설정/방법 실행/결과 확인이 가능.
 * - GT: 접이식 섹션 (저장된 경우 요약 배너)
 * - 방법: 카테고리 칩 + 전체 실행
 * - 결과: 매트릭스 + 상세 패널
 */
import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import {
  Play, Loader2, AlertCircle, CheckCircle2, Zap,
  ChevronDown, ChevronRight, Calendar, Clock, Circle,
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
  const [elapsed, setElapsed] = useState(0);
  const elapsedRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startTimer = useCallback(() => {
    setElapsed(0);
    if (elapsedRef.current) clearInterval(elapsedRef.current);
    elapsedRef.current = setInterval(() => setElapsed((p) => p + 1), 1000);
  }, []);

  const stopTimer = useCallback(() => {
    if (elapsedRef.current) { clearInterval(elapsedRef.current); elapsedRef.current = null; }
  }, []);

  useEffect(() => {
    return () => { if (elapsedRef.current) clearInterval(elapsedRef.current); };
  }, []);

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

  const selectedSession = useMemo(
    () => sessions.find((s) => s.session_id === selectedSessionId),
    [sessions, selectedSessionId],
  );

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

    startTimer();
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
      stopTimer();
      setIsRunning(false);
      setRunningMethod(null);
    }
  }, [selectedSessionId, selectedEngines, isRunning]);

  const handleRunAll = useCallback(async () => {
    if (!selectedSessionId || selectedEngines.length === 0 || isRunning) return;
    setIsRunning(true);
    setRunningMethod('all');
    setError(null);

    startTimer();
    try {
      const res = await analysisApi.fullCompare(selectedSessionId, selectedEngines);
      setResult(res);
      setCompletedMethods(new Set(METHOD_INFO.map((m) => m.id)));
      setSelectedMethodId(METHOD_INFO[0].id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '전체 실행 실패');
    } finally {
      stopTimer();
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

          {/* 엔진 pill 토글 */}
          <div className="flex items-center gap-1.5 ml-auto flex-wrap">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 mr-1">엔진:</span>
            {ALL_ENGINES.map((eng) => (
              <button
                key={eng}
                onClick={() => toggleEngine(eng)}
                disabled={isRunning}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition ${
                  selectedEngines.includes(eng)
                    ? 'bg-blue-600 text-white'
                    : 'border border-gray-300 dark:border-gray-600 text-gray-500 hover:border-blue-400 hover:text-blue-600'
                }`}
              >
                {ENGINE_LABELS[eng]}
              </button>
            ))}
          </div>
        </div>

        {/* 세션 정보 스트립 */}
        {selectedSession && (
          <div className="mt-3 flex items-center gap-3 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700/40 text-xs">
            <span className="font-medium text-gray-700 dark:text-gray-300 truncate max-w-[300px]">
              {selectedSession.filename}
            </span>
            {gtSaved && annotations.length > 0 && (
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3 h-3 text-green-500" />
                {annotations.map((a) => (
                  <span key={a.role} className="px-1.5 py-0.5 rounded font-mono font-bold text-[10px]" style={{
                    backgroundColor: a.role === 'od' ? '#fecaca' : a.role === 'id' ? '#bfdbfe' : '#bbf7d0',
                    color: a.role === 'od' ? '#dc2626' : a.role === 'id' ? '#2563eb' : '#16a34a',
                  }}>
                    {ROLE_LABELS[a.role]}={a.value}
                  </span>
                ))}
              </div>
            )}
            {!gtSaved && (
              <span className="text-amber-500">GT 미설정</span>
            )}
            {selectedSession.created_at && (
              <span className="text-gray-400 ml-auto flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {new Date(selectedSession.created_at).toLocaleDateString()}
              </span>
            )}
          </div>
        )}
      </div>

      {!selectedSessionId && <EmptyState />}

      {selectedSessionId && (
        <>
          {/* GT 섹션 -- 접이식 */}
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
                {!gtSaved && <span className="text-xs text-amber-600">미설정 -- 클릭하여 설정</span>}
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
                전체 실행 ({selectedEngines.length} x {METHOD_INFO.length})
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

          {/* 실행 중 상태 패널 */}
          {isRunning && (
            <RunningStatusPanel
              methodId={runningMethod}
              elapsed={elapsed}
              engineCount={selectedEngines.length}
            />
          )}

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

const GEOMETRY_STEPS = [
  { label: '원 검출 (Contour + HoughCircles)', est: '~5초' },
  { label: '치수선 검출 (LSD)', est: '~3초' },
  { label: '원 주변 OCR 크롭 + 인식', est: '~30-90초' },
  { label: '원 근접도 기반 역할 분류', est: '~1초' },
];

const METHOD_PIPELINE_HINTS: Record<string, string[]> = {
  K: ['원/치수선 검출', 'OCR 크롭 (focused + wide)', '값 크기 기반 OD/ID/W 분류'],
  A: ['OCR 텍스트 추출', '기호 패턴 매칭 (⌀, R, ±)', '역할 분류'],
  B: ['OCR 텍스트 추출', '단위/공차 포함 여부', '역할 분류'],
  all: ['전체 14개 방법 순차 실행', 'OCR 엔진별 텍스트 추출', '방법별 역할 분류 + 점수 산출'],
};

function RunningStatusPanel({ methodId, elapsed, engineCount }: {
  methodId: string | null;
  elapsed: number;
  engineCount: number;
}) {
  const methodInfo = METHOD_INFO.find((m) => m.id === methodId);
  const isGeometry = methodInfo?.category === 'geometry' || methodId === 'K';
  const isAll = methodId === 'all';
  const hints = methodId ? (METHOD_PIPELINE_HINTS[methodId] || METHOD_PIPELINE_HINTS['all']) : [];
  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;
  const timeStr = mins > 0 ? `${mins}분 ${secs}초` : `${secs}초`;

  return (
    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
      <div className="flex items-center gap-3 mb-3">
        <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
        <div className="flex-1">
          <p className="text-sm font-semibold text-blue-800 dark:text-blue-300">
            {isAll ? '전체 실행 중' : `${methodInfo?.label || methodId} 실행 중`}
            <span className="ml-2 text-xs font-normal text-blue-600 dark:text-blue-400">
              ({engineCount}개 엔진)
            </span>
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-sm font-mono font-bold text-blue-700 dark:text-blue-300">
          <Clock className="w-4 h-4" />
          {timeStr}
        </div>
      </div>

      {/* 파이프라인 단계 */}
      {isGeometry && (
        <div className="space-y-1.5 ml-8">
          <p className="text-xs font-medium text-blue-700 dark:text-blue-400 mb-1">기하학 파이프라인 (4단계):</p>
          {GEOMETRY_STEPS.map((step, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <Circle className="w-2.5 h-2.5 text-blue-400" />
              <span className="text-gray-700 dark:text-gray-300">{step.label}</span>
              <span className="text-gray-400 ml-auto">{step.est}</span>
            </div>
          ))}
          <p className="text-[10px] text-blue-500 mt-2">
            * 3단계 OCR 크롭이 가장 오래 걸립니다 (엔진 수 x 크롭 수). 502 에러 시 백엔드 메모리 부족일 수 있습니다.
          </p>
        </div>
      )}

      {!isGeometry && hints.length > 0 && (
        <div className="space-y-1 ml-8">
          {hints.map((hint, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <Circle className="w-2.5 h-2.5 text-blue-400" />
              <span className="text-gray-700 dark:text-gray-300">{hint}</span>
            </div>
          ))}
        </div>
      )}

      {elapsed > 60 && (
        <p className="text-[10px] text-amber-600 dark:text-amber-400 ml-8 mt-2">
          1분 이상 소요 중 — 기하학 방법은 도면 복잡도에 따라 2~5분 걸릴 수 있습니다.
        </p>
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
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8">
      <div className="max-w-xl mx-auto text-center">
        <FlaskIcon className="w-12 h-12 text-blue-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">개별 도면 분석</h3>
        <p className="text-sm text-gray-500 mb-6">
          단일 도면에서 OD/ID/W를 추출하는 <b>14개 분류 방법</b>을 <b>7개 OCR 엔진</b>으로 비교합니다.
        </p>
        <div className="text-left space-y-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg p-5">
          <Step num={1} title="도면 선택" desc="위 드롭다운에서 분석할 세션(도면)을 선택합니다." />
          <Step num={2} title="Ground Truth 설정" desc="도면 위에 드래그로 OD/ID/W 정답 영역과 값을 표시합니다. 이미 설정된 경우 자동 로드됩니다." />
          <Step num={3} title="방법 실행" desc="14개 분류 방법 중 개별 또는 전체를 실행합니다. 기호 기반, 통계/위치, 파이프라인, 기하학 4개 카테고리로 구분됩니다." />
          <Step num={4} title="결과 비교" desc="엔진x방법 정확도 매트릭스에서 어떤 조합이 가장 정확한지 확인합니다. 셀 클릭으로 상세 결과를 볼 수 있습니다." />
        </div>
      </div>
    </div>
  );
}

function Step({ num, title, desc }: { num: number; title: string; desc: string }) {
  return (
    <div className="flex items-start gap-3">
      <span className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
        {num}
      </span>
      <div>
        <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">{title}</span>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{desc}</p>
      </div>
    </div>
  );
}

function FlaskIcon(props: { className?: string }) {
  return <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M9 3h6M10 3v7.4a2 2 0 0 1-.5 1.3L4.26 18.7A1 1 0 0 0 5 20h14a1 1 0 0 0 .74-1.3L14.5 11.7a2 2 0 0 1-.5-1.3V3"/><path d="M8.5 14h7"/></svg>;
}
