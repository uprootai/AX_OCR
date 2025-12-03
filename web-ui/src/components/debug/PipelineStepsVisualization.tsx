import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { ChevronDown, ChevronRight, ZoomIn, CheckCircle, Clock } from 'lucide-react';

interface PipelineStep {
  id: string;
  label: string;
  description: string;
  image?: string; // base64 or URL
  data: any;
  processingTime?: number;
  status: 'completed' | 'pending' | 'skipped';
}

interface PipelineStepsVisualizationProps {
  imageFile: File;
  result: any; // Full API response
}

export default function PipelineStepsVisualization({ imageFile, result }: PipelineStepsVisualizationProps) {
  const [expandedStep, setExpandedStep] = useState<string | null>('yolo');

  // 단계별 데이터 구성
  const steps: PipelineStep[] = [
    {
      id: 'original',
      label: '원본 이미지',
      description: '업로드된 원본 도면',
      image: URL.createObjectURL(imageFile),
      data: {
        filename: imageFile.name,
        size: `${(imageFile.size / 1024).toFixed(2)} KB`,
        type: imageFile.type
      },
      status: 'completed'
    },
    {
      id: 'yolo',
      label: 'YOLO 객체 검출',
      description: 'YOLOv11로 치수, GD&T, 텍스트 블록 검출',
      image: result.data?.yolo_results?.visualized_image
        ? `data:image/jpeg;base64,${result.data.yolo_results.visualized_image}`
        : undefined,
      data: {
        total_detections: result.data?.yolo_results?.total_detections || 0,
        classes: result.data?.yolo_results?.detections?.reduce((acc: Record<string, number>, det: { class_name?: string; class?: string }) => {
          const className = det.class_name || det.class || 'unknown';
          acc[className] = (acc[className] || 0) + 1;
          return acc;
        }, {} as Record<string, number>) || {}
      },
      processingTime: result.data?.yolo_results?.processing_time,
      status: result.data?.yolo_results ? 'completed' : 'skipped'
    },
    {
      id: 'ocr',
      label: 'OCR 텍스트 추출',
      description: 'eDOCr v2로 치수 값 인식',
      image: result.data?.ocr_results?.visualized_image
        ? `data:image/jpeg;base64,${result.data.ocr_results.visualized_image}`
        : undefined,
      data: {
        dimensions_count: result.data?.ocr_results?.dimensions?.length || 0,
        gdt_count: result.data?.ocr_results?.gdt_symbols?.length || 0,
        dimensions: result.data?.ocr_results?.dimensions || []
      },
      processingTime: result.data?.ocr_results?.processing_time,
      status: result.data?.ocr_results ? 'completed' : 'skipped'
    },
    {
      id: 'edgnet',
      label: 'EDGNet 구조 분석',
      description: 'GraphSAGE 기반 레이어 분류',
      image: result.data?.segmentation_results?.visualized_image
        ? `data:image/jpeg;base64,${result.data.segmentation_results.visualized_image}`
        : undefined,
      data: {
        components_count: result.data?.segmentation_results?.total_components || 0,
        nodes: result.data?.segmentation_results?.components?.length || 0,
        edges: 0,
        status_message: result.data?.segmentation_results?.components ? 'completed' : 'unknown'
      },
      processingTime: result.data?.segmentation_results?.processing_time,
      status: result.data?.segmentation_results ? 'completed' : 'skipped'
    },
    {
      id: 'ensemble',
      label: '결과 통합',
      description: 'YOLO + OCR + EDGNet 병합',
      image: result.data?.ensemble?.visualized_image
        ? `data:image/jpeg;base64,${result.data.ensemble.visualized_image}`
        : undefined,
      data: {
        final_dimensions: result.data?.ensemble?.dimensions?.length || 0,
        yolo_count: result.data?.yolo_results?.total_detections || 0,
        ocr_count: result.data?.ocr_results?.dimensions?.length || 0,
        strategy: result.data?.ensemble?.strategy || 'Basic'
      },
      status: (result.data?.ensemble || result.data?.ocr_results) ? 'completed' : 'skipped'
    },
    {
      id: 'tolerance',
      label: '공차 예측',
      description: 'Skin Model로 제조 가능성 분석',
      image: result.data?.tolerance_results?.data?.visualized_image
        ? `data:image/jpeg;base64,${result.data.tolerance_results.data.visualized_image}`
        : undefined,
      data: {
        manufacturability_score: result.data?.tolerance_results?.data?.manufacturability?.score || 0,
        difficulty: result.data?.tolerance_results?.data?.manufacturability?.difficulty || 'N/A'
      },
      processingTime: result.data?.tolerance_results?.processing_time,
      status: result.data?.tolerance_results ? 'completed' : 'skipped'
    }
  ];

  const handleImageClick = (imageUrl: string) => {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
      <div class="relative max-w-7xl w-full">
        <img src="${imageUrl}" class="w-full h-auto max-h-[90vh] object-contain rounded-lg" />
        <button class="absolute top-4 right-4 bg-white/10 hover:bg-white/20 text-white text-3xl font-bold w-12 h-12 rounded-full flex items-center justify-center">&times;</button>
      </div>
    `;
    modal.onclick = () => modal.remove();
    document.body.appendChild(modal);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>파이프라인 단계별 시각화</CardTitle>
        <p className="text-sm text-muted-foreground">
          각 단계의 처리 결과를 시각적으로 확인하세요
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {steps.map((step) => {
          const isExpanded = expandedStep === step.id;
          const isSkipped = step.status === 'skipped';

          return (
            <div
              key={step.id}
              className={`border rounded-lg overflow-hidden transition-all ${
                isSkipped ? 'opacity-50' : ''
              }`}
            >
              {/* Step Header */}
              <button
                onClick={() => setExpandedStep(isExpanded ? null : step.id)}
                className="w-full p-4 flex items-center justify-between hover:bg-accent transition-colors"
              >
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown className="w-5 h-5 text-primary" />
                  ) : (
                    <ChevronRight className="w-5 h-5" />
                  )}
                  <div className="text-left">
                    <p className="font-semibold flex items-center gap-2">
                      {step.label}
                      {step.status === 'completed' && (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                      {isSkipped && (
                        <Badge variant="outline" className="text-xs">건너뜀</Badge>
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">{step.description}</p>
                  </div>
                </div>
                {step.processingTime !== undefined && (
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    {(step.processingTime / 1000).toFixed(2)}s
                  </div>
                )}
              </button>

              {/* Step Content */}
              {isExpanded && !isSkipped && (
                <div className="p-4 border-t bg-accent/20 space-y-4">
                  {/* Visualization Image */}
                  {step.image && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-medium">시각화 결과</p>
                        <button
                          onClick={() => handleImageClick(step.image!)}
                          className="text-sm text-primary hover:underline flex items-center gap-1"
                        >
                          <ZoomIn className="w-4 h-4" />
                          확대 보기
                        </button>
                      </div>
                      <img
                        src={step.image}
                        alt={step.label}
                        className="w-full h-auto border rounded cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={() => handleImageClick(step.image!)}
                      />
                    </div>
                  )}

                  {/* Data Details */}
                  <div>
                    <p className="text-sm font-medium mb-2">처리 결과</p>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(step.data).map(([key, value]) => {
                        // Skip complex objects and arrays for display
                        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                          return null;
                        }

                        // Format arrays
                        if (Array.isArray(value)) {
                          return (
                            <div key={key} className="col-span-2 p-2 bg-background rounded text-xs">
                              <span className="font-medium">{key}:</span>
                              <span className="ml-2 text-muted-foreground">
                                {value.length}개 항목
                              </span>
                            </div>
                          );
                        }

                        return (
                          <div key={key} className="p-2 bg-background rounded text-xs">
                            <p className="font-medium text-muted-foreground">{key}</p>
                            <p className="text-sm font-semibold">{String(value)}</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Detailed List for Dimensions */}
                  {step.id === 'ocr' && step.data.dimensions && step.data.dimensions.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">검출된 치수 (상위 10개)</p>
                      <div className="max-h-48 overflow-y-auto space-y-1">
                        {step.data.dimensions.slice(0, 10).map((dim: { value?: string | number; text?: string; confidence: number }, idx: number) => (
                          <div key={idx} className="flex items-center justify-between p-2 bg-background rounded text-xs">
                            <span className="font-mono font-semibold">{dim.value || dim.text}</span>
                            <Badge variant="outline" className="text-xs">
                              {(dim.confidence * 100).toFixed(0)}%
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Class Distribution for YOLO */}
                  {step.id === 'yolo' && Object.keys(step.data.classes).length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">검출 클래스 분포</p>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(step.data.classes).map(([className, count]) => (
                          <div key={className} className="flex items-center justify-between p-2 bg-background rounded text-xs">
                            <span>{className}</span>
                            <Badge variant="outline">{String(count)}개</Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Summary */}
        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-950 dark:to-green-950 rounded-lg border">
          <h4 className="font-semibold mb-2">처리 완료</h4>
          <p className="text-sm text-muted-foreground">
            총 {steps.filter(s => s.status === 'completed').length}/{steps.length} 단계 완료
            (처리 시간: {result.processing_time ? (result.processing_time / 1000).toFixed(2) : '0'}s)
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
