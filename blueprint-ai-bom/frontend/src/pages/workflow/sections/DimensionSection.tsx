/**
 * Dimension Section
 * 치수 OCR 결과 섹션 컴포넌트
 */

import { useState } from 'react';
import { Loader2, PencilLine } from 'lucide-react';
import { DimensionList } from '../../../components/DimensionList';
import { DimensionOverlay } from '../../../components/DimensionOverlay';
import { DrawingCanvas } from '../../../components/DrawingCanvas';
import type { Dimension, DimensionStats } from '../types/workflow';

interface DimensionSectionProps {
  sessionId: string;
  dimensions: Dimension[];
  dimensionStats: DimensionStats | null;
  selectedDimensionId: string | null;
  setSelectedDimensionId: (id: string | null) => void;
  imageData: string | null;
  imageSize: { width: number; height: number } | null;
  isRunningAnalysis: boolean;
  onVerify: (id: string, status: 'approved' | 'rejected') => void;
  onEdit: (id: string, newValue: string) => void;
  onDelete: (id: string) => void;
  onBulkApprove: (ids: string[]) => void;
  onAutoApprove: () => void;
  onReset: () => void;
  isAutoApproving: boolean;
  onAddManualDimension: (value: string, box: { x1: number; y1: number; x2: number; y2: number }) => Promise<void>;
  onImagePopup?: () => void;
}

export function DimensionSection({
  sessionId,
  dimensions,
  dimensionStats,
  selectedDimensionId,
  setSelectedDimensionId,
  imageData,
  imageSize,
  isRunningAnalysis,
  onVerify,
  onEdit,
  onDelete,
  onBulkApprove,
  onAutoApprove,
  onReset,
  isAutoApproving,
  onAddManualDimension,
  onImagePopup,
}: DimensionSectionProps) {
  const [showManualAdd, setShowManualAdd] = useState(false);
  const [manualValue, setManualValue] = useState('');

  // sessionId used for manual dimension add (passed via onAddManualDimension)
  void sessionId;

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          📏 치수 OCR 결과
          <span className="text-base font-normal text-gray-500 ml-2">
            ({dimensions.length}개 치수)
          </span>
          {dimensionStats && (
            <span className="text-sm text-gray-500 ml-2">
              ({dimensionStats.approved + dimensionStats.modified + dimensionStats.manual}/{dimensions.length} 승인됨)
            </span>
          )}
        </h2>
        <div className="flex items-center gap-2">
          {imageData && imageSize && (
            <button
              onClick={() => setShowManualAdd(!showManualAdd)}
              className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg transition-colors ${
                showManualAdd
                  ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              <PencilLine className="w-4 h-4" />
              수작업 추가
            </button>
          )}
          {isRunningAnalysis && (
            <div className="flex items-center text-primary-600">
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              <span className="text-sm">분석 중...</span>
            </div>
          )}
        </div>
      </div>

      {/* 수작업 치수 추가 */}
      {showManualAdd && imageData && imageSize && (
        <div className="mb-4 p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700 rounded-lg">
          <h3 className="text-sm font-semibold text-purple-800 dark:text-purple-300 mb-3">
            수작업 치수 추가
          </h3>
          <div className="mb-3">
            <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">
              1. 치수 값 입력
            </label>
            <input
              type="text"
              value={manualValue}
              onChange={(e) => setManualValue(e.target.value)}
              placeholder="예: Ø50, R1.6, 100±0.1"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
            2. 도면에서 바운딩 박스 그리기
          </p>
          <DrawingCanvas
            imageData={imageData}
            imageSize={imageSize}
            selectedClass={manualValue || undefined}
            maxWidth="100%"
            existingBoxes={
              dimensions
                .filter(d =>
                  d.verification_status === 'approved' ||
                  d.verification_status === 'modified' ||
                  d.verification_status === 'manual'
                )
                .map(d => ({
                  bbox: d.bbox,
                  label: d.modified_value || d.value,
                  color: d.verification_status === 'manual' ? '#a855f7' :
                    d.verification_status === 'modified' ? '#f97316' : '#22c55e'
                }))
            }
            onBoxDrawn={async (box) => {
              if (!manualValue.trim()) {
                alert('치수 값을 먼저 입력해주세요!');
                return;
              }
              await onAddManualDimension(manualValue.trim(), box);
              setManualValue('');
              setShowManualAdd(false);
            }}
          />
        </div>
      )}

      {/* 도면 오버레이 */}
      {imageData && imageSize && dimensions.length > 0 && (
        <DimensionOverlay
          imageData={imageData}
          imageSize={imageSize}
          dimensions={dimensions}
          selectedId={selectedDimensionId}
          onSelect={(id) => setSelectedDimensionId(id)}
          onImagePopup={onImagePopup}
        />
      )}

      {/* 검증 진행률 바 */}
      {dimensionStats && (
        <div className="mx-4 mb-2">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>검증 진행률</span>
            <span>{Math.round(((dimensionStats.approved + dimensionStats.modified + dimensionStats.manual) / Math.max(dimensions.length, 1)) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div
              className="bg-green-500 h-1.5 rounded-full transition-all"
              style={{ width: `${Math.round(((dimensionStats.approved + dimensionStats.modified + dimensionStats.manual) / Math.max(dimensions.length, 1)) * 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* 통합 치수 리스트 */}
      <DimensionList
        dimensions={dimensions}
        stats={dimensionStats || undefined}
        onVerify={onVerify}
        onEdit={onEdit}
        onDelete={onDelete}
        onBulkApprove={onBulkApprove}
        onAutoApprove={onAutoApprove}
        onReset={onReset}
        isAutoApproving={isAutoApproving}
        onHover={(id) => setSelectedDimensionId(id)}
        selectedId={selectedDimensionId}
        imageData={imageData}
        imageSize={imageSize}
      />

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
