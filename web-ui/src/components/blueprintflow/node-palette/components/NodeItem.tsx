/**
 * NodeItem Component
 * 개별 노드 아이템 렌더링
 */

import { Lightbulb, ArrowRight, AlertCircle } from 'lucide-react';
import { getNodeDefinition } from '../../../../config/nodeDefinitions';
import type { NodeConfig } from '../types';

interface RecommendedInput {
  from: string;
  field: string;
  reason: string;
}

interface NodeItemProps {
  node: NodeConfig;
  isActive: boolean;
  onDragStart: (e: React.DragEvent, nodeType: string, label: string) => void;
  tooltipColorScheme?: 'green' | 'purple' | 'red' | 'cyan';
  // Input 노드 전용 props
  isImageInputNode?: boolean;
  uploadedImage?: string | null;
  uploadedFileName?: string | null;
  onImageClick?: () => void;
}

// 색상 스킴 매핑
const colorSchemes = {
  green: {
    bg: 'from-green-50 to-emerald-50 dark:from-green-900/90 dark:to-emerald-900/90',
    border: 'border-green-300 dark:border-green-700',
    headerBorder: 'border-green-200 dark:border-green-700',
    headerIcon: 'text-green-700 dark:text-green-300',
    headerText: 'text-green-900 dark:text-green-100',
    from: 'text-green-800 dark:text-green-200',
    arrow: 'text-green-600',
    field: 'text-green-700 dark:text-green-300',
    reason: 'text-green-800 dark:text-green-100',
    reasonBorder: 'border-green-400',
  },
  purple: {
    bg: 'from-purple-50 to-violet-50 dark:from-purple-900/90 dark:to-violet-900/90',
    border: 'border-purple-300 dark:border-purple-700',
    headerBorder: 'border-purple-200 dark:border-purple-700',
    headerIcon: 'text-purple-700 dark:text-purple-300',
    headerText: 'text-purple-900 dark:text-purple-100',
    from: 'text-purple-800 dark:text-purple-200',
    arrow: 'text-purple-600',
    field: 'text-purple-700 dark:text-purple-300',
    reason: 'text-purple-800 dark:text-purple-100',
    reasonBorder: 'border-purple-400',
  },
  red: {
    bg: 'from-red-50 to-orange-50 dark:from-red-900/90 dark:to-orange-900/90',
    border: 'border-red-300 dark:border-red-700',
    headerBorder: 'border-red-200 dark:border-red-700',
    headerIcon: 'text-red-700 dark:text-red-300',
    headerText: 'text-red-900 dark:text-red-100',
    from: 'text-red-800 dark:text-red-200',
    arrow: 'text-red-600',
    field: 'text-red-700 dark:text-red-300',
    reason: 'text-red-800 dark:text-red-100',
    reasonBorder: 'border-red-400',
  },
  cyan: {
    bg: 'from-cyan-50 to-teal-50 dark:from-cyan-900/90 dark:to-teal-900/90',
    border: 'border-cyan-300 dark:border-cyan-700',
    headerBorder: 'border-cyan-200 dark:border-cyan-700',
    headerIcon: 'text-cyan-700 dark:text-cyan-300',
    headerText: 'text-cyan-900 dark:text-cyan-100',
    from: 'text-cyan-800 dark:text-cyan-200',
    arrow: 'text-cyan-600',
    field: 'text-cyan-700 dark:text-cyan-300',
    reason: 'text-cyan-800 dark:text-cyan-100',
    reasonBorder: 'border-cyan-400',
  },
};

/**
 * 추천 연결 툴팁 컴포넌트
 */
