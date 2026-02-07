/**
 * ProjectListPage - 프로젝트 목록 페이지
 * Phase 2D: 프로젝트 관리 UI
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
import { projectApi, type Project } from '../../lib/api';
import { ProjectCard } from './components/ProjectCard';
import { ProjectCreateModal } from './components/ProjectCreateModal';
import { ThemeToggle } from '../../components/ThemeToggle';
import { useTheme } from '../../hooks/useTheme';

export function ProjectListPage() {
  const navigate = useNavigate();
  const { isDark, toggle: toggleTheme } = useTheme();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [customerFilter, setCustomerFilter] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // 프로젝트 목록 로드
  const loadProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await projectApi.list(
        customerFilter || undefined,
        100
      );
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

  // 고객사 목록 추출
  const customers = [...new Set(projects.map((p) => p.customer))].sort();

  // 필터링된 프로젝트
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

  // 프로젝트 생성 완료 핸들러
  const handleProjectCreated = (projectId: string) => {
    navigate(`/projects/${projectId}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 헤더 */}
      <header className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </Link>
              <div className="flex items-center gap-2">
                <FolderOpen className="w-6 h-6 text-blue-500" />
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">프로젝트</h1>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle isDark={isDark} onToggle={toggleTheme} />
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
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                <Plus className="w-4 h-4" />
                새 프로젝트
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 필터 영역 */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          {/* 검색 */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="프로젝트 검색..."
              className="w-full pl-10 pr-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* 고객사 필터 */}
          <div className="relative">
            <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
            <select
              value={customerFilter}
              onChange={(e) => setCustomerFilter(e.target.value)}
              className="pl-10 pr-8 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none"
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
          <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">전체 프로젝트</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{projects.length}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">전체 세션</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {projects.reduce((sum, p) => sum + p.session_count, 0)}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">완료</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {projects.reduce((sum, p) => sum + p.completed_count, 0)}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">대기</p>
            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {projects.reduce((sum, p) => sum + p.pending_count, 0)}
            </p>
          </div>
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 mb-6">
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
            <FolderOpen className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            {projects.length === 0 ? (
              <>
                <p className="text-gray-500 dark:text-gray-400">프로젝트가 없습니다.</p>
                <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                  "새 프로젝트" 버튼을 클릭하여 시작하세요.
                </p>
              </>
            ) : (
              <>
                <p className="text-gray-500 dark:text-gray-400">검색 결과가 없습니다.</p>
                <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
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

      {/* 프로젝트 생성 모달 */}
      <ProjectCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={handleProjectCreated}
      />
    </div>
  );
}

export default ProjectListPage;
