import { useState, useMemo } from 'react';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Eye,
  FileText,
  Download,
  Filter,
} from 'lucide-react';
import { MOCK_VIEWS, MOCK_MATCH_RESULTS } from './mockData';
import type { CroppedView, MatchResult, SeverityLevel } from './types';
import CroppedViewPanel from './components/CroppedViewPanel';
import BboxOverlayViewer from './components/BboxOverlayViewer';
import MatchResultTable from './components/MatchResultTable';
import ManualLabelForm from './components/ManualLabelForm';

type FilterType = SeverityLevel | 'ALL';

export default function BMTHitlVerification() {
  const [selectedView, setSelectedView] = useState<CroppedView | null>(null);
  const [filter, setFilter] = useState<FilterType>('ALL');
  const [verificationResults, setVerificationResults] = useState<MatchResult[]>(MOCK_MATCH_RESULTS);
  const [showManualForm, setShowManualForm] = useState(false);
  const [editingResult, setEditingResult] = useState<MatchResult | null>(null);

  // Summary stats
  const stats = useMemo(() => {
    const total = verificationResults.length;
    const matched = verificationResults.filter((r) => r.severity === 'OK').length;
    const mismatched = verificationResults.filter((r) => r.severity === 'CRITICAL').length;
    const review = verificationResults.filter((r) => r.severity === 'REVIEW' || r.severity === 'WARN').length;
    const pending = verificationResults.filter((r) => !r.verificationAction).length;
    return { total, matched, mismatched, review, pending };
  }, [verificationResults]);

  // Filtered results
  const filteredResults = useMemo(() => {
    if (filter === 'ALL') return verificationResults;
    return verificationResults.filter((r) => r.severity === filter);
  }, [verificationResults, filter]);

  const handleAction = (id: string, action: string) => {
    setVerificationResults((prev) =>
      prev.map((r) => (r.id === id ? { ...r, verificationAction: action as MatchResult['verificationAction'] } : r)),
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <FileText className="w-7 h-7 text-blue-600 dark:text-blue-400" />
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              도면-BOM 교차검증 Human-in-the-Loop
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300">
              <Download className="w-4 h-4" />
              리포트 다운로드
            </button>
          </div>
        </div>

        {/* Summary Stats Bar */}
        <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
            전체: <span className="font-bold text-gray-900 dark:text-white">{stats.total}건</span>
          </span>
          <span className="text-gray-300 dark:text-gray-600">|</span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
            <CheckCircle className="w-3.5 h-3.5" /> 매칭: {stats.matched}
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
            <XCircle className="w-3.5 h-3.5" /> 불일치: {stats.mismatched}
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400">
            <AlertTriangle className="w-3.5 h-3.5" /> 검토필요: {stats.review}
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
            <Eye className="w-3.5 h-3.5" /> 미확인: {stats.pending}
          </span>

          {/* Filter */}
          <div className="ml-auto flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as FilterType)}
              className="text-sm border border-gray-200 dark:border-gray-600 rounded-md px-2 py-1 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300"
            >
              <option value="ALL">전체</option>
              <option value="OK">정상</option>
              <option value="WARN">주의</option>
              <option value="REVIEW">검토 필요</option>
              <option value="CRITICAL">심각</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex gap-4">
        {/* Left Panel - Cropped Views */}
        <div className="w-1/3">
          <CroppedViewPanel
            views={MOCK_VIEWS}
            selectedView={selectedView}
            onSelectView={setSelectedView}
          />
        </div>

        {/* Right Panel - Detail + Results */}
        <div className="w-2/3 space-y-4">
          {selectedView && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-3">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                  {selectedView.viewName}
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  추출 태그 {selectedView.tags.length}개
                </p>
              </div>
              <BboxOverlayViewer
                view={selectedView}
                onTagAction={(tagId, action) => {
                  console.log(`Tag ${tagId}: ${action}`);
                  handleAction(tagId, action);
                }}
                onAddManualTag={(x, y) => {
                  console.log(`수작업 TAG 추가 at (${x.toFixed(1)}%, ${y.toFixed(1)}%)`);
                }}
              />
            </div>
          )}

          <MatchResultTable
            results={filteredResults}
            onAction={(id, action, editedValue) => handleAction(id, action)}
            filter={filter}
          />

          <ManualLabelForm
            onSubmit={(tagCode, partName) => {
              console.log('수작업 TAG 추가:', tagCode, partName);
            }}
          />
        </div>
      </div>
    </div>
  );
}
