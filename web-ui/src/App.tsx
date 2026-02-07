import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useUIStore } from './store/uiStore';
import { useEffect, lazy, Suspense } from 'react';

// Error Boundary
import ErrorBoundary from './components/ErrorBoundary';

// Layout (sync - always needed)
import Layout from './components/layout/Layout';

// Landing (sync - first page)
import Landing from './pages/Landing';

// Lazy-loaded Pages
const Dashboard = lazy(() => import('./pages/dashboard/Dashboard'));
const Guide = lazy(() => import('./pages/dashboard/Guide'));
const Docs = lazy(() => import('./pages/docs/Docs'));
// Monitor 페이지 제거됨 - Dashboard의 APIStatusMonitor로 통합
const Admin = lazy(() => import('./pages/admin/Admin'));
const APIDetail = lazy(() => import('./pages/admin/APIDetail'));

// BlueprintFlow Pages (lazy - heavy components)
const BlueprintFlowBuilder = lazy(() => import('./pages/blueprintflow/BlueprintFlowBuilder'));
const BlueprintFlowList = lazy(() => import('./pages/blueprintflow/BlueprintFlowList'));
const BlueprintFlowTemplates = lazy(() => import('./pages/blueprintflow/BlueprintFlowTemplates'));

// PID Overlay Page (lazy)
const PIDOverlayPage = lazy(() => import('./pages/pid-overlay/PIDOverlayPage'));

// Project Pages (lazy)
const ProjectList = lazy(() => import('./pages/project/ProjectListPage'));
const ProjectDetail = lazy(() => import('./pages/project/ProjectDetailPage'));

// Loading fallback
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
  </div>
);

// React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // 30초
    },
  },
});

function App() {
  const theme = useUIStore((state) => state.theme);

  useEffect(() => {
    // 테마 적용
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* 랜딩 페이지 (레이아웃 없음) */}
              <Route path="/" element={<Landing />} />

              {/* 레이아웃이 있는 페이지들 */}
              <Route element={<Layout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/guide" element={<Guide />} />
                <Route path="/docs" element={<Docs />} />

                {/* BlueprintFlow 페이지 */}
                <Route path="/blueprintflow/builder" element={<BlueprintFlowBuilder />} />
                <Route path="/blueprintflow/list" element={<BlueprintFlowList />} />
                <Route path="/blueprintflow/templates" element={<BlueprintFlowTemplates />} />

                {/* 모니터링 페이지 - Dashboard로 통합됨 */}

                {/* 관리 페이지 */}
                <Route path="/admin" element={<Admin />} />
                <Route path="/admin/api/:apiId" element={<APIDetail />} />

                {/* P&ID 오버레이 페이지 */}
                <Route path="/pid-overlay" element={<PIDOverlayPage />} />

                {/* 프로젝트 관리 페이지 */}
                <Route path="/projects" element={<ProjectList />} />
                <Route path="/projects/:projectId" element={<ProjectDetail />} />
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
