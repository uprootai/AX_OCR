import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';

interface NodeResult {
  nodeId: string;
  nodeType: string;
  status: 'success' | 'error' | 'pending' | 'running';
  executionTime?: number;
  output?: any;
}

interface ResultSummaryCardProps {
  results: NodeResult[];
  totalExecutionTime?: number;
}

export default function ResultSummaryCard({
  results,
  totalExecutionTime,
}: ResultSummaryCardProps) {
  const successCount = results.filter((r) => r.status === 'success').length;
  const errorCount = results.filter((r) => r.status === 'error').length;
  const pendingCount = results.filter((r) => r.status === 'pending').length;

  // Extract summary statistics from results
  const ocrStats = {
    dimensions: 0,
    gdt: 0,
    textBlocks: 0,
  };

  const segmentationStats = {
    components: 0,
    graphNodes: 0,
  };

  const toleranceStats = {
    score: 0,
    difficulty: '',
  };

  results.forEach((result) => {
    const output = result.output;
    if (!output) return;

    // OCR stats
    if (output.dimensions) {
      ocrStats.dimensions += Array.isArray(output.dimensions)
        ? output.dimensions.length
        : 0;
    }
    if (output.gdt) {
      ocrStats.gdt += Array.isArray(output.gdt) ? output.gdt.length : 0;
    }
    if (output.text?.total_blocks !== undefined) {
      ocrStats.textBlocks += output.text.total_blocks;
    }

    // Segmentation stats
    if (output.num_components !== undefined) {
      segmentationStats.components += output.num_components;
    }
    if (output.graph?.nodes !== undefined) {
      segmentationStats.graphNodes += output.graph.nodes;
    }

    // Tolerance stats
    if (output.manufacturability) {
      toleranceStats.score = output.manufacturability.score;
      toleranceStats.difficulty = output.manufacturability.difficulty;
    }
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'running':
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const hasOCRData = ocrStats.dimensions > 0 || ocrStats.gdt > 0;
  const hasSegmentationData = segmentationStats.components > 0;
  const hasToleranceData = toleranceStats.score > 0;

  return (
    <Card>
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Pipeline Summary</h3>
          {totalExecutionTime !== undefined && (
            <Badge variant="outline" className="text-xs">
              {(totalExecutionTime / 1000).toFixed(2)}s
            </Badge>
          )}
        </div>

        {/* Execution Status */}
        <div className="flex gap-3 text-xs">
          <div className="flex items-center gap-1">
            <CheckCircle className="w-3 h-3 text-green-500" />
            <span className="text-green-700 dark:text-green-300">
              {successCount} success
            </span>
          </div>
          {errorCount > 0 && (
            <div className="flex items-center gap-1">
              <XCircle className="w-3 h-3 text-red-500" />
              <span className="text-red-700 dark:text-red-300">
                {errorCount} failed
              </span>
            </div>
          )}
          {pendingCount > 0 && (
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-yellow-500" />
              <span className="text-yellow-700 dark:text-yellow-300">
                {pendingCount} pending
              </span>
            </div>
          )}
        </div>

        {/* Results Summary */}
        <div className="grid grid-cols-3 gap-2">
          {/* OCR Summary */}
          {hasOCRData && (
            <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
              <div className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">
                OCR
              </div>
              <div className="text-xs text-blue-700 dark:text-blue-300 space-y-0.5">
                <div>Dims: {ocrStats.dimensions}</div>
                <div>GD&T: {ocrStats.gdt}</div>
                {ocrStats.textBlocks > 0 && (
                  <div>Blocks: {ocrStats.textBlocks}</div>
                )}
              </div>
            </div>
          )}

          {/* Segmentation Summary */}
          {hasSegmentationData && (
            <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
              <div className="text-xs font-semibold text-green-900 dark:text-green-100 mb-1">
                Segmentation
              </div>
              <div className="text-xs text-green-700 dark:text-green-300 space-y-0.5">
                <div>Components: {segmentationStats.components}</div>
                {segmentationStats.graphNodes > 0 && (
                  <div>Graph: {segmentationStats.graphNodes} nodes</div>
                )}
              </div>
            </div>
          )}

          {/* Tolerance Summary */}
          {hasToleranceData && (
            <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200 dark:border-orange-800">
              <div className="text-xs font-semibold text-orange-900 dark:text-orange-100 mb-1">
                Tolerance
              </div>
              <div className="text-xs text-orange-700 dark:text-orange-300 space-y-0.5">
                <div>Score: {(toleranceStats.score * 100).toFixed(0)}%</div>
                <div>Level: {toleranceStats.difficulty}</div>
              </div>
            </div>
          )}
        </div>

        {/* Node Results List */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground">
            Node Results
          </div>
          <div className="space-y-1">
            {results.map((result) => (
              <div
                key={result.nodeId}
                className="flex items-center justify-between p-1.5 rounded bg-accent/50 text-xs"
              >
                <div className="flex items-center gap-2">
                  {getStatusIcon(result.status)}
                  <span className="font-medium">{result.nodeType}</span>
                </div>
                {result.executionTime !== undefined && (
                  <span className="text-muted-foreground">
                    {(result.executionTime / 1000).toFixed(2)}s
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}
