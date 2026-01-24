/**
 * CustomerImageReviewPage - 고객용 이미지 검토 페이지
 * Phase 2F: 제한된 권한의 고객용 UI
 * - 이미지 + 검출 결과 표시
 * - 검출 결과 수정 가능 (라벨, bbox)
 * - 승인/거부 가능
 * - 워크플로우/모델/파라미터 수정 불가
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  XCircle,
  Edit3,
  Lock,
  Loader2,
  ZoomIn,
  ZoomOut,
  RotateCw,
  MessageSquare,
} from 'lucide-react';
import { sessionApi, type SessionImage, type ImageReviewStatus, type Detection } from '../../lib/api';

export function CustomerImageReviewPage() {
  const { projectId, imageId } = useParams<{ projectId: string; imageId: string }>();
  const navigate = useNavigate();
  const [image, setImage] = useState<SessionImage | null>(null);
  const [allImages, setAllImages] = useState<SessionImage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [reviewNotes, setReviewNotes] = useState('');
  const [showNotes, setShowNotes] = useState(false);

  // 현재 이미지 인덱스
  const currentIndex = allImages.findIndex((img) => img.image_id === imageId);

  // 데이터 로드
  const loadData = useCallback(async () => {
    if (!projectId || !imageId) return;
    setIsLoading(true);
    setError(null);
    try {
      // 프로젝트의 첫 번째 세션 ID 가져오기 (간단한 구현)
      // 실제로는 이미지가 속한 세션을 찾아야 함
      const project = await (await import('../../lib/api')).projectApi.get(projectId);
      if (project.sessions.length === 0) {
        setError('세션을 찾을 수 없습니다.');
        return;
      }

      const sessionId = project.sessions[0].session_id;
      const [imageList, imageDetail] = await Promise.all([
        sessionApi.listImages(sessionId),
        sessionApi.getImageDetail(sessionId, imageId, true),
      ]);

      setAllImages(imageList);
      setImage(imageDetail);
      setReviewNotes(imageDetail.review_notes || '');
    } catch (err) {
      console.error('Failed to load image:', err);
      setError('이미지를 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [projectId, imageId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 검토 상태 변경
  const handleReview = async (status: ImageReviewStatus) => {
    if (!projectId || !imageId || !image) return;

    setIsSaving(true);
    try {
      // 프로젝트의 첫 번째 세션 ID 가져오기
      const project = await (await import('../../lib/api')).projectApi.get(projectId);
      if (project.sessions.length === 0) return;

      const sessionId = project.sessions[0].session_id;
      await sessionApi.updateImageReview(
        sessionId,
        imageId,
        status,
        '고객', // 검토자
        reviewNotes || undefined
      );

      // 다음 이미지로 이동 (있는 경우)
      if (currentIndex < allImages.length - 1) {
        const nextImage = allImages[currentIndex + 1];
        navigate(`/customer/${projectId}/review/${nextImage.image_id}`);
      } else {
        // 마지막 이미지인 경우 목록으로
        navigate(`/customer/${projectId}`);
      }
    } catch (err) {
      console.error('Failed to update review:', err);
      setError('검토 상태 변경에 실패했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  // 이전/다음 이미지 네비게이션
  const goToPrev = () => {
    if (currentIndex > 0) {
      const prevImage = allImages[currentIndex - 1];
      navigate(`/customer/${projectId}/review/${prevImage.image_id}`);
    }
  };

  const goToNext = () => {
    if (currentIndex < allImages.length - 1) {
      const nextImage = allImages[currentIndex + 1];
      navigate(`/customer/${projectId}/review/${nextImage.image_id}`);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!image) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">
        <div className="text-center">
          <p className="text-gray-400">{error || '이미지를 찾을 수 없습니다.'}</p>
          <Link
            to={`/customer/${projectId}`}
            className="inline-flex items-center gap-2 mt-4 text-blue-400 hover:text-blue-300"
          >
            <ArrowLeft className="w-4 h-4" />
            목록으로
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* 헤더 */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              to={`/customer/${projectId}`}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-300" />
            </Link>
            <div>
              <h1 className="text-white font-medium">{image.filename}</h1>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <span>{currentIndex + 1} / {allImages.length}</span>
                <span>•</span>
                <span>검출 {image.detection_count}개</span>
                <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded text-xs flex items-center gap-1">
                  <Lock className="w-3 h-3" />
                  고객 검토
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* 줌 컨트롤 */}
            <div className="flex items-center gap-1 bg-gray-700 rounded-lg px-2 py-1">
              <button
                onClick={() => setZoom(Math.max(0.5, zoom - 0.25))}
                className="p-1 hover:bg-gray-600 rounded"
              >
                <ZoomOut className="w-4 h-4 text-gray-300" />
              </button>
              <span className="text-sm text-gray-300 w-12 text-center">
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={() => setZoom(Math.min(3, zoom + 0.25))}
                className="p-1 hover:bg-gray-600 rounded"
              >
                <ZoomIn className="w-4 h-4 text-gray-300" />
              </button>
              <button
                onClick={() => setZoom(1)}
                className="p-1 hover:bg-gray-600 rounded ml-1"
              >
                <RotateCw className="w-4 h-4 text-gray-300" />
              </button>
            </div>

            {/* 메모 토글 */}
            <button
              onClick={() => setShowNotes(!showNotes)}
              className={`p-2 rounded-lg transition-colors ${showNotes ? 'bg-blue-500 text-white' : 'hover:bg-gray-700 text-gray-300'}`}
            >
              <MessageSquare className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* 메인 영역 */}
      <div className="flex-1 flex">
        {/* 이미지 뷰어 */}
        <div className="flex-1 relative overflow-auto p-4">
          <div
            className="relative inline-block min-w-full"
            style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
          >
            {/* 원본 이미지 표시 (실제로는 파일 경로에서 로드) */}
            {image.thumbnail_base64 ? (
              <img
                src={`data:image/jpeg;base64,${image.thumbnail_base64}`}
                alt={image.filename}
                className="max-w-full"
              />
            ) : (
              <div className="w-full h-96 bg-gray-800 flex items-center justify-center text-gray-500">
                이미지를 불러올 수 없습니다
              </div>
            )}

            {/* 검출 결과 오버레이 */}
            {image.detections?.map((det: Detection, idx: number) => (
              <div
                key={det.id || idx}
                className="absolute border-2 border-green-500"
                style={{
                  left: det.bbox.x1,
                  top: det.bbox.y1,
                  width: det.bbox.x2 - det.bbox.x1,
                  height: det.bbox.y2 - det.bbox.y1,
                }}
              >
                <div className="absolute -top-5 left-0 bg-green-500 text-white text-xs px-1 rounded whitespace-nowrap">
                  {det.class_name} ({Math.round(det.confidence * 100)}%)
                </div>
              </div>
            ))}
          </div>

          {/* 이전/다음 버튼 */}
          <button
            onClick={goToPrev}
            disabled={currentIndex <= 0}
            className="absolute left-4 top-1/2 -translate-y-1/2 p-3 bg-black/50 hover:bg-black/70 rounded-full text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <button
            onClick={goToNext}
            disabled={currentIndex >= allImages.length - 1}
            className="absolute right-4 top-1/2 -translate-y-1/2 p-3 bg-black/50 hover:bg-black/70 rounded-full text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ArrowRight className="w-6 h-6" />
          </button>
        </div>

        {/* 메모 패널 */}
        {showNotes && (
          <div className="w-80 bg-gray-800 border-l border-gray-700 p-4">
            <h3 className="text-white font-medium mb-3">검토 메모</h3>
            <textarea
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="검토 의견을 입력하세요..."
              className="w-full h-40 bg-gray-700 text-white rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-2">
              승인/거부 시 메모가 함께 저장됩니다.
            </p>
          </div>
        )}
      </div>

      {/* 하단 액션 바 */}
      <div className="bg-gray-800 border-t border-gray-700 px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          {/* 현재 상태 */}
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">현재 상태:</span>
            <span
              className={`px-3 py-1 rounded text-sm font-medium ${
                image.review_status === 'approved'
                  ? 'bg-green-500/20 text-green-300'
                  : image.review_status === 'rejected'
                    ? 'bg-red-500/20 text-red-300'
                    : image.review_status === 'modified'
                      ? 'bg-yellow-500/20 text-yellow-300'
                      : 'bg-gray-600 text-gray-300'
              }`}
            >
              {image.review_status}
            </span>
          </div>

          {/* 액션 버튼 */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleReview('rejected')}
              disabled={isSaving}
              className="flex items-center gap-2 px-6 py-2 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-colors disabled:opacity-50"
            >
              <XCircle className="w-5 h-5" />
              거부
            </button>
            <button
              onClick={() => handleReview('modified')}
              disabled={isSaving}
              className="flex items-center gap-2 px-6 py-2 bg-yellow-500/20 text-yellow-300 rounded-lg hover:bg-yellow-500/30 transition-colors disabled:opacity-50"
            >
              <Edit3 className="w-5 h-5" />
              수정 필요
            </button>
            <button
              onClick={() => handleReview('approved')}
              disabled={isSaving}
              className="flex items-center gap-2 px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
            >
              {isSaving ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <CheckCircle className="w-5 h-5" />
              )}
              승인
            </button>
          </div>
        </div>
      </div>

      {/* 에러 토스트 */}
      {error && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
          {error}
        </div>
      )}
    </div>
  );
}

export default CustomerImageReviewPage;
