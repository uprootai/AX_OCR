/**
 * BatchEvalPage — 다수 도면 일괄 치수 분석 + 후행 평가
 *
 * 세션을 랜덤 선택해 K(기하학)·H(값순위)·S(세션명) 방법으로 OD/ID/W 추출,
 * 사용자가 맞음/틀림을 토글하여 후행 평가.
 *
 * 새로고침 복원: batch_id를 URL 파라미터로 유지 → 페이지 로드 시 자동 복원.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { analysisApi, type SessionEvalRow, type BatchEvalStatus } from '../../lib/api/analysis';

const POLL_INTERVAL = 2000;

// ==================== 평가 토글 ====================

type TriState = boolean | null;

function cycleTriState(v: TriState): TriState {
  if (v === null) return true;
  if (v === true) return false;
  return null;
}

function TriToggle({
  value,
  onChange,
  label,
}: {
  value: TriState;
  onChange: (v: TriState) => void;
  label: string;
}) {
  const bg =
    value === true ? '#22c55e' : value === false ? '#ef4444' : '#6b7280';
  return (
    <button
      onClick={() => onChange(cycleTriState(value))}
      title={`${label}: ${value === true ? '정확' : value === false ? '오류' : '미평가'}`}
      style={{
        background: bg,
        color: '#fff',
        border: 'none',
        borderRadius: 4,
        padding: '2px 8px',
        cursor: 'pointer',
        fontSize: 13,
        minWidth: 32,
      }}
    >
      {value === true ? '✓' : value === false ? '✗' : '—'}
    </button>
  );
}

// ==================== 요약 바 ====================

function SummaryBar({ rows }: { rows: SessionEvalRow[] }) {
  const done = rows.filter((r) => r.status === 'done');
  const odOk = done.filter((r) => r.od_correct === true).length;
  const idOk = done.filter((r) => r.id_correct === true).length;
  const wOk = done.filter((r) => r.w_correct === true).length;
  const evaluated = done.filter(
    (r) => r.od_correct !== null || r.id_correct !== null || r.w_correct !== null,
  ).length;

  return (
    <div
      style={{
        display: 'flex',
        gap: 16,
        padding: '8px 16px',
        background: '#f8fafc',
        borderRadius: 8,
        fontSize: 14,
        flexWrap: 'wrap',
      }}
    >
      <span>총 <b>{rows.length}</b>개</span>
      <span>완료 <b>{done.length}</b></span>
      <span>평가 <b>{evaluated}</b></span>
      <span style={{ color: '#22c55e' }}>OD 정확 <b>{odOk}</b></span>
      <span style={{ color: '#3b82f6' }}>ID 정확 <b>{idOk}</b></span>
      <span style={{ color: '#f59e0b' }}>W 정확 <b>{wOk}</b></span>
    </div>
  );
}

// ==================== 진행률 바 ====================

function ProgressBar({ total, completed, failed }: { total: number; completed: number; failed: number }) {
  const pct = total > 0 ? Math.round(((completed + failed) / total) * 100) : 0;
  return (
    <div style={{ width: '100%', background: '#e5e7eb', borderRadius: 6, height: 8 }}>
      <div
        style={{
          width: `${pct}%`,
          background: failed > 0 ? '#f59e0b' : '#3b82f6',
          borderRadius: 6,
          height: 8,
          transition: 'width 0.3s',
        }}
      />
    </div>
  );
}

// ==================== 이전 배치 목록 ====================

interface BatchListItem {
  batch_id: string;
  status: string;
  total: number;
  completed: number;
  failed: number;
}

function PreviousBatches({
  onSelect,
  currentBatchId,
}: {
  onSelect: (id: string) => void;
  currentBatchId: string | null;
}) {
  const [batches, setBatches] = useState<BatchListItem[]>([]);

  useEffect(() => {
    analysisApi.listBatchEvals().then(setBatches).catch(() => {});
  }, [currentBatchId]); // 새 배치 시작 시 리프레시

  if (batches.length === 0) return null;

  return (
    <div style={{ marginBottom: 12 }}>
      <span style={{ fontSize: 12, color: '#6b7280', marginRight: 8 }}>이전 배치:</span>
      {batches.map((b) => (
        <button
          key={b.batch_id}
          onClick={() => onSelect(b.batch_id)}
          style={{
            marginRight: 6,
            padding: '2px 10px',
            borderRadius: 4,
            border: b.batch_id === currentBatchId ? '2px solid #3b82f6' : '1px solid #d1d5db',
            background: b.batch_id === currentBatchId ? '#eff6ff' : '#fff',
            cursor: 'pointer',
            fontSize: 12,
          }}
        >
          {b.batch_id} ({b.completed}/{b.total})
          {b.status === 'running' && ' ...'}
        </button>
      ))}
    </div>
  );
}

// ==================== 메인 페이지 ====================

export function BatchEvalPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [count, setCount] = useState(10);
  const [batchId, setBatchId] = useState<string | null>(searchParams.get('batch') ?? null);
  const [batch, setBatch] = useState<BatchEvalStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // URL에서 batch_id 복원 — 페이지 로드 시 자동
  useEffect(() => {
    const urlBatch = searchParams.get('batch');
    if (urlBatch && !batch) {
      loadBatch(urlBatch);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // batch_id → URL 동기화
  useEffect(() => {
    if (batchId) {
      setSearchParams({ batch: batchId }, { replace: true });
    }
  }, [batchId, setSearchParams]);

  // 배치 로드 (복원 또는 이전 배치 선택)
  const loadBatch = useCallback(async (id: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    setBatchId(id);
    try {
      const s = await analysisApi.getBatchEvalStatus(id);
      setBatch(s);
      if (s.status === 'running' || s.status === 'pending') {
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
        }
      } catch { /* 폴링 에러 무시 */ }
    }, POLL_INTERVAL);
  };

  // 배치 시작
  const startBatch = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const res = await analysisApi.startBatchEval(count);
      setBatchId(res.batch_id);
      const status = await analysisApi.getBatchEvalStatus(res.batch_id);
      setBatch(status);
      startPolling(res.batch_id);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '배치 시작 실패';
      setError(msg);
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [count]);

  // 후행 평가 저장
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
      } catch { /* 실패 시 다음 폴링에서 복구 */ }
    },
    [batchId, batch],
  );

  const isRunning = batch?.status === 'running';

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      {/* 헤더 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
        <Link to="/dimension-lab" style={{ color: '#6b7280', textDecoration: 'none' }}>
          Dimension Lab
        </Link>
        <span style={{ color: '#9ca3af' }}>/</span>
        <h1 style={{ margin: 0, fontSize: 20 }}>배치 평가</h1>
        {batchId && (
          <span style={{ fontSize: 12, color: '#9ca3af', fontFamily: 'monospace' }}>
            #{batchId}
          </span>
        )}
      </div>

      {/* 이전 배치 목록 */}
      <PreviousBatches onSelect={loadBatch} currentBatchId={batchId} />

      {/* 컨트롤 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <label style={{ fontSize: 14 }}>
          세션 수:
          <input
            type="number"
            min={1}
            max={100}
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            style={{
              width: 60, marginLeft: 8, padding: '4px 8px',
              borderRadius: 4, border: '1px solid #d1d5db',
            }}
            disabled={isRunning}
          />
        </label>
        <button
          onClick={startBatch}
          disabled={loading || isRunning}
          style={{
            padding: '6px 20px', borderRadius: 6, border: 'none',
            background: isRunning ? '#9ca3af' : '#3b82f6',
            color: '#fff', cursor: isRunning ? 'not-allowed' : 'pointer', fontSize: 14,
          }}
        >
          {isRunning ? '실행 중...' : '랜덤 선택 & 실행'}
        </button>
        {error && <span style={{ color: '#ef4444', fontSize: 13 }}>{error}</span>}
      </div>

      {/* 진행률 */}
      {batch && (
        <div style={{ marginBottom: 12 }}>
          <ProgressBar total={batch.total} completed={batch.completed} failed={batch.failed} />
          <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
            {batch.completed + batch.failed} / {batch.total} ({batch.status})
          </div>
        </div>
      )}

      {/* 요약 */}
      {batch && batch.rows.length > 0 && <SummaryBar rows={batch.rows} />}

      {/* 결과 테이블 */}
      {batch && batch.rows.length > 0 && (
        <div style={{ overflowX: 'auto', marginTop: 16 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f1f5f9', textAlign: 'left' }}>
                <th style={thStyle}>#</th>
                <th style={thStyle}>세션</th>
                <th style={thStyle}>상태</th>
                <th style={{ ...thStyle, color: '#ef4444' }}>OD</th>
                <th style={{ ...thStyle, color: '#3b82f6' }}>ID</th>
                <th style={{ ...thStyle, color: '#f59e0b' }}>W</th>
                <th style={thStyle}>K (기하학)</th>
                <th style={thStyle}>H (순위)</th>
                <th style={thStyle}>OD평가</th>
                <th style={thStyle}>ID평가</th>
                <th style={thStyle}>W평가</th>
              </tr>
            </thead>
            <tbody>
              {batch.rows.map((row, idx) => (
                <tr
                  key={row.session_id}
                  style={{
                    borderBottom: '1px solid #e5e7eb',
                    background: row.status === 'error' ? '#fef2f2' : undefined,
                  }}
                >
                  <td style={tdStyle}>{idx + 1}</td>
                  <td style={{ ...tdStyle, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {row.filename || row.session_id.slice(0, 8)}
                    {row.has_gt && (
                      <span style={{ marginLeft: 4, fontSize: 10, color: '#22c55e' }}>GT</span>
                    )}
                  </td>
                  <td style={tdStyle}>
                    <StatusBadge status={row.status} />
                  </td>
                  <td style={{ ...tdStyle, fontWeight: 600 }}>{row.od ?? '—'}</td>
                  <td style={{ ...tdStyle, fontWeight: 600 }}>{row.id_val ?? '—'}</td>
                  <td style={{ ...tdStyle, fontWeight: 600 }}>{row.width ?? '—'}</td>
                  <td style={{ ...tdStyle, fontSize: 11, color: '#6b7280' }}>
                    {row.geometry_od ?? '—'} / {row.geometry_id ?? '—'} / {row.geometry_w ?? '—'}
                  </td>
                  <td style={{ ...tdStyle, fontSize: 11, color: '#6b7280' }}>
                    {row.ranking_od ?? '—'} / {row.ranking_id ?? '—'} / {row.ranking_w ?? '—'}
                  </td>
                  <td style={tdStyle}>
                    {row.status === 'done' && (
                      <TriToggle
                        value={row.od_correct}
                        onChange={(v) => saveEval(row.session_id, 'od_correct', v)}
                        label="OD"
                      />
                    )}
                  </td>
                  <td style={tdStyle}>
                    {row.status === 'done' && (
                      <TriToggle
                        value={row.id_correct}
                        onChange={(v) => saveEval(row.session_id, 'id_correct', v)}
                        label="ID"
                      />
                    )}
                  </td>
                  <td style={tdStyle}>
                    {row.status === 'done' && (
                      <TriToggle
                        value={row.w_correct}
                        onChange={(v) => saveEval(row.session_id, 'w_correct', v)}
                        label="W"
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ==================== 헬퍼 컴포넌트 ====================

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; label: string }> = {
    pending: { bg: '#e5e7eb', label: '대기' },
    running: { bg: '#dbeafe', label: '실행' },
    done: { bg: '#dcfce7', label: '완료' },
    error: { bg: '#fee2e2', label: '오류' },
  };
  const { bg, label } = map[status] ?? { bg: '#e5e7eb', label: status };
  return (
    <span style={{ background: bg, padding: '2px 8px', borderRadius: 4, fontSize: 11 }}>
      {label}
    </span>
  );
}

// ==================== 스타일 ====================

const thStyle: React.CSSProperties = {
  padding: '8px 10px', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap',
};

const tdStyle: React.CSSProperties = {
  padding: '6px 10px', whiteSpace: 'nowrap',
};
