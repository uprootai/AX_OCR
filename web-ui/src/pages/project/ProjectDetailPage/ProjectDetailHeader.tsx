/**
 * ProjectDetailHeader - 프로젝트 상세 페이지 상단 헤더
 */

import { Link } from 'react-router-dom';
import {
  FolderOpen,
  ArrowLeft,
  Trash2,
  RefreshCw,
  Loader2,
  MoreVertical,
  ExternalLink,
  Download,
  Upload,
  Settings,
  Database,
  Building,
} from 'lucide-react';
import { Tooltip } from '../../../components/ui/Tooltip';
import type { ProjectDetail } from '../../../lib/blueprintBomApi';
import { TYPE_DESCRIPTIONS, type TypeColors } from './constants';

interface ProjectDetailHeaderProps {
  project: ProjectDetail;
  projectId: string;
  colors: TypeColors;
  isLoading: boolean;
  isDeleting: boolean;
  isExporting: boolean;
  isImporting: boolean;
  showMenu: boolean;
  onRefresh: () => void;
  onToggleMenu: (show: boolean) => void;
  onShowSettings: () => void;
  onShowGTManagement: () => void;
  onExport: () => void;
  onImportClick: () => void;
  onDelete: () => void;
}

export function ProjectDetailHeader({
  project,
  projectId,
  colors,
  isLoading,
  isDeleting,
  isExporting,
  isImporting,
  showMenu,
  onRefresh,
  onToggleMenu,
  onShowSettings,
  onShowGTManagement,
  onExport,
  onImportClick,
  onDelete,
}: ProjectDetailHeaderProps) {
  return (
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
                  <Tooltip
                    content={TYPE_DESCRIPTIONS[project.project_type] || '프로젝트 유형'}
                    position="bottom"
                  >
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
              onClick={onRefresh}
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
                onClick={() => onToggleMenu(!showMenu)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <MoreVertical className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
              {showMenu && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => onToggleMenu(false)}
                  />
                  <div className="absolute right-0 mt-2 w-52 bg-white dark:bg-gray-800 rounded-xl shadow-lg dark:shadow-black/30 border border-gray-200 dark:border-gray-700 z-20 overflow-hidden">
                    <button
                      className="w-full px-4 py-2.5 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
                      onClick={onShowSettings}
                    >
                      <Settings className="w-4 h-4" />
                      프로젝트 설정
                    </button>
                    <button
                      className="w-full px-4 py-2.5 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
                      onClick={onShowGTManagement}
                    >
                      <Database className="w-4 h-4" />
                      GT 관리
                    </button>
                    <div className="border-t border-gray-100 dark:border-gray-700" />
                    <a
                      href={`/bom/projects/${projectId}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full px-4 py-2.5 text-left text-sm hover:bg-blue-50 dark:hover:bg-blue-900/30 flex items-center gap-2 text-blue-600 dark:text-blue-400"
                      onClick={() => onToggleMenu(false)}
                    >
                      <ExternalLink className="w-4 h-4" />
                      BOM 전용 UI에서 열기
                    </a>
                    <div className="border-t border-gray-100 dark:border-gray-700" />
                    <button
                      className="w-full px-4 py-2.5 text-left text-sm hover:bg-blue-50 dark:hover:bg-blue-900/30 flex items-center gap-2 text-blue-600 dark:text-blue-400"
                      onClick={onExport}
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
                      onClick={onImportClick}
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
                      onClick={onDelete}
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
  );
}
