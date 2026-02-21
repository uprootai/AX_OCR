/**
 * Agent Verification Dashboard
 *
 * Agent 검증 결과 통계 대시보드
 * - 세션별 approve/reject/modify 분포
 * - Agent vs Human 비교
 * - Reject 이유 분석
 * - Confidence 분포
 */

import { useState, useEffect, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface DashboardData {
  session_id: string;
  filename: string;
  drawing_type: string;
  symbol: ItemStats;
  dimension: ItemStats;
}

interface ItemStats {
  total: number;
  verified?: number;
  pending?: number;
  actions?: Record<string, number>;
  verified_by?: { agent: number; human: number };
  reject_reasons?: Record<string, number>;
  modifications?: Array<Record<string, string>>;
  avg_confidence_by_action?: Record<string, number>;
}

// ─── Utility ───────────────────────────
function pct(n: number, total: number): string {
  return total > 0 ? `${((n / total) * 100).toFixed(1)}%` : '0%';
}

const ACTION_COLORS: Record<string, string> = {
  approved: '#22c55e',
  rejected: '#ef4444',
  modified: '#f59e0b',
  pending: '#94a3b8',
};

// ─── Components ────────────────────────

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div style={{ background: '#1e293b', borderRadius: 8, padding: '16px 20px', minWidth: 140, textAlign: 'center' }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || '#e2e8f0' }}>{value}</div>
      <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function ActionBar({ actions, total }: { actions: Record<string, number>; total: number }) {
  if (total === 0) return <div style={{ color: '#64748b', fontSize: 13 }}>데이터 없음</div>;
  return (
    <div>
      <div style={{ display: 'flex', height: 24, borderRadius: 6, overflow: 'hidden', marginBottom: 8 }}>
        {Object.entries(actions).filter(([, v]) => v > 0).map(([action, count]) => (
          <div
            key={action}
            style={{ width: pct(count, total), background: ACTION_COLORS[action] || '#64748b', minWidth: count > 0 ? 2 : 0 }}
            title={`${action}: ${count}`}
          />
        ))}
      </div>
      <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
        {Object.entries(actions).filter(([, v]) => v > 0).map(([action, count]) => (
          <span key={action} style={{ color: ACTION_COLORS[action] }}>
            {action}: {count} ({pct(count, total)})
          </span>
        ))}
      </div>
    </div>
  );
}

