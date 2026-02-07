/**
 * ProjectCard - 프로젝트 카드 컴포넌트
 *
 * web-ui 네이티브 구현 (다크모드 지원)
 */

import { Link } from 'react-router-dom';
import {
  FolderOpen,
  FileText,
  CheckCircle,
  Clock,
  Building,
  LayoutTemplate,
  ChevronRight,
} from 'lucide-react';
import type { Project } from '../../../lib/blueprintBomApi';

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const progressPercent =
    project.session_count > 0
      ? Math.round((project.completed_count / project.session_count) * 100)
      : 0;

  // project_type에 따른 색상
  const getTypeColors = () => {
    if (project.project_type === 'pid_detection') {
      return {
        bg: 'bg-cyan-100 dark:bg-cyan-900/30',
        icon: 'text-cyan-600 dark:text-cyan-400',
        badge: 'bg-cyan-100 dark:bg-cyan-900/50 text-cyan-700 dark:text-cyan-300',
        label: 'P&ID',
      };
    }
    if (project.project_type === 'bom_quotation') {
      return {
        bg: 'bg-pink-100 dark:bg-pink-900/30',
        icon: 'text-pink-600 dark:text-pink-400',
        badge: 'bg-pink-100 dark:bg-pink-900/50 text-pink-700 dark:text-pink-300',
        label: 'BOM',
      };
    }
    // general
    return {
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      icon: 'text-blue-600 dark:text-blue-400',
      badge: 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300',
      label: '일반',
    };
  };

  const colors = getTypeColors();

  return (
    <Link
      to={`/projects/${project.project_id}`}
      className="block bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700
               shadow-sm hover:shadow-md dark:hover:shadow-lg dark:hover:shadow-black/20
               transition-all group"
    >
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors.bg}`}>
              <FolderOpen className={`w-5 h-5 ${colors.icon}`} />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {project.name}
              </h3>
              <div className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                <Building className="w-3.5 h-3.5" />
                <span>{project.customer}</span>
                <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${colors.badge}`}>
                  {colors.label}
                </span>
              </div>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-gray-400 dark:text-gray-500 group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-colors" />
        </div>

        {project.description && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-3 line-clamp-2">
            {project.description}
          </p>
        )}

        <div className="grid grid-cols-3 gap-3 mt-4">
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div className="flex items-center justify-center gap-1 text-gray-600 dark:text-gray-300">
              <FileText className="w-4 h-4" />
              <span className="text-lg font-bold">{project.session_count}</span>
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400">세션</span>
          </div>
          <div className="text-center p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="flex items-center justify-center gap-1 text-green-600 dark:text-green-400">
              <CheckCircle className="w-4 h-4" />
              <span className="text-lg font-bold">{project.completed_count}</span>
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400">완료</span>
          </div>
          <div className="text-center p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <div className="flex items-center justify-center gap-1 text-yellow-600 dark:text-yellow-400">
              <Clock className="w-4 h-4" />
              <span className="text-lg font-bold">{project.pending_count}</span>
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400">대기</span>
          </div>
        </div>

        {project.session_count > 0 && (
          <div className="mt-4">
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
        )}

        {project.default_template_name && (
          <div className="flex items-center gap-2 mt-4 text-sm text-gray-500 dark:text-gray-400">
            <LayoutTemplate className="w-4 h-4" />
            <span>템플릿: {project.default_template_name}</span>
          </div>
        )}
      </div>

      <div className="px-5 py-3 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-b-xl">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>생성: {new Date(project.created_at).toLocaleDateString('ko-KR')}</span>
          <span>수정: {new Date(project.updated_at).toLocaleDateString('ko-KR')}</span>
        </div>
      </div>
    </Link>
  );
}

export default ProjectCard;
