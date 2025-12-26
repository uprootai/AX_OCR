/**
 * Symbol Verification Section
 * 심볼 검증 및 수정 섹션 컴포넌트
 */

import { useState } from 'react';
import { Loader2, X, CheckCircle } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import { FEATURE_TOOLTIPS } from '../../../components/tooltipContent';
import { DrawingCanvas } from '../../../components/DrawingCanvas';
import { DetectionRow } from '../components/DetectionRow';
import type { VerificationStatus, Detection } from '../../../types';

interface ClassExample {
  class_name: string;
  image_base64: string;
}

interface GTMatch {
  detection_idx: number;
  gt_bbox: { x1: number; y1: number; x2: number; y2: number };
  gt_class: string;
  iou: number;
  class_match: boolean;
}

interface GTCompareResult {
  tp_matches: GTMatch[];
}

interface SymbolVerificationSectionProps {
  // Data
  detections: Detection[];
  paginatedDetections: Detection[];
  imageData: string | null;
  imageSize: { width: number; height: number } | null;
  availableClasses: string[];
  classExamples: ClassExample[];
  gtCompareResult: GTCompareResult | null;
  // Pagination
  currentPage: number;
  totalPages: number;
  itemsPerPage: number;
  setCurrentPage: (page: number) => void;
  // Stats
  stats: {
    total: number;
    approved: number;
    rejected: number;
    pending: number;
    manual: number;
  };
  // State
  showGTImages: boolean;
  setShowGTImages: (show: boolean) => void;
  showRefImages: boolean;
  setShowRefImages: (show: boolean) => void;
  showManualLabel: boolean;
  setShowManualLabel: (show: boolean) => void;
  manualLabel: { class_name: string };
  setManualLabel: (label: { class_name: string }) => void;
  verificationFinalized: boolean;
  setVerificationFinalized: (finalized: boolean) => void;
  // Handlers
  onApproveAll: () => void;
  onRejectAll: () => void;
  onVerify: (id: string, status: VerificationStatus, modifiedClassName?: string) => void;
  onDelete: (id: string) => void;
  onAddManualDetection: (box: { x1: number; y1: number; x2: number; y2: number }) => Promise<void>;
  // Loading
  isLoading: boolean;
}

