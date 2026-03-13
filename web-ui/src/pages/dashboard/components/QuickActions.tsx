import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { TestTube, FileText, Activity } from 'lucide-react';

export function QuickActions() {
  const { t } = useTranslation();

  return (
    <div id="section-quick-actions" className="scroll-mt-4 grid md:grid-cols-3 gap-6">
      <Card className="hover:border-primary transition-colors cursor-pointer">
        <Link to="/blueprintflow/builder">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TestTube className="h-5 w-5 text-primary" />
              BlueprintFlow
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              비주얼 워크플로우로 API를 테스트하고 파이프라인을 구성하세요.
            </p>
          </CardContent>
        </Link>
      </Card>

      <Card className="hover:border-primary transition-colors cursor-pointer">
        <Link to="/blueprintflow/templates">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              {t('dashboard.analyzeTitle')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {t('dashboard.analyzeDesc')}
            </p>
          </CardContent>
        </Link>
      </Card>

      <Card className="hover:border-primary transition-colors cursor-pointer">
        <Link to="/monitor">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              {t('dashboard.monitorTitle')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {t('dashboard.monitorDesc')}
            </p>
          </CardContent>
        </Link>
      </Card>
    </div>
  );
}
