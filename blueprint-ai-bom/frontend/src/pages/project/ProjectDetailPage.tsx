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
  ChevronDown,
  ChevronRight,
  Images,
} from 'lucide-react';
import { projectApi, sessionApi, type ProjectDetail } from '../../lib/api';
import { BOMWorkflowSection } from './components/BOMWorkflowSection';
import { PIDWorkflowSection } from './components/PIDWorkflowSection';
import { ProjectSettingsModal } from './components/ProjectSettingsModal';
import { GTManagementModal } from './components/GTManagementModal';
import { ThemeToggle } from '../../components/ThemeToggle';
import { useTheme } from '../../hooks/useTheme';

// 카테고리 정렬 순서 (BOM PDF 분홍색 구조)
const CATEGORY_ORDER = [
  '저널베어링 (Journal Bearing) — 8 SET',
  '스러스트베어링 (Thrust Bearing) — 2 SET',
  '체결부품 (Fasteners)',
  '조정부품 (Adjustment Parts)',
  '기타부품 (Miscellaneous)',
];

// 카테고리 색상 (BOM PDF 분홍색 계열)
const CATEGORY_COLORS: Record<string, string> = {
  '저널베어링 (Journal Bearing) — 8 SET':
    'bg-pink-50 dark:bg-pink-950/30 border-pink-200 dark:border-pink-800',
  '스러스트베어링 (Thrust Bearing) — 2 SET':
    'bg-rose-50 dark:bg-rose-950/30 border-rose-200 dark:border-rose-800',
  '체결부품 (Fasteners)':
    'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800',
  '조정부품 (Adjustment Parts)':
    'bg-sky-50 dark:bg-sky-950/30 border-sky-200 dark:border-sky-800',
  '기타부품 (Miscellaneous)':
    'bg-gray-50 dark:bg-gray-900/30 border-gray-200 dark:border-gray-700',
};

const CATEGORY_HEADER_COLORS: Record<string, string> = {
  '저널베어링 (Journal Bearing) — 8 SET':
    'text-pink-700 dark:text-pink-300 bg-pink-100 dark:bg-pink-900/40',
  '스러스트베어링 (Thrust Bearing) — 2 SET':
    'text-rose-700 dark:text-rose-300 bg-rose-100 dark:bg-rose-900/40',
  '체결부품 (Fasteners)':
    'text-amber-700 dark:text-amber-300 bg-amber-100 dark:bg-amber-900/40',
  '조정부품 (Adjustment Parts)':
    'text-sky-700 dark:text-sky-300 bg-sky-100 dark:bg-sky-900/40',
  '기타부품 (Miscellaneous)':
    'text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800/40',
};

type SessionItem = {
  session_id: string;
  filename: string;
  status: string;
  detection_count: number;
  verified_count: number;
  image_count?: number;
  metadata?: Record<string, unknown>;
};

