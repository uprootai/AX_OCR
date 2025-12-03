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
const TestHub = lazy(() => import('./pages/test/TestHub'));
const TestEdocr2 = lazy(() => import('./pages/test/TestEdocr2'));
const TestEdgnet = lazy(() => import('./pages/test/TestEdgnet'));
const TestSkinmodel = lazy(() => import('./pages/test/TestSkinmodel'));
const TestGateway = lazy(() => import('./pages/test/TestGateway'));
const TestYolo = lazy(() => import('./pages/test/TestYolo'));
const TestVL = lazy(() => import('./pages/test/TestVL'));
const Analyze = lazy(() => import('./pages/analyze/Analyze'));
const Monitor = lazy(() => import('./pages/monitor/Monitor'));
const Admin = lazy(() => import('./pages/admin/Admin'));
const Settings = lazy(() => import('./pages/settings/Settings'));

// BlueprintFlow Pages (lazy - heavy components)
const BlueprintFlowBuilder = lazy(() => import('./pages/blueprintflow/BlueprintFlowBuilder'));
const BlueprintFlowList = lazy(() => import('./pages/blueprintflow/BlueprintFlowList'));
const BlueprintFlowTemplates = lazy(() => import('./pages/blueprintflow/BlueprintFlowTemplates'));

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

                {/* 테스트 페이지 */}
                <Route path="/test" element={<TestHub />} />
                <Route path="/test/yolo" element={<TestYolo />} />
                <Route path="/test/edocr2" element={<TestEdocr2 />} />
                <Route path="/test/edgnet" element={<TestEdgnet />} />
                <Route path="/test/skinmodel" element={<TestSkinmodel />} />
                <Route path="/test/gateway" element={<TestGateway />} />
                <Route path="/test/vl" element={<TestVL />} />

                {/* 분석 페이지 */}
                <Route path="/analyze" element={<Analyze />} />

                {/* BlueprintFlow 페이지 */}
                <Route path="/blueprintflow/builder" element={<BlueprintFlowBuilder />} />
                <Route path="/blueprintflow/list" element={<BlueprintFlowList />} />
                <Route path="/blueprintflow/templates" element={<BlueprintFlowTemplates />} />

                {/* 모니터링 페이지 */}
                <Route path="/monitor" element={<Monitor />} />

                {/* 관리 페이지 */}
                <Route path="/admin" element={<Admin />} />

                {/* 설정 페이지 */}
                <Route path="/settings" element={<Settings />} />
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
