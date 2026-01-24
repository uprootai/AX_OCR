/**
 * ImageReviewSection - 이미지별 Human-in-the-Loop 검토 섹션
 * Phase 2C: 다중 이미지 세션에서 이미지별 검토 수행
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Images,
  Upload,
  CheckCircle,
  XCircle,
  Filter,
  RefreshCw,
  Loader2,
  ChevronDown,
  Grid,
  List,
} from 'lucide-react';
import { sessionApi } from '../../../lib/api';
import { ImageReviewCard } from '../components/ImageReviewCard';
import { ImageReviewProgressBar } from '../components/ImageReviewProgressBar';
import type {
  SessionImage,
  SessionImageProgress,
  ImageReviewStatus,
} from '../../../types';

interface ImageReviewSectionProps {
  sessionId: string;
  onImageSelect?: (imageId: string, image: SessionImage) => void;
  onExportReady?: () => void;
}

type FilterStatus = 'all' | ImageReviewStatus;
type ViewMode = 'grid' | 'list';

export function ImageReviewSection({
  sessionId,
  onImageSelect,
  onExportReady,
}: ImageReviewSectionProps) {
  const [images, setImages] = useState<SessionImage[]>([]);
  const [progress, setProgress] = useState<SessionImageProgress | null>(null);
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [filter, setFilter] = useState<FilterStatus>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 이미지 목록 및 진행률 로드
  const loadData = useCallback(async () => {
    if (!sessionId) return;
    setIsLoading(true);
    setError(null);
    try {
      const [imageList, progressData] = await Promise.all([
        sessionApi.listImages(sessionId),
        sessionApi.getImageProgress(sessionId),
      ]);
      setImages(imageList);
      setProgress(progressData);

      // Export 준비 완료 시 콜백
      if (progressData.export_ready) {
        onExportReady?.();
      }
    } catch (err) {
      console.error('Failed to load images:', err);
      setError('이미지 목록을 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, onExportReady]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 이미지 업로드 처리
  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    setError(null);
    try {
      const result = await sessionApi.bulkUploadImages(
        sessionId,
        Array.from(files)
      );
      if (result.failed_count > 0) {
        setError(`${result.failed_count}개 파일 업로드 실패`);
      }
      await loadData();
    } catch (err) {
      console.error('Failed to upload images:', err);
      setError('이미지 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  // 이미지 검토 상태 변경
  const handleReview = async (imageId: string, status: ImageReviewStatus) => {
    try {
      await sessionApi.updateImageReview(sessionId, imageId, status);
      await loadData();
    } catch (err) {
      console.error('Failed to update review:', err);
      setError('검토 상태 변경에 실패했습니다.');
    }
  };

  // 이미지 선택
  const handleSelect = (imageId: string) => {
    setSelectedImageId(imageId);
    const image = images.find((img) => img.image_id === imageId);
    if (image) {
      onImageSelect?.(imageId, image);
    }
  };

  // 일괄 검토
  const handleBulkReview = async (status: ImageReviewStatus) => {
    const targetImages = filteredImages
      .filter(
        (img) =>
          img.review_status === 'pending' || img.review_status === 'processed'
      )
      .map((img) => img.image_id);

    if (targetImages.length === 0) return;

    try {
      await sessionApi.bulkReviewImages(sessionId, targetImages, status);
      await loadData();
    } catch (err) {
      console.error('Failed to bulk review:', err);
      setError('일괄 검토에 실패했습니다.');
    }
  };

  // 필터링된 이미지 목록
  const filteredImages =
    filter === 'all'
      ? images
      : images.filter((img) => img.review_status === filter);

  const filterOptions: { value: FilterStatus; label: string }[] = [
    { value: 'all', label: '전체' },
    { value: 'pending', label: '대기' },
    { value: 'processed', label: '분석완료' },
    { value: 'approved', label: '승인' },
    { value: 'rejected', label: '거부' },
    { value: 'modified', label: '수정됨' },
    { value: 'manual_labeled', label: '수동라벨' },
  ];

  return (
    <div className="bg-white rounded-xl border shadow-sm">
      {/* 헤더 */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Images className="w-5 h-5 text-blue-500" />
            <h2 className="font-semibold text-gray-900">이미지 검토</h2>
            <span className="text-sm text-gray-500">
              ({images.length}개)
            </span>
          </div>
          <div className="flex items-center gap-2">
            {/* 새로고침 */}
            <button
              onClick={loadData}
              disabled={isLoading}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="새로고침"
            >
              <RefreshCw
                className={`w-4 h-4 text-gray-500 ${isLoading ? 'animate-spin' : ''}`}
              />
            </button>
            {/* 보기 모드 전환 */}
            <div className="flex border rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100 text-gray-500'}`}
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100 text-gray-500'}`}
              >
                <List className="w-4 h-4" />
              </button>
            </div>
            {/* 이미지 추가 */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="flex items-center gap-1 px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              {isUploading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              이미지 추가
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*"
              className="hidden"
              onChange={(e) => handleUpload(e.target.files)}
            />
          </div>
        </div>
      </div>

      {/* 진행률 표시 */}
      {progress && (
        <div className="p-4 border-b">
          <ImageReviewProgressBar progress={progress} />
        </div>
      )}

      {/* 필터 및 일괄 작업 */}
      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          {/* 필터 */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <div className="relative">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as FilterStatus)}
                className="appearance-none bg-white border rounded-lg px-3 py-1.5 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {filterOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
            <span className="text-sm text-gray-500">
              {filteredImages.length}개 표시
            </span>
          </div>

          {/* 일괄 작업 */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">일괄 검토:</span>
            <button
              onClick={() => handleBulkReview('approved')}
              className="flex items-center gap-1 px-2 py-1 text-sm text-green-600 hover:bg-green-50 rounded transition-colors"
            >
              <CheckCircle className="w-4 h-4" />
              전체 승인
            </button>
            <button
              onClick={() => handleBulkReview('rejected')}
              className="flex items-center gap-1 px-2 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
            >
              <XCircle className="w-4 h-4" />
              전체 거부
            </button>
          </div>
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="p-4 bg-red-50 border-b border-red-100">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* 이미지 그리드/리스트 */}
      <div className="p-4">
        {isLoading && images.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        ) : images.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Images className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>이미지가 없습니다.</p>
            <p className="text-sm mt-1">위의 "이미지 추가" 버튼을 클릭하여 추가하세요.</p>
          </div>
        ) : filteredImages.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Filter className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>필터 조건에 맞는 이미지가 없습니다.</p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {filteredImages.map((image) => (
              <ImageReviewCard
                key={image.image_id}
                image={image}
                isSelected={selectedImageId === image.image_id}
                onSelect={handleSelect}
                onReview={handleReview}
                onViewDetails={(id) => handleSelect(id)}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredImages.map((image) => (
              <div
                key={image.image_id}
                className={`flex items-center gap-4 p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedImageId === image.image_id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleSelect(image.image_id)}
              >
                {/* 썸네일 */}
                <div className="w-16 h-16 rounded bg-gray-100 overflow-hidden flex-shrink-0">
                  {image.thumbnail_base64 ? (
                    <img
                      src={`data:image/jpeg;base64,${image.thumbnail_base64}`}
                      alt={image.filename}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <Images className="w-6 h-6" />
                    </div>
                  )}
                </div>
                {/* 정보 */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {image.filename}
                  </p>
                  <p className="text-sm text-gray-500">
                    검출: {image.detection_count}개 | 검증: {image.verified_count}개
                  </p>
                </div>
                {/* 상태 */}
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      image.review_status === 'approved'
                        ? 'bg-green-100 text-green-600'
                        : image.review_status === 'rejected'
                          ? 'bg-red-100 text-red-600'
                          : image.review_status === 'modified'
                            ? 'bg-yellow-100 text-yellow-600'
                            : image.review_status === 'processed'
                              ? 'bg-blue-100 text-blue-600'
                              : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {image.review_status}
                  </span>
                </div>
                {/* 빠른 액션 */}
                <div className="flex gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleReview(image.image_id, 'approved');
                    }}
                    className="p-1.5 hover:bg-green-100 rounded transition-colors"
                    title="승인"
                  >
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleReview(image.image_id, 'rejected');
                    }}
                    className="p-1.5 hover:bg-red-100 rounded transition-colors"
                    title="거부"
                  >
                    <XCircle className="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ImageReviewSection;
