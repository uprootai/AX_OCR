import { PlayCircle, CheckCircle2, XCircle, Clock } from 'lucide-react';
import DetectionResultCard from '../DetectionResultCard';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';

interface NodeStatus {
  status: 'pending' | 'running' | 'completed' | 'failed';
  error?: string;
  message?: string;
  elapsedSeconds?: number;
  output?: {
    detections?: unknown[];
    dimensions?: unknown[];
    tables?: unknown[];
    texts?: unknown[];
    [key: string]: unknown;
  };
}

interface ExecutionResultCardProps {
  nodeStatus: NodeStatus;
  uploadedImage: string | null;
  uploadedFileName: string | null;
}

export function ExecutionResultCard({ nodeStatus, uploadedImage, uploadedFileName }: ExecutionResultCardProps) {
  const borderColor =
    nodeStatus.status === 'completed' ? 'border-l-green-500 bg-green-50 dark:bg-green-900/20' :
    nodeStatus.status === 'failed' ? 'border-l-red-500 bg-red-50 dark:bg-red-900/20' :
    nodeStatus.status === 'running' ? 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/20' :
    'border-l-gray-300';

  return (
    <Card className={`border-l-4 ${borderColor}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          {nodeStatus.status === 'completed' && <CheckCircle2 className="w-4 h-4 text-green-500" />}
          {nodeStatus.status === 'failed' && <XCircle className="w-4 h-4 text-red-500" />}
          {nodeStatus.status === 'running' && <Clock className="w-4 h-4 text-blue-500 animate-spin" />}
          {nodeStatus.status === 'pending' && <PlayCircle className="w-4 h-4 text-gray-400" />}
          실행 결과
          {nodeStatus.elapsedSeconds && !Array.isArray(nodeStatus.output?.detections) && (
            <span className="text-xs text-gray-500 ml-auto">
              {nodeStatus.elapsedSeconds.toFixed(1)}초
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        {nodeStatus.status === 'failed' && nodeStatus.error && (
          <div className="p-2 bg-red-100 dark:bg-red-900/40 rounded text-red-700 dark:text-red-300">
            ❌ {nodeStatus.error}
          </div>
        )}
        {nodeStatus.status === 'completed' && nodeStatus.output && (
          <>
            {Array.isArray(nodeStatus.output.detections) && nodeStatus.output.detections.length > 0 ? (
              <DetectionResultCard
                nodeStatus={nodeStatus}
                uploadedImage={uploadedImage}
                uploadedFileName={uploadedFileName}
              />
            ) : (
              <div className="space-y-2">
                {Array.isArray(nodeStatus.output.dimensions) && nodeStatus.output.dimensions.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium">📏 치수:</span>
                    <span>{nodeStatus.output.dimensions.length}개</span>
                  </div>
                )}
                {Array.isArray(nodeStatus.output.tables) && nodeStatus.output.tables.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium">📊 테이블:</span>
                    <span>{nodeStatus.output.tables.length}개</span>
                  </div>
                )}
                {Array.isArray(nodeStatus.output.texts) && nodeStatus.output.texts.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium">📝 텍스트:</span>
                    <span>{nodeStatus.output.texts.length}개</span>
                  </div>
                )}
                <details className="mt-2">
                  <summary className="cursor-pointer text-blue-600 dark:text-blue-400 hover:underline">
                    JSON 데이터 보기
                  </summary>
                  <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-auto max-h-40">
                    {JSON.stringify(nodeStatus.output, null, 2).slice(0, 2000)}
                    {JSON.stringify(nodeStatus.output).length > 2000 && '...'}
                  </pre>
                </details>
              </div>
            )}
          </>
        )}
        {nodeStatus.status === 'running' && (
          <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
            <div className="animate-pulse">실행 중...</div>
            {nodeStatus.message && <span>({nodeStatus.message})</span>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
