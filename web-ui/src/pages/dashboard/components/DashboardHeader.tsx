import { useTranslation } from 'react-i18next';
import { Button } from '../../../components/ui/Button';
import { RefreshCw, Plus } from 'lucide-react';

interface DashboardHeaderProps {
  isAutoDiscovering: boolean;
  onAutoDiscover: () => void;
  onAddAPI: () => void;
}

export function DashboardHeader({ isAutoDiscovering, onAutoDiscover, onAddAPI }: DashboardHeaderProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-3xl font-bold mb-2">{t('dashboard.title')}</h1>
        <p className="text-muted-foreground">
          {t('dashboard.subtitle')}
        </p>
      </div>
      <div className="flex gap-2">
        <Button
          variant="outline"
          onClick={onAutoDiscover}
          disabled={isAutoDiscovering}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isAutoDiscovering ? 'animate-spin' : ''}`} />
          {isAutoDiscovering ? '검색 중...' : 'API 자동 검색'}
        </Button>
        <Button onClick={onAddAPI}>
          <Plus className="w-4 h-4 mr-2" />
          API 추가
        </Button>
      </div>
    </div>
  );
}
