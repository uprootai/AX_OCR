import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card';
import Mermaid from '../../../../components/ui/Mermaid';
import ImageZoom from '../../../../components/ui/ImageZoom';
import { Code } from 'lucide-react';

interface PipelineSectionProps {
  sectionRef: (el: HTMLElement | null) => void;
}

export function PipelineSection({ sectionRef }: PipelineSectionProps) {
  const { t } = useTranslation();

  const pipelineChart = `sequenceDiagram
    participant User as User
    participant Dashboard as Dashboard
    participant Builder as BlueprintFlow Builder
    participant Gateway as Gateway API
    participant APIs as Various APIs

    User->>Dashboard: 1. Add new API (enter URL)
    Dashboard->>Dashboard: 2. Auto-discover /api/v1/info
    Dashboard-->>User: 3. Register as Custom API

    User->>Builder: 4. Design workflow
    Builder->>Builder: 5. Place & connect nodes
    Builder-->>User: 6. Real-time preview

    User->>Builder: 7. Click execute
    Builder->>Gateway: 8. Send workflow JSON
    Gateway->>APIs: 9. Parallel/sequential execution
    APIs-->>Gateway: 10. Collect results
    Gateway-->>Builder: 11. Integrated result
    Builder-->>User: 12. Display visualization`;

  return (
    <section
      id="pipeline"
      ref={sectionRef}
      className="mb-12 scroll-mt-20"
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Code className="w-5 h-5 mr-2" />
            {t('guide.blueprintflowPipeline')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.workflowPipeline')}
              </h3>
              <ImageZoom>
                <Mermaid chart={pipelineChart} />
              </ImageZoom>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
