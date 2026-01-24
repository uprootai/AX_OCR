/**
 * ImageReviewCard - 이미지 검토 카드 컴포넌트
 * 썸네일 + 상태 배지 + 검출 수 + 빠른 검토 버튼
 */

import { useState } from 'react';
import {
  CheckCircle,
  XCircle,
  Edit3,
  Clock,
  Loader2,
  Eye,
  MoreVertical,
  Tag,
} from 'lucide-react';
import type { SessionImage, ImageReviewStatus } from '../../../types';

interface ImageReviewCardProps {
  image: SessionImage;
  isSelected?: boolean;
  onSelect?: (imageId: string) => void;
  onReview?: (imageId: string, status: ImageReviewStatus) => Promise<void>;
  onViewDetails?: (imageId: string) => void;
}

const STATUS_CONFIG: Record<
  ImageReviewStatus,
  { label: string; color: string; bgColor: string; icon: React.ReactNode }
> = {
  pending: {
    label: '대기',
    color: 'text-gray-500',
    bgColor: 'bg-gray-100',
    icon: <Clock className="w-3 h-3" />,
  },
  processed: {
    label: '분석완료',
    color: 'text-blue-500',
    bgColor: 'bg-blue-100',
    icon: <Eye className="w-3 h-3" />,
  },
  approved: {
    label: '승인',
    color: 'text-green-500',
    bgColor: 'bg-green-100',
    icon: <CheckCircle className="w-3 h-3" />,
  },
  rejected: {
    label: '거부',
    color: 'text-red-500',
    bgColor: 'bg-red-100',
    icon: <XCircle className="w-3 h-3" />,
  },
  modified: {
    label: '수정됨',
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-100',
    icon: <Edit3 className="w-3 h-3" />,
  },
  manual_labeled: {
    label: '수동라벨',
    color: 'text-purple-500',
    bgColor: 'bg-purple-100',
    icon: <Tag className="w-3 h-3" />,
  },
};

export function ImageReviewCard({
  image,
  isSelected = false,
  onSelect,
  onReview,
  onViewDetails,
}: ImageReviewCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const statusConfig = STATUS_CONFIG[image.review_status] || STATUS_CONFIG.pending;

  const handleReview = async (status: ImageReviewStatus) => {
    if (!onReview || isLoading) return;
    setIsLoading(true);
    try {
      await onReview(image.image_id, status);
    } finally {
      setIsLoading(false);
      setShowActions(false);
    }
  };

  return (
    <div
      className={`
        relative group rounded-lg border-2 transition-all cursor-pointer
        ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300 bg-white'}
        ${isLoading ? 'opacity-50' : ''}
      `}
      onClick={() => onSelect?.(image.image_id)}
    >
      {/* 썸네일 */}
      <div className="aspect-square relative overflow-hidden rounded-t-lg bg-gray-100">
        {image.thumbnail_base64 ? (
          <img
            src={`data:image/jpeg;base64,${image.thumbnail_base64}`}
            alt={image.filename}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <Eye className="w-8 h-8" />
          </div>
        )}

        {/* 상태 배지 */}
        <div
          className={`absolute top-2 left-2 px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 ${statusConfig.bgColor} ${statusConfig.color}`}
        >
          {statusConfig.icon}
          {statusConfig.label}
        </div>

        {/* 검출 수 배지 */}
        {image.detection_count > 0 && (
          <div className="absolute top-2 right-2 bg-black/60 text-white px-2 py-0.5 rounded-full text-xs">
            {image.detection_count}개 검출
          </div>
        )}

        {/* 로딩 오버레이 */}
        {isLoading && (
          <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
            <Loader2 className="w-6 h-6 text-white animate-spin" />
          </div>
        )}

        {/* 호버 액션 버튼 */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
          <div className="flex gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onViewDetails?.(image.image_id);
              }}
              className="p-2 bg-white rounded-full shadow-lg hover:bg-gray-100 transition-colors"
              title="상세 보기"
            >
              <Eye className="w-4 h-4 text-gray-700" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowActions(!showActions);
              }}
              className="p-2 bg-white rounded-full shadow-lg hover:bg-gray-100 transition-colors"
              title="검토 옵션"
            >
              <MoreVertical className="w-4 h-4 text-gray-700" />
            </button>
          </div>
        </div>
      </div>

      {/* 정보 영역 */}
      <div className="p-2">
        <p className="text-xs text-gray-600 truncate" title={image.filename}>
          {image.filename}
        </p>
        {image.verified_count > 0 && (
          <p className="text-xs text-gray-400 mt-1">
            검증: {image.verified_count}/{image.detection_count}
          </p>
        )}
      </div>

      {/* 빠른 액션 드롭다운 */}
      {showActions && (
        <div
          className="absolute bottom-12 right-2 bg-white rounded-lg shadow-lg border z-10 overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className="w-full px-3 py-2 text-sm text-left hover:bg-green-50 flex items-center gap-2"
            onClick={() => handleReview('approved')}
          >
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span>승인</span>
          </button>
          <button
            className="w-full px-3 py-2 text-sm text-left hover:bg-red-50 flex items-center gap-2"
            onClick={() => handleReview('rejected')}
          >
            <XCircle className="w-4 h-4 text-red-500" />
            <span>거부</span>
          </button>
          <button
            className="w-full px-3 py-2 text-sm text-left hover:bg-yellow-50 flex items-center gap-2"
            onClick={() => handleReview('modified')}
          >
            <Edit3 className="w-4 h-4 text-yellow-500" />
            <span>수정됨으로 표시</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default ImageReviewCard;