function RecommendedTooltip({
  recommendedInputs,
  colorScheme = 'green',
}: {
  recommendedInputs: RecommendedInput[];
  colorScheme: 'green' | 'purple' | 'red' | 'cyan';
}) {
  const colors = colorSchemes[colorScheme];

  return (
    <div className="absolute left-full ml-2 top-0 hidden group-hover:block z-50 w-72">
      <div
        className={`bg-gradient-to-br ${colors.bg} p-3 rounded-lg shadow-xl border-2 ${colors.border}`}
      >
        <div className={`flex items-center gap-2 mb-2 pb-2 border-b ${colors.headerBorder}`}>
          <Lightbulb className={`w-4 h-4 ${colors.headerIcon}`} />
          <span className={`text-xs font-semibold ${colors.headerText}`}>
            추천 연결 패턴
          </span>
        </div>
        <div className="space-y-2">
          {recommendedInputs.map((rec, idx) => (
            <div key={idx} className="text-xs">
              <div className="flex items-center gap-1.5 mb-1">
                <span className={`font-mono font-semibold ${colors.from}`}>{rec.from}</span>
                <ArrowRight className={`w-3 h-3 ${colors.arrow}`} />
                <span className={`font-mono ${colors.field}`}>{rec.field}</span>
              </div>
              <p className={`${colors.reason} leading-relaxed pl-2 border-l-2 ${colors.reasonBorder}`}>
                {rec.reason}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * 업로드된 이미지 미리보기 (Image Input 노드 전용)
 */
function ImagePreview({
  uploadedImage,
  uploadedFileName,
  onImageClick,
}: {
  uploadedImage: string;
  uploadedFileName?: string | null;
  onImageClick?: () => void;
}) {
  return (
    <div className="mt-2 ml-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
      <div className="flex items-center gap-2 mb-1">
        <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
          Uploaded Image
        </span>
      </div>
      <div className="relative group">
        <img
          src={uploadedImage}
          alt="Uploaded preview"
          className="w-full h-20 object-cover rounded border border-gray-300 dark:border-gray-600 cursor-pointer hover:opacity-80 transition-opacity"
          onClick={onImageClick}
          title="클릭하여 확대"
        />
        {uploadedFileName && (
          <div
            className="mt-1 text-xs text-gray-500 dark:text-gray-400 truncate cursor-pointer hover:text-blue-500"
            onClick={onImageClick}
          >
            {uploadedFileName}
          </div>
        )}
        {/* 클릭 힌트 */}
        <div className="absolute bottom-1 right-1 bg-black/50 text-white text-[10px] px-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
          클릭하여 확대
        </div>
      </div>
    </div>
  );
}

/**
 * NodeItem 컴포넌트
 * 드래그 가능한 개별 노드 아이템
 */
export function NodeItem({
  node,
  isActive,
  onDragStart,
  tooltipColorScheme = 'green',
  isImageInputNode = false,
  uploadedImage,
  uploadedFileName,
  onImageClick,
}: NodeItemProps) {
  const isEmojiIcon = typeof node.icon === 'string';
  const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;
  const definition = getNodeDefinition(node.type);
  const hasRecommendedInputs =
    definition?.recommendedInputs && definition.recommendedInputs.length > 0;

  return (
    <div className="relative group">
      <div
        draggable={isActive}
        onDragStart={(e) => isActive && onDragStart(e, node.type, node.label)}
        className={`flex items-start gap-2 p-3 rounded-lg border-2 transition-shadow ${
          isActive
            ? 'cursor-move bg-white dark:bg-gray-700 hover:shadow-md'
            : 'cursor-not-allowed bg-gray-100 dark:bg-gray-800 opacity-50'
        }`}
        style={{ borderColor: isActive ? `${node.color}40` : '#9ca3af40' }}
        title={isActive ? undefined : 'Container is stopped'}
      >
        {isEmojiIcon ? (
          <span className={`text-xl mt-0.5 flex-shrink-0 ${!isActive && 'grayscale'}`}>
            {String(node.icon)}
          </span>
        ) : Icon ? (
          <Icon
            className="w-5 h-5 mt-0.5 flex-shrink-0"
            style={{ color: isActive ? node.color : '#9ca3af' }}
          />
        ) : null}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <div
              className="font-medium text-sm"
              style={{ color: isActive ? node.color : '#9ca3af' }}
            >
              {node.label}
            </div>
            {hasRecommendedInputs && isActive && (
              <Lightbulb className="w-3 h-3 text-yellow-500" />
            )}
            {!isActive && <AlertCircle className="w-3 h-3 text-red-400" />}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">{node.description}</div>
        </div>
      </div>

      {/* 업로드된 이미지 썸네일 표시 (Image Input 노드만) */}
      {isImageInputNode && uploadedImage && (
        <ImagePreview
          uploadedImage={uploadedImage}
          uploadedFileName={uploadedFileName}
          onImageClick={onImageClick}
        />
      )}

      {/* 추천 연결 툴팁 */}
      {hasRecommendedInputs && isActive && (
        <RecommendedTooltip
          recommendedInputs={definition.recommendedInputs!}
          colorScheme={tooltipColorScheme}
        />
      )}
    </div>
  );
}
