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
import EdocrGuide from '../../components/guides/EdocrGuide';
import { edocr2Api } from '../../lib/api';
import { useMonitoringStore } from '../../store/monitoringStore';
import { Loader2, Play, FileText, Layers, ZoomIn, X, BookOpen } from 'lucide-react';
import type { OCRResult, RequestTrace } from '../../types/api';

type EdocrVersion = 'v1' | 'v2';

export default function TestEdocr2() {
  const [file, setFile] = useState<File | null>(null);
  const [version, setVersion] = useState<EdocrVersion>('v1');
  const [showGuide, setShowGuide] = useState(true);
  const [showImageModal, setShowImageModal] = useState(false);
  const [modalImageSrc, setModalImageSrc] = useState('');
  const [options, setOptions] = useState({
    extract_dimensions: true,
    extract_gdt: true,
    extract_text: true,
    extract_tables: true, // v2 only
    visualize: false,
    language: 'eng', // v2 only
    cluster_threshold: 20, // v2 only
  });
  const [result, setResult] = useState<OCRResult | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<RequestTrace | null>(null);

  const { traces, addTrace } = useMonitoringStore();
  const edocr2Traces = traces.filter((t) => t.endpoint.includes('edocr2') || t.endpoint.includes('/api/v'));

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      const startTime = Date.now();
      const traceId = `edocr2-${version}-${Date.now()}`;

      try {
        const response = version === 'v1'
          ? await edocr2Api.ocr(file, options)
          : await edocr2Api.ocrV2(file, options);
        const duration = Date.now() - startTime;

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint: `/api/${version}/ocr`,
          method: 'POST',
          status: 200,
          duration,
          request: {
            file: file.name,
            options,
            version,
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
          endpoint: `/api/${version}/ocr`,
          method: 'POST',
          status: error.response?.status || 0,
          duration,
          request: {
            file: file.name,
            options,
            version,
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

  const versionInfo = {
    v1: {
      title: 'eDOCr v1',
      description: 'eDOCr v1을 통해 도면에서 치수, GD&T, 텍스트 정보를 추출합니다.',
      badge: 'Version 1',
      badgeColor: "default" as const,
      features: ['치수 추출', 'GD&T 추출', '텍스트 추출', '~36초 (CPU)'],
    },
    v2: {
      title: 'eDOCr v2',
      description: 'eDOCr v2를 통해 도면에서 치수, GD&T, 텍스트, 테이블 정보를 추출합니다.',
      badge: 'Version 2 - Advanced',
      badgeColor: 'default' as const,
      features: ['치수 추출', 'GD&T 추출', '텍스트 추출', '테이블 OCR', '고급 세그멘테이션', '~45-60초 (CPU)'],
    },
  };

  const currentVersion = versionInfo[version];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <FileText className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">{currentVersion.title} API Test</h1>
            <Badge variant={currentVersion.badgeColor} className="text-sm">
              {currentVersion.badge}
            </Badge>
          </div>
          <Button
            variant={showGuide ? 'default' : 'outline'}
            onClick={() => setShowGuide(!showGuide)}
          >
            <BookOpen className="w-4 h-4 mr-2" />
            {showGuide ? '가이드 숨기기' : '가이드 보기'}
          </Button>
        </div>
        <p className="text-muted-foreground mb-2">{currentVersion.description}</p>

        {/* Version Features */}
        <div className="flex flex-wrap gap-2">
          {currentVersion.features.map((feature, idx) => (
            <Badge key={idx} variant="default" className="text-xs">
              {feature}
            </Badge>
          ))}
        </div>
      </div>

      {/* Usage Guide */}
      {showGuide && <EdocrGuide />}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left Column: Test Configuration */}
        <div className="space-y-6">
          {/* Version Selection */}
          <Card>
            <CardHeader>
              <CardTitle>0. 버전 선택</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <label className="block">
                  <span className="text-sm font-medium mb-2 block">eDOCr Version</span>
                  <select
                    value={version}
                    onChange={(e) => setVersion(e.target.value as EdocrVersion)}
                    className="w-full px-3 py-2 bg-background border rounded-md"
                  >
                    <option value="v1">v1 - Fast (치수, GD&T, 텍스트)</option>
                    <option value="v2">v2 - Advanced (+ 테이블 OCR)</option>
                  </select>
                </label>

                {version === 'v2' && (
                  <div className="p-3 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-md">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                      ✨ v2 전용 기능
                    </p>
                    <ul className="text-xs text-blue-800 dark:text-blue-200 space-y-1">
                      <li>• 테이블 OCR (Tesseract)</li>
                      <li>• 고급 세그멘테이션 (layer_segm)</li>
                      <li>• 언어 선택 가능</li>
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

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

          {/* Options */}
          <Card>
            <CardHeader>
              <CardTitle>2. OCR 옵션</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.extract_dimensions}
                  onChange={(e) =>
                    setOptions({ ...options, extract_dimensions: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <div>
                  <p className="font-medium">치수 추출 (Extract Dimensions)</p>
                  <p className="text-sm text-muted-foreground">
                    도면에서 치수 정보를 추출합니다.
                  </p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.extract_gdt}
                  onChange={(e) =>
                    setOptions({ ...options, extract_gdt: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <div>
                  <p className="font-medium">GD&T 추출 (Extract GD&T)</p>
                  <p className="text-sm text-muted-foreground">
                    기하 공차 정보를 추출합니다.
                  </p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.extract_text}
                  onChange={(e) =>
                    setOptions({ ...options, extract_text: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <div>
                  <p className="font-medium">텍스트 추출 (Extract Text)</p>
                  <p className="text-sm text-muted-foreground">
                    도면의 모든 텍스트를 추출합니다.
                  </p>
                </div>
              </label>

              {version === 'v2' && (
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={options.extract_tables}
                    onChange={(e) =>
                      setOptions({ ...options, extract_tables: e.target.checked })
                    }
                    className="w-4 h-4"
                  />
                  <div>
                    <p className="font-medium flex items-center gap-2">
                      <Layers className="h-4 w-4 text-blue-500" />
                      테이블 추출 (Extract Tables) - v2 전용
                    </p>
                    <p className="text-sm text-muted-foreground">
                      도면의 테이블 정보를 추출합니다 (Tesseract OCR).
                    </p>
                  </div>
                </label>
              )}

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
                    결과를 이미지로 시각화합니다.
                  </p>
                </div>
              </label>

              {version === 'v2' && (
                <div className="pt-3 border-t space-y-3">
                  <label className="block">
                    <p className="font-medium mb-2">언어 (Language) - v2</p>
                    <select
                      value={options.language}
                      onChange={(e) => setOptions({ ...options, language: e.target.value })}
                      className="w-full px-3 py-2 bg-background border rounded-md text-sm"
                    >
                      <option value="eng">English</option>
                      <option value="kor">한국어</option>
                      <option value="jpn">日本語</option>
                      <option value="chi_sim">简体中文</option>
                    </select>
                  </label>

                  <label className="block">
                    <p className="font-medium mb-2">클러스터 임계값 - v2</p>
                    <input
                      type="number"
                      value={options.cluster_threshold}
                      onChange={(e) =>
                        setOptions({ ...options, cluster_threshold: Number(e.target.value) })
                      }
                      min="10"
                      max="50"
                      className="w-full px-3 py-2 bg-background border rounded-md text-sm"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      치수 클러스터링 임계값 (px, 기본: 20)
                    </p>
                  </label>
                </div>
              )}
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
                    Processing with {version.toUpperCase()}...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 mr-2" />
                    {version.toUpperCase()} OCR 실행
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Request Timeline */}
          {edocr2Traces.length > 0 && (
            <RequestTimeline
              traces={edocr2Traces}
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
                  <CardTitle className="flex items-center justify-between">
                    <span>OCR 결과</span>
                    <Badge variant="default">{version.toUpperCase()}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`grid ${version === 'v2' ? 'grid-cols-4' : 'grid-cols-3'} gap-4 mb-4`}>
                    <div className="text-center p-4 bg-accent rounded-lg">
                      <p className="text-2xl font-bold">{result.dimensions?.length || 0}</p>
                      <p className="text-sm text-muted-foreground">Dimensions</p>
                    </div>
                    <div className="text-center p-4 bg-accent rounded-lg">
                      <p className="text-2xl font-bold">{result.gdt?.length || 0}</p>
                      <p className="text-sm text-muted-foreground">GD&T</p>
                    </div>
                    <div className="text-center p-4 bg-accent rounded-lg">
                      <p className="text-2xl font-bold">{result.text?.total_blocks || 0}</p>
                      <p className="text-sm text-muted-foreground">Text Blocks</p>
                    </div>
                    {version === 'v2' && (
                      <div className="text-center p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
                        <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                          {result.text?.tables?.length || 0}
                        </p>
                        <p className="text-sm text-blue-600 dark:text-blue-400">Tables</p>
                      </div>
                    )}
                  </div>

                  {/* Dimensions */}
                  {result.dimensions && result.dimensions.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-semibold mb-2">Dimensions</h4>
                      <div className="space-y-2">
                        {result.dimensions.slice(0, 5).map((dim, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-background border rounded flex items-center justify-between"
                          >
                            <div>
                              <Badge>{dim.type}</Badge>
                              <span className="ml-2 font-mono">
                                {dim.value} {dim.unit}
                              </span>
                            </div>
                            {dim.tolerance && (
                              <span className="text-sm text-muted-foreground">
                                ±{dim.tolerance}
                              </span>
                            )}
                          </div>
                        ))}
                        {result.dimensions.length > 5 && (
                          <p className="text-sm text-muted-foreground text-center">
                            ... and {result.dimensions.length - 5} more
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Tables (v2 only) */}
                  {version === 'v2' && result.text?.tables && result.text.tables.length > 0 && (
                    <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <Layers className="h-4 w-4 text-blue-500" />
                        Tables (v2 Feature)
                      </h4>
                      <div className="space-y-2">
                        {result.text.tables.map((table: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-3 bg-white dark:bg-slate-900 border rounded"
                          >
                            <p className="text-sm">
                              <span className="font-medium">Table {idx + 1}:</span>{' '}
                              {table.rows || 0} rows × {table.cols || 0} columns
                            </p>
                            {table.location && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Location: ({table.location[0]}, {table.location[1]})
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Server-side Visualization Image (if available) */}
              {result.visualization_url && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>서버 생성 시각화 이미지</span>
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => {
                          setModalImageSrc(`http://localhost:${version === 'v1' ? '5001' : '5002'}${result.visualization_url}`);
                          setShowImageModal(true);
                        }}
                      >
                        <ZoomIn className="h-4 w-4 mr-2" />
                        확대 보기
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <img
                      src={`http://localhost:${version === 'v1' ? '5001' : '5002'}${result.visualization_url}`}
                      alt="OCR Visualization"
                      className="w-full border rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                      onClick={() => {
                        setModalImageSrc(`http://localhost:${version === 'v1' ? '5001' : '5002'}${result.visualization_url}`);
                        setShowImageModal(true);
                      }}
                    />
                    <p className="text-sm text-muted-foreground mt-2">
                      eDOCr {version.toUpperCase()} API에서 생성된 시각화 이미지 (클릭하면 확대됩니다)
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* Server-side Visualization - v2 feature */}
              {result?.visualization && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>시각화 결과 (Server-side)</span>
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => {
                          setModalImageSrc(`http://localhost:5002/api/v2/results/${result.visualization}`);
                          setShowImageModal(true);
                        }}
                      >
                        <ZoomIn className="h-4 w-4 mr-2" />
                        확대 보기
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex gap-2 items-center text-sm text-muted-foreground mb-4">
                        <div className="flex items-center gap-1">
                          <div className="w-4 h-4 bg-green-500"></div>
                          <span>Dimensions (D0, D1, ...)</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-4 h-4 bg-blue-500"></div>
                          <span>GD&T (G0, G1, ...)</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-4 h-4 bg-red-500"></div>
                          <span>Text (T0, T1, ...)</span>
                        </div>
                      </div>
                      <img
                        src={`http://localhost:5002/api/v2/results/${result.visualization}`}
                        alt="OCR Visualization"
                        className="w-full border rounded cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={() => {
                          setModalImageSrc(`http://localhost:5002/api/v2/results/${result.visualization}`);
                          setShowImageModal(true);
                        }}
                      />
                      <p className="text-xs text-muted-foreground text-center">
                        이미지를 클릭하면 확대해서 볼 수 있습니다
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Client-side OCR Visualization - only for images */}
              {file && file.type.startsWith('image/') && !result?.visualization && (
                <OCRVisualization
                  imageFile={file}
                  ocrResult={result}
                  onZoomClick={(imageDataUrl) => {
                    setModalImageSrc(imageDataUrl);
                    setShowImageModal(true);
                  }}
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
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="mb-2">파일을 업로드하고 OCR을 실행하세요</p>
                <p className="text-sm">
                  현재 선택: <strong>{currentVersion.title}</strong>
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Image Zoom Modal */}
      {showImageModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={() => setShowImageModal(false)}
        >
          <div className="relative max-w-7xl max-h-full">
            <button
              onClick={() => setShowImageModal(false)}
              className="absolute -top-10 right-0 text-white hover:text-gray-300 transition-colors"
            >
              <X className="h-8 w-8" />
            </button>
            <img
              src={modalImageSrc}
              alt="Visualization Zoomed"
              className="max-w-full max-h-[90vh] object-contain rounded"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}
    </div>
  );
}
