import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Sparkles, Download, GitBranch, Clock, Target, Star, Zap, Brain, Layers, Lightbulb, FlaskConical } from 'lucide-react';
import { useWorkflowStore } from '../../store/workflowStore';
import type { WorkflowDefinition } from '../../lib/api';

interface TemplateInfo {
  nameKey: string;
  descKey: string;
  useCaseKey: string;
  workflow: WorkflowDefinition;
  estimatedTime: string;
  accuracy: string;
  category: 'basic' | 'advanced' | 'pid' | 'ai' | 'benchmark';
  featured?: boolean;
}

export default function BlueprintFlowTemplates() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { loadWorkflow } = useWorkflowStore();

  const templates: TemplateInfo[] = [
    // ============ FEATURED TEMPLATES ============
    {
      nameKey: 'completeAnalysis',
      descKey: 'completeAnalysisDesc',
      useCaseKey: 'completeAnalysisUseCase',
      estimatedTime: '25-35s',
      accuracy: '97%',
      category: 'advanced',
      featured: true,
      workflow: {
        name: 'Complete Drawing Analysis',
        description: 'Full analysis pipeline with detection, OCR, tolerance analysis, and AI description',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Drawing Input', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'esrgan_1', type: 'esrgan', label: 'Image Enhancement', parameters: { scale: 2 }, position: { x: 300, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'Symbol Detection', parameters: { confidence: 0.35, imgsz: 1280 }, position: { x: 500, y: 100 } },
          { id: 'edgnet_1', type: 'edgnet', label: 'Segmentation', parameters: { threshold: 0.5 }, position: { x: 500, y: 300 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'Dimension OCR', parameters: {}, position: { x: 750, y: 300 } },
          { id: 'ocr_ensemble_1', type: 'ocr_ensemble', label: 'OCR Ensemble', parameters: {}, position: { x: 750, y: 100 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: 'Tolerance Analysis', parameters: {}, position: { x: 950, y: 300 } },
          { id: 'vl_1', type: 'vl', label: 'AI Description', parameters: { prompt: 'Describe this engineering drawing' }, position: { x: 1000, y: 150 } },
          { id: 'merge_1', type: 'merge', label: 'Final Results', parameters: {}, position: { x: 1200, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e2', source: 'esrgan_1', target: 'yolo_1' },
          { id: 'e3', source: 'esrgan_1', target: 'edgnet_1' },
          { id: 'e4', source: 'yolo_1', target: 'ocr_ensemble_1' },
          { id: 'e5', source: 'edgnet_1', target: 'edocr2_1' },
          { id: 'e6', source: 'edocr2_1', target: 'skinmodel_1' },
          { id: 'e7', source: 'ocr_ensemble_1', target: 'vl_1' },
          { id: 'e8', source: 'skinmodel_1', target: 'vl_1' },
          { id: 'e9', source: 'vl_1', target: 'merge_1' },
        ],
      },
    },
    {
      nameKey: 'pidAnalysis',
      descKey: 'pidAnalysisDesc',
      useCaseKey: 'pidAnalysisUseCase',
      estimatedTime: '20-30s',
      accuracy: '92%',
      category: 'pid',
      featured: true,
      workflow: {
        name: 'P&ID Analysis Pipeline',
        description: 'Complete P&ID analysis with symbol detection, line detection, connectivity analysis, and design validation',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'P&ID Image Input', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'yolopid_1', type: 'yolopid', label: 'YOLO-PID Symbol Detection', parameters: { confidence: 0.25, iou: 0.45, imgsz: 640 }, position: { x: 400, y: 100 } },
          { id: 'linedetector_1', type: 'linedetector', label: 'Line Detector', parameters: { method: 'lsd', merge_lines: true, classify_types: true }, position: { x: 400, y: 300 } },
          { id: 'pidanalyzer_1', type: 'pidanalyzer', label: 'P&ID Analyzer', parameters: { generate_bom: true, generate_valve_list: true, generate_equipment_list: true }, position: { x: 700, y: 200 } },
          { id: 'designchecker_1', type: 'designchecker', label: 'Design Checker', parameters: { severity_threshold: 'warning' }, position: { x: 1000, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolopid_1' },
          { id: 'e2', source: 'imageinput_1', target: 'linedetector_1' },
          { id: 'e3', source: 'yolopid_1', target: 'pidanalyzer_1' },
          { id: 'e4', source: 'linedetector_1', target: 'pidanalyzer_1' },
          { id: 'e5', source: 'pidanalyzer_1', target: 'designchecker_1' },
        ],
      },
    },

    // ============ BASIC TEMPLATES ============
    {
      nameKey: 'speedPipeline',
      descKey: 'speedPipelineDesc',
      useCaseKey: 'speedPipelineUseCase',
      estimatedTime: '3-5s',
      accuracy: '88%',
      category: 'basic',
      workflow: {
        name: 'Speed Pipeline',
        description: 'Fastest pipeline for quick analysis',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 100 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.5, imgsz: 640 }, position: { x: 350, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'Korean OCR', parameters: {}, position: { x: 600, y: 100 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'yolo_1', target: 'edocr2_1' },
        ],
      },
    },
    {
      nameKey: 'basicOCR',
      descKey: 'basicOCRDesc',
      useCaseKey: 'basicOCRUseCase',
      estimatedTime: '5-8s',
      accuracy: '90%',
      category: 'basic',
      workflow: {
        name: 'Basic OCR Pipeline',
        description: 'Simple OCR workflow with detection and tolerance',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 100 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.5 }, position: { x: 350, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'Korean OCR', parameters: {}, position: { x: 600, y: 100 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: 'Tolerance Analysis', parameters: {}, position: { x: 850, y: 100 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'yolo_1', target: 'edocr2_1' },
          { id: 'e3', source: 'edocr2_1', target: 'skinmodel_1' },
        ],
      },
    },

    // ============ ADVANCED TEMPLATES ============
    {
      nameKey: 'accuracyPipeline',
      descKey: 'accuracyPipelineDesc',
      useCaseKey: 'accuracyPipelineUseCase',
      estimatedTime: '10-15s',
      accuracy: '95%',
      category: 'advanced',
      workflow: {
        name: 'Accuracy Pipeline',
        description: 'High accuracy pipeline with dual OCR and segmentation',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 100 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.35, imgsz: 1280 }, position: { x: 300, y: 100 } },
          { id: 'edgnet_1', type: 'edgnet', label: 'Edge Segmentation', parameters: { threshold: 0.5 }, position: { x: 500, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'Korean OCR', parameters: {}, position: { x: 700, y: 50 } },
          { id: 'paddleocr_1', type: 'paddleocr', label: 'PaddleOCR', parameters: { lang: 'en' }, position: { x: 700, y: 150 } },
          { id: 'merge_1', type: 'merge', label: 'Merge Results', parameters: {}, position: { x: 900, y: 100 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'yolo_1', target: 'edgnet_1' },
          { id: 'e3', source: 'edgnet_1', target: 'edocr2_1' },
          { id: 'e4', source: 'edgnet_1', target: 'paddleocr_1' },
          { id: 'e5', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e6', source: 'paddleocr_1', target: 'merge_1' },
        ],
      },
    },
    {
      nameKey: 'ocrEnsemble',
      descKey: 'ocrEnsembleDesc',
      useCaseKey: 'ocrEnsembleUseCase',
      estimatedTime: '12-18s',
      accuracy: '96%',
      category: 'advanced',
      workflow: {
        name: 'OCR Ensemble Pipeline',
        description: 'Image enhancement with 4-engine OCR ensemble voting and tolerance analysis',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 150 } },
          { id: 'esrgan_1', type: 'esrgan', label: 'ESRGAN Upscale', parameters: { scale: 2 }, position: { x: 300, y: 150 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.3, imgsz: 1280 }, position: { x: 500, y: 150 } },
          { id: 'ocr_ensemble_1', type: 'ocr_ensemble', label: 'OCR Ensemble (4-way)', parameters: {}, position: { x: 750, y: 50 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'Dimension OCR', parameters: {}, position: { x: 750, y: 250 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: 'Tolerance Analysis', parameters: {}, position: { x: 1000, y: 250 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e2', source: 'esrgan_1', target: 'yolo_1' },
          { id: 'e3', source: 'yolo_1', target: 'ocr_ensemble_1' },
          { id: 'e4', source: 'yolo_1', target: 'edocr2_1' },
          { id: 'e5', source: 'edocr2_1', target: 'skinmodel_1' },
        ],
      },
    },
    {
      nameKey: 'multiOCRComparison',
      descKey: 'multiOCRComparisonDesc',
      useCaseKey: 'multiOCRComparisonUseCase',
      estimatedTime: '15-20s',
      accuracy: '94%',
      category: 'advanced',
      workflow: {
        name: 'Multi-OCR Comparison',
        description: 'Compare results from 5 different OCR engines',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.4 }, position: { x: 300, y: 200 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'eDOCr2', parameters: {}, position: { x: 550, y: 50 } },
          { id: 'paddleocr_1', type: 'paddleocr', label: 'PaddleOCR', parameters: {}, position: { x: 550, y: 130 } },
          { id: 'tesseract_1', type: 'tesseract', label: 'Tesseract', parameters: {}, position: { x: 550, y: 210 } },
          { id: 'trocr_1', type: 'trocr', label: 'TrOCR', parameters: {}, position: { x: 550, y: 290 } },
          { id: 'merge_1', type: 'merge', label: 'Compare & Merge', parameters: {}, position: { x: 800, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'yolo_1', target: 'edocr2_1' },
          { id: 'e3', source: 'yolo_1', target: 'paddleocr_1' },
          { id: 'e4', source: 'yolo_1', target: 'tesseract_1' },
          { id: 'e5', source: 'yolo_1', target: 'trocr_1' },
          { id: 'e6', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e7', source: 'paddleocr_1', target: 'merge_1' },
          { id: 'e8', source: 'tesseract_1', target: 'merge_1' },
          { id: 'e9', source: 'trocr_1', target: 'merge_1' },
        ],
      },
    },

    // Full OCR Benchmark - All 8 OCR engines
    {
      nameKey: 'fullOCRBenchmark',
      descKey: 'fullOCRBenchmarkDesc',
      useCaseKey: 'fullOCRBenchmarkUseCase',
      estimatedTime: '25-35s',
      accuracy: 'Comparison',
      category: 'benchmark',
      workflow: {
        name: 'Full OCR Benchmark',
        description: 'Compare all 8 OCR engines side-by-side for comprehensive evaluation',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 50, y: 300 } },
          // Row 1: Detection-based OCRs
          { id: 'edocr2_1', type: 'edocr2', label: 'eDOCr2 (Drawing)', parameters: {}, position: { x: 350, y: 50 } },
          { id: 'paddleocr_1', type: 'paddleocr', label: 'PaddleOCR (Fast)', parameters: { lang: 'en' }, position: { x: 350, y: 130 } },
          { id: 'tesseract_1', type: 'tesseract', label: 'Tesseract (General)', parameters: { lang: 'eng' }, position: { x: 350, y: 210 } },
          { id: 'trocr_1', type: 'trocr', label: 'TrOCR (Handwriting)', parameters: {}, position: { x: 350, y: 290 } },
          // Row 2: Advanced OCRs
          { id: 'suryaocr_1', type: 'suryaocr', label: 'Surya (Layout)', parameters: {}, position: { x: 350, y: 370 } },
          { id: 'doctr_1', type: 'doctr', label: 'DocTR (Document)', parameters: {}, position: { x: 350, y: 450 } },
          { id: 'easyocr_1', type: 'easyocr', label: 'EasyOCR (Multilingual)', parameters: { languages: ['en'] }, position: { x: 350, y: 530 } },
          { id: 'ocr_ensemble_1', type: 'ocr_ensemble', label: 'Ensemble (Voting)', parameters: {}, position: { x: 350, y: 610 } },
          // Merge all results
          { id: 'merge_1', type: 'merge', label: 'All OCR Results', parameters: {}, position: { x: 650, y: 300 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'edocr2_1' },
          { id: 'e2', source: 'imageinput_1', target: 'paddleocr_1' },
          { id: 'e3', source: 'imageinput_1', target: 'tesseract_1' },
          { id: 'e4', source: 'imageinput_1', target: 'trocr_1' },
          { id: 'e5', source: 'imageinput_1', target: 'suryaocr_1' },
          { id: 'e6', source: 'imageinput_1', target: 'doctr_1' },
          { id: 'e7', source: 'imageinput_1', target: 'easyocr_1' },
          { id: 'e8', source: 'imageinput_1', target: 'ocr_ensemble_1' },
          { id: 'e9', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e10', source: 'paddleocr_1', target: 'merge_1' },
          { id: 'e11', source: 'tesseract_1', target: 'merge_1' },
          { id: 'e12', source: 'trocr_1', target: 'merge_1' },
          { id: 'e13', source: 'suryaocr_1', target: 'merge_1' },
          { id: 'e14', source: 'doctr_1', target: 'merge_1' },
          { id: 'e15', source: 'easyocr_1', target: 'merge_1' },
          { id: 'e16', source: 'ocr_ensemble_1', target: 'merge_1' },
        ],
      },
    },

    // Detection Benchmark - YOLO vs YOLO-PID
    {
      nameKey: 'detectionBenchmark',
      descKey: 'detectionBenchmarkDesc',
      useCaseKey: 'detectionBenchmarkUseCase',
      estimatedTime: '10-15s',
      accuracy: 'Comparison',
      category: 'benchmark',
      workflow: {
        name: 'Detection Benchmark',
        description: 'Compare YOLO (general symbol) vs YOLO-PID (P&ID specialized) detection',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 50, y: 200 } },
          // YOLO variants
          { id: 'yolo_1', type: 'yolo', label: 'YOLO (General)', parameters: { confidence: 0.35, imgsz: 1280 }, position: { x: 350, y: 100 } },
          { id: 'yolo_2', type: 'yolo', label: 'YOLO (High Conf)', parameters: { confidence: 0.5, imgsz: 1280 }, position: { x: 350, y: 180 } },
          { id: 'yolopid_1', type: 'yolopid', label: 'YOLO-PID (P&ID)', parameters: { confidence: 0.25, imgsz: 640 }, position: { x: 350, y: 260 } },
          { id: 'yolopid_2', type: 'yolopid', label: 'YOLO-PID (High Res)', parameters: { confidence: 0.25, imgsz: 1280 }, position: { x: 350, y: 340 } },
          // Merge results
          { id: 'merge_1', type: 'merge', label: 'Detection Comparison', parameters: {}, position: { x: 650, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'yolo_2' },
          { id: 'e3', source: 'imageinput_1', target: 'yolopid_1' },
          { id: 'e4', source: 'imageinput_1', target: 'yolopid_2' },
          { id: 'e5', source: 'yolo_1', target: 'merge_1' },
          { id: 'e6', source: 'yolo_2', target: 'merge_1' },
          { id: 'e7', source: 'yolopid_1', target: 'merge_1' },
          { id: 'e8', source: 'yolopid_2', target: 'merge_1' },
        ],
      },
    },

    // Segmentation Benchmark - EDGNet vs Line Detector
    {
      nameKey: 'segmentationBenchmark',
      descKey: 'segmentationBenchmarkDesc',
      useCaseKey: 'segmentationBenchmarkUseCase',
      estimatedTime: '8-12s',
      accuracy: 'Comparison',
      category: 'benchmark',
      workflow: {
        name: 'Segmentation Benchmark',
        description: 'Compare EDGNet edge segmentation vs Line Detector for different use cases',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 50, y: 200 } },
          // EDGNet variants
          { id: 'edgnet_1', type: 'edgnet', label: 'EDGNet (Default)', parameters: { threshold: 0.5 }, position: { x: 350, y: 80 } },
          { id: 'edgnet_2', type: 'edgnet', label: 'EDGNet (High Sens)', parameters: { threshold: 0.3 }, position: { x: 350, y: 160 } },
          // Line Detector variants
          { id: 'linedetector_1', type: 'linedetector', label: 'Line Detector (LSD)', parameters: { method: 'lsd', merge_lines: true, classify_types: true }, position: { x: 350, y: 240 } },
          { id: 'linedetector_2', type: 'linedetector', label: 'Line Detector (Hough)', parameters: { method: 'hough', merge_lines: true, classify_types: true }, position: { x: 350, y: 320 } },
          // Merge results
          { id: 'merge_1', type: 'merge', label: 'Segmentation Comparison', parameters: {}, position: { x: 650, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'edgnet_1' },
          { id: 'e2', source: 'imageinput_1', target: 'edgnet_2' },
          { id: 'e3', source: 'imageinput_1', target: 'linedetector_1' },
          { id: 'e4', source: 'imageinput_1', target: 'linedetector_2' },
          { id: 'e5', source: 'edgnet_1', target: 'merge_1' },
          { id: 'e6', source: 'edgnet_2', target: 'merge_1' },
          { id: 'e7', source: 'linedetector_1', target: 'merge_1' },
          { id: 'e8', source: 'linedetector_2', target: 'merge_1' },
        ],
      },
    },

    // Analysis Benchmark - SkinModel, PID Analyzer, Design Checker
    {
      nameKey: 'analysisBenchmark',
      descKey: 'analysisBenchmarkDesc',
      useCaseKey: 'analysisBenchmarkUseCase',
      estimatedTime: '15-25s',
      accuracy: 'Comparison',
      category: 'benchmark',
      workflow: {
        name: 'Analysis Benchmark',
        description: 'Compare all analysis engines: SkinModel tolerance, PID Analyzer connectivity, Design Checker validation',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 50, y: 200 } },
          // Detection first
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.35 }, position: { x: 250, y: 100 } },
          { id: 'yolopid_1', type: 'yolopid', label: 'YOLO-PID Detection', parameters: { confidence: 0.25 }, position: { x: 250, y: 300 } },
          { id: 'linedetector_1', type: 'linedetector', label: 'Line Detector', parameters: { method: 'lsd' }, position: { x: 250, y: 400 } },
          // OCR for tolerance
          { id: 'edocr2_1', type: 'edocr2', label: 'Dimension OCR', parameters: {}, position: { x: 450, y: 100 } },
          // Analysis engines
          { id: 'skinmodel_1', type: 'skinmodel', label: 'SkinModel (Tolerance)', parameters: {}, position: { x: 650, y: 100 } },
          { id: 'pidanalyzer_1', type: 'pidanalyzer', label: 'PID Analyzer (Connectivity)', parameters: { generate_bom: true, generate_valve_list: true }, position: { x: 650, y: 250 } },
          { id: 'designchecker_1', type: 'designchecker', label: 'Design Checker (Validation)', parameters: { severity_threshold: 'warning' }, position: { x: 650, y: 400 } },
          // Merge results
          { id: 'merge_1', type: 'merge', label: 'Analysis Comparison', parameters: {}, position: { x: 900, y: 250 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'yolopid_1' },
          { id: 'e3', source: 'imageinput_1', target: 'linedetector_1' },
          { id: 'e4', source: 'yolo_1', target: 'edocr2_1' },
          { id: 'e5', source: 'edocr2_1', target: 'skinmodel_1' },
          { id: 'e6', source: 'yolopid_1', target: 'pidanalyzer_1' },
          { id: 'e7', source: 'linedetector_1', target: 'pidanalyzer_1' },
          { id: 'e8', source: 'pidanalyzer_1', target: 'designchecker_1' },
          { id: 'e9', source: 'skinmodel_1', target: 'merge_1' },
          { id: 'e10', source: 'pidanalyzer_1', target: 'merge_1' },
          { id: 'e11', source: 'designchecker_1', target: 'merge_1' },
        ],
      },
    },

    // Preprocessing Benchmark - ESRGAN scales
    {
      nameKey: 'preprocessingBenchmark',
      descKey: 'preprocessingBenchmarkDesc',
      useCaseKey: 'preprocessingBenchmarkUseCase',
      estimatedTime: '20-30s',
      accuracy: 'Comparison',
      category: 'benchmark',
      workflow: {
        name: 'Preprocessing Benchmark',
        description: 'Compare image enhancement effects: Original vs ESRGAN 2x vs ESRGAN 4x on OCR accuracy',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 50, y: 200 } },
          // Original path
          { id: 'edocr2_1', type: 'edocr2', label: 'OCR (Original)', parameters: {}, position: { x: 350, y: 50 } },
          // ESRGAN 2x path
          { id: 'esrgan_1', type: 'esrgan', label: 'ESRGAN 2x', parameters: { scale: 2 }, position: { x: 250, y: 200 } },
          { id: 'edocr2_2', type: 'edocr2', label: 'OCR (2x Upscale)', parameters: {}, position: { x: 450, y: 200 } },
          // ESRGAN 4x path
          { id: 'esrgan_2', type: 'esrgan', label: 'ESRGAN 4x', parameters: { scale: 4 }, position: { x: 250, y: 350 } },
          { id: 'edocr2_3', type: 'edocr2', label: 'OCR (4x Upscale)', parameters: {}, position: { x: 450, y: 350 } },
          // Merge results
          { id: 'merge_1', type: 'merge', label: 'Quality Comparison', parameters: {}, position: { x: 650, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'edocr2_1' },
          { id: 'e2', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e3', source: 'imageinput_1', target: 'esrgan_2' },
          { id: 'e4', source: 'esrgan_1', target: 'edocr2_2' },
          { id: 'e5', source: 'esrgan_2', target: 'edocr2_3' },
          { id: 'e6', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e7', source: 'edocr2_2', target: 'merge_1' },
          { id: 'e8', source: 'edocr2_3', target: 'merge_1' },
        ],
      },
    },

    // AI Benchmark - VL with different prompts
    {
      nameKey: 'aiBenchmark',
      descKey: 'aiBenchmarkDesc',
      useCaseKey: 'aiBenchmarkUseCase',
      estimatedTime: '15-25s',
      accuracy: 'Comparison',
      category: 'benchmark',
      workflow: {
        name: 'AI Benchmark',
        description: 'Compare Vision-Language model responses with different prompts and contexts',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 50, y: 200 } },
          // Different prompt inputs
          { id: 'textinput_1', type: 'textinput', label: 'Describe Drawing', parameters: { text: 'Describe this engineering drawing in detail' }, position: { x: 250, y: 50 } },
          { id: 'textinput_2', type: 'textinput', label: 'Extract Dimensions', parameters: { text: 'Extract all dimensions and tolerances from this drawing' }, position: { x: 250, y: 200 } },
          { id: 'textinput_3', type: 'textinput', label: 'Analyze Issues', parameters: { text: 'Identify potential issues or errors in this drawing' }, position: { x: 250, y: 350 } },
          // VL models with different prompts
          { id: 'vl_1', type: 'vl', label: 'VL (Description)', parameters: {}, position: { x: 500, y: 50 } },
          { id: 'vl_2', type: 'vl', label: 'VL (Dimensions)', parameters: {}, position: { x: 500, y: 200 } },
          { id: 'vl_3', type: 'vl', label: 'VL (Review)', parameters: {}, position: { x: 500, y: 350 } },
          // Merge results
          { id: 'merge_1', type: 'merge', label: 'AI Response Comparison', parameters: {}, position: { x: 750, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'vl_1' },
          { id: 'e2', source: 'imageinput_1', target: 'vl_2' },
          { id: 'e3', source: 'imageinput_1', target: 'vl_3' },
          { id: 'e4', source: 'textinput_1', target: 'vl_1' },
          { id: 'e5', source: 'textinput_2', target: 'vl_2' },
          { id: 'e6', source: 'textinput_3', target: 'vl_3' },
          { id: 'e7', source: 'vl_1', target: 'merge_1' },
          { id: 'e8', source: 'vl_2', target: 'merge_1' },
          { id: 'e9', source: 'vl_3', target: 'merge_1' },
        ],
      },
    },

    // ============ AI TEMPLATES ============
    {
      nameKey: 'vlAssisted',
      descKey: 'vlAssistedDesc',
      useCaseKey: 'vlAssistedUseCase',
      estimatedTime: '8-12s',
      accuracy: '93%',
      category: 'ai',
      workflow: {
        name: 'VL-Assisted Analysis',
        description: 'Vision-Language AI for intelligent drawing understanding',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Drawing Input', parameters: {}, position: { x: 100, y: 150 } },
          { id: 'textinput_1', type: 'textinput', label: 'Analysis Prompt', parameters: { text: 'Analyze this engineering drawing and extract all dimensions' }, position: { x: 100, y: 300 } },
          { id: 'vl_1', type: 'vl', label: 'VL Model Analysis', parameters: {}, position: { x: 400, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Verification', parameters: { confidence: 0.4 }, position: { x: 700, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'vl_1' },
          { id: 'e2', source: 'textinput_1', target: 'vl_1' },
          { id: 'e3', source: 'vl_1', target: 'yolo_1' },
        ],
      },
    },
    {
      nameKey: 'knowledgeEnhanced',
      descKey: 'knowledgeEnhancedDesc',
      useCaseKey: 'knowledgeEnhancedUseCase',
      estimatedTime: '10-15s',
      accuracy: '91%',
      category: 'ai',
      workflow: {
        name: 'Knowledge-Enhanced Analysis',
        description: 'Use domain knowledge for context-aware analysis',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Drawing Input', parameters: {}, position: { x: 100, y: 150 } },
          { id: 'textinput_1', type: 'textinput', label: 'Query', parameters: { text: 'GD&T symbols meaning' }, position: { x: 100, y: 300 } },
          { id: 'yolo_1', type: 'yolo', label: 'Symbol Detection', parameters: { confidence: 0.4 }, position: { x: 350, y: 150 } },
          { id: 'knowledge_1', type: 'knowledge', label: 'Knowledge Query', parameters: {}, position: { x: 350, y: 300 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'OCR', parameters: {}, position: { x: 600, y: 150 } },
          { id: 'merge_1', type: 'merge', label: 'Contextualized Results', parameters: {}, position: { x: 850, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'textinput_1', target: 'knowledge_1' },
          { id: 'e3', source: 'yolo_1', target: 'edocr2_1' },
          { id: 'e4', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e5', source: 'knowledge_1', target: 'merge_1' },
        ],
      },
    },

    // ============ CONTROL FLOW TEMPLATES ============
    {
      nameKey: 'conditionalOCR',
      descKey: 'conditionalOCRDesc',
      useCaseKey: 'conditionalOCRUseCase',
      estimatedTime: '8-12s',
      accuracy: '94%',
      category: 'advanced',
      workflow: {
        name: 'Conditional OCR Pipeline',
        description: 'Intelligent branching based on detection confidence',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 150 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.5 }, position: { x: 300, y: 150 } },
          { id: 'if_1', type: 'if', label: 'Check Confidence', parameters: { condition: 'confidence > 0.8' }, position: { x: 500, y: 150 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'eDOCr2 (High Conf)', parameters: {}, position: { x: 700, y: 80 } },
          { id: 'ocr_ensemble_1', type: 'ocr_ensemble', label: 'OCR Ensemble (Low Conf)', parameters: {}, position: { x: 700, y: 220 } },
          { id: 'merge_1', type: 'merge', label: 'Merge Results', parameters: {}, position: { x: 950, y: 150 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'yolo_1', target: 'if_1' },
          { id: 'e3', source: 'if_1', target: 'edocr2_1', sourceHandle: 'true' },
          { id: 'e4', source: 'if_1', target: 'ocr_ensemble_1', sourceHandle: 'false' },
          { id: 'e5', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e6', source: 'ocr_ensemble_1', target: 'merge_1' },
        ],
      },
    },
    {
      nameKey: 'loopDetection',
      descKey: 'loopDetectionDesc',
      useCaseKey: 'loopDetectionUseCase',
      estimatedTime: '15-25s',
      accuracy: '96%',
      category: 'advanced',
      workflow: {
        name: 'Loop Detection Pipeline',
        description: 'Process each detection individually for maximum accuracy',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 150 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.35 }, position: { x: 300, y: 150 } },
          { id: 'loop_1', type: 'loop', label: 'For Each Detection', parameters: { iterator: 'detections' }, position: { x: 500, y: 150 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'OCR Each Box', parameters: {}, position: { x: 700, y: 150 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: 'Tolerance Analysis', parameters: {}, position: { x: 900, y: 150 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'yolo_1', target: 'loop_1' },
          { id: 'e3', source: 'loop_1', target: 'edocr2_1' },
          { id: 'e4', source: 'edocr2_1', target: 'skinmodel_1' },
        ],
      },
    },
  ];

  const handleLoadTemplate = (template: TemplateInfo) => {
    loadWorkflow(template.workflow);
    navigate('/blueprintflow/builder');
  };

  // Group templates by category
  const featuredTemplates = templates.filter(t => t.featured);
  const basicTemplates = templates.filter(t => t.category === 'basic');
  const advancedTemplates = templates.filter(t => t.category === 'advanced' && !t.featured);
  const pidTemplates = templates.filter(t => t.category === 'pid' && !t.featured);
  const aiTemplates = templates.filter(t => t.category === 'ai');
  const benchmarkTemplates = templates.filter(t => t.category === 'benchmark');

  const categoryInfo = {
    featured: { icon: Star, color: 'from-amber-500 to-orange-500', label: t('blueprintflow.featuredTemplates') },
    basic: { icon: Zap, color: 'from-green-500 to-emerald-500', label: t('blueprintflow.basicTemplates') },
    advanced: { icon: Layers, color: 'from-blue-500 to-indigo-500', label: t('blueprintflow.advancedTemplates') },
    pid: { icon: GitBranch, color: 'from-purple-500 to-pink-500', label: t('blueprintflow.pidTemplates') },
    ai: { icon: Brain, color: 'from-cyan-500 to-teal-500', label: t('blueprintflow.aiTemplates') },
    benchmark: { icon: FlaskConical, color: 'from-rose-500 to-red-500', label: t('blueprintflow.benchmarkTemplates') },
  };

  const renderCategorySection = (categoryTemplates: TemplateInfo[], categoryKey: keyof typeof categoryInfo) => {
    if (categoryTemplates.length === 0) return null;
    const { icon: Icon, color, label } = categoryInfo[categoryKey];

    return (
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-4">
          <div className={`p-2 rounded-lg bg-gradient-to-r ${color}`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{label}</h2>
          <Badge variant="outline">{categoryTemplates.length}</Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {categoryTemplates.map((template, index) => (
            <Card key={index} className={`hover:shadow-lg transition-shadow group ${template.featured ? 'ring-2 ring-amber-400 dark:ring-amber-500' : ''}`}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CardTitle className="text-xl font-bold">
                        {t(`blueprintflow.${template.nameKey}`)}
                      </CardTitle>
                      {template.featured && (
                        <Star className="w-5 h-5 text-amber-500 fill-amber-500" />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {t(`blueprintflow.${template.descKey}`)}
                    </p>
                  </div>
                  <Badge className={`bg-gradient-to-r ${color} text-white`}>
                    {template.category.toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 mb-6">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <GitBranch className="w-4 h-4" />
                      <span>{t('blueprintflow.nodes')}:</span>
                    </div>
                    <span className="font-semibold">{template.workflow.nodes.length} nodes</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <Clock className="w-4 h-4" />
                      <span>{t('blueprintflow.estimatedTime')}:</span>
                    </div>
                    <span className="font-semibold">{template.estimatedTime}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <Target className="w-4 h-4" />
                      <span>{t('blueprintflow.accuracy')}:</span>
                    </div>
                    <span className="font-semibold text-green-600 dark:text-green-400">
                      {template.accuracy}
                    </span>
                  </div>
                </div>

                {/* Use Case Recommendation */}
                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 mb-4">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="text-xs font-semibold text-amber-800 dark:text-amber-300 mb-1">
                        {t('blueprintflow.whenToUse')}
                      </div>
                      <p className="text-xs text-amber-700 dark:text-amber-400">
                        {t(`blueprintflow.${template.useCaseKey}`)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4">
                  <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                    Pipeline Flow:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {template.workflow.nodes.map((node, idx) => (
                      <div key={node.id} className="flex items-center">
                        <Badge variant="outline" className="text-xs">
                          {node.label}
                        </Badge>
                        {idx < template.workflow.nodes.length - 1 && (
                          <span className="mx-1 text-gray-400">→</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <Button
                  onClick={() => handleLoadTemplate(template)}
                  className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700"
                >
                  <Download className="w-4 h-4" />
                  {t('blueprintflow.useTemplate')}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Sparkles className="w-8 h-8 text-cyan-600" />
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            {t('blueprintflow.workflowTemplates')}
          </h1>
          <Badge className="bg-cyan-600">BETA</Badge>
          <Badge variant="outline" className="ml-2">{templates.length} templates</Badge>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          {t('blueprintflow.templatesSubtitle')}
        </p>
      </div>

      {/* Featured Templates */}
      {renderCategorySection(featuredTemplates, 'featured')}

      {/* Basic Templates */}
      {renderCategorySection(basicTemplates, 'basic')}

      {/* Advanced Templates */}
      {renderCategorySection(advancedTemplates, 'advanced')}

      {/* P&ID Templates */}
      {renderCategorySection(pidTemplates, 'pid')}

      {/* AI Templates */}
      {renderCategorySection(aiTemplates, 'ai')}

      {/* Benchmark Templates */}
      {renderCategorySection(benchmarkTemplates, 'benchmark')}

      {/* How Templates Work */}
      <Card className="mt-8 border-cyan-200 dark:border-cyan-800">
        <CardHeader className="bg-cyan-50 dark:bg-cyan-900/20">
          <CardTitle className="text-cyan-900 dark:text-cyan-100">
            {t('blueprintflow.howTemplatesWork')}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {t('blueprintflow.templatesExplanation')}
          </p>
          <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-xs font-mono overflow-x-auto">
            <pre>{`{
  "workflow": {
    "name": "${t('blueprintflow.accuracyPipeline')}",
    "nodes": [
      { "id": "yolo_1", "type": "yolo", "params": {...} },
      { "id": "edocr2_1", "type": "edocr2", "params": {...} }
    ],
    "edges": [
      { "source": "yolo_1", "target": "edocr2_1" }
    ]
  }
}`}</pre>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
