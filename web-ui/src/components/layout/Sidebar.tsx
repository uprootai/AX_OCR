import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Home,
  TestTube,
  Activity,
  Settings,
  FileText,
  BookOpen,
  Book,
  Shield,
  Workflow,
} from 'lucide-react';

const navigationItems = [
  { key: 'dashboard', href: '/dashboard', icon: Home },
  { key: 'guide', href: '/guide', icon: BookOpen },
  { key: 'docs', href: '/docs', icon: Book },
  { key: 'test', href: '/test', icon: TestTube },
  { key: 'analyze', href: '/analyze', icon: FileText },
  { key: 'monitor', href: '/monitor', icon: Activity },
  { key: 'admin', href: '/admin', icon: Shield },
  { key: 'settings', href: '/settings', icon: Settings },
];

const blueprintFlowItems = [
  { key: 'blueprintflowBuilder', href: '/blueprintflow/builder', beta: true },
  { key: 'blueprintflowList', href: '/blueprintflow/list', beta: true },
  { key: 'blueprintflowTemplates', href: '/blueprintflow/templates', beta: true },
];

export default function Sidebar() {
  const location = useLocation();
  const { t } = useTranslation();

  return (
    <aside className="w-64 border-r bg-card p-4">
      <nav className="space-y-2">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname.startsWith(item.href);

          return (
            <Link
              key={item.key}
              to={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-accent'
              }`}
            >
              <Icon className="h-5 w-5" />
              {t(`sidebar.${item.key}`)}
            </Link>
          );
        })}
      </nav>

      {/* BlueprintFlow Section */}
      <div className="mt-6 p-4 bg-gradient-to-br from-cyan-50 to-blue-50 dark:from-cyan-900/30 dark:to-blue-900/30 rounded-lg border-2 border-cyan-200 dark:border-cyan-800">
        <div className="flex items-center gap-2 mb-3">
          <Workflow className="h-5 w-5 text-cyan-600 dark:text-cyan-400" />
          <h3 className="font-semibold text-sm text-cyan-900 dark:text-cyan-100">
            BlueprintFlow
          </h3>
          <span className="px-1.5 py-0.5 text-[10px] font-bold bg-cyan-600 text-white rounded">
            BETA
          </span>
        </div>
        <p className="text-xs text-cyan-700 dark:text-cyan-300 mb-3">
          {t('blueprintflow.title')}
        </p>
        <div className="space-y-1.5 text-xs">
          {blueprintFlowItems.map((item) => {
            const isActive = location.pathname.startsWith(item.href);
            return (
              <Link
                key={item.key}
                to={item.href}
                className={`flex items-center gap-1.5 px-2 py-1.5 rounded hover:bg-cyan-100 dark:hover:bg-cyan-900/50 transition-colors ${
                  isActive
                    ? 'bg-cyan-100 dark:bg-cyan-900/50 text-cyan-900 dark:text-cyan-100 font-medium'
                    : 'text-cyan-700 dark:text-cyan-300'
                }`}
              >
                <span>•</span>
                <span>{t(`sidebar.${item.key}`)}</span>
              </Link>
            );
          })}
        </div>
      </div>

      <div className="mt-4 p-4 bg-accent/50 rounded-lg">
        <h3 className="font-semibold text-sm mb-2">{t('sidebar.quickTest')}</h3>
        <div className="space-y-1 text-xs">
          <Link
            to="/test/gateway"
            className="flex items-center gap-1 hover:underline text-muted-foreground"
          >
            <span>• Gateway</span>
            <span className="px-1 py-0.5 text-[10px] font-semibold bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
              {t('sidebar.recommended')}
            </span>
          </Link>
          <Link
            to="/test/yolo"
            className="flex items-center gap-1 hover:underline text-muted-foreground"
          >
            <span>• YOLOv11</span>
            <span className="px-1 py-0.5 text-[10px] font-semibold bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded">
              GPU
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
            className="flex items-center gap-1 hover:underline text-muted-foreground"
          >
            <span>• EDGNet</span>
            <span className="px-1 py-0.5 text-[10px] font-semibold bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded">
              GPU
            </span>
          </Link>
          <Link
            to="/test/skinmodel"
            className="block hover:underline text-muted-foreground"
          >
            • Skin Model
          </Link>
          <Link
            to="/test/vl"
            className="flex items-center gap-1 hover:underline text-muted-foreground"
          >
            <span>• VL Model</span>
            <span className="px-1 py-0.5 text-[10px] font-semibold bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded">
              LLM
            </span>
          </Link>
        </div>
      </div>
    </aside>
  );
}
