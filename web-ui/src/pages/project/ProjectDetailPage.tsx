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
  Upload,
  FileText,
  CheckCircle,
  Clock,
  LayoutTemplate,
  Building,
  RefreshCw,
  Loader2,
  MoreVertical,
  Settings,
  Database,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { projectApi, type ProjectDetail } from '../../lib/blueprintBomApi';
import { BOMWorkflowSection } from './components/BOMWorkflowSection';
import { PIDWorkflowSection } from './components/PIDWorkflowSection';

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0 || !projectId) return;
    setIsUploading(true);
    setError(null);
    try {
      await projectApi.batchUpload(projectId, Array.from(files));
      await loadProject();
    } catch (err) {
      console.error('Failed to upload files:', err);
      setError('파일 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  const progressPercent =
    project && project.session_count > 0
      ? Math.round((project.completed_count / project.session_count) * 100)
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
                    <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${colors.badge}`}>
                      {colors.label}
                    </span>
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
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="bg-blue-500 hover:bg-blue-600 text-white"
              >
                {isUploading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4 mr-2" />
                )}
                도면 추가
              </Button>
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
                    <div className="absolute right-0 mt-2 w-52 bg-white dark:bg-gray-800 rounded-xl shadow-lg dark:shadow-black/30 border border-gray-200 dark:border-gray-700 z-20 overflow-hidden">
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
                        className="w-full px-4 py-2.5 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
                        onClick={() => setShowMenu(false)}
                      >
                        <Settings className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                        프로젝트 설정
                      </button>
                      <button
                        className="w-full px-4 py-2.5 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
                        onClick={() => setShowMenu(false)}
                      >
                        <Database className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                        GT 관리
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

          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
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
              <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-400">진행률</span>
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
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 dark:text-white">세션 목록</h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {(project.sessions ?? []).length}개
            </span>
          </div>
          {(project.sessions ?? []).length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-gray-400 dark:text-gray-500" />
              </div>
              <p className="text-gray-600 dark:text-gray-300 font-medium">세션이 없습니다.</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                "도면 추가" 버튼을 클릭하여 도면을 업로드하세요.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {(project.sessions ?? []).map((session) => (
                <Link
                  key={session.session_id}
                  to={`/blueprintflow/builder?session=${session.session_id}`}
                  className="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors group"
                >
                  <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {session.filename}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      검출: {session.detection_count}개 | 검증: {session.verified_count}개
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
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
                    <ChevronRight className="w-5 h-5 text-gray-400 dark:text-gray-500 group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-colors" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default ProjectDetailPage;