function RejectReasons({ reasons }: { reasons: Record<string, number> }) {
  const entries = Object.entries(reasons).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return null;
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', marginBottom: 6 }}>Reject 이유 분석</div>
      {entries.map(([reason, count]) => (
        <div key={reason} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#94a3b8', padding: '3px 0', borderBottom: '1px solid #334155' }}>
          <span style={{ maxWidth: '80%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{reason}</span>
          <span style={{ color: '#ef4444', fontWeight: 600 }}>{count}</span>
        </div>
      ))}
    </div>
  );
}

function ItemSection({ title, stats }: { title: string; stats: ItemStats }) {
  if (stats.total === 0) return (
    <div style={{ background: '#0f172a', borderRadius: 8, padding: 16, marginBottom: 16 }}>
      <h3 style={{ color: '#64748b', margin: 0 }}>{title} — 데이터 없음</h3>
    </div>
  );

  const actions = stats.actions || {};
  const verifiedBy = stats.verified_by || { agent: 0, human: 0 };
  const avgConf = stats.avg_confidence_by_action || {};

  return (
    <div style={{ background: '#0f172a', borderRadius: 8, padding: 20, marginBottom: 16 }}>
      <h3 style={{ color: '#e2e8f0', margin: '0 0 16px 0', fontSize: 16 }}>{title}</h3>

      {/* Stat cards */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
        <StatCard label="전체" value={stats.total} />
        <StatCard label="승인" value={actions.approved || 0} color="#22c55e" sub={avgConf.approved ? `avg conf: ${avgConf.approved}` : ''} />
        <StatCard label="거부" value={actions.rejected || 0} color="#ef4444" sub={avgConf.rejected ? `avg conf: ${avgConf.rejected}` : ''} />
        <StatCard label="수정" value={actions.modified || 0} color="#f59e0b" />
        <StatCard label="대기" value={actions.pending || 0} color="#94a3b8" />
      </div>

      {/* Action bar */}
      <ActionBar actions={actions} total={stats.total} />

      {/* Agent vs Human */}
      <div style={{ display: 'flex', gap: 16, marginTop: 16, fontSize: 13 }}>
        <span style={{ color: '#60a5fa' }}>Agent: {verifiedBy.agent}건 ({pct(verifiedBy.agent, stats.total)})</span>
        <span style={{ color: '#a78bfa' }}>Human: {verifiedBy.human}건 ({pct(verifiedBy.human, stats.total)})</span>
      </div>

      {/* Reject reasons */}
      {stats.reject_reasons && <RejectReasons reasons={stats.reject_reasons} />}

      {/* Modifications */}
      {stats.modifications && stats.modifications.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', marginBottom: 6 }}>수정 내역</div>
          {stats.modifications.map((mod, i) => (
            <div key={i} style={{ fontSize: 12, color: '#f59e0b', padding: '2px 0' }}>
              {mod.id?.slice(0, 12)}.. {Object.entries(mod).filter(([k]) => k !== 'id').map(([k, v]) => `${k}: ${v}`).join(' | ')}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ─────────────────────────

export default function AgentDashboardPage() {
  const [sessionId, setSessionId] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchDashboard = useCallback(async (sid: string) => {
    if (!sid) return;
    setLoading(true);
    setError('');
    try {
      const resp = await fetch(`${API_BASE}/verification/agent/dashboard/${sid}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const d = await resp.json();
      setData(d);
      setSessionId(sid);
    } catch (e) {
      setError(String(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-load from URL hash
  useEffect(() => {
    const hash = window.location.hash.replace('#', '');
    if (hash) {
      setInputValue(hash);
      fetchDashboard(hash);
    }
  }, [fetchDashboard]);

  return (
    <div style={{ background: '#0f172a', minHeight: '100vh', color: '#e2e8f0', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '24px 16px' }}>
        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 8px 0' }}>Agent Verification Dashboard</h1>
          <p style={{ color: '#64748b', margin: 0, fontSize: 14 }}>LLM Agent 검증 결과 통계 및 분석</p>
        </div>

        {/* Session input */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          <input
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && fetchDashboard(inputValue.trim())}
            placeholder="Session ID 입력..."
            style={{ flex: 1, background: '#1e293b', border: '1px solid #334155', borderRadius: 6, padding: '8px 12px', color: '#e2e8f0', fontSize: 14, outline: 'none' }}
          />
          <button
            onClick={() => fetchDashboard(inputValue.trim())}
            disabled={loading}
            style={{ background: '#3b82f6', color: 'white', border: 'none', borderRadius: 6, padding: '8px 20px', cursor: 'pointer', fontSize: 14, fontWeight: 600 }}
          >
            {loading ? '...' : '조회'}
          </button>
        </div>

        {error && <div style={{ background: '#7f1d1d', borderRadius: 6, padding: 12, color: '#fca5a5', marginBottom: 16, fontSize: 13 }}>{error}</div>}

        {/* Dashboard content */}
        {data && (
          <>
            {/* Session info */}
            <div style={{ background: '#1e293b', borderRadius: 8, padding: '12px 20px', marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: 15, fontWeight: 600 }}>{data.filename}</span>
                <span style={{ color: '#64748b', fontSize: 12, marginLeft: 12 }}>{sessionId.slice(0, 8)}..</span>
              </div>
              <span style={{
                background: data.drawing_type === 'pid' ? '#7c3aed' : data.drawing_type === 'electrical' ? '#2563eb' : '#475569',
                color: 'white', padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600,
              }}>
                {data.drawing_type}
              </span>
            </div>

            {/* Summary cards */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
              <StatCard label="Symbol" value={data.symbol.total} color="#60a5fa" />
              <StatCard label="Dimension" value={data.dimension.total} color="#a78bfa" />
              <StatCard
                label="완료율"
                value={pct(
                  (data.symbol.total - (data.symbol.actions?.pending || 0)) + (data.dimension.total - (data.dimension.actions?.pending || 0)),
                  data.symbol.total + data.dimension.total
                )}
                color="#22c55e"
              />
              <StatCard
                label="Agent 비율"
                value={pct(
                  (data.symbol.verified_by?.agent || 0) + (data.dimension.verified_by?.agent || 0),
                  data.symbol.total + data.dimension.total
                )}
                color="#60a5fa"
              />
            </div>

            {/* Item sections */}
            <ItemSection title="Symbol (검출)" stats={data.symbol} />
            <ItemSection title="Dimension (치수)" stats={data.dimension} />
          </>
        )}

        {!data && !loading && !error && (
          <div style={{ textAlign: 'center', color: '#475569', padding: 60, fontSize: 14 }}>
            Session ID를 입력하여 Agent 검증 결과를 조회하세요
          </div>
        )}
      </div>
    </div>
  );
}
