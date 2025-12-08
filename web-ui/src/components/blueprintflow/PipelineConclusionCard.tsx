import { useMemo } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import {
  Target,
  Ruler,
  AlertCircle,
  CheckCircle2,
  Layers,
  Boxes,
  ClipboardList,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

// Types for node outputs
interface Detection {
  class_name?: string;
  class?: string;
  label?: string;
  confidence?: number;
  bbox?: number[];
}

interface Dimension {
  type?: string;
  text?: string;
  value?: string;
  raw_text?: string;
  unit?: string;
}

interface GDTItem {
  symbol?: string;
  value?: string;
  datum?: string;
  tolerance?: string;
}

interface PIDSymbol {
  class_name?: string;
  symbol_type?: string;
  confidence?: number;
}

interface NodeOutput {
  // YOLO outputs
  detections?: Detection[];
  predictions?: Detection[];
  objects?: Detection[];

  // OCR outputs
  dimensions?: Dimension[];
  gdt?: GDTItem[];
  ocr_results?: Array<{ text: string; confidence?: number }>;
  text?: string | { text?: string; total_blocks?: number };
  texts?: string[];

  // P&ID outputs
  symbols?: PIDSymbol[];
  lines?: Array<{ line_id?: string; type?: string }>;
  connections?: Array<{ from?: string; to?: string }>;
  bom?: Array<{ item?: string; quantity?: number }>;
  violations?: Array<{ rule?: string; message?: string }>;

  // General
  [key: string]: unknown;
}

interface NodeStatus {
  node_id: string;
  node_type?: string;
  status: string;
  output?: NodeOutput;
}

interface ExecutionResult {
  status: string;
  execution_time_ms?: number;
  node_statuses?: NodeStatus[];
  final_output?: Record<string, NodeOutput>;
}

interface PipelineConclusionCardProps {
  executionResult: ExecutionResult;
  nodes: Array<{ id: string; type?: string; data?: { label?: string } }>;
}

export default function PipelineConclusionCard({
  executionResult,
  nodes,
}: PipelineConclusionCardProps) {
  const { t } = useTranslation();

  // Extract and aggregate all results
  const conclusion = useMemo(() => {
    const result = {
      // Detection results
      detectedObjects: [] as Array<{ name: string; confidence: number; source: string }>,

      // OCR results
      dimensions: [] as Array<{ type: string; value: string; source: string }>,
      gdtSymbols: [] as Array<{ symbol: string; value: string; datum: string }>,
      textBlocks: [] as string[],

      // P&ID results
      pidSymbols: [] as Array<{ name: string; confidence: number }>,
      pidConnections: 0,
      pidViolations: [] as Array<{ rule: string; message: string }>,
      bomItems: [] as Array<{ item: string; quantity: number }>,

      // Summary counts
      totalDetections: 0,
      totalDimensions: 0,
      totalGDT: 0,
      totalTexts: 0,
    };

    if (!executionResult.node_statuses) return result;

    executionResult.node_statuses.forEach((nodeStatus) => {
      const node = nodes.find((n) => n.id === nodeStatus.node_id);
      const nodeType = node?.type || nodeStatus.node_type || 'unknown';
      const nodeName = node?.data?.label || nodeType;
      const output = nodeStatus.output || executionResult.final_output?.[nodeStatus.node_id];

      if (!output) return;

      // Extract YOLO detections
      const detections = output.detections || output.predictions || output.objects;
      if (Array.isArray(detections)) {
        detections.forEach((det) => {
          const name = det.class_name || det.class || det.label || 'unknown';
          const confidence = det.confidence || 0;
          result.detectedObjects.push({ name, confidence, source: nodeName });
          result.totalDetections++;
        });
      }

      // Extract OCR dimensions
      if (Array.isArray(output.dimensions)) {
        output.dimensions.forEach((dim) => {
          const type = dim.type || 'linear';
          const value = dim.text || dim.value || dim.raw_text || '';
          if (value) {
            result.dimensions.push({ type, value, source: nodeName });
            result.totalDimensions++;
          }
        });
      }

      // Extract GD&T
      if (Array.isArray(output.gdt)) {
        output.gdt.forEach((g) => {
          result.gdtSymbols.push({
            symbol: g.symbol || '',
            value: g.value || g.tolerance || '',
            datum: g.datum || '',
          });
          result.totalGDT++;
        });
      }

      // Extract OCR texts
      if (Array.isArray(output.ocr_results)) {
        output.ocr_results.forEach((r) => {
          if (r.text) {
            result.textBlocks.push(r.text);
            result.totalTexts++;
          }
        });
      }
      if (Array.isArray(output.texts)) {
        output.texts.forEach((text) => {
          result.textBlocks.push(text);
          result.totalTexts++;
        });
      }
      if (typeof output.text === 'string' && output.text) {
        result.textBlocks.push(output.text);
        result.totalTexts++;
      }

      // Extract P&ID symbols
      if (Array.isArray(output.symbols)) {
        output.symbols.forEach((sym) => {
          result.pidSymbols.push({
            name: sym.class_name || sym.symbol_type || 'unknown',
            confidence: sym.confidence || 0,
          });
        });
      }

      // Extract P&ID connections
      if (Array.isArray(output.connections)) {
        result.pidConnections += output.connections.length;
      }

      // Extract P&ID violations
      if (Array.isArray(output.violations)) {
        output.violations.forEach((v) => {
          result.pidViolations.push({
            rule: v.rule || 'unknown',
            message: v.message || '',
          });
        });
      }

      // Extract BOM
      if (Array.isArray(output.bom)) {
        output.bom.forEach((b) => {
          result.bomItems.push({
            item: b.item || 'unknown',
            quantity: b.quantity || 1,
          });
        });
      }
    });

    return result;
  }, [executionResult, nodes]);

  // Group detections by class
  const groupedDetections = useMemo(() => {
    const groups: Record<string, { count: number; avgConfidence: number }> = {};
    conclusion.detectedObjects.forEach((obj) => {
      if (!groups[obj.name]) {
        groups[obj.name] = { count: 0, avgConfidence: 0 };
      }
      groups[obj.name].count++;
      groups[obj.name].avgConfidence += obj.confidence;
    });
    Object.keys(groups).forEach((key) => {
      groups[key].avgConfidence /= groups[key].count;
    });
    return groups;
  }, [conclusion.detectedObjects]);

  // Group dimensions by type
  const groupedDimensions = useMemo(() => {
    const groups: Record<string, string[]> = {};
    conclusion.dimensions.forEach((dim) => {
      if (!groups[dim.type]) {
        groups[dim.type] = [];
      }
      groups[dim.type].push(dim.value);
    });
    return groups;
  }, [conclusion.dimensions]);

  const hasData =
    conclusion.totalDetections > 0 ||
    conclusion.totalDimensions > 0 ||
    conclusion.totalGDT > 0 ||
    conclusion.pidSymbols.length > 0 ||
    conclusion.bomItems.length > 0;

  if (!hasData) {
    return null;
  }

  return (
    <Card className="mt-4 border-2 border-blue-200 dark:border-blue-800">
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b pb-3">
          <div className="flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {t('blueprintflow.conclusion', '분석 결론')}
            </h3>
          </div>
          <Badge variant="default" className="bg-blue-600">
            {t('blueprintflow.analysisComplete', '분석 완료')}
          </Badge>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {conclusion.totalDetections > 0 && (
            <div className="flex items-center gap-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <Target className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              <div>
                <div className="text-xs text-purple-600 dark:text-purple-400">{t('blueprintflow.detectedObjects', '검출 객체')}</div>
                <div className="text-lg font-bold text-purple-700 dark:text-purple-300">{conclusion.totalDetections}</div>
              </div>
            </div>
          )}
          {conclusion.totalDimensions > 0 && (
            <div className="flex items-center gap-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <Ruler className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <div>
                <div className="text-xs text-blue-600 dark:text-blue-400">{t('blueprintflow.dimensions', '치수')}</div>
                <div className="text-lg font-bold text-blue-700 dark:text-blue-300">{conclusion.totalDimensions}</div>
              </div>
            </div>
          )}
          {conclusion.totalGDT > 0 && (
            <div className="flex items-center gap-2 p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <Layers className="w-4 h-4 text-green-600 dark:text-green-400" />
              <div>
                <div className="text-xs text-green-600 dark:text-green-400">GD&T</div>
                <div className="text-lg font-bold text-green-700 dark:text-green-300">{conclusion.totalGDT}</div>
              </div>
            </div>
          )}
          {conclusion.pidSymbols.length > 0 && (
            <div className="flex items-center gap-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <Boxes className="w-4 h-4 text-orange-600 dark:text-orange-400" />
              <div>
                <div className="text-xs text-orange-600 dark:text-orange-400">{t('blueprintflow.pidSymbols', 'P&ID 심볼')}</div>
                <div className="text-lg font-bold text-orange-700 dark:text-orange-300">{conclusion.pidSymbols.length}</div>
              </div>
            </div>
          )}
        </div>

        {/* Detected Objects Detail */}
        {Object.keys(groupedDetections).length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-700 dark:text-gray-300">
              <Target className="w-4 h-4" />
              {t('blueprintflow.detectedObjectsList', '검출된 객체 목록')}
            </h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(groupedDetections).map(([name, data]) => (
                <Badge
                  key={name}
                  variant="outline"
                  className="flex items-center gap-1 px-2 py-1"
                >
                  <span className="font-medium">{name}</span>
                  <span className="text-xs bg-gray-200 dark:bg-gray-700 px-1.5 rounded">
                    {data.count}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({(data.avgConfidence * 100).toFixed(0)}%)
                  </span>
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Dimensions Detail */}
        {Object.keys(groupedDimensions).length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-700 dark:text-gray-300">
              <Ruler className="w-4 h-4" />
              {t('blueprintflow.recognizedDimensions', '인식된 치수')}
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {Object.entries(groupedDimensions).map(([type, values]) => (
                <div
                  key={type}
                  className="p-2 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1 capitalize">
                    {type} ({values.length})
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {values.slice(0, 10).map((val, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded"
                      >
                        {val}
                      </span>
                    ))}
                    {values.length > 10 && (
                      <span className="text-xs text-gray-500">
                        +{values.length - 10} more
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* GD&T Detail */}
        {conclusion.gdtSymbols.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-700 dark:text-gray-300">
              <Layers className="w-4 h-4" />
              {t('blueprintflow.gdtSymbols', 'GD&T 기호')}
            </h4>
            <div className="flex flex-wrap gap-2">
              {conclusion.gdtSymbols.slice(0, 15).map((gdt, idx) => (
                <Badge key={idx} variant="outline" className="px-2 py-1">
                  <span className="font-mono">{gdt.symbol}</span>
                  {gdt.value && <span className="ml-1">{gdt.value}</span>}
                  {gdt.datum && <span className="ml-1 text-gray-500">({gdt.datum})</span>}
                </Badge>
              ))}
              {conclusion.gdtSymbols.length > 15 && (
                <span className="text-xs text-gray-500 self-center">
                  +{conclusion.gdtSymbols.length - 15} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* P&ID Analysis */}
        {(conclusion.pidSymbols.length > 0 || conclusion.bomItems.length > 0) && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-700 dark:text-gray-300">
              <Boxes className="w-4 h-4" />
              {t('blueprintflow.pidAnalysis', 'P&ID 분석 결과')}
            </h4>

            {conclusion.pidSymbols.length > 0 && (
              <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                <div className="text-xs font-medium text-orange-600 dark:text-orange-400 mb-1">
                  {t('blueprintflow.detectedSymbols', '검출된 심볼')}
                </div>
                <div className="flex flex-wrap gap-1">
                  {conclusion.pidSymbols.slice(0, 20).map((sym, idx) => (
                    <span
                      key={idx}
                      className="text-xs px-1.5 py-0.5 bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300 rounded"
                    >
                      {sym.name} ({(sym.confidence * 100).toFixed(0)}%)
                    </span>
                  ))}
                  {conclusion.pidSymbols.length > 20 && (
                    <span className="text-xs text-gray-500">
                      +{conclusion.pidSymbols.length - 20} more
                    </span>
                  )}
                </div>
              </div>
            )}

            {conclusion.bomItems.length > 0 && (
              <div className="p-2 bg-teal-50 dark:bg-teal-900/20 rounded-lg">
                <div className="text-xs font-medium text-teal-600 dark:text-teal-400 mb-1">
                  {t('blueprintflow.bomItems', 'BOM 항목')}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-1">
                  {conclusion.bomItems.slice(0, 12).map((item, idx) => (
                    <div
                      key={idx}
                      className="text-xs flex justify-between px-2 py-1 bg-teal-100 dark:bg-teal-900 rounded"
                    >
                      <span>{item.item}</span>
                      <span className="font-bold">x{item.quantity}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {conclusion.pidConnections > 0 && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {t('blueprintflow.connectionsFound', '연결 감지')}: {conclusion.pidConnections}
              </div>
            )}
          </div>
        )}

        {/* Violations / Warnings */}
        {conclusion.pidViolations.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold flex items-center gap-2 text-red-600 dark:text-red-400">
              <AlertCircle className="w-4 h-4" />
              {t('blueprintflow.violations', '설계 규칙 위반')} ({conclusion.pidViolations.length})
            </h4>
            <div className="space-y-1">
              {conclusion.pidViolations.slice(0, 5).map((v, idx) => (
                <div
                  key={idx}
                  className="text-xs p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded"
                >
                  <span className="font-medium text-red-700 dark:text-red-300">{v.rule}:</span>{' '}
                  <span className="text-red-600 dark:text-red-400">{v.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Overall Status */}
        <div className="pt-3 border-t flex items-center justify-between">
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-medium">
              {t('blueprintflow.analysisSuccessful', '분석이 성공적으로 완료되었습니다')}
            </span>
          </div>
          <div className="text-sm text-gray-500">
            {executionResult.execution_time_ms && (
              <span>
                {t('blueprintflow.totalTime', '총 소요 시간')}: {(executionResult.execution_time_ms / 1000).toFixed(2)}s
              </span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
