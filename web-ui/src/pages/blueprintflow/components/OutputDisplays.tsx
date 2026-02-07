/**
 * OutputDisplays Component
 * 워크플로우 실행 결과의 다양한 출력 형식 표시
 *
 * ExecutionStatusPanel.tsx에서 추출
 */

import OCRVisualization from '../../../components/debug/OCRVisualization';
import ToleranceVisualization from '../../../components/debug/ToleranceVisualization';
import SegmentationVisualization from '../../../components/debug/SegmentationVisualization';
import DataTableView from '../../../components/blueprintflow/DataTableView';
import VisualizationImage from '../../../components/blueprintflow/VisualizationImage';
import { extractArrayData, extractVisualizationImages } from '../../../components/blueprintflow/outputExtractors';
import type {
  PipelineOutput,
  Detection,
  DimensionResult,
  TextResult,
  OCRBlock,
  SegmentResult,
  ToleranceItem,
} from '../types';

// Output display router
export function OutputDisplay({
  output,
  nodeType,
  nodeId,
  uploadedImage,
}: {
  output: PipelineOutput;
  nodeType: string;
  nodeId: string;
  uploadedImage: string | null;
}) {
  return (
    <>
      {/* Output Image - visualized_image 우선 (바운딩박스 포함) */}
      {(output.visualized_image || output.image) && (
        <OutputImageDisplay
          imageData={output.visualized_image || output.image || ''}
          nodeLabel={nodeType}
        />
      )}

      {/* Detections (YOLO) */}
      {output.detections && Array.isArray(output.detections) && (
        <DetectionsDisplay detections={output.detections} />
      )}

      {/* eDOCr2 Dimensions */}
      {output.dimensions && Array.isArray(output.dimensions) && (
        <DimensionsDisplay dimensions={output.dimensions} gdtCount={output.gdt?.length} />
      )}

      {/* OCR Visualization */}
      {(nodeType === 'edocr2' || nodeType.includes('ocr')) &&
       (output.dimensions || output.gdt) &&
       uploadedImage && (
        <div className="mt-3">
          <OCRVisualization
            imageBase64={uploadedImage}
            ocrResult={{
              dimensions: (output.dimensions || []) as { type: string; value: number; unit: string; tolerance: string | number | null }[],
              gdt: (output.gdt || []) as { type: string; value: number; datum: string | null }[],
              text: (typeof output.text === 'object' ? output.text : { total_blocks: 0 }) as { total_blocks?: number },
            }}
            compact={true}
          />
        </div>
      )}

      {/* Text Results */}
      {output.text && typeof output.text === 'string' && (
        <TextDisplay text={output.text} />
      )}

      {/* PaddleOCR Text Results */}
      {output.text_results && Array.isArray(output.text_results) && (
        <TextResultsDisplay textResults={output.text_results} />
      )}

      {/* OCR Blocks */}
      {output.blocks && Array.isArray(output.blocks) && (
        <BlocksDisplay blocks={output.blocks} />
      )}

      {/* Segmentation Results */}
      {output.segments && Array.isArray(output.segments) && (
        <SegmentsDisplay segments={output.segments} />
      )}
      {output.mask && (
        <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
          <div className="text-xs font-semibold text-green-900 dark:text-green-100">
            🎨 Segmentation Mask Available
          </div>
        </div>
      )}

      {/* Segmentation Visualization */}
      {nodeType === 'edgnet' && (output.num_components !== undefined || output.classifications) && (
        <div className="mt-3">
          <SegmentationVisualization
            imageBase64={uploadedImage || undefined}
            segmentationResult={{
              num_components: output.num_components || 0,
              classifications: output.classifications || { contour: 0, text: 0, dimension: 0 },
              graph: output.graph || { nodes: 0, edges: 0, avg_degree: 0 },
              vectorization: output.vectorization || { num_bezier_curves: 0, total_length: 0 },
            }}
            compact={true}
          />
        </div>
      )}

      {/* Tolerance Results */}
      {output.tolerances && Array.isArray(output.tolerances) && (
        <TolerancesDisplay tolerances={output.tolerances} />
      )}
      {output.analysis && typeof output.analysis === 'object' && (
        <AnalysisDisplay analysis={output.analysis} />
      )}

      {/* Tolerance Visualization */}
      {nodeType === 'skinmodel' && (output.manufacturability || output.predicted_tolerances) && (
        <div className="mt-3">
          <ToleranceVisualization
            toleranceData={{
              manufacturability: output.manufacturability,
              predicted_tolerances: output.predicted_tolerances,
              analysis: output.analysis,
            }}
            compact={true}
          />
        </div>
      )}

      {/* VL Results */}
      {output.result && typeof output.result === 'string' && (
        <VLResultDisplay result={output.result} />
      )}
      {output.description && typeof output.description === 'string' && (
        <VLDescriptionDisplay description={output.description} />
      )}

      {/* Data Table Views */}
      {(() => {
        const arrayData = extractArrayData(output as Record<string, unknown>);
        if (arrayData.length === 0) return null;
        return (
          <div className="mt-3 space-y-3">
            {arrayData.map(({ field, data, title }) => (
              <DataTableView
                key={field}
                data={data}
                title={title}
                nodeType={nodeType}
                exportFilename={`${nodeId}_${field}`}
                compact={true}
                pageSize={5}
              />
            ))}
          </div>
        );
      })()}

      {/* Visualization Images */}
      {(() => {
        const visualizations = extractVisualizationImages(output as Record<string, unknown>);
        const filteredVis = visualizations.filter(
          v => v.field !== 'image' && v.field !== 'visualized_image'
        );
        if (filteredVis.length === 0) return null;
        return (
          <div className="mt-3 space-y-2">
            {filteredVis.map(({ field, base64, title }) => (
              <VisualizationImage
                key={field}
                base64={base64}
                title={title}
                maxHeight="200px"
              />
            ))}
          </div>
        );
      })()}

      {/* Raw Data Viewer */}
      {Object.keys(output).length > 0 && (
        <details className="mt-2">
          <summary className="text-xs font-medium text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-gray-200">
            🔍 View Raw Data ({Object.keys(output).length} fields)
          </summary>
          <pre className="mt-2 p-2 bg-white dark:bg-gray-900 rounded text-xs overflow-auto max-h-60 border border-gray-200 dark:border-gray-700">
            {JSON.stringify(output, null, 2)}
          </pre>
        </details>
      )}
    </>
  );
}

