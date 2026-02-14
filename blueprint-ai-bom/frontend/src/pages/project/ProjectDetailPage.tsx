/**
 * ProjectDetailPage - 프로젝트 상세 페이지
 * Phase 2D: 프로젝트 관리 UI
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  FolderOpen,
  ArrowLeft,
  Trash2,
  Upload,
  Download,
  FileText,
  CheckCircle,
  Clock,
  LayoutTemplate,
  Building,
  RefreshCw,
  Loader2,
  MoreVertical,
  ExternalLink,
  Settings,
  Database,
} from 'lucide-react';
import { projectApi, sessionApi, type ProjectDetail } from '../../lib/api';
import { BOMWorkflowSection } from './components/BOMWorkflowSection';
import { PIDWorkflowSection } from './components/PIDWorkflowSection';
import { ProjectSettingsModal } from './components/ProjectSettingsModal';
import { GTManagementModal } from './components/GTManagementModal';
import { ThemeToggle } from '../../components/ThemeToggle';
import { useTheme } from '../../hooks/useTheme';

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { isDark, toggle: toggleTheme } = useTheme();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showGTManagement, setShowGTManagement] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const importFileRef = useRef<HTMLInputElement>(null);

  // 프로젝트 로드
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

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  // 프로젝트 삭제
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

  // 도면 업로드
  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0 || !projectId) return;
    setIsUploading(true);
    setError(null);
    try {
      // 각 파일을 개별 세션으로 업로드
      for (const file of Array.from(files)) {
        await sessionApi.upload(file);
      }
      await loadProject();
    } catch (err) {
      console.error('Failed to upload files:', err);
      setError('파일 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  // 프로젝트 Export
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

  // 프로젝트 Import
  const handleImportProject = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setIsImporting(true);
    setShowMenu(false);
    try {
      const result = await projectApi.importProject(file);
      navigate(`/projects/${result.project_id}`);
    } catch (err) {
      console.error('Failed to import project:', err);
      setError('프로젝트 Import에 실패했습니다.');
    } finally {
      setIsImporting(false);
      if (importFileRef.current) importFileRef.current.value = '';
    }
  };

  // 진행률 계산
  const progressPercent =
    project && project.session_count > 0
      ? Math.round((project.completed_count / project.session_count) * 100)
      : 0;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <FolderOpen className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
          <p className="text-gray-500 dark:text-gray-400">{error || '프로젝트를 찾을 수 없습니다.'}</p>
          <Link
            to="/projects"
            className="inline-flex items-center gap-2 mt-4 text-blue-500 hover:text-blue-600"
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
      <header className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                to="/projects"
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </Link>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">{project.name}</h1>
                <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                  <Building className="w-3.5 h-3.5" />
                  <span>{project.customer}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle isDark={isDark} onToggle={toggleTheme} />
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
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
              >
                {isUploading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
                도면 추가
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,.pdf"
                className="hidden"
                onChange={(e) => handleUpload(e.target.files)}
              />
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
                    <div className="absolute right-0 mt-2 w-52 bg-white dark:bg-gray-800 rounded-lg shadow-lg border dark:border-gray-700 z-20 overflow-hidden">
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
                      <hr className="dark:border-gray-700" />
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
                      <hr className="dark:border-gray-700" />
                      <button
                        className="w-full px-4 py-2.5 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
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
        {/* 에러 메시지 */}
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 mb-6">
            {error}
          </div>
        )}

        {/* 프로젝트 정보 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* 기본 정보 */}
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl border dark:border-gray-700 p-6">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4">프로젝트 정보</h2>
            {project.description && (
              <p className="text-gray-600 dark:text-gray-300 mb-4">{project.description}</p>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">생성일</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {new Date(project.created_at).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">최근 수정</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {new Date(project.updated_at).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>
              {project.default_template_name && (
                <div className="col-span-2">
                  <p className="text-sm text-gray-500 dark:text-gray-400">기본 템플릿</p>
                  <div className="flex items-center gap-2 font-medium text-blue-600 dark:text-blue-400">
                    <LayoutTemplate className="w-4 h-4" />
                    {project.default_template_name}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 통계 */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border dark:border-gray-700 p-6">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4">진행 현황</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
                  <FileText className="w-4 h-4" />
                  <span>전체 세션</span>
                </div>
                <span className="text-xl font-bold text-gray-900 dark:text-white">
                  {project.session_count}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                  <CheckCircle className="w-4 h-4" />
                  <span>완료</span>
                </div>
                <span className="text-xl font-bold text-green-600 dark:text-green-400">
                  {project.completed_count}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
                  <Clock className="w-4 h-4" />
                  <span>대기</span>
                </div>
                <span className="text-xl font-bold text-yellow-600 dark:text-yellow-400">
                  {project.pending_count}
                </span>
              </div>
              <div className="pt-2">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-400">진행률</span>
                  <span className="font-medium text-gray-900 dark:text-white">{progressPercent}%</span>
                </div>
                <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 워크플로우 - 타입에 따라 분기 */}
        {project.project_type !== 'pid_detection' ? (
          <BOMWorkflowSection
            projectId={projectId!}
            project={project}
            onRefresh={loadProject}
          />
        ) : (
          <PIDWorkflowSection
            projectId={projectId!}
            project={project}
            onRefresh={loadProject}
          />
        )}

        {/* 세션 목록 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border dark:border-gray-700">
          <div className="p-4 border-b dark:border-gray-700 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 dark:text-white">세션 목록</h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {(project.sessions ?? []).length}개
            </span>
          </div>
          {(project.sessions ?? []).length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
              <p className="text-gray-500 dark:text-gray-400">세션이 없습니다.</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                "도면 추가" 버튼을 클릭하여 도면을 업로드하세요.
              </p>
            </div>
          ) : (
            <div className="divide-y dark:divide-gray-700">
              {(project.sessions ?? []).map((session) => (
                <Link
                  key={session.session_id}
                  to={`/workflow?session=${session.session_id}`}
                  className="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white truncate">
                      {session.filename}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      검출: {session.detection_count}개 | 검증: {session.verified_count}개
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        session.status === 'completed'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                          : session.status === 'error'
                            ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                            : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                      }`}
                    >
                      {session.status}
                    </span>
                    <ExternalLink className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                  </div>
                </Link>
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
