import { useState, useEffect } from 'react';

export interface HyperParameters {
  // YOLO 하이퍼파라미터
  yolo_conf_threshold: number;
  yolo_iou_threshold: number;
  yolo_imgsz: number;
  yolo_visualize: boolean;

  // eDOCr2 하이퍼파라미터
  edocr_extract_dimensions: boolean;
  edocr_extract_gdt: boolean;
  edocr_extract_text: boolean;
  edocr_extract_tables: boolean;
  edocr_visualize: boolean;
  edocr_language: string;
  edocr_cluster_threshold: number;

  // EDGNet 하이퍼파라미터
  edgnet_num_classes: number;
  edgnet_visualize: boolean;
  edgnet_save_graph: boolean;

  // PaddleOCR 하이퍼파라미터
  paddle_det_db_thresh: number;
  paddle_det_db_box_thresh: number;
  paddle_min_confidence: number;
  paddle_use_angle_cls: boolean;

  // Skin Model 하이퍼파라미터
  skin_material: string;
  skin_manufacturing_process: string;
  skin_correlation_length: number;
}

export const defaultHyperParams: HyperParameters = {
  // YOLO
  yolo_conf_threshold: 0.25,
  yolo_iou_threshold: 0.7,
  yolo_imgsz: 1280,
  yolo_visualize: true,

  // eDOCr2
  edocr_extract_dimensions: true,
  edocr_extract_gdt: true,
  edocr_extract_text: true,
  edocr_extract_tables: true,
  edocr_visualize: false,
  edocr_language: 'eng',
  edocr_cluster_threshold: 20,

  // EDGNet
  edgnet_num_classes: 3,
  edgnet_visualize: true,
  edgnet_save_graph: false,

  // PaddleOCR
  paddle_det_db_thresh: 0.3,
  paddle_det_db_box_thresh: 0.5,
  paddle_min_confidence: 0.5,
  paddle_use_angle_cls: true,

  // Skin Model
  skin_material: 'steel',
  skin_manufacturing_process: 'machining',
  skin_correlation_length: 10.0,
};

export function useHyperParameters() {
  const [hyperParams, setHyperParams] = useState<HyperParameters>(defaultHyperParams);

  useEffect(() => {
    const savedHyperParams = localStorage.getItem('hyperParameters');
    if (savedHyperParams) {
      try {
        setHyperParams(JSON.parse(savedHyperParams));
      } catch (e) {
        console.error('Failed to load saved hyperparameters:', e);
      }
    }
  }, []);

  return hyperParams;
}

export function getHyperParameters(): HyperParameters {
  const savedHyperParams = localStorage.getItem('hyperParameters');
  if (savedHyperParams) {
    try {
      return JSON.parse(savedHyperParams);
    } catch (e) {
      console.error('Failed to load saved hyperparameters:', e);
    }
  }
  return defaultHyperParams;
}
