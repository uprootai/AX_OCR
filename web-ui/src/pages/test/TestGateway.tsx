import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { FileUploadSection } from '../../components/upload/FileUploadSection';
import { DimensionChart } from '../../components/charts/DimensionChart';
import { ProcessingTimeChart } from '../../components/charts/ProcessingTimeChart';
import { ResultActions } from '../../components/results/ResultActions';
import JSONViewer from '../../components/debug/JSONViewer';
import RequestInspector from '../../components/debug/RequestInspector';
import RequestTimeline from '../../components/debug/RequestTimeline';
import ErrorPanel from '../../components/debug/ErrorPanel';
import OCRVisualization from '../../components/debug/OCRVisualization';
import SegmentationVisualization from '../../components/debug/SegmentationVisualization';
import PipelineStepsVisualization from '../../components/debug/PipelineStepsVisualization';
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
    use_yolo_crop_ocr: false,
    use_ensemble: false,
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
              <FileUploadSection
                onFileSelect={setFile}
                currentFile={file}
                accept={{
                  'image/*': ['.png', '.jpg', '.jpeg'],
                  'application/pdf': ['.pdf']
                }}
                maxSize={10 * 1024 * 1024}  // 10MB in bytes
                disabled={mutation.isPending}
                showSamples={true}
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
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-semibold">파이프라인 모드</label>
                  <p className="text-xs text-muted-foreground mt-1">
                    목적에 따라 최적화된 처리 전략을 선택하세요
                  </p>
                </div>
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
                    <div className="text-xs text-blue-600 dark:text-blue-400 mt-1 font-medium">
                      순차 처리 + 업스케일링
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
                    <div className="text-xs text-green-600 dark:text-green-400 mt-1 font-medium">
                      병렬 처리 + 빠른 응답
                    </div>
                  </button>
                </div>

                {/* Mode Explanation */}
                <div className={`p-3 rounded-lg text-sm ${
                  pipelineMode === 'hybrid'
                    ? 'bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800'
                    : 'bg-green-50 dark:bg-green-950/50 border border-green-200 dark:border-green-800'
                }`}>
                  {pipelineMode === 'hybrid' ? (
                    <div>
                      <p className="font-semibold text-blue-900 dark:text-blue-100 mb-1">
                        🔵 하이브리드 모드 처리 흐름
                      </p>
                      <p className="text-xs text-blue-700 dark:text-blue-300">
                        1단계: YOLO 검출 → 2단계: 검출 영역 업스케일 + OCR & EDGNet 병렬 → 3단계: 결과 병합 → 4단계: 공차 예측
                      </p>
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                        💡 작은 텍스트도 업스케일링으로 정확하게 인식합니다
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="font-semibold text-green-900 dark:text-green-100 mb-1">
                        ⚡ 속도 우선 모드 처리 흐름
                      </p>
                      <p className="text-xs text-green-700 dark:text-green-300">
                        1단계: YOLO & OCR & EDGNet 모두 병렬 실행 → 2단계: 결과 병합 → 3단계: 공차 예측
                      </p>
                      <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                        💡 모든 단계를 동시에 처리하여 대량 도면 처리에 최적화
                      </p>
                    </div>
                  )}
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

              {/* Advanced OCR Options */}
              <div className="pt-2 border-t">
                <label className="text-sm font-semibold mb-2 block flex items-center gap-2">
                  <span className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-2 py-0.5 rounded text-xs">NEW</span>
                  고급 OCR 전략
                </label>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                    <input
                      type="checkbox"
                      checked={options.use_yolo_crop_ocr}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        setOptions({
                          ...options,
                          use_yolo_crop_ocr: checked,
                          // 앙상블은 YOLO Crop OCR이 활성화되어야 사용 가능
                          use_ensemble: checked ? options.use_ensemble : false
                        });
                      }}
                      className="w-4 h-4"
                    />
                    <div className="flex-1">
                      <p className="font-medium flex items-center gap-2">
                        🎯 YOLO Crop OCR
                        <Badge variant="success" className="text-xs">재현율 +16.7%</Badge>
                      </p>
                      <p className="text-sm text-muted-foreground">
                        YOLO 검출 영역별 개별 OCR 수행 (재현율 93.3%, 처리 시간 +2.1%)
                      </p>
                    </div>
                  </label>

                  <label className={`flex items-center gap-3 cursor-pointer p-3 rounded-lg border transition-colors ${
                    options.use_yolo_crop_ocr
                      ? 'hover:bg-gray-50 dark:hover:bg-gray-800'
                      : 'opacity-50 cursor-not-allowed bg-gray-100 dark:bg-gray-900'
                  }`}>
                    <input
                      type="checkbox"
                      checked={options.use_ensemble}
                      disabled={!options.use_yolo_crop_ocr}
                      onChange={(e) =>
                        setOptions({ ...options, use_ensemble: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <div className="flex-1">
                      <p className="font-medium flex items-center gap-2">
                        🚀 앙상블 전략
                        <Badge variant="secondary" className="text-xs">정밀도 +33%</Badge>
                      </p>
                      <p className="text-sm text-muted-foreground">
                        YOLO Crop OCR + eDOCr v2 가중치 기반 융합 (예상 F1 Score 95%+)
                      </p>
                      {!options.use_yolo_crop_ocr && (
                        <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                          ⚠️ YOLO Crop OCR을 먼저 활성화해주세요
                        </p>
                      )}
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
              onComplete={() => {
                // Pipeline complete - data available in result state
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
              {/* Pipeline Steps Visualization */}
              {file && (
                <PipelineStepsVisualization
                  imageFile={file}
                  result={result}
                />
              )}

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

              {/* YOLO Detection Results */}
              {result.data?.yolo_results && (
                <Card className="border-2 border-primary/20">
                  <CardHeader className="bg-primary/5">
                    <CardTitle className="flex items-center gap-2">
                      <span className="text-primary">🎯</span>
                      YOLO 객체 검출 결과
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Detection Stats */}
                    <div className="grid grid-cols-2 gap-3 text-sm p-3 bg-muted/50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">검출 개수</span>
                        <span className="font-bold text-lg text-primary">{result.data.yolo_results.total_detections}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">처리 시간</span>
                        <span className="font-bold">{result.data.yolo_results.processing_time.toFixed(2)}s</span>
                      </div>
                    </div>

                    {/* Legend Explanation */}
                    <div className="p-4 bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-950/30 dark:to-green-950/30 border border-blue-200 dark:border-blue-800 rounded-lg space-y-3">
                      <h4 className="font-semibold text-sm flex items-center gap-2">
                        <span>🎨</span>
                        색상 범례 (Detection Classes)
                      </h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="flex items-center gap-2">
                          <div className="w-4 h-4 bg-blue-500 border border-blue-700 rounded"></div>
                          <span><strong>파란색</strong>: 치수 (Dimensions)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-4 h-4 bg-green-500 border border-green-700 rounded"></div>
                          <span><strong>초록색</strong>: GD&T 기호</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-4 h-4 bg-orange-500 border border-orange-700 rounded"></div>
                          <span><strong>주황색</strong>: 표면 조도</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-4 h-4 bg-cyan-400 border border-cyan-600 rounded"></div>
                          <span><strong>청록색</strong>: 텍스트 블록</span>
                        </div>
                      </div>
                      <div className="pt-2 border-t border-blue-200 dark:border-blue-800">
                        <p className="text-xs text-muted-foreground">
                          <strong>라벨 형식:</strong> <code className="bg-white/50 dark:bg-black/30 px-1.5 py-0.5 rounded">클래스명 (신뢰도)</code>
                          <br />
                          <strong>예시:</strong> <code className="bg-white/50 dark:bg-black/30 px-1.5 py-0.5 rounded">linear_dim (0.85)</code> = 선형 치수, 신뢰도 85%
                        </p>
                      </div>
                    </div>

                    {/* Visualization Image */}
                    {result.data.yolo_results.visualized_image ? (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm text-muted-foreground">
                            💡 클릭하면 크게 볼 수 있습니다
                          </p>
                          {result.download_urls?.yolo_visualization && (
                            <a
                              href={`http://localhost:8000${result.download_urls.yolo_visualization}`}
                              download
                              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (result.download_urls?.yolo_visualization) {
                                  navigator.clipboard.writeText(`http://localhost:8000${result.download_urls.yolo_visualization}`);
                                  alert('다운로드 URL이 클립보드에 복사되었습니다!');
                                }
                              }}
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                              </svg>
                              다운로드 / URL 복사
                            </a>
                          )}
                        </div>
                        <img
                          src={`data:image/jpeg;base64,${result.data.yolo_results.visualized_image}`}
                          alt="YOLO Detection Visualization"
                          className="w-full h-auto border-2 border-border rounded-lg cursor-pointer hover:opacity-90 hover:border-primary transition-all shadow-md"
                          onClick={() => {
                            const modal = document.createElement('div');
                            modal.className = 'fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 p-4';
                            modal.innerHTML = `
                              <div class="relative max-w-7xl w-full">
                                <img src="data:image/jpeg;base64,${result.data.yolo_results?.visualized_image}" class="w-full h-auto max-h-[90vh] object-contain rounded-lg" />
                                <button class="absolute top-4 right-4 bg-white/10 hover:bg-white/20 text-white text-3xl font-bold w-12 h-12 rounded-full flex items-center justify-center">&times;</button>
                              </div>
                            `;
                            modal.onclick = () => modal.remove();
                            document.body.appendChild(modal);
                          }}
                        />

                        {/* Color Legend */}
                        <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-lg">
                          <h4 className="text-sm font-semibold mb-3 text-slate-900 dark:text-slate-100">
                            📊 바운딩 박스 색상 범례
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div className="flex items-start gap-3">
                              <div className="w-6 h-6 rounded border-2 border-blue-500 bg-blue-500/20 flex-shrink-0 mt-0.5"></div>
                              <div>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">파란색 (Blue)</p>
                                <p className="text-xs text-slate-600 dark:text-slate-400">치수 (Dimensions): 지름(Ø), 선형(Linear), 반지름(R), 각도, 모따기, 공차, 기준 치수</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-3">
                              <div className="w-6 h-6 rounded border-2 border-green-500 bg-green-500/20 flex-shrink-0 mt-0.5"></div>
                              <div>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">초록색 (Green)</p>
                                <p className="text-xs text-slate-600 dark:text-slate-400">GD&T 기호: 평면도(⏥), 원통도(⌭), 위치도(⌖), 직각도(⊥), 평행도(∥)</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-3">
                              <div className="w-6 h-6 rounded border-2 border-orange-500 bg-orange-500/20 flex-shrink-0 mt-0.5"></div>
                              <div>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">주황색 (Orange)</p>
                                <p className="text-xs text-slate-600 dark:text-slate-400">표면 조도 (Surface Roughness): Ra, Rz 등 표면 마감 품질 표시</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-3">
                              <div className="w-6 h-6 rounded border-2 border-cyan-500 bg-cyan-500/20 flex-shrink-0 mt-0.5"></div>
                              <div>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">청록색 (Cyan)</p>
                                <p className="text-xs text-slate-600 dark:text-slate-400">텍스트 블록 (Text Blocks): 부품명, 재질, 스케일, 주석 등 일반 텍스트</p>
                              </div>
                            </div>
                          </div>
                          <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                            <p className="text-xs text-slate-600 dark:text-slate-400">
                              💡 <strong>괄호 안의 숫자는 신뢰도(Confidence)</strong>입니다. 예: <code className="px-1 py-0.5 bg-slate-200 dark:bg-slate-800 rounded text-xs">linear_dim (0.58)</code>은 YOLO 모델이 해당 영역을 선형 치수로 58% 확신함을 의미합니다.
                            </p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                        <p className="text-sm text-yellow-800 dark:text-yellow-200">
                          ⚠️ 시각화 이미지가 생성되지 않았습니다. "시각화" 옵션을 활성화하고 다시 시도해주세요.
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* OCR Results */}
              {result.data?.ocr && (
                <Card>
                  <CardHeader>
                    <CardTitle>OCR 결과 (eDOCr v2)</CardTitle>
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

              {/* YOLO Crop OCR Results */}
              {result.data?.yolo_crop_ocr_results && (
                <Card className="border-2 border-purple-200 dark:border-purple-800">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      🎯 YOLO Crop OCR 결과
                      <Badge variant="success" className="text-xs">재현율 향상</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-4 gap-3 mb-3">
                      <div className="text-center p-3 bg-purple-50 dark:bg-purple-950 rounded">
                        <p className="text-2xl font-bold">{result.data.yolo_crop_ocr_results.total_texts || 0}</p>
                        <p className="text-xs text-muted-foreground">검출 치수</p>
                      </div>
                      <div className="text-center p-3 bg-purple-50 dark:bg-purple-950 rounded">
                        <p className="text-2xl font-bold">{result.data.yolo_crop_ocr_results.successful_crops || 0}/{result.data.yolo_crop_ocr_results.crop_count || 0}</p>
                        <p className="text-xs text-muted-foreground">Crop 성공</p>
                      </div>
                      <div className="text-center p-3 bg-purple-50 dark:bg-purple-950 rounded">
                        <p className="text-2xl font-bold">{((result.data.yolo_crop_ocr_results.processing_time || 0) / 1000).toFixed(1)}s</p>
                        <p className="text-xs text-muted-foreground">처리 시간</p>
                      </div>
                      <div className="text-center p-3 bg-purple-50 dark:bg-purple-950 rounded">
                        <p className="text-2xl font-bold">{result.data.yolo_crop_ocr_results.dimensions?.length || 0}</p>
                        <p className="text-xs text-muted-foreground">필터링 후</p>
                      </div>
                    </div>
                    {result.data.yolo_crop_ocr_results.dimensions && result.data.yolo_crop_ocr_results.dimensions.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <p className="text-sm font-semibold">검출된 치수 (신뢰도 상위 10개):</p>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          {result.data.yolo_crop_ocr_results.dimensions.slice(0, 10).map((dim: any, idx: number) => (
                            <div key={idx} className="flex items-center justify-between p-2 bg-background border rounded">
                              <span className="font-mono font-semibold">{dim.value}</span>
                              <Badge variant="outline" className="text-xs">
                                {(dim.confidence * 100).toFixed(0)}%
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Ensemble Results */}
              {result.data?.ensemble && result.data.ensemble.strategy?.includes('Advanced') && (
                <Card className="border-2 border-blue-200 dark:border-blue-800">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      🚀 앙상블 융합 결과
                      <Badge variant="secondary" className="text-xs">정밀도+재현율</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-950 rounded">
                      <p className="text-sm font-semibold mb-1">전략:</p>
                      <p className="text-xs text-muted-foreground">{result.data.ensemble.strategy}</p>
                    </div>
                    <div className="grid grid-cols-4 gap-3 mb-3">
                      <div className="text-center p-3 bg-accent rounded">
                        <p className="text-2xl font-bold">{result.data.ensemble.dimensions?.length || 0}</p>
                        <p className="text-xs text-muted-foreground">총 치수</p>
                      </div>
                      <div className="text-center p-3 bg-green-50 dark:bg-green-950 rounded">
                        <p className="text-2xl font-bold">{result.data.ensemble.dimensions?.filter((d: any) => d.confirmed_by).length || 0}</p>
                        <p className="text-xs text-muted-foreground">양쪽 확인</p>
                      </div>
                      <div className="text-center p-3 bg-purple-50 dark:bg-purple-950 rounded">
                        <p className="text-2xl font-bold">{result.data.ensemble.dimensions?.filter((d: any) => d.source === 'yolo_crop_ocr' && !d.confirmed_by).length || 0}</p>
                        <p className="text-xs text-muted-foreground">YOLO만</p>
                      </div>
                      <div className="text-center p-3 bg-orange-50 dark:bg-orange-950 rounded">
                        <p className="text-2xl font-bold">{result.data.ensemble.dimensions?.filter((d: any) => d.source === 'edocr_v2' && !d.confirmed_by).length || 0}</p>
                        <p className="text-xs text-muted-foreground">eDOCr만</p>
                      </div>
                    </div>
                    {result.data.ensemble.dimensions && result.data.ensemble.dimensions.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <p className="text-sm font-semibold">최종 융합 치수 (신뢰도 상위 10개):</p>
                        <div className="space-y-1.5 text-sm">
                          {result.data.ensemble.dimensions.slice(0, 10).map((dim: any, idx: number) => (
                            <div key={idx} className="flex items-center gap-2 p-2 bg-background border rounded">
                              <span className="font-mono font-semibold flex-1">{dim.value}</span>
                              <Badge variant={dim.confirmed_by ? 'success' : 'outline'} className="text-xs">
                                {dim.source === 'yolo_crop_ocr' ? 'YOLO' : 'eDOCr'}
                                {dim.confirmed_by && ' ✓'}
                              </Badge>
                              <Badge variant="outline" className="text-xs">
                                {(dim.confidence * 100).toFixed(0)}%
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
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

              {/* Analytics Charts */}
              {result.data && (
                <>
                  {/* Result Actions */}
                  <Card>
                    <CardHeader>
                      <CardTitle>결과 다운로드</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResultActions
                        data={result.data}
                        filename={`drawing_analysis_${new Date().toISOString().split('T')[0]}`}
                      />
                    </CardContent>
                  </Card>

                  {/* Dimension Distribution Chart */}
                  {(result.data.ensemble?.dimensions || result.data.ocr?.data?.dimensions) && (
                    <DimensionChart
                      dimensions={result.data.ensemble?.dimensions || result.data.ocr?.data?.dimensions || []}
                      title="치수 분포 분석"
                    />
                  )}

                  {/* Processing Time Chart */}
                  <ProcessingTimeChart
                    yoloTime={result.data.yolo_results?.processing_time ? result.data.yolo_results.processing_time / 1000 : 0}
                    ocrTime={result.data.ocr?.processing_time ? result.data.ocr.processing_time / 1000 : 0}
                    segmentationTime={result.data.segmentation?.processing_time ? result.data.segmentation.processing_time / 1000 : 0}
                    toleranceTime={result.data.tolerance?.processing_time ? result.data.tolerance.processing_time / 1000 : 0}
                    totalTime={result.processing_time ? result.processing_time / 1000 : 0}
                    title="단계별 처리 시간"
                  />
                </>
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
