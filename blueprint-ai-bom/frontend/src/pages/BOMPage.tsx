/**
 * BOM Page - BOM 결과 및 내보내기
 */

import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { FileSpreadsheet, Download, Loader2, RefreshCw } from 'lucide-react';
import { useSessionStore } from '../store/sessionStore';
import { bomApi } from '../lib/api';
import type { ExportFormat } from '../types';

export function BOMPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get('session');

  const {
    currentSession,
    bomData,
    isLoading,
    error,
    loadSession,
    generateBOM,
    clearError,
  } = useSessionStore();

  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<ExportFormat>('excel');

  useEffect(() => {
    if (sessionId && !currentSession) {
      loadSession(sessionId);
    }
  }, [sessionId, currentSession, loadSession]);

  const handleGenerateBOM = async () => {
    await generateBOM();
  };

  const handleExport = async () => {
    if (!sessionId) return;

    setExporting(true);
    try {
      const url = bomApi.getDownloadUrl(sessionId, exportFormat);
      window.open(url, '_blank');
    } finally {
      setExporting(false);
    }
  };

  if (!sessionId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">세션 ID가 필요합니다.</p>
        <button onClick={() => navigate('/')} className="mt-4 text-primary-600 hover:text-primary-700">
          홈으로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
          <span>{error}</span>
          <button onClick={clearError} className="text-red-500 hover:text-red-700">×</button>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">부품 명세서 (BOM)</h1>
          {currentSession && (
            <p className="text-gray-500 mt-1">{currentSession.filename}</p>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleGenerateBOM}
            disabled={isLoading}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>재생성</span>
          </button>
          {bomData && (
            <div className="flex items-center space-x-2">
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
                className="border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="excel">Excel (.xlsx)</option>
                <option value="csv">CSV (.csv)</option>
                <option value="json">JSON (.json)</option>
                <option value="pdf">PDF (.pdf)</option>
              </select>
              <button
                onClick={handleExport}
                disabled={exporting}
                className="flex items-center space-x-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {exporting ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Download className="w-5 h-5" />
                )}
                <span>내보내기</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* BOM Content */}
      {!bomData ? (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
          <FileSpreadsheet className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-lg text-gray-500 mb-6">BOM이 아직 생성되지 않았습니다.</p>
          <button
            onClick={handleGenerateBOM}
            disabled={isLoading}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {isLoading ? 'BOM 생성 중...' : 'BOM 생성'}
          </button>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-5 gap-4">
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-sm text-gray-500">총 품목</p>
              <p className="text-2xl font-bold text-gray-900">{bomData.summary.total_items}</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-sm text-gray-500">총 수량</p>
              <p className="text-2xl font-bold text-gray-900">{bomData.summary.total_quantity}</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-sm text-gray-500">소계</p>
              <p className="text-2xl font-bold text-gray-900">
                ₩{bomData.summary.subtotal.toLocaleString()}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-sm text-gray-500">부가세 (10%)</p>
              <p className="text-2xl font-bold text-gray-900">
                ₩{bomData.summary.vat.toLocaleString()}
              </p>
            </div>
            <div className="bg-primary-50 rounded-lg shadow-sm border border-primary-200 p-4">
              <p className="text-sm text-primary-600">합계</p>
              <p className="text-2xl font-bold text-primary-700">
                ₩{bomData.summary.total.toLocaleString()}
              </p>
            </div>
          </div>

          {/* BOM Table */}
          <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      No.
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      부품명
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      모델명
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      수량
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      단가
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      합계
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      공급업체
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      리드타임
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      신뢰도
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {bomData.items.map((item) => (
                    <tr key={item.item_no} className="hover:bg-gray-50">
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.item_no}
                      </td>
                      <td className="px-4 py-4 text-sm font-medium text-gray-900 max-w-[200px] truncate" title={item.class_name}>
                        {item.class_name}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.model_name || '-'}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                        {item.quantity}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                        ₩{item.unit_price.toLocaleString()}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900 text-right">
                        ₩{item.total_price.toLocaleString()}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">
                        {item.supplier || '-'}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500 text-center">
                        <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded">
                          {item.lead_time || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                        <span
                          className={`px-2 py-1 rounded-full text-xs ${
                            item.avg_confidence >= 0.9
                              ? 'bg-green-100 text-green-800'
                              : item.avg_confidence >= 0.7
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {(item.avg_confidence * 100).toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Meta Info */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-500">
            <p>생성일: {new Date(bomData.created_at).toLocaleString('ko-KR')}</p>
            <p>검출 수: {bomData.detection_count}개 / 승인 수: {bomData.approved_count}개</p>
            {bomData.model_id && <p>모델: {bomData.model_id}</p>}
          </div>
        </>
      )}
    </div>
  );
}
