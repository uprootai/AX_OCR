import { Link } from 'react-router-dom';
import { Moon, Sun, Menu } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';

export default function Header() {
  const { theme, toggleTheme, toggleSidebar } = useUIStore();

  return (
    <header className="border-b bg-card">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-accent rounded-md"
          >
            <Menu className="h-5 w-5" />
          </button>
          <Link to="/dashboard" className="text-xl font-bold">
            AX 도면 분석 시스템
          </Link>
        </div>

        <nav className="flex items-center gap-6">
          <Link
            to="/dashboard"
            className="text-sm font-medium hover:text-primary"
          >
            Dashboard
          </Link>
          <Link
            to="/test"
            className="text-sm font-medium hover:text-primary"
          >
            Test
          </Link>
          <Link
            to="/analyze"
            className="text-sm font-medium hover:text-primary"
          >
            Analyze
          </Link>
          <Link
            to="/monitor"
            className="text-sm font-medium hover:text-primary"
          >
            Monitor
          </Link>

          <button
            onClick={toggleTheme}
            className="p-2 hover:bg-accent rounded-md"
          >
            {theme === 'light' ? (
              <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
          </button>
        </nav>
      </div>
    </header>
  );
}
