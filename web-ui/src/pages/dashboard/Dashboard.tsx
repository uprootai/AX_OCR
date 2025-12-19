import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import APIStatusMonitor from '../../components/monitoring/APIStatusMonitor';
import ContainerManager from '../../components/dashboard/ContainerManager';
import AddAPIDialog from '../../components/dashboard/AddAPIDialog';
import ExportToBuiltinDialog from '../../components/dashboard/ExportToBuiltinDialog';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Link } from 'react-router-dom';
import { TestTube, Activity, FileText, TrendingUp, Plus, RefreshCw, Download, Trash2, ToggleLeft, ToggleRight, ClipboardList, ExternalLink } from 'lucide-react';
import { useAPIConfigStore, type APIConfig } from '../../store/apiConfigStore';

// BOM 세션 타입
interface BOMSession {
  session_id: string;
  filename: string;
  status: string;
  created_at: string;
  detection_count: number;
  verified_count: number;
  bom_generated: boolean;
}

export default function Dashboard() {
  const { t } = useTranslation();
  const [isAddAPIDialogOpen, setIsAddAPIDialogOpen] = useState(false);
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const [selectedAPIForExport, setSelectedAPIForExport] = useState<APIConfig | null>(null);
  const [isAutoDiscovering, setIsAutoDiscovering] = useState(false);
  const { addAPI, customAPIs, removeAPI, toggleAPI } = useAPIConfigStore();

  // BOM 세션 상태
  const [bomSessions, setBomSessions] = useState<BOMSession[]>([]);
  const [bomLoading, setBomLoading] = useState(false);
  const [bomError, setBomError] = useState<string | null>(null);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);

  // BOM 세션 목록 가져오기
  const fetchBomSessions = useCallback(async () => {
    setBomLoading(true);
    setBomError(null);
    try {
      const response = await fetch('http://localhost:5020/sessions');
      if (response.ok) {
        const sessions = await response.json();
        setBomSessions(sessions);
      } else {
        setBomError('세션 조회 실패');
      }
    } catch (error) {
      setBomError('BOM 서버에 연결할 수 없습니다');
      console.error('BOM 세션 조회 실패:', error);
    } finally {
      setBomLoading(false);
    }
  }, []);

  // BOM 세션 삭제
  const deleteBomSession = useCallback(async (sessionId: string) => {
    if (!confirm('이 세션을 삭제하시겠습니까?')) return;

    setDeletingSessionId(sessionId);
    try {
      const response = await fetch(`http://localhost:5020/sessions/${sessionId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setBomSessions(prev => prev.filter(s => s.session_id !== sessionId));
      } else {
        alert('세션 삭제에 실패했습니다.');
      }
    } catch (error) {
      console.error('세션 삭제 실패:', error);
      alert('세션 삭제 중 오류가 발생했습니다.');
    } finally {
      setDeletingSessionId(null);
    }
  }, []);

  // BOM 세션 로드
  useEffect(() => {
    fetchBomSessions();
  }, [fetchBomSessions]);

  const handleExportAPI = (api: APIConfig) => {
    setSelectedAPIForExport(api);
    setIsExportDialogOpen(true);
  };

  /**
   * Docker 내부 호스트명을 localhost로 변환
   * 예: http://yolo-api:5005 -> http://localhost:5005
   */
  const convertToLocalhost = (url: string): string => {
    try {
      const parsed = new URL(url);
      // Docker 서비스명 패턴: xxx-api 형태
      if (parsed.hostname.includes('-api') || parsed.hostname.includes('_api')) {
        parsed.hostname = 'localhost';
      }
      return parsed.toString().replace(/\/$/, ''); // 끝의 슬래시 제거
    } catch {
      return url;
    }
  };

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
        apis.forEach((apiInfo: {
          id: string;
          name?: string;
          base_url: string;
          display_name?: string;
          category?: string;
          port?: number;
          icon?: string;
          color?: string;
          description?: string;
          status?: string;
          inputs?: Array<{ name: string; type: string }>;
          outputs?: Array<{ name: string; type: string }>;
          parameters?: Array<{ name: string; type: string; default?: string | number | boolean }>;
        }) => {
          // 이미 추가된 API는 건너뛰기
          if (currentAPIs.find(api => api.id === apiInfo.id)) {
            return;
          }

          // Docker 내부 URL을 localhost로 변환
          const browserAccessibleUrl = convertToLocalhost(apiInfo.base_url);

          // APIConfig 형식으로 변환하여 추가
          addAPI({
            id: apiInfo.id,
            name: apiInfo.name || apiInfo.id,
            displayName: apiInfo.display_name || apiInfo.id,
            baseUrl: browserAccessibleUrl,
            port: apiInfo.port || 0,
            icon: apiInfo.icon || '🔧',
            color: apiInfo.color || '#666',
            category: (apiInfo.category || 'ocr') as 'knowledge' | 'input' | 'detection' | 'ocr' | 'segmentation' | 'preprocessing' | 'analysis' | 'ai' | 'control',
            description: apiInfo.description || '',
            enabled: apiInfo.status === 'healthy',
            inputs: (apiInfo.inputs || []).map(i => ({ ...i, description: '' })),
            outputs: (apiInfo.outputs || []).map(o => ({ ...o, description: '' })),
            parameters: (apiInfo.parameters || []).map(p => ({
              name: p.name,
              type: (p.type || 'string') as 'number' | 'string' | 'boolean' | 'select',
              default: p.default ?? '',
              description: '',
            })),
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

      {/* Container Manager */}
      <ContainerManager />

      {/* BOM Sessions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ClipboardList className="w-5 h-5" />
              BOM 세션 관리
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchBomSessions}
              disabled={bomLoading}
            >
              <RefreshCw className={`w-4 h-4 mr-1 ${bomLoading ? 'animate-spin' : ''}`} />
              새로고침
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {bomError ? (
            <div className="text-center py-4 text-muted-foreground">
              <p className="text-amber-600 dark:text-amber-400">{bomError}</p>
              <p className="text-sm mt-1">Blueprint AI BOM 서버 (포트 5020)가 실행 중인지 확인하세요.</p>
            </div>
          ) : bomLoading ? (
            <div className="text-center py-4 text-muted-foreground">
              세션 로딩 중...
            </div>
          ) : bomSessions.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground">
              <p>등록된 BOM 세션이 없습니다.</p>
              <a
                href="http://localhost:3000"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-2 text-blue-600 hover:underline"
              >
                BOM 생성 시작하기 <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          ) : (
            <div className="space-y-3">
              {bomSessions.map((session) => (
                <div
                  key={session.session_id}
                  className="flex items-center justify-between p-4 border rounded-lg bg-background hover:bg-muted/50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{session.filename}</div>
                    <div className="text-sm text-muted-foreground flex items-center gap-3 mt-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        session.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                        session.status === 'in_progress' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' :
                        'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                      }`}>
                        {session.status === 'completed' ? '완료' : session.status === 'in_progress' ? '진행중' : session.status}
                      </span>
                      <span>검출: {session.detection_count}개</span>
                      <span>검증: {session.verified_count}개</span>
                      {session.bom_generated && (
                        <span className="text-green-600 dark:text-green-400">BOM 생성됨</span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {new Date(session.created_at).toLocaleString('ko-KR')}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <a
                      href={`http://localhost:3000/workflow?session=${session.session_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      열기 <ExternalLink className="w-3 h-3" />
                    </a>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteBomSession(session.session_id)}
                      disabled={deletingSessionId === session.session_id}
                      className="text-destructive hover:text-destructive disabled:opacity-50"
                    >
                      {deletingSessionId === session.session_id ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add API Dialog */}
      <AddAPIDialog
        isOpen={isAddAPIDialogOpen}
        onClose={() => setIsAddAPIDialogOpen(false)}
      />

      {/* Export to Built-in Dialog */}
      <ExportToBuiltinDialog
        isOpen={isExportDialogOpen}
        onClose={() => {
          setIsExportDialogOpen(false);
          setSelectedAPIForExport(null);
        }}
        apiConfig={selectedAPIForExport}
      />

      {/* Custom APIs Management */}
      {customAPIs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5" />
              Custom APIs ({customAPIs.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {customAPIs.map((api) => (
                <div
                  key={api.id}
                  className={`flex items-center justify-between p-4 border rounded-lg transition-colors ${
                    api.enabled ? 'bg-background' : 'bg-muted/50 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                      style={{ backgroundColor: api.color + '20', color: api.color }}
                    >
                      {api.icon}
                    </div>
                    <div>
                      <div className="font-semibold flex items-center gap-2">
                        {api.displayName}
                        <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{api.id}</code>
                      </div>
                      <div className="text-sm text-muted-foreground">{api.description}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {api.baseUrl} • {api.category}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* Toggle */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleAPI(api.id)}
                      title={api.enabled ? '비활성화' : '활성화'}
                    >
                      {api.enabled ? (
                        <ToggleRight className="w-5 h-5 text-green-500" />
                      ) : (
                        <ToggleLeft className="w-5 h-5 text-muted-foreground" />
                      )}
                    </Button>

                    {/* Export to Built-in */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleExportAPI(api)}
                      title="Built-in API로 내보내기"
                      className="gap-1"
                    >
                      <Download className="w-4 h-4" />
                      내보내기
                    </Button>

                    {/* Delete */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (confirm(`"${api.displayName}" API를 삭제하시겠습니까?`)) {
                          removeAPI(api.id);
                        }
                      }}
                      title="삭제"
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            {/* 가이드 메시지 */}
            <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                <strong>💡 워크플로우:</strong> Custom API로 테스트 → <strong>내보내기</strong> 버튼으로 Built-in API 코드 생성 → 파일 저장 → Custom API 비활성화
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6">
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
                <h4 className="font-semibold">BlueprintFlow 워크플로우</h4>
                <p className="text-sm text-muted-foreground">
                  비주얼 워크플로우에서 각 API를 노드로 추가하고 테스트하세요.
                </p>
                <Link to="/blueprintflow/builder">
                  <Button variant="outline" size="sm" className="mt-2">
                    워크플로우 시작하기
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
                  템플릿을 선택하여 OCR, 세그멘테이션, 공차 예측을 한 번에 실행하세요.
                </p>
                <Link to="/blueprintflow/templates">
                  <Button variant="outline" size="sm" className="mt-2">
                    템플릿 선택하기
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
