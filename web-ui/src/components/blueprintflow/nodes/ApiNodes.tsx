import { memo } from 'react';
import type { NodeProps } from 'reactflow';
import {
  Target,
  FileText,
  Network,
  Ruler,
  Eye,
  FileSearch,
  Image,
  Type,
} from 'lucide-react';
import { BaseNode } from './BaseNode';

// YOLO Node
export const YoloNode = memo((props: NodeProps) => (
  <BaseNode
    {...props}
    icon={Target}
    title="YOLO"
    color="#10b981"
    category="api"
  />
));
YoloNode.displayName = 'YoloNode';

// eDOCr2 Node
export const Edocr2Node = memo((props: NodeProps) => (
  <BaseNode
    {...props}
    icon={FileText}
    title="eDOCr2"
    color="#3b82f6"
    category="api"
  />
));
Edocr2Node.displayName = 'Edocr2Node';

// EDGNet Node
export const EdgnetNode = memo((props: NodeProps) => (
  <BaseNode
    {...props}
    icon={Network}
    title="EDGNet"
    color="#8b5cf6"
    category="api"
  />
));
EdgnetNode.displayName = 'EdgnetNode';

// SkinModel Node
export const SkinmodelNode = memo((props: NodeProps) => (
  <BaseNode
    {...props}
    icon={Ruler}
    title="SkinModel"
    color="#f59e0b"
    category="api"
  />
));
SkinmodelNode.displayName = 'SkinmodelNode';

// PaddleOCR Node
export const PaddleocrNode = memo((props: NodeProps) => (
  <BaseNode
    {...props}
    icon={FileSearch}
    title="PaddleOCR"
    color="#06b6d4"
    category="api"
  />
));
PaddleocrNode.displayName = 'PaddleocrNode';

// VL Node
export const VlNode = memo((props: NodeProps) => (
  <BaseNode
    {...props}
    icon={Eye}
    title="Vision-Language"
    color="#ec4899"
    category="api"
  />
));
VlNode.displayName = 'VlNode';

// ImageInput Node
export const ImageInputNode = memo((props: NodeProps) => (
  <BaseNode
    {...props}
    icon={Image}
    title="Image Input"
    color="#f97316"
    category="input"
  />
));
ImageInputNode.displayName = 'ImageInputNode';

// TextInput Node
export const TextInputNode = memo((props: NodeProps) => (
  <BaseNode
    {...props}
    icon={Type}
    title="Text Input"
    color="#8b5cf6"
    category="input"
  />
));
TextInputNode.displayName = 'TextInputNode';
