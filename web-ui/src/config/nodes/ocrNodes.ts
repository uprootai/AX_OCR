/**
 * OCR Nodes
 * 텍스트 인식 노드 정의 (8개 OCR 엔진)
 */

import type { NodeDefinition } from './types';

export const ocrNodes: Record<string, NodeDefinition> = {
  edocr2: {
    type: 'edocr2',
    label: 'eDOCr2 Korean OCR',
    category: 'ocr',
    color: '#3b82f6',
    icon: 'FileText',
    description: '한국어 텍스트 인식 전문 OCR. 도면의 치수, 공차, 주석 등을 정확하게 읽습니다.',
    inputs: [
      {
        name: 'image',
        type: 'Image | DetectionResult[]',
        description: '📄 도면 이미지 또는 🎯 YOLO 검출 영역',
      },
    ],
    outputs: [
      {
        name: 'text_results',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록 (내용, 위치, 정확도)',
      },
    ],
    parameters: [
      {
        name: 'version',
        type: 'select',
        default: 'v2',
        options: ['v1', 'v2', 'ensemble'],
        description: 'eDOCr 버전 (v1: 5001, v2: 5002, ensemble: 가중 평균 0.6/0.4)',
      },
      {
        name: 'language',
        type: 'select',
        default: 'eng',
        options: ['eng', 'kor', 'jpn', 'chi_sim'],
        description: '인식 언어 (eng: 영어, kor: 한국어, jpn: 일본어, chi_sim: 중국어)',
      },
      {
        name: 'extract_dimensions',
        type: 'boolean',
        default: true,
        description: '치수 정보 추출 (φ476, 10±0.5, R20 등)',
      },
      {
        name: 'extract_gdt',
        type: 'boolean',
        default: true,
        description: 'GD&T 정보 추출 (평행도, 직각도, 위치도 등)',
      },
      {
        name: 'extract_text',
        type: 'boolean',
        default: true,
        description: '텍스트 정보 추출 (도면 번호, 재질, 주석 등)',
      },
      {
        name: 'extract_tables',
        type: 'boolean',
        default: true,
        description: '표 정보 추출 (BOM, 치수 표 등)',
      },
      {
        name: 'cluster_threshold',
        type: 'number',
        default: 20,
        min: 5,
        max: 100,
        step: 5,
        description: '텍스트 클러스터링 임계값 (픽셀 단위)',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: 'OCR 결과 시각화 이미지 생성',
      },
    ],
    examples: [
      'YOLO 검출 → eDOCr2 → 한글/숫자 치수 인식',
      '공차 표기 (±0.05), 주석 텍스트 추출',
    ],
    usageTips: [
      '한국어가 포함된 도면은 language=kor로 설정하세요',
      'YOLO의 검출 영역을 입력으로 받으면 특정 영역만 정밀 분석할 수 있습니다',
      'visualize=true로 설정하면 인식된 텍스트의 위치를 시각적으로 확인할 수 있습니다',
      '⭐ SkinModel 노드와 연결 시 텍스트 위치 정보가 자동으로 활용되어 치수 매칭 정확도가 향상됩니다',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO가 검출한 텍스트 영역만 정밀 분석하여 처리 속도와 정확도를 높입니다',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면 이미지에서 모든 텍스트를 추출합니다',
      },
    ],
  },
  paddleocr: {
    type: 'paddleocr',
    label: 'PaddleOCR',
    category: 'ocr',
    color: '#06b6d4',
    icon: 'FileSearch',
    description: '다국어 지원 OCR. 영어, 숫자 인식에 강점. eDOCr2의 대안으로 사용.',
    inputs: [
      {
        name: 'image',
        type: 'Image | DetectionResult[]',
        description: '📄 도면 이미지 또는 🎯 특정 검출 영역',
      },
    ],
    outputs: [
      {
        name: 'text_results',
        type: 'OCRResult[]',
        description: '📝 인식된 영문/숫자 텍스트 목록',
      },
    ],
    parameters: [
      {
        name: 'lang',
        type: 'select',
        default: 'en',
        options: ['en', 'ch', 'korean', 'japan', 'french'],
        description: '인식 언어',
      },
      {
        name: 'det_db_thresh',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.05,
        description: '텍스트 검출 임계값 (낮을수록 더 많이 검출)',
      },
      {
        name: 'det_db_box_thresh',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05,
        description: '박스 임계값 (높을수록 정확한 박스만)',
      },
      {
        name: 'use_angle_cls',
        type: 'boolean',
        default: true,
        description: '회전된 텍스트 감지 여부 (90도, 180도, 270도)',
      },
      {
        name: 'min_confidence',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05,
        description: '최소 신뢰도 (이 값 이하는 필터링)',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: 'OCR 결과 시각화 이미지 생성 (바운딩 박스 + 텍스트)',
      },
    ],
    examples: [
      '영문 도면 → PaddleOCR → 영어 텍스트 추출',
      'IF 노드로 eDOCr2 실패 시 대안으로 사용',
    ],
    usageTips: [
      '영문/숫자가 많은 도면은 eDOCr2 대신 PaddleOCR을 사용하면 더 정확합니다',
      '✨ visualize=true로 설정하면 인식된 텍스트의 바운딩 박스와 위치를 시각적으로 확인할 수 있습니다',
      'IF 노드와 함께 사용하여 eDOCr2 실패 시 자동 fallback으로 활용할 수 있습니다',
      'SkinModel과 연결 시 텍스트 위치 정보가 자동으로 활용되어 치수 분석 정확도가 향상됩니다',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO가 검출한 텍스트 영역만 정밀 분석하여 처리 속도를 높입니다',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면에서 영문/숫자 텍스트를 추출합니다',
      },
      {
        from: 'edgnet',
        field: 'segmented_image',
        reason: '전처리된 선명한 이미지에서 텍스트를 인식하면 정확도가 향상됩니다',
      },
    ],
  },
  tesseract: {
    type: 'tesseract',
    label: 'Tesseract OCR',
    category: 'ocr',
    color: '#059669',
    icon: 'ScanText',
    description: 'Google Tesseract 기반 OCR. 문서 텍스트 인식, 다국어 지원.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 또는 문서 이미지',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
    ],
    parameters: [
      {
        name: 'lang',
        type: 'select',
        default: 'eng',
        options: ['eng', 'kor', 'jpn', 'chi_sim', 'eng+kor'],
        description: '인식 언어',
      },
      {
        name: 'psm',
        type: 'select',
        default: '3',
        options: ['0', '1', '3', '4', '6', '7', '11', '12', '13'],
        description: 'Page Segmentation Mode (3: 자동, 6: 단일 블록)',
      },
      {
        name: 'output_type',
        type: 'select',
        default: 'data',
        options: ['string', 'data'],
        description: '출력 형식 (string: 텍스트만, data: 위치정보 포함)',
      },
    ],
    examples: [
      'ImageInput → Tesseract → 영문 도면 텍스트 추출',
      'OCR Ensemble의 구성 엔진 (15% 가중치)',
    ],
    usageTips: [
      '💡 다국어 도면은 lang=eng+kor로 설정하세요',
      '💡 OCR Ensemble과 함께 사용하면 정확도가 향상됩니다',
      '💡 psm=6은 단일 텍스트 블록에 적합합니다',
    ],
  },
  trocr: {
    type: 'trocr',
    label: 'TrOCR',
    category: 'ocr',
    color: '#7c3aed',
    icon: 'Wand2',
    description: 'Microsoft TrOCR (Transformer OCR). Scene Text Recognition에 강점.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 텍스트 라인 이미지 (크롭 권장)',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트',
      },
    ],
    parameters: [
      {
        name: 'model_type',
        type: 'select',
        default: 'printed',
        options: ['printed', 'handwritten'],
        description: '모델 타입 (printed: 인쇄체, handwritten: 필기체)',
      },
      {
        name: 'max_length',
        type: 'number',
        default: 64,
        min: 16,
        max: 256,
        step: 16,
        description: '최대 출력 길이',
      },
      {
        name: 'num_beams',
        type: 'number',
        default: 4,
        min: 1,
        max: 10,
        step: 1,
        description: 'Beam Search 빔 수 (높을수록 정확, 느림)',
      },
    ],
    examples: [
      'YOLO 검출 영역 → TrOCR → 개별 텍스트 인식',
      'OCR Ensemble의 구성 엔진 (10% 가중치)',
    ],
    usageTips: [
      '💡 단일 텍스트 라인 이미지에 최적화되어 있습니다',
      '💡 전체 문서는 YOLO로 텍스트 영역 검출 후 개별 처리 권장',
      '💡 손글씨 스타일 텍스트에 handwritten 모델 사용',
    ],
  },
  ocr_ensemble: {
    type: 'ocr_ensemble',
    label: 'OCR Ensemble',
    category: 'ocr',
    color: '#0891b2',
    icon: 'Layers',
    description: '4개 OCR 엔진 가중 투표 앙상블 (eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%)',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'results',
        type: 'EnsembleResult[]',
        description: '📝 앙상블 결과 (가중 투표 기반)',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
      {
        name: 'engine_results',
        type: 'object',
        description: '🔍 각 엔진별 원본 결과',
      },
    ],
    parameters: [
      {
        name: 'edocr2_weight',
        type: 'number',
        default: 0.40,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'eDOCr2 가중치 (기본 40%)',
      },
      {
        name: 'paddleocr_weight',
        type: 'number',
        default: 0.35,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'PaddleOCR 가중치 (기본 35%)',
      },
      {
        name: 'tesseract_weight',
        type: 'number',
        default: 0.15,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'Tesseract 가중치 (기본 15%)',
      },
      {
        name: 'trocr_weight',
        type: 'number',
        default: 0.10,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'TrOCR 가중치 (기본 10%)',
      },
      {
        name: 'similarity_threshold',
        type: 'number',
        default: 0.7,
        min: 0.5,
        max: 1,
        step: 0.05,
        description: '텍스트 유사도 임계값 (결과 그룹화 기준)',
      },
    ],
    examples: [
      'ImageInput → OCR Ensemble → 최고 정확도 OCR 결과',
      'ESRGAN → OCR Ensemble → 저품질 도면도 정확히 인식',
    ],
    usageTips: [
      '⭐ 단일 OCR 엔진보다 훨씬 높은 정확도를 제공합니다',
      '💡 가중치를 조정하여 특정 엔진에 더 높은 신뢰도 부여 가능',
      '💡 여러 엔진이 동의하는 결과는 신뢰도가 더 높습니다',
      '💡 처리 시간이 단일 엔진보다 길지만 정확도가 훨씬 높습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면에서 4개 OCR 엔진으로 텍스트를 추출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '⭐ 업스케일된 이미지로 OCR 정확도를 극대화합니다',
      },
      {
        from: 'edgnet',
        field: 'segmented_image',
        reason: '전처리된 이미지에서 더 정확한 결과를 얻습니다',
      },
    ],
  },
  suryaocr: {
    type: 'suryaocr',
    label: 'Surya OCR',
    category: 'ocr',
    color: '#8b5cf6',
    icon: 'ScanText',
    description: 'Surya OCR - 90+ 언어 지원, 레이아웃 분석, 높은 정확도. 기계 도면에 최적화.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 또는 문서 이미지',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록 (bbox 포함)',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
      {
        name: 'layout',
        type: 'LayoutElement[]',
        description: '📐 레이아웃 요소 (선택적)',
      },
    ],
    parameters: [
      {
        name: 'languages',
        type: 'string',
        default: 'ko,en',
        description: '인식 언어 (쉼표 구분, 90+ 언어 지원)',
      },
      {
        name: 'detect_layout',
        type: 'boolean',
        default: false,
        description: '레이아웃 분석 활성화 (테이블, 단락 감지)',
      },
    ],
    examples: [
      'ImageInput → Surya OCR → 다국어 도면 텍스트 추출',
      'ESRGAN → Surya OCR → 고정밀 OCR',
    ],
    usageTips: [
      '⭐ 기계 도면 OCR에서 가장 높은 정확도를 제공합니다',
      '💡 90+ 언어를 지원하여 다국어 도면에 적합합니다',
      '💡 detect_layout=true로 테이블/단락 구조 분석 가능',
      '💡 DocTR, EasyOCR보다 기술 도면에서 정확도가 높습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면에서 텍스트를 추출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '⭐ 업스케일된 이미지로 OCR 정확도를 극대화합니다',
      },
    ],
  },
  doctr: {
    type: 'doctr',
    label: 'DocTR',
    category: 'ocr',
    color: '#0ea5e9',
    icon: 'FileText',
    description: 'DocTR (Document Text Recognition) - 문서 OCR 특화, 정규화된 bbox 출력.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 문서 또는 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록 (정규화 bbox)',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
    ],
    parameters: [
      {
        name: 'det_arch',
        type: 'select',
        default: 'db_resnet50',
        options: ['db_resnet50', 'db_mobilenet_v3_large', 'linknet_resnet18'],
        description: '텍스트 검출 모델 아키텍처',
      },
      {
        name: 'reco_arch',
        type: 'select',
        default: 'crnn_vgg16_bn',
        options: ['crnn_vgg16_bn', 'crnn_mobilenet_v3_small', 'master', 'sar_resnet31'],
        description: '텍스트 인식 모델 아키텍처',
      },
      {
        name: 'straighten_pages',
        type: 'boolean',
        default: false,
        description: '기울어진 페이지 자동 보정',
      },
      {
        name: 'export_as_xml',
        type: 'boolean',
        default: false,
        description: 'XML 형식으로 내보내기',
      },
    ],
    examples: [
      'ImageInput → DocTR → 문서 텍스트 추출',
      '기울어진 스캔 → DocTR (straighten=true) → 보정된 OCR',
    ],
    usageTips: [
      '💡 문서 OCR에 특화되어 있으며 정확한 bbox를 제공합니다',
      '💡 straighten_pages=true로 기울어진 스캔 보정 가능',
      '💡 db_resnet50이 가장 정확하고, db_mobilenet이 가장 빠릅니다',
      '💡 기계 도면보다는 일반 문서에 더 적합합니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '문서 이미지에서 텍스트를 추출합니다',
      },
    ],
  },
  easyocr: {
    type: 'easyocr',
    label: 'EasyOCR',
    category: 'ocr',
    color: '#22c55e',
    icon: 'Languages',
    description: 'EasyOCR - 80+ 언어 지원, CPU 친화적, 한국어 지원 우수.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 또는 문서 이미지',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
    ],
    parameters: [
      {
        name: 'languages',
        type: 'string',
        default: 'ko,en',
        description: '인식 언어 (쉼표 구분, ko/en/ja/ch_sim 등)',
      },
      {
        name: 'detail',
        type: 'boolean',
        default: true,
        description: '상세 결과 (bbox 포함)',
      },
      {
        name: 'paragraph',
        type: 'boolean',
        default: false,
        description: '문단 단위로 결합',
      },
      {
        name: 'batch_size',
        type: 'number',
        default: 1,
        min: 1,
        max: 32,
        step: 1,
        description: '배치 크기 (높을수록 빠름, 메모리 증가)',
      },
    ],
    examples: [
      'ImageInput → EasyOCR → 한국어 도면 텍스트 추출',
      'CPU 환경에서 빠른 OCR 처리',
    ],
    usageTips: [
      '💡 CPU에서도 빠르게 동작하여 GPU 없는 환경에 적합합니다',
      '💡 80+ 언어를 지원하며 한국어 인식이 우수합니다',
      '💡 paragraph=true로 문단 단위 텍스트 결합 가능',
      '⚠️ 작은 글자나 기술 용어는 Surya OCR보다 정확도가 낮을 수 있습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '다국어 도면에서 텍스트를 추출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '저해상도 이미지 업스케일 후 OCR 정확도 향상',
      },
    ],
  },
};
