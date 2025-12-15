/**
 * DetectionCard - 개별 검출 결과 카드
 * 크롭된 이미지, 승인/거부/수정 기능 포함
 * 그리드 및 리스트 레이아웃 지원, 다크모드 대응
 */

import { useState, useMemo } from 'react';
import { Check, X, Edit2, Save, RotateCcw } from 'lucide-react';
import type { Detection, VerificationStatus } from '../types';

interface DetectionCardProps {
  detection: Detection;
  index: number;
  imageData: string | null;
  imageSize: { width: number; height: number } | null;
  availableClasses: string[];
  onVerify: (status: VerificationStatus, modifiedClassName?: string) => void;
}

export function DetectionCard({
  detection,
  index,
  imageData,
  imageSize,
  availableClasses,
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

  // 크롭된 이미지 생성
  const croppedImageUrl = useMemo(() => {
    if (!imageData || !imageSize) return null;

    const bbox = detection.modified_bbox || detection.bbox;
    const { x1, y1, x2, y2 } = bbox;

    // Canvas를 사용하여 이미지 크롭
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    const img = new Image();
    img.src = imageData;

    // 이미지 로드 완료 시 크롭 실행
    return new Promise<string>((resolve) => {
      if (img.complete) {
        cropImage();
      } else {
        img.onload = cropImage;
      }

      function cropImage() {
        // 원본 이미지 크기 대비 실제 좌표 계산
        const scaleX = img.naturalWidth / imageSize!.width;
        const scaleY = img.naturalHeight / imageSize!.height;

        const cropX = Math.max(0, Math.floor(x1 * scaleX));
        const cropY = Math.max(0, Math.floor(y1 * scaleY));
        const cropW = Math.min(img.naturalWidth - cropX, Math.floor((x2 - x1) * scaleX));
        const cropH = Math.min(img.naturalHeight - cropY, Math.floor((y2 - y1) * scaleY));

        canvas.width = cropW;
        canvas.height = cropH;

        ctx!.drawImage(
          img,
          cropX, cropY, cropW, cropH,
          0, 0, cropW, cropH
        );

        resolve(canvas.toDataURL('image/png'));
      }
    });
  }, [imageData, imageSize, detection.bbox, detection.modified_bbox]);

  // 크롭 이미지 상태
  const [croppedSrc, setCroppedSrc] = useState<string | null>(null);

  // 크롭 이미지 로드
  useMemo(() => {
    if (croppedImageUrl instanceof Promise) {
      croppedImageUrl.then(setCroppedSrc);
    }
  }, [croppedImageUrl]);

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

        {/* 크롭된 이미지 - 중앙 정렬 */}
        <div className="flex-shrink-0 w-full h-32 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden flex items-center justify-center mb-3">
          {croppedSrc ? (
            <img
              src={croppedSrc}
              alt={`검출 ${index + 1}`}
              className="max-w-full max-h-full object-contain"
            />
          ) : (
            <div className="text-gray-400 dark:text-gray-500 text-xs text-center p-2">
              이미지 로딩...
            </div>
          )}
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
