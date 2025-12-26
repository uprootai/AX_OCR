/**
 * Detection Row Component
 * 개별 검출 결과 행 컴포넌트
 */

import { useState, useEffect } from 'react';
import { Loader2, Check, X, Trash2 } from 'lucide-react';
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

interface DetectionRowProps {
  detection: Detection;
  index: number;
  globalIndex: number;
  imageData: string | null;
  imageSize: { width: number; height: number } | null;
  availableClasses: string[];
  classExamples: ClassExample[];
  gtMatch: GTMatch | null;
  gtBbox: { x1: number; y1: number; x2: number; y2: number } | null;
  showGTImages: boolean;
  showRefImages: boolean;
  editingId: string | null;
  editingClassName: string;
  setEditingId: (id: string | null) => void;
  setEditingClassName: (name: string) => void;
  onVerify: (id: string, status: VerificationStatus, modifiedClassName?: string) => void;
  onDelete: (id: string) => void;
}

export function DetectionRow({
  detection,
  globalIndex,
  imageData,
  imageSize,
  availableClasses,
  classExamples,
  gtMatch,
  gtBbox,
  showGTImages,
  showRefImages,
  editingId,
  editingClassName,
  setEditingId,
  setEditingClassName,
  onVerify,
  onDelete,
}: DetectionRowProps) {
  // Status colors
  const statusColors = {
    approved: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    rejected: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
    pending: 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700',
    manual: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800',
    modified: 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800',
  };

  // Crop image from bbox
  const cropImage = (bbox: { x1: number; y1: number; x2: number; y2: number }) => {
    if (!imageData || !imageSize) return null;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    const img = new Image();
    img.src = imageData;

    const width = bbox.x2 - bbox.x1;
    const height = bbox.y2 - bbox.y1;
    canvas.width = width;
    canvas.height = height;

    return new Promise<string>((resolve) => {
      img.onload = () => {
        ctx.drawImage(img, bbox.x1, bbox.y1, width, height, 0, 0, width, height);
        resolve(canvas.toDataURL());
      };
      if (img.complete) {
        ctx.drawImage(img, bbox.x1, bbox.y1, width, height, 0, 0, width, height);
        resolve(canvas.toDataURL());
      }
    });
  };

  const [croppedSrc, setCroppedSrc] = useState<string | null>(null);
  const [gtCroppedSrc, setGtCroppedSrc] = useState<string | null>(null);

  useEffect(() => {
    if (imageData && imageSize) {
      cropImage(detection.bbox)?.then(src => src && setCroppedSrc(src));
      if (gtBbox) {
        cropImage(gtBbox)?.then(src => src && setGtCroppedSrc(src));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [imageData, imageSize, detection.bbox, gtBbox]);

  const refExample = classExamples.find(ex => detection.class_name.includes(ex.class_name));

  return (
    <div className={`p-4 rounded-lg border ${statusColors[detection.verification_status]} mb-3`}>
      <div className="flex items-start gap-4">
        {/* Index */}
        <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-gray-200 dark:bg-gray-700 rounded-full text-sm font-bold">
          {globalIndex + 1}
        </div>

        {/* Images (GT, Detection, Reference) */}
        <div className="flex gap-2 flex-shrink-0">
          {/* GT Image */}
          {showGTImages && (
            <div className="text-center">
              <p className="text-xs text-gray-500 mb-1">🏷️ GT</p>
              <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded border flex items-center justify-center overflow-hidden">
                {gtCroppedSrc ? (
                  <img src={gtCroppedSrc} alt="GT" className="max-w-full max-h-full object-contain" />
                ) : (
                  <span className="text-xs text-gray-400">없음</span>
                )}
              </div>
            </div>
          )}

          {/* Detection Image */}
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">🔍 검출</p>
            <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded border flex items-center justify-center overflow-hidden">
              {croppedSrc ? (
                <img src={croppedSrc} alt="Detection" className="max-w-full max-h-full object-contain" />
              ) : (
                <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
              )}
            </div>
          </div>

          {/* Reference Image */}
          {showRefImages && (
            <div className="text-center">
              <p className="text-xs text-gray-500 mb-1">📚 참조</p>
              <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded border flex items-center justify-center overflow-hidden">
                {refExample?.image_base64 ? (
                  <img
                    src={`data:image/jpeg;base64,${refExample.image_base64}`}
                    alt="Reference"
                    className="max-w-full max-h-full object-contain"
                  />
                ) : (
                  <span className="text-xs text-gray-400">없음</span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {editingId === detection.id ? (
              // Edit mode: show class dropdown
              <select
                value={editingClassName}
                onChange={(e) => setEditingClassName(e.target.value)}
                className="px-2 py-1 text-sm border border-orange-300 dark:border-orange-600 rounded bg-white dark:bg-gray-800 focus:ring-2 focus:ring-orange-500"
                autoFocus
              >
                {availableClasses.map(cls => (
                  <option key={cls} value={cls}>{cls}</option>
                ))}
              </select>
            ) : (
              <span className="font-semibold text-gray-900 dark:text-white">
                {detection.modified_class_name || detection.class_name}
                {detection.modified_class_name && detection.modified_class_name !== detection.class_name && (
                  <span className="ml-1 text-xs text-orange-500">(수정됨)</span>
                )}
              </span>
            )}
            <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded">
              {(detection.confidence * 100).toFixed(1)}%
            </span>
            {gtMatch && (
              <span className={`text-xs px-2 py-0.5 rounded ${gtMatch.class_match ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                IoU: {(gtMatch.iou * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500">
            위치: ({detection.bbox.x1}, {detection.bbox.y1}) - ({detection.bbox.x2}, {detection.bbox.y2})
          </p>
          {gtMatch && !gtMatch.class_match && (
            <p className="text-xs text-yellow-600 mt-1">
              GT 클래스: {gtMatch.gt_class}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {editingId === detection.id ? (
            // Edit mode actions
            <>
              <button
                onClick={() => {
                  // Save edited class name
                  if (editingClassName && editingClassName !== detection.class_name) {
                    onVerify(detection.id, 'approved', editingClassName);
                  }
                  setEditingId(null);
                  setEditingClassName('');
                }}
                className="px-3 py-1.5 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-sm flex items-center gap-1"
                title="수정 완료"
              >
                <Check className="w-3 h-3" />
                <span>완료</span>
              </button>
              <button
                onClick={() => {
                  setEditingId(null);
                  setEditingClassName('');
                }}
                className="px-3 py-1.5 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 text-sm"
                title="취소"
              >
                취소
              </button>
            </>
          ) : (
            // Normal actions
            <>
              <button
                onClick={() => onVerify(detection.id, 'approved')}
                disabled={editingId !== null}
                className={`p-2 rounded-lg transition-colors ${detection.verification_status === 'approved'
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-green-100 hover:text-green-600'
                  } disabled:opacity-50`}
                title="승인"
              >
                <Check className="w-4 h-4" />
              </button>
              <button
                onClick={() => onVerify(detection.id, 'rejected')}
                disabled={editingId !== null}
                className={`p-2 rounded-lg transition-colors ${detection.verification_status === 'rejected'
                  ? 'bg-red-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-red-100 hover:text-red-600'
                  } disabled:opacity-50`}
                title="거부"
              >
                <X className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  setEditingId(detection.id);
                  setEditingClassName(detection.modified_class_name || detection.class_name);
                }}
                disabled={editingId !== null}
                className={`p-2 rounded-lg transition-colors ${detection.verification_status === 'modified'
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-orange-100 hover:text-orange-600'
                  } disabled:opacity-50`}
                title="수정"
              >
                <span className="text-sm">✏️</span>
              </button>
              {/* 삭제 버튼 - 수작업 라벨만 삭제 가능 */}
              {detection.verification_status === 'manual' && (
                <button
                  onClick={() => {
                    if (confirm('이 수작업 라벨을 삭제하시겠습니까?')) {
                      onDelete(detection.id);
                    }
                  }}
                  disabled={editingId !== null}
                  className="p-2 rounded-lg transition-colors bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-red-100 hover:text-red-600 disabled:opacity-50"
                  title="삭제"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
