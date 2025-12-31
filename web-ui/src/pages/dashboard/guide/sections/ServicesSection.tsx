import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';

interface ServicesSectionProps {
  sectionRef: (el: HTMLElement | null) => void;
}

export function ServicesSection({ sectionRef }: ServicesSectionProps) {
  const { t } = useTranslation();

  return (
    <section
      id="services"
      ref={sectionRef}
      className="mb-12 scroll-mt-20"
    >
      <Card>
        <CardHeader>
          <CardTitle>{t('guide.serviceRoles')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Gateway */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded text-sm">Gateway</span>
              </h3>
              <div className="p-4 border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-900/20">
                <h4 className="font-bold text-orange-900 dark:text-orange-100 mb-2">Gateway API (Port 8000)</h4>
                <p className="text-sm text-orange-800 dark:text-orange-200 mb-2">Orchestrator integrating all backend APIs</p>
                <ul className="text-xs space-y-1 text-orange-700 dark:text-orange-300">
                  <li><strong>* Endpoints:</strong> GET /api/v1/health, POST /api/v1/process, POST /api/v1/quote</li>
                  <li><strong>* Features:</strong> Merge multiple API results, single endpoint</li>
                </ul>
              </div>
            </div>

            {/* Detection */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-sm">Detection</span>
                <span className="text-sm text-muted-foreground">(2 engines)</span>
              </h3>
              <div className="grid md:grid-cols-2 gap-3">
                <div className="p-4 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20">
                  <h4 className="font-bold text-blue-900 dark:text-blue-100 mb-2">YOLOv11 API (Port 5005)</h4>
                  <p className="text-sm text-blue-800 dark:text-blue-200 mb-2">Detect 14 classes in engineering drawings</p>
                  <ul className="text-xs space-y-1 text-blue-700 dark:text-blue-300">
                    <li><strong>* Targets:</strong> Dimension lines, arrows, text, GD&T symbols, etc.</li>
                    <li><strong>* Features:</strong> Trained on synthetic data, CPU/GPU support</li>
                  </ul>
                </div>
                <div className="p-4 border-l-4 border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-bold text-emerald-900 dark:text-emerald-100">YOLO P&ID Mode</h4>
                    <Badge className="bg-emerald-600 text-xs">model_type</Badge>
                  </div>
                  <p className="text-sm text-emerald-800 dark:text-emerald-200 mb-2">P&ID symbol detection with model_type=pid_class_aware</p>
                  <ul className="text-xs space-y-1 text-emerald-700 dark:text-emerald-300">
                    <li><strong>* Targets:</strong> 15 valve types, 5 pump types, 20 instrument types, etc.</li>
                    <li><strong>* Config:</strong> model_type: pid_class_aware/pid_class_agnostic</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* OCR */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-sm">OCR</span>
                <span className="text-sm text-muted-foreground">(5 engines)</span>
              </h3>
              <div className="grid md:grid-cols-2 gap-3">
                <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20">
                  <h4 className="font-bold text-green-900 dark:text-green-100 text-sm">eDOCr2 (5002)</h4>
                  <p className="text-xs text-green-700 dark:text-green-300">Drawing-specific OCR, GD&T extraction</p>
                </div>
                <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20">
                  <h4 className="font-bold text-green-900 dark:text-green-100 text-sm">PaddleOCR (5006)</h4>
                  <p className="text-xs text-green-700 dark:text-green-300">General-purpose multilingual OCR, GPU accelerated</p>
                </div>
                <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20">
                  <h4 className="font-bold text-green-900 dark:text-green-100 text-sm">Tesseract (5008)</h4>
                  <p className="text-xs text-green-700 dark:text-green-300">Legacy OCR, table extraction</p>
                </div>
                <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20">
                  <h4 className="font-bold text-green-900 dark:text-green-100 text-sm">TrOCR (5009)</h4>
                  <p className="text-xs text-green-700 dark:text-green-300">Transformer OCR, handwriting recognition</p>
                </div>
                <div className="p-3 border-l-4 border-amber-500 bg-amber-50 dark:bg-amber-900/20 md:col-span-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-amber-900 dark:text-amber-100 text-sm">OCR Ensemble (5011)</h4>
                    <Badge className="bg-amber-600 text-xs">Ensemble</Badge>
                  </div>
                  <p className="text-xs text-amber-700 dark:text-amber-300">4-engine weighted voting fusion</p>
                </div>
              </div>
            </div>

            {/* Segmentation */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-sm">Segmentation</span>
                <span className="text-sm text-muted-foreground">(2 engines)</span>
              </h3>
              <div className="grid md:grid-cols-2 gap-3">
                <div className="p-4 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20">
                  <h4 className="font-bold text-purple-900 dark:text-purple-100 mb-2">EDGNet API (Port 5012)</h4>
                  <p className="text-sm text-purple-800 dark:text-purple-200 mb-2">Drawing segmentation (layer separation)</p>
                  <ul className="text-xs space-y-1 text-purple-700 dark:text-purple-300">
                    <li><strong>* Models:</strong> UNet (edge), GraphSAGE (classification)</li>
                    <li><strong>* Features:</strong> Contour, text, dimension layer separation</li>
                  </ul>
                </div>
                <div className="p-4 border-l-4 border-teal-500 bg-teal-50 dark:bg-teal-900/20">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-bold text-teal-900 dark:text-teal-100">Line Detector (Port 5016)</h4>
                    <Badge className="bg-teal-600 text-xs">P&ID</Badge>
                  </div>
                  <p className="text-sm text-teal-800 dark:text-teal-200 mb-2">P&ID piping and signal line detection</p>
                  <ul className="text-xs space-y-1 text-teal-700 dark:text-teal-300">
                    <li><strong>* Algorithm:</strong> LSD + Hough Transform</li>
                    <li><strong>* Features:</strong> Line classification, intersection detection, merging</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* P&ID Analysis Pipeline */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="px-2 py-1 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 rounded text-sm">P&ID Analysis</span>
                <Badge className="bg-rose-600 text-xs">NEW</Badge>
              </h3>
              <div className="grid md:grid-cols-2 gap-3">
                <div className="p-4 border-l-4 border-violet-500 bg-violet-50 dark:bg-violet-900/20">
                  <h4 className="font-bold text-violet-900 dark:text-violet-100 mb-2">P&ID Analyzer (Port 5018)</h4>
                  <p className="text-sm text-violet-800 dark:text-violet-200 mb-2">Symbol connectivity analysis and BOM generation</p>
                  <ul className="text-xs space-y-1 text-violet-700 dark:text-violet-300">
                    <li><strong>* Output:</strong> BOM, valve signal list, equipment list</li>
                    <li><strong>* Features:</strong> Graph-based connectivity analysis</li>
                  </ul>
                </div>
                <div className="p-4 border-l-4 border-red-500 bg-red-50 dark:bg-red-900/20">
                  <h4 className="font-bold text-red-900 dark:text-red-100 mb-2">Design Checker (Port 5019)</h4>
                  <p className="text-sm text-red-800 dark:text-red-200 mb-2">Design rule validation and error detection</p>
                  <ul className="text-xs space-y-1 text-red-700 dark:text-red-300">
                    <li><strong>* Rules:</strong> 20+ design rules (6 categories)</li>
                    <li><strong>* Standards:</strong> ISO 10628, ISA 5.1, ASME</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Other Services (collapsed) */}
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20">
                <h4 className="font-bold text-yellow-900 dark:text-yellow-100 mb-1">ESRGAN (5010)</h4>
                <p className="text-xs text-yellow-700 dark:text-yellow-300">2x/4x upscaling, noise removal</p>
              </div>
              <div className="p-4 border-l-4 border-pink-500 bg-pink-50 dark:bg-pink-900/20">
                <h4 className="font-bold text-pink-900 dark:text-pink-100 mb-1">SkinModel (5003)</h4>
                <p className="text-xs text-pink-700 dark:text-pink-300">Tolerance prediction and manufacturability analysis</p>
              </div>
              <div className="p-4 border-l-4 border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-bold text-indigo-900 dark:text-indigo-100">VL (5004)</h4>
                  <Badge className="bg-indigo-600 text-xs">Multimodal</Badge>
                </div>
                <p className="text-xs text-indigo-700 dark:text-indigo-300">Vision-Language, BLIP/Claude/GPT-4V</p>
              </div>
              <div className="p-4 border-l-4 border-violet-500 bg-violet-50 dark:bg-violet-900/20">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-bold text-violet-900 dark:text-violet-100">Knowledge (5007)</h4>
                  <Badge className="bg-violet-600 text-xs">GraphRAG</Badge>
                </div>
                <p className="text-xs text-violet-700 dark:text-violet-300">Neo4j + GraphRAG domain knowledge engine</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
