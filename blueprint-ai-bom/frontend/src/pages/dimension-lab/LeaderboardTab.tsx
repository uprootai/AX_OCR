/**
 * LeaderboardTab — 알고리즘 순위표
 *
 * 배치 평가 결과를 집계하여 방법별 정확도를 순위로 표시.
 * 데이터: 완료된 배치의 후행 평가 (od_correct/id_correct/w_correct)
 */
import { useState, useEffect, useMemo } from 'react';
import { Trophy, RefreshCw, Loader2, GitCompareArrows, Info } from 'lucide-react';
import { analysisApi, type BatchEvalStatus } from '../../lib/api/analysis';

type DimFilter = 'all' | 'od' | 'id' | 'w';

interface MethodStats {
  method: string;
  label: string;
  total: number;
  odCorrect: number;
  odTotal: number;
  idCorrect: number;
  idTotal: number;
  wCorrect: number;
  wTotal: number;
  overallAcc: number;
  coverage: { od: number; id: number; w: number };
}

export function LeaderboardTab() {
  const [stats, setStats] = useState<MethodStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<DimFilter>('all');
  const [totalSessions, setTotalSessions] = useState(0);
  const [totalBatches, setTotalBatches] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [compareSelection, setCompareSelection] = useState<string[]>([]);

  const loadData = async () => {
    setLoading(true);
    try {
      const batches = await analysisApi.listBatchEvals();
      const completedBatches = batches.filter(
        (b: { status: string }) => b.status === 'completed' || b.status === 'error',
      );
      setTotalBatches(completedBatches.length);

      const allRows: BatchEvalStatus['rows'] = [];
      for (const b of completedBatches) {
        try {
          const detail = await analysisApi.getBatchEvalStatus(b.batch_id);
          allRows.push(...detail.rows.filter((r) => r.status === 'done'));
        } catch { /* skip */ }
      }
      setTotalSessions(allRows.length);
      setLastUpdate(new Date().toLocaleString());

      const methods = [
        { key: 'best', label: '최종 선택 (K->H->S 폴백)', odField: 'od', idField: 'id_val', wField: 'width' },
        { key: 'geometry', label: 'K. 기하학기반', odField: 'geometry_od', idField: 'geometry_id', wField: 'geometry_w' },
        { key: 'ranking', label: 'H. 값크기순위', odField: 'ranking_od', idField: 'ranking_id', wField: 'ranking_w' },
        { key: 'session_ref', label: 'S. 세션명참조', odField: 'ref_od', idField: 'ref_id', wField: 'ref_w' },
      ];

      const result: MethodStats[] = methods.map(({ key, label, odField, idField, wField }) => {
        let odCorrect = 0, odTotal = 0, idCorrect = 0, idTotal = 0, wCorrect = 0, wTotal = 0;

        for (const row of allRows) {
          const r = row as unknown as Record<string, unknown>;
          if (r.od_correct !== null && r.od_correct !== undefined) {
            odTotal++;
            if (r.od_correct === true) odCorrect++;
          }
          if (r.id_correct !== null && r.id_correct !== undefined) {
            idTotal++;
            if (r.id_correct === true) idCorrect++;
          }
          if (r.w_correct !== null && r.w_correct !== undefined) {
            wTotal++;
            if (r.w_correct === true) wCorrect++;
          }
        }

        // K/H/S는 "값 존재 여부"를 커버리지로 표시 (정확도가 아님)
        const coverageOd = allRows.filter((r) => (r as unknown as Record<string, unknown>)[odField]).length;
        const coverageId = allRows.filter((r) => (r as unknown as Record<string, unknown>)[idField]).length;
        const coverageW = allRows.filter((r) => (r as unknown as Record<string, unknown>)[wField]).length;

        if (key !== 'best') {
          return {
            method: key, label, total: allRows.length,
            odCorrect, odTotal, idCorrect, idTotal, wCorrect, wTotal,
            overallAcc: (odTotal + idTotal + wTotal) > 0
              ? (odCorrect + idCorrect + wCorrect) / (odTotal + idTotal + wTotal) : 0,
            coverage: {
              od: allRows.length > 0 ? coverageOd / allRows.length : 0,
              id: allRows.length > 0 ? coverageId / allRows.length : 0,
              w: allRows.length > 0 ? coverageW / allRows.length : 0,
            },
          };
        }

        const totalEval = odTotal + idTotal + wTotal;
        const totalCorrect = odCorrect + idCorrect + wCorrect;
        return {
          method: key, label, total: allRows.length,
          odCorrect, odTotal, idCorrect, idTotal, wCorrect, wTotal,
          overallAcc: totalEval > 0 ? totalCorrect / totalEval : 0,
          coverage: {
            od: allRows.length > 0 ? coverageOd / allRows.length : 0,
            id: allRows.length > 0 ? coverageId / allRows.length : 0,
            w: allRows.length > 0 ? coverageW / allRows.length : 0,
          },
        };
      });

      setStats(result);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const sortedStats = useMemo(() => {
    return [...stats].sort((a, b) => {
      if (filter === 'od') return (b.odTotal > 0 ? b.odCorrect / b.odTotal : 0) - (a.odTotal > 0 ? a.odCorrect / a.odTotal : 0);
      if (filter === 'id') return (b.idTotal > 0 ? b.idCorrect / b.idTotal : 0) - (a.idTotal > 0 ? a.idCorrect / a.idTotal : 0);
      if (filter === 'w') return (b.wTotal > 0 ? b.wCorrect / b.wTotal : 0) - (a.wTotal > 0 ? a.wCorrect / a.wTotal : 0);
      return b.overallAcc - a.overallAcc;
    });
  }, [stats, filter]);

  const pct = (n: number, d: number) => d > 0 ? `${((n / d) * 100).toFixed(0)}%` : '--';
  const pctNum = (n: number, d: number) => d > 0 ? (n / d) * 100 : 0;
  const pctColor = (n: number, d: number) => {
    if (d === 0) return 'text-gray-400';
    const v = n / d;
    if (v >= 0.8) return 'text-green-600';
    if (v >= 0.5) return 'text-yellow-600';
    return 'text-red-500';
  };
  const barColor = (v: number) => {
    if (v >= 80) return 'bg-green-500';
    if (v >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const toggleCompare = (method: string) => {
    setCompareSelection((prev) => {
      if (prev.includes(method)) return prev.filter((m) => m !== method);
      if (prev.length >= 2) return [prev[1], method];
      return [...prev, method];
    });
  };

  const compareStats = useMemo(() => {
    if (compareSelection.length !== 2) return null;
    const a = stats.find((s) => s.method === compareSelection[0]);
    const b = stats.find((s) => s.method === compareSelection[1]);
    if (!a || !b) return null;
    return { a, b };
  }, [stats, compareSelection]);

  return (
    <div className="space-y-4">
      {/* 헤더 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Trophy className="w-5 h-5 text-amber-500" />
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">알고리즘 순위</h3>
              <p className="text-xs text-gray-500 flex items-center gap-1">
                <Info className="w-3 h-3" />
                {totalBatches}개 배치 ({totalSessions}개 세션) 기반
                {lastUpdate && <span className="ml-1 text-gray-400">| 마지막 업데이트: {lastUpdate}</span>}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {(['all', 'od', 'id', 'w'] as DimFilter[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition ${
                  filter === f
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400'
                }`}
              >
                {f === 'all' ? '전체' : f.toUpperCase()}
              </button>
            ))}
            <button
              onClick={() => { setCompareMode(!compareMode); setCompareSelection([]); }}
              className={`p-1.5 rounded transition ${
                compareMode ? 'bg-purple-100 text-purple-600' : 'text-gray-400 hover:text-gray-600'
              }`}
              title="방법 비교"
            >
              <GitCompareArrows className="w-4 h-4" />
            </button>
            <button
              onClick={loadData}
              disabled={loading}
              className="p-1.5 text-gray-400 hover:text-gray-600 transition"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* 비교 모드 안내 */}
      {compareMode && compareSelection.length < 2 && (
        <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg px-4 py-2 text-xs text-purple-700 dark:text-purple-300">
          비교할 방법 2개를 클릭하세요 ({compareSelection.length}/2 선택됨)
        </div>
      )}

      {/* 순위 테이블 */}
      {sortedStats.length > 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700/50 text-left text-xs font-semibold">
                <th className="px-4 py-3 w-8">#</th>
                <th className="px-4 py-3">방법</th>
                <th className="px-4 py-3 w-16 text-center">샘플</th>
                <th className="px-4 py-3 w-32 text-center text-red-500">OD 정확도</th>
                <th className="px-4 py-3 w-32 text-center text-blue-500">ID 정확도</th>
                <th className="px-4 py-3 w-32 text-center text-amber-500">W 정확도</th>
                <th className="px-4 py-3 w-32 text-center">전체</th>
              </tr>
            </thead>
            <tbody>
              {sortedStats.map((s, idx) => (
                <tr
                  key={s.method}
                  onClick={() => compareMode && toggleCompare(s.method)}
                  className={`border-t border-gray-100 dark:border-gray-700 ${
                    compareMode ? 'cursor-pointer hover:bg-purple-50 dark:hover:bg-purple-900/10' : ''
                  } ${compareSelection.includes(s.method) ? 'bg-purple-50 dark:bg-purple-900/20 ring-1 ring-purple-300' : ''}`}
                >
                  <td className="px-4 py-3">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      idx === 0 ? 'bg-amber-100 text-amber-700' :
                      idx === 1 ? 'bg-gray-100 text-gray-600' :
                      idx === 2 ? 'bg-orange-100 text-orange-700' :
                      'bg-gray-50 text-gray-400'
                    }`}>
                      {idx + 1}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-medium text-gray-900 dark:text-white">{s.label}</span>
                    {s.method !== 'best' && (
                      <span className="ml-2 text-[10px] text-gray-400">
                        커버리지 {(((s.coverage.od + s.coverage.id + s.coverage.w) / 3) * 100).toFixed(0)}%
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-500">{s.total}</td>
                  <td className="px-4 py-3">
                    <AccBar value={pctNum(s.odCorrect, s.odTotal)} label={pct(s.odCorrect, s.odTotal)} colorClass={pctColor(s.odCorrect, s.odTotal)} />
                  </td>
                  <td className="px-4 py-3">
                    <AccBar value={pctNum(s.idCorrect, s.idTotal)} label={pct(s.idCorrect, s.idTotal)} colorClass={pctColor(s.idCorrect, s.idTotal)} />
                  </td>
                  <td className="px-4 py-3">
                    <AccBar value={pctNum(s.wCorrect, s.wTotal)} label={pct(s.wCorrect, s.wTotal)} colorClass={pctColor(s.wCorrect, s.wTotal)} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 justify-center">
                      <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${barColor(s.overallAcc * 100)}`}
                          style={{ width: `${s.overallAcc * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                        {(s.overallAcc * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyLeaderboard />
      )}

      {/* 비교 뷰 */}
      {compareMode && compareStats && (
        <CompareView a={compareStats.a} b={compareStats.b} />
      )}
    </div>
  );
}

function AccBar({ value, label, colorClass }: { value: number; label: string; colorClass: string }) {
  const barColor = value >= 80 ? 'bg-green-500' : value >= 50 ? 'bg-yellow-500' : value > 0 ? 'bg-red-500' : 'bg-gray-300';
  return (
    <div className="flex items-center gap-2">
      <div className="w-14 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 flex-shrink-0">
        <div className={`h-1.5 rounded-full transition-all ${barColor}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className={`text-xs font-semibold ${colorClass}`}>{label}</span>
    </div>
  );
}

function CompareView({ a, b }: { a: MethodStats; b: MethodStats }) {
  const pct = (n: number, d: number) => d > 0 ? ((n / d) * 100).toFixed(0) : '--';
  const dims = [
    { key: 'OD', color: 'text-red-500', aVal: pct(a.odCorrect, a.odTotal), bVal: pct(b.odCorrect, b.odTotal), aNum: a.odTotal > 0 ? a.odCorrect / a.odTotal : 0, bNum: b.odTotal > 0 ? b.odCorrect / b.odTotal : 0 },
    { key: 'ID', color: 'text-blue-500', aVal: pct(a.idCorrect, a.idTotal), bVal: pct(b.idCorrect, b.idTotal), aNum: a.idTotal > 0 ? a.idCorrect / a.idTotal : 0, bNum: b.idTotal > 0 ? b.idCorrect / b.idTotal : 0 },
    { key: 'W', color: 'text-amber-500', aVal: pct(a.wCorrect, a.wTotal), bVal: pct(b.wCorrect, b.wTotal), aNum: a.wTotal > 0 ? a.wCorrect / a.wTotal : 0, bNum: b.wTotal > 0 ? b.wCorrect / b.wTotal : 0 },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-purple-200 dark:border-purple-800 p-4">
      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        <GitCompareArrows className="w-4 h-4 text-purple-500" />
        방법 비교
      </h4>
      <div className="grid grid-cols-3 gap-4">
        {dims.map(({ key, color, aVal, bVal, aNum, bNum }) => (
          <div key={key} className="text-center">
            <p className={`text-xs font-semibold ${color} mb-2`}>{key}</p>
            <div className="flex items-end justify-center gap-3">
              <div className="text-center">
                <div className="w-10 bg-gray-200 dark:bg-gray-700 rounded-t mx-auto" style={{ height: `${Math.max(aNum * 60, 4)}px` }}>
                  <div className={`w-full rounded-t ${aNum > bNum ? 'bg-green-500' : 'bg-gray-400'}`} style={{ height: '100%' }} />
                </div>
                <p className="text-xs font-bold mt-1">{aVal}%</p>
                <p className="text-[10px] text-gray-400 truncate max-w-[80px]">{a.label.split(' ')[0]}</p>
              </div>
              <div className="text-center">
                <div className="w-10 bg-gray-200 dark:bg-gray-700 rounded-t mx-auto" style={{ height: `${Math.max(bNum * 60, 4)}px` }}>
                  <div className={`w-full rounded-t ${bNum > aNum ? 'bg-green-500' : 'bg-gray-400'}`} style={{ height: '100%' }} />
                </div>
                <p className="text-xs font-bold mt-1">{bVal}%</p>
                <p className="text-[10px] text-gray-400 truncate max-w-[80px]">{b.label.split(' ')[0]}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyLeaderboard() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8">
      <div className="max-w-xl mx-auto text-center">
        <Trophy className="w-12 h-12 text-amber-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">알고리즘 리더보드</h3>
        <p className="text-sm text-gray-500 mb-6">
          배치 평가의 후행 평가 결과를 집계하여 <b>어떤 방법이 가장 정확한지</b> 순위를 매깁니다.
        </p>
        <div className="text-left space-y-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg p-5">
          <div className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-amber-500 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">1</span>
            <div>
              <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">배치 평가 실행</span>
              <p className="text-xs text-gray-500 mt-0.5">"배치 평가" 탭에서 도면을 일괄 분석합니다.</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-amber-500 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">2</span>
            <div>
              <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">후행 평가 완료</span>
              <p className="text-xs text-gray-500 mt-0.5">결과 테이블에서 각 OD/ID/W가 맞는지 토글로 평가합니다.</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-amber-500 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">3</span>
            <div>
              <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">순위 확인</span>
              <p className="text-xs text-gray-500 mt-0.5">K(기하학), H(값순위), S(세션명), 최종 선택의 OD/ID/W별 정확도와 전체 순위를 확인합니다.</p>
            </div>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-4">
          배치를 많이 실행하고 평가할수록 순위의 신뢰도가 높아집니다.
        </p>
      </div>
    </div>
  );
}
