import { X, Info, ArrowRight, Settings, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { getNodeDefinition } from '../../config/nodeDefinitions';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import type { Node } from 'reactflow';

interface NodeDetailPanelProps {
  selectedNode: Node | null;
  onClose: () => void;
  onUpdateNode: (nodeId: string, data: any) => void;
}

export default function NodeDetailPanel({ selectedNode, onClose, onUpdateNode }: NodeDetailPanelProps) {
  const [showParameters, setShowParameters] = useState(true);
  const [showExamples, setShowExamples] = useState(true);

  if (!selectedNode) {
    return (
      <div className="w-96 bg-gray-100 dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 p-6 flex items-center justify-center">
        <div className="text-center text-gray-500 dark:text-gray-400">
          <Info className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">노드를 선택하면</p>
          <p className="text-sm">상세 정보가 표시됩니다</p>
        </div>
      </div>
    );
  }

  const nodeType = selectedNode.type || '';
  const definition = getNodeDefinition(nodeType);

  if (!definition) {
    return (
      <div className="w-96 bg-white dark:bg-gray-800 border-l p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">알 수 없는 노드</h3>
          <Button onClick={onClose} variant="ghost" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-sm text-gray-500">이 노드 타입의 정보가 없습니다.</p>
      </div>
    );
  }

  const handleParameterChange = (paramName: string, value: any) => {
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

  return (
    <div className="w-96 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 overflow-y-auto">
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
          {definition.category === 'api' ? 'API 노드' : '제어 노드'}
        </p>
      </div>

      <div className="p-4 space-y-4">
        {/* Description */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Info className="w-4 h-4" />
              설명
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {definition.description}
            </p>
          </CardContent>
        </Card>

        {/* Inputs */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <ArrowRight className="w-4 h-4 rotate-180 text-blue-500" />
              입력 (Inputs)
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
              출력 (Outputs)
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
                  파라미터
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
                      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
                        {param.name}
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

                      {param.type === 'string' && (
                        <input
                          type="text"
                          value={currentValue}
                          onChange={(e) => handleParameterChange(param.name, e.target.value)}
                          className="w-full px-2 py-1 text-xs border rounded dark:bg-gray-700 dark:border-gray-600"
                        />
                      )}

                      {param.type === 'select' && (
                        <select
                          value={currentValue}
                          onChange={(e) => handleParameterChange(param.name, e.target.value)}
                          className="w-full px-2 py-1 text-xs border rounded dark:bg-gray-700 dark:border-gray-600"
                        >
                          {param.options?.map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>
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
                          <span className="text-xs">활성화</span>
                        </label>
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
                <CardTitle className="text-sm">💡 사용 예시</CardTitle>
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
      </div>
    </div>
  );
}
