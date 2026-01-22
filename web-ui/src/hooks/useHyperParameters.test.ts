/**
 * Tests for useHyperParameters hook
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useHyperParameters, getHyperParameters, defaultHyperParams, type HyperParameters } from './useHyperParameters';

describe('useHyperParameters', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should return default hyperparameters when localStorage is empty', () => {
    const { result } = renderHook(() => useHyperParameters());
    expect(result.current).toEqual(defaultHyperParams);
  });

  it('should load saved hyperparameters from localStorage', () => {
    const savedParams: HyperParameters = {
      ...defaultHyperParams,
      yolo_conf_threshold: 0.5,
      yolo_imgsz: 1024,
    };
    localStorage.setItem('hyperParameters', JSON.stringify(savedParams));

    const { result } = renderHook(() => useHyperParameters());
    expect(result.current.yolo_conf_threshold).toBe(0.5);
    expect(result.current.yolo_imgsz).toBe(1024);
  });

  it('should handle invalid JSON in localStorage gracefully', () => {
    localStorage.setItem('hyperParameters', 'invalid-json');
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useHyperParameters());

    expect(result.current).toEqual(defaultHyperParams);
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});

describe('getHyperParameters', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should return default parameters when localStorage is empty', () => {
    const params = getHyperParameters();
    expect(params).toEqual(defaultHyperParams);
  });

  it('should return saved parameters from localStorage', () => {
    const savedParams: HyperParameters = {
      ...defaultHyperParams,
      edocr_language: 'kor',
      edocr_extract_tables: false,
    };
    localStorage.setItem('hyperParameters', JSON.stringify(savedParams));

    const params = getHyperParameters();
    expect(params.edocr_language).toBe('kor');
    expect(params.edocr_extract_tables).toBe(false);
  });

  it('should handle invalid JSON and return defaults', () => {
    localStorage.setItem('hyperParameters', '{invalid}');
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const params = getHyperParameters();

    expect(params).toEqual(defaultHyperParams);
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});

describe('defaultHyperParams', () => {
  it('should have correct YOLO defaults', () => {
    expect(defaultHyperParams.yolo_conf_threshold).toBe(0.25);
    expect(defaultHyperParams.yolo_iou_threshold).toBe(0.7);
    expect(defaultHyperParams.yolo_imgsz).toBe(1280);
    expect(defaultHyperParams.yolo_visualize).toBe(true);
  });

  it('should have correct eDOCr2 defaults', () => {
    expect(defaultHyperParams.edocr_extract_dimensions).toBe(true);
    expect(defaultHyperParams.edocr_extract_gdt).toBe(true);
    expect(defaultHyperParams.edocr_extract_text).toBe(true);
    expect(defaultHyperParams.edocr_extract_tables).toBe(true);
    expect(defaultHyperParams.edocr_visualize).toBe(false);
    expect(defaultHyperParams.edocr_language).toBe('eng');
    expect(defaultHyperParams.edocr_cluster_threshold).toBe(20);
  });

  it('should have correct EDGNet defaults', () => {
    expect(defaultHyperParams.edgnet_num_classes).toBe(3);
    expect(defaultHyperParams.edgnet_visualize).toBe(true);
    expect(defaultHyperParams.edgnet_save_graph).toBe(false);
  });

  it('should have correct PaddleOCR defaults', () => {
    expect(defaultHyperParams.paddle_det_db_thresh).toBe(0.3);
    expect(defaultHyperParams.paddle_det_db_box_thresh).toBe(0.5);
    expect(defaultHyperParams.paddle_min_confidence).toBe(0.5);
    expect(defaultHyperParams.paddle_use_angle_cls).toBe(true);
  });

  it('should have correct Skin Model defaults', () => {
    expect(defaultHyperParams.skin_material).toBe('steel');
    expect(defaultHyperParams.skin_manufacturing_process).toBe('machining');
    expect(defaultHyperParams.skin_correlation_length).toBe(10.0);
  });

  it('should have all expected keys', () => {
    const expectedKeys = [
      'yolo_conf_threshold', 'yolo_iou_threshold', 'yolo_imgsz', 'yolo_visualize',
      'edocr_extract_dimensions', 'edocr_extract_gdt', 'edocr_extract_text',
      'edocr_extract_tables', 'edocr_visualize', 'edocr_language', 'edocr_cluster_threshold',
      'edgnet_num_classes', 'edgnet_visualize', 'edgnet_save_graph',
      'paddle_det_db_thresh', 'paddle_det_db_box_thresh', 'paddle_min_confidence', 'paddle_use_angle_cls',
      'skin_material', 'skin_manufacturing_process', 'skin_correlation_length',
    ];

    expectedKeys.forEach(key => {
      expect(defaultHyperParams).toHaveProperty(key);
    });
  });
});
