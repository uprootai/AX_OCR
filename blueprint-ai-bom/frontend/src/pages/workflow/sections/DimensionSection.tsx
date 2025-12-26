/**
 * Dimension Section
 * 치수 OCR 결과 섹션 컴포넌트
 */

import { Loader2 } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../../../lib/constants';
import logger from '../../../lib/logger';
import { DimensionList } from '../../../components/DimensionList';
import { VerificationQueue } from '../../../components/VerificationQueue';
import type { Dimension, DimensionStats } from '../types/workflow';

interface DimensionSectionProps {
  sessionId: string;
  dimensions: Dimension[];
  dimensionStats: DimensionStats | null;
  selectedDimensionId: string | null;
  setSelectedDimensionId: (id: string | null) => void;
  setDimensions: (dimensions: Dimension[]) => void;
  setDimensionStats: (stats: DimensionStats | null) => void;
  showVerificationQueue: boolean;
  setShowVerificationQueue: (show: boolean) => void;
  imageData: string | null;
  imageSize: { width: number; height: number } | null;
  isRunningAnalysis: boolean;
  onVerify: (id: string, status: 'approved' | 'rejected') => void;
  onEdit: (id: string, newValue: string) => void;
  onDelete: (id: string) => void;
  onBulkApprove: (ids: string[]) => void;
}

export function DimensionSection({
  sessionId,
  dimensions,
  dimensionStats,
  selectedDimensionId,
  setSelectedDimensionId,
  setDimensions,
  setDimensionStats,
  showVerificationQueue,
  setShowVerificationQueue,
  imageData,
  imageSize,
  isRunningAnalysis,
  onVerify,
  onEdit,
  onDelete,
  onBulkApprove,
}: DimensionSectionProps) {
  const refreshDimensions = async () => {
    const { data } = await axios.get(`${API_BASE_URL}/analysis/dimensions/${sessionId}`);
    setDimensions(data.dimensions || []);
    setDimensionStats(data.stats || null);
  };

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          📏 치수 OCR 결과
          <span className="text-base font-normal text-gray-500 ml-2">
            ({dimensions.length}개 치수)
          </span>
        </h2>
        {isRunningAnalysis && (
          <div className="flex items-center text-primary-600">
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
            <span className="text-sm">분석 중...</span>
          </div>
        )}
      </div>

      {/* 뷰 모드 토글 */}
      <div className="flex gap-2 mb-3">
        <button
          onClick={() => setShowVerificationQueue(false)}
          className={`flex-1 px-3 py-2 text-sm rounded-lg transition-colors ${
            !showVerificationQueue
              ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
          }`}
        >
          치수 목록
        </button>
        <button
          onClick={() => setShowVerificationQueue(true)}
          className={`flex-1 px-3 py-2 text-sm rounded-lg transition-colors ${
            showVerificationQueue
              ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
          }`}
        >
          Active Learning 큐
        </button>
      </div>

      {/* Dimension List 또는 Verification Queue */}
      {!showVerificationQueue ? (
        <DimensionList
          dimensions={dimensions}
          stats={dimensionStats || undefined}
          onVerify={onVerify}
          onEdit={onEdit}
          onDelete={onDelete}
          onBulkApprove={onBulkApprove}
          onHover={(id) => setSelectedDimensionId(id)}
          selectedId={selectedDimensionId}
          imageData={imageData}
          imageSize={imageSize}
        />
      ) : (
        <VerificationQueue
          sessionId={sessionId}
          itemType="dimension"
          onVerify={(itemId, action) => {
            logger.log(`Verified ${itemId}: ${action}`);
            refreshDimensions();
          }}
          onAutoApprove={() => {
            refreshDimensions();
          }}
          onItemSelect={(itemId) => setSelectedDimensionId(itemId)}
          apiBaseUrl={API_BASE_URL}
        />
      )}

      {/* 치수 요약 */}
      {dimensionStats && (
        <div className="mt-4 grid grid-cols-5 gap-2 text-sm">
          <div className="bg-gray-50 dark:bg-gray-700 rounded p-2 text-center">
            <p className="text-lg font-bold text-gray-900 dark:text-white">{dimensions.length}</p>
            <p className="text-xs text-gray-500">총 치수</p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded p-2 text-center">
            <p className="text-lg font-bold text-yellow-600">{dimensionStats.pending}</p>
            <p className="text-xs text-gray-500">대기</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded p-2 text-center">
            <p className="text-lg font-bold text-green-600">{dimensionStats.approved}</p>
            <p className="text-xs text-gray-500">승인</p>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 rounded p-2 text-center">
            <p className="text-lg font-bold text-red-600">{dimensionStats.rejected}</p>
            <p className="text-xs text-gray-500">거부</p>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded p-2 text-center">
            <p className="text-lg font-bold text-blue-600">{dimensionStats.modified + dimensionStats.manual}</p>
            <p className="text-xs text-gray-500">수정</p>
          </div>
        </div>
      )}
    </section>
  );
}