export function SymbolVerificationSection({
  detections,
  paginatedDetections,
  imageData,
  imageSize,
  availableClasses,
  classExamples,
  gtCompareResult,
  currentPage,
  totalPages,
  itemsPerPage,
  setCurrentPage,
  stats,
  showGTImages,
  setShowGTImages,
  showRefImages,
  setShowRefImages,
  showManualLabel,
  setShowManualLabel,
  manualLabel,
  setManualLabel,
  verificationFinalized,
  setVerificationFinalized,
  onApproveAll,
  onRejectAll,
  onVerify,
  onDelete,
  onAddManualDetection,
  isLoading,
}: SymbolVerificationSectionProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingClassName, setEditingClassName] = useState<string>('');

  const getGtBboxForDetection = (detectionIndex: number) => {
    if (!gtCompareResult) return null;
    const match = gtCompareResult.tp_matches.find(m => m.detection_idx === detectionIndex);
    return match?.gt_bbox || null;
  };

  const getGtMatchForDetection = (detectionIndex: number) => {
    if (!gtCompareResult) return null;
    return gtCompareResult.tp_matches.find(m => m.detection_idx === detectionIndex) || null;
  };

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-1">
          ✅ 심볼 검증 및 수정
          <InfoTooltip content={FEATURE_TOOLTIPS.symbolVerification.description} position="right" />
        </h2>
        <div className="flex items-center space-x-3">
          <div className="flex items-center">
            <button
              onClick={onApproveAll}
              disabled={isLoading}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>처리 중...</span>
                </>
              ) : (
                <span>전체 승인</span>
              )}
            </button>
            <InfoTooltip content={FEATURE_TOOLTIPS.approveAll.description} position="bottom" iconSize={12} />
          </div>
          <div className="flex items-center">
            <button
              onClick={onRejectAll}
              disabled={isLoading}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>처리 중...</span>
                </>
              ) : (
                <span>전체 거부</span>
              )}
            </button>
            <InfoTooltip content={FEATURE_TOOLTIPS.rejectAll.description} position="bottom" iconSize={12} />
          </div>
        </div>
      </div>

      {/* Options */}
      <div className="flex items-center space-x-6 mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showGTImages}
            onChange={(e) => setShowGTImages(e.target.checked)}
            className="rounded"
          />
          <span className="text-sm">🏷️ GT 이미지 표시</span>
          <InfoTooltip content={FEATURE_TOOLTIPS.showGT.description} position="bottom" iconSize={12} />
        </label>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showRefImages}
            onChange={(e) => setShowRefImages(e.target.checked)}
            className="rounded"
          />
          <span className="text-sm">📚 참조 이미지 표시</span>
          <InfoTooltip content={FEATURE_TOOLTIPS.showReference.description} position="bottom" iconSize={12} />
        </label>
        <div className="flex items-center">
          <button
            onClick={() => setShowManualLabel(!showManualLabel)}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            ✏️ 수작업 라벨 추가
          </button>
          <InfoTooltip content={FEATURE_TOOLTIPS.manualLabel.description} position="bottom" iconSize={12} />
        </div>
      </div>

      {/* Manual Label Section */}
      {showManualLabel && imageData && imageSize && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <h3 className="font-semibold mb-3">✏️ 수작업 라벨 추가</h3>
          <div className="mb-4">
            <label className="text-sm text-gray-600 dark:text-gray-400 mb-1 block">1. 클래스 선택</label>
            <select
              value={manualLabel.class_name}
              onChange={(e) => setManualLabel({ class_name: e.target.value })}
              className="w-full max-w-xs px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
            >
              <option value="">클래스 선택...</option>
              {availableClasses.map(cls => (
                <option key={cls} value={cls}>{cls}</option>
              ))}
            </select>
          </div>
          <div className="mb-4">
            <label className="text-sm text-gray-600 dark:text-gray-400 mb-1 block">2. 바운딩 박스 그리기</label>
            <DrawingCanvas
              imageData={imageData}
              imageSize={imageSize}
              selectedClass={manualLabel.class_name}
              maxWidth="100%"
              existingBoxes={
                detections
                  .filter(d =>
                    d.verification_status === 'approved' ||
                    d.verification_status === 'modified' ||
                    d.verification_status === 'manual'
                  )
                  .map(d => ({
                    bbox: d.bbox,
                    label: d.modified_class_name || d.class_name,
                    color: d.verification_status === 'manual' ? '#a855f7' :
                      d.verification_status === 'modified' ? '#f97316' : '#22c55e'
                  }))
              }
              onBoxDrawn={async (box) => {
                if (!manualLabel.class_name) {
                  alert('클래스를 먼저 선택해주세요!');
                  return;
                }
                await onAddManualDetection(box);
              }}
            />
          </div>

          {/* 추가된 수작업 라벨 목록 */}
          {detections.filter(d => d.verification_status === 'manual').length > 0 && (
            <div className="mt-4 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
              <h4 className="font-semibold text-purple-700 dark:text-purple-300 mb-2">
                🎨 수작업 라벨 목록 ({detections.filter(d => d.verification_status === 'manual').length}개)
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {detections
                  .filter(d => d.verification_status === 'manual')
                  .map((d, idx) => (
                    <div
                      key={d.id}
                      className="flex items-center justify-between p-2 bg-white dark:bg-gray-800 rounded border border-purple-100 dark:border-purple-700"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="w-6 h-6 flex items-center justify-center bg-purple-500 text-white text-xs rounded-full">
                          {idx + 1}
                        </span>
                        <div>
                          <span className="font-medium text-gray-900 dark:text-white">
                            {d.class_name}
                          </span>
                          <span className="ml-2 text-xs text-gray-500">
                            ({Math.round(d.bbox.x1)}, {Math.round(d.bbox.y1)}) - ({Math.round(d.bbox.x2)}, {Math.round(d.bbox.y2)})
                          </span>
                          <span className="ml-2 text-xs text-gray-400">
                            {Math.round(d.bbox.x2 - d.bbox.x1)}×{Math.round(d.bbox.y2 - d.bbox.y1)}px
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          if (confirm(`"${d.class_name}" 수작업 라벨을 삭제하시겠습니까?`)) {
                            onDelete(d.id);
                          }
                        }}
                        className="p-1 text-red-500 hover:bg-red-100 dark:hover:bg-red-900/30 rounded"
                        title="삭제"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">
          {currentPage} / {totalPages} 페이지 (전체 {detections.length}개 중 {(currentPage - 1) * itemsPerPage + 1}-{Math.min(currentPage * itemsPerPage, detections.length)}번째)
        </p>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentPage(1)}
            disabled={currentPage === 1}
            className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
          >
            처음
          </button>
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
          >
            이전
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
            <button
              key={page}
              onClick={() => setCurrentPage(page)}
              className={`px-3 py-1 text-sm rounded ${page === currentPage
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700'
                }`}
            >
              {page}
            </button>
          ))}
          <button
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
          >
            다음
          </button>
          <button
            onClick={() => setCurrentPage(totalPages)}
            disabled={currentPage === totalPages}
            className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
          >
            마지막
          </button>
        </div>
      </div>

      {/* Detection List */}
      <div className="space-y-3">
        <h3 className="font-semibold text-gray-900 dark:text-white">검출 결과</h3>
        {paginatedDetections.map((detection, index) => {
          const globalIndex = (currentPage - 1) * itemsPerPage + index;
          return (
            <DetectionRow
              key={detection.id}
              detection={detection}
              index={index}
              globalIndex={globalIndex}
              imageData={imageData}
              imageSize={imageSize}
              availableClasses={availableClasses}
              classExamples={classExamples}
              gtMatch={getGtMatchForDetection(globalIndex)}
              gtBbox={getGtBboxForDetection(globalIndex)}
              showGTImages={showGTImages}
              showRefImages={showRefImages}
              editingId={editingId}
              editingClassName={editingClassName}
              setEditingId={setEditingId}
              setEditingClassName={setEditingClassName}
              onVerify={onVerify}
              onDelete={onDelete}
            />
          );
        })}
      </div>

      {/* 검증 완료 버튼 */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <p>현재 검증 현황:
              승인 <span className="font-bold text-green-600">{stats.approved}</span>개 /
              거부 <span className="font-bold text-red-600">{stats.rejected}</span>개 /
              수작업 <span className="font-bold text-purple-600">{stats.manual}</span>개 /
              대기 <span className="font-bold text-gray-500">{stats.pending}</span>개
            </p>
            <p className="text-xs text-gray-500 mt-1">
              BOM에 포함될 항목: <span className="font-bold text-primary-600">{stats.approved + stats.manual}</span>개
              (승인 + 수작업)
            </p>
          </div>
          <div className="flex items-center">
            <button
              onClick={() => {
                const finalCount = stats.approved + stats.manual;
                if (finalCount === 0) {
                  alert('BOM에 포함할 항목이 없습니다.\n검출 결과를 승인하거나 수작업 라벨을 추가해주세요.');
                  return;
                }
                setVerificationFinalized(true);
              }}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-semibold transition-all ${verificationFinalized
                ? 'bg-green-100 text-green-700 border-2 border-green-500'
                : 'bg-green-600 text-white hover:bg-green-700'
                }`}
            >
              {verificationFinalized ? (
                <>
                  <CheckCircle className="w-5 h-5" />
                  <span>검증 완료됨</span>
                </>
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" />
                  <span>검증 완료</span>
                </>
              )}
            </button>
            <InfoTooltip content={FEATURE_TOOLTIPS.verificationComplete.description} position="left" iconSize={14} />
          </div>
        </div>
        {verificationFinalized && (
          <p className="mt-2 text-sm text-green-600 dark:text-green-400">
            ✓ 검증이 완료되었습니다. 아래에서 최종 결과를 확인하고 BOM을 생성하세요.
          </p>
        )}
      </div>
    </section>
  );
}
