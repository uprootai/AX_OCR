import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import Mermaid from '../../../../components/ui/Mermaid';
import ImageZoom from '../../../../components/ui/ImageZoom';

interface BlueprintFlowSectionProps {
  sectionRef: (el: HTMLElement | null) => void;
}

export function BlueprintFlowSection({ sectionRef }: BlueprintFlowSectionProps) {
  const { t } = useTranslation();

  const workflowBuilderChart = `flowchart LR
    subgraph Left["Left Sidebar"]
        NP[Node Palette]
        API[API Nodes x21]
        CTL[Control Nodes x3]
    end

    subgraph Center["Center Canvas"]
        RF[ReactFlow]
        CN[Custom Nodes]
        MM[Minimap]
    end

    subgraph Right["Right Panel"]
        PP[Properties Panel]
        PE[Parameter Editor]
    end

    NP --> RF
    RF --> PP

    style Center fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Left fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style Right fill:#e8f5e9,stroke:#388e3c,stroke-width:2px`;

  const conditionalBranchChart = `flowchart LR
    A[YOLO] --> B{IF Node}
    B -->|detections > 0| C[eDOCr2]
    B -->|else| D[PaddleOCR]
    C --> E[Result]
    D --> E

    style B fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    style C fill:#d1fae5,stroke:#10b981,stroke-width:2px
    style D fill:#e5e7eb,stroke:#6b7280,stroke-width:2px`;

  return (
    <section
      id="blueprintflow"
      ref={sectionRef}
      className="mb-12 scroll-mt-20"
    >
      <Card className="border-4 border-green-500">
        <CardHeader className="bg-green-50 dark:bg-green-900/20">
          <CardTitle className="flex items-center text-green-900 dark:text-green-100">
            <span className="text-2xl mr-2">[Complete]</span>
            BlueprintFlow (Phase 1-4 Complete)
            <Badge className="ml-3 bg-green-600">Implemented</Badge>
          </CardTitle>
          <p className="text-sm text-green-800 dark:text-green-200 mt-2">
            Visual Workflow Builder - Drag and drop to compose API pipelines
          </p>
          <div className="mt-3 flex gap-2">
            <a href="/blueprintflow/builder" className="px-3 py-1 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition-colors">
              Open Builder
            </a>
            <a href="/blueprintflow/templates" className="px-3 py-1 bg-green-100 text-green-800 rounded-lg text-sm hover:bg-green-200 transition-colors dark:bg-green-800 dark:text-green-100">
              View Templates
            </a>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Implementation Status */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 rounded text-center">
                <div className="text-3xl font-bold text-green-600 dark:text-green-400">31</div>
                <div className="text-sm text-green-800 dark:text-green-200">Node Types</div>
              </div>
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded text-center">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">21</div>
                <div className="text-sm text-blue-800 dark:text-blue-200">API Services</div>
              </div>
              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border-l-4 border-purple-500 rounded text-center">
                <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">729</div>
                <div className="text-sm text-purple-800 dark:text-purple-200">Tests Passing</div>
              </div>
              <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 border-l-4 border-cyan-500 rounded text-center">
                <div className="text-3xl font-bold text-cyan-600 dark:text-cyan-400">27</div>
                <div className="text-sm text-cyan-800 dark:text-cyan-200">API Specs</div>
              </div>
            </div>

            {/* Node Types */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">Supported Node Types (31)</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded">
                  <strong>Input (2)</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>* ImageInput, TextInput</li>
                  </ul>
                </div>
                <div className="p-2 bg-cyan-100 dark:bg-cyan-900/30 rounded">
                  <strong>Detection (2)</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>* YOLO, Table Detector</li>
                  </ul>
                </div>
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded">
                  <strong>OCR (8)</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>* eDOCr2, PaddleOCR</li>
                    <li>* Tesseract, TrOCR</li>
                    <li>* OCR Ensemble, SuryaOCR</li>
                    <li>* DocTR, EasyOCR</li>
                  </ul>
                </div>
                <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded">
                  <strong>Segmentation (2)</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>* EDGNet, Line Detector</li>
                  </ul>
                </div>
                <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded">
                  <strong>Preprocessing (1)</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>* ESRGAN (4x upscale)</li>
                  </ul>
                </div>
                <div className="p-2 bg-rose-100 dark:bg-rose-900/30 rounded">
                  <strong>Analysis (8)</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>* SkinModel, PID Analyzer</li>
                    <li>* Design Checker, Blueprint AI BOM</li>
                    <li>* GT Comparison, PDF/Excel Export</li>
                    <li>* PID Features, Verification Queue</li>
                  </ul>
                </div>
                <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded">
                  <strong>AI/Knowledge (3)</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>* VL (Vision-Language)</li>
                    <li>* Knowledge (GraphRAG)</li>
                    <li>* PID Composer</li>
                  </ul>
                </div>
                <div className="p-2 bg-gray-200 dark:bg-gray-700 rounded">
                  <strong>Control (3)</strong>
                  <ul className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                    <li>* IF, Loop, Merge</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Workflow Builder UI */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.workflowBuilderUI')}
              </h3>
              <ImageZoom>
                <Mermaid chart={workflowBuilderChart} />
              </ImageZoom>
            </div>

            {/* Conditional Branch Example */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.conditionalBranchExample')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {t('guide.conditionalBranchDesc')}
              </p>
              <ImageZoom>
                <Mermaid chart={conditionalBranchChart} />
              </ImageZoom>
            </div>

            {/* Reference Docs */}
            <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800 rounded-lg">
              <h4 className="font-semibold text-cyan-900 dark:text-cyan-100 mb-2 flex items-center">
                <span className="mr-2">{t('guide.detailedDesignDocs')}</span>
              </h4>
              <ul className="text-sm space-y-2 text-cyan-800 dark:text-cyan-200">
                <li>* <strong>Complete Design Doc:</strong> <code className="bg-cyan-100 dark:bg-cyan-900 px-2 py-1 rounded text-xs">docs/BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md</code></li>
                <li>* <strong>API Integration Guide:</strong> <code className="bg-cyan-100 dark:bg-cyan-900 px-2 py-1 rounded text-xs">docs/BLUEPRINTFLOW_API_INTEGRATION_GUIDE.md</code></li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
