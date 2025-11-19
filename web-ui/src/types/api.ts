// API 타입 정의

export interface HealthCheckResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

export interface AnalysisOptions {
  ocr: boolean;
  segmentation: boolean;
  tolerance: boolean;
  visualize: boolean;
}

export interface AnalysisRequest {
  file: File;
  options: AnalysisOptions;
}

export interface Dimension {
  type: string;
  value: number;
  unit: string;
  tolerance: string | number | null;
  // New bbox format (v1 & v2)
  bbox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  // Legacy location format (deprecated)
  location?: {
    x: number;
    y: number;
  };
}

export interface GDT {
  type: string;
  value: number;
  datum: string | null;
  // New bbox format (v1 & v2)
  bbox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  // Legacy location format (deprecated)
  location?: {
    x: number;
    y: number;
  };
}

export interface TextInfo {
  drawing_number?: string;
  revision?: string;
  title?: string;
  material?: string;
  notes?: string[];
  total_blocks?: number;
  tables?: any[]; // v2 feature: table OCR results
}

export interface OCRResult {
  dimensions: Dimension[];
  gdt: GDT[];
  text: TextInfo;
  visualization_url?: string;
  visualization?: string; // v2 feature: filename of visualization image
}

export interface SegmentationResult {
  num_components: number;
  classifications: {
    contour: number;
    text: number;
    dimension: number;
  };
  graph: {
    nodes: number;
    edges: number;
    avg_degree: number;
  };
  vectorization: {
    num_bezier_curves: number;
    total_length: number;
  };
  visualization_url?: string;
}

export interface ToleranceResult {
  predicted_tolerances: {
    flatness: number;
    cylindricity: number;
    position: number;
    perpendicularity?: number;
  };
  manufacturability: {
    score: number;
    difficulty: 'Easy' | 'Medium' | 'Hard';
    recommendations: string[];
  };
  assemblability: {
    score: number;
    clearance: number;
    interference_risk: 'Low' | 'Medium' | 'High';
  };
  process_parameters?: {
    correlation_length: number;
    systematic_deviation: number;
    random_deviation_std: number;
  };
}

export interface AnalysisResult {
  status: 'success' | 'error';
  data: {
    job_id?: string;
    yolo_results?: {
      status: string;
      file_id: string;
      detections: any[];
      total_detections: number;
      processing_time: number;
      model_used: string;
      image_size: {
        width: number;
        height: number;
      };
      visualized_image?: string; // Base64 encoded visualization
    };
    segmentation?: {
      status: string;
      data: SegmentationResult;
      processing_time: number;
      file_id: string;
    };
    ocr?: {
      status: string;
      data: OCRResult;
      processing_time: number;
      file_id: string;
    };
    tolerance?: {
      status: string;
      data: ToleranceResult;
      processing_time: number;
    };
    yolo_crop_ocr_results?: {
      dimensions: any[];
      total_texts: number;
      crop_count: number;
      successful_crops: number;
      processing_time: number;
    };
    ensemble?: {
      dimensions: any[];
      yolo_detections_count: number;
      ocr_dimensions_count: number;
      yolo_crop_ocr_count?: number;
      strategy: string;
    };
  };
  processing_time: number;
  file_id: string;
  download_urls?: {
    yolo_visualization?: string;
    result_json?: string;
    original?: string;
  };
}

export interface QuoteRequest {
  file: File;
  materialCost: number;
  machiningRate: number;
  tolerancePremium: number;
}

export interface QuoteResult {
  status: 'success' | 'error';
  data: {
    quote: {
      breakdown: {
        material_cost: number;
        machining_cost: number;
        tolerance_premium: number;
        total: number;
      };
      lead_time_days: number;
      confidence: number;
    };
    ocr?: OCRResult;
    segmentation?: SegmentationResult;
    tolerance?: ToleranceResult;
  };
  processing_time: number;
}

export interface APIError {
  message: string;
  status: number;
  code?: string;
  detail?: string;
  details?: any;
  url?: string;
}

export interface RequestTrace {
  id: string;
  timestamp: Date;
  endpoint: string;
  method: string;
  status: number;
  duration: number;
  request: any;
  response: any;
  error?: APIError;
  timeline?: {
    upload?: number;
    edocr2?: number;
    edgnet?: number;
    skinmodel?: number;
    response?: number;
  };
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'error';
  latency: number;
  lastCheck: Date;
  errorCount?: number;
  swaggerUrl?: string;
}
