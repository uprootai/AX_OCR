/**
 * ProjectDetailPage - 프로젝트 상세 페이지 (orchestrator)
 *
 * web-ui 네이티브 구현 (다크모드 지원)
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FolderOpen, ArrowLeft, Loader2 } from 'lucide-react';
import {
  projectApi,
  sessionApi,
  type ProjectDetail,
  type SessionListItem,
} from '../../../lib/blueprintBomApi';
import { BOMWorkflowSection } from '../components/BOMWorkflowSection';
import { PIDWorkflowSection } from '../components/PIDWorkflowSection';
import { ProjectSettingsModal } from '../components/ProjectSettingsModal';
import { GTManagementModal } from '../components/GTManagementModal';
import { getTypeColors } from './constants';
import { ProjectDetailHeader } from './ProjectDetailHeader';
import { ProjectInfoPanel } from './ProjectInfoPanel';
import { UnlinkedSessionsPanel } from './UnlinkedSessionsPanel';

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
    ? project.completed_count +
      (project.sessions ?? []).filter((s) => s.status === 'verified').length
    : 0;
  const progressPercent =
    project && project.session_count > 0
      ? Math.round((doneCount / project.session_count) * 100)
      : 0;

  const colors = getTypeColors(project);

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
      <ProjectDetailHeader
        project={project}
        projectId={projectId!}
        colors={colors}
        isLoading={isLoading}
        isDeleting={isDeleting}
        isExporting={isExporting}
        isImporting={isImporting}
        showMenu={showMenu}
        onRefresh={loadProject}
        onToggleMenu={setShowMenu}
        onShowSettings={() => { setShowMenu(false); setShowSettings(true); }}
        onShowGTManagement={() => { setShowMenu(false); setShowGTManagement(true); }}
        onExport={handleExportProject}
        onImportClick={() => { setShowMenu(false); importFileRef.current?.click(); }}
        onDelete={() => { setShowMenu(false); handleDelete(); }}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-600 dark:text-red-400 mb-6">
            {error}
          </div>
        )}

        <ProjectInfoPanel
          project={project}
          doneCount={doneCount}
          progressPercent={progressPercent}
        />

        {/* 워크플로우: P&ID 검출 → BOM 견적 순서 */}
        {(project.project_type === 'pid_detection' || (project.sessions ?? []).length > 0) && (
          <PIDWorkflowSection
            projectId={projectId!}
            project={project}
            onRefresh={loadProject}
            onUnlinkSession={handleUnlinkSession}
            unlinkingSessionId={unlinkingSessionId}
          />
        )}
        {project.project_type === 'bom_quotation' && (
          <BOMWorkflowSection
            projectId={projectId!}
            project={project}
            onRefresh={loadProject}
          />
        )}

        <UnlinkedSessionsPanel
          unlinkedSessions={unlinkedSessions}
          isLoadingUnlinked={isLoadingUnlinked}
          linkingSessionId={linkingSessionId}
          onLinkSession={handleLinkSession}
        />

        {/* 프로젝트 Import용 hidden input */}
        <input
          ref={importFileRef}
          type="file"
          accept=".json"
          onChange={handleImportProject}
          className="hidden"
        />
      </main>

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
