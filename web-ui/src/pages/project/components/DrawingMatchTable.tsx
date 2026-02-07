/**
 * DrawingMatchTable - 도면 매칭 테이블
 *
 * web-ui 네이티브 구현 (다크모드 지원)
 */

import { useState } from 'react';
import { Link2, Loader2, Search, AlertCircle } from 'lucide-react';
import { projectApi, type BOMItem, type DrawingMatchResult } from '../../../lib/blueprintBomApi';

interface DrawingMatchTableProps {
  projectId: string;
  bomItems: BOMItem[];
  drawingFolder?: string;
  onMatchComplete: (result: DrawingMatchResult) => void;
}

export function DrawingMatchTable({
  projectId,
  bomItems,
  drawingFolder: initialFolder,
  onMatchComplete,
}: DrawingMatchTableProps) {
  const [folderPath, setFolderPath] = useState(initialFolder || '');
  const [isMatching, setIsMatching] = useState(false);
  const [result, setResult] = useState<DrawingMatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const quotationItems = bomItems.filter((i) => i.needs_quotation);

  const handleMatch = async () => {
    if (!folderPath.trim()) {
      setError('도면 폴더 경로를 입력하세요.');
      return;
    }
    setIsMatching(true);
    setError(null);
    try {
      const data = await projectApi.matchDrawings(projectId, folderPath.trim());
      setResult(data);
      onMatchComplete(data);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : '도면 매칭에 실패했습니다.';
      setError(msg);
    } finally {
      setIsMatching(false);
    }
  };

  const displayItems = result?.items.filter((i) => i.needs_quotation) ?? quotationItems;
  const matchedCount = result?.matched_count ?? 0;
  const totalCount = result?.total_items ?? quotationItems.length;
  const matchPercent = totalCount > 0 ? Math.round((matchedCount / totalCount) * 100) : 0;
  const unmatchedCount = result?.unmatched_count ?? 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
        <Link2 className="w-5 h-5 text-gray-400 dark:text-gray-500" />
        <h3 className="font-semibold text-gray-900 dark:text-white">도면 매칭</h3>
      </div>

      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
        <label className="block text-sm text-gray-600 dark:text-gray-400 mb-2">도면 폴더 경로</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            placeholder="/app/data/dsebearing/PJT/04_부품도면"
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     placeholder-gray-400 dark:placeholder-gray-500
                     focus:outline-none focus:ring-2 focus:ring-blue-300 dark:focus:ring-blue-500"
          />
          <button
            onClick={handleMatch}
            disabled={isMatching || !folderPath.trim()}
            className="px-4 py-2 bg-blue-500 dark:bg-blue-600 text-white rounded-lg hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {isMatching ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            매칭 시작
          </button>
        </div>
        {error && (
          <div className="mt-2 flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4 mb-2">
            <span className="text-sm text-gray-700 dark:text-gray-300">
              매칭 결과: <span className="font-bold">{matchedCount}/{totalCount}</span>{' '}
              ({matchPercent}%)
            </span>
            {unmatchedCount > 0 && (
              <span className="text-sm text-red-600 dark:text-red-400">
                미매칭 {unmatchedCount}개
              </span>
            )}
          </div>
          <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 dark:bg-green-400 transition-all"
              style={{ width: `${matchPercent}%` }}
            />
          </div>
        </div>
      )}

      <div className="max-h-[400px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0">
            <tr className="text-left text-gray-500 dark:text-gray-400">
              <th className="px-4 py-2 w-10">#</th>
              <th className="px-4 py-2">도면번호</th>
              <th className="px-4 py-2">품명</th>
              <th className="px-4 py-2">재질</th>
              <th className="px-4 py-2">매칭 파일</th>
              <th className="px-4 py-2 w-16 text-center">상태</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {displayItems.map((item, idx) => (
              <tr key={item.item_no} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <td className="px-4 py-2 text-gray-400 dark:text-gray-500">{idx + 1}</td>
                <td className="px-4 py-2 font-mono text-gray-900 dark:text-white">
                  {item.drawing_number}
                </td>
                <td className="px-4 py-2 text-gray-700 dark:text-gray-300 truncate max-w-[200px]">
                  {item.description}
                </td>
                <td className="px-4 py-2 text-gray-500 dark:text-gray-400">{item.material || '-'}</td>
                <td className="px-4 py-2 text-gray-700 dark:text-gray-300 truncate max-w-[250px]">
                  {item.matched_file || '-'}
                </td>
                <td className="px-4 py-2 text-center">
                  {item.matched_file ? (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                      매칭
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
                      미매칭
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {displayItems.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400 dark:text-gray-500">
                  견적 대상 항목이 없습니다.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
