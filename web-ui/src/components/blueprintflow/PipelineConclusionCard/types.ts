// Types for node outputs used in PipelineConclusionCard

export interface Detection {
  class_name?: string;
  class?: string;
  label?: string;
  confidence?: number;
  bbox?: number[];
}

export interface Dimension {
  type?: string;
  text?: string;
  value?: string;
  raw_text?: string;
  unit?: string;
}

export interface GDTItem {
  symbol?: string;
  value?: string;
  datum?: string;
  tolerance?: string;
}

export interface PIDSymbol {
  class_name?: string;
  symbol_type?: string;
  confidence?: number;
}

export interface NodeOutput {
  // YOLO outputs
  detections?: Detection[];
  predictions?: Detection[];
  objects?: Detection[];

  // OCR outputs
  dimensions?: Dimension[];
  gdt?: GDTItem[];
  ocr_results?: Array<{ text: string; confidence?: number }>;
  text?: string | { text?: string; total_blocks?: number };
  texts?: string[];

  // P&ID outputs
  symbols?: PIDSymbol[];
  lines?: Array<{ line_id?: string; type?: string }>;
  connections?: Array<{ from?: string; to?: string }>;
  bom?: Array<{ item?: string; quantity?: number }>;
  violations?: Array<{ rule?: string; message?: string }>;

  // General
  [key: string]: unknown;
}

export interface NodeStatus {
  node_id: string;
  node_type?: string;
  status: string;
  output?: NodeOutput;
}

export interface ExecutionResult {
  status: string;
  execution_time_ms?: number;
  node_statuses?: NodeStatus[];
  final_output?: Record<string, NodeOutput>;
}

export interface PipelineConclusionCardProps {
  executionResult: ExecutionResult;
  nodes: Array<{ id: string; type?: string; data?: { label?: string } }>;
}

export interface ConclusionData {
  detectedObjects: Array<{ name: string; confidence: number; source: string }>;
  dimensions: Array<{ type: string; value: string; source: string }>;
  gdtSymbols: Array<{ symbol: string; value: string; datum: string }>;
  textBlocks: string[];
  pidSymbols: Array<{ name: string; confidence: number }>;
  pidConnections: number;
  pidViolations: Array<{ rule: string; message: string }>;
  bomItems: Array<{ item: string; quantity: number }>;
  totalDetections: number;
  totalDimensions: number;
  totalGDT: number;
  totalTexts: number;
}
