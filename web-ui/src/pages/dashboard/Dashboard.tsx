import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import APIStatusMonitor from '../../components/monitoring/APIStatusMonitor';
import AddAPIDialog from '../../components/dashboard/AddAPIDialog';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Link } from 'react-router-dom';
import { TestTube, Activity, FileText, TrendingUp, Plus, RefreshCw } from 'lucide-react';
import { useAPIConfigStore } from '../../store/apiConfigStore';

export default function Dashboard() {
  const { t } = useTranslation();
  const [isAddAPIDialogOpen, setIsAddAPIDialogOpen] = useState(false);
  const [isAutoDiscovering, setIsAutoDiscovering] = useState(false);
  const { addAPI, customAPIs } = useAPIConfigStore();

  /**
   * Gateway API Registry에서 자동으로 API 검색
   */
  const handleAutoDiscover = async () => {
    setIsAutoDiscovering(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/registry/list');
      if (response.ok) {
        const data = await response.json();
        const apis = data.apis || [];

        // 현재 등록된 API 목록을 store에서 직접 가져오기 (stale closure 방지)
        const currentAPIs = useAPIConfigStore.getState().customAPIs;

        let addedCount = 0;
        apis.forEach((apiInfo: any) => {
          // 이미 추가된 API는 건너뛰기
          if (currentAPIs.find(api => api.id === apiInfo.id)) {
            return;
          }

          // APIConfig 형식으로 변환하여 추가
          addAPI({
            id: apiInfo.id,
            name: apiInfo.name,
            displayName: apiInfo.display_name,
            baseUrl: apiInfo.base_url,
            port: apiInfo.port,
            icon: apiInfo.icon,
            color: apiInfo.color,
            category: apiInfo.category === 'control' ? 'control' : 'api',
            description: apiInfo.description,
            enabled: apiInfo.status === 'healthy',
            inputs: apiInfo.inputs || [],
            outputs: apiInfo.outputs || [],
            parameters: apiInfo.parameters || [],
          });
          addedCount++;
        });

        if (addedCount > 0) {
          alert(`✅ ${addedCount}개의 새 API가 자동으로 추가되었습니다!`);
        } else {
          alert(`ℹ️ 모든 API가 이미 등록되어 있습니다.`);
        }
      }
    } catch (error) {
      console.error('Auto-discover failed:', error);
      alert('⚠️ API 자동 검색에 실패했습니다. Gateway API가 실행 중인지 확인하세요.');
    } finally {
      setIsAutoDiscovering(false);
    }
  };

  // 앱 시작 시 자동 검색 (최초 1회만)
  useEffect(() => {
    // localStorage에서 자동 검색 수행 여부 확인
    const hasAutoDiscovered = localStorage.getItem('auto-discovered');
    if (!hasAutoDiscovered) {
      handleAutoDiscover();
      localStorage.setItem('auto-discovered', 'true');
    }
  }, []);

  return (
    <div className="space-y-6">
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
            onClick={handleAutoDiscover}
            disabled={isAutoDiscovering}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isAutoDiscovering ? 'animate-spin' : ''}`} />
            {isAutoDiscovering ? '검색 중...' : 'API 자동 검색'}
          </Button>
          <Button onClick={() => setIsAddAPIDialogOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            API 추가
          </Button>
        </div>
      </div>

      {/* API Status Monitor */}
      <APIStatusMonitor />

      {/* Add API Dialog */}
      <AddAPIDialog
        isOpen={isAddAPIDialogOpen}
        onClose={() => setIsAddAPIDialogOpen(false)}
      />

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card className="hover:border-primary transition-colors cursor-pointer">
          <Link to="/test">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TestTube className="h-5 w-5 text-primary" />
                {t('dashboard.apiTests')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {t('dashboard.apiTestsDesc')}
              </p>
            </CardContent>
          </Link>
        </Card>

        <Card className="hover:border-primary transition-colors cursor-pointer">
          <Link to="/analyze">
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

      {/* Quick Stats */}
      <div className="grid md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">오늘 분석</p>
                <p className="text-2xl font-bold">0</p>
              </div>
              <TrendingUp className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">성공률</p>
                <p className="text-2xl font-bold">100%</p>
              </div>
              <Activity className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">평균 응답</p>
                <p className="text-2xl font-bold">4.5s</p>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">에러</p>
                <p className="text-2xl font-bold">0</p>
              </div>
              <Activity className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Getting Started */}
      <Card>
        <CardHeader>
          <CardTitle>Getting Started</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
                1
              </div>
              <div>
                <h4 className="font-semibold">API 상태 확인</h4>
                <p className="text-sm text-muted-foreground">
                  위의 API Health Status에서 모든 서비스가 정상 작동하는지 확인하세요.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
                2
              </div>
              <div>
                <h4 className="font-semibold">개별 API 테스트</h4>
                <p className="text-sm text-muted-foreground">
                  Test 메뉴에서 각 API의 기능을 개별적으로 테스트할 수 있습니다.
                </p>
                <Link to="/test">
                  <Button variant="outline" size="sm" className="mt-2">
                    테스트 시작하기
                  </Button>
                </Link>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
                3
              </div>
              <div>
                <h4 className="font-semibold">통합 분석 실행</h4>
                <p className="text-sm text-muted-foreground">
                  도면 파일을 업로드하여 OCR, 세그멘테이션, 공차 예측을 한 번에 실행하세요.
                </p>
                <Link to="/analyze">
                  <Button variant="outline" size="sm" className="mt-2">
                    분석 시작하기
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
