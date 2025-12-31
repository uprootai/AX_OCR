/**
 * Default hyperparameter values for each API service
 * These values are used when no saved configuration exists
 */

import type { HyperParams } from '../hooks/useAPIDetail';

export const DEFAULT_HYPERPARAMS: Record<string, HyperParams> = {
  yolo: {
    conf_threshold: 0.25,
    iou_threshold: 0.7,
    imgsz: '1280',
    model_type: 'engineering',
    use_sahi: false,
    slice_size: '512',
    visualize: true,
  },
  edocr2: {
    extract_dimensions: true,
    extract_gdt: true,
    extract_text: true,
    extract_tables: true,
    language: 'eng',
    cluster_threshold: 20,
  },
  edgnet: {
    num_classes: 3,
    visualize: true,
    save_graph: false,
  },
  line_detector: {
    method: 'combined',
    min_length: 0,
    max_lines: 0,
    merge_threshold: 10,
    classify_types: true,
    classify_colors: true,
    classify_styles: true,
    detect_intersections: true,
    detect_regions: false,
    region_line_styles: 'dashed,dash_dot',
    min_region_area: 5000,
    visualize: true,
    visualize_regions: true,
  },
  paddleocr: {
    det_db_thresh: 0.3,
    det_db_box_thresh: 0.5,
    min_confidence: 0.5,
    use_angle_cls: true,
  },
  tesseract: {
    language: 'kor+eng',
    psm: '3',
    visualize: false,
  },
  trocr: {
    model_size: 'base',
    max_length: 64,
    visualize: false,
  },
  ocr_ensemble: {
    engines: 'all',
    voting: 'weighted',
    visualize: false,
  },
  surya_ocr: {
    language: 'ko',
    layout_analysis: true,
    visualize: false,
  },
  doctr: {
    det_model: 'db_resnet50',
    reco_model: 'crnn_vgg16_bn',
    visualize: false,
  },
  easyocr: {
    language: 'ko',
    min_confidence: 0.5,
    paragraph: true,
  },
  esrgan: {
    scale: '4',
    tile_size: 256,
  },
  skinmodel: {
    material: 'steel',
    manufacturing_process: 'machining',
    correlation_length: 10.0,
  },
  pid_analyzer: {
    connection_distance: 30,
    generate_bom: true,
    visualize: true,
  },
  design_checker: {
    ruleset: 'standard',
    include_warnings: true,
  },
  knowledge: {
    search_mode: 'hybrid',
    search_depth: 2,
    top_k: 10,
  },
  vl: {
    model: 'qwen-vl',
    max_tokens: 1024,
    temperature: 0.7,
  },
  blueprint_ai_bom: {
    symbol_detection: true,
    dimension_ocr: true,
    gdt_parsing: true,
    human_in_the_loop: true,
    confidence_threshold: 0.8,
  },
};
