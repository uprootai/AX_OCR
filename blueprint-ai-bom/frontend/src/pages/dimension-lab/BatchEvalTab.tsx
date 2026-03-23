/**
 * BatchEvalTab — 다수 도면 일괄 치수 평가
 *
 * 세션을 랜덤 선택해 edocr2 OCR -> K/H/S 방법으로 OD/ID/W 추출,
 * 사용자가 맞음/틀림을 토글하여 후행 평가.
 */
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { analysisApi, type SessionEvalRow, type BatchEvalStatus } from '../../lib/api/analysis';
import {
  Play, Loader2, CheckCircle2, XCircle, Minus, LayoutList,
  StopCircle, Download, ChevronRight, ChevronDown, Clock,
} from 'lucide-react';

const POLL_INTERVAL = 2000;

type TriState = boolean | null;

function cycleTriState(v: TriState): TriState {
  if (v === null) return true;
  if (v === true) return false;
  return null;
}

export function BatchEvalTab() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [count, setCount] = useState(10);
  const [batchId, setBatchId] = useState<string | null>(searchParams.get('batch') ?? null);
  const [batch, setBatch] = useState<BatchEvalStatus | null>(null);
  const [batches, setBatches] = useState<Array<{ batch_id: string; status: string; total: number; completed: number; failed: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const activeRowRef = useRef<HTMLTableRowElement | null>(null);

  // 배치 목록 로드
  useEffect(() => {
    analysisApi.listBatchEvals().then(setBatches).catch(() => {});
  }, [batchId]);

  // URL에서 batch_id 복원
  useEffect(() => {
    const urlBatch = searchParams.get('batch');
    if (urlBatch && !batch) loadBatch(urlBatch);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // batch_id -> URL 동기화
  useEffect(() => {
    if (batchId) setSearchParams({ batch: batchId }, { replace: true });
  }, [batchId, setSearchParams]);

  // 활성 행 자동 스크롤
  useEffect(() => {
    if (activeRowRef.current) {
      activeRowRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [batch?.rows]);

  const loadBatch = useCallback(async (id: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    setBatchId(id);
    try {
      const s = await analysisApi.getBatchEvalStatus(id);
      setBatch(s);
      if (s.status === 'running' || s.status === 'pending') {
        startTimeRef.current = Date.now();
        startPolling(id);
      }
    } catch {
      setError(`배치 ${id}를 찾을 수 없습니다`);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startPolling = (id: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const s = await analysisApi.getBatchEvalStatus(id);
        setBatch(s);
        if (s.status === 'completed' || s.status === 'error') {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          startTimeRef.current = null;
        }
      } catch { /* ignore */ }
    }, POLL_INTERVAL);
  };

  const startBatch = useCallback(async () => {
    setError(null);
    setLoading(true);
    startTimeRef.current = Date.now();
    try {
      const res = await analysisApi.startBatchEval(count);
      setBatchId(res.batch_id);
      const status = await analysisApi.getBatchEvalStatus(res.batch_id);
      setBatch(status);
      startPolling(res.batch_id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '배치 시작 실패');
      startTimeRef.current = null;
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [count]);

  const cancelBatch = useCallback(async () => {
    if (!batchId) return;
    try {
      await analysisApi.cancelBatchEval(batchId);
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
      const s = await analysisApi.getBatchEvalStatus(batchId);
      setBatch(s);
      startTimeRef.current = null;
    } catch { setError('취소 실패'); }
  }, [batchId]);

  const saveEval = useCallback(
    async (sessionId: string, field: 'od_correct' | 'id_correct' | 'w_correct', value: TriState) => {
      if (!batchId || !batch) return;
      setBatch((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          rows: prev.rows.map((r) =>
            r.session_id === sessionId ? { ...r, [field]: value } : r,
          ),
        };
      });
      try {
        await analysisApi.saveBatchSessionEval(batchId, sessionId, { [field]: value });
      } catch { /* 다음 폴링에서 복구 */ }
    },
    [batchId, batch],
  );

  const isRunning = batch?.status === 'running';
  const doneRows = batch?.rows.filter((r) => r.status === 'done') ?? [];
  const runningRow = batch?.rows.find((r) => r.status === 'running');

  // ETR 계산
  const etr = useMemo(() => {
    if (!isRunning || !batch || !startTimeRef.current) return null;
    const completed = batch.completed + batch.failed;
    if (completed < 2) return null;
    const elapsed = (Date.now() - startTimeRef.current) / 1000;
    const remaining = batch.total - completed;
    const perItem = elapsed / completed;
    const etrSec = Math.round(perItem * remaining);
    if (etrSec < 60) return `~${etrSec}초`;
    return `~${Math.round(etrSec / 60)}분`;
  }, [isRunning, batch]);

  const exportCsv = useCallback(() => {
    if (!batch) return;
    const BOM = '\uFEFF';
    const headers = ['#', '세션ID', '파일명', '상태', 'OD', 'ID', 'W',
      'K_OD', 'K_ID', 'K_W', 'H_OD', 'H_ID', 'H_W',
      'L_OD', 'L_ID', 'L_W', 'M_OD', 'M_ID', 'M_W',
      'N_OD', 'N_ID', 'N_W', 'S_OD', 'S_ID', 'S_W',
      'OD평가', 'ID평가', 'W평가'];
    const rows = batch.rows.map((r, i) => [
      i + 1, r.session_id, r.filename || '', r.status,
      r.od ?? '', r.id_val ?? '', r.width ?? '',
      r.geometry_od ?? '', r.geometry_id ?? '', r.geometry_w ?? '',
      r.ranking_od ?? '', r.ranking_id ?? '', r.ranking_w ?? '',
      r.endpoint_od ?? '', r.endpoint_id ?? '', r.endpoint_w ?? '',
      r.symbol_od ?? '', r.symbol_id ?? '', r.symbol_w ?? '',
      r.raycast_od ?? '', r.raycast_id ?? '', r.raycast_w ?? '',
      r.ref_od ?? '', r.ref_id ?? '', r.ref_w ?? '',
      r.od_correct === null ? '' : r.od_correct ? 'O' : 'X',
      r.id_correct === null ? '' : r.id_correct ? 'O' : 'X',
      r.w_correct === null ? '' : r.w_correct ? 'O' : 'X',
    ]);
    const csv = BOM + [headers, ...rows].map((row) =>
      row.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(','),
    ).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch_${batchId}_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [batch, batchId]);

  return (
    <div className="space-y-4">
      {/* 컨트롤 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">세션 수</label>
            <input
              type="number"
              min={1}
              max={100}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              disabled={isRunning}
              className="w-16 px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white"
            />
          </div>
          <button
            onClick={startBatch}
            disabled={loading || isRunning}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 text-sm font-medium transition"
          >
            {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {isRunning ? '실행 중...' : '랜덤 선택 & 실행'}
          </button>
          {isRunning && (
            <button
              onClick={cancelBatch}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2 text-sm font-medium transition"
            >
              <StopCircle className="w-4 h-4" />
              취소
            </button>
          )}
          {batch?.status === 'completed' && (
            <button
              onClick={exportCsv}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 text-sm font-medium transition"
            >
              <Download className="w-4 h-4" />
              CSV 다운로드
            </button>
          )}
          {batchId && (
            <span className="text-xs font-mono text-gray-400">#{batchId}</span>
          )}
          {error && <span className="text-sm text-red-500">{error}</span>}
        </div>

        {/* 이전 배치 */}
        {batches.length > 0 && (
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-500">이전:</span>
            {batches.map((b) => (
              <button
                key={b.batch_id}
                onClick={() => loadBatch(b.batch_id)}
                className={`px-2 py-0.5 rounded text-xs font-mono transition ${
                  b.batch_id === batchId
                    ? 'bg-blue-100 text-blue-700 border border-blue-300 dark:bg-blue-900/30 dark:text-blue-400'
                    : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400'
                }`}
              >
                {b.batch_id} ({b.completed}/{b.total})
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 진행률 + 요약 */}
      {batch && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          {/* 현재 처리 중 배너 */}
          {isRunning && runningRow && (
            <div className="mb-3 flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              <span className="text-sm text-blue-700 dark:text-blue-300 font-medium">
                처리 중: {runningRow.filename || runningRow.session_id.slice(0, 8)}
              </span>
              <span className="text-xs text-blue-500 ml-1">
                ({batch.completed + batch.failed + 1}/{batch.total})
              </span>
              {etr && (
                <span className="text-xs text-blue-400 ml-auto flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  남은 시간: {etr}
                </span>
              )}
            </div>
          )}

          {/* 진행률 바 */}
          <div className="mb-3">
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${batch.failed > 0 ? 'bg-amber-500' : 'bg-blue-600'}`}
                style={{ width: `${batch.total > 0 ? ((batch.completed + batch.failed) / batch.total) * 100 : 0}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {batch.completed + batch.failed} / {batch.total}
              <span className="ml-2">({batch.status === 'completed' ? '완료' : batch.status === 'error' ? '오류' : batch.status === 'running' ? '실행 중' : batch.status === 'cancelled' ? '취소됨' : '대기'})</span>
            </div>
          </div>

          {/* 요약 */}
          {doneRows.length > 0 && <SummaryBar rows={batch.rows} />}
        </div>
      )}

      {/* 결과 테이블 */}
      {batch && batch.rows.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          {/* 테이블 헤더 토글 */}
          <div className="px-4 py-2 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <button
              onClick={() => setShowDetail(!showDetail)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition"
            >
              {showDetail ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              방법별 상세 {showDetail ? '숨기기' : '보기'}
            </button>
            {batch.status === 'completed' && (
              <button
                onClick={exportCsv}
                className="flex items-center gap-1 text-xs text-green-600 hover:text-green-700 transition"
              >
                <Download className="w-3 h-3" />
                CSV
              </button>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-700/50 text-left text-xs font-semibold">
                  <th className="px-3 py-2 w-8">#</th>
                  <th className="px-3 py-2">세션</th>
                  <th className="px-3 py-2 w-16">상태</th>
                  <th className="px-3 py-2 w-16 text-red-500">OD</th>
                  <th className="px-3 py-2 w-16 text-blue-500">ID</th>
                  <th className="px-3 py-2 w-16 text-amber-500">W</th>
                  {showDetail && (
                    <>
                      <th className="px-3 py-2 text-gray-400">K (기하학)</th>
                      <th className="px-3 py-2 text-gray-400">H (순위)</th>
                      <th className="px-3 py-2 text-gray-400">L (끝점)</th>
                      <th className="px-3 py-2 text-gray-400">M (심볼)</th>
                      <th className="px-3 py-2 text-gray-400">N (레이)</th>
                      <th className="px-3 py-2 text-gray-400">S (세션명)</th>
                    </>
                  )}
                  <th className="px-3 py-2 w-12">OD</th>
                  <th className="px-3 py-2 w-12">ID</th>
                  <th className="px-3 py-2 w-12">W</th>
                </tr>
              </thead>
              <tbody>
                {batch.rows.map((row, idx) => {
                  const isActive = row.status === 'running';
                  return (
                    <tr
                      key={row.session_id}
                      ref={isActive ? activeRowRef : undefined}
                      className={`border-t border-gray-100 dark:border-gray-700 ${
                        isActive ? 'animate-pulse bg-blue-50 dark:bg-blue-900/10' :
                        row.status === 'error' ? 'bg-red-50 dark:bg-red-900/10' : ''
                      }`}
                    >
                      <td className="px-3 py-2 text-xs text-gray-400">{idx + 1}</td>
                      <td className="px-3 py-2 max-w-[200px] truncate text-xs">
                        {row.filename || row.session_id.slice(0, 8)}
                        {row.has_gt && <span className="ml-1 text-green-500 text-[10px]">GT</span>}
                      </td>
                      <td className="px-3 py-2">
                        <StatusBadge status={row.status} />
                      </td>
                      <td className="px-3 py-2 font-semibold">{row.od ?? '—'}</td>
                      <td className="px-3 py-2 font-semibold">{row.id_val ?? '—'}</td>
                      <td className="px-3 py-2 font-semibold">{row.width ?? '—'}</td>
                      {showDetail && (
                        <>
                          <td className="px-3 py-2 text-xs text-gray-400">
                            {row.geometry_od ?? '—'}/{row.geometry_id ?? '—'}/{row.geometry_w ?? '—'}
                          </td>
                          <td className="px-3 py-2 text-xs text-gray-400">
                            {row.ranking_od ?? '—'}/{row.ranking_id ?? '—'}/{row.ranking_w ?? '—'}
                          </td>
                          <td className="px-3 py-2 text-xs text-gray-400">
                            {row.endpoint_od ?? '—'}/{row.endpoint_id ?? '—'}/{row.endpoint_w ?? '—'}
                          </td>
                          <td className="px-3 py-2 text-xs text-gray-400">
                            {row.symbol_od ?? '—'}/{row.symbol_id ?? '—'}/{row.symbol_w ?? '—'}
                          </td>
                          <td className="px-3 py-2 text-xs text-gray-400">
                            {row.raycast_od ?? '—'}/{row.raycast_id ?? '—'}/{row.raycast_w ?? '—'}
                          </td>
                          <td className="px-3 py-2 text-xs text-gray-400">
                            {row.ref_od ?? '—'}/{row.ref_id ?? '—'}/{row.ref_w ?? '—'}
                          </td>
                        </>
                      )}
                      <td className="px-3 py-2">
                        {row.status === 'done' && (
                          <TriToggle value={row.od_correct} onChange={(v) => saveEval(row.session_id, 'od_correct', v)} />
                        )}
                      </td>
                      <td className="px-3 py-2">
                        {row.status === 'done' && (
                          <TriToggle value={row.id_correct} onChange={(v) => saveEval(row.session_id, 'id_correct', v)} />
                        )}
                      </td>
                      <td className="px-3 py-2">
                        {row.status === 'done' && (
                          <TriToggle value={row.w_correct} onChange={(v) => saveEval(row.session_id, 'w_correct', v)} />
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 빈 상태 */}
      {!batch && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8">
          <div className="max-w-xl mx-auto text-center">
            <LayoutList className="w-12 h-12 text-blue-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">배치 평가</h3>
            <p className="text-sm text-gray-500 mb-6">
              <b>다수 도면</b>을 한 번에 분석하여 알고리즘의 실제 정확도를 검증합니다.
            </p>
            <div className="text-left space-y-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg p-5">
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">1</span>
                <div>
                  <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">세션 수 설정</span>
                  <p className="text-xs text-gray-500 mt-0.5">위에서 분석할 도면 수를 입력합니다 (1~100개). 랜덤으로 선택됩니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">2</span>
                <div>
                  <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">자동 실행</span>
                  <p className="text-xs text-gray-500 mt-0.5">각 도면에 edocr2 OCR + K(기하학)/H(값순위)/S(세션명) 방법으로 OD/ID/W를 추출합니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">3</span>
                <div>
                  <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">후행 평가</span>
                  <p className="text-xs text-gray-500 mt-0.5">결과 테이블에서 각 OD/ID/W 값이 맞는지 토글로 평가합니다. 이 데이터가 리더보드에 반영됩니다.</p>
                </div>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-4">
              대형 도면은 OCR에 수 분이 소요될 수 있습니다. 순차 처리로 안정적으로 진행됩니다.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== 서브 컴포넌트 ====================

function TriToggle({ value, onChange }: { value: TriState; onChange: (v: TriState) => void }) {
  return (
    <button
      onClick={() => onChange(cycleTriState(value))}
      className={`w-7 h-7 rounded flex items-center justify-center text-white text-xs font-bold transition ${
        value === true ? 'bg-green-500 hover:bg-green-600' :
        value === false ? 'bg-red-500 hover:bg-red-600' :
        'bg-gray-400 hover:bg-gray-500'
      }`}
    >
      {value === true ? <CheckCircle2 className="w-3.5 h-3.5" /> :
       value === false ? <XCircle className="w-3.5 h-3.5" /> :
       <Minus className="w-3.5 h-3.5" />}
    </button>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
    running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    done: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  };
  const labels: Record<string, string> = { pending: '대기', running: '실행', done: '완료', error: '오류' };
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${styles[status] ?? styles.pending}`}>
      {labels[status] ?? status}
    </span>
  );
}

function SummaryBar({ rows }: { rows: SessionEvalRow[] }) {
  const done = rows.filter((r) => r.status === 'done');
  const odOk = done.filter((r) => r.od_correct === true).length;
  const idOk = done.filter((r) => r.id_correct === true).length;
  const wOk = done.filter((r) => r.w_correct === true).length;
  const evaluated = done.filter(
    (r) => r.od_correct !== null || r.id_correct !== null || r.w_correct !== null,
  ).length;

  return (
    <div className="flex gap-4 text-sm text-gray-600 dark:text-gray-400 flex-wrap">
      <span>총 <b className="text-gray-900 dark:text-white">{rows.length}</b></span>
      <span>완료 <b className="text-gray-900 dark:text-white">{done.length}</b></span>
      <span>평가 <b className="text-gray-900 dark:text-white">{evaluated}</b></span>
      <span className="text-red-500">OD <b>{odOk}</b></span>
      <span className="text-blue-500">ID <b>{idOk}</b></span>
      <span className="text-amber-500">W <b>{wOk}</b></span>
    </div>
  );
}
