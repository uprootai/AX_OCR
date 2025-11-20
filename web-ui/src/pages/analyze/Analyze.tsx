import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Tooltip } from '../../components/ui/Tooltip';
import FileUploader from '../../components/debug/FileUploader';
import JSONViewer from '../../components/debug/JSONViewer';
import OCRVisualization from '../../components/debug/OCRVisualization';
import { gatewayApi } from '../../lib/api';
import { useAnalysisStore } from '../../store/analysisStore';
import {
  Loader2,
  Play,
  Download,
  FileText,
  Network,
  Target,
  CheckCircle,
  TrendingUp,
} from 'lucide-react';

export default function Analyze() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'overview' | 'ocr' | 'segmentation' | 'tolerance'>('overview');

  const {
    currentFile,
    options,
    status,
    progress,
    result,
    error,
    setFile,
    setOptions,
    setStatus,
    setProgress,
    setResult,
    setError,
  } = useAnalysisStore();

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      setStatus('uploading');
      setProgress(10);

      const response = await gatewayApi.process(
        file,
        {
          use_ocr: options.ocr,
          use_segmentation: options.segmentation,
          use_tolerance: options.tolerance,
          visualize: options.visualize,
        },
        (progressPercent) => {
          setProgress(Math.min(progressPercent, 90));
        }
      );

      setProgress(100);
      return response;
    },
    onSuccess: (data) => {
      setStatus('complete');
      setResult(data);
      setError(null);
    },
    onError: (error: any) => {
      setStatus('error');
      const errorMessage = error.response?.data?.detail || error.message || t('analyze.analysisError');
      setError(errorMessage);
    },
  });

  const handleAnalyze = () => {
    if (!currentFile) return;

    // PDF 파일은 자동으로 이미지로 변환되어 세그멘테이션됩니다
    setResult(null);
    setError(null);
    setStatus('analyzing');
    mutation.mutate(currentFile);
  };

  const handleDownloadJSON = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis-${result.file_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getProgressStage = () => {
    if (status === 'uploading') return t('analyze.uploading');
    if (status === 'analyzing') {
      if (progress < 30) return t('analyze.ocrProcessing');
      if (progress < 60) return t('analyze.segmentationProcessing');
      if (progress < 90) return t('analyze.toleranceProcessing');
      return t('analyze.generatingResults');
    }
    return '';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">{t('analyze.title')}</h1>
        <p className="text-muted-foreground">
          {t('analyze.subtitle')}
        </p>
      </div>

      {/* Information Banner */}
      <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            <svg className="h-5 w-5 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
              {t('analyze.integratedAnalysis')}
            </h3>
            <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
              <li>• {t('analyze.integratedInfo1')}</li>
              <li>• <strong>{t('analyze.integratedInfo2')}</strong></li>
              <li>• {t('analyze.integratedInfo3')}</li>
              <li>• {t('analyze.integratedInfo4')}</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left Column: Configuration */}
        <div className="lg:col-span-1 space-y-6">
          {/* File Upload */}
          <Card>
            <CardHeader>
              <CardTitle>{t('analyze.fileSelection')}</CardTitle>
            </CardHeader>
            <CardContent>
              <FileUploader
                onFileSelect={(file) => {
                  setFile(file);
                  setResult(null);
                  setError(null);
                }}
                currentFile={currentFile}
                accept="image/*,.pdf"
                maxSize={10}
              />
            </CardContent>
          </Card>

          {/* Analysis Options */}
          <Card>
            <CardHeader>
              <CardTitle>{t('analyze.analysisOptions')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.ocr}
                  onChange={(e) => setOptions({ ...options, ocr: e.target.checked })}
                  className="w-4 h-4"
                  disabled={status === 'analyzing' || status === 'uploading'}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    <span className="font-medium">OCR</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{t('analyze.ocrOption')}</p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.segmentation}
                  onChange={(e) => setOptions({ ...options, segmentation: e.target.checked })}
                  className="w-4 h-4"
                  disabled={status === 'analyzing' || status === 'uploading'}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Network className="h-4 w-4" />
                    <span className="font-medium">{t('analyze.segmentation')}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{t('analyze.segmentationOption')}</p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.tolerance}
                  onChange={(e) => setOptions({ ...options, tolerance: e.target.checked })}
                  className="w-4 h-4"
                  disabled={status === 'analyzing' || status === 'uploading'}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    <span className="font-medium">{t('analyze.toleranceAnalysis')}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{t('analyze.toleranceOption')}</p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.visualize}
                  onChange={(e) => setOptions({ ...options, visualize: e.target.checked })}
                  className="w-4 h-4"
                  disabled={status === 'analyzing' || status === 'uploading'}
                />
                <div className="flex-1">
                  <span className="font-medium">{t('common.export')}</span>
                  <p className="text-xs text-muted-foreground">{t('analyze.visualizeOption')}</p>
                </div>
              </label>
            </CardContent>
          </Card>

          {/* Execute */}
          <Card>
            <CardHeader>
              <CardTitle>{t('analyze.execute')}</CardTitle>
            </CardHeader>
            <CardContent>
              <Button
                onClick={handleAnalyze}
                disabled={!currentFile || mutation.isPending}
                className="w-full"
                size="lg"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    {t('analyze.analyzing')}
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 mr-2" />
                    {t('analyze.startAnalysis')}
                  </>
                )}
              </Button>

              {/* Progress Bar */}
              {(status === 'uploading' || status === 'analyzing') && (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">{getProgressStage()}</span>
                    <span className="text-sm text-muted-foreground">{progress}%</span>
                  </div>
                  <div className="h-2 bg-accent rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-2 space-y-6">
          {/* Error State */}
          {error && (
            <Card className="border-destructive/50 bg-destructive/5">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-destructive/10 rounded-full">
                    <TrendingUp className="h-5 w-5 text-destructive" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-destructive mb-1">{t('analyze.analysisFailed')}</h3>
                    <p className="text-sm text-destructive/80">{error}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Results */}
          {result && (
            <>
              {/* Actions */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="font-semibold">분석 완료</span>
                </div>
                <Button variant="outline" size="sm" onClick={handleDownloadJSON}>
                  <Download className="h-4 w-4 mr-2" />
                  JSON 다운로드
                </Button>
              </div>

              {/* Tabs */}
              <Card>
                <CardHeader>
                  <div className="flex gap-2 border-b -mb-6">
                    <button
                      onClick={() => setActiveTab('overview')}
                      className={`px-4 py-2 font-medium transition-colors ${
                        activeTab === 'overview'
                          ? 'text-primary border-b-2 border-primary'
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      개요
                    </button>
                    {result.data?.ocr && (
                      <button
                        onClick={() => setActiveTab('ocr')}
                        className={`px-4 py-2 font-medium transition-colors ${
                          activeTab === 'ocr'
                            ? 'text-primary border-b-2 border-primary'
                            : 'text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        OCR
                      </button>
                    )}
                    {result.data?.segmentation && (
                      <button
                        onClick={() => setActiveTab('segmentation')}
                        className={`px-4 py-2 font-medium transition-colors ${
                          activeTab === 'segmentation'
                            ? 'text-primary border-b-2 border-primary'
                            : 'text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        세그멘테이션
                      </button>
                    )}
                    {result.data?.tolerance && (
                      <button
                        onClick={() => setActiveTab('tolerance')}
                        className={`px-4 py-2 font-medium transition-colors ${
                          activeTab === 'tolerance'
                            ? 'text-primary border-b-2 border-primary'
                            : 'text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        공차 분석
                      </button>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="pt-6">
                  {/* Overview Tab */}
                  {activeTab === 'overview' && (
                    <div className="space-y-4">
                      <div className="grid md:grid-cols-2 gap-4">
                        <div className="p-4 bg-accent rounded-lg">
                          <p className="text-sm text-muted-foreground mb-1">전체 상태</p>
                          <Badge variant={result.status === 'success' ? 'success' : 'error'} className="text-lg">
                            {result.status}
                          </Badge>
                        </div>
                        <div className="p-4 bg-accent rounded-lg">
                          <p className="text-sm text-muted-foreground mb-1">총 처리 시간</p>
                          <p className="text-2xl font-bold">{result.processing_time.toFixed(0)}ms</p>
                        </div>
                      </div>

                      <div className="p-4 bg-background border rounded-lg">
                        <p className="text-sm font-medium mb-2">파일 정보</p>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">파일 ID:</span>
                            <span className="font-mono">{result.file_id}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">파일명:</span>
                            <span>{currentFile?.name}</span>
                          </div>
                        </div>
                      </div>

                      {/* Service Summary */}
                      <div className="space-y-2">
                        <p className="font-semibold">실행된 서비스</p>
                        {result.data?.ocr && (
                          <div className="flex items-center justify-between p-3 bg-background border rounded">
                            <div className="flex items-center gap-2">
                              <FileText className="h-4 w-4" />
                              <span>OCR</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <Badge variant="success">{result.data.ocr.status}</Badge>
                              <span className="text-sm text-muted-foreground">
                                {result.data.ocr.processing_time.toFixed(0)}ms
                              </span>
                            </div>
                          </div>
                        )}
                        {result.data?.segmentation && (
                          <div className="flex items-center justify-between p-3 bg-background border rounded">
                            <div className="flex items-center gap-2">
                              <Network className="h-4 w-4" />
                              <span>세그멘테이션</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <Badge variant="success">{result.data.segmentation.status}</Badge>
                              <span className="text-sm text-muted-foreground">
                                {result.data.segmentation.processing_time.toFixed(0)}ms
                              </span>
                            </div>
                          </div>
                        )}
                        {result.data?.tolerance && (
                          <div className="flex items-center justify-between p-3 bg-background border rounded">
                            <div className="flex items-center gap-2">
                              <Target className="h-4 w-4" />
                              <span>공차 분석</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <Badge variant="success">{result.data.tolerance.status}</Badge>
                              <span className="text-sm text-muted-foreground">
                                {result.data.tolerance.processing_time.toFixed(0)}ms
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* OCR Tab */}
                  {activeTab === 'ocr' && result.data?.ocr && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-accent rounded-lg">
                          <p className="text-3xl font-bold">{result.data.ocr.data.dimensions?.length || 0}</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            <Tooltip content="OCR로 추출된 치수 값들의 개수 (지름, 길이, 반지름 등)">
                              Dimensions
                            </Tooltip>
                          </p>
                        </div>
                        <div className="text-center p-4 bg-accent rounded-lg">
                          <p className="text-3xl font-bold">{result.data.ocr.data.gdt?.length || 0}</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            <Tooltip content="OCR로 추출된 기하공차(진직도, 평면도, 원통도 등) 표기의 개수">
                              GD&T
                            </Tooltip>
                          </p>
                        </div>
                        <div className="text-center p-4 bg-accent rounded-lg">
                          <p className="text-3xl font-bold">{result.data.ocr.data.text?.total_blocks || 0}</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            <Tooltip content="OCR로 감지된 텍스트 블록의 개수 (재질명, 주석, 기타 정보 등)">
                              Text Blocks
                            </Tooltip>
                          </p>
                        </div>
                      </div>

                      {result.data.ocr.data.dimensions && result.data.ocr.data.dimensions.length > 0 && (
                        <div>
                          <p className="font-semibold mb-3">주요 치수</p>
                          <div className="space-y-2">
                            {result.data.ocr.data.dimensions.slice(0, 10).map((dim, idx) => (
                              <div key={idx} className="flex items-center justify-between p-3 bg-background border rounded">
                                <div className="flex items-center gap-3">
                                  <Badge>{dim.type}</Badge>
                                  <span className="font-mono">
                                    {dim.value} {dim.unit}
                                  </span>
                                </div>
                                {dim.tolerance && (
                                  <span className="text-sm text-muted-foreground">±{dim.tolerance}</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* OCR Visualization - only for images */}
                      {currentFile && currentFile.type.startsWith('image/') && (
                        <OCRVisualization
                          imageFile={currentFile}
                          ocrResult={result.data.ocr.data}
                        />
                      )}

                      <JSONViewer data={result.data.ocr.data} title="전체 OCR 데이터" defaultExpanded={false} />
                    </div>
                  )}

                  {/* Segmentation Tab */}
                  {activeTab === 'segmentation' && result.data?.segmentation && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-4 bg-accent rounded-lg">
                          <p className="text-3xl font-bold">{result.data.segmentation.data.num_components}</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            <Tooltip content="세그멘테이션으로 식별된 도면 요소의 총 개수">
                              Components
                            </Tooltip>
                          </p>
                        </div>
                        <div className="text-center p-4 bg-accent rounded-lg">
                          <p className="text-3xl font-bold">{result.data.segmentation.data.graph?.nodes || 0}</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            <Tooltip content="도면 요소 간의 관계를 나타내는 그래프 노드 수">
                              Graph Nodes
                            </Tooltip>
                          </p>
                        </div>
                      </div>

                      <div>
                        <p className="font-semibold mb-3">컴포넌트 분류</p>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between p-3 bg-background border rounded">
                            <Tooltip content="도면에서 감지된 윤곽선(외형선, 내부선 등)의 개수">
                              Contours
                            </Tooltip>
                            <Badge>{result.data.segmentation.data.classifications?.contour || 0}</Badge>
                          </div>
                          <div className="flex items-center justify-between p-3 bg-background border rounded">
                            <Tooltip content="도면에서 감지된 텍스트 영역의 개수">
                              Text
                            </Tooltip>
                            <Badge>{result.data.segmentation.data.classifications?.text || 0}</Badge>
                          </div>
                          <div className="flex items-center justify-between p-3 bg-background border rounded">
                            <Tooltip content="도면에서 감지된 치수 표기의 개수">
                              Dimensions
                            </Tooltip>
                            <Badge>{result.data.segmentation.data.classifications?.dimension || 0}</Badge>
                          </div>
                        </div>
                      </div>

                      <JSONViewer data={result.data.segmentation.data} title="전체 세그멘테이션 데이터" defaultExpanded={false} />
                    </div>
                  )}

                  {/* Tolerance Tab */}
                  {activeTab === 'tolerance' && result.data?.tolerance && (
                    <div className="space-y-4">
                      <div>
                        <p className="font-semibold mb-3">{t('analyze.manufacturability')}</p>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between p-4 bg-background border rounded">
                            <span>점수</span>
                            <div className="flex items-center gap-3">
                              <div className="w-32 h-2 bg-accent rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-primary"
                                  style={{ width: `${(result.data.tolerance.data.manufacturability?.score || 0) * 100}%` }}
                                />
                              </div>
                              <span className="font-semibold">
                                {((result.data.tolerance.data.manufacturability?.score || 0) * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center justify-between p-4 bg-background border rounded">
                            <span>난이도</span>
                            <Badge>{result.data.tolerance.data.manufacturability?.difficulty}</Badge>
                          </div>
                        </div>
                      </div>

                      <div>
                        <p className="font-semibold mb-3">예측된 공차</p>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="p-3 bg-background border rounded">
                            <p className="text-xs text-muted-foreground mb-1">Flatness</p>
                            <p className="font-mono font-semibold">
                              {result.data.tolerance.data.predicted_tolerances?.flatness.toFixed(4)}
                            </p>
                          </div>
                          <div className="p-3 bg-background border rounded">
                            <p className="text-xs text-muted-foreground mb-1">Cylindricity</p>
                            <p className="font-mono font-semibold">
                              {result.data.tolerance.data.predicted_tolerances?.cylindricity.toFixed(4)}
                            </p>
                          </div>
                          <div className="p-3 bg-background border rounded">
                            <p className="text-xs text-muted-foreground mb-1">Position</p>
                            <p className="font-mono font-semibold">
                              {result.data.tolerance.data.predicted_tolerances?.position.toFixed(4)}
                            </p>
                          </div>
                          {result.data.tolerance.data.predicted_tolerances?.perpendicularity !== undefined && (
                            <div className="p-3 bg-background border rounded">
                              <p className="text-xs text-muted-foreground mb-1">Perpendicularity</p>
                              <p className="font-mono font-semibold">
                                {result.data.tolerance.data.predicted_tolerances.perpendicularity.toFixed(4)}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>

                      <JSONViewer data={result.data.tolerance.data} title="전체 공차 분석 데이터" defaultExpanded={false} />
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}

          {/* Empty State */}
          {!result && !error && status === 'idle' && (
            <Card>
              <CardContent className="py-16 text-center text-muted-foreground">
                <FileText className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg mb-2">{t('analyze.uploadPrompt')}</p>
                <p className="text-sm">
                  {t('analyze.uploadInstruction')}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