// Helper components for output display
function OutputImageDisplay({ imageData, nodeLabel }: { imageData: string; nodeLabel: string }) {
  const src = imageData.startsWith('data:') ? imageData : `data:image/jpeg;base64,${imageData}`;
  return (
    <div className="mt-3">
      <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
        📸 Output Image:
      </div>
      <img
        src={src}
        alt={`${nodeLabel} result`}
        className="w-full h-auto rounded border border-gray-300 dark:border-gray-600 shadow-sm cursor-pointer hover:shadow-lg transition-shadow"
        onClick={(e) => {
          const img = e.currentTarget;
          const win = window.open('', '_blank');
          if (win) {
            win.document.write(`<img src="${img.src}" style="max-width:100%; height:auto;" />`);
          }
        }}
        title="클릭하여 크게 보기"
      />
    </div>
  );
}

function DetectionsDisplay({ detections }: { detections: Detection[] }) {
  return (
    <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
      <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">
        🎯 Detections: {detections.length} objects
      </div>
      <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
        {detections.slice(0, 3).map((det, i) => (
          <div key={i}>
            • {det.class_name || det.class || 'Unknown'} ({(det.confidence * 100).toFixed(1)}%)
          </div>
        ))}
        {detections.length > 3 && (
          <div className="text-blue-500 dark:text-blue-400">
            ... and {detections.length - 3} more
          </div>
        )}
      </div>
    </div>
  );
}

function DimensionsDisplay({ dimensions, gdtCount }: { dimensions: DimensionResult[]; gdtCount?: number }) {
  return (
    <div className="mt-2 p-2 bg-indigo-50 dark:bg-indigo-900/20 rounded border border-indigo-200 dark:border-indigo-800">
      <div className="text-xs font-semibold text-indigo-900 dark:text-indigo-100">
        📏 Dimensions: {dimensions.length}
        {(gdtCount ?? 0) > 0 && ` | GD&T: ${gdtCount}`}
      </div>
      <div className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">
        {dimensions.slice(0, 5).map((dim, i) => (
          <div key={i}>
            • {dim.type && `[${dim.type}] `}{dim.value || dim.text || JSON.stringify(dim).slice(0, 50)}{dim.unit || ''}{dim.tolerance ? ` ±${dim.tolerance}` : ''}
          </div>
        ))}
        {dimensions.length > 5 && (
          <div className="text-indigo-500 dark:text-indigo-400">
            ... and {dimensions.length - 5} more
          </div>
        )}
      </div>
    </div>
  );
}

function TextDisplay({ text }: { text: string }) {
  return (
    <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
      <div className="text-xs font-semibold text-purple-900 dark:text-purple-100">
        📝 Extracted Text:
      </div>
      <div className="text-xs text-purple-700 dark:text-purple-300 mt-1 whitespace-pre-wrap">
        {text.slice(0, 200)}
        {text.length > 200 && '...'}
      </div>
    </div>
  );
}

