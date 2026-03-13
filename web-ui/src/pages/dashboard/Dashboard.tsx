import { useState } from 'react';
import APIStatusMonitor from '../../components/monitoring/APIStatusMonitor';
import ContainerManager from '../../components/dashboard/ContainerManager';
import AddAPIDialog from '../../components/dashboard/AddAPIDialog';
import ExportToBuiltinDialog from '../../components/dashboard/ExportToBuiltinDialog';
import Toast from '../../components/ui/Toast';
import { type APIConfig } from '../../store/apiConfigStore';
import {
  useDashboard,
  DashboardHeader,
  SectionNav,
  ProjectsSection,
  CustomAPIsSection,
  QuickActions,
  QuickStats,
  GettingStarted,
} from './components';

// Re-export types for consumers that may import from this file
export type { ToastState, ProjectWithSessions } from './components';

export default function Dashboard() {
  const [isAddAPIDialogOpen, setIsAddAPIDialogOpen] = useState(false);
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const [selectedAPIForExport, setSelectedAPIForExport] = useState<APIConfig | null>(null);

  const {
    toast,
    setToast,
    showToast,
    projectData,
    projectsLoading,
    fetchProjects,
    isAutoDiscovering,
    handleAutoDiscover,
    customAPIs,
    removeAPI,
    toggleAPI,
  } = useDashboard();

  const handleExportAPI = (api: APIConfig) => {
    setSelectedAPIForExport(api);
    setIsExportDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <DashboardHeader
        isAutoDiscovering={isAutoDiscovering}
        onAutoDiscover={handleAutoDiscover}
        onAddAPI={() => setIsAddAPIDialogOpen(true)}
      />

      <SectionNav hasCustomAPIs={customAPIs.length > 0} />

      {/* API Status Monitor */}
      <div id="section-api" className="scroll-mt-4">
        <APIStatusMonitor />
      </div>

      {/* Container Manager */}
      <div id="section-containers" className="scroll-mt-4">
        <ContainerManager />
      </div>

      <ProjectsSection
        projectData={projectData}
        projectsLoading={projectsLoading}
        onRefresh={fetchProjects}
      />

      {/* Add API Dialog */}
      <AddAPIDialog
        isOpen={isAddAPIDialogOpen}
        onClose={() => setIsAddAPIDialogOpen(false)}
      />

      {/* Export to Built-in Dialog */}
      <ExportToBuiltinDialog
        isOpen={isExportDialogOpen}
        onClose={() => {
          setIsExportDialogOpen(false);
          setSelectedAPIForExport(null);
        }}
        apiConfig={selectedAPIForExport}
      />

      <CustomAPIsSection
        customAPIs={customAPIs}
        onToggle={toggleAPI}
        onExport={handleExportAPI}
        onRemove={(id, displayName) => {
          removeAPI(id);
          showToast(`✓ ${displayName} API가 삭제되었습니다`, 'success');
        }}
      />

      <QuickActions />

      <QuickStats />

      <GettingStarted />

      {/* Toast 알림 */}
      {toast.show && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.type === 'error' ? 15000 : 10000}
          onClose={() => setToast(prev => ({ ...prev, show: false }))}
        />
      )}
    </div>
  );
}
