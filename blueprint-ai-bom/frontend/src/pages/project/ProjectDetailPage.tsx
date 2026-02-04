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
} from 'lucide-react';
import { projectApi, sessionApi, type ProjectDetail } from '../../lib/api';
import { BOMWorkflowSection } from './components/BOMWorkflowSection';

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

  // 진행률 계산
  const progressPercent =
    project && project.session_count > 0
      ? Math.round((project.completed_count / project.session_count) * 100)
      : 0;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <FolderOpen className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">{error || '프로젝트를 찾을 수 없습니다.'}</p>
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
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                to="/projects"
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-500" />
              </Link>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{project.name}</h1>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Building className="w-3.5 h-3.5" />
                  <span>{project.customer}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={loadProject}
                disabled={isLoading}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="새로고침"
              >
                <RefreshCw
                  className={`w-5 h-5 text-gray-500 ${isLoading ? 'animate-spin' : ''}`}
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
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <MoreVertical className="w-5 h-5 text-gray-500" />
                </button>
                {showMenu && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setShowMenu(false)}
                    />
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-20">
                      <button
                        className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                        onClick={() => {
                          setShowMenu(false);
                          // TODO: 설정 모달
                        }}
                      >
                        <Settings className="w-4 h-4 text-gray-400" />
                        프로젝트 설정
                      </button>
                      <button
                        className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                        onClick={() => {
                          setShowMenu(false);
                          // TODO: GT 관리
                        }}
                      >
                        <Database className="w-4 h-4 text-gray-400" />
                        GT 관리
                      </button>
                      <hr />
                      <button
                        className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
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
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 mb-6">
            {error}
          </div>
        )}

        {/* 프로젝트 정보 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* 기본 정보 */}
          <div className="lg:col-span-2 bg-white rounded-xl border p-6">
            <h2 className="font-semibold text-gray-900 mb-4">프로젝트 정보</h2>
            {project.description && (
              <p className="text-gray-600 mb-4">{project.description}</p>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">생성일</p>
                <p className="font-medium">
                  {new Date(project.created_at).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">최근 수정</p>
                <p className="font-medium">
                  {new Date(project.updated_at).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>
              {project.default_template_name && (
                <div className="col-span-2">
                  <p className="text-sm text-gray-500">기본 템플릿</p>
                  <div className="flex items-center gap-2 font-medium text-blue-600">
                    <LayoutTemplate className="w-4 h-4" />
                    {project.default_template_name}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 통계 */}
          <div className="bg-white rounded-xl border p-6">
            <h2 className="font-semibold text-gray-900 mb-4">진행 현황</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-gray-600">
                  <FileText className="w-4 h-4" />
                  <span>전체 세션</span>
                </div>
                <span className="text-xl font-bold text-gray-900">
                  {project.session_count}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle className="w-4 h-4" />
                  <span>완료</span>
                </div>
                <span className="text-xl font-bold text-green-600">
                  {project.completed_count}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-yellow-600">
                  <Clock className="w-4 h-4" />
                  <span>대기</span>
                </div>
                <span className="text-xl font-bold text-yellow-600">
                  {project.pending_count}
                </span>
              </div>
              <div className="pt-2">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-600">진행률</span>
                  <span className="font-medium">{progressPercent}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* BOM 워크플로우 */}
        <BOMWorkflowSection
          projectId={projectId!}
          project={project}
          onRefresh={loadProject}
        />

        {/* 세션 목록 */}
        <div className="bg-white rounded-xl border">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">세션 목록</h2>
            <span className="text-sm text-gray-500">
              {project.sessions.length}개
            </span>
          </div>
          {project.sessions.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">세션이 없습니다.</p>
              <p className="text-sm text-gray-400 mt-1">
                "도면 추가" 버튼을 클릭하여 도면을 업로드하세요.
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {project.sessions.map((session) => (
                <Link
                  key={session.session_id}
                  to={`/workflow?session=${session.session_id}`}
                  className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">
                      {session.filename}
                    </p>
                    <p className="text-sm text-gray-500">
                      검출: {session.detection_count}개 | 검증: {session.verified_count}개
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        session.status === 'completed'
                          ? 'bg-green-100 text-green-600'
                          : session.status === 'error'
                            ? 'bg-red-100 text-red-600'
                            : 'bg-blue-100 text-blue-600'
                      }`}
                    >
                      {session.status}
                    </span>
                    <ExternalLink className="w-4 h-4 text-gray-400" />
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