function TextResultsDisplay({ textResults }: { textResults: TextResult[] }) {
  return (
    <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
      <div className="text-xs font-semibold text-purple-900 dark:text-purple-100">
        📝 OCR Text Results: {textResults.length}
      </div>
      <div className="text-xs text-purple-700 dark:text-purple-300 mt-1">
        {textResults.slice(0, 5).map((textResult, i) => (
          <div key={i}>
            • {textResult.text || textResult.content || JSON.stringify(textResult).slice(0, 50)}
          </div>
        ))}
        {textResults.length > 5 && (
          <div className="text-purple-500 dark:text-purple-400">
            ... and {textResults.length - 5} more
          </div>
        )}
      </div>
    </div>
  );
}

function BlocksDisplay({ blocks }: { blocks: OCRBlock[] }) {
  return (
    <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
      <div className="text-xs font-semibold text-purple-900 dark:text-purple-100">
        📝 OCR Blocks: {blocks.length}
      </div>
      <div className="text-xs text-purple-700 dark:text-purple-300 mt-1">
        {blocks.slice(0, 3).map((block, i) => (
          <div key={i}>• {block.text || JSON.stringify(block).slice(0, 50)}</div>
        ))}
        {blocks.length > 3 && (
          <div className="text-purple-500 dark:text-purple-400">
            ... and {blocks.length - 3} more
          </div>
        )}
      </div>
    </div>
  );
}

function SegmentsDisplay({ segments }: { segments: SegmentResult[] }) {
  return (
    <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
      <div className="text-xs font-semibold text-green-900 dark:text-green-100">
        🎨 Segmentation: {segments.length} segments
      </div>
      <div className="text-xs text-green-700 dark:text-green-300 mt-1">
        {segments.slice(0, 3).map((seg, i) => (
          <div key={i}>
            • {seg.class || seg.type || `Segment ${i + 1}`}
            {seg.confidence && ` (${(seg.confidence * 100).toFixed(1)}%)`}
          </div>
        ))}
        {segments.length > 3 && (
          <div className="text-green-500 dark:text-green-400">
            ... and {segments.length - 3} more
          </div>
        )}
      </div>
    </div>
  );
}

function TolerancesDisplay({ tolerances }: { tolerances: ToleranceItem[] }) {
  return (
    <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200 dark:border-orange-800">
      <div className="text-xs font-semibold text-orange-900 dark:text-orange-100">
        📐 Tolerance Analysis: {tolerances.length} items
      </div>
      <div className="text-xs text-orange-700 dark:text-orange-300 mt-1">
        {tolerances.slice(0, 5).map((tol, i) => (
          <div key={i}>
            • {tol.dimension || tol.name || `Tolerance ${i + 1}`}
            {tol.value && `: ${tol.value}`}
          </div>
        ))}
        {tolerances.length > 5 && (
          <div className="text-orange-500 dark:text-orange-400">
            ... and {tolerances.length - 5} more
          </div>
        )}
      </div>
    </div>
  );
}

function AnalysisDisplay({ analysis }: { analysis: Record<string, unknown> }) {
  return (
    <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200 dark:border-orange-800">
      <div className="text-xs font-semibold text-orange-900 dark:text-orange-100">
        📐 Analysis Details:
      </div>
      <div className="text-xs text-orange-700 dark:text-orange-300 mt-1">
        {Object.entries(analysis).slice(0, 5).map(([key, value]) => (
          <div key={key}>• {key}: {String(value).slice(0, 50)}</div>
        ))}
      </div>
    </div>
  );
}

function VLResultDisplay({ result }: { result: string }) {
  return (
    <div className="mt-2 p-2 bg-pink-50 dark:bg-pink-900/20 rounded border border-pink-200 dark:border-pink-800">
      <div className="text-xs font-semibold text-pink-900 dark:text-pink-100">
        🤖 VL Result:
      </div>
      <div className="text-xs text-pink-700 dark:text-pink-300 mt-1 whitespace-pre-wrap">
        {result.slice(0, 300)}
        {result.length > 300 && '...'}
      </div>
    </div>
  );
}

function VLDescriptionDisplay({ description }: { description: string }) {
  return (
    <div className="mt-2 p-2 bg-pink-50 dark:bg-pink-900/20 rounded border border-pink-200 dark:border-pink-800">
      <div className="text-xs font-semibold text-pink-900 dark:text-pink-100">
        🤖 AI Description:
      </div>
      <div className="text-xs text-pink-700 dark:text-pink-300 mt-1 whitespace-pre-wrap">
        {description.slice(0, 300)}
        {description.length > 300 && '...'}
      </div>
    </div>
  );
}
