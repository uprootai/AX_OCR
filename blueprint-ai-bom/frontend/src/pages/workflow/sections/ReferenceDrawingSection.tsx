/**
 * ReferenceDrawingSection - 원본 도면 섹션
 * 업로드된 도면 이미지와 기본 정보를 표시
 */

import { InfoTooltip } from '../../../components/Tooltip';
import { FEATURE_TOOLTIPS } from '../../../components/tooltipContent';

interface ReferenceDrawingSectionProps {
  imageData: string;
  imageSize: { width: number; height: number } | null;
  detectionCount?: number;
  approvedCount?: number;
  onImageClick: () => void;
}

export function ReferenceDrawingSection({
  imageData,
  imageSize,
  onImageClick,
}: ReferenceDrawingSectionProps) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-1">
        📐 원본 도면
        <InfoTooltip content={FEATURE_TOOLTIPS.referenceDrawing.description} position="right" />
      </h2>
      <div className="relative">
        <img
          src={imageData}
          alt="도면"
          className="w-full max-h-[600px] object-contain rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:opacity-90 transition-opacity"
          onClick={onImageClick}
          title="클릭하여 크게 보기"
        />
        {imageSize && (
          <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
            {imageSize.width} × {imageSize.height}
          </div>
        )}
        <p className="text-xs text-gray-500 text-center mt-1">📌 클릭하여 크게 보기</p>
      </div>
    </section>
  );
}
