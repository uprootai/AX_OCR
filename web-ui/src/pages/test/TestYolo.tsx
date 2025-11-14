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
import YOLOVisualization from '../../components/debug/YOLOVisualization';
import Mermaid from '../../components/ui/Mermaid';
import { yoloApi } from '../../lib/api';
import { useMonitoringStore } from '../../store/monitoringStore';
import { Loader2, Play, ZoomIn, X, BookOpen, Info } from 'lucide-react';
import type { RequestTrace } from '../../types/api';

export default function TestYolo() {
  const [file, setFile] = useState<File | null>(null);
  const [showImageModal, setShowImageModal] = useState(false);
  const [modalImageSrc, setModalImageSrc] = useState('');
  const [showGuide, setShowGuide] = useState(true);
  const [options, setOptions] = useState({
    conf_threshold: 0.25,
    iou_threshold: 0.7,
    imgsz: 1280,
    visualize: true,
  });
  const [result, setResult] = useState<any>(null);
  const [selectedTrace, setSelectedTrace] = useState<RequestTrace | null>(null);

  const { traces, addTrace } = useMonitoringStore();
  const yoloTraces = traces.filter((t) => t.endpoint.includes('yolo') || t.endpoint.includes('/detect'));

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      const startTime = Date.now();
      const traceId = `yolo-${Date.now()}`;

      try {
        const response = await yoloApi.detect(file, options);
        const duration = Date.now() - startTime;

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint: '/api/v1/detect',
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
        return response;
      } catch (error: any) {
        const duration = Date.now() - startTime;

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint: '/api/v1/detect',
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

  const handleSubmit = () => {
    if (file) {
      mutation.mutate(file);
    }
  };

  const openImageModal = (src: string) => {
    setModalImageSrc(src);
    setShowImageModal(true);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              YOLOv11 Object Detection
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              공학 도면에서 치수, GD&T, 공차 등 14개 클래스를 자동으로 검출합니다 (mAP50: 80.4%)
            </p>
          </div>
          <Button
            variant={showGuide ? 'default' : 'outline'}
            onClick={() => setShowGuide(!showGuide)}
          >
            <BookOpen className="w-4 h-4 mr-2" />
            {showGuide ? '가이드 숨기기' : '가이드 보기'}
          </Button>
        </div>

        {/* Detection Classes Summary */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-0.5">
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white font-bold text-sm">
                14
              </span>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                🎯 검출 가능한 객체 클래스
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
                <div className="space-y-1">
                  <p className="font-medium text-blue-900 dark:text-blue-100">📏 치수 (6종)</p>
                  <ul className="text-gray-700 dark:text-gray-300 space-y-0.5 ml-4">
                    <li>• 직경 (diameter_dim)</li>
                    <li>• 선형 (linear_dim)</li>
                    <li>• 반경 (radius_dim)</li>
                    <li>• 각도 (angular_dim)</li>
                    <li>• 모따기 (chamfer_dim)</li>
                    <li>• 공차 (tolerance_dim)</li>
                  </ul>
                </div>
                <div className="space-y-1">
                  <p className="font-medium text-purple-900 dark:text-purple-100">📐 GD&T (5종)</p>
                  <ul className="text-gray-700 dark:text-gray-300 space-y-0.5 ml-4">
                    <li>• 평면도 (flatness)</li>
                    <li>• 원통도 (cylindricity)</li>
                    <li>• 위치도 (position)</li>
                    <li>• 수직도 (perpendicularity)</li>
                    <li>• 평행도 (parallelism)</li>
                  </ul>
                </div>
                <div className="space-y-1">
                  <p className="font-medium text-green-900 dark:text-green-100">🔧 기타 (3종)</p>
                  <ul className="text-gray-700 dark:text-gray-300 space-y-0.5 ml-4">
                    <li>• 표면 거칠기 (surface_roughness)</li>
                    <li>• 참조 치수 (reference_dim)</li>
                    <li>• 텍스트 블록 (text_block)</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Usage Guide Section */}
      {showGuide && (
        <Card className="mb-6 border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20">
          <CardHeader>
            <CardTitle className="flex items-center text-blue-900 dark:text-blue-100">
              <Info className="w-5 h-5 mr-2" />
              YOLOv11 사용 가이드
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* System Architecture */}
            <div>
              <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
                📊 시스템 아키텍처
              </h3>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <Mermaid chart={`graph TB
    A["도면 이미지 업로드"] --> B["YOLOv11 API\n포트 5005"]
    B --> C["합성 데이터로 학습된 모델\nmAP50: 80.4%"]
    C --> D["객체 검출 수행"]
    D --> E["14개 클래스 분류"]
    E --> F1["치수: 직경, 선형, 반경, 각도"]
    E --> F2["GD&T: 평면도, 원통도, 위치도"]
    E --> F3["공차 및 표면 거칠기"]
    E --> F4["텍스트 블록"]
    F1 --> G["결과 반환\n(bbox, 신뢰도, 클래스)"]
    F2 --> G
    F3 --> G
    F4 --> G
    G --> H["시각화 이미지 생성\n(선택사항)"]

    style A fill:#1e3a8a,stroke:#60a5fa,stroke-width:3px,color:#fff
    style B fill:#1e40af,stroke:#3b82f6,stroke-width:3px,color:#fff
    style C fill:#065f46,stroke:#34d399,stroke-width:3px,color:#fff
    style D fill:#0c4a6e,stroke:#38bdf8,stroke-width:3px,color:#fff
    style E fill:#164e63,stroke:#22d3ee,stroke-width:3px,color:#fff
    style G fill:#78350f,stroke:#fbbf24,stroke-width:3px,color:#fff
    style H fill:#9a3412,stroke:#fb923c,stroke-width:3px,color:#fff`} />
              </div>
            </div>

            {/* Training Pipeline */}
            <div>
              <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
                🔄 학습 파이프라인
              </h3>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <Mermaid chart={`sequenceDiagram
    participant U as 사용자
    participant S as 합성 데이터 생성기
    participant T as 학습 스크립트
    participant M as YOLOv11 모델
    participant A as API 서버

    U->>S: 1. 합성 데이터 생성 (1000개 이미지)
    S->>S: 2. 랜덤 배치 (크기/방향/위치)
    S->>T: 3. 데이터셋 준비 (700/150/150)
    T->>M: 4. 학습 시작 (100 epochs)
    M->>M: 5. 전이 학습 (COCO weights)
    M->>T: 6. 학습 완료 (mAP50: 80.4%)
    T->>A: 7. 모델 배포 (best.pt)
    A->>U: 8. 추론 준비 완료`} />
              </div>
            </div>

            {/* Detected Classes */}
            <div>
              <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
                🎯 검출 가능한 14개 클래스
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div className="bg-white dark:bg-gray-800 p-3 rounded border">
                  <p className="font-semibold text-sm">치수 (Dimensions)</p>
                  <ul className="text-xs mt-1 space-y-1 text-gray-600 dark:text-gray-400">
                    <li>• 직경 (diameter_dim)</li>
                    <li>• 선형 (linear_dim)</li>
                    <li>• 반경 (radius_dim)</li>
                    <li>• 각도 (angular_dim)</li>
                    <li>• 모따기 (chamfer_dim)</li>
                  </ul>
                </div>
                <div className="bg-white dark:bg-gray-800 p-3 rounded border">
                  <p className="font-semibold text-sm">GD&T</p>
                  <ul className="text-xs mt-1 space-y-1 text-gray-600 dark:text-gray-400">
                    <li>• 평면도 (flatness)</li>
                    <li>• 원통도 (cylindricity)</li>
                    <li>• 위치도 (position)</li>
                    <li>• 직각도 (perpendicularity)</li>
                    <li>• 평행도 (parallelism)</li>
                  </ul>
                </div>
                <div className="bg-white dark:bg-gray-800 p-3 rounded border">
                  <p className="font-semibold text-sm">기타</p>
                  <ul className="text-xs mt-1 space-y-1 text-gray-600 dark:text-gray-400">
                    <li>• 공차 (tolerance_dim)</li>
                    <li>• 참조치수 (reference_dim)</li>
                    <li>• 표면거칠기 (surface_roughness)</li>
                    <li>• 텍스트블록 (text_block)</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Usage Steps */}
            <div>
              <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
                📝 사용 방법
              </h3>
              <ol className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                <li className="flex items-start">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0">
                    1
                  </span>
                  <span>
                    <strong>파일 업로드:</strong> 공학 도면 이미지를 업로드합니다 (JPG, PNG)
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0">
                    2
                  </span>
                  <span>
                    <strong>옵션 설정:</strong> 신뢰도 임계값(0.25 권장), 이미지 크기(1280 권장), 시각화 여부를 선택합니다
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0">
                    3
                  </span>
                  <span>
                    <strong>검출 실행:</strong> "Run Detection" 버튼을 클릭하여 분석을 시작합니다
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0">
                    4
                  </span>
                  <span>
                    <strong>결과 확인:</strong> 검출된 객체 목록, 바운딩 박스, 신뢰도를 확인합니다
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0">
                    5
                  </span>
                  <span>
                    <strong>시각화 보기:</strong> 시각화를 활성화한 경우 검출 결과가 표시된 이미지를 확인할 수 있습니다
                  </span>
                </li>
              </ol>
            </div>

            {/* Performance Info */}
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4 rounded-lg">
              <h4 className="font-semibold text-green-900 dark:text-green-100 mb-2">
                ⚡ 성능 지표
              </h4>
              <ul className="text-sm space-y-1 text-green-800 dark:text-green-200">
                <li>• <strong>mAP50:</strong> 80.4% (eDOCr 8.3% 대비 <strong>10배 향상</strong>)</li>
                <li>• <strong>mAP50-95:</strong> 62.4%</li>
                <li>• <strong>Precision:</strong> 81%</li>
                <li>• <strong>Recall:</strong> 68.6%</li>
                <li>• <strong>처리 시간:</strong> 이미지당 ~1-2초 (CPU 기준)</li>
                <li>• <strong>비용:</strong> 완전 무료 (자체 호스팅)</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Input & Options */}
        <div className="space-y-6">
          {/* File Upload */}
          <Card>
            <CardHeader>
              <CardTitle>1. 이미지 업로드</CardTitle>
            </CardHeader>
            <CardContent>
              <FileUploader currentFile={file} onFileSelect={setFile} />
            </CardContent>
          </Card>

          {/* Detection Options */}
          <Card>
            <CardHeader>
              <CardTitle>2. 검출 옵션</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Confidence Threshold: {options.conf_threshold}
                  <span className="text-gray-500 ml-2 text-xs">
                    (낮을수록 더 많이 검출, 높을수록 정확도 향상)
                  </span>
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={options.conf_threshold}
                  onChange={(e) =>
                    setOptions({ ...options, conf_threshold: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  IOU Threshold: {options.iou_threshold}
                  <span className="text-gray-500 ml-2 text-xs">
                    (중복 검출 제거 기준)
                  </span>
                </label>
                <input
                  type="range"
                  min="0.3"
                  max="0.9"
                  step="0.05"
                  value={options.iou_threshold}
                  onChange={(e) =>
                    setOptions({ ...options, iou_threshold: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Image Size
                </label>
                <select
                  value={options.imgsz}
                  onChange={(e) =>
                    setOptions({ ...options, imgsz: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
                >
                  <option value={640}>640 (빠름)</option>
                  <option value={1280}>1280 (권장)</option>
                  <option value={1920}>1920 (고해상도)</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="visualize"
                  checked={options.visualize}
                  onChange={(e) =>
                    setOptions({ ...options, visualize: e.target.checked })
                  }
                  className="mr-2"
                />
                <label htmlFor="visualize" className="text-sm font-medium">
                  Generate Visualization
                </label>
              </div>
            </CardContent>
          </Card>

          {/* Run Button */}
          <Card>
            <CardContent className="pt-6">
              <Button
                onClick={handleSubmit}
                disabled={!file || mutation.isPending}
                className="w-full"
                size="lg"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Detecting...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Run Detection
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Results */}
        <div className="space-y-6">
          {/* Error Display */}
          {mutation.isError && <ErrorPanel error={mutation.error as any} />}

          {/* Results */}
          {result && (
            <>
              {/* Detection Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Detection Results</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Total Detections
                        </p>
                        <p className="text-2xl font-bold">
                          {result.detection_count}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Processing Time
                        </p>
                        <p className="text-2xl font-bold">
                          {result.processing_time.toFixed(2)}s
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        Model Info
                      </p>
                      <div className="flex gap-2">
                        <Badge>{result.model_info?.model_name || 'YOLOv11n'}</Badge>
                        <Badge variant="outline">
                          {result.model_info?.device || 'CPU'}
                        </Badge>
                      </div>
                    </div>

                    {/* Detected Objects List */}
                    <div>
                      <p className="text-sm font-medium mb-2">Detected Objects:</p>
                      <div className="max-h-64 overflow-y-auto space-y-2">
                        {result.detections?.map((det: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-3 bg-gray-50 dark:bg-gray-800 rounded border"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <Badge>{det.class_name}</Badge>
                              <span className="text-sm font-semibold">
                                {(det.confidence * 100).toFixed(1)}%
                              </span>
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              Position: ({det.bbox.x}, {det.bbox.y}) | Size:{' '}
                              {det.bbox.width} × {det.bbox.height}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* YOLO Bounding Box Visualization */}
              {result.detections && result.detections.length > 0 && file && (
                <YOLOVisualization
                  imageFile={file}
                  detections={result.detections}
                  onZoomClick={openImageModal}
                />
              )}

              {/* Visualized Image */}
              {result.visualized_image && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>Visualization</span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openImageModal(`data:image/png;base64,${result.visualized_image}`)}
                      >
                        <ZoomIn className="w-4 h-4" />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <img
                      src={`data:image/png;base64,${result.visualized_image}`}
                      alt="Visualization"
                      className="w-full rounded-lg cursor-pointer"
                      onClick={() => openImageModal(`data:image/png;base64,${result.visualized_image}`)}
                    />
                  </CardContent>
                </Card>
              )}

              {/* JSON Response */}
              <Card>
                <CardHeader>
                  <CardTitle>Full Response</CardTitle>
                </CardHeader>
                <CardContent>
                  <JSONViewer data={result} />
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>

      {/* Request History */}
      {yoloTraces.length > 0 && (
        <div className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Request Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <RequestTimeline traces={yoloTraces} onSelectTrace={setSelectedTrace} />
            </CardContent>
          </Card>

          {selectedTrace && (
            <Card>
              <CardHeader>
                <CardTitle>Request Inspector</CardTitle>
              </CardHeader>
              <CardContent>
                <RequestInspector trace={selectedTrace} />
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Image Modal */}
      {showImageModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={() => setShowImageModal(false)}
        >
          <div className="relative max-w-7xl max-h-full">
            <button
              onClick={() => setShowImageModal(false)}
              className="absolute top-4 right-4 bg-white dark:bg-gray-800 p-2 rounded-full shadow-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={modalImageSrc}
              alt="Full size"
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
            />
          </div>
        </div>
      )}
    </div>
  );
}
