/**
 * BlueprintFlow Constants
 * 상수 및 샘플 데이터
 */

import type { SampleFile } from '../../components/upload/SampleFileGrid';
import {
  ImageInputNode,
  TextInputNode,
  YoloNode,
  Edocr2Node,
  EdgnetNode,
  SkinmodelNode,
  PaddleocrNode,
  VlNode,
  IfNode,
  LoopNode,
  MergeNode,
} from '../../components/blueprintflow/nodes';
import DynamicNode from '../../components/blueprintflow/nodes/DynamicNode';

// Base node type mapping
export const baseNodeTypes = {
  // Input nodes
  imageinput: ImageInputNode,
  textinput: TextInputNode,

  // Detection nodes
  yolo: YoloNode,
  table_detector: DynamicNode,

  // OCR nodes
  edocr2: Edocr2Node,
  paddleocr: PaddleocrNode,
  tesseract: DynamicNode,
  trocr: DynamicNode,
  'ocr-ensemble': DynamicNode,
  suryaocr: DynamicNode,
  doctr: DynamicNode,
  easyocr: DynamicNode,

  // Segmentation nodes
  edgnet: EdgnetNode,
  'line-detector': DynamicNode,

  // Preprocessing nodes
  esrgan: DynamicNode,

  // Analysis nodes
  skinmodel: SkinmodelNode,
  'pid-analyzer': DynamicNode,
  'design-checker': DynamicNode,
  'blueprint-ai-bom': DynamicNode,
  gt_comparison: DynamicNode,
  'pid-composer': DynamicNode,
  'pid-features': DynamicNode,
  'pdf-export': DynamicNode,
  'verification-queue': DynamicNode,

  // DSE Bearing analysis nodes
  titleblock: DynamicNode,
  partslist: DynamicNode,
  dimensionparser: DynamicNode,
  bommatcher: DynamicNode,
  quotegenerator: DynamicNode,

  // Knowledge nodes
  knowledge: DynamicNode,

  // AI nodes
  vl: VlNode,

  // Control nodes
  if: IfNode,
  loop: LoopNode,
  merge: MergeNode,
};

// Node ID generator
let nodeId = 0;
export const getId = () => `node_${nodeId++}`;
export const resetNodeId = () => { nodeId = 0; };

// BlueprintFlow sample images
export const BLUEPRINT_SAMPLES: SampleFile[] = [
  {
    id: 'sample-1',
    name: 'Intermediate Shaft (Image)',
    path: '/samples/sample2_interm_shaft.jpg',
    description: '선박 중간축 도면 - 모든 분석 지원',
    type: 'image',
    recommended: true
  },
  {
    id: 'sample-2',
    name: 'S60ME-C Shaft (Korean)',
    path: '/samples/sample3_s60me_shaft.jpg',
    description: 'S60ME-C 중간축 도면 - 한글 포함',
    type: 'image'
  },
  {
    id: 'sample-3',
    name: 'P&ID Diagram (Eastman)',
    path: '/samples/sample6_pid_diagram.png',
    description: 'P&ID 공정도 - YOLO (P&ID 모델), Line Detector, PID Analyzer 분석용',
    type: 'image'
  },
  {
    id: 'sample-7',
    name: 'MCP Panel Body (BOM)',
    path: '/samples/sample7_mcp_panel_body.jpg',
    description: '전기 제어판 도면 - BOM 부품 검출용',
    type: 'image'
  },
  {
    id: 'sample-8',
    name: 'Control Panel 1',
    path: '/samples/sample8_blueprint_31.jpg',
    description: '제어판 도면 1 - BOM 부품 검출용',
    type: 'image'
  },
  {
    id: 'sample-9',
    name: 'Control Panel 2',
    path: '/samples/sample9_blueprint_35.jpg',
    description: '제어판 도면 2 - BOM 부품 검출용',
    type: 'image'
  },
  {
    id: 'sample-bwms',
    name: 'BWMS P&ID (SIGNAL 영역)',
    path: '/samples/bwms_pid_sample.png',
    description: 'BWMS 시스템 P&ID - SIGNAL FOR BWMS 점선 영역 검출 테스트용',
    type: 'image',
    recommended: true
  },
  {
    id: 'dse-bearing-assy',
    name: 'DSE T1 Bearing ASSY',
    path: '/samples/dse_bearing_assy_t1.png',
    description: 'DSE Bearing T1 조립도 (360x190) - Title Block, Parts List, 치수 포함',
    type: 'image',
    recommended: true
  },
  {
    id: 'dse-ring-assy',
    name: 'DSE Ring ASSY (T1)',
    path: '/samples/dse_ring_assy_t1.png',
    description: 'DSE Bearing Ring ASSY T1 - 링 조립 도면',
    type: 'image'
  },
  {
    id: 'dse-casing-assy',
    name: 'DSE Casing ASSY (T1)',
    path: '/samples/dse_casing_assy_t1.png',
    description: 'DSE Bearing Casing ASSY T1 - 케이싱 조립 도면',
    type: 'image'
  },
  {
    id: 'dse-thrust-bearing',
    name: 'DSE Thrust Bearing ASSY',
    path: '/samples/dse_thrust_bearing_assy.png',
    description: 'DSE Thrust Bearing ASSY (OD670xID440) - 스러스트 베어링 도면',
    type: 'image'
  }
];

// MiniMap node colors (by category)
export const getNodeColor = (nodeType: string | undefined): string => {
  switch (nodeType) {
    // Input - green
    case 'imageinput':
    case 'textinput':
      return '#22c55e';

    // Detection - blue
    case 'yolo':
    case 'table_detector':
      return '#3b82f6';

    // OCR - purple
    case 'edocr2':
    case 'paddleocr':
    case 'tesseract':
    case 'trocr':
    case 'ocr-ensemble':
    case 'suryaocr':
    case 'doctr':
    case 'easyocr':
      return '#8b5cf6';

    // Segmentation - cyan
    case 'edgnet':
    case 'line-detector':
      return '#06b6d4';

    // Preprocessing - pink
    case 'esrgan':
      return '#ec4899';

    // Analysis - orange/amber
    case 'skinmodel':
    case 'pid-analyzer':
    case 'design-checker':
    case 'blueprint-ai-bom':
    case 'gt_comparison':
    case 'pid-composer':
    case 'pid-features':
    case 'pdf-export':
    case 'verification-queue':
    case 'titleblock':
    case 'partslist':
    case 'dimensionparser':
    case 'bommatcher':
    case 'quotegenerator':
      return '#f59e0b';

    // Knowledge - teal
    case 'knowledge':
      return '#14b8a6';

    // AI - indigo
    case 'vl':
      return '#6366f1';

    // Control - gray
    case 'if':
    case 'loop':
    case 'merge':
      return '#64748b';

    default:
      return '#6b7280';
  }
};
