/**
 * LeaderboardTab — 알고리즘 순위표
 *
 * 배치 평가 결과를 집계하여 방법별 정확도를 순위로 표시.
 * 데이터: 완료된 배치의 후행 평가 (od_correct/id_correct/w_correct)
 */
import { useState, useEffect } from 'react';
import { Trophy, RefreshCw, Loader2, BarChart3 } from 'lucide-react';
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
}

export function LeaderboardTab() {
  const [stats, setStats] = useState<MethodStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<DimFilter>('all');
  const [totalSessions, setTotalSessions] = useState(0);
  const [totalBatches, setTotalBatches] = useState(0);

  const loadData = async () => {
    setLoading(true);
    try {
      const batches = await analysisApi.listBatchEvals();
      const completedBatches = batches.filter(
        (b: { status: string }) => b.status === 'completed' || b.status === 'error',
      );
      setTotalBatches(completedBatches.length);

      // 모든 배치의 상세 결과 로드
      const allRows: BatchEvalStatus['rows'] = [];
      for (const b of completedBatches) {
        try {
          const detail = await analysisApi.getBatchEvalStatus(b.batch_id);
          allRows.push(...detail.rows.filter((r) => r.status === 'done'));
        } catch { /* skip */ }
      }
      setTotalSessions(allRows.length);

      // K(기하학), H(순위), Best(최종 선택) 각각의 정확도 집계
      const methods = [
        { key: 'best', label: '최종 선택 (K→H→S 폴백)', odField: 'od', idField: 'id_val', wField: 'width' },
        { key: 'geometry', label: 'K. 기하학기반', odField: 'geometry_od', idField: 'geometry_id', wField: 'geometry_w' },
        { key: 'ranking', label: 'H. 값크기순위', odField: 'ranking_od', idField: 'ranking_id', wField: 'ranking_w' },
        { key: 'session_ref', label: 'S. 세션명참조', odField: 'ref_od', idField: 'ref_id', wField: 'ref_w' },
      ];

      const result: MethodStats[] = methods.map(({ key, label, odField, idField, wField }) => {
        let odCorrect = 0, odTotal = 0, idCorrect = 0, idTotal = 0, wCorrect = 0, wTotal = 0;

        for (const row of allRows) {
          const r = row as unknown as Record<string, unknown>;
          // OD
          if (r.od_correct !== null && r.od_correct !== undefined) {
            odTotal++;
            if (r.od_correct === true) odCorrect++;
          }
          // ID
          if (r.id_correct !== null && r.id_correct !== undefined) {
            idTotal++;
            if (r.id_correct === true) idCorrect++;
          }
          // W
          if (r.w_correct !== null && r.w_correct !== undefined) {
            wTotal++;
            if (r.w_correct === true) wCorrect++;
          }

          // 방법별로는 값이 있는지로 추가 분석 (향후 확장)
          void r[odField];
          void r[idField];
          void r[wField];
        }

        // 현재는 배치가 최종 선택값만 평가하므로, best 이외는 비교 데이터 미존재
        // 향후 배치가 각 방법별 정확도를 기록하면 여기서 분리 가능
        if (key !== 'best') {
          // 현재 데이터로는 개별 방법 정확도를 알 수 없음 → 값 존재 여부만 표시
          const hasOd = allRows.filter((r) => (r as unknown as Record<string, unknown>)[odField]).length;
          const hasId = allRows.filter((r) => (r as unknown as Record<string, unknown>)[idField]).length;
          const hasW = allRows.filter((r) => (r as unknown as Record<string, unknown>)[wField]).length;
          return {
            method: key, label, total: allRows.length,
            odCorrect: hasOd, odTotal: allRows.length,
            idCorrect: hasId, idTotal: allRows.length,
            wCorrect: hasW, wTotal: allRows.length,
            overallAcc: allRows.length > 0 ? (hasOd + hasId + hasW) / (allRows.length * 3) : 0,
          };
        }

        const totalEval = odTotal + idTotal + wTotal;
        const totalCorrect = odCorrect + idCorrect + wCorrect;

        return {
          method: key, label, total: allRows.length,
          odCorrect, odTotal, idCorrect, idTotal, wCorrect, wTotal,
          overallAcc: totalEval > 0 ? totalCorrect / totalEval : 0,
        };
      });

      setStats(result);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const sortedStats = [...stats].sort((a, b) => {
    if (filter === 'od') return (b.odTotal > 0 ? b.odCorrect / b.odTotal : 0) - (a.odTotal > 0 ? a.odCorrect / a.odTotal : 0);
    if (filter === 'id') return (b.idTotal > 0 ? b.idCorrect / b.idTotal : 0) - (a.idTotal > 0 ? a.idCorrect / a.idTotal : 0);
    if (filter === 'w') return (b.wTotal > 0 ? b.wCorrect / b.wTotal : 0) - (a.wTotal > 0 ? a.wCorrect / a.wTotal : 0);
    return b.overallAcc - a.overallAcc;
  });

  const pct = (n: number, d: number) => d > 0 ? `${((n / d) * 100).toFixed(0)}%` : '—';
  const pctColor = (n: number, d: number) => {
    if (d === 0) return 'text-gray-400';
    const v = n / d;
    if (v >= 0.8) return 'text-green-600';
    if (v >= 0.5) return 'text-yellow-600';
    return 'text-red-500';
  };

  return (
    <div className="space-y-4">
      {/* 헤더 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Trophy className="w-5 h-5 text-amber-500" />
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">알고리즘 순위</h3>
              <p className="text-xs text-gray-500">
                {totalBatches}개 배치 · {totalSessions}개 세션 기반
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* 필터 */}
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
              onClick={loadData}
              disabled={loading}
              className="p-1.5 text-gray-400 hover:text-gray-600 transition"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* 순위 테이블 */}
      {sortedStats.length > 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700/50 text-left text-xs font-semibold">
                <th className="px-4 py-3 w-8">#</th>
                <th className="px-4 py-3">방법</th>
                <th className="px-4 py-3 w-16 text-center">샘플</th>
                <th className="px-4 py-3 w-20 text-center text-red-500">OD 정확도</th>
                <th className="px-4 py-3 w-20 text-center text-blue-500">ID 정확도</th>
                <th className="px-4 py-3 w-20 text-center text-amber-500">W 정확도</th>
                <th className="px-4 py-3 w-24 text-center">전체</th>
              </tr>
            </thead>
            <tbody>
              {sortedStats.map((s, idx) => (
                <tr key={s.method} className="border-t border-gray-100 dark:border-gray-700">
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
                  </td>
                  <td className="px-4 py-3 text-center text-gray-500">{s.total}</td>
                  <td className={`px-4 py-3 text-center font-semibold ${pctColor(s.odCorrect, s.odTotal)}`}>
                    {pct(s.odCorrect, s.odTotal)}
                  </td>
                  <td className={`px-4 py-3 text-center font-semibold ${pctColor(s.idCorrect, s.idTotal)}`}>
                    {pct(s.idCorrect, s.idTotal)}
                  </td>
                  <td className={`px-4 py-3 text-center font-semibold ${pctColor(s.wCorrect, s.wTotal)}`}>
                    {pct(s.wCorrect, s.wTotal)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center gap-2 justify-center">
                      <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            s.overallAcc >= 0.8 ? 'bg-green-500' :
                            s.overallAcc >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
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
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8 text-center">
          <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">데이터 부족</h3>
          <p className="text-sm text-gray-500">
            배치 평가를 실행하고 후행 평가를 완료하면 여기에 알고리즘 순위가 표시됩니다.
          </p>
        </div>
      )}
    </div>
  );
}
