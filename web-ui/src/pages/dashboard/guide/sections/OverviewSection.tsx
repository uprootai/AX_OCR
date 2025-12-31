import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card';
import { BookOpen, Zap, Database, Server } from 'lucide-react';

interface OverviewSectionProps {
  sectionRef: (el: HTMLElement | null) => void;
}

export function OverviewSection({ sectionRef }: OverviewSectionProps) {
  const { t } = useTranslation();

  return (
    <section
      id="overview"
      ref={sectionRef}
      className="mb-12 scroll-mt-20"
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BookOpen className="w-5 h-5 mr-2" />
            {t('guide.projectOverview')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-gray-700 dark:text-gray-300">
              {t('guide.projectDescription')}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex items-center mb-2">
                  <Zap className="w-5 h-5 mr-2 text-blue-600 dark:text-blue-400" />
                  <h3 className="font-semibold text-blue-900 dark:text-blue-100">{t('guide.coreStrength')}</h3>
                </div>
                <ul className="text-sm space-y-1 text-blue-800 dark:text-blue-200">
                  <li>* <strong>{t('guide.coreStr1')}</strong></li>
                  <li>* {t('guide.coreStr2')}</li>
                  <li>* {t('guide.coreStr3')}</li>
                </ul>
              </div>

              <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <div className="flex items-center mb-2">
                  <Database className="w-5 h-5 mr-2 text-green-600 dark:text-green-400" />
                  <h3 className="font-semibold text-green-900 dark:text-green-100">{t('guide.flexibleAPIs')}</h3>
                </div>
                <ul className="text-sm space-y-1 text-green-800 dark:text-green-200">
                  <li>* {t('guide.flexApi1')}</li>
                  <li>* {t('guide.flexApi2')}</li>
                  <li>* {t('guide.flexApi3')}</li>
                </ul>
              </div>

              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
                <div className="flex items-center mb-2">
                  <Server className="w-5 h-5 mr-2 text-purple-600 dark:text-purple-400" />
                  <h3 className="font-semibold text-purple-900 dark:text-purple-100">{t('guide.microservices')}</h3>
                </div>
                <ul className="text-sm space-y-1 text-purple-800 dark:text-purple-200">
                  <li>* {t('guide.microservices1')}</li>
                  <li>* {t('guide.microservices2')}</li>
                  <li>* {t('guide.microservices3')}</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
