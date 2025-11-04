import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  TestTube,
  Activity,
  Settings,
  FileText,
  BookOpen,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Guide', href: '/guide', icon: BookOpen },
  { name: 'API Tests', href: '/test', icon: TestTube },
  { name: 'Analyze', href: '/analyze', icon: FileText },
  { name: 'Monitor', href: '/monitor', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 border-r bg-card p-4">
      <nav className="space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname.startsWith(item.href);

          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-accent'
              }`}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="mt-8 p-4 bg-accent/50 rounded-lg">
        <h3 className="font-semibold text-sm mb-2">Quick Test</h3>
        <div className="space-y-1 text-xs">
          <Link
            to="/test/yolo"
            className="flex items-center gap-1 hover:underline text-muted-foreground"
          >
            <span>• YOLOv11</span>
            <span className="px-1 py-0.5 text-[10px] font-semibold bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
              ⭐ 권장
            </span>
          </Link>
          <Link
            to="/test/edocr2"
            className="flex items-center gap-1 hover:underline text-muted-foreground"
          >
            <span>• eDOCr v1/v2</span>
            <span className="px-1 py-0.5 text-[10px] font-semibold bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded">
              GPU
            </span>
          </Link>
          <Link
            to="/test/edgnet"
            className="block hover:underline text-muted-foreground"
          >
            • EDGNet
          </Link>
          <Link
            to="/test/skinmodel"
            className="block hover:underline text-muted-foreground"
          >
            • Skin Model
          </Link>
          <Link
            to="/test/gateway"
            className="block hover:underline text-muted-foreground"
          >
            • Gateway
          </Link>
        </div>
      </div>
    </aside>
  );
}
