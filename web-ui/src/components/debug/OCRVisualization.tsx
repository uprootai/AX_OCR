// Barrel re-export — implementation moved to ocr-visualization/
export type { SVGOverlayData, OCRVisualizationProps, BoundingBox } from './ocr-visualization/types';
export { OCR_LAYER_CONFIG } from './ocr-visualization/types';
export { parseLocation } from './ocr-visualization/utils';
export {
  LayerControls,
  Legend,
  SVGOverlayView,
  CanvasView,
  DetectionList,
} from './ocr-visualization/OCRVisualizationPanels';
export { default } from './ocr-visualization/OCRVisualizationMain';
