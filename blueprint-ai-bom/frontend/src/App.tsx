/**
 * Blueprint AI BOM - Main App
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout';
import { HomePage, DetectionPage, VerificationPage, BOMPage, WorkflowPage, GuidePage } from './pages';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 새로운 통합 워크플로우 페이지 (기본) */}
        <Route path="/" element={<WorkflowPage />} />
        <Route path="/workflow" element={<WorkflowPage />} />
        <Route path="/guide" element={<GuidePage />} />

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
