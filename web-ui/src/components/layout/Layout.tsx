import { Outlet, useLocation } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import { useUIStore } from '../../store/uiStore';

// 풀스크린 레이아웃을 사용하는 경로 (Header/Sidebar 유지, 패딩만 제거)
const FULLSCREEN_PATHS = ['/blueprintflow/builder'];

export default function Layout() {
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);
  const location = useLocation();
  const isFullscreen = FULLSCREEN_PATHS.some(p => location.pathname.startsWith(p));

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      <Header />
      <div className="flex flex-1 min-h-0">
        {sidebarOpen && <Sidebar />}
        <main className={`flex-1 ${isFullscreen ? '' : 'p-6 overflow-y-auto'}`}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
