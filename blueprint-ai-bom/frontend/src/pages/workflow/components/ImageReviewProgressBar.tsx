/**
 * ImageReviewProgressBar - 이미지 검토 진행률 표시
 * 상태별 색상 막대와 통계 표시
 */

import {
  CheckCircle,
  XCircle,
  Edit3,
  Clock,
  Eye,
  Tag,
  Download,
} from 'lucide-react';
import type { SessionImageProgress } from '../../../types';

interface ImageReviewProgressBarProps {
  progress: SessionImageProgress;
  onExport?: () => void;
  className?: string;
}

export function ImageReviewProgressBar({
  progress,
  onExport,
  className = '',
}: ImageReviewProgressBarProps) {
  const {
    total_images,
    pending_count,
    processed_count,
    approved_count,
    rejected_count,
    modified_count,
    manual_labeled_count,
    progress_percent,
    export_ready,
  } = progress;

  // 완료된 항목 (approved + modified + manual_labeled)
  const completedCount = approved_count + modified_count + manual_labeled_count;

  // 각 상태별 비율 계산
  const getPercent = (count: number) =>
    total_images > 0 ? (count / total_images) * 100 : 0;

  return (
    <div className={`bg-white rounded-lg border p-4 ${className}`}>
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-gray-900">이미지 검토 진행률</h3>
          <span className="text-sm text-gray-500">
            {completedCount}/{total_images} 완료
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-blue-600">
            {progress_percent.toFixed(1)}%
          </span>
          {export_ready && onExport && (
            <button
              onClick={onExport}
              className="flex items-center gap-1 px-3 py-1 bg-green-500 text-white text-sm rounded-lg hover:bg-green-600 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
          )}
        </div>
      </div>

      {/* 진행률 막대 */}
      <div className="h-4 bg-gray-100 rounded-full overflow-hidden flex">
        {/* 승인 (녹색) */}
        {approved_count > 0 && (
          <div
            className="h-full bg-green-500 transition-all"
            style={{ width: `${getPercent(approved_count)}%` }}
            title={`승인: ${approved_count}개`}
          />
        )}
        {/* 수정됨 (노란색) */}
        {modified_count > 0 && (
          <div
            className="h-full bg-yellow-500 transition-all"
            style={{ width: `${getPercent(modified_count)}%` }}
            title={`수정됨: ${modified_count}개`}
          />
        )}
        {/* 수동라벨 (보라색) */}
        {manual_labeled_count > 0 && (
          <div
            className="h-full bg-purple-500 transition-all"
            style={{ width: `${getPercent(manual_labeled_count)}%` }}
            title={`수동라벨: ${manual_labeled_count}개`}
          />
        )}
        {/* 거부 (빨간색) */}
        {rejected_count > 0 && (
          <div
            className="h-full bg-red-500 transition-all"
            style={{ width: `${getPercent(rejected_count)}%` }}
            title={`거부: ${rejected_count}개`}
          />
        )}
        {/* 분석완료 (파란색) */}
        {processed_count > 0 && (
          <div
            className="h-full bg-blue-400 transition-all"
            style={{ width: `${getPercent(processed_count)}%` }}
            title={`분석완료: ${processed_count}개`}
          />
        )}
        {/* 대기 (회색) - 나머지 공간 */}
      </div>

      {/* 상태별 통계 */}
      <div className="flex flex-wrap gap-4 mt-3 text-xs">
        {approved_count > 0 && (
          <div className="flex items-center gap-1 text-green-600">
            <CheckCircle className="w-3 h-3" />
            <span>승인 {approved_count}</span>
          </div>
        )}
        {modified_count > 0 && (
          <div className="flex items-center gap-1 text-yellow-600">
            <Edit3 className="w-3 h-3" />
            <span>수정됨 {modified_count}</span>
          </div>
        )}
        {manual_labeled_count > 0 && (
          <div className="flex items-center gap-1 text-purple-600">
            <Tag className="w-3 h-3" />
            <span>수동라벨 {manual_labeled_count}</span>
          </div>
        )}
        {rejected_count > 0 && (
          <div className="flex items-center gap-1 text-red-600">
            <XCircle className="w-3 h-3" />
            <span>거부 {rejected_count}</span>
          </div>
        )}
        {processed_count > 0 && (
          <div className="flex items-center gap-1 text-blue-600">
            <Eye className="w-3 h-3" />
            <span>분석완료 {processed_count}</span>
          </div>
        )}
        {pending_count > 0 && (
          <div className="flex items-center gap-1 text-gray-500">
            <Clock className="w-3 h-3" />
            <span>대기 {pending_count}</span>
          </div>
        )}
      </div>

      {/* Export 준비 상태 메시지 */}
      {export_ready ? (
        <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
          모든 이미지 검토가 완료되었습니다. Export가 가능합니다.
        </div>
      ) : (
        total_images > 0 &&
        pending_count + processed_count > 0 && (
          <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
            {pending_count + processed_count}개의 이미지가 검토 대기 중입니다.
          </div>
        )
      )}
    </div>
  );
}

export default ImageReviewProgressBar;
