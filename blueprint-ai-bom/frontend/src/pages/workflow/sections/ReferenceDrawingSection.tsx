/**
 * ReferenceDrawingSection - 원본 도면 섹션
 * 업로드된 도면 이미지와 기본 정보를 표시
 */

import { InfoTooltip } from '../../../components/Tooltip';
import { FEATURE_TOOLTIPS } from '../../../components/tooltipContent';

interface ReferenceDrawingSectionProps {
  imageData: string;
  imageSize: { width: number; height: number } | null;
  detectionCount: number;
  approvedCount: number;
  onImageClick: () => void;
}

export function ReferenceDrawingSection({
  imageData,
  imageSize,
  detectionCount,
  approvedCount,
  onImageClick,
}: ReferenceDrawingSectionProps) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-1">
        📐 원본 도면
        <InfoTooltip content={FEATURE_TOOLTIPS.referenceDrawing.description} position="right" />
      </h2>
      <div className="flex gap-4">
        <div className="flex-1">
          <img
            src={imageData}
            alt="도면"
            className="w-full max-h-[400px] object-contain rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:opacity-90 transition-opacity"
            onClick={onImageClick}
            title="클릭하여 크게 보기"
          />
          <p className="text-xs text-gray-500 text-center mt-1">📌 클릭하여 크게 보기</p>
        </div>
        {imageSize && (
          <div className="w-48 space-y-2 text-sm">
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2 flex items-center">
              <span className="text-gray-500">크기:</span>
              <span className="ml-2 font-medium">{imageSize.width} × {imageSize.height}</span>
              <InfoTooltip content={FEATURE_TOOLTIPS.imageSize.description} position="left" iconSize={12} />
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2 flex items-center">
              <span className="text-gray-500">검출:</span>
              <span className="ml-2 font-medium">{detectionCount}개</span>
              <InfoTooltip content={FEATURE_TOOLTIPS.detectionCount.description} position="left" iconSize={12} />
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2 flex items-center">
              <span className="text-gray-500">승인:</span>
              <span className="ml-2 font-medium text-green-600">{approvedCount}개</span>
              <InfoTooltip content={FEATURE_TOOLTIPS.approvedCount.description} position="left" iconSize={12} />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
