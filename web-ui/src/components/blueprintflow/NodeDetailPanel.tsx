import { X, Info, Settings, ChevronLeft, ChevronRight, Link } from 'lucide-react';
import { useState, memo, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useNodeDefinitions } from '../../hooks/useNodeDefinitions';
import { getRecommendedNodes, FEATURE_NODE_RECOMMENDATIONS } from '../../config/nodes/inputNodes';
import { Button } from '../ui/Button';
import { useWorkflowStore } from '../../store/workflowStore';

import { ImagePreviewCard, ImageModal } from './node-detail/ImagePreviewCard';
import { RecommendedNodesCard } from './node-detail/RecommendedNodesCard';
import { ExecutionResultCard } from './node-detail/ExecutionResultCard';
import { ParametersCard } from './node-detail/ParametersCard';
import { DescriptionCard, NodeIOCards, ExamplesCard, UsageTipsCard, RecommendedInputsCard } from './node-detail/MetaCards';
import type { NodeDetailPanelProps } from './node-detail/types';

// Re-export types for consumers
export type { NodeDetailPanelProps } from './node-detail/types';

const NodeDetailPanel = memo(function NodeDetailPanel({
  selectedNode,
  onClose,
  onUpdateNode,
  onAddNode,
}: NodeDetailPanelProps) {
  const { t } = useTranslation();
  const [showParameters, setShowParameters] = useState(true);
  const [showExamples, setShowExamples] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showImageModal, setShowImageModal] = useState(false);

  const { getDefinition } = useNodeDefinitions();

  const uploadedImage = useWorkflowStore((state) => state.uploadedImage);
  const uploadedFileName = useWorkflowStore((state) => state.uploadedFileName);
  const uploadedGTFile = useWorkflowStore((state) => state.uploadedGTFile);
  const nodeStatuses = useWorkflowStore((state) => state.nodeStatuses);
  const currentNodeStatus = selectedNode ? nodeStatuses[selectedNode.id] : null;

  const featuresRecommendation = useMemo(() => {
    if (!selectedNode || selectedNode.type !== 'imageinput') return null;
    const features: string[] = selectedNode.data?.parameters?.features || [];
    if (features.length === 0) return null;

    const recommendedNodes = getRecommendedNodes(features);
    if (recommendedNodes.length === 0) return null;

    const descriptions = features
      .filter((f) => FEATURE_NODE_RECOMMENDATIONS[f])
      .map((f) => FEATURE_NODE_RECOMMENDATIONS[f].description);

    return { nodes: recommendedNodes, descriptions };
  }, [selectedNode]);

  // Collapsed state
  if (isCollapsed) {
    return (
      <div className="w-12 bg-gray-100 dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 relative flex flex-col items-center pt-4">
        <button
          onClick={() => setIsCollapsed(false)}
          className="absolute -left-3 top-4 z-10 w-6 h-6 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-full flex items-center justify-center shadow-md hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          title="Expand panel"
        >
          <ChevronLeft className="w-4 h-4 text-gray-600 dark:text-gray-300" />
        </button>
        <div className="mt-6 space-y-3">
          <div className="w-8 h-8 flex items-center justify-center rounded bg-blue-100 dark:bg-blue-900/30" title="Node Details">
            <Info className="w-4 h-4 text-blue-500" />
          </div>
          <div className="w-8 h-8 flex items-center justify-center rounded bg-purple-100 dark:bg-purple-900/30" title="Parameters">
            <Settings className="w-4 h-4 text-purple-500" />
          </div>
          <div className="w-8 h-8 flex items-center justify-center rounded bg-green-100 dark:bg-green-900/30" title="Connections">
            <Link className="w-4 h-4 text-green-500" />
          </div>
        </div>
      </div>
    );
  }

  if (!selectedNode) {
    return (
      <div className="w-96 bg-gray-100 dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 p-6 flex items-center justify-center relative">
        <button
          onClick={() => setIsCollapsed(true)}
          className="absolute -left-3 top-4 z-10 w-6 h-6 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-full flex items-center justify-center shadow-md hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          title="Collapse panel"
        >
          <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-300" />
        </button>
        <div className="text-center text-gray-500 dark:text-gray-400">
          <Info className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">{t('nodeDetail.selectNode')}</p>
          <p className="text-sm">{t('nodeDetail.showDetails')}</p>
        </div>
      </div>
    );
  }

  const nodeType = selectedNode.type || '';
  const definition = getDefinition(nodeType);

  if (!definition) {
    return (
      <div className="w-96 bg-white dark:bg-gray-800 border-l p-6 relative">
        <button
          onClick={() => setIsCollapsed(true)}
          className="absolute -left-3 top-4 z-10 w-6 h-6 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-full flex items-center justify-center shadow-md hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          title="Collapse panel"
        >
          <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-300" />
        </button>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">{t('nodeDetail.unknownNode')}</h3>
          <Button onClick={onClose} variant="ghost" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-sm text-gray-500">{t('nodeDetail.noNodeInfo')}</p>
      </div>
    );
  }

  return (
    <div className="w-96 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 overflow-y-auto relative">
      {/* Collapse Button */}
      <button
        onClick={() => setIsCollapsed(true)}
        className="absolute -left-3 top-4 z-20 w-6 h-6 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-full flex items-center justify-center shadow-md hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
        title="Collapse panel"
      >
        <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-300" />
      </button>

      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: definition.color }} />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {definition.label}
            </h3>
          </div>
          <Button onClick={onClose} variant="ghost" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {definition.category === 'control' ? t('nodeDetail.controlNode') : t('nodeDetail.apiNode')}
        </p>
      </div>

      <div className="p-4 space-y-4">
        {/* Description */}
        <DescriptionCard definition={definition} />

        {/* Image Preview - Only for ImageInput node */}
        {nodeType === 'imageinput' && (
          <ImagePreviewCard
            uploadedImage={uploadedImage}
            uploadedFileName={uploadedFileName}
            uploadedGTFile={uploadedGTFile}
            showImageModal={showImageModal}
            onShowModal={() => setShowImageModal(true)}
          />
        )}

        {/* Recommended Nodes */}
        {nodeType === 'imageinput' && featuresRecommendation && (
          <RecommendedNodesCard
            nodes={featuresRecommendation.nodes}
            descriptions={featuresRecommendation.descriptions}
            onAddNode={onAddNode}
          />
        )}

        {/* Inputs / Outputs */}
        <NodeIOCards definition={definition} />

        {/* Execution Result */}
        {currentNodeStatus && (
          <ExecutionResultCard
            nodeStatus={currentNodeStatus}
            uploadedImage={uploadedImage}
            uploadedFileName={uploadedFileName}
          />
        )}

        {/* Parameters */}
        {definition.parameters.length > 0 && (
          <ParametersCard
            definition={definition}
            selectedNode={selectedNode}
            nodeType={nodeType}
            showParameters={showParameters}
            onToggle={() => setShowParameters(!showParameters)}
            onUpdateNode={onUpdateNode}
          />
        )}

        {/* Examples */}
        <ExamplesCard
          definition={definition}
          showExamples={showExamples}
          onToggle={() => setShowExamples(!showExamples)}
        />

        {/* Usage Tips */}
        <UsageTipsCard definition={definition} />

        {/* Recommended Inputs */}
        <RecommendedInputsCard definition={definition} />
      </div>

      {/* Image Modal */}
      {showImageModal && uploadedImage && (
        <ImageModal
          uploadedImage={uploadedImage}
          uploadedFileName={uploadedFileName}
          onClose={() => setShowImageModal(false)}
        />
      )}
    </div>
  );
});

export default NodeDetailPanel;
