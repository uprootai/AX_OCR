/**
 * DimensionLabPage — OD/ID/W 추출 연구 허브
 *
 * 3개 탭:
 * - 개별 분석: 단일 도면의 GT + 14개 방법 비교
 * - 배치 평가: N개 도면 일괄 추출 + 후행 평가
 * - 리더보드: 방법별 정확도 순위
 */
import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Ruler, ArrowLeft, FlaskConical, LayoutList, Trophy,
  FileImage, CheckSquare, Layers,
} from 'lucide-react';
import type { LabTab } from './types';
import { SingleAnalysisTab } from './SingleAnalysisTab';
import { BatchEvalTab } from './BatchEvalTab';
import { LeaderboardTab } from './LeaderboardTab';
import { sessionApi } from '../../lib/api';
import { analysisApi } from '../../lib/api/analysis';

const TABS: { key: LabTab; label: string; icon: typeof FlaskConical }[] = [
  { key: 'single', label: '개별 분석', icon: FlaskConical },
  { key: 'batch', label: '배치 평가', icon: LayoutList },
  { key: 'leaderboard', label: '리더보드', icon: Trophy },
];

interface LabStats {
  totalSessions: number;
  completedBatches: number;
  totalBatches: number;
}

export function DimensionLabPage() {
  const [searchParams] = useSearchParams();
  const initialTab = (searchParams.get('tab') as LabTab) || 'single';
  const [activeTab, setActiveTab] = useState<LabTab>(initialTab);
  const [stats, setStats] = useState<LabStats>({ totalSessions: 0, completedBatches: 0, totalBatches: 0 });

  useEffect(() => {
    Promise.all([
      sessionApi.list(100).then((s) => (Array.isArray(s) ? s.length : 0)).catch(() => 0),
      analysisApi.listBatchEvals().catch(() => []),
    ]).then(([sessionCount, batches]) => {
      const completed = batches.filter((b: { status: string }) =>
        b.status === 'completed' || b.status === 'error',
      ).length;
      setStats({ totalSessions: sessionCount, completedBatches: completed, totalBatches: batches.length });
    });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 헤더 */}
      <header className="bg-white dark:bg-gray-800 border-b dark:border-gray-700">
        <div className="max-w-[1600px] mx-auto px-4 py-3 flex items-center gap-3">
          <Link
            to="/workflow"
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <Ruler className="w-6 h-6 text-blue-600" />
          <div>
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">Dimension Lab</h1>
            <p className="text-xs text-gray-500 hidden sm:block">
              7개 OCR 엔진 x 14개 분류 방법으로 OD/ID/W 추출 알고리즘을 비교 평가합니다
            </p>
          </div>
        </div>
      </header>

      {/* 통계 스트립 */}
      <div className="bg-white dark:bg-gray-800 border-b dark:border-gray-700">
        <div className="max-w-[1600px] mx-auto px-4 py-2 flex gap-3">
          <StatCard
            icon={FileImage}
            label="전체 도면"
            value={stats.totalSessions}
            color="border-blue-500"
          />
          <StatCard
            icon={CheckSquare}
            label="완료 배치"
            value={stats.completedBatches}
            color="border-green-500"
          />
          <StatCard
            icon={Layers}
            label="전체 배치"
            value={stats.totalBatches}
            color="border-amber-500"
          />
        </div>
      </div>

      {/* 탭 바 */}
      <div className="bg-white dark:bg-gray-800 border-b dark:border-gray-700">
        <div className="max-w-[1600px] mx-auto px-4 flex gap-1">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-4 py-2.5 text-sm font-medium flex items-center gap-2 border-b-2 transition ${
                activeTab === key
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
              {key === 'batch' && stats.completedBatches > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                  {stats.completedBatches}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 탭 컨텐츠 */}
      <main className="max-w-[1600px] mx-auto px-4 py-4">
        {activeTab === 'single' && <SingleAnalysisTab />}
        {activeTab === 'batch' && <BatchEvalTab />}
        {activeTab === 'leaderboard' && <LeaderboardTab />}
      </main>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }: {
  icon: typeof FileImage;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className={`flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-gray-50 dark:bg-gray-700/40 border-l-3 ${color}`}>
      <Icon className="w-4 h-4 text-gray-400" />
      <div>
        <p className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</p>
        <p className="text-sm font-bold text-gray-900 dark:text-white">{value}</p>
      </div>
    </div>
  );
}
