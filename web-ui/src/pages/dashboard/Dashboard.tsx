import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import APIStatusMonitor from '../../components/monitoring/APIStatusMonitor';
import ContainerManager from '../../components/dashboard/ContainerManager';
import AddAPIDialog from '../../components/dashboard/AddAPIDialog';
import ExportToBuiltinDialog from '../../components/dashboard/ExportToBuiltinDialog';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import Toast from '../../components/ui/Toast';
import { Link } from 'react-router-dom';
import { TestTube, Activity, FileText, TrendingUp, Plus, RefreshCw, Download, Trash2, ToggleLeft, ToggleRight, ExternalLink, FolderOpen, Building, ChevronRight, CheckCircle, Clock, Server, Container, BarChart3, Rocket, Wrench } from 'lucide-react';
import { useAPIConfigStore, type APIConfig } from '../../store/apiConfigStore';
import { GATEWAY_URL } from '../../lib/api';
import { projectApi, type Project, type ProjectDetail as BOMProjectDetail } from '../../lib/blueprintBomApi';

// Toast 알림 타입
interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

// 프로젝트 세션 타입
type ProjectWithSessions = {
  project: Project;
  sessions: BOMProjectDetail['sessions'];
};

export default function Dashboard() {
  const { t } = useTranslation();
  const [isAddAPIDialogOpen, setIsAddAPIDialogOpen] = useState(false);
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const [selectedAPIForExport, setSelectedAPIForExport] = useState<APIConfig | null>(null);
  const [isAutoDiscovering, setIsAutoDiscovering] = useState(false);
  const { addAPI, customAPIs, removeAPI, toggleAPI } = useAPIConfigStore();

  // 프로젝트 상태
  const [projectData, setProjectData] = useState<ProjectWithSessions[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);

  // Toast 알림 상태
  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });

  // Toast 표시 헬퍼 함수
  const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message, type });
  }, []);

  // 프로젝트 목록 + 세션 로드
  const fetchProjects = useCallback(async () => {
    setProjectsLoading(true);
    try {
      const result = await projectApi.list(undefined, 100);
      const projectList = result.projects ?? [];
      // 각 프로젝트 상세 (세션 포함) 병렬 로드
      const details = await Promise.all(
        projectList.map(async (p) => {
          try {
            const detail = await projectApi.get(p.project_id);
            return { project: p, sessions: detail.sessions ?? [] };
          } catch {
            return { project: p, sessions: [] };
          }
        })
      );
      setProjectData(details);
    } catch {
      // BOM 서버 연결 실패 시 무시
    } finally {
      setProjectsLoading(false);
    }
  }, []);

  // 프로젝트 로드
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

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
      const response = await fetch(`${GATEWAY_URL}/api/v1/registry/list`);
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
          showToast(`✓ ${addedCount}개의 새 API가 추가되었습니다`, 'success');
        } else {
          showToast('모든 API가 이미 등록되어 있습니다', 'info');
        }
      }
    } catch {
      showToast('✗ API 자동 검색 실패\nGateway API가 실행 중인지 확인하세요', 'error');
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

      {/* 섹션 목차 네비게이션 */}
      <nav className="flex flex-wrap gap-2 p-3 bg-muted/40 rounded-lg border">
        {[
          { id: 'section-api', icon: Server, label: 'API 상태', tooltip: 'YOLO, eDOCr2, PaddleOCR 등 21개 AI 서비스의 실시간 헬스체크 상태를 확인합니다. GPU VRAM 사용량, 온도, 카테고리별(Detection, OCR, Segmentation 등) 가동률과 응답 시간을 모니터링할 수 있습니다.' },
          { id: 'section-containers', icon: Container, label: '컨테이너', tooltip: 'Docker로 실행 중인 모든 API 컨테이너의 상태(Running/Stopped)를 확인하고, 개별 서비스를 시작하거나 중지할 수 있습니다. 포트 번호와 컨테이너 이름도 표시됩니다.' },
          { id: 'section-projects', icon: FolderOpen, label: '프로젝트 현황', tooltip: 'BOM 견적 프로젝트와 P&ID 검출 프로젝트의 전체 현황을 확인합니다. 프로젝트별 세션 수, 완료/대기 상태, 진행률을 한눈에 볼 수 있고, 각 세션을 클릭하면 BlueprintFlow 워크플로우로 이동합니다.' },
          { id: 'section-quick-actions', icon: Rocket, label: '빠른 실행', tooltip: '자주 사용하는 기능으로 바로 이동합니다. BlueprintFlow 빌더에서 워크플로우를 구성하거나, 분석 템플릿을 선택하여 OCR·세그멘테이션·공차 예측을 한 번에 실행하거나, 실시간 모니터링 페이지로 이동할 수 있습니다.' },
          { id: 'section-stats', icon: BarChart3, label: '통계', tooltip: '시스템 운영 지표를 요약합니다. 오늘 처리한 분석 건수, 전체 API 호출 성공률(%), 평균 응답 시간(초), 누적 에러 수를 카드 형태로 보여줍니다.' },
          ...(customAPIs.length > 0 ? [{ id: 'section-custom-apis', icon: Wrench, label: 'Custom APIs', tooltip: '사용자가 직접 등록한 Custom API 목록입니다. 각 API를 활성화/비활성화하거나, Built-in API로 내보내기하거나, 삭제할 수 있습니다. Gateway에서 자동 검색된 API도 여기에 표시됩니다.' }] : []),
          { id: 'section-getting-started', icon: FileText, label: 'Getting Started', tooltip: '시스템 사용법을 3단계로 안내합니다. ① API 상태 확인 → ② BlueprintFlow에서 노드 기반 워크플로우 구성 → ③ 템플릿을 활용한 통합 분석 실행. 처음 사용하시는 분은 이 가이드를 따라해 보세요.' },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              title={item.tooltip}
              onClick={() => document.getElementById(item.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md bg-background border hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <Icon className="w-3.5 h-3.5" />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* API Status Monitor */}
      <div id="section-api" className="scroll-mt-4">
        <APIStatusMonitor />
      </div>

      {/* Container Manager */}
      <div id="section-containers" className="scroll-mt-4">
        <ContainerManager />
      </div>

      {/* 프로젝트 현황 */}
      <Card id="section-projects" className="scroll-mt-4">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FolderOpen className="w-5 h-5 text-pink-500" />
              프로젝트 현황
              {projectData.length > 0 && (
                <span className="text-sm font-normal text-muted-foreground">
                  ({projectData.length}개)
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchProjects}
                disabled={projectsLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${projectsLoading ? 'animate-spin' : ''}`} />
                새로고침
              </Button>
              <Link to="/projects">
                <Button variant="outline" size="sm">
                  전체 보기
                </Button>
              </Link>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {projectsLoading && projectData.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground">
              프로젝트 로딩 중...
            </div>
          ) : projectData.length === 0 ? (
            <div className="text-center py-6 text-muted-foreground">
              <FolderOpen className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>등록된 프로젝트가 없습니다.</p>
              <Link to="/projects" className="inline-flex items-center gap-1 mt-2 text-blue-600 hover:underline text-sm">
                프로젝트 생성하기
              </Link>
            </div>
          ) : (
            <>
              {/* 요약 통계 */}
              <div className="grid grid-cols-4 gap-3 mb-6">
                <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
                  <p className="text-xs text-muted-foreground">프로젝트</p>
                  <p className="text-xl font-bold">{projectData.length}</p>
                </div>
                <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg text-center">
                  <p className="text-xs text-muted-foreground">전체 세션</p>
                  <p className="text-xl font-bold text-blue-600">
                    {projectData.reduce((s, d) => s + d.project.session_count, 0)}
                  </p>
                </div>
                <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg text-center">
                  <p className="text-xs text-muted-foreground">완료</p>
                  <p className="text-xl font-bold text-green-600">
                    {projectData.reduce((s, d) => s + d.project.completed_count, 0)}
                  </p>
                </div>
                <div className="p-3 bg-yellow-50 dark:bg-yellow-950 rounded-lg text-center">
                  <p className="text-xs text-muted-foreground">대기</p>
                  <p className="text-xl font-bold text-yellow-600">
                    {projectData.reduce((s, d) => s + d.project.pending_count, 0)}
                  </p>
                </div>
              </div>

              {/* 프로젝트별 세션 목록 */}
              <div className="space-y-4">
                {projectData.map(({ project, sessions }) => {
                  const progress = project.session_count > 0
                    ? Math.round((project.completed_count / project.session_count) * 100)
                    : 0;
                  return (
                    <div key={project.project_id} className="border rounded-lg overflow-hidden">
                      {/* 프로젝트 헤더 */}
                      <a
                        href={`http://localhost:3000/projects/${project.project_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between p-4 bg-muted/30 hover:bg-muted/60 transition-colors"
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                            project.project_type === 'pid_detection' ? 'bg-cyan-100 dark:bg-cyan-900' : 'bg-pink-100 dark:bg-pink-900'
                          }`}>
                            <FolderOpen className={`w-4 h-4 ${
                              project.project_type === 'pid_detection' ? 'text-cyan-600' : 'text-pink-600'
                            }`} />
                          </div>
                          <div className="min-w-0">
                            <div className="font-semibold flex items-center gap-2">
                              {project.name}
                              <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${
                                project.project_type === 'pid_detection'
                                  ? 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900 dark:text-cyan-300'
                                  : 'bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300'
                              }`}>
                                {project.project_type === 'pid_detection' ? 'P&ID' : 'BOM'}
                              </span>
                            </div>
                            <div className="text-sm text-muted-foreground flex items-center gap-1">
                              <Building className="w-3 h-3" /> {project.customer}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm shrink-0 ml-4">
                          <div className="flex items-center gap-3 text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <FileText className="w-3.5 h-3.5" /> {project.session_count}
                            </span>
                            <span className="flex items-center gap-1 text-green-600">
                              <CheckCircle className="w-3.5 h-3.5" /> {project.completed_count}
                            </span>
                            <span className="flex items-center gap-1 text-yellow-600">
                              <Clock className="w-3.5 h-3.5" /> {project.pending_count}
                            </span>
                          </div>
                          {project.session_count > 0 && (
                            <div className="flex items-center gap-2 w-24">
                              <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-green-500 transition-all"
                                  style={{ width: `${progress}%` }}
                                />
                              </div>
                              <span className="text-xs text-muted-foreground w-8 text-right">{progress}%</span>
                            </div>
                          )}
                          <ExternalLink className="w-4 h-4 text-blue-500" />
                          <ChevronRight className="w-4 h-4 text-muted-foreground" />
                        </div>
                      </a>

                      {/* 세션 목록 (최대 5개) */}
                      {sessions.length > 0 && (
                        <div className="divide-y">
                          {sessions.slice(0, 5).map((session) => (
                            <a
                              key={session.session_id}
                              href={`http://localhost:3000/workflow?session=${session.session_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center justify-between px-4 py-2.5 hover:bg-muted/30 transition-colors"
                            >
                              <div className="flex items-center gap-3 flex-1 min-w-0">
                                <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
                                <span className="text-sm truncate">{session.filename}</span>
                              </div>
                              <div className="flex items-center gap-3 ml-4 shrink-0">
                                <span className="text-xs text-muted-foreground">
                                  검출 {session.detection_count} · 검증 {session.verified_count}
                                </span>
                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                  session.status === 'completed'
                                    ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                                    : session.status === 'error'
                                      ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                                      : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                                }`}>
                                  {session.status === 'completed' ? '완료' : session.status}
                                </span>
                                <ExternalLink className="w-3.5 h-3.5 text-muted-foreground" />
                              </div>
                            </a>
                          ))}
                          {sessions.length > 5 && (
                            <a
                              href={`http://localhost:3000/projects/${project.project_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center justify-center py-2.5 text-sm text-blue-600 hover:bg-muted/30 transition-colors"
                            >
                              + {sessions.length - 5}개 더 보기
                            </a>
                          )}
                        </div>
                      )}
                      {sessions.length === 0 && (
                        <div className="px-4 py-3 text-sm text-muted-foreground">
                          세션이 없습니다.
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
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
        <Card id="section-custom-apis" className="scroll-mt-4">
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
                        removeAPI(api.id);
                        showToast(`✓ ${api.displayName} API가 삭제되었습니다`, 'success');
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

      {/* Quick Stats */}
      <div id="section-stats" className="scroll-mt-4 grid md:grid-cols-4 gap-4">
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
      <Card id="section-getting-started" className="scroll-mt-4">
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

      {/* Toast 알림 */}
      {toast.show && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.type === 'error' ? 15000 : 10000}
          onClose={() => setToast(prev => ({ ...prev, show: false }))}
        />
      )}
    </div>
  );
}
