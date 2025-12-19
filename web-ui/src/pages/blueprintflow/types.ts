/**
 * BlueprintFlow Type Definitions
 * 워크플로우 빌더 관련 타입 정의
 */

// API response node status type (snake_case from backend)
export interface APINodeStatus {
  node_id: string;
  status: string;
  execution_time?: number;
  start_time?: string;
  end_time?: string;
  output?: Record<string, unknown>;
  error?: string;
}

// API result types for type-safe rendering
export interface Detection {
  class_name?: string;
  class?: string;
  confidence: number;
  bbox?: { x: number; y: number; width: number; height: number };
  class_id?: number;
}

export interface DimensionResult {
  type?: string;
  value?: number | string;
  text?: string;
  unit?: string;
  tolerance?: string | number;
}

export interface TextResult {
  text?: string;
  content?: string;
  confidence?: number;
}

export interface OCRBlock {
  text?: string;
  confidence?: number;
}

export interface SegmentResult {
  class?: string;
  type?: string;
  confidence?: number;
}

export interface ToleranceItem {
  dimension?: string;
  name?: string;
  value?: string | number;
}

// GDT type for OCR results
export interface GDTItem {
  type: string;
  value: number;
  datum: string | null;
  bbox?: { x: number; y: number; width: number; height: number };
}

// Flexible output type for pipeline results
export interface PipelineOutput {
  [key: string]: unknown;
  detections?: Detection[];
  dimensions?: DimensionResult[];
  text_results?: TextResult[];
  blocks?: OCRBlock[];
  segments?: SegmentResult[];
  tolerances?: ToleranceItem[];
  analysis?: Record<string, unknown>;
  result?: string;
  description?: string;
  image?: string;
  visualized_image?: string;
  gdt?: GDTItem[];
  text?: string | { total_blocks?: number };
  manufacturability?: { score: number; difficulty: string };
  predicted_tolerances?: Record<string, number>;
  // Segmentation specific
  num_components?: number;
  classifications?: { contour: number; text: number; dimension: number };
  graph?: { nodes: number; edges: number; avg_degree: number };
  vectorization?: { num_bezier_curves: number; total_length: number };
  // UI action for human-in-the-loop
  ui_action?: { url?: string; label?: string };
  session_id?: string;
  message?: string;
  mask?: unknown;
}

// Container warning modal state
export interface ContainerWarningModalState {
  isOpen: boolean;
  stoppedContainers: string[];
  isStarting: boolean;
}

// Execution group for parallel display
export interface ExecutionGroup {
  type: 'parallel' | 'sequential';
  nodes: APINodeStatus[];
  startTime?: string;
  endTime?: string;
}

// Workflow node with data
export interface WorkflowNodeData {
  label?: string;
  description?: string;
  parameters?: Record<string, unknown>;
  icon?: string;
  color?: string;
}
