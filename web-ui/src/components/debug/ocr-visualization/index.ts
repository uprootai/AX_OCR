// Barrel re-export — preserves all existing import paths
export type { SVGOverlayData, OCRVisualizationProps, BoundingBox } from './types';
export { OCR_LAYER_CONFIG } from './types';
export { parseLocation } from './utils';
export {
  LayerControls,
  Legend,
  SVGOverlayView,
  CanvasView,
  DetectionList,
} from './OCRVisualizationPanels';
export { default } from './OCRVisualizationMain';
