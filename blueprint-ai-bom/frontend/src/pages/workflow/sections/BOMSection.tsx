/**
 * BOM Section
 * BOM 생성 및 내보내기 섹션 컴포넌트
 */

import { FileSpreadsheet, Download, Loader2, DollarSign } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import { FEATURE_TOOLTIPS } from '../../../components/tooltipContent';
import type { Detection, ExportFormat } from '../../../types';

interface BOMItem {
  class_name: string;
  quantity: number;
  dimensions?: string[];
  unit_price?: number;
  total_price?: number;
}

interface BOMData {
  items: BOMItem[];
  summary: {
    total_quantity: number;
    total?: number;
  };
}

interface BOMSectionProps {
  sessionId: string;
  detections: Detection[];
  bomData: BOMData | null;
  stats: {
    approved: number;
    manual: number;
  };
  dimensionStats?: { approved: number; modified?: number; manual?: number } | null;
  exportFormat: ExportFormat;
  setExportFormat: (format: ExportFormat) => void;
  onGenerateBOM: () => void;
  isLoading: boolean;
  apiBaseUrl: string;
  hasCustomPricing?: boolean;
  // BOM ↔ 도면 하이라이트 연동
  selectedClassName?: string | null;
  onClassSelect?: (className: string | null) => void;
}