function SubImageTable({ sessionId }: { sessionId: string }) {
  const [images, setImages] = useState<Array<{
    image_id: string; filename: string;
    od?: string | null; id?: string | null; width?: string | null;
    dimension_count?: number;
  }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    sessionApi.listImages(sessionId)
      .then((imgs) => setImages(imgs as typeof images))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <div className="px-6 py-3 text-xs text-gray-400 dark:text-gray-500">
        <Loader2 className="w-3 h-3 animate-spin inline mr-1" />
        이미지 로딩 중...
      </div>
    );
  }

  if (images.length === 0) return null;

  const hasAnyDims = images.some((img) => img.od || img.id || img.width);

  return (
    <div className="px-4 pb-3">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-gray-500 dark:text-gray-400 border-b dark:border-gray-700">
            <th className="text-left py-1.5 pl-2 font-medium">도면</th>
            {hasAnyDims && (
              <>
                <th className="text-right py-1.5 px-2 font-medium w-20">OD</th>
                <th className="text-right py-1.5 px-2 font-medium w-20">ID</th>
                <th className="text-right py-1.5 px-2 font-medium w-20">W</th>
              </>
            )}
            <th className="text-right py-1.5 pr-2 font-medium w-16">치수</th>
          </tr>
        </thead>
        <tbody>
          {images.map((img) => (
            <tr
              key={img.image_id}
              className="border-b border-gray-50 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/30"
            >
              <td className="py-1.5 pl-2 text-gray-700 dark:text-gray-300 truncate max-w-[200px]">
                {img.filename?.replace('.png', '')}
              </td>
              {hasAnyDims && (
                <>
                  <td className="text-right py-1.5 px-2 font-mono text-gray-900 dark:text-white">
                    {img.od ? <span className="text-pink-600 dark:text-pink-400">{img.od}</span> : <span className="text-gray-300 dark:text-gray-600">—</span>}
                  </td>
                  <td className="text-right py-1.5 px-2 font-mono text-gray-900 dark:text-white">
                    {img.id ? <span className="text-blue-600 dark:text-blue-400">{img.id}</span> : <span className="text-gray-300 dark:text-gray-600">—</span>}
                  </td>
                  <td className="text-right py-1.5 px-2 font-mono text-gray-900 dark:text-white">
                    {img.width ? <span className="text-amber-600 dark:text-amber-400">{img.width}</span> : <span className="text-gray-300 dark:text-gray-600">—</span>}
                  </td>
                </>
              )}
              <td className="text-right py-1.5 pr-2 text-gray-500 dark:text-gray-400">
                {img.dimension_count ?? 0}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GroupedSessionList({ sessions }: { sessions: SessionItem[] }) {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [expandedSession, setExpandedSession] = useState<string | null>(null);

  if (sessions.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl border dark:border-gray-700 p-12 text-center">
        <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
        <p className="text-gray-500 dark:text-gray-400">세션이 없습니다.</p>
      </div>
    );
  }

  // 카테고리별 그룹핑
  const groups: Record<string, SessionItem[]> = {};
  for (const s of sessions) {
    const cat = (s.metadata?.category as string) || '미분류';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(s);
  }

  // 정렬: CATEGORY_ORDER 순서, 없는 카테고리는 뒤로
  const sortedCategories = Object.keys(groups).sort((a, b) => {
    const ai = CATEGORY_ORDER.indexOf(a);
    const bi = CATEGORY_ORDER.indexOf(b);
    return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
  });

  const toggle = (cat: string) =>
    setCollapsed((prev) => ({ ...prev, [cat]: !prev[cat] }));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-900 dark:text-white">
          세션 목록
        </h2>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {sortedCategories.length}개 카테고리 · {sessions.length}개 세션
        </span>
      </div>

      {sortedCategories.map((category) => {
        const items = groups[category];
        const isCollapsed = collapsed[category] ?? false;
        const borderColor =
          CATEGORY_COLORS[category] ||
          'bg-gray-50 dark:bg-gray-900/30 border-gray-200 dark:border-gray-700';
        const headerColor =
          CATEGORY_HEADER_COLORS[category] ||
          'text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800/40';

        return (
          <div
            key={category}
            className={`rounded-xl border overflow-hidden ${borderColor}`}
          >
            {/* 카테고리 헤더 (분홍색 그룹) */}
            <button
              onClick={() => toggle(category)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-left font-semibold text-sm ${headerColor} transition-colors hover:opacity-90`}
            >
              {isCollapsed ? (
                <ChevronRight className="w-4 h-4 flex-shrink-0" />
              ) : (
                <ChevronDown className="w-4 h-4 flex-shrink-0" />
              )}
              <span className="flex-1">{category}</span>
              <span className="text-xs font-normal opacity-70">
                {items.length}개 세션
              </span>
            </button>

            {/* 세션 목록 (노란색 서브) */}
            {!isCollapsed && (
              <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
                {items.map((session) => {
                  const isExpanded = expandedSession === session.session_id;
                  return (
                    <div key={session.session_id}>
                      <div
                        className="flex items-center gap-4 px-4 py-3 hover:bg-white/60 dark:hover:bg-gray-700/30 transition-colors cursor-pointer"
                        onClick={() =>
                          setExpandedSession(isExpanded ? null : session.session_id)
                        }
                      >
                        <div className="w-9 h-9 bg-white dark:bg-gray-700 rounded-lg flex items-center justify-center border dark:border-gray-600">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm text-gray-900 dark:text-white truncate">
                            {session.filename}
                          </p>
                          <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            <span>
                              검출: {session.detection_count}개
                            </span>
                            <span>
                              검증: {session.verified_count}개
                            </span>
                            {(session.image_count ?? 0) > 0 && (
                              <span className="inline-flex items-center gap-1">
                                <Images className="w-3 h-3" />
                                {session.image_count}장
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium ${
                              session.status === 'completed'
                                ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                                : session.status === 'error'
                                  ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                                  : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                            }`}
                          >
                            {session.status}
                          </span>
                          <Link
                            to={`/workflow?session=${session.session_id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                            title="워크플로우 열기"
                          >
                            <ExternalLink className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
                          </Link>
                        </div>
                      </div>
                      {isExpanded && (
                        <SubImageTable sessionId={session.session_id} />
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

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

        {/* 세션 목록 — 카테고리별 그룹핑 */}
        <GroupedSessionList sessions={project.sessions ?? []} />
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
