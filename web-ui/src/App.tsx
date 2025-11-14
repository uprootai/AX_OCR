import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useUIStore } from './store/uiStore';
import { useEffect } from 'react';

// Error Boundary
import ErrorBoundary from './components/ErrorBoundary';

// Layout
import Layout from './components/layout/Layout';

// Pages
import Landing from './pages/Landing';
import Dashboard from './pages/dashboard/Dashboard';
import Guide from './pages/dashboard/Guide';
import Docs from './pages/docs/Docs';
import TestHub from './pages/test/TestHub';
import TestEdocr2 from './pages/test/TestEdocr2';
import TestEdgnet from './pages/test/TestEdgnet';
import TestSkinmodel from './pages/test/TestSkinmodel';
import TestGateway from './pages/test/TestGateway';
import TestYolo from './pages/test/TestYolo';
import Analyze from './pages/analyze/Analyze';
import Monitor from './pages/monitor/Monitor';
import Admin from './pages/admin/Admin';
import Settings from './pages/settings/Settings';

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

              {/* 분석 페이지 */}
              <Route path="/analyze" element={<Analyze />} />

              {/* 모니터링 페이지 */}
              <Route path="/monitor" element={<Monitor />} />

              {/* 관리 페이지 */}
              <Route path="/admin" element={<Admin />} />

              {/* 설정 페이지 */}
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