export function BOMSection({
  sessionId,
  detections,
  bomData,
  stats,
  dimensionStats,
  exportFormat,
  setExportFormat,
  onGenerateBOM,
  isLoading,
  apiBaseUrl,
  hasCustomPricing = false,
  selectedClassName,
  onClassSelect,
}: BOMSectionProps) {
  const approvedDetections = detections.filter(d =>
    d.verification_status === 'approved' ||
    d.verification_status === 'modified' ||
    d.verification_status === 'manual'
  );

  // 치수 승인 수 계산
  const dimApproved = (dimensionStats?.approved || 0) + (dimensionStats?.modified || 0) + (dimensionStats?.manual || 0);
  const totalApproved = stats.approved + stats.manual + dimApproved;

  // 클래스별로 그룹화
  const grouped = approvedDetections.reduce((acc, d) => {
    const className = d.modified_class_name || d.class_name;
    if (!acc[className]) {
      acc[className] = { count: 0, items: [] as Detection[] };
    }
    acc[className].count++;
    acc[className].items.push(d);
    return acc;
  }, {} as Record<string, { count: number; items: Detection[] }>);

  const sortedClasses = Object.entries(grouped).sort((a, b) => b[1].count - a[1].count);

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          BOM 생성 및 내보내기
          <InfoTooltip content={FEATURE_TOOLTIPS.bomGeneration.description} position="right" />
          {hasCustomPricing && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded-full">
              <DollarSign className="w-3 h-3" />
              커스텀 단가
            </span>
          )}
        </h2>
        <div className="flex items-center space-x-3">
          <div className="flex items-center">
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
            >
              <option value="excel">Excel (.xlsx)</option>
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
            <InfoTooltip content={FEATURE_TOOLTIPS.exportFormat.description} position="bottom" iconSize={12} />
          </div>
          <div className="flex items-center">
            <button
              onClick={onGenerateBOM}
              disabled={isLoading || totalApproved === 0}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <FileSpreadsheet className="w-5 h-5" />
              )}
              <span>BOM 생성</span>
            </button>
            <InfoTooltip content={FEATURE_TOOLTIPS.generateBOM.description} position="bottom" iconSize={12} />
          </div>
        </div>
      </div>

      {totalApproved === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <FileSpreadsheet className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>승인된 검출 또는 치수가 없습니다.</p>
          <p className="text-sm">위에서 검출 결과 또는 치수를 승인하세요.</p>
        </div>
      ) : bomData ? (
        <div>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold">{bomData.items.length}</p>
              <p className="text-sm text-gray-500">품목 수</p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold">{bomData.summary.total_quantity}</p>
              <p className="text-sm text-gray-500">총 수량</p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold">{bomData.summary.total?.toLocaleString() || '-'}</p>
              <p className="text-sm text-gray-500">예상 비용 (원)</p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-green-600">✓</p>
              <p className="text-sm text-gray-500">생성 완료</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-4 py-2 text-left">#</th>
                  <th className="px-4 py-2 text-left">품목명</th>
                  <th className="px-4 py-2 text-left">치수 (규격)</th>
                  <th className="px-4 py-2 text-center">수량</th>
                  <th className="px-4 py-2 text-right">단가</th>
                  <th className="px-4 py-2 text-right">금액</th>
                </tr>
              </thead>
              <tbody>
                {bomData.items.map((item, idx) => {
                  const isSelected = selectedClassName === item.class_name;
                  return (
                  <tr
                    key={idx}
                    onClick={() => onClassSelect?.(isSelected ? null : item.class_name)}
                    className={`border-b border-gray-200 dark:border-gray-700 cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-blue-50 dark:bg-blue-900/30 ring-1 ring-blue-400'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                    }`}
                  >
                    <td className="px-4 py-2">{idx + 1}</td>
                    <td className={`px-4 py-2 font-medium ${isSelected ? 'text-blue-700 dark:text-blue-300' : ''}`}>{item.class_name}</td>
                    <td className="px-4 py-2">
                      {item.dimensions && item.dimensions.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {item.dimensions.map((dim, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-600 rounded text-xs whitespace-nowrap">
                              {dim}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-xs">-</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-center">{item.quantity}</td>
                    <td className="px-4 py-2 text-right">{item.unit_price?.toLocaleString() || '-'}</td>
                    <td className="px-4 py-2 text-right">{item.total_price?.toLocaleString() || '-'}</td>
                  </tr>
                  );
                })}
              </tbody>
              <tfoot className="bg-gray-50 dark:bg-gray-700 font-bold">
                <tr>
                  <td colSpan={3} className="px-4 py-2">합계</td>
                  <td className="px-4 py-2 text-center">{bomData.summary.total_quantity}</td>
                  <td className="px-4 py-2"></td>
                  <td className="px-4 py-2 text-right">{bomData.summary.total?.toLocaleString() || '-'}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div className="mt-4 flex justify-end">
            <a
              href={`${apiBaseUrl}/bom/${sessionId}/download?format=${exportFormat}`}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              download
            >
              <Download className="w-4 h-4" />
              <span>다운로드</span>
            </a>
          </div>
        </div>
      ) : (
        <div>
          {/* BOM 생성 전 미리보기 */}
          <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              💡 아래 승인된 검출 결과를 기반으로 BOM이 생성됩니다. "BOM 생성" 버튼을 클릭하세요.
            </p>
          </div>

          {/* 미리보기 테이블 */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-4 py-2 text-left">#</th>
                  <th className="px-4 py-2 text-left">품목명 (클래스)</th>
                  <th className="px-4 py-2 text-center">수량</th>
                  <th className="px-4 py-2 text-center">상태</th>
                  <th className="px-4 py-2 text-left">검출 ID</th>
                </tr>
              </thead>
              <tbody>
                {sortedClasses.map(([className, data], idx) => {
                  const isSelected = selectedClassName === className;
                  return (
                  <tr
                    key={className}
                    onClick={() => onClassSelect?.(isSelected ? null : className)}
                    className={`border-b border-gray-200 dark:border-gray-700 cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-blue-50 dark:bg-blue-900/30 ring-1 ring-blue-400'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                    }`}
                  >
                    <td className="px-4 py-2">{idx + 1}</td>
                    <td className={`px-4 py-2 font-medium ${isSelected ? 'text-blue-700 dark:text-blue-300' : ''}`}>{className}</td>
                    <td className="px-4 py-2 text-center font-bold text-primary-600">{data.count}</td>
                    <td className="px-4 py-2 text-center">
                      <div className="flex justify-center space-x-1">
                        {data.items.some(i => i.verification_status === 'approved') && (
                          <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">승인</span>
                        )}
                        {data.items.some(i => i.verification_status === 'modified') && (
                          <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded">수정</span>
                        )}
                        {data.items.some(i => i.verification_status === 'manual') && (
                          <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">수작업</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-2 text-xs text-gray-500">
                      {data.items.map(i => i.id.slice(0, 6)).join(', ')}
                    </td>
                  </tr>
                  );
                })}
              </tbody>
              <tfoot className="bg-gray-50 dark:bg-gray-700 font-bold">
                <tr>
                  <td colSpan={2} className="px-4 py-2">합계</td>
                  <td className="px-4 py-2 text-center">{approvedDetections.length}</td>
                  <td colSpan={2} className="px-4 py-2"></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
