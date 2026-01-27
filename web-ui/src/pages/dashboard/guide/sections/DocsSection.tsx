import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card';

interface DocsSectionProps {
  sectionRef: (el: HTMLElement | null) => void;
}

export function DocsSection({ sectionRef }: DocsSectionProps) {
  const { t } = useTranslation();

  return (
    <section
      id="docs"
      ref={sectionRef}
      className="mb-12 scroll-mt-20"
    >
      <Card>
        <CardHeader>
          <CardTitle>{t('guide.documentation')}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {t('guide.docDescription')}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2 flex items-center">
                <span className="mr-2">[Doc]</span> User Guide
              </h3>
              <ul className="text-sm space-y-1 text-blue-800 dark:text-blue-200">
                <li>* INSTALLATION_GUIDE.md</li>
                <li>* TROUBLESHOOTING.md</li>
                <li>* ADMIN_MANUAL.md</li>
              </ul>
            </div>
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2 flex items-center">
                <span className="mr-2">[Dev]</span> Developer Guide
              </h3>
              <ul className="text-sm space-y-1 text-green-800 dark:text-green-200">
                <li>* API_SPEC_SYSTEM_GUIDE.md</li>
                <li>* DYNAMIC_API_SYSTEM_GUIDE.md</li>
                <li>* BLUEPRINTFLOW_API_INTEGRATION_GUIDE.md</li>
              </ul>
            </div>
            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <h3 className="font-semibold text-purple-900 dark:text-purple-100 mb-2 flex items-center">
                <span className="mr-2">[Flow]</span> BlueprintFlow
              </h3>
              <ul className="text-sm space-y-1 text-purple-800 dark:text-purple-200">
                <li>* BlueprintFlow Overview</li>
                <li>* Architecture Design</li>
                <li>* VL + TextInput Integration</li>
              </ul>
            </div>
            <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <h3 className="font-semibold text-orange-900 dark:text-orange-100 mb-2 flex items-center">
                <span className="mr-2">[Tech]</span> Technical Implementation
              </h3>
              <ul className="text-sm space-y-1 text-orange-800 dark:text-orange-200">
                <li>* YOLO Quick Start</li>
                <li>* eDOCr v1/v2 Deployment</li>
                <li>* Synthetic Data Strategy</li>
              </ul>
            </div>
            <div className="p-4 bg-rose-50 dark:bg-rose-900/20 rounded-lg md:col-span-2">
              <h3 className="font-semibold text-rose-900 dark:text-rose-100 mb-2 flex items-center">
                <span className="mr-2">[BOM]</span> Blueprint AI BOM v10.5
              </h3>
              <ul className="text-sm space-y-1 text-rose-800 dark:text-rose-200">
                <li>* Template → Project → Session workflow architecture</li>
                <li>* Self-contained Export (Docker images + port offset)</li>
                <li>* Human-in-the-Loop image review system</li>
                <li>* Customer-model mapping (8 customers, auto YOLO model selection)</li>
              </ul>
            </div>
          </div>

          <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              <strong>View All Documents:</strong>{' '}
              <a href="/docs" className="text-blue-600 hover:underline">/docs page</a> - Search and read all documentation.
            </p>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
