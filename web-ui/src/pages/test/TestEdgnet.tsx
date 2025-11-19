import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { FileUploadSection } from '../../components/upload/FileUploadSection';
import JSONViewer from '../../components/debug/JSONViewer';
import RequestInspector from '../../components/debug/RequestInspector';
import RequestTimeline from '../../components/debug/RequestTimeline';
import ErrorPanel from '../../components/debug/ErrorPanel';
import SegmentationVisualization from '../../components/debug/SegmentationVisualization';
import EdgnetGuide from '../../components/guides/EdgnetGuide';
import { edgnetApi } from '../../lib/api';
import { useMonitoringStore } from '../../store/monitoringStore';
import { Loader2, Play, Network, BookOpen } from 'lucide-react';
import type { SegmentationResult, RequestTrace } from '../../types/api';

export default function TestEdgnet() {
  const [file, setFile] = useState<File | null>(null);
  const [showGuide, setShowGuide] = useState(true);
  const [options, setOptions] = useState({
    vectorize: true,
    visualize: false,
  });
  const [result, setResult] = useState<SegmentationResult | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<RequestTrace | null>(null);

  const { traces, addTrace } = useMonitoringStore();
  const edgnetTraces = traces.filter((t) => t.endpoint.includes('segment') || t.endpoint.includes('edgnet'));

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      const startTime = Date.now();
      const traceId = `edgnet-${Date.now()}`;

      try {
        const response = await edgnetApi.segment(file, options);
        const duration = Date.now() - startTime;

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint: '/api/v1/segment',
          method: 'POST',
          status: 200,
          duration,
          request: {
            file: file.name,
            options,
          },
          response,
        };

        addTrace(trace);
        setSelectedTrace(trace);
        return response.data;
      } catch (error: any) {
        const duration = Date.now() - startTime;

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint: '/api/v1/segment',
          method: 'POST',
          status: error.response?.status || 0,
          duration,
          request: {
            file: file.name,
            options,
          },
          response: error.response?.data || null,
          error: {
            status: error.response?.status || 0,
            code: error.response?.status?.toString() || 'NETWORK_ERROR',
            message: error.response?.data?.detail || error.message,
            details: error.response?.data,
          },
        };

        addTrace(trace);
        setSelectedTrace(trace);
        throw error;
      }
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleTest = () => {
    if (!file) return;
    setResult(null);
    mutation.mutate(file);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <Network className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">EDGNet API Test</h1>
          </div>
          <Button
            variant={showGuide ? 'default' : 'outline'}
            onClick={() => setShowGuide(!showGuide)}
          >
            <BookOpen className="w-4 h-4 mr-2" />
            {showGuide ? '가이드 숨기기' : '가이드 보기'}
          </Button>
        </div>
        <p className="text-muted-foreground">
          도면 이미지를 세그멘테이션하고 그래프 구조로 변환합니다.
        </p>
      </div>

      {/* Usage Guide */}
      {showGuide && <EdgnetGuide />}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left Column: Test Configuration */}
        <div className="space-y-6">
          {/* File Upload */}
          <Card>
            <CardHeader>
              <CardTitle>1. 파일 업로드</CardTitle>
            </CardHeader>
            <CardContent>
              <FileUploadSection
                onFileSelect={setFile}
                currentFile={file}
                accept={{ 'image/*': ['.png', '.jpg', '.jpeg'], 'application/pdf': ['.pdf'] }}
                maxSize={10 * 1024 * 1024}
                disabled={mutation.isPending}
                showSamples={true}
              />
            </CardContent>
          </Card>

          {/* Options */}
          <Card>
            <CardHeader>
              <CardTitle>2. 세그멘테이션 옵션</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.vectorize}
                  onChange={(e) =>
                    setOptions({ ...options, vectorize: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <div>
                  <p className="font-medium">벡터화 (Vectorization)</p>
                  <p className="text-sm text-muted-foreground">
                    세그먼트를 베지어 곡선으로 변환합니다.
                  </p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.visualize}
                  onChange={(e) =>
                    setOptions({ ...options, visualize: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <div>
                  <p className="font-medium">시각화 (Visualization)</p>
                  <p className="text-sm text-muted-foreground">
                    세그멘테이션 결과를 이미지로 시각화합니다.
                  </p>
                </div>
              </label>
            </CardContent>
          </Card>

          {/* Execute */}
          <Card>
            <CardHeader>
              <CardTitle>3. 실행</CardTitle>
            </CardHeader>
            <CardContent>
              <Button
                onClick={handleTest}
                disabled={!file || mutation.isPending}
                className="w-full"
                size="lg"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 mr-2" />
                    세그멘테이션 실행
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Request Timeline */}
          {edgnetTraces.length > 0 && (
            <RequestTimeline
              traces={edgnetTraces}
              onSelectTrace={setSelectedTrace}
              maxItems={10}
            />
          )}
        </div>

        {/* Right Column: Results */}
        <div className="space-y-6">
          {/* Error */}
          {mutation.isError && (
            <ErrorPanel
              error={{
                status: (mutation.error as any)?.response?.status || 0,
                code: (mutation.error as any)?.response?.status?.toString() || 'ERROR',
                message:
                  (mutation.error as any)?.response?.data?.detail ||
                  (mutation.error as any)?.message ||
                  'An error occurred',
                details: (mutation.error as any)?.response?.data,
              }}
              onRetry={handleTest}
            />
          )}

          {/* Results */}
          {result && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>세그멘테이션 결과</CardTitle>
                </CardHeader>
                <CardContent>
                  {/* Summary Stats */}
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="text-center p-4 bg-accent rounded-lg">
                      <p className="text-2xl font-bold">{result.num_components}</p>
                      <p className="text-sm text-muted-foreground">Components</p>
                    </div>
                    <div className="text-center p-4 bg-accent rounded-lg">
                      <p className="text-2xl font-bold">{result.graph?.nodes || 0}</p>
                      <p className="text-sm text-muted-foreground">Graph Nodes</p>
                    </div>
                  </div>

                  {/* Classifications */}
                  <div className="mb-6">
                    <h4 className="font-semibold mb-3">Component Classification</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-background border rounded">
                        <div className="flex items-center gap-2">
                          <Badge>Contours</Badge>
                        </div>
                        <span className="font-semibold">{result.classifications?.contour || 0}</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-background border rounded">
                        <div className="flex items-center gap-2">
                          <Badge>Text</Badge>
                        </div>
                        <span className="font-semibold">{result.classifications?.text || 0}</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-background border rounded">
                        <div className="flex items-center gap-2">
                          <Badge>Dimensions</Badge>
                        </div>
                        <span className="font-semibold">{result.classifications?.dimension || 0}</span>
                      </div>
                    </div>
                  </div>

                  {/* Graph Info */}
                  {result.graph && (
                    <div className="mb-6">
                      <h4 className="font-semibold mb-3">Graph Structure</h4>
                      <div className="grid grid-cols-3 gap-3">
                        <div className="text-center p-3 bg-background border rounded">
                          <p className="text-lg font-bold">{result.graph.nodes}</p>
                          <p className="text-xs text-muted-foreground">Nodes</p>
                        </div>
                        <div className="text-center p-3 bg-background border rounded">
                          <p className="text-lg font-bold">{result.graph.edges}</p>
                          <p className="text-xs text-muted-foreground">Edges</p>
                        </div>
                        <div className="text-center p-3 bg-background border rounded">
                          <p className="text-lg font-bold">{result.graph.avg_degree.toFixed(2)}</p>
                          <p className="text-xs text-muted-foreground">Avg Degree</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Vectorization Info */}
                  {result.vectorization && (
                    <div className="mb-6">
                      <h4 className="font-semibold mb-3">Vectorization</h4>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="text-center p-3 bg-background border rounded">
                          <p className="text-lg font-bold">{result.vectorization.num_bezier_curves}</p>
                          <p className="text-xs text-muted-foreground">Bezier Curves</p>
                        </div>
                        <div className="text-center p-3 bg-background border rounded">
                          <p className="text-lg font-bold">{result.vectorization.total_length.toFixed(1)}</p>
                          <p className="text-xs text-muted-foreground">Total Length</p>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Segmentation Visualization - only for images */}
              {file && file.type.startsWith('image/') && (
                <SegmentationVisualization
                  imageFile={file}
                  segmentationResult={result}
                />
              )}

              <JSONViewer data={result} title="Full JSON Response" defaultExpanded={false} />
            </div>
          )}

          {/* Request Inspector */}
          {selectedTrace && <RequestInspector trace={selectedTrace} />}

          {/* Empty State */}
          {!result && !mutation.isError && !mutation.isPending && (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <Network className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>파일을 업로드하고 세그멘테이션을 실행하세요</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
