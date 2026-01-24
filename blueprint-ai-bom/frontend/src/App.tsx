/**
 * Blueprint AI BOM - Main App
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout';
import { HomePage, DetectionPage, VerificationPage, BOMPage, WorkflowPage, GuidePage } from './pages';
import { ProjectListPage, ProjectDetailPage } from './pages/project';
import { CustomerWorkflowPage, CustomerImageReviewPage, CustomerSessionPage } from './pages/customer';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 새로운 통합 워크플로우 페이지 (기본) */}
        <Route path="/" element={<WorkflowPage />} />
        <Route path="/workflow" element={<WorkflowPage />} />
        <Route path="/guide" element={<GuidePage />} />

        {/* Phase 2D: 프로젝트 관리 */}
        <Route path="/projects" element={<ProjectListPage />} />
        <Route path="/projects/:projectId" element={<ProjectDetailPage />} />

        {/* Phase 2F: 고객용 UI (프로젝트 기반) */}
        <Route path="/customer/:projectId" element={<CustomerWorkflowPage />} />
        <Route path="/customer/:projectId/review/:imageId" element={<CustomerImageReviewPage />} />

        {/* Phase 2G: 고객용 UI (워크플로우 세션 기반) */}
        <Route path="/customer/session/:sessionId" element={<CustomerSessionPage />} />

        {/* 기존 페이지들 (호환성 유지) */}
        <Route element={<Layout />}>
          <Route path="/legacy" element={<HomePage />} />
          <Route path="/detection" element={<DetectionPage />} />
          <Route path="/verification" element={<VerificationPage />} />
          <Route path="/bom" element={<BOMPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
