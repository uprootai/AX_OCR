export * from './ApiNodes';
export * from './ControlNodes';
export * from './BaseNode';

// Node type mapping for ReactFlow
export const nodeTypes = {
  imageinput: 'imageinput',
  yolo: 'yolo',
  edocr2: 'edocr2',
  edgnet: 'edgnet',
  skinmodel: 'skinmodel',
  paddleocr: 'paddleocr',
  vl: 'vl',
  if: 'if',
  loop: 'loop',
  merge: 'merge',
} as const;

export type NodeType = typeof nodeTypes[keyof typeof nodeTypes];
