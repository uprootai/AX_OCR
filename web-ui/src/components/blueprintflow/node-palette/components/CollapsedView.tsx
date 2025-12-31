/**
 * CollapsedView Component
 * 접힌 상태의 노드 팔레트 뷰
 */

import {
  Image,
  Target,
  FileText,
  Network,
  Ruler,
  Eye,
  GitBranch,
} from 'lucide-react';

interface CategoryIcon {
  icon: React.ElementType;
  color: string;
  bgColor: string;
  title: string;
}

const categoryIcons: CategoryIcon[] = [
  {
    icon: Image,
    color: 'text-orange-500',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    title: 'Input',
  },
  {
    icon: Target,
    color: 'text-green-500',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    title: 'Detection',
  },
  {
    icon: FileText,
    color: 'text-blue-500',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    title: 'OCR',
  },
  {
    icon: Network,
    color: 'text-purple-500',
    bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    title: 'Segmentation',
  },
  {
    icon: Ruler,
    color: 'text-amber-500',
    bgColor: 'bg-amber-100 dark:bg-amber-900/30',
    title: 'Analysis',
  },
  {
    icon: Eye,
    color: 'text-pink-500',
    bgColor: 'bg-pink-100 dark:bg-pink-900/30',
    title: 'AI',
  },
  {
    icon: GitBranch,
    color: 'text-red-500',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    title: 'Control',
  },
];

/**
 * CollapsedView 컴포넌트
 * 팔레트가 접혔을 때 카테고리 아이콘만 표시
 */
export function CollapsedView() {
  return (
    <div className="p-2 pt-10 space-y-2">
      {categoryIcons.map(({ icon: Icon, color, bgColor, title }) => (
        <div
          key={title}
          className={`w-8 h-8 flex items-center justify-center rounded ${bgColor}`}
          title={title}
        >
          <Icon className={`w-4 h-4 ${color}`} />
        </div>
      ))}
    </div>
  );
}
