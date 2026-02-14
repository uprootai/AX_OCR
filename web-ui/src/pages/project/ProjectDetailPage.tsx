/**
 * ProjectDetailPage - 프로젝트 상세 페이지
 *
 * web-ui 네이티브 구현 (다크모드 지원)
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  FolderOpen,
  ArrowLeft,
  Trash2,
  FileText,
  CheckCircle,
  Clock,
  LayoutTemplate,
  Building,
  RefreshCw,
  Loader2,
  MoreVertical,
  ExternalLink,
  Link2,
  Plus,
  Download,
  Upload,
  Settings,
  Database,
} from 'lucide-react';
import { projectApi, sessionApi, type ProjectDetail, type SessionListItem } from '../../lib/blueprintBomApi';
import { Tooltip } from '../../components/ui/Tooltip';
import { BOMWorkflowSection } from './components/BOMWorkflowSection';
import { PIDWorkflowSection } from './components/PIDWorkflowSection';
import { ProjectSettingsModal } from './components/ProjectSettingsModal';
import { GTManagementModal } from './components/GTManagementModal';

/** 활성 기능(feature) 이름 → 설명 */
const FEATURE_DESCRIPTIONS: Record<string, string> = {
  symbol_verification: 'YOLO 검출 결과를 사람이 확인하고 승인/반려하는 Human-in-the-Loop 검증 기능',
  gt_comparison: 'Ground Truth 데이터와 검출 결과를 비교하여 정확도(mAP, IoU)를 측정',
  bom_generation: '승인된 검출 결과를 기반으로 부품 목록(BOM)과 견적서를 자동 생성',
  dimension_extraction: '도면에서 치수 정보를 OCR로 추출하여 부품 크기·공차 분석',
  verification: '검출 결과에 대한 사람의 검증(승인/반려) 워크플로우',
};

