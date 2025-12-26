/**
 * Relation Section
 * 치수-객체 관계 추출 섹션 컴포넌트
 */

import { Loader2, RefreshCw } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import { FEATURE_TOOLTIPS } from '../../../components/tooltipContent';
import { RelationList } from '../../../components/RelationList';
import { RelationOverlay } from '../../../components/RelationOverlay';
import type { Detection, DimensionRelation, RelationStatistics } from '../../../types';
import type { Dimension } from '../types/workflow';

interface RelationSectionProps {
  imageData: string;
  imageSize: { width: number; height: number };
  relations: DimensionRelation[];
  relationStats: RelationStatistics | null;
  dimensions: Dimension[];
  detections: Detection[];
  selectedDimensionId: string | null;
  setSelectedDimensionId: (id: string | null) => void;
  showRelations: boolean;
  setShowRelations: (show: boolean) => void;
  isExtractingRelations: boolean;
  onExtractRelations: () => void;
  onManualLink: (dimensionId: string, targetId: string) => void;
  onDeleteRelation: (relationId: string) => void;
}

export function RelationSection({
  imageData,
  imageSize,
  relations,
  relationStats,
  dimensions,
  detections,
  selectedDimensionId,
  setSelectedDimensionId,
  showRelations,
  setShowRelations,
  isExtractingRelations,
  onExtractRelations,
  onManualLink,
  onDeleteRelation,
}: RelationSectionProps) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          🔗 치수-객체 관계
          <InfoTooltip content={FEATURE_TOOLTIPS.dimensionRelation.description} position="right" />
          {relations.length > 0 && (
            <span className="px-2 py-0.5 text-xs font-normal bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 rounded-full">
              {relations.length}개
            </span>
          )}
        </h2>
        <div className="flex items-center gap-2">
          {/* 토글 버튼 */}
          <button
            onClick={() => setShowRelations(!showRelations)}
            className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
              showRelations
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
            }`}
          >
            {showRelations ? '관계선 표시' : '관계선 숨김'}
          </button>
          {/* 추출 버튼 */}
          <button
            onClick={onExtractRelations}
            disabled={isExtractingRelations}
            className="flex items-center gap-2 px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isExtractingRelations ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" />
                추출 중...
              </>
            ) : (
              <>
                <RefreshCw className="w-3 h-3" />
                관계 재추출
              </>
            )}
          </button>
        </div>
      </div>

      {/* 이미지 + 관계 오버레이 */}
      {relations.length > 0 && showRelations && (
        <div className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 mb-4" style={{ height: 350 }}>
          <img
            src={imageData}
            alt="Blueprint with relations"
            className="w-full h-full object-contain"
          />
          <RelationOverlay
            relations={relations}
            dimensions={dimensions.map(d => ({ id: d.id, bbox: d.bbox, value: d.value }))}
            detections={detections}
            imageSize={imageSize}
            containerSize={{ width: 600, height: 350 }}
            selectedDimensionId={selectedDimensionId}
            showLabels={true}
            showConfidence={true}
          />
        </div>
      )}

      {/* 관계 목록 */}
      <RelationList
        relations={relations}
        statistics={relationStats}
        dimensions={dimensions.map(d => ({ id: d.id, value: d.value, bbox: d.bbox }))}
        detections={detections}
        onManualLink={onManualLink}
        onDeleteRelation={onDeleteRelation}
        onSelectDimension={(id) => setSelectedDimensionId(id)}
        selectedDimensionId={selectedDimensionId}
        isLoading={isExtractingRelations}
      />
    </section>
  );
}
