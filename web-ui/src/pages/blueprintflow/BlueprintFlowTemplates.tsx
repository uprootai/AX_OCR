import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Sparkles, Download, GitBranch, Clock, Target, Star, Zap, Brain, Layers, Lightbulb, FlaskConical, Ship, Cog } from 'lucide-react';
import { useWorkflowStore } from '../../store/workflowStore';
import type { WorkflowDefinition } from '../../lib/api';

type TemplateCategory = 'all' | 'featured' | 'techcross' | 'dsebearing' | 'basic' | 'advanced' | 'pid' | 'ai' | 'benchmark';

interface TemplateInfo {
  nameKey: string;
  descKey: string;
  useCaseKey: string;
  workflow: WorkflowDefinition;
  estimatedTime: string;
  accuracy: string;
  category: 'basic' | 'advanced' | 'pid' | 'ai' | 'benchmark' | 'techcross' | 'dsebearing';
  featured?: boolean;
}

export default function BlueprintFlowTemplates() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { loadWorkflow } = useWorkflowStore();
  const [activeTab, setActiveTab] = useState<TemplateCategory>('all');

  const templates: TemplateInfo[] = [
    // ============ FEATURED TEMPLATES ============
    {
      nameKey: 'completeAnalysis',
      descKey: 'completeAnalysisDesc',
      useCaseKey: 'completeAnalysisUseCase',
      estimatedTime: '30-40s',
      accuracy: '98%',
      category: 'advanced',
      featured: true,
      workflow: {
        name: 'Complete Drawing Analysis',
        description: 'Full analysis with AI BOM Human-in-the-Loop, detection, OCR, tolerance analysis, and AI description',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Drawing Input', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'esrgan_1', type: 'esrgan', label: 'Image Enhancement', parameters: { scale: 2 }, position: { x: 300, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'Symbol Detection', parameters: { confidence: 0.35, imgsz: 1280 }, position: { x: 500, y: 100 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Symbol Verification (AI BOM)', parameters: { features: ['symbol_detection', 'vlm_auto_classification', 'human_verification'] }, position: { x: 700, y: 100 } },
          { id: 'edgnet_1', type: 'edgnet', label: 'Segmentation', parameters: { threshold: 0.5 }, position: { x: 500, y: 300 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'Dimension OCR', parameters: {}, position: { x: 750, y: 300 } },
          { id: 'ocr_ensemble_1', type: 'ocr_ensemble', label: 'OCR Ensemble', parameters: {}, position: { x: 900, y: 100 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: 'Tolerance Analysis', parameters: {}, position: { x: 950, y: 300 } },
          { id: 'vl_1', type: 'vl', label: 'AI Description', parameters: { prompt: 'Describe this engineering drawing' }, position: { x: 1100, y: 150 } },
          { id: 'merge_1', type: 'merge', label: 'Final Results', parameters: {}, position: { x: 1300, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e2', source: 'esrgan_1', target: 'yolo_1' },
          { id: 'e3', source: 'esrgan_1', target: 'edgnet_1' },
          { id: 'e4', source: 'esrgan_1', target: 'aibom_1' },
          { id: 'e5', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e6', source: 'aibom_1', target: 'ocr_ensemble_1' },
          { id: 'e7', source: 'edgnet_1', target: 'edocr2_1' },
          { id: 'e8', source: 'edocr2_1', target: 'skinmodel_1' },
          { id: 'e9', source: 'ocr_ensemble_1', target: 'vl_1' },
          { id: 'e10', source: 'skinmodel_1', target: 'vl_1' },
          { id: 'e11', source: 'vl_1', target: 'merge_1' },
        ],
      },
    },
    {
      nameKey: 'pidAnalysis',
      descKey: 'pidAnalysisDesc',
      useCaseKey: 'pidAnalysisUseCase',
      estimatedTime: '25-35s',
      accuracy: '96%',
      category: 'pid',
      featured: true,
      workflow: {
        name: 'P&ID Analysis Pipeline',
        description: 'Complete P&ID analysis with AI BOM Human-in-the-Loop, symbol detection, line detection, connectivity analysis',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'P&ID Image Input', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO P&ID Symbol Detection', parameters: { model_type: 'pid_class_aware', confidence: 0.25, iou: 0.45, imgsz: 640, use_sahi: true }, position: { x: 350, y: 100 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Symbol Verification (AI BOM)', parameters: { features: ['symbol_detection', 'vlm_auto_classification', 'human_verification'] }, position: { x: 600, y: 100 } },
          { id: 'linedetector_1', type: 'linedetector', label: 'Line Detector', parameters: { method: 'lsd', min_length: 50, merge_lines: true, classify_types: true }, position: { x: 350, y: 300 } },
          { id: 'pidanalyzer_1', type: 'pidanalyzer', label: 'P&ID Analyzer', parameters: { generate_bom: true, generate_valve_list: true, generate_equipment_list: true }, position: { x: 850, y: 200 } },
          { id: 'designchecker_1', type: 'designchecker', label: 'Design Checker', parameters: { severity_threshold: 'warning' }, position: { x: 1100, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'imageinput_1', target: 'linedetector_1' },
          { id: 'e5', source: 'aibom_1', target: 'pidanalyzer_1' },
          { id: 'e6', source: 'linedetector_1', target: 'pidanalyzer_1' },
          { id: 'e7', source: 'pidanalyzer_1', target: 'designchecker_1' },
        ],
      },
    },

    // ============ TECHCROSS TEMPLATES ============
    {
      nameKey: 'techcrossBwmsChecklist',
      descKey: 'techcrossBwmsChecklistDesc',
      useCaseKey: 'techcrossBwmsChecklistUseCase',
      estimatedTime: '15-25s',
      accuracy: '97%',
      category: 'techcross',
      featured: true,
      workflow: {
        name: 'TECHCROSS 1-1: BWMS Checklist',
        description: 'BWMS P&ID 체크리스트 검증 - AI BOM Human-in-the-Loop, 58개 ECS 규칙, 84% 노이즈 제거',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'P&ID 도면 입력', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'P&ID 심볼 검출', parameters: { model_type: 'pid_class_aware', confidence: 0.25, iou: 0.45, imgsz: 640, use_sahi: true }, position: { x: 350, y: 200 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: '심볼 검증 (AI BOM)', parameters: { features: ['symbol_detection', 'vlm_auto_classification', 'human_verification'] }, position: { x: 600, y: 200 } },
          { id: 'linedetector_1', type: 'linedetector', label: '라인 검출', parameters: { method: 'lsd', min_length: 50, classify_types: true, classify_colors: true }, position: { x: 600, y: 350 } },
          { id: 'pidanalyzer_1', type: 'pidanalyzer', label: '연결성 분석', parameters: { generate_bom: false, generate_valve_list: false, generate_equipment_list: false }, position: { x: 850, y: 350 } },
          { id: 'designchecker_1', type: 'designchecker', label: 'BWMS 체크리스트', parameters: { rule_profile: 'bwms', product_type: 'ECS', severity_threshold: 'warning' }, position: { x: 1100, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'Excel 내보내기', parameters: { template: 'techcross_checklist' }, position: { x: 1350, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'imageinput_1', target: 'linedetector_1' },
          { id: 'e5', source: 'aibom_1', target: 'pidanalyzer_1' },
          { id: 'e6', source: 'linedetector_1', target: 'pidanalyzer_1' },
          { id: 'e7', source: 'aibom_1', target: 'designchecker_1' },
          { id: 'e8', source: 'pidanalyzer_1', target: 'designchecker_1' },
          { id: 'e9', source: 'designchecker_1', target: 'excelexport_1' },
        ],
      },
    },
    {
      nameKey: 'techcrossValveSignal',
      descKey: 'techcrossValveSignalDesc',
      useCaseKey: 'techcrossValveSignalUseCase',
      estimatedTime: '15-25s',
      accuracy: '96%',
      category: 'techcross',
      workflow: {
        name: 'TECHCROSS 1-2: Valve Signal List',
        description: '밸브 신호 목록 생성 - AI BOM Human-in-the-Loop, Control/Isolation/Safety/Check/Relief 분류',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'P&ID 도면 입력', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'P&ID 심볼 검출', parameters: { model_type: 'pid_class_aware', confidence: 0.25, iou: 0.45, imgsz: 640, use_sahi: true }, position: { x: 350, y: 200 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: '밸브 검증 (AI BOM)', parameters: { features: ['symbol_detection', 'valve_classification', 'human_verification'] }, position: { x: 600, y: 200 } },
          { id: 'pidfeatures_1', type: 'pidfeatures', label: '밸브 신호 분석', parameters: { detect_valves: true, detect_equipment: false, classify_valve_types: true }, position: { x: 850, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'Valve Signal Excel', parameters: { template: 'techcross_valve_signal' }, position: { x: 1100, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'aibom_1', target: 'pidfeatures_1' },
          { id: 'e5', source: 'pidfeatures_1', target: 'excelexport_1' },
        ],
      },
    },
    {
      nameKey: 'techcrossEquipmentList',
      descKey: 'techcrossEquipmentListDesc',
      useCaseKey: 'techcrossEquipmentListUseCase',
      estimatedTime: '15-25s',
      accuracy: '93%',
      category: 'techcross',
      workflow: {
        name: 'TECHCROSS 1-3: Equipment List',
        description: '장비 목록 생성 - AI BOM 기반 Human-in-the-Loop 검증, PUMP/TANK/ECU/FMU/HGU 검출 및 수량 집계',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'P&ID 도면 입력', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'P&ID 심볼 검출', parameters: { model_type: 'pid_class_aware', confidence: 0.25, iou: 0.45, imgsz: 640, use_sahi: true }, position: { x: 400, y: 200 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'AI BOM 검증', parameters: { features: ['symbol_detection', 'vlm_auto_classification'] }, position: { x: 700, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'Equipment List Excel', parameters: { template: 'techcross_equipment' }, position: { x: 1000, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'aibom_1', target: 'excelexport_1' },
        ],
      },
    },
    {
      nameKey: 'techcrossDeviation',
      descKey: 'techcrossDeviationDesc',
      useCaseKey: 'techcrossDeviationUseCase',
      estimatedTime: '20-30s',
      accuracy: '92%',
      category: 'techcross',
      workflow: {
        name: 'TECHCROSS 1-4: Deviation Analysis (AI BOM)',
        description: '편차 분석 - AI BOM 기반 Human-in-the-Loop 검증, ISO 10628/ISA 5.1/BWMS 표준 편차 검토 및 심각도 조정',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'P&ID 도면 입력', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'P&ID 심볼 검출', parameters: { model_type: 'pid_class_aware', confidence: 0.25, iou: 0.45, imgsz: 640, use_sahi: true }, position: { x: 350, y: 100 } },
          { id: 'linedetector_1', type: 'linedetector', label: '라인 검출', parameters: { method: 'lsd', min_length: 50, classify_types: true, detect_intersections: true }, position: { x: 350, y: 300 } },
          { id: 'pidanalyzer_1', type: 'pidanalyzer', label: '연결성 분석', parameters: { generate_bom: false, generate_valve_list: false, generate_equipment_list: false }, position: { x: 600, y: 200 } },
          { id: 'pidfeatures_1', type: 'pidfeatures', label: '편차 분석', parameters: { analyze_deviation: true, standards: ['ISO_10628', 'ISA_5.1', 'BWMS'], analysis_types: ['connectivity', 'symbol_validation'] }, position: { x: 850, y: 200 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: '편차 검증 (AI BOM)', parameters: { features: ['symbol_detection', 'deviation_review'] }, position: { x: 1050, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'Deviation List Excel', parameters: { template: 'techcross_deviation' }, position: { x: 1250, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'linedetector_1' },
          { id: 'e3', source: 'yolo_1', target: 'pidanalyzer_1' },
          { id: 'e4', source: 'linedetector_1', target: 'pidanalyzer_1' },
          { id: 'e5', source: 'pidanalyzer_1', target: 'pidfeatures_1' },
          { id: 'e6', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e7', source: 'pidfeatures_1', target: 'aibom_1' },
          { id: 'e8', source: 'aibom_1', target: 'excelexport_1' },
        ],
      },
    },

    // ============ DSE BEARING TEMPLATES ============
    {
      nameKey: 'dseBearingAnalysis',
      descKey: 'dseBearingAnalysisDesc',
      useCaseKey: 'dseBearingAnalysisUseCase',
      estimatedTime: '20-30s',
      accuracy: '96%',
      category: 'dsebearing',
      featured: true,
      workflow: {
        name: 'DSE Bearing 1-1: 도면 분석 + AI BOM',
        description: '터빈 베어링 기계 부품도 분석 - Table Detector로 BOM 테이블 추출, 치수/재질/공차 추출, 견적용 BOM 생성',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: '부품도 입력', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'tabledetector_1', type: 'table_detector', label: 'BOM 테이블 추출', parameters: { borderless: true, ocr_engine: 'tesseract', confidence_threshold: 0.5 }, position: { x: 350, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: '치수/텍스트 OCR', parameters: { extract_dimensions: true, extract_gdt: true, language: 'ko+en' }, position: { x: 350, y: 300 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: '도면 검증 (AI BOM)', parameters: { features: ['table_extraction', 'dimension_extraction', 'human_verification'], drawing_type: 'mechanical' }, position: { x: 600, y: 200 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: '공차 분석', parameters: { task: 'tolerance', material_type: 'steel', manufacturing_process: 'machining' }, position: { x: 850, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'BOM Excel 내보내기', parameters: { export_type: 'all', project_name: 'DSE Bearing BOM' }, position: { x: 1100, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'tabledetector_1' },
          { id: 'e2', source: 'imageinput_1', target: 'edocr2_1' },
          { id: 'e3', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e4', source: 'tabledetector_1', target: 'aibom_1' },
          { id: 'e5', source: 'edocr2_1', target: 'aibom_1' },
          { id: 'e6', source: 'aibom_1', target: 'skinmodel_1' },
          { id: 'e7', source: 'skinmodel_1', target: 'excelexport_1' },
        ],
      },
    },
    {
      nameKey: 'dseBearingQuote',
      descKey: 'dseBearingQuoteDesc',
      useCaseKey: 'dseBearingQuoteUseCase',
      estimatedTime: '25-35s',
      accuracy: '95%',
      category: 'dsebearing',
      workflow: {
        name: 'DSE Bearing 1-2: 견적용 종합 분석',
        description: '도면 분석 + VLM 분류 + Table Detector + 공차 분석 - 소재비/가공비 견적 자동화',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: '부품도 입력', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'vl_1', type: 'vl', label: 'VLM 도면 분류', parameters: { prompt: '이 기계도면의 부품 종류, 재질, 주요 치수를 분석해주세요' }, position: { x: 350, y: 50 } },
          { id: 'tabledetector_1', type: 'table_detector', label: 'BOM 테이블 추출', parameters: { borderless: true, ocr_engine: 'tesseract', confidence_threshold: 0.5 }, position: { x: 350, y: 200 } },
          { id: 'edocr2_1', type: 'edocr2', label: '치수/텍스트 OCR', parameters: { extract_dimensions: true, extract_gdt: true }, position: { x: 350, y: 350 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: '도면 검증 (AI BOM)', parameters: { features: ['table_extraction', 'vlm_auto_classification', 'dimension_extraction', 'human_verification'], drawing_type: 'mechanical' }, position: { x: 600, y: 200 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: '공차 분석', parameters: { task: 'manufacturability', material_type: 'steel', manufacturing_process: 'machining' }, position: { x: 850, y: 200 } },
          { id: 'merge_1', type: 'merge', label: '분석 결과 통합', parameters: {}, position: { x: 1050, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: '견적서 Excel', parameters: { export_type: 'all', project_name: 'DSE Bearing Quote' }, position: { x: 1250, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'vl_1' },
          { id: 'e2', source: 'imageinput_1', target: 'tabledetector_1' },
          { id: 'e3', source: 'imageinput_1', target: 'edocr2_1' },
          { id: 'e4', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e5', source: 'tabledetector_1', target: 'aibom_1' },
          { id: 'e6', source: 'edocr2_1', target: 'aibom_1' },
          { id: 'e7', source: 'vl_1', target: 'merge_1' },
          { id: 'e8', source: 'aibom_1', target: 'skinmodel_1' },
          { id: 'e9', source: 'skinmodel_1', target: 'merge_1' },
          { id: 'e10', source: 'merge_1', target: 'excelexport_1' },
        ],
      },
    },
    {
      nameKey: 'dseBearingBomMatch',
      descKey: 'dseBearingBomMatchDesc',
      useCaseKey: 'dseBearingBomMatchUseCase',
      estimatedTime: '15-20s',
      accuracy: '97%',
      category: 'dsebearing',
      workflow: {
        name: 'DSE Bearing 1-3: BOM 매칭',
        description: '도면번호 기반 BOM 자동 매핑 - TD00XXXXX ↔ BOM 품목 연결',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: '부품도 입력', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'edocr2_1', type: 'edocr2', label: '도면번호/품명 OCR', parameters: { extract_text: true, extract_tables: true, language: 'ko+en' }, position: { x: 350, y: 200 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'BOM 매칭 (AI BOM)', parameters: { features: ['part_number_extraction', 'bom_matching', 'human_verification'], drawing_type: 'mechanical' }, position: { x: 600, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'BOM 매칭 결과', parameters: { export_type: 'all', project_name: 'DSE Bearing BOM Match' }, position: { x: 850, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'edocr2_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'edocr2_1', target: 'aibom_1' },
          { id: 'e4', source: 'aibom_1', target: 'excelexport_1' },
        ],
      },
    },
    // DSE Bearing 2-1: Bearing Ring ASSY (T1-T8 시리즈)
    {
      nameKey: 'dseBearingRingAssy',
      descKey: 'dseBearingRingAssyDesc',
      useCaseKey: 'dseBearingRingAssyUseCase',
      estimatedTime: '25-35s',
      accuracy: '94%',
      category: 'dsebearing',
      workflow: {
        name: 'DSE Bearing 2-1: Bearing Ring ASSY',
        description: 'Tilting Pad(T1-T3)/Elliptical(T4-T8) 베어링 링 조립체 - Table Detector로 BOM 추출 + Babbitt 라이닝 틈새 분석',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Ring ASSY 도면', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'esrgan_1', type: 'esrgan', label: '이미지 향상', parameters: { scale: 2 }, position: { x: 300, y: 200 } },
          { id: 'tabledetector_1', type: 'table_detector', label: 'BOM 테이블 추출', parameters: { borderless: true, ocr_engine: 'tesseract', confidence_threshold: 0.5 }, position: { x: 500, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: '치수/공차 OCR', parameters: { extract_dimensions: true, extract_gdt: true, extract_tables: true }, position: { x: 500, y: 300 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'BOM 검증 (AI BOM)', parameters: { features: ['table_extraction', 'part_list', 'human_verification'], drawing_type: 'bearing_ring' }, position: { x: 750, y: 200 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: '틈새 공차 분석', parameters: { task: 'tolerance', material_type: 'steel', correlation_length: 2.0 }, position: { x: 1000, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'Ring ASSY BOM', parameters: { export_type: 'all', project_name: 'DSE Bearing Ring ASSY' }, position: { x: 1250, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e2', source: 'esrgan_1', target: 'tabledetector_1' },
          { id: 'e3', source: 'esrgan_1', target: 'edocr2_1' },
          { id: 'e4', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e5', source: 'tabledetector_1', target: 'aibom_1' },
          { id: 'e6', source: 'edocr2_1', target: 'aibom_1' },
          { id: 'e7', source: 'aibom_1', target: 'skinmodel_1' },
          { id: 'e8', source: 'skinmodel_1', target: 'excelexport_1' },
        ],
      },
    },
    // DSE Bearing 2-2: Bearing Casing ASSY
    {
      nameKey: 'dseBearingCasingAssy',
      descKey: 'dseBearingCasingAssyDesc',
      useCaseKey: 'dseBearingCasingAssyUseCase',
      estimatedTime: '25-35s',
      accuracy: '93%',
      category: 'dsebearing',
      workflow: {
        name: 'DSE Bearing 2-2: Bearing Casing ASSY',
        description: '베어링 케이싱 조립체 - Table Detector + VLM으로 상하부 Split 구조, 오일 포트/나사 가공 추출',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Casing ASSY 도면', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'esrgan_1', type: 'esrgan', label: '이미지 향상', parameters: { scale: 2 }, position: { x: 300, y: 200 } },
          { id: 'tabledetector_1', type: 'table_detector', label: 'BOM 테이블 추출', parameters: { borderless: true, ocr_engine: 'tesseract', confidence_threshold: 0.5 }, position: { x: 500, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: '나사/포트 OCR', parameters: { extract_dimensions: true, extract_text: true, language: 'ko+en' }, position: { x: 500, y: 300 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Casing 검증', parameters: { features: ['table_extraction', 'machining_specs', 'human_verification'], drawing_type: 'bearing_casing' }, position: { x: 750, y: 200 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: '가공 난이도 분석', parameters: { task: 'manufacturability', material_type: 'steel', manufacturing_process: 'machining' }, position: { x: 1000, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'Casing 가공 명세', parameters: { export_type: 'all', project_name: 'DSE Bearing Casing' }, position: { x: 1250, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e2', source: 'esrgan_1', target: 'tabledetector_1' },
          { id: 'e3', source: 'esrgan_1', target: 'edocr2_1' },
          { id: 'e4', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e5', source: 'tabledetector_1', target: 'aibom_1' },
          { id: 'e6', source: 'edocr2_1', target: 'aibom_1' },
          { id: 'e7', source: 'aibom_1', target: 'skinmodel_1' },
          { id: 'e8', source: 'skinmodel_1', target: 'excelexport_1' },
        ],
      },
    },
    // DSE Bearing 2-3: Thrust Bearing (TBN/GEN Side)
    {
      nameKey: 'dseThrustBearing',
      descKey: 'dseThrustBearingDesc',
      useCaseKey: 'dseThrustBearingUseCase',
      estimatedTime: '30-40s',
      accuracy: '95%',
      category: 'dsebearing',
      workflow: {
        name: 'DSE Bearing 2-3: Thrust Bearing',
        description: '스러스트 베어링 조립체 (TBN/GEN Side) - Table Detector + VLM으로 12개 PAD, Leveling Plate, PIVOT 분석',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Thrust Bearing 도면', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'esrgan_1', type: 'esrgan', label: '이미지 향상', parameters: { scale: 2 }, position: { x: 300, y: 100 } },
          { id: 'vl_1', type: 'vl', label: 'VLM 구조 분석', parameters: { prompt: '스러스트 베어링의 PAD 배열, 상하부 케이싱 구조, 레벨링 플레이트 배치를 분석해주세요' }, position: { x: 300, y: 300 } },
          { id: 'tabledetector_1', type: 'table_detector', label: 'BOM 테이블 추출', parameters: { borderless: true, ocr_engine: 'tesseract', confidence_threshold: 0.5 }, position: { x: 550, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: '치수/토크 OCR', parameters: { extract_dimensions: true, extract_text: true, extract_tables: true }, position: { x: 550, y: 300 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Thrust BOM 검증', parameters: { features: ['table_extraction', 'thrust_pad_count', 'human_verification'], drawing_type: 'thrust_bearing' }, position: { x: 800, y: 200 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: 'PAD 틈새 분석', parameters: { task: 'tolerance', material_type: 'steel', correlation_length: 1.5 }, position: { x: 1050, y: 200 } },
          { id: 'merge_1', type: 'merge', label: '분석 통합', parameters: {}, position: { x: 1250, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'Thrust Bearing BOM', parameters: { export_type: 'all', project_name: 'DSE Thrust Bearing' }, position: { x: 1450, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e2', source: 'imageinput_1', target: 'vl_1' },
          { id: 'e3', source: 'esrgan_1', target: 'tabledetector_1' },
          { id: 'e4', source: 'esrgan_1', target: 'edocr2_1' },
          { id: 'e5', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e6', source: 'tabledetector_1', target: 'aibom_1' },
          { id: 'e7', source: 'edocr2_1', target: 'aibom_1' },
          { id: 'e8', source: 'aibom_1', target: 'skinmodel_1' },
          { id: 'e9', source: 'vl_1', target: 'merge_1' },
          { id: 'e10', source: 'skinmodel_1', target: 'merge_1' },
          { id: 'e11', source: 'merge_1', target: 'excelexport_1' },
        ],
      },
    },
    // DSE Bearing 2-4: CV Cone Cover (용접 상세)
    {
      nameKey: 'dseCvConeCover',
      descKey: 'dseCvConeCoverDesc',
      useCaseKey: 'dseCvConeCoverUseCase',
      estimatedTime: '30-40s',
      accuracy: '92%',
      category: 'dsebearing',
      workflow: {
        name: 'DSE Bearing 2-4: CV Cone Cover',
        description: 'CV용 콘 커버 + 천공 실린더 - VLM 용접 상세(V-groove, 35°/60° 개선), Table Detector로 BOM 추출, 전개도 분석',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'CV Cone 도면', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'esrgan_1', type: 'esrgan', label: '이미지 향상', parameters: { scale: 2 }, position: { x: 300, y: 100 } },
          { id: 'vl_1', type: 'vl', label: 'VLM 용접 해석', parameters: { prompt: '용접 상세도(SECTION A-A)의 개선 각도, 루트 간격, 패스 정보와 전개도(UNFOLDED VIEW)의 홀 패턴을 분석해주세요' }, position: { x: 300, y: 350 } },
          { id: 'tabledetector_1', type: 'table_detector', label: 'BOM 테이블 추출', parameters: { borderless: true, ocr_engine: 'tesseract', confidence_threshold: 0.5 }, position: { x: 550, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: '용접/홀 OCR', parameters: { extract_dimensions: true, extract_text: true, language: 'ko+en' }, position: { x: 550, y: 250 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'CV BOM 검증', parameters: { features: ['table_extraction', 'weld_detail', 'hole_pattern', 'human_verification'], drawing_type: 'cv_cone_cover' }, position: { x: 800, y: 175 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: '용접 난이도 분석', parameters: { task: 'manufacturability', manufacturing_process: 'welding', material_type: 'steel' }, position: { x: 1050, y: 100 } },
          { id: 'merge_1', type: 'merge', label: '분석 통합', parameters: {}, position: { x: 1250, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'CV 제작 명세', parameters: { export_type: 'all', project_name: 'DSE CV Cone Cover' }, position: { x: 1450, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e2', source: 'imageinput_1', target: 'vl_1' },
          { id: 'e3', source: 'esrgan_1', target: 'tabledetector_1' },
          { id: 'e4', source: 'esrgan_1', target: 'edocr2_1' },
          { id: 'e5', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e6', source: 'tabledetector_1', target: 'aibom_1' },
          { id: 'e7', source: 'edocr2_1', target: 'aibom_1' },
          { id: 'e8', source: 'aibom_1', target: 'skinmodel_1' },
          { id: 'e9', source: 'vl_1', target: 'merge_1' },
          { id: 'e10', source: 'skinmodel_1', target: 'merge_1' },
          { id: 'e11', source: 'merge_1', target: 'excelexport_1' },
        ],
      },
    },
    // DSE Bearing 2-5: GD&T 추출 특화
    {
      nameKey: 'dseBearingGdt',
      descKey: 'dseBearingGdtDesc',
      useCaseKey: 'dseBearingGdtUseCase',
      estimatedTime: '20-30s',
      accuracy: '88%',
      category: 'dsebearing',
      workflow: {
        name: 'DSE Bearing 2-5: GD&T 추출',
        description: '기하공차 특화 추출 - VLM + OCR로 평면도⊡/평행도///수직도⊥/흔들림⌀ + 데이텀 참조 분석',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: '부품도 입력', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'esrgan_1', type: 'esrgan', label: '4x 업스케일', parameters: { scale: 4 }, position: { x: 300, y: 200 } },
          { id: 'vl_1', type: 'vl', label: 'VLM GD&T 분석', parameters: { prompt: '이 도면의 기하공차(GD&T) 기호를 모두 찾아 분석해주세요. 평면도, 평행도, 수직도, 흔들림 기호와 데이텀 참조(A, B, C 등)를 추출하고 각 공차값을 정리해주세요.' }, position: { x: 550, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'GD&T 값 OCR', parameters: { extract_gdt: true, extract_dimensions: true }, position: { x: 550, y: 300 } },
          { id: 'ocr_ensemble_1', type: 'ocr_ensemble', label: '앙상블 검증', parameters: { engines: ['edocr2', 'paddleocr', 'tesseract'] }, position: { x: 800, y: 200 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'GD&T 검증', parameters: { features: ['vlm_gdt_extraction', 'datum_reference', 'human_verification'], drawing_type: 'gdt_focused' }, position: { x: 1050, y: 200 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: 'GD&T 스택 분석', parameters: { task: 'validate', material_type: 'steel', manufacturing_process: 'machining' }, position: { x: 1300, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'GD&T 리포트', parameters: { export_type: 'all', project_name: 'DSE GD&T Analysis' }, position: { x: 1550, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e2', source: 'esrgan_1', target: 'vl_1' },
          { id: 'e3', source: 'esrgan_1', target: 'edocr2_1' },
          { id: 'e4', source: 'vl_1', target: 'ocr_ensemble_1' },
          { id: 'e5', source: 'edocr2_1', target: 'ocr_ensemble_1' },
          { id: 'e6', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e7', source: 'ocr_ensemble_1', target: 'aibom_1' },
          { id: 'e8', source: 'aibom_1', target: 'skinmodel_1' },
          { id: 'e9', source: 'skinmodel_1', target: 'excelexport_1' },
        ],
      },
    },
    // DSE Bearing 2-6: BOM 테이블 추출 특화 (Table Detector 사용)
    {
      nameKey: 'dseBearingBomExtract',
      descKey: 'dseBearingBomExtractDesc',
      useCaseKey: 'dseBearingBomExtractUseCase',
      estimatedTime: '20-30s',
      accuracy: '97%',
      category: 'dsebearing',
      workflow: {
        name: 'DSE Bearing 2-6: BOM 테이블 추출',
        description: 'Table Detector(TATR+img2table) 기반 BOM 테이블 추출 - NO/DESCRIPTION/MATERIAL/SIZE/QTY/WT 자동 추출',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: '조립도 입력', parameters: {}, position: { x: 100, y: 200 } },
          // Table Detector: 테이블 검출 + 구조 추출
          { id: 'table_detector_1', type: 'table_detector', label: '테이블 검출/추출', parameters: { mode: 'analyze', ocr_engine: 'tesseract', borderless: true, confidence_threshold: 0.7, min_confidence: 50 }, position: { x: 350, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'BOM 셀 OCR', parameters: { extract_text: true, extract_tables: true, language: 'ko+en' }, position: { x: 350, y: 300 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'BOM 구조화', parameters: { features: ['table_extraction', 'cell_parsing', 'material_mapping', 'human_verification'], drawing_type: 'bom_focused' }, position: { x: 600, y: 200 } },
          { id: 'vl_1', type: 'vl', label: 'VLM 보정', parameters: { prompt: 'BOM 테이블에서 누락되거나 잘못 인식된 항목이 있는지 확인하고, 부품 번호와 재질 코드를 검증해주세요' }, position: { x: 850, y: 200 } },
          { id: 'excelexport_1', type: 'excelexport', label: 'BOM Excel', parameters: { export_type: 'all', project_name: 'DSE Full BOM' }, position: { x: 1100, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'table_detector_1' },
          { id: 'e2', source: 'imageinput_1', target: 'edocr2_1' },
          { id: 'e3', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e4', source: 'table_detector_1', target: 'aibom_1' },
          { id: 'e5', source: 'edocr2_1', target: 'aibom_1' },
          { id: 'e6', source: 'aibom_1', target: 'vl_1' },
          { id: 'e7', source: 'vl_1', target: 'excelexport_1' },
        ],
      },
    },
    // DSE Bearing 2-7: Parts List 테이블 추출 (Table Detector 전용)
    {
      nameKey: 'dseBearingPartsListExtract',
      descKey: 'dseBearingPartsListExtractDesc',
      useCaseKey: 'dseBearingPartsListExtractUseCase',
      estimatedTime: '10-20s',
      accuracy: '95%',
      category: 'dsebearing',
      workflow: {
        name: 'DSE Bearing 2-7: Parts List 추출',
        description: 'Table Detector 단독 - Parts List 테이블 빠른 추출 (img2table + TATR)',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: '도면 입력', parameters: {}, position: { x: 100, y: 200 } },
          // ESRGAN 업스케일링 (선택적)
          { id: 'esrgan_1', type: 'esrgan', label: 'GPU 업스케일링', parameters: { scale: 2, tile_size: 256 }, position: { x: 300, y: 200 } },
          // Table Detector: 테이블 영역 검출 + 구조 추출
          { id: 'table_detector_1', type: 'table_detector', label: 'Parts List 검출', parameters: { mode: 'analyze', ocr_engine: 'paddle', borderless: true, confidence_threshold: 0.7, min_confidence: 60, output_format: 'json' }, position: { x: 500, y: 200 } },
          // Excel 출력
          { id: 'excelexport_1', type: 'excelexport', label: 'Parts List Excel', parameters: { export_type: 'all', project_name: 'DSE Parts List' }, position: { x: 750, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e2', source: 'esrgan_1', target: 'table_detector_1' },
          { id: 'e3', source: 'table_detector_1', target: 'excelexport_1' },
        ],
      },
    },
    // DSE Bearing 2-8: YOLO 기반 Parts List 추출 (YOLO → Table Detector 파이프라인)
    {
      nameKey: 'dseBearingYoloPartsListExtract',
      descKey: 'dseBearingYoloPartsListExtractDesc',
      useCaseKey: 'dseBearingYoloPartsListExtractUseCase',
      estimatedTime: '15-25s',
      accuracy: '98%',
      category: 'dsebearing',
      featured: true,
      workflow: {
        name: 'DSE Bearing 2-8: YOLO 기반 Parts List 추출',
        description: 'YOLO로 text_block 영역 검출 후 Table Detector로 테이블 구조 추출 - TATR 검출 한계 극복',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: '도면 입력', parameters: {}, position: { x: 100, y: 200 } },
          // YOLO: text_block 영역 검출 (Parts List 테이블 위치)
          { id: 'yolo_1', type: 'yolo', label: 'Parts List 영역 검출', parameters: { model_type: 'drawing', confidence: 0.35, iou: 0.45, imgsz: 1280, classes: ['text_block'] }, position: { x: 350, y: 200 } },
          // Table Detector: YOLO가 검출한 영역에서 테이블 구조 추출
          { id: 'table_detector_1', type: 'table_detector', label: '테이블 구조 추출', parameters: { mode: 'analyze', ocr_engine: 'paddle', borderless: true, confidence_threshold: 0.5, min_confidence: 60 }, position: { x: 600, y: 200 } },
          // AI BOM: Human-in-the-Loop 검증
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Parts List 검증 (AI BOM)', parameters: { features: ['table_verification', 'human_verification'] }, position: { x: 850, y: 200 } },
          // Excel 출력
          { id: 'excelexport_1', type: 'excelexport', label: 'Parts List Excel', parameters: { export_type: 'all', project_name: 'DSE Parts List' }, position: { x: 1100, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'yolo_1', target: 'table_detector_1' },
          { id: 'e3', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e4', source: 'table_detector_1', target: 'aibom_1' },
          { id: 'e5', source: 'aibom_1', target: 'excelexport_1' },
        ],
      },
    },
    // DSE Bearing 3-1: 정밀 분석 (복잡한 공차/특수 폰트/용접 기호 해결) - GPU ESRGAN 포함
    {
      nameKey: 'dseBearingPrecision',
      descKey: 'dseBearingPrecisionDesc',
      useCaseKey: 'dseBearingPrecisionUseCase',
      estimatedTime: '35-50s',
      accuracy: '97%',
      category: 'dsebearing',
      workflow: {
        name: 'DSE Bearing 3-1: 정밀 분석',
        description: '복잡한 다단 공차(+0.15/-0.00), 특수 폰트 도면번호, 용접 기호를 정확하게 추출하는 고정밀 파이프라인 (GPU 업스케일링 + Table Detector 포함)',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: '도면 입력', parameters: {}, position: { x: 50, y: 250 } },
          // 0단계: GPU 4x 업스케일링 (저해상도 도면 개선)
          { id: 'esrgan_1', type: 'esrgan', label: 'GPU 업스케일링', parameters: { scale: 2, tile_size: 256 }, position: { x: 175, y: 250 } },
          // 1단계: BOM 테이블 추출 (병렬)
          { id: 'tabledetector_1', type: 'table_detector', label: 'BOM 테이블 추출', parameters: { borderless: true, ocr_engine: 'tesseract', confidence_threshold: 0.5 }, position: { x: 350, y: 100 } },
          // 2단계: 다단 공차 분리 추출 (cluster_threshold 낮춤, 병렬)
          { id: 'edocr2_1', type: 'edocr2', label: '다단 공차 OCR', parameters: { extract_dimensions: true, extract_gdt: true, cluster_threshold: 15, language: 'ko+en' }, position: { x: 350, y: 250 } },
          // 3단계: 특수 폰트 대응 OCR 앙상블 (병렬)
          { id: 'ocr_ensemble_1', type: 'ocr_ensemble', label: '도면번호 앙상블', parameters: { profile: 'edocr2_focus', edocr2_weight: 0.5, paddleocr_weight: 0.3, tesseract_weight: 0.1, trocr_weight: 0.1 }, position: { x: 350, y: 400 } },
          // 4단계: AI BOM 통합 검증
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'AI BOM 검증', parameters: { features: ['table_extraction', 'dimension_extraction', 'tolerance_parsing', 'human_verification'], drawing_type: 'mechanical_precision' }, position: { x: 550, y: 250 } },
          // 5단계: 공차 분석 (다단 공차 파싱)
          { id: 'skinmodel_1', type: 'skinmodel', label: '공차 스택 분석', parameters: { task: 'tolerance', material_type: 'steel', manufacturing_process: 'machining', correlation_length: 1.0 }, position: { x: 800, y: 150 } },
          // 6단계: VL 모델로 용접 기호 + 도면번호 검증
          { id: 'vl_1', type: 'vl', label: '용접/도면번호 검증', parameters: { prompt: '이 도면에서 다음을 정확히 추출해주세요:\n1. 도면번호와 리비전\n2. 모든 용접 기호 (타입, 사이즈, 위치)\n3. 복잡한 공차 (예: +0.15/-0.00 형식)\n4. 재질 사양\nJSON 형식으로 응답해주세요.' }, position: { x: 800, y: 350 } },
          // 7단계: 결과 통합
          { id: 'merge_1', type: 'merge', label: '정밀 결과 통합', parameters: {}, position: { x: 1050, y: 250 } },
          // 8단계: Excel 출력
          { id: 'excelexport_1', type: 'excelexport', label: '정밀 BOM Excel', parameters: { export_type: 'all', project_name: 'DSE Precision Analysis' }, position: { x: 1250, y: 250 } },
        ],
        edges: [
          // ImageInput → ESRGAN → 3개 병렬 처리 (Table Detector, eDOCr2, OCR Ensemble)
          { id: 'e0', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e1', source: 'esrgan_1', target: 'tabledetector_1' },
          { id: 'e2', source: 'esrgan_1', target: 'edocr2_1' },
          { id: 'e3', source: 'esrgan_1', target: 'ocr_ensemble_1' },
          // 병렬 결과 → AI BOM
          { id: 'e4', source: 'esrgan_1', target: 'aibom_1' },
          { id: 'e5', source: 'tabledetector_1', target: 'aibom_1' },
          { id: 'e6', source: 'edocr2_1', target: 'aibom_1' },
          { id: 'e7', source: 'ocr_ensemble_1', target: 'aibom_1' },
          // AI BOM → 분석 (병렬)
          { id: 'e8', source: 'aibom_1', target: 'skinmodel_1' },
          { id: 'e9', source: 'aibom_1', target: 'vl_1' },
          // 분석 → Merge
          { id: 'e10', source: 'skinmodel_1', target: 'merge_1' },
          { id: 'e11', source: 'vl_1', target: 'merge_1' },
          // Merge → Excel
          { id: 'e12', source: 'merge_1', target: 'excelexport_1' },
        ],
      },
    },

    // ============ BASIC TEMPLATES ============
    {
      nameKey: 'speedPipeline',
      descKey: 'speedPipelineDesc',
      useCaseKey: 'speedPipelineUseCase',
      estimatedTime: '8-12s',
      accuracy: '94%',
      category: 'basic',
      workflow: {
        name: 'Speed Pipeline',
        description: 'Fast pipeline with AI BOM Human-in-the-Loop verification',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 100 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.5, imgsz: 640 }, position: { x: 350, y: 100 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: { features: ['symbol_detection', 'human_verification'] }, position: { x: 600, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'Korean OCR', parameters: {}, position: { x: 850, y: 100 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'aibom_1', target: 'edocr2_1' },
        ],
      },
    },
    {
      nameKey: 'basicOCR',
      descKey: 'basicOCRDesc',
      useCaseKey: 'basicOCRUseCase',
      estimatedTime: '10-15s',
      accuracy: '95%',
      category: 'basic',
      workflow: {
        name: 'Basic OCR Pipeline',
        description: 'OCR workflow with AI BOM Human-in-the-Loop and tolerance analysis',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 100 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.5 }, position: { x: 350, y: 100 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: { features: ['symbol_detection', 'human_verification'] }, position: { x: 600, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'Korean OCR', parameters: {}, position: { x: 850, y: 100 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: 'Tolerance Analysis', parameters: {}, position: { x: 1100, y: 100 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'aibom_1', target: 'edocr2_1' },
          { id: 'e5', source: 'edocr2_1', target: 'skinmodel_1' },
        ],
      },
    },

    // ============ ADVANCED TEMPLATES ============
    {
      nameKey: 'accuracyPipeline',
      descKey: 'accuracyPipelineDesc',
      useCaseKey: 'accuracyPipelineUseCase',
      estimatedTime: '15-20s',
      accuracy: '97%',
      category: 'advanced',
      workflow: {
        name: 'Accuracy Pipeline',
        description: 'High accuracy with AI BOM Human-in-the-Loop, dual OCR and segmentation',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 100 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.35, imgsz: 1280 }, position: { x: 300, y: 100 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: { features: ['symbol_detection', 'vlm_auto_classification', 'human_verification'] }, position: { x: 500, y: 100 } },
          { id: 'edgnet_1', type: 'edgnet', label: 'Edge Segmentation', parameters: { threshold: 0.5 }, position: { x: 700, y: 100 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'Korean OCR', parameters: {}, position: { x: 900, y: 50 } },
          { id: 'paddleocr_1', type: 'paddleocr', label: 'PaddleOCR', parameters: { lang: 'en' }, position: { x: 900, y: 150 } },
          { id: 'merge_1', type: 'merge', label: 'Merge Results', parameters: {}, position: { x: 1100, y: 100 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'aibom_1', target: 'edgnet_1' },
          { id: 'e5', source: 'edgnet_1', target: 'edocr2_1' },
          { id: 'e6', source: 'edgnet_1', target: 'paddleocr_1' },
          { id: 'e7', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e8', source: 'paddleocr_1', target: 'merge_1' },
        ],
      },
    },
    {
      nameKey: 'ocrEnsemble',
      descKey: 'ocrEnsembleDesc',
      useCaseKey: 'ocrEnsembleUseCase',
      estimatedTime: '18-25s',
      accuracy: '98%',
      category: 'advanced',
      workflow: {
        name: 'OCR Ensemble Pipeline',
        description: 'AI BOM Human-in-the-Loop with 4-engine OCR ensemble voting and tolerance analysis',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 150 } },
          { id: 'esrgan_1', type: 'esrgan', label: 'ESRGAN Upscale', parameters: { scale: 2 }, position: { x: 300, y: 150 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.3, imgsz: 1280 }, position: { x: 500, y: 150 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: { features: ['symbol_detection', 'vlm_auto_classification', 'human_verification'] }, position: { x: 700, y: 150 } },
          { id: 'ocr_ensemble_1', type: 'ocr_ensemble', label: 'OCR Ensemble (4-way)', parameters: {}, position: { x: 950, y: 50 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'Dimension OCR', parameters: {}, position: { x: 950, y: 250 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: 'Tolerance Analysis', parameters: {}, position: { x: 1200, y: 250 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'esrgan_1' },
          { id: 'e2', source: 'esrgan_1', target: 'yolo_1' },
          { id: 'e3', source: 'esrgan_1', target: 'aibom_1' },
          { id: 'e4', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e5', source: 'aibom_1', target: 'ocr_ensemble_1' },
          { id: 'e6', source: 'aibom_1', target: 'edocr2_1' },
          { id: 'e7', source: 'edocr2_1', target: 'skinmodel_1' },
        ],
      },
    },
    {
      nameKey: 'multiOCRComparison',
      descKey: 'multiOCRComparisonDesc',
      useCaseKey: 'multiOCRComparisonUseCase',
      estimatedTime: '18-25s',
      accuracy: '96%',
      category: 'advanced',
      workflow: {
        name: 'Multi-OCR Comparison',
        description: 'AI BOM Human-in-the-Loop with 4 OCR engine comparison',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.4 }, position: { x: 300, y: 200 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: { features: ['symbol_detection', 'human_verification'] }, position: { x: 500, y: 200 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'eDOCr2', parameters: {}, position: { x: 750, y: 80 } },
          { id: 'paddleocr_1', type: 'paddleocr', label: 'PaddleOCR', parameters: {}, position: { x: 750, y: 160 } },
          { id: 'tesseract_1', type: 'tesseract', label: 'Tesseract', parameters: {}, position: { x: 750, y: 240 } },
          { id: 'easyocr_1', type: 'easyocr', label: 'EasyOCR', parameters: { languages: ['en'] }, position: { x: 750, y: 320 } },
          { id: 'merge_1', type: 'merge', label: 'Compare & Merge', parameters: {}, position: { x: 1000, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'aibom_1', target: 'edocr2_1' },
          { id: 'e5', source: 'aibom_1', target: 'paddleocr_1' },
          { id: 'e6', source: 'aibom_1', target: 'tesseract_1' },
          { id: 'e7', source: 'aibom_1', target: 'easyocr_1' },
          { id: 'e8', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e9', source: 'paddleocr_1', target: 'merge_1' },
          { id: 'e10', source: 'tesseract_1', target: 'merge_1' },
          { id: 'e11', source: 'easyocr_1', target: 'merge_1' },
        ],
      },
    },

    // Full OCR Benchmark - 5 OCR engines (active)
    {
      nameKey: 'fullOCRBenchmark',
      descKey: 'fullOCRBenchmarkDesc',
      useCaseKey: 'fullOCRBenchmarkUseCase',
      estimatedTime: '15-25s',
      accuracy: 'Comparison',
      category: 'benchmark',
      workflow: {
        name: 'Full OCR Benchmark',
        description: 'Compare 5 active OCR engines side-by-side for comprehensive evaluation',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 50, y: 200 } },
          // Active OCR engines
          { id: 'edocr2_1', type: 'edocr2', label: 'eDOCr2 (Drawing)', parameters: {}, position: { x: 350, y: 50 } },
          { id: 'paddleocr_1', type: 'paddleocr', label: 'PaddleOCR (Fast)', parameters: { lang: 'en' }, position: { x: 350, y: 130 } },
          { id: 'tesseract_1', type: 'tesseract', label: 'Tesseract (General)', parameters: { lang: 'eng' }, position: { x: 350, y: 210 } },
          { id: 'easyocr_1', type: 'easyocr', label: 'EasyOCR (Multilingual)', parameters: { languages: ['en'] }, position: { x: 350, y: 290 } },
          { id: 'ocr_ensemble_1', type: 'ocr_ensemble', label: 'Ensemble (Voting)', parameters: {}, position: { x: 350, y: 370 } },
          // Merge all results
          { id: 'merge_1', type: 'merge', label: 'All OCR Results', parameters: {}, position: { x: 650, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'edocr2_1' },
          { id: 'e2', source: 'imageinput_1', target: 'paddleocr_1' },
          { id: 'e3', source: 'imageinput_1', target: 'tesseract_1' },
          { id: 'e4', source: 'imageinput_1', target: 'easyocr_1' },
          { id: 'e5', source: 'imageinput_1', target: 'ocr_ensemble_1' },
          { id: 'e6', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e7', source: 'paddleocr_1', target: 'merge_1' },
          { id: 'e8', source: 'tesseract_1', target: 'merge_1' },
          { id: 'e9', source: 'easyocr_1', target: 'merge_1' },
          { id: 'e10', source: 'ocr_ensemble_1', target: 'merge_1' },
        ],
      },
    },

    // Detection Benchmark - YOLO model_type variants
    {
      nameKey: 'detectionBenchmark',
      descKey: 'detectionBenchmarkDesc',
      useCaseKey: 'detectionBenchmarkUseCase',
      estimatedTime: '10-15s',
      accuracy: 'Comparison',
      category: 'benchmark',
      workflow: {
        name: 'Detection Benchmark',
        description: 'Compare YOLO models: engineering vs P&ID specialized detection',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 50, y: 200 } },
          // YOLO variants with different model types
          { id: 'yolo_1', type: 'yolo', label: 'YOLO (Engineering)', parameters: { model_type: 'engineering', confidence: 0.35, imgsz: 1280 }, position: { x: 350, y: 100 } },
          { id: 'yolo_2', type: 'yolo', label: 'YOLO (BOM Detector)', parameters: { model_type: 'bom_detector', confidence: 0.4, imgsz: 1024 }, position: { x: 350, y: 180 } },
          { id: 'yolo_3', type: 'yolo', label: 'YOLO (P&ID)', parameters: { model_type: 'pid_class_aware', confidence: 0.25, imgsz: 640, use_sahi: true }, position: { x: 350, y: 260 } },
          { id: 'yolo_4', type: 'yolo', label: 'YOLO (P&ID Agnostic)', parameters: { model_type: 'pid_class_agnostic', confidence: 0.25, imgsz: 640, use_sahi: true }, position: { x: 350, y: 340 } },
          // Merge results
          { id: 'merge_1', type: 'merge', label: 'Detection Comparison', parameters: {}, position: { x: 650, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'yolo_2' },
          { id: 'e3', source: 'imageinput_1', target: 'yolo_3' },
          { id: 'e4', source: 'imageinput_1', target: 'yolo_4' },
          { id: 'e5', source: 'yolo_1', target: 'merge_1' },
          { id: 'e6', source: 'yolo_2', target: 'merge_1' },
          { id: 'e7', source: 'yolo_3', target: 'merge_1' },
          { id: 'e8', source: 'yolo_4', target: 'merge_1' },
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
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { model_type: 'engineering', confidence: 0.35 }, position: { x: 250, y: 100 } },
          { id: 'yolo_2', type: 'yolo', label: 'YOLO P&ID Detection', parameters: { model_type: 'pid_class_aware', confidence: 0.25, use_sahi: true }, position: { x: 250, y: 300 } },
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
          { id: 'e2', source: 'imageinput_1', target: 'yolo_2' },
          { id: 'e3', source: 'imageinput_1', target: 'linedetector_1' },
          { id: 'e4', source: 'yolo_1', target: 'edocr2_1' },
          { id: 'e5', source: 'edocr2_1', target: 'skinmodel_1' },
          { id: 'e6', source: 'yolo_2', target: 'pidanalyzer_1' },
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
      estimatedTime: '12-18s',
      accuracy: '96%',
      category: 'ai',
      workflow: {
        name: 'VL-Assisted Analysis',
        description: 'AI BOM Human-in-the-Loop with Vision-Language AI for intelligent drawing understanding',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Drawing Input', parameters: {}, position: { x: 100, y: 150 } },
          { id: 'textinput_1', type: 'textinput', label: 'Analysis Prompt', parameters: { text: 'Analyze this engineering drawing and extract all dimensions' }, position: { x: 100, y: 300 } },
          { id: 'vl_1', type: 'vl', label: 'VL Model Analysis', parameters: {}, position: { x: 400, y: 200 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.4 }, position: { x: 650, y: 200 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: { features: ['symbol_detection', 'vlm_auto_classification', 'human_verification'] }, position: { x: 900, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'vl_1' },
          { id: 'e2', source: 'textinput_1', target: 'vl_1' },
          { id: 'e3', source: 'vl_1', target: 'yolo_1' },
          { id: 'e4', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e5', source: 'yolo_1', target: 'aibom_1' },
        ],
      },
    },
    {
      nameKey: 'knowledgeEnhanced',
      descKey: 'knowledgeEnhancedDesc',
      useCaseKey: 'knowledgeEnhancedUseCase',
      estimatedTime: '15-20s',
      accuracy: '95%',
      category: 'ai',
      workflow: {
        name: 'AI-Enhanced Analysis',
        description: 'AI BOM Human-in-the-Loop with Vision-Language AI for context-aware analysis',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Drawing Input', parameters: {}, position: { x: 100, y: 150 } },
          { id: 'textinput_1', type: 'textinput', label: 'Query', parameters: { text: 'Explain the GD&T symbols and tolerances in this drawing' }, position: { x: 100, y: 300 } },
          { id: 'yolo_1', type: 'yolo', label: 'Symbol Detection', parameters: { confidence: 0.4 }, position: { x: 350, y: 150 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: { features: ['symbol_detection', 'human_verification'] }, position: { x: 550, y: 150 } },
          { id: 'vl_1', type: 'vl', label: 'VL Context Analysis', parameters: {}, position: { x: 350, y: 300 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'OCR', parameters: {}, position: { x: 750, y: 150 } },
          { id: 'merge_1', type: 'merge', label: 'Contextualized Results', parameters: {}, position: { x: 1000, y: 200 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'imageinput_1', target: 'vl_1' },
          { id: 'e5', source: 'textinput_1', target: 'vl_1' },
          { id: 'e6', source: 'aibom_1', target: 'edocr2_1' },
          { id: 'e7', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e8', source: 'vl_1', target: 'merge_1' },
        ],
      },
    },

    // ============ CONTROL FLOW TEMPLATES ============
    {
      nameKey: 'conditionalOCR',
      descKey: 'conditionalOCRDesc',
      useCaseKey: 'conditionalOCRUseCase',
      estimatedTime: '12-18s',
      accuracy: '96%',
      category: 'advanced',
      workflow: {
        name: 'Conditional OCR Pipeline',
        description: 'AI BOM Human-in-the-Loop with intelligent branching based on detection confidence',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 150 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.5 }, position: { x: 300, y: 150 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: { features: ['symbol_detection', 'human_verification'] }, position: { x: 500, y: 150 } },
          { id: 'if_1', type: 'if', label: 'Check Confidence', parameters: { condition: 'confidence > 0.8' }, position: { x: 700, y: 150 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'eDOCr2 (High Conf)', parameters: {}, position: { x: 900, y: 80 } },
          { id: 'ocr_ensemble_1', type: 'ocr_ensemble', label: 'OCR Ensemble (Low Conf)', parameters: {}, position: { x: 900, y: 220 } },
          { id: 'merge_1', type: 'merge', label: 'Merge Results', parameters: {}, position: { x: 1150, y: 150 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'aibom_1', target: 'if_1' },
          { id: 'e5', source: 'if_1', target: 'edocr2_1', sourceHandle: 'true' },
          { id: 'e6', source: 'if_1', target: 'ocr_ensemble_1', sourceHandle: 'false' },
          { id: 'e7', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e8', source: 'ocr_ensemble_1', target: 'merge_1' },
        ],
      },
    },
    {
      nameKey: 'loopDetection',
      descKey: 'loopDetectionDesc',
      useCaseKey: 'loopDetectionUseCase',
      estimatedTime: '20-30s',
      accuracy: '98%',
      category: 'advanced',
      workflow: {
        name: 'Loop Detection Pipeline',
        description: 'AI BOM Human-in-the-Loop with iterative processing for maximum accuracy',
        nodes: [
          { id: 'imageinput_1', type: 'imageinput', label: 'Image Input', parameters: {}, position: { x: 100, y: 150 } },
          { id: 'yolo_1', type: 'yolo', label: 'YOLO Detection', parameters: { confidence: 0.35 }, position: { x: 300, y: 150 } },
          { id: 'aibom_1', type: 'blueprint-ai-bom', label: 'Verification (AI BOM)', parameters: { features: ['symbol_detection', 'human_verification'] }, position: { x: 500, y: 150 } },
          { id: 'loop_1', type: 'loop', label: 'For Each Detection', parameters: { iterator: 'detections' }, position: { x: 700, y: 150 } },
          { id: 'edocr2_1', type: 'edocr2', label: 'OCR Each Box', parameters: {}, position: { x: 900, y: 150 } },
          { id: 'skinmodel_1', type: 'skinmodel', label: 'Tolerance Analysis', parameters: {}, position: { x: 1100, y: 150 } },
        ],
        edges: [
          { id: 'e1', source: 'imageinput_1', target: 'yolo_1' },
          { id: 'e2', source: 'imageinput_1', target: 'aibom_1' },
          { id: 'e3', source: 'yolo_1', target: 'aibom_1' },
          { id: 'e4', source: 'aibom_1', target: 'loop_1' },
          { id: 'e5', source: 'loop_1', target: 'edocr2_1' },
          { id: 'e6', source: 'edocr2_1', target: 'skinmodel_1' },
        ],
      },
    },
  ];

  const handleLoadTemplate = (template: TemplateInfo) => {
    loadWorkflow(template.workflow);
    navigate('/blueprintflow/builder');
  };


  const categoryInfo: Record<TemplateCategory, { icon: typeof Star; color: string; label: string; shortLabel: string }> = {
    all: { icon: Sparkles, color: 'from-gray-500 to-gray-600', label: t('blueprintflow.allTemplates', '전체'), shortLabel: t('blueprintflow.all', '전체') },
    featured: { icon: Star, color: 'from-amber-500 to-orange-500', label: t('blueprintflow.featuredTemplates'), shortLabel: '⭐ Featured' },
    techcross: { icon: Ship, color: 'from-sky-500 to-blue-600', label: t('blueprintflow.techcrossTemplates'), shortLabel: '🚢 TECHCROSS' },
    dsebearing: { icon: Cog, color: 'from-amber-500 to-orange-600', label: t('blueprintflow.dsebearingTemplates'), shortLabel: '⚙️ DSE Bearing' },
    basic: { icon: Zap, color: 'from-green-500 to-emerald-500', label: t('blueprintflow.basicTemplates'), shortLabel: '⚡ Basic' },
    advanced: { icon: Layers, color: 'from-blue-500 to-indigo-500', label: t('blueprintflow.advancedTemplates'), shortLabel: '🔧 Advanced' },
    pid: { icon: GitBranch, color: 'from-purple-500 to-pink-500', label: t('blueprintflow.pidTemplates'), shortLabel: '🔀 P&ID' },
    ai: { icon: Brain, color: 'from-cyan-500 to-teal-500', label: t('blueprintflow.aiTemplates'), shortLabel: '🧠 AI' },
    benchmark: { icon: FlaskConical, color: 'from-rose-500 to-red-500', label: t('blueprintflow.benchmarkTemplates'), shortLabel: '🧪 Benchmark' },
  };

  // Get templates for active tab
  const getFilteredTemplates = (): TemplateInfo[] => {
    if (activeTab === 'all') return templates;
    if (activeTab === 'featured') return templates.filter(t => t.featured);
    return templates.filter(t => t.category === activeTab);
  };

  const filteredTemplates = getFilteredTemplates();

  // Count templates per category
  const getCategoryCount = (category: TemplateCategory): number => {
    if (category === 'all') return templates.length;
    if (category === 'featured') return templates.filter(t => t.featured).length;
    return templates.filter(t => t.category === category).length;
  };

  const tabCategories: TemplateCategory[] = ['all', 'featured', 'techcross', 'dsebearing', 'basic', 'advanced', 'pid', 'ai', 'benchmark'];


  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
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

      {/* Tab Navigation */}
      <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap gap-1 -mb-px overflow-x-auto pb-px">
          {tabCategories.map((category) => {
            const { icon: Icon, shortLabel } = categoryInfo[category];
            const count = getCategoryCount(category);
            const isActive = activeTab === category;

            return (
              <button
                key={category}
                onClick={() => setActiveTab(category)}
                className={`
                  flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all whitespace-nowrap
                  ${isActive
                    ? `border-cyan-500 text-cyan-600 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-900/20`
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                  }
                `}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-500' : ''}`} />
                <span>{shortLabel}</span>
                <Badge
                  variant={isActive ? 'default' : 'outline'}
                  className={`ml-1 text-xs px-1.5 py-0 ${isActive ? 'bg-cyan-500' : ''}`}
                >
                  {count}
                </Badge>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Tab Header */}
      {activeTab !== 'all' && (
        <div className="flex items-center gap-3 mb-6">
          <div className={`p-2 rounded-lg bg-gradient-to-r ${categoryInfo[activeTab].color}`}>
            {(() => {
              const Icon = categoryInfo[activeTab].icon;
              return <Icon className="w-5 h-5 text-white" />;
            })()}
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {categoryInfo[activeTab].label}
          </h2>
          <Badge variant="outline">{filteredTemplates.length}</Badge>
        </div>
      )}

      {/* Template Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {filteredTemplates.map((template, index) => {
          const { color } = categoryInfo[template.category as TemplateCategory] || categoryInfo.basic;

          return (
            <Card
              key={`${template.nameKey}-${index}`}
              className={`hover:shadow-lg transition-shadow group ${template.featured ? 'ring-2 ring-amber-400 dark:ring-amber-500' : ''}`}
            >
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
          );
        })}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            {t('blueprintflow.noTemplatesInCategory', '이 카테고리에 템플릿이 없습니다.')}
          </p>
        </div>
      )}

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
