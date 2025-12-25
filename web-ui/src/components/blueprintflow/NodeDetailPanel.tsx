import { X, Info, ArrowRight, Settings, ChevronDown, ChevronUp, ChevronLeft, ChevronRight, Lightbulb, Link, Image, FileImage, HelpCircle, Plus } from 'lucide-react';
import { useState, memo, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { getNodeDefinition } from '../../config/nodeDefinitions';
import { getRecommendedNodes, FEATURE_NODE_RECOMMENDATIONS } from '../../config/nodes/inputNodes';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { useWorkflowStore } from '../../store/workflowStore';
import type { Node } from 'reactflow';
import type { SelectOption, CheckboxOption } from '../../config/nodes/types';

// Helper to check if option is SelectOption object
const isSelectOption = (opt: string | SelectOption): opt is SelectOption => {
  return typeof opt === 'object' && 'value' in opt;
};

// Helper to check if option is CheckboxOption object
const isCheckboxOption = (opt: unknown): opt is CheckboxOption => {
  return typeof opt === 'object' && opt !== null && 'value' in opt && 'label' in opt;
};

interface NodeDetailPanelProps {
  selectedNode: Node | null;
  onClose: () => void;
  onUpdateNode: (nodeId: string, data: Record<string, unknown>) => void;
  onAddNode?: (nodeType: string) => void;  // 추천 노드 추가 콜백
}

const NodeDetailPanel = memo(function NodeDetailPanel({ selectedNode, onClose, onUpdateNode, onAddNode }: NodeDetailPanelProps) {
  const { t } = useTranslation();
  const [showParameters, setShowParameters] = useState(true);
  const [showExamples, setShowExamples] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showImageModal, setShowImageModal] = useState(false);

  // Get uploaded image from store
  const uploadedImage = useWorkflowStore((state) => state.uploadedImage);
  const uploadedFileName = useWorkflowStore((state) => state.uploadedFileName);

  // features 기반 추천 노드 계산 (ImageInput 노드일 때만)
  const featuresRecommendation = useMemo(() => {
    if (!selectedNode || selectedNode.type !== 'imageinput') return null;
    const features: string[] = selectedNode.data?.parameters?.features || [];
    if (features.length === 0) return null;

    const recommendedNodes = getRecommendedNodes(features);
    if (recommendedNodes.length === 0) return null;

    // 활성화된 features에 대한 설명 생성
    const descriptions = features
      .filter(f => FEATURE_NODE_RECOMMENDATIONS[f])
      .map(f => FEATURE_NODE_RECOMMENDATIONS[f].description);

    return {
      nodes: recommendedNodes,
      descriptions,
    };
  }, [selectedNode]);

  // Collapsed state - show only toggle button
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
  const definition = getNodeDefinition(nodeType);

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

  const handleParameterChange = (paramName: string, value: string | number | boolean | string[]) => {
    const currentData = selectedNode.data || {};
    const currentParams = currentData.parameters || {};

    onUpdateNode(selectedNode.id, {
      ...currentData,
      parameters: {
        ...currentParams,
        [paramName]: value,
      },
    });
  };

  // checkboxGroup 값 토글 핸들러
  const handleCheckboxToggle = (paramName: string, optionValue: string, currentValues: string[]) => {
    const newValues = currentValues.includes(optionValue)
      ? currentValues.filter(v => v !== optionValue)
      : [...currentValues, optionValue];
    handleParameterChange(paramName, newValues);
  };

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
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: definition.color }}
            />
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
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Info className="w-4 h-4" />
              {t('nodeDetail.description')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {definition.description}
            </p>
          </CardContent>
        </Card>

        {/* Image Preview - Only for ImageInput node */}
        {nodeType === 'imageinput' && (
          <Card className="border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 text-green-700 dark:text-green-300">
                <FileImage className="w-4 h-4" />
                {t('nodeDetail.currentImage')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {uploadedImage ? (
                <div className="space-y-2">
                  <div className="relative group">
                    <img
                      src={uploadedImage}
                      alt="Uploaded preview"
                      className="w-full h-auto rounded-lg border border-green-300 dark:border-green-700 max-h-48 object-contain bg-white cursor-pointer hover:opacity-80 transition-opacity"
                      onClick={() => setShowImageModal(true)}
                      title="클릭하여 확대"
                    />
                    {/* 클릭 힌트 */}
                    <div className="absolute bottom-2 right-2 bg-black/50 text-white text-[10px] px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                      🔍 클릭하여 확대
                    </div>
                  </div>
                  <div
                    className="flex items-center gap-2 text-xs text-green-600 dark:text-green-400 cursor-pointer hover:text-green-700"
                    onClick={() => setShowImageModal(true)}
                  >
                    <Image className="w-3 h-3" />
                    <span className="truncate font-medium">{uploadedFileName || t('nodeDetail.image')}</span>
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {t('nodeDetail.size')}: {Math.round(uploadedImage.length / 1024)} KB (base64)
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-400 dark:text-gray-500">
                  <Image className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">{t('nodeDetail.noImageUploaded')}</p>
                  <p className="text-xs mt-1">{t('nodeDetail.useUploadButton')}</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Recommended Nodes - Based on selected features */}
        {nodeType === 'imageinput' && featuresRecommendation && (
          <Card className="border-orange-200 dark:border-orange-800 bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 text-orange-700 dark:text-orange-300">
                <Lightbulb className="w-4 h-4" />
                📌 추천 노드
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* Description list */}
              <div className="space-y-1">
                {featuresRecommendation.descriptions.map((desc, idx) => (
                  <p key={idx} className="text-xs text-orange-800 dark:text-orange-200">
                    • {desc}
                  </p>
                ))}
              </div>

              {/* Node buttons */}
              <div className="flex flex-wrap gap-2">
                {featuresRecommendation.nodes.map((nodeTypeId) => {
                  const nodeDef = getNodeDefinition(nodeTypeId);
                  return (
                    <button
                      key={nodeTypeId}
                      onClick={() => onAddNode?.(nodeTypeId)}
                      disabled={!onAddNode}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full bg-white dark:bg-gray-700 border border-orange-300 dark:border-orange-600 text-orange-700 dark:text-orange-300 hover:bg-orange-100 dark:hover:bg-orange-800/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                    >
                      <Plus className="w-3 h-3" />
                      {nodeDef?.label || nodeTypeId}
                    </button>
                  );
                })}
              </div>

              {/* Tips */}
              <div className="flex items-start gap-2 p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <span className="text-orange-500">💡</span>
                <span className="text-xs text-orange-800 dark:text-orange-200">
                  선택한 기능에 필요한 노드입니다. 클릭하여 추가하세요.
                </span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Inputs */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <ArrowRight className="w-4 h-4 rotate-180 text-blue-500" />
              {t('nodeDetail.inputs')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {definition.inputs.map((input, idx) => (
              <div key={idx} className="border-l-2 border-blue-500 pl-3 py-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-blue-600 dark:text-blue-400">
                    {input.name}
                  </span>
                  <span className="text-xs text-gray-500">: {input.type}</span>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  {input.description}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Outputs */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <ArrowRight className="w-4 h-4 text-green-500" />
              {t('nodeDetail.outputs')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {definition.outputs.map((output, idx) => (
              <div key={idx} className="border-l-2 border-green-500 pl-3 py-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-green-600 dark:text-green-400">
                    {output.name}
                  </span>
                  <span className="text-xs text-gray-500">: {output.type}</span>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  {output.description}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Parameters */}
        {definition.parameters.length > 0 && (
          <Card>
            <CardHeader>
              <button
                onClick={() => setShowParameters(!showParameters)}
                className="w-full flex items-center justify-between cursor-pointer"
              >
                <CardTitle className="text-sm flex items-center gap-2">
                  <Settings className="w-4 h-4 text-purple-500" />
                  {t('nodeDetail.parameters')}
                </CardTitle>
                {showParameters ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>
            </CardHeader>
            {showParameters && (
              <CardContent className="space-y-3">
                {definition.parameters.map((param) => {
                  const currentValue =
                    selectedNode.data?.parameters?.[param.name] ?? param.default;

                  return (
                    <div key={param.name} className="space-y-1">
                      <label className="text-xs font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1">
                        {param.name}
                        {param.tooltip && (
                          <span className="group relative">
                            <HelpCircle className="w-3 h-3 text-gray-400 hover:text-blue-500 cursor-help" />
                            <span className="absolute z-50 hidden group-hover:block w-64 p-2 text-xs bg-gray-900 text-white rounded-lg shadow-lg -left-28 top-5">
                              {param.tooltip}
                            </span>
                          </span>
                        )}
                      </label>
                      <p className="text-xs text-gray-500">{param.description}</p>

                      {param.type === 'number' && (
                        <div className="flex items-center gap-2">
                          <input
                            type="range"
                            min={param.min}
                            max={param.max}
                            step={param.step}
                            value={currentValue}
                            onChange={(e) =>
                              handleParameterChange(param.name, parseFloat(e.target.value))
                            }
                            className="flex-1"
                          />
                          <span className="text-xs font-mono w-12 text-right">
                            {currentValue}
                          </span>
                        </div>
                      )}

                      {(param.type === 'string' || param.type === 'textarea') && (
                        <textarea
                          value={currentValue || ''}
                          onChange={(e) => handleParameterChange(param.name, e.target.value)}
                          onFocus={(e) => e.stopPropagation()}
                          onKeyDown={(e) => e.stopPropagation()}
                          onMouseDown={(e) => e.stopPropagation()}
                          placeholder={param.placeholder || t('nodeDetail.enterText')}
                          rows={param.type === 'textarea' ? 4 : 3}
                          className="w-full px-2 py-1 text-xs border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white resize-y min-h-[60px] nodrag nopan font-mono"
                        />
                      )}

                      {param.type === 'select' && (
                        <div className="space-y-2">
                          <select
                            value={currentValue}
                            onChange={(e) => handleParameterChange(param.name, e.target.value)}
                            className="w-full px-2 py-1 text-xs border rounded dark:bg-gray-700 dark:border-gray-600"
                          >
                            {param.options?.map((opt) => {
                              const value = isSelectOption(opt) ? opt.value : opt;
                              const label = isSelectOption(opt) ? opt.label : opt;
                              return (
                                <option key={value} value={value}>
                                  {label}
                                </option>
                              );
                            })}
                          </select>
                          {/* Show description for selected option */}
                          {param.options?.some(isSelectOption) && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 p-2 rounded border border-gray-200 dark:border-gray-600">
                              {(() => {
                                const selectedOpt = param.options?.find(
                                  (opt) => isSelectOption(opt) && opt.value === currentValue
                                );
                                if (selectedOpt && isSelectOption(selectedOpt)) {
                                  return (
                                    <div className="flex items-start gap-2">
                                      <HelpCircle className="w-3 h-3 mt-0.5 text-blue-500 flex-shrink-0" />
                                      <span>{selectedOpt.description}</span>
                                    </div>
                                  );
                                }
                                return null;
                              })()}
                            </div>
                          )}
                        </div>
                      )}

                      {param.type === 'boolean' && (
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={currentValue}
                            onChange={(e) =>
                              handleParameterChange(param.name, e.target.checked)
                            }
                          />
                          <span className="text-xs">{t('nodeDetail.enabled')}</span>
                        </label>
                      )}

                      {param.type === 'checkboxGroup' && (
                        <div className="space-y-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                          {param.options?.map((opt) => {
                            if (!isCheckboxOption(opt)) return null;
                            const isChecked = Array.isArray(currentValue)
                              ? currentValue.includes(opt.value)
                              : false;
                            return (
                              <div key={opt.value} className="group relative">
                                <label
                                  className={`flex items-center gap-2 p-1.5 rounded cursor-pointer transition-colors ${
                                    isChecked
                                      ? 'bg-blue-50 dark:bg-blue-900/30'
                                      : 'hover:bg-gray-100 dark:hover:bg-gray-600/50'
                                  }`}
                                >
                                  <input
                                    type="checkbox"
                                    checked={isChecked}
                                    onChange={() =>
                                      handleCheckboxToggle(
                                        param.name,
                                        opt.value,
                                        Array.isArray(currentValue) ? currentValue : []
                                      )
                                    }
                                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                  />
                                  <span className="text-sm">
                                    {opt.icon && <span className="mr-1">{opt.icon}</span>}
                                    {opt.label}
                                  </span>
                                  {opt.hint && (
                                    <span className="text-xs text-gray-400 ml-auto">
                                      {opt.hint}
                                    </span>
                                  )}
                                </label>
                                {/* Hover Tooltip */}
                                {opt.description && (
                                  <div className="absolute z-50 hidden group-hover:block w-72 p-3 text-xs bg-gray-900 text-white rounded-lg shadow-xl left-0 top-full mt-1 leading-relaxed">
                                    <div className="flex items-start gap-2">
                                      <span className="text-lg flex-shrink-0">{opt.icon}</span>
                                      <div>
                                        <div className="font-semibold text-blue-300 mb-1">{opt.label}</div>
                                        <div className="text-gray-200">{opt.description}</div>
                                      </div>
                                    </div>
                                    {/* Arrow */}
                                    <div className="absolute -top-1.5 left-4 w-3 h-3 bg-gray-900 rotate-45"></div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                          {/* 활성화된 기능 수 표시 */}
                          <div className="text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-600">
                            {Array.isArray(currentValue) ? currentValue.length : 0}개 기능 활성화
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            )}
          </Card>
        )}

        {/* Examples */}
        {definition.examples.length > 0 && (
          <Card>
            <CardHeader>
              <button
                onClick={() => setShowExamples(!showExamples)}
                className="w-full flex items-center justify-between cursor-pointer"
              >
                <CardTitle className="text-sm">💡 {t('nodeDetail.usageExample')}</CardTitle>
                {showExamples ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>
            </CardHeader>
            {showExamples && (
              <CardContent>
                <ul className="space-y-2">
                  {definition.examples.map((example, idx) => (
                    <li key={idx} className="text-xs text-gray-600 dark:text-gray-400 flex gap-2">
                      <span className="text-gray-400">•</span>
                      <span>{example}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            )}
          </Card>
        )}

        {/* Usage Tips */}
        {definition.usageTips && definition.usageTips.length > 0 && (
          <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 text-blue-900 dark:text-blue-300">
                <Lightbulb className="w-4 h-4" />
                💡 {t('nodeDetail.usageTip')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2.5">
                {definition.usageTips.map((tip, idx) => (
                  <li key={idx} className="text-xs text-blue-800 dark:text-blue-200 flex gap-2 leading-relaxed">
                    <span className="text-blue-400 mt-0.5">•</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Recommended Inputs */}
        {definition.recommendedInputs && definition.recommendedInputs.length > 0 && (
          <Card className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200 dark:border-green-800">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 text-green-900 dark:text-green-300">
                <Link className="w-4 h-4" />
                🔗 {t('nodeDetail.recommendedConnections')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {definition.recommendedInputs.map((rec, idx) => (
                  <div key={idx} className="border-l-2 border-green-500 pl-3 py-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs font-semibold text-green-700 dark:text-green-400">
                        {rec.from}
                      </span>
                      <ArrowRight className="w-3 h-3 text-green-600" />
                      <span className="font-mono text-xs text-green-600 dark:text-green-400">
                        {rec.field}
                      </span>
                    </div>
                    <p className="text-xs text-green-800 dark:text-green-200 leading-relaxed">
                      {rec.reason}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 이미지 확대 모달 */}
      {showImageModal && uploadedImage && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={() => setShowImageModal(false)}
        >
          <div
            className="relative max-w-[90vw] max-h-[90vh] bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 닫기 버튼 */}
            <button
              onClick={() => setShowImageModal(false)}
              className="absolute top-3 right-3 z-10 w-8 h-8 flex items-center justify-center bg-black/50 hover:bg-black/70 text-white rounded-full transition-colors"
              title="닫기 (ESC)"
            >
              ✕
            </button>
            {/* 이미지 */}
            <img
              src={uploadedImage}
              alt="Uploaded preview full"
              className="max-w-[85vw] max-h-[85vh] object-contain"
            />
            {/* 파일 정보 */}
            {uploadedFileName && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
                <div className="text-white text-sm font-medium">
                  📁 {uploadedFileName}
                </div>
                <div className="text-white/70 text-xs mt-1">
                  크기: {Math.round(uploadedImage.length / 1024)} KB (base64) | 클릭하여 닫기
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
});

export default NodeDetailPanel;
