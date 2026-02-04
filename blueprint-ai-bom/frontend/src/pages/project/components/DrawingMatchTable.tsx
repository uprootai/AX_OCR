/**
 * DrawingMatchTable - 도면 매칭 테이블
 * 도면 폴더 경로 입력, 매칭 실행, 결과 테이블 표시
 */

import { useState } from 'react';
import { Link2, Loader2, Search, AlertCircle } from 'lucide-react';
import { projectApi, type BOMItem, type DrawingMatchResult } from '../../../lib/api';

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
    <div className="bg-white rounded-xl border overflow-hidden">
      {/* 헤더 */}
      <div className="p-4 border-b flex items-center gap-2">
        <Link2 className="w-5 h-5 text-gray-400" />
        <h3 className="font-semibold text-gray-900">도면 매칭</h3>
      </div>

      {/* 폴더 경로 입력 */}
      <div className="p-4 border-b bg-gray-50">
        <label className="block text-sm text-gray-600 mb-2">도면 폴더 경로</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            placeholder="/app/data/dsebearing/PJT/04_부품도면"
            className="flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <button
            onClick={handleMatch}
            disabled={isMatching || !folderPath.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 flex items-center gap-2"
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
          <div className="mt-2 flex items-center gap-2 text-sm text-red-600">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {/* 결과 요약 */}
      {result && (
        <div className="p-4 border-b">
          <div className="flex items-center gap-4 mb-2">
            <span className="text-sm text-gray-700">
              매칭 결과: <span className="font-bold">{matchedCount}/{totalCount}</span>{' '}
              ({matchPercent}%)
            </span>
            {unmatchedCount > 0 && (
              <span className="text-sm text-red-600">
                미매칭 {unmatchedCount}개
              </span>
            )}
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 transition-all"
              style={{ width: `${matchPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* 테이블 */}
      <div className="max-h-[400px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 sticky top-0">
            <tr className="text-left text-gray-500">
              <th className="px-4 py-2 w-10">#</th>
              <th className="px-4 py-2">도면번호</th>
              <th className="px-4 py-2">품명</th>
              <th className="px-4 py-2">재질</th>
              <th className="px-4 py-2">매칭 파일</th>
              <th className="px-4 py-2 w-16 text-center">상태</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {displayItems.map((item, idx) => (
              <tr key={item.item_no} className="hover:bg-gray-50">
                <td className="px-4 py-2 text-gray-400">{idx + 1}</td>
                <td className="px-4 py-2 font-mono text-gray-900">
                  {item.drawing_number}
                </td>
                <td className="px-4 py-2 text-gray-700 truncate max-w-[200px]">
                  {item.description}
                </td>
                <td className="px-4 py-2 text-gray-500">{item.material || '-'}</td>
                <td className="px-4 py-2 text-gray-700 truncate max-w-[250px]">
                  {item.matched_file || '-'}
                </td>
                <td className="px-4 py-2 text-center">
                  {item.matched_file ? (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
                      매칭
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                      미매칭
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {displayItems.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
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
