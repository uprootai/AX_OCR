import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card';

interface QuickstartSectionProps {
  sectionRef: (el: HTMLElement | null) => void;
}

export function QuickstartSection({ sectionRef }: QuickstartSectionProps) {
  const { t } = useTranslation();

  return (
    <section
      id="quickstart"
      ref={sectionRef}
      className="mb-12 scroll-mt-20"
    >
      <Card>
        <CardHeader>
          <CardTitle>{t('guide.quickStartGuide')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2 flex items-center text-green-900 dark:text-green-100">
                <span className="text-xl mr-2">[1]</span>
                Build Workflow with BlueprintFlow (Recommended)
              </h3>
              <ol className="space-y-2 text-sm ml-4">
                <li className="flex items-start">
                  <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">1</span>
                  <span>Go to <a href="/blueprintflow/builder" className="text-green-600 hover:underline font-medium">BlueprintFlow Builder</a></span>
                </li>
                <li className="flex items-start">
                  <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">2</span>
                  <span>Drag desired API nodes from left palette to canvas</span>
                </li>
                <li className="flex items-start">
                  <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">3</span>
                  <span>Drag connection lines between nodes to build workflow</span>
                </li>
                <li className="flex items-start">
                  <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">4</span>
                  <span>Click each node and adjust parameters in right panel</span>
                </li>
                <li className="flex items-start">
                  <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">5</span>
                  <span>Click "Execute" button and check real-time results</span>
                </li>
              </ol>
            </div>

            <div className="border-t pt-4">
              <h3 className="font-semibold mb-2 flex items-center text-cyan-900 dark:text-cyan-100">
                <span className="text-xl mr-2">[2]</span>
                Add New API (Custom API)
              </h3>
              <ol className="space-y-2 text-sm ml-4">
                <li className="flex items-start">
                  <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">1</span>
                  <span>Click <strong>"Add API"</strong> button in top-right of <a href="/dashboard" className="text-cyan-600 hover:underline font-medium">Dashboard</a></span>
                </li>
                <li className="flex items-start">
                  <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">2</span>
                  <span>Enter API URL (e.g., <code>http://localhost:5007</code>) and click <strong>"Auto Discover"</strong></span>
                </li>
                <li className="flex items-start">
                  <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">3</span>
                  <span>API info auto-populates (icon, color, category, etc.)</span>
                </li>
                <li className="flex items-start">
                  <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">4</span>
                  <span>Save for <strong>instant reflection</strong>: Dashboard, Settings, BlueprintFlow nodes</span>
                </li>
                <li className="flex items-start">
                  <span className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center mr-3 flex-shrink-0 text-xs">5</span>
                  <span>After testing, use <strong>"Export"</strong> button to convert to Built-in API</span>
                </li>
              </ol>
              <div className="mt-3 p-3 bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800 rounded">
                <p className="text-xs text-cyan-800 dark:text-cyan-200">
                  <strong>Core Value:</strong> Any OCR engine, any Detection model - just enter the URL and instantly test various combinations in BlueprintFlow!
                </p>
              </div>
            </div>

            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">Tips</h4>
              <ul className="text-sm space-y-1 text-yellow-800 dark:text-yellow-200">
                <li>* First API call may be slow due to model loading (faster afterwards)</li>
                <li>* Use <a href="/blueprintflow/templates" className="underline">templates</a> for quick start with verified workflows</li>
                <li>* APIs with <code>/api/v1/info</code> endpoint can be auto-discovered</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
