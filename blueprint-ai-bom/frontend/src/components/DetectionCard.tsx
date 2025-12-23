/**
 * DetectionCard - 개별 검출 결과 카드
 * 크롭된 이미지, 승인/거부/수정 기능 포함
 * 그리드 및 리스트 레이아웃 지원, 다크모드 대응
 */

import { useState, useEffect } from 'react';
import { Check, X, Edit2, Save, RotateCcw } from 'lucide-react';
import logger from '../lib/logger';
import type { Detection, VerificationStatus } from '../types';

interface DetectionCardProps {
  detection: Detection;
  index: number;
  imageData: string | null;
  imageSize: { width: number; height: number } | null;
  availableClasses: string[];
  referenceImage?: string | null; // class_examples에서 가져온 참조 이미지 (base64)
  gtClassName?: string | null; // GT 클래스명
  gtIou?: number | null; // IoU 점수
  gtBbox?: { x1: number; y1: number; x2: number; y2: number } | null; // GT bbox for cropping
  onVerify: (status: VerificationStatus, modifiedClassName?: string) => void;
}

export function DetectionCard({
  detection,
  index,
  imageData,
  imageSize,
  availableClasses,
  referenceImage,
  gtClassName,
  gtIou,
  gtBbox,
  onVerify,
}: DetectionCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [selectedClass, setSelectedClass] = useState(
    detection.modified_class_name || detection.class_name
  );

  // 상태에 따른 스타일 (다크모드 지원)
  const statusStyles = {
    pending: {
      border: 'border-yellow-300 dark:border-yellow-600',
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      badge: 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300',
      label: '대기중',
    },
    approved: {
      border: 'border-green-300 dark:border-green-600',
      bg: 'bg-green-50 dark:bg-green-900/20',
      badge: 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300',
      label: '승인됨',
    },
    rejected: {
      border: 'border-red-300 dark:border-red-600',
      bg: 'bg-red-50 dark:bg-red-900/20',
      badge: 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300',
      label: '거부됨',
    },
    modified: {
      border: 'border-purple-300 dark:border-purple-600',
      bg: 'bg-purple-50 dark:bg-purple-900/20',
      badge: 'bg-purple-100 dark:bg-purple-900/50 text-purple-800 dark:text-purple-300',
      label: '수정됨',
    },
    manual: {
      border: 'border-blue-300 dark:border-blue-600',
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      badge: 'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300',
      label: '수동추가',
    },
  };

  const currentStatus = detection.verification_status;
  const style = statusStyles[currentStatus] || statusStyles.pending;

  // 크롭 이미지 상태
  const [croppedSrc, setCroppedSrc] = useState<string | null>(null);
  // GT 크롭 이미지 상태
  const [gtCroppedSrc, setGtCroppedSrc] = useState<string | null>(null);

  // 크롭된 이미지 생성 (useEffect로 side effect 처리)
  useEffect(() => {
    if (!imageData || !imageSize) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- 조건부 early return, 필수적인 초기화
      setCroppedSrc(null);
      return;
    }

    const bbox = detection.modified_bbox || detection.bbox;
    const { x1, y1, x2, y2 } = bbox;

    // Canvas를 사용하여 이미지 크롭
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setCroppedSrc(null);
      return;
    }

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = imageData;

    function cropImage() {
      // bbox 좌표를 직접 사용 (imageSize는 이미 원본 크기)
      const cropX = Math.max(0, Math.floor(x1));
      const cropY = Math.max(0, Math.floor(y1));
      const cropW = Math.max(1, Math.floor(x2 - x1));
      const cropH = Math.max(1, Math.floor(y2 - y1));

      canvas.width = cropW;
      canvas.height = cropH;

      ctx!.drawImage(
        img,
        cropX, cropY, cropW, cropH,
        0, 0, cropW, cropH
      );

      try {
        const dataUrl = canvas.toDataURL('image/png');
        setCroppedSrc(dataUrl);
      } catch (e) {
        logger.error('Failed to crop image:', e);
        setCroppedSrc(null);
      }
    }

    if (img.complete && img.naturalWidth > 0) {
      cropImage();
    } else {
      img.onload = cropImage;
      img.onerror = () => setCroppedSrc(null);
    }
  }, [imageData, imageSize, detection.bbox, detection.modified_bbox]);

  // GT 크롭된 이미지 생성
  useEffect(() => {
    if (!imageData || !imageSize || !gtBbox) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- 조건부 early return, 필수적인 초기화
      setGtCroppedSrc(null);
      return;
    }

    const { x1, y1, x2, y2 } = gtBbox;

    // Canvas를 사용하여 이미지 크롭
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setGtCroppedSrc(null);
      return;
    }

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = imageData;

    function cropGtImage() {
      const cropX = Math.max(0, Math.floor(x1));
      const cropY = Math.max(0, Math.floor(y1));
      const cropW = Math.max(1, Math.floor(x2 - x1));
      const cropH = Math.max(1, Math.floor(y2 - y1));

      canvas.width = cropW;
      canvas.height = cropH;

      ctx!.drawImage(
        img,
        cropX, cropY, cropW, cropH,
        0, 0, cropW, cropH
      );

      try {
        const dataUrl = canvas.toDataURL('image/png');
        setGtCroppedSrc(dataUrl);
      } catch (e) {
        logger.error('Failed to crop GT image:', e);
        setGtCroppedSrc(null);
      }
    }

    if (img.complete && img.naturalWidth > 0) {
      cropGtImage();
    } else {
      img.onload = cropGtImage;
      img.onerror = () => setGtCroppedSrc(null);
    }
  }, [imageData, imageSize, gtBbox]);

  // 클래스 수정 완료
  const handleSaveEdit = () => {
    if (selectedClass !== detection.class_name) {
      onVerify('modified', selectedClass);
    }
    setIsEditing(false);
  };

  // 클래스 수정 취소
  const handleCancelEdit = () => {
    setSelectedClass(detection.modified_class_name || detection.class_name);
    setIsEditing(false);
  };

  // 현재 표시할 클래스명
  const displayClassName = detection.modified_class_name || detection.class_name;

  return (
    <div className={`rounded-lg border-2 ${style.border} ${style.bg} p-4 transition-colors`}>
      {/* 그리드/리스트 모두 대응하는 세로 레이아웃 */}
      <div className="flex flex-col h-full">
        {/* 상단: 번호 + 상태 배지 */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gray-700 dark:bg-gray-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
              {index + 1}
            </div>
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${style.badge}`}>
              {style.label}
            </span>
          </div>
          <span className={`text-sm font-bold ${
            detection.confidence >= 0.9 ? 'text-green-600 dark:text-green-400' :
            detection.confidence >= 0.7 ? 'text-yellow-600 dark:text-yellow-400' :
            'text-red-600 dark:text-red-400'
          }`} title="검출 신뢰도">
            {(detection.confidence * 100).toFixed(0)}%
          </span>
        </div>

        {/* 3개 이미지 비교 - Streamlit 스타일 */}
        <div className="flex gap-2 mb-3">
          {/* 1. GT (Ground Truth) 이미지 */}
          <div className="flex-1 min-w-0">
            <div className="text-xs text-center mb-1 font-medium text-blue-600 dark:text-blue-400">
              🏷️ GT
            </div>
            <div className="h-20 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded overflow-hidden flex items-center justify-center">
              {gtCroppedSrc ? (
                <img
                  src={gtCroppedSrc}
                  alt="GT"
                  className="max-w-full max-h-full object-contain"
                />
              ) : gtClassName && gtIou !== undefined && gtIou !== null ? (
                <div className="text-center p-1">
                  <div className="text-green-500 dark:text-green-400 text-lg">✓</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">매칭됨</div>
                </div>
              ) : (
                <div className="text-gray-300 dark:text-gray-600 text-xs text-center">
                  없음
                </div>
              )}
            </div>
            {gtClassName && gtIou !== undefined && gtIou !== null && (
              <div className="text-xs text-center mt-0.5 text-green-600 dark:text-green-400 truncate" title={gtClassName}>
                IoU: {(gtIou * 100).toFixed(0)}%
              </div>
            )}
          </div>

          {/* 2. 검출 (Detection) 이미지 */}
          <div className="flex-1 min-w-0">
            <div className="text-xs text-center mb-1 font-medium text-green-600 dark:text-green-400">
              🔍 검출
            </div>
            <div className="h-20 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded overflow-hidden flex items-center justify-center">
              {croppedSrc ? (
                <img
                  src={croppedSrc}
                  alt={`검출 ${index + 1}`}
                  className="max-w-full max-h-full object-contain"
                />
              ) : (
                <div className="text-gray-400 dark:text-gray-500 text-xs text-center">
                  로딩...
                </div>
              )}
            </div>
            <div className="text-xs text-center mt-0.5 text-gray-500 dark:text-gray-400">
              {(detection.confidence * 100).toFixed(0)}%
            </div>
          </div>

          {/* 3. 참조 (Reference) 이미지 */}
          <div className="flex-1 min-w-0">
            <div className="text-xs text-center mb-1 font-medium text-purple-600 dark:text-purple-400">
              📚 참조
            </div>
            <div className="h-20 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded overflow-hidden flex items-center justify-center">
              {referenceImage ? (
                <img
                  src={`data:image/jpeg;base64,${referenceImage}`}
                  alt="참조"
                  className="max-w-full max-h-full object-contain"
                />
              ) : (
                <div className="text-gray-300 dark:text-gray-600 text-xs text-center">
                  없음
                </div>
              )}
            </div>
            <div className="text-xs text-center mt-0.5 text-gray-500 dark:text-gray-400">
              표준 심볼
            </div>
          </div>
        </div>

        {/* 클래스명 */}
        <div className="flex-1 min-w-0 mb-3">
          {isEditing ? (
            <div>
              <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">클래스 선택:</label>
              <select
                value={selectedClass}
                onChange={(e) => setSelectedClass(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {availableClasses.map((cls) => (
                  <option key={cls} value={cls}>
                    {cls}
                  </option>
                ))}
                {!availableClasses.includes(displayClassName) && (
                  <option value={displayClassName}>{displayClassName}</option>
                )}
              </select>
            </div>
          ) : (
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate" title={displayClassName}>
              {displayClassName}
            </h3>
          )}

          {/* 원본 클래스명 표시 (수정된 경우) */}
          {detection.modified_class_name && detection.modified_class_name !== detection.class_name && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
              원래: {detection.class_name}
            </p>
          )}

          {/* 메타 정보 - Streamlit 스타일: 좌표 + 크기 */}
          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 space-y-0.5">
            <div title="검출 위치 (좌상단)">
              📍 위치: ({detection.bbox.x1}, {detection.bbox.y1})
            </div>
            <div title="바운딩 박스 크기">
              📐 크기: {detection.bbox.x2 - detection.bbox.x1}×{detection.bbox.y2 - detection.bbox.y1}px
            </div>
          </div>
        </div>

        {/* 액션 버튼 - 가로 배치 */}
        <div className="flex items-center space-x-2">
          {isEditing ? (
            <>
              <button
                onClick={handleSaveEdit}
                className="flex-1 flex items-center justify-center space-x-1 px-2 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-xs transition-colors"
                title="변경사항 저장"
              >
                <Save className="w-3.5 h-3.5" />
                <span>저장</span>
              </button>
              <button
                onClick={handleCancelEdit}
                className="flex-1 flex items-center justify-center space-x-1 px-2 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 text-xs transition-colors"
                title="편집 취소"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>취소</span>
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => onVerify('approved')}
                disabled={currentStatus === 'approved'}
                className={`flex-1 flex items-center justify-center space-x-1 px-2 py-1.5 rounded-lg text-xs transition-colors ${
                  currentStatus === 'approved'
                    ? 'bg-green-200 dark:bg-green-900/50 text-green-800 dark:text-green-300 cursor-not-allowed'
                    : 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-300 dark:border-green-700 hover:bg-green-100 dark:hover:bg-green-900/50'
                }`}
                title="이 검출을 승인합니다 (BOM에 포함)"
              >
                <Check className="w-3.5 h-3.5" />
                <span>승인</span>
              </button>
              <button
                onClick={() => onVerify('rejected')}
                disabled={currentStatus === 'rejected'}
                className={`flex-1 flex items-center justify-center space-x-1 px-2 py-1.5 rounded-lg text-xs transition-colors ${
                  currentStatus === 'rejected'
                    ? 'bg-red-200 dark:bg-red-900/50 text-red-800 dark:text-red-300 cursor-not-allowed'
                    : 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-300 dark:border-red-700 hover:bg-red-100 dark:hover:bg-red-900/50'
                }`}
                title="이 검출을 거부합니다 (BOM에서 제외)"
              >
                <X className="w-3.5 h-3.5" />
                <span>거부</span>
              </button>
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center justify-center px-2 py-1.5 bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 text-xs transition-colors"
                title="클래스명을 수정합니다"
              >
                <Edit2 className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
