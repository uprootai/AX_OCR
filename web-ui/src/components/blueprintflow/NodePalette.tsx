/**
 * NodePalette Component
 * 노드 팔레트 메인 컴포넌트 - 드래그 앤 드롭 가능한 노드 목록
 *
 * 리팩토링: 2025-12-31
 * - 원본 1,024줄 -> 리팩토링 후 ~150줄
 * - 모듈화: node-palette/ 디렉토리로 분리
 *   - types.ts: 타입 정의
 *   - constants.ts: 노드 설정 상수
 *   - hooks/: useNodePalette, useContainerStatus
 *   - components/: NodeItem, NodeCategory, CollapsedView, ImagePreviewModal
 */

import { ChevronLeft, ChevronRight } from 'lucide-react';
import {
  useNodePalette,
  useContainerStatus,
  NodeCategory,
  ControlFlowCategory,
  CollapsedView,
  ImagePreviewModal,
} from './node-palette';
import type { NodePaletteProps } from './node-palette';

/**
 * NodePalette 메인 컴포넌트
 * 워크플로우 빌더에서 사용할 수 있는 노드 목록을 표시
 */
export default function NodePalette({
  onNodeDragStart,
  uploadedImage,
  uploadedFileName,
}: NodePaletteProps) {
  // 노드 팔레트 상태
  const {
    isCollapsed,
    setIsCollapsed,
    showImageModal,
    setShowImageModal,
    inputNodes,
    bomNodes,
    detectionNodes,
    ocrNodes,
    segmentationNodes,
    preprocessingNodes,
    analysisNodes,
    knowledgeNodes,
    aiNodes,
    controlNodes,
  } = useNodePalette();

  // 컨테이너 상태
  const { isNodeActive } = useContainerStatus();

  // 이미지 모달 열기 핸들러
  const handleImageClick = () => setShowImageModal(true);

  return (
    <div
      className={`${isCollapsed ? 'w-12' : 'w-64'} bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto transition-all duration-300 relative flex flex-col`}
    >
      {/* Toggle Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-3 top-4 z-10 w-6 h-6 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-full flex items-center justify-center shadow-md hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
        title={isCollapsed ? 'Expand palette' : 'Collapse palette'}
      >
        {isCollapsed ? (
          <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-300" />
        ) : (
          <ChevronLeft className="w-4 h-4 text-gray-600 dark:text-gray-300" />
        )}
      </button>

      {/* Collapsed View - Icons Only */}
      {isCollapsed ? (
        <CollapsedView />
      ) : (
        <div className="p-4 flex-1">
          <h2 className="text-lg font-semibold mb-4">Node Palette</h2>

          {/* Input Nodes */}
          <NodeCategory
            title="Input"
            emoji=""
            nodes={inputNodes}
            isNodeActive={isNodeActive}
            onNodeDragStart={onNodeDragStart}
            uploadedImage={uploadedImage}
            uploadedFileName={uploadedFileName}
            onImageClick={handleImageClick}
          />

          {/* BOM Nodes */}
          <NodeCategory
            title="BOM 생성"
            emoji=""
            nodes={bomNodes}
            isNodeActive={isNodeActive}
            onNodeDragStart={onNodeDragStart}
            tooltipColorScheme="purple"
          />

          {/* Detection Nodes */}
          <NodeCategory
            title="Detection"
            emoji=""
            nodes={detectionNodes}
            isNodeActive={isNodeActive}
            onNodeDragStart={onNodeDragStart}
            tooltipColorScheme="green"
          />

          {/* Segmentation Nodes */}
          <NodeCategory
            title="Segmentation"
            emoji=""
            nodes={segmentationNodes}
            isNodeActive={isNodeActive}
            onNodeDragStart={onNodeDragStart}
            tooltipColorScheme="purple"
          />

          {/* Analysis Nodes */}
          <NodeCategory
            title="Analysis"
            emoji=""
            nodes={analysisNodes}
            isNodeActive={isNodeActive}
            onNodeDragStart={onNodeDragStart}
            tooltipColorScheme="green"
          />

          {/* Knowledge Nodes */}
          <NodeCategory
            title="Knowledge"
            emoji=""
            nodes={knowledgeNodes}
            isNodeActive={isNodeActive}
            onNodeDragStart={onNodeDragStart}
            tooltipColorScheme="purple"
          />

          {/* AI Nodes */}
          <NodeCategory
            title="AI / LLM"
            emoji=""
            nodes={aiNodes}
            isNodeActive={isNodeActive}
            onNodeDragStart={onNodeDragStart}
            tooltipColorScheme="purple"
          />

          {/* Preprocessing Nodes */}
          <NodeCategory
            title="Preprocessing"
            emoji=""
            nodes={preprocessingNodes}
            isNodeActive={isNodeActive}
            onNodeDragStart={onNodeDragStart}
            tooltipColorScheme="red"
          />

          {/* OCR Nodes */}
          <NodeCategory
            title="OCR"
            emoji=""
            nodes={ocrNodes}
            isNodeActive={isNodeActive}
            onNodeDragStart={onNodeDragStart}
            tooltipColorScheme="cyan"
          />

          {/* Control Nodes - Always at the end */}
          <ControlFlowCategory nodes={controlNodes} onNodeDragStart={onNodeDragStart} />
        </div>
      )}

      {/* 이미지 확대 모달 */}
      {showImageModal && uploadedImage && (
        <ImagePreviewModal
          uploadedImage={uploadedImage}
          uploadedFileName={uploadedFileName}
          onClose={() => setShowImageModal(false)}
        />
      )}
    </div>
  );
}