/** project_type → 설명 */
const TYPE_DESCRIPTIONS: Record<string, string> = {
  pid_detection: 'P&ID(배관계장도) 도면의 심볼을 자동 검출·분석하는 프로젝트',
  bom_quotation: 'BOM(부품 목록) PDF를 파싱하고 도면 매칭 후 견적을 산출하는 프로젝트',
  general: '범용 도면 분석 프로젝트',
};

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [unlinkedSessions, setUnlinkedSessions] = useState<SessionListItem[]>([]);
  const [isLoadingUnlinked, setIsLoadingUnlinked] = useState(false);
  const [linkingSessionId, setLinkingSessionId] = useState<string | null>(null);
  const [unlinkingSessionId, setUnlinkingSessionId] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showGTManagement, setShowGTManagement] = useState(false);
  const importFileRef = useRef<HTMLInputElement>(null);
  const loadProject = useCallback(async () => {
    if (!projectId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await projectApi.get(projectId);
      setProject(data);
    } catch (err) {
      console.error('Failed to load project:', err);
      setError('프로젝트를 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const refreshProject = useCallback(async () => {
    if (!projectId) return;
    try {
      const data = await projectApi.get(projectId);
      setProject(data);
    } catch (err) {
      console.error('Failed to refresh project:', err);
    }
  }, [projectId]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  const handleDelete = async () => {
    if (!projectId || !project) return;
    if (!confirm(`정말로 "${project.name}" 프로젝트를 삭제하시겠습니까?`)) return;

    setIsDeleting(true);
    try {
      await projectApi.delete(projectId);
      navigate('/projects');
    } catch (err) {
      console.error('Failed to delete project:', err);
      setError('프로젝트 삭제에 실패했습니다.');
    } finally {
      setIsDeleting(false);
    }
  };

  const loadUnlinkedSessions = useCallback(async () => {
    setIsLoadingUnlinked(true);
    try {
      const allSessions = await sessionApi.list(undefined, 100);
      setUnlinkedSessions(allSessions.filter((s) => !s.project_id));
    } catch (err) {
      console.error('Failed to load unlinked sessions:', err);
    } finally {
      setIsLoadingUnlinked(false);
    }
  }, []);

  useEffect(() => {
    loadUnlinkedSessions();
  }, [loadUnlinkedSessions]);

  const handleLinkSession = async (sessionId: string) => {
    if (!projectId) return;
    setLinkingSessionId(sessionId);
    try {
      await sessionApi.updateProjectId(sessionId, projectId);
      setUnlinkedSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      await refreshProject();
    } catch (err) {
      console.error('Failed to link session:', err);
      setError('세션 연결에 실패했습니다.');
    } finally {
      setLinkingSessionId(null);
    }
  };

  const handleUnlinkSession = async (sessionId: string) => {
    setUnlinkingSessionId(sessionId);
    try {
      await sessionApi.unlinkProjectId(sessionId);
      await refreshProject();
    } catch (err) {
      console.error('Failed to unlink session:', err);
      setError('세션 분리에 실패했습니다.');
    } finally {
      setUnlinkingSessionId(null);
    }
  };

  const handleExportProject = async () => {
    if (!projectId) return;
    setIsExporting(true);
    setShowMenu(false);
    try {
      await projectApi.exportProject(projectId);
    } catch (err) {
      console.error('Failed to export project:', err);
      setError('프로젝트 Export에 실패했습니다.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleImportProject = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setIsImporting(true);
    setShowMenu(false);
    try {
      const result = await projectApi.importProject(file);
      const newId = (result as unknown as { project_id: string }).project_id;
      if (newId) {
        navigate(`/projects/${newId}`);
      }
    } catch (err) {
      console.error('Failed to import project:', err);
      setError('프로젝트 Import에 실패했습니다. 유효한 JSON 파일인지 확인해주세요.');
    } finally {
      setIsImporting(false);
      if (importFileRef.current) importFileRef.current.value = '';
    }
  };

  // completed + verified 상태 모두 완료로 카운트
  const doneCount = project
    ? project.completed_count + (project.sessions ?? []).filter(
        (s) => s.status === 'verified'
      ).length
    : 0;
  const progressPercent =
    project && project.session_count > 0
      ? Math.round((doneCount / project.session_count) * 100)
      : 0;

  // project_type에 따른 색상
  const getTypeColors = () => {
    if (project?.project_type === 'pid_detection') {
      return {
        bg: 'bg-cyan-100 dark:bg-cyan-900/30',
        icon: 'text-cyan-600 dark:text-cyan-400',
        badge: 'bg-cyan-100 dark:bg-cyan-900/50 text-cyan-700 dark:text-cyan-300',
        label: 'P&ID',
      };
    }
    if (project?.project_type === 'bom_quotation') {
      return {
        bg: 'bg-pink-100 dark:bg-pink-900/30',
        icon: 'text-pink-600 dark:text-pink-400',
        badge: 'bg-pink-100 dark:bg-pink-900/50 text-pink-700 dark:text-pink-300',
        label: 'BOM',
      };
    }
    return {
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      icon: 'text-blue-600 dark:text-blue-400',
      badge: 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300',
      label: '일반',
    };
  };

  const colors = getTypeColors();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 dark:text-blue-400 animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <FolderOpen className="w-8 h-8 text-gray-400 dark:text-gray-500" />
          </div>
          <p className="text-gray-600 dark:text-gray-300 font-medium">
            {error || '프로젝트를 찾을 수 없습니다.'}
          </p>
          <Link
            to="/projects"
            className="inline-flex items-center gap-2 mt-4 text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300"
          >
            <ArrowLeft className="w-4 h-4" />
            프로젝트 목록으로
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 헤더 */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                to="/projects"
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </Link>
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colors.bg}`}>
                  <FolderOpen className={`w-5 h-5 ${colors.icon}`} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                      {project.name}
                    </h1>
                    <Tooltip content={TYPE_DESCRIPTIONS[project.project_type] || '프로젝트 유형'} position="bottom">
                      <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${colors.badge}`}>
                        {colors.label}
                      </span>
                    </Tooltip>
                  </div>
                  <div className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
                    <Building className="w-3.5 h-3.5" />
                    <span>{project.customer}</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={loadProject}
                disabled={isLoading}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="새로고침"
              >
                <RefreshCw
                  className={`w-5 h-5 text-gray-500 dark:text-gray-400 ${isLoading ? 'animate-spin' : ''}`}
                />
              </button>
              <div className="relative">
                <button
                  onClick={() => setShowMenu(!showMenu)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <MoreVertical className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                </button>
                {showMenu && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setShowMenu(false)}
                    />
                    <div className="absolute right-0 mt-2 w-52 bg-white dark:bg-gray-800 rounded-xl shadow-lg dark:shadow-black/30 border border-gray-200 dark:border-gray-700 z-20 overflow-hidden">
                      <button
                        className="w-full px-4 py-2.5 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
                        onClick={() => {
                          setShowMenu(false);
                          setShowSettings(true);
                        }}
                      >
                        <Settings className="w-4 h-4" />
                        프로젝트 설정
                      </button>
                      <button
                        className="w-full px-4 py-2.5 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
                        onClick={() => {
                          setShowMenu(false);
                          setShowGTManagement(true);
                        }}
                      >
                        <Database className="w-4 h-4" />
                        GT 관리
                      </button>
                      <div className="border-t border-gray-100 dark:border-gray-700" />
                      <a
                        href={`http://localhost:3000/projects/${projectId}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full px-4 py-2.5 text-left text-sm hover:bg-blue-50 dark:hover:bg-blue-900/30 flex items-center gap-2 text-blue-600 dark:text-blue-400"
                        onClick={() => setShowMenu(false)}
                      >
                        <ExternalLink className="w-4 h-4" />
                        BOM 전용 UI에서 열기
                      </a>
                      <div className="border-t border-gray-100 dark:border-gray-700" />
                      <button
                        className="w-full px-4 py-2.5 text-left text-sm hover:bg-blue-50 dark:hover:bg-blue-900/30 flex items-center gap-2 text-blue-600 dark:text-blue-400"
                        onClick={handleExportProject}
                        disabled={isExporting}
                      >
                        {isExporting ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Download className="w-4 h-4" />
                        )}
                        프로젝트 Export
                      </button>
                      <button
                        className="w-full px-4 py-2.5 text-left text-sm hover:bg-green-50 dark:hover:bg-green-900/30 flex items-center gap-2 text-green-600 dark:text-green-400"
                        onClick={() => {
                          setShowMenu(false);
                          importFileRef.current?.click();
                        }}
                        disabled={isImporting}
                      >
                        {isImporting ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Upload className="w-4 h-4" />
                        )}
                        프로젝트 Import
                      </button>
                      <div className="border-t border-gray-100 dark:border-gray-700" />
                      <button
                        className="w-full px-4 py-2.5 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 flex items-center gap-2"
                        onClick={() => {
                          setShowMenu(false);
                          handleDelete();
                        }}
                        disabled={isDeleting}
                      >
                        <Trash2 className="w-4 h-4" />
                        프로젝트 삭제
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-600 dark:text-red-400 mb-6">
            {error}
          </div>
        )}

        {/* 프로젝트 정보 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4">프로젝트 정보</h2>
            {project.description && (
              <p className="text-gray-600 dark:text-gray-400 mb-4">{project.description}</p>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Tooltip content="프로젝트가 처음 생성된 날짜입니다" position="right">
                  <p className="text-sm text-gray-500 dark:text-gray-400">생성일</p>
                </Tooltip>
                <p className="font-medium text-gray-900 dark:text-white">
                  {new Date(project.created_at).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>
              <div>
                <Tooltip content="프로젝트 데이터가 마지막으로 변경된 시점입니다" position="right">
                  <p className="text-sm text-gray-500 dark:text-gray-400">최근 수정</p>
                </Tooltip>
                <p className="font-medium text-gray-900 dark:text-white">
                  {new Date(project.updated_at).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>
              {project.bom_source && (
                <div>
                  <Tooltip content="업로드된 BOM(부품 목록) PDF 파일명입니다. BOM 견적 워크플로우에서 사용됩니다." position="bottom">
                    <p className="text-sm text-gray-500 dark:text-gray-400">BOM 소스</p>
                  </Tooltip>
                  <p className="font-medium text-gray-900 dark:text-white truncate" title={project.bom_source}>
                    {project.bom_source}
                  </p>
                </div>
              )}
              {project.drawing_folder && (
                <div>
                  <Tooltip content="도면 파일이 저장된 서버 경로입니다. BOM 항목과 도면 자동 매칭에 사용됩니다." position="bottom">
                    <p className="text-sm text-gray-500 dark:text-gray-400">도면 폴더</p>
                  </Tooltip>
                  <p className="font-medium text-gray-900 dark:text-white truncate" title={project.drawing_folder}>
                    {project.drawing_folder}
                  </p>
                </div>
              )}
              {project.bom_item_count > 0 && (
                <div>
                  <Tooltip content="BOM PDF에서 파싱된 부품 총 수입니다. 괄호 안은 견적이 완료된 항목 수입니다." position="bottom">
                    <p className="text-sm text-gray-500 dark:text-gray-400">BOM 아이템</p>
                  </Tooltip>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {project.bom_item_count}개
                    {project.quoted_count > 0 && (
                      <span className="text-sm text-gray-500 dark:text-gray-400 ml-1">
                        (견적 {project.quoted_count}개)
                      </span>
                    )}
                  </p>
                </div>
              )}
              {project.total_quotation > 0 && (
                <div>
                  <Tooltip content="모든 부품의 견적 합계 금액입니다 (재료비 + 가공비 + 부가세 포함)" position="bottom">
                    <p className="text-sm text-gray-500 dark:text-gray-400">총 견적액</p>
                  </Tooltip>
                  <p className="font-medium text-gray-900 dark:text-white">
                    ₩{project.total_quotation.toLocaleString('ko-KR')}
                  </p>
                </div>
              )}
              {project.default_template_name && (
                <div className="col-span-2">
                  <Tooltip content="새 세션 생성 시 자동 적용되는 BlueprintFlow 워크플로우 템플릿입니다. 검출·분석 파이프라인을 정의합니다." position="bottom">
                    <p className="text-sm text-gray-500 dark:text-gray-400">기본 템플릿</p>
                  </Tooltip>
                  <div className="flex items-center gap-2 font-medium text-blue-600 dark:text-blue-400">
                    <LayoutTemplate className="w-4 h-4" />
                    {project.default_template_name}
                  </div>
                </div>
              )}
              {project.default_features.length > 0 && (
                <div className="col-span-2">
                  <Tooltip content="세션에서 자동으로 활성화되는 분석 기능 목록입니다. 각 뱃지 위에 마우스를 올리면 상세 설명을 볼 수 있습니다." position="bottom">
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1.5">활성 기능</p>
                  </Tooltip>
                  <div className="flex flex-wrap gap-1.5">
                    {project.default_features.map((feature) => (
                      <Tooltip
                        key={feature}
                        content={FEATURE_DESCRIPTIONS[feature] || feature}
                        position="bottom"
                      >
                        <span
                          className="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs font-medium rounded-md cursor-help"
                        >
                          {feature}
                        </span>
                      </Tooltip>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4">진행 현황</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Tooltip content="프로젝트에 연결된 도면 분석 세션의 총 수입니다. 각 세션은 하나의 도면 이미지에 대한 분석 단위입니다." position="bottom">
                  <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
                    <FileText className="w-4 h-4" />
                    <span>전체 세션</span>
                  </div>
                </Tooltip>
                <span className="text-xl font-bold text-gray-900 dark:text-white">
                  {project.session_count}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <Tooltip content="검출 및 검증이 모두 완료된 세션 수입니다. completed와 verified 상태를 포함합니다." position="bottom">
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                    <CheckCircle className="w-4 h-4" />
                    <span>완료</span>
                  </div>
                </Tooltip>
                <span className="text-xl font-bold text-green-600 dark:text-green-400">
                  {doneCount}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <Tooltip content="아직 분석이 시작되지 않았거나 검증이 진행 중인 세션 수입니다." position="bottom">
                  <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
                    <Clock className="w-4 h-4" />
                    <span>대기</span>
                  </div>
                </Tooltip>
                <span className="text-xl font-bold text-yellow-600 dark:text-yellow-400">
                  {project.pending_count}
                </span>
              </div>
              <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-between text-sm mb-1">
                  <Tooltip content="완료된 세션의 비율입니다. 100%가 되면 모든 도면 분석이 완료된 것입니다." position="bottom">
                    <span className="text-gray-600 dark:text-gray-400">진행률</span>
                  </Tooltip>
                  <span className="font-medium text-gray-900 dark:text-white">{progressPercent}%</span>
                </div>
                <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 dark:bg-blue-400 transition-all"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 워크플로우: P&ID 검출 → BOM 견적 순서 */}
        <PIDWorkflowSection
          projectId={projectId!}
          project={project}
          onRefresh={loadProject}
          onUnlinkSession={handleUnlinkSession}
          unlinkingSessionId={unlinkingSessionId}
        />
        {project.project_type === 'bom_quotation' && (
          <BOMWorkflowSection
            projectId={projectId!}
            project={project}
            onRefresh={loadProject}
          />
        )}

        {/* 기존 세션 연결 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <div className="px-5 pt-4 pb-2 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-1">
              <Link2 className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <Tooltip content="프로젝트에 포함되지 않은 기존 세션을 이 프로젝트에 연결할 수 있습니다. 연결된 세션은 위의 워크플로우에서 관리됩니다." position="bottom">
                <h2 className="font-semibold text-gray-900 dark:text-white">기존 세션 연결</h2>
              </Tooltip>
              {!isLoadingUnlinked && unlinkedSessions.length > 0 && (
                <span className="px-1.5 py-0.5 rounded-full text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400">
                  {unlinkedSessions.length}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              프로젝트에 포함되지 않은 기존 세션을 연결합니다.
            </p>
          </div>

          {isLoadingUnlinked ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
            </div>
          ) : unlinkedSessions.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-400 dark:text-green-500" />
              </div>
              <p className="text-gray-600 dark:text-gray-300 font-medium">미연결 세션이 없습니다.</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                모든 세션이 프로젝트에 연결되어 있습니다.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {unlinkedSessions.map((session) => (
                <div
                  key={session.session_id}
                  className="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors group"
                >
                  <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center shrink-0">
                    <FileText className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                      {session.filename}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {session.created_at
                        ? new Date(session.created_at).toLocaleDateString('ko-KR')
                        : '날짜 없음'}
                      {' · '}검출: {session.detection_count}개
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium ${
                        session.status === 'completed'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                          : session.status === 'error'
                            ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                            : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                      }`}
                    >
                      {session.status}
                    </span>
                    <button
                      onClick={() => handleLinkSession(session.session_id)}
                      disabled={linkingSessionId === session.session_id}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
                    >
                      {linkingSessionId === session.session_id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Plus className="w-3.5 h-3.5" />
                      )}
                      연결
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        {/* 프로젝트 Import용 hidden input */}
        <input
          ref={importFileRef}
          type="file"
          accept=".json"
          onChange={handleImportProject}
          className="hidden"
        />
      </main>

      {/* 모달 */}
      <ProjectSettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        project={project}
        onUpdated={loadProject}
      />
      <GTManagementModal
        isOpen={showGTManagement}
        onClose={() => setShowGTManagement(false)}
        projectId={projectId!}
      />
    </div>
  );
}

export default ProjectDetailPage;
