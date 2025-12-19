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

// Base node type mapping
export const baseNodeTypes = {
  imageinput: ImageInputNode,
  textinput: TextInputNode,
  yolo: YoloNode,
  edocr2: Edocr2Node,
  edgnet: EdgnetNode,
  skinmodel: SkinmodelNode,
  paddleocr: PaddleocrNode,
  vl: VlNode,
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
    description: 'P&ID 공정도 - YOLO-PID, Line Detector, PID Analyzer 분석용',
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
  }
];

// MiniMap node colors
export const getNodeColor = (nodeType: string | undefined): string => {
  switch (nodeType) {
    case 'imageinput': return '#22c55e';
    case 'yolo': return '#3b82f6';
    case 'edocr2': return '#8b5cf6';
    case 'skinmodel': return '#f59e0b';
    default: return '#6b7280';
  }
};
