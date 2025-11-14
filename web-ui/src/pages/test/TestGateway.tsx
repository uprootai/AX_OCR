import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import FileUploader from '../../components/debug/FileUploader';
import JSONViewer from '../../components/debug/JSONViewer';
import RequestInspector from '../../components/debug/RequestInspector';
import RequestTimeline from '../../components/debug/RequestTimeline';
import ErrorPanel from '../../components/debug/ErrorPanel';
import OCRVisualization from '../../components/debug/OCRVisualization';
import SegmentationVisualization from '../../components/debug/SegmentationVisualization';
import GatewayGuide from '../../components/guides/GatewayGuide';
import PipelineProgress from '../../components/ui/PipelineProgress';
import { gatewayApi } from '../../lib/api';
import { useMonitoringStore } from '../../store/monitoringStore';
import { getHyperParameters } from '../../hooks/useHyperParameters';
import { Loader2, Play, Zap, CheckCircle, BookOpen } from 'lucide-react';
import type { AnalysisResult, RequestTrace } from '../../types/api';

export default function TestGateway() {
  const [file, setFile] = useState<File | null>(null);
  const [showGuide, setShowGuide] = useState(true);
  const [pipelineMode, setPipelineMode] = useState<'hybrid' | 'speed'>('speed');
  const [options, setOptions] = useState({
    use_ocr: true,
    use_segmentation: true,
    use_tolerance: true,
    visualize: false,
  });
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<RequestTrace | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [showProgress, setShowProgress] = useState(false);

  const { traces, addTrace } = useMonitoringStore();
  const gatewayTraces = traces.filter((t) => t.endpoint.includes('process') || t.endpoint.includes('gateway'));

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      const startTime = Date.now();
      const traceId = `gateway-${Date.now()}`;

      // Show progress tracking
      setShowProgress(true);
      setResult(null);

      try {
        // Get hyperparameters from localStorage
        const hyperParams = getHyperParameters();

        const response = await gatewayApi.process(file, {
          ...options,
          pipeline_mode: pipelineMode,
          ...hyperParams  // Spread hyperparameters into options
        });
        const duration = Date.now() - startTime;

        // Set job_id for progress tracking
        if (response.data?.job_id) {
          setJobId(response.data.job_id);
        }

        // Extract timeline from response if available
        const timeline = {
          upload: response.data?.ocr?.processing_time || 0,
          edocr2: response.data?.ocr?.processing_time || 0,
          edgnet: response.data?.segmentation?.processing_time || 0,
          skinmodel: response.data?.tolerance?.processing_time || 0,
          response: 100,
        };

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint: '/api/v1/process',
          method: 'POST',
          status: 200,
          duration,
          request: {
            file: file.name,
            options,
          },
          response,
          timeline,
        };

        addTrace(trace);
        setSelectedTrace(trace);
        return response;
      } catch (error: any) {
        const duration = Date.now() - startTime;

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint: '/api/v1/process',
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

    // Generate job_id based on timestamp and filename (matches backend format)
    const generatedJobId = `${Math.floor(Date.now() / 1000)}_${file.name}`;
    setJobId(generatedJobId);
    setShowProgress(true);

    mutation.mutate(file);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <Zap className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Gateway API Test</h1>
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
          통합 파이프라인을 통해 OCR, 세그멘테이션, 공차 분석을 한 번에 실행합니다.
        </p>
      </div>

      {/* Usage Guide */}
      {showGuide && <GatewayGuide />}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left Column: Test Configuration */}
        <div className="space-y-6">
          {/* File Upload */}
          <Card>
            <CardHeader>
              <CardTitle>1. 파일 업로드</CardTitle>
            </CardHeader>
            <CardContent>
              <FileUploader
                onFileSelect={setFile}
                currentFile={file}
                accept="image/*,.pdf"
                maxSize={10}
              />
            </CardContent>
          </Card>

          {/* Pipeline Options */}
          <Card>
            <CardHeader>
              <CardTitle>2. 파이프라인 옵션</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Pipeline Mode Selection */}
              <div className="space-y-2">
                <label className="text-sm font-semibold">파이프라인 모드</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setPipelineMode('hybrid')}
                    className={`p-3 rounded-lg border-2 transition-all text-left ${
                      pipelineMode === 'hybrid'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
                        : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                    }`}
                  >
                    <div className="font-semibold flex items-center gap-2">
                      ⚖️ 하이브리드
                      {pipelineMode === 'hybrid' && (
                        <CheckCircle className="w-4 h-4 text-blue-500" />
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      정확도 ~95% | 40-50초
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPipelineMode('speed')}
                    className={`p-3 rounded-lg border-2 transition-all text-left ${
                      pipelineMode === 'speed'
                        ? 'border-green-500 bg-green-50 dark:bg-green-950'
                        : 'border-gray-300 dark:border-gray-600 hover:border-green-400'
                    }`}
                  >
                    <div className="font-semibold flex items-center gap-2">
                      ⚡ 속도 우선
                      {pipelineMode === 'speed' && (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      정확도 ~93% | 35-45초
                    </div>
                  </button>
                </div>
              </div>

              {/* Additional Options */}
              <div className="pt-2 border-t">
                <label className="text-sm font-semibold mb-2 block">추가 옵션</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={options.use_ocr}
                      onChange={(e) =>
                        setOptions({ ...options, use_ocr: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <div>
                      <p className="font-medium">OCR 실행</p>
                      <p className="text-sm text-muted-foreground">
                        eDOCr2를 사용하여 치수, GD&T, 텍스트 정보 추출
                      </p>
                    </div>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={options.use_segmentation}
                      onChange={(e) =>
                        setOptions({ ...options, use_segmentation: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <div>
                      <p className="font-medium">세그멘테이션 실행</p>
                      <p className="text-sm text-muted-foreground">
                        EDGNet을 사용하여 도면 요소 분류 및 그래프 생성
                      </p>
                    </div>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={options.use_tolerance}
                      onChange={(e) =>
                        setOptions({ ...options, use_tolerance: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <div>
                      <p className="font-medium">공차 분석 실행</p>
                      <p className="text-sm text-muted-foreground">
                        Skin Model을 사용하여 공차 예측 및 제조 가능성 분석
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
                      <p className="font-medium">시각화</p>
                      <p className="text-sm text-muted-foreground">
                        결과를 이미지로 시각화합니다
                      </p>
                    </div>
                  </label>
                </div>
              </div>
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
                    통합 분석 실행
                  </>
                )}
              </Button>
              <p className="text-xs text-muted-foreground mt-2 text-center">
                선택된 모든 서비스가 순차적으로 실행됩니다
              </p>
            </CardContent>
          </Card>

          {/* Real-time Progress */}
          {showProgress && jobId && (
            <PipelineProgress
              jobId={jobId}
              pipelineMode={pipelineMode}
              onComplete={(data) => {
                console.log('Pipeline complete:', data);
              }}
              onError={(error) => {
                console.error('Pipeline error:', error);
              }}
            />
          )}

          {/* Request Timeline */}
          {gatewayTraces.length > 0 && (
            <RequestTimeline
              traces={gatewayTraces}
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
              {/* Summary Card */}
              <Card>
                <CardHeader>
                  <CardTitle>분석 결과 요약</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-background border rounded">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        <span className="font-medium">전체 상태</span>
                      </div>
                      <Badge variant={result.status === 'success' ? 'success' : 'error'}>
                        {result.status}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-background border rounded">
                      <span className="font-medium">총 처리 시간</span>
                      <Badge>{result.processing_time.toFixed(2)}ms</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-background border rounded">
                      <span className="font-medium">파일 ID</span>
                      <span className="text-sm font-mono">{result.file_id}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* OCR Results */}
              {result.data?.ocr && (
                <Card>
                  <CardHeader>
                    <CardTitle>OCR 결과</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-3 mb-3">
                      <div className="text-center p-3 bg-accent rounded">
                        <p className="text-2xl font-bold">{result.data.ocr.data.dimensions?.length || 0}</p>
                        <p className="text-xs text-muted-foreground">Dimensions</p>
                      </div>
                      <div className="text-center p-3 bg-accent rounded">
                        <p className="text-2xl font-bold">{result.data.ocr.data.gdt?.length || 0}</p>
                        <p className="text-xs text-muted-foreground">GD&T</p>
                      </div>
                      <div className="text-center p-3 bg-accent rounded">
                        <p className="text-2xl font-bold">{result.data.ocr.processing_time.toFixed(0)}</p>
                        <p className="text-xs text-muted-foreground">ms</p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Status</span>
                      <Badge variant="success">{result.data.ocr.status}</Badge>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Segmentation Results */}
              {result.data?.segmentation && (
                <Card>
                  <CardHeader>
                    <CardTitle>세그멘테이션 결과</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-3 mb-3">
                      <div className="text-center p-3 bg-accent rounded">
                        <p className="text-2xl font-bold">{result.data.segmentation.data.num_components}</p>
                        <p className="text-xs text-muted-foreground">Components</p>
                      </div>
                      <div className="text-center p-3 bg-accent rounded">
                        <p className="text-2xl font-bold">{result.data.segmentation.data.graph?.nodes || 0}</p>
                        <p className="text-xs text-muted-foreground">Nodes</p>
                      </div>
                      <div className="text-center p-3 bg-accent rounded">
                        <p className="text-2xl font-bold">{result.data.segmentation.processing_time.toFixed(0)}</p>
                        <p className="text-xs text-muted-foreground">ms</p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Status</span>
                      <Badge variant="success">{result.data.segmentation.status}</Badge>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Tolerance Results */}
              {result.data?.tolerance && (
                <Card>
                  <CardHeader>
                    <CardTitle>공차 분석 결과</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 mb-3">
                      <div className="flex items-center justify-between p-2 bg-background border rounded text-sm">
                        <span>제조 가능성</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-1.5 bg-accent rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary"
                              style={{ width: `${result.data.tolerance.data.manufacturability?.score * 100}%` }}
                            />
                          </div>
                          <span className="font-semibold">
                            {((result.data.tolerance.data.manufacturability?.score || 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-2 bg-background border rounded text-sm">
                        <span>난이도</span>
                        <Badge>{result.data.tolerance.data.manufacturability?.difficulty}</Badge>
                      </div>
                      <div className="flex items-center justify-between p-2 bg-background border rounded text-sm">
                        <span>처리 시간</span>
                        <Badge>{result.data.tolerance.processing_time.toFixed(0)}ms</Badge>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Status</span>
                      <Badge variant="success">{result.data.tolerance.status}</Badge>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* OCR Visualization - only for images */}
              {file && file.type.startsWith('image/') && result.data?.ocr && (
                <OCRVisualization
                  imageFile={file}
                  ocrResult={result.data.ocr.data}
                />
              )}

              {/* Segmentation Visualization - only for images */}
              {file && file.type.startsWith('image/') && result.data?.segmentation && (
                <SegmentationVisualization
                  imageFile={file}
                  segmentationResult={result.data.segmentation.data}
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
                <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="mb-2">파일을 업로드하고 통합 분석을 실행하세요</p>
                <p className="text-xs">
                  Gateway API는 모든 서비스를 오케스트레이션합니다
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
