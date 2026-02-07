/**
 * ProjectListPage - 프로젝트 목록 페이지
 *
 * web-ui 네이티브 구현 (다크모드 지원)
 */

import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FolderOpen,
  Plus,
  Search,
  RefreshCw,
  Loader2,
  ArrowLeft,
  Building,
  ChevronDown,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { projectApi, type Project } from '../../lib/blueprintBomApi';
import { ProjectCard } from './components/ProjectCard';
import { ProjectCreateModal } from './components/ProjectCreateModal';

export function ProjectListPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [customerFilter, setCustomerFilter] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const loadProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await projectApi.list(customerFilter || undefined, 100);
      setProjects(result.projects ?? []);
    } catch (err) {
      console.error('Failed to load projects:', err);
      setError('프로젝트 목록을 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [customerFilter]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const customers = [...new Set(projects.map((p) => p.customer))].sort();

  const filteredProjects = projects.filter((project) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        project.name.toLowerCase().includes(query) ||
        project.customer.toLowerCase().includes(query) ||
        project.description?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const handleProjectCreated = (projectId: string) => {
    navigate(`/projects/${projectId}`);
  };

  const totalSessions = projects.reduce((sum, p) => sum + p.session_count, 0);
  const totalCompleted = projects.reduce((sum, p) => sum + p.completed_count, 0);
  const totalPending = projects.reduce((sum, p) => sum + p.pending_count, 0);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 헤더 */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                to="/dashboard"
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </Link>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
                  <FolderOpen className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900 dark:text-white">프로젝트</h1>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {projects.length}개 프로젝트
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={loadProjects}
                disabled={isLoading}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="새로고침"
              >
                <RefreshCw
                  className={`w-5 h-5 text-gray-500 dark:text-gray-400 ${isLoading ? 'animate-spin' : ''}`}
                />
              </button>
              <Button
                onClick={() => setShowCreateModal(true)}
                className="bg-blue-500 hover:bg-blue-600 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                새 프로젝트
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 필터 영역 */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="프로젝트 검색..."
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                       placeholder-gray-400 dark:placeholder-gray-500
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       transition-colors"
            />
          </div>
          <div className="relative">
            <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
            <select
              value={customerFilter}
              onChange={(e) => setCustomerFilter(e.target.value)}
              className="pl-10 pr-10 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       appearance-none cursor-pointer transition-colors"
            >
              <option value="">전체 고객사</option>
              {customers.map((customer) => (
                <option key={customer} value={customer}>
                  {customer}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500 pointer-events-none" />
          </div>
        </div>

        {/* 통계 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">전체 프로젝트</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{projects.length}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">전체 세션</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{totalSessions}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">완료</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{totalCompleted}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">대기</p>
            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{totalPending}</p>
          </div>
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-600 dark:text-red-400 mb-6">
            {error}
          </div>
        )}

        {/* 프로젝트 그리드 */}
        {isLoading && projects.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <FolderOpen className="w-8 h-8 text-gray-400 dark:text-gray-500" />
            </div>
            {projects.length === 0 ? (
              <>
                <p className="text-gray-600 dark:text-gray-300 font-medium">프로젝트가 없습니다.</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  "새 프로젝트" 버튼을 클릭하여 시작하세요.
                </p>
              </>
            ) : (
              <>
                <p className="text-gray-600 dark:text-gray-300 font-medium">검색 결과가 없습니다.</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  다른 검색어로 시도해보세요.
                </p>
              </>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
              <ProjectCard key={project.project_id} project={project} />
            ))}
          </div>
        )}
      </main>

      <ProjectCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={handleProjectCreated}
      />
    </div>
  );
}

export default ProjectListPage;
