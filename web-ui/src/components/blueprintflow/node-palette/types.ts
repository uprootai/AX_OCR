/**
 * Node Palette Types
 * 노드 팔레트 관련 타입 정의
 */

export type NodeCategory =
  | 'input'
  | 'bom'
  | 'detection'
  | 'ocr'
  | 'segmentation'
  | 'preprocessing'
  | 'analysis'
  | 'knowledge'
  | 'ai'
  | 'control';

export interface NodeConfig {
  type: string;
  label: string;
  description: string;
  icon: React.ElementType | string; // 아이콘은 컴포넌트 또는 이모지
  color: string;
  category: NodeCategory;
}

export interface NodePaletteProps {
  onNodeDragStart: (event: React.DragEvent, nodeType: string, label: string) => void;
  uploadedImage?: string | null;
  uploadedFileName?: string | null;
}

export interface RecommendedInput {
  from: string;
  field: string;
  reason: string;
}

export interface NodeItemProps {
  node: NodeConfig;
  isActive: boolean;
  onDragStart: (e: React.DragEvent, nodeType: string, label: string) => void;
  hasRecommendedInputs?: boolean;
  recommendedInputs?: RecommendedInput[];
  isImageInputNode?: boolean;
  uploadedImage?: string | null;
  uploadedFileName?: string | null;
  onImageClick?: () => void;
  tooltipColorScheme?: 'green' | 'purple' | 'red' | 'cyan';
}

export interface NodeCategoryProps {
  title: string;
  emoji: string;
  nodes: NodeConfig[];
  isNodeActive: (nodeType: string) => boolean;
  onNodeDragStart: (e: React.DragEvent, nodeType: string, label: string) => void;
  tooltipColorScheme?: 'green' | 'purple' | 'red' | 'cyan';
  uploadedImage?: string | null;
  uploadedFileName?: string | null;
  onImageClick?: () => void;
}
