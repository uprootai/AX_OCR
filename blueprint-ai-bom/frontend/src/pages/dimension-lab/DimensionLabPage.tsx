/**
 * DimensionLabPage — OD/ID/W 추출 연구 허브
 *
 * 3개 탭:
 * - 개별 분석: 단일 도면의 GT + 14개 방법 비교
 * - 배치 평가: N개 도면 일괄 추출 + 후행 평가
 * - 리더보드: 방법별 정확도 순위
 */
import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Ruler, ArrowLeft, FlaskConical, LayoutList, Trophy,
} from 'lucide-react';
import type { LabTab } from './types';
import { SingleAnalysisTab } from './SingleAnalysisTab';
import { BatchEvalTab } from './BatchEvalTab';
import { LeaderboardTab } from './LeaderboardTab';

const TABS: { key: LabTab; label: string; icon: typeof FlaskConical }[] = [
  { key: 'single', label: '개별 분석', icon: FlaskConical },
  { key: 'batch', label: '배치 평가', icon: LayoutList },
  { key: 'leaderboard', label: '리더보드', icon: Trophy },
];

export function DimensionLabPage() {
  const [searchParams] = useSearchParams();
  const initialTab = (searchParams.get('tab') as LabTab) || 'single';
  const [activeTab, setActiveTab] = useState<LabTab>(initialTab);

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
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">Dimension Lab</h1>
          <span className="text-sm text-gray-500 hidden sm:inline">
            OD/ID/W 추출 알고리즘 연구
          </span>
        </div>
      </header>

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
