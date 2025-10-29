import { useUIStore } from '../../store/uiStore';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Moon, Sun, Monitor, Settings as SettingsIcon } from 'lucide-react';

export default function Settings() {
  const { theme, setTheme, debugPanelOpen, toggleDebugPanel } = useUIStore();

  const apiUrls = {
    gateway: import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000',
    edocr2: import.meta.env.VITE_EDOCR2_URL || 'http://localhost:5001',
    edgnet: import.meta.env.VITE_EDGNET_URL || 'http://localhost:5012',
    skinmodel: import.meta.env.VITE_SKINMODEL_URL || 'http://localhost:5003',
  };

  return (
    <div className="p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center gap-3">
        <SettingsIcon className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">시스템 설정 및 환경 구성</p>
        </div>
      </div>

      {/* 테마 설정 */}
      <Card>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Monitor className="h-5 w-5" />
                테마 설정
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                UI 테마를 선택하세요
              </p>
            </div>
            <Badge variant="default">
              {theme === 'dark' ? 'Dark Mode' : 'Light Mode'}
            </Badge>
          </div>

          <div className="flex gap-3">
            <Button
              variant={theme === 'light' ? 'default' : 'outline'}
              onClick={() => setTheme('light')}
              className="flex items-center gap-2"
            >
              <Sun className="h-4 w-4" />
              Light
            </Button>
            <Button
              variant={theme === 'dark' ? 'default' : 'outline'}
              onClick={() => setTheme('dark')}
              className="flex items-center gap-2"
            >
              <Moon className="h-4 w-4" />
              Dark
            </Button>
          </div>
        </div>
      </Card>

      {/* 디버그 설정 */}
      <Card>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">디버그 패널</h2>
              <p className="text-sm text-muted-foreground mt-1">
                개발자 도구 및 디버그 패널 표시
              </p>
            </div>
            <Badge variant={debugPanelOpen ? 'success' : 'default'}>
              {debugPanelOpen ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>

          <Button
            variant={debugPanelOpen ? 'default' : 'outline'}
            onClick={toggleDebugPanel}
          >
            {debugPanelOpen ? 'Disable' : 'Enable'} Debug Panel
          </Button>
        </div>
      </Card>

      {/* API 엔드포인트 */}
      <Card>
        <div className="p-6 space-y-4">
          <div>
            <h2 className="text-xl font-semibold">API 엔드포인트</h2>
            <p className="text-sm text-muted-foreground mt-1">
              현재 설정된 API 서버 주소 (환경 변수)
            </p>
          </div>

          <div className="space-y-3">
            {Object.entries(apiUrls).map(([name, url]) => (
              <div
                key={name}
                className="flex items-center justify-between p-3 bg-accent/50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <Badge variant="default" className="uppercase">
                    {name}
                  </Badge>
                  <code className="text-sm font-mono">{url}</code>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              💡 <strong>참고:</strong> API URL은 <code>.env</code> 파일에서 설정됩니다.
              변경하려면 환경 변수를 수정하고 애플리케이션을 재시작하세요.
            </p>
          </div>
        </div>
      </Card>

      {/* 시스템 정보 */}
      <Card>
        <div className="p-6 space-y-4">
          <div>
            <h2 className="text-xl font-semibold">시스템 정보</h2>
            <p className="text-sm text-muted-foreground mt-1">
              애플리케이션 버전 및 환경
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-accent/50 rounded-lg">
              <div className="text-sm text-muted-foreground">Version</div>
              <div className="text-lg font-semibold">1.0.0</div>
            </div>
            <div className="p-3 bg-accent/50 rounded-lg">
              <div className="text-sm text-muted-foreground">Environment</div>
              <div className="text-lg font-semibold">
                {import.meta.env.MODE}
              </div>
            </div>
            <div className="p-3 bg-accent/50 rounded-lg">
              <div className="text-sm text-muted-foreground">Build</div>
              <div className="text-lg font-semibold">
                {import.meta.env.DEV ? 'Development' : 'Production'}
              </div>
            </div>
            <div className="p-3 bg-accent/50 rounded-lg">
              <div className="text-sm text-muted-foreground">React</div>
              <div className="text-lg font-semibold">18.3.1</div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
