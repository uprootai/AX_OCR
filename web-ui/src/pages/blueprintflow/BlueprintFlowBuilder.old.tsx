import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Workflow, Construction, Rocket } from 'lucide-react';

export default function BlueprintFlowBuilder() {
  const { t } = useTranslation();

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Workflow className="w-8 h-8 text-cyan-600" />
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            {t('blueprintflow.builderTitle')}
          </h1>
          <Badge className="bg-cyan-600">BETA</Badge>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          {t('blueprintflow.builderSubtitle')}
        </p>
      </div>

      {/* Coming Soon */}
      <Card className="border-2 border-cyan-200 dark:border-cyan-800">
        <CardHeader className="bg-gradient-to-r from-cyan-50 to-blue-50 dark:from-cyan-900/30 dark:to-blue-900/30">
          <CardTitle className="flex items-center gap-2 text-cyan-900 dark:text-cyan-100">
            <Construction className="w-6 h-6" />
            {t('blueprintflow.inDevelopment')}
          </CardTitle>
        </CardHeader>
        <CardContent className="py-12">
          <div className="text-center space-y-6">
            <Rocket className="w-24 h-24 mx-auto text-cyan-600 dark:text-cyan-400" />

            <div>
              <h2 className="text-2xl font-bold mb-2 text-gray-900 dark:text-white">
                {t('blueprintflow.workflowBuilderTitle')}
              </h2>
              <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                {t('blueprintflow.workflowBuilderDesc')}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto mt-8">
              <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-cyan-200 dark:border-cyan-800">
                <h3 className="font-semibold mb-2 text-cyan-900 dark:text-cyan-100">
                  {t('blueprintflow.phase1Title')}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {t('blueprintflow.phase1Desc')}
                </p>
                <div className="mt-2">
                  <Badge className="bg-yellow-600">{t('blueprintflow.statusPlanned')}</Badge>
                </div>
              </div>

              <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold mb-2">{t('blueprintflow.phase2Title')}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {t('blueprintflow.phase2Desc')}
                </p>
                <div className="mt-2">
                  <Badge className="bg-gray-400">{t('blueprintflow.statusPending')}</Badge>
                </div>
              </div>

              <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold mb-2">{t('blueprintflow.phase35Title')}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {t('blueprintflow.phase35Desc')}
                </p>
                <div className="mt-2">
                  <Badge className="bg-gray-400">{t('blueprintflow.statusPending')}</Badge>
                </div>
              </div>
            </div>

            <div className="mt-8 p-6 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg border border-cyan-200 dark:border-cyan-800 max-w-2xl mx-auto">
              <h3 className="font-semibold mb-2 text-cyan-900 dark:text-cyan-100">
                {t('blueprintflow.designDocsTitle')}
              </h3>
              <p className="text-sm text-cyan-700 dark:text-cyan-300 mb-3">
                {t('blueprintflow.designDocsDesc')}
              </p>
              <div className="space-y-2 text-left text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-cyan-600 rounded-full"></span>
                  <code className="text-xs bg-white dark:bg-gray-900 px-2 py-1 rounded">
                    docs/BLUEPRINTFLOW_ARCHITECTURE_COMPLETE_DESIGN.md
                  </code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-cyan-600 rounded-full"></span>
                  <code className="text-xs bg-white dark:bg-gray-900 px-2 py-1 rounded">
                    CLAUDE.md (섹션: BlueprintFlow Development Guidelines)
                  </code>
                </div>
              </div>
            </div>

            <p className="text-sm text-gray-500 dark:text-gray-500">
              {t('blueprintflow.estimatedCompletion')}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
