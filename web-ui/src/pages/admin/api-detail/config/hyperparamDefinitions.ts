/**
 * Hyperparameter definitions for each API service
 * Defines the UI controls, validation, and descriptions for each parameter
 */

export interface HyperparamDefinitionItem {
  key?: string;
  label: string;
  type: 'number' | 'boolean' | 'select' | 'text';
  min?: number;
  max?: number;
  step?: number;
  options?: { value: string; label: string }[];
  description: string;
}

export const HYPERPARAM_DEFINITIONS: Record<string, HyperparamDefinitionItem[]> = {
  yolo: [
    { label: '신뢰도 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '검출 객체의 최소 신뢰도 (0-1)' },
    { label: 'IoU 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '겹치는 박스 제거 기준' },
    { label: '입력 이미지 크기', type: 'select', options: [{ value: '640', label: '640px (빠름)' }, { value: '1280', label: '1280px (균형)' }, { value: '1920', label: '1920px (정밀)' }], description: 'YOLO 입력 크기' },
    { label: '모델 타입', type: 'select', options: [{ value: 'engineering', label: '기계도면 (14종)' }, { value: 'bom_detector', label: '전력설비 (27종)' }, { value: 'pid_class_aware', label: 'P&ID 분류 (32종)' }, { value: 'pid_class_agnostic', label: 'P&ID 위치만' }], description: 'YOLO 모델 선택' },
    { label: 'SAHI 슬라이싱', type: 'boolean', description: 'SAHI 슬라이싱 (P&ID 모델은 자동 활성화)' },
    { label: '슬라이스 크기', type: 'select', options: [{ value: '256', label: '256px (최정밀)' }, { value: '512', label: '512px (균형)' }, { value: '768', label: '768px' }, { value: '1024', label: '1024px (빠름)' }], description: 'SAHI 슬라이스 크기' },
    { label: '시각화 생성', type: 'boolean', description: '바운딩 박스 이미지 생성' },
  ],
  edocr2: [
    { label: '치수 추출', type: 'boolean', description: '치수 값, 단위, 공차 정보 추출' },
    { label: 'GD&T 추출', type: 'boolean', description: '기하 공차 기호 인식' },
    { label: '텍스트 추출', type: 'boolean', description: '도면번호, 제목 등 텍스트 블록 추출' },
    { label: '테이블 추출', type: 'boolean', description: '구조화된 표 데이터 추출' },
    { label: '언어 코드', type: 'text', description: 'Tesseract 언어 코드 (eng, kor 등)' },
    { label: '클러스터링 임계값', type: 'number', min: 1, max: 100, step: 1, description: '치수 텍스트 그룹화 거리' },
  ],
  edgnet: [
    { label: '클래스 개수', type: 'number', min: 2, max: 10, step: 1, description: '세그멘테이션 클래스 수' },
    { label: '시각화 생성', type: 'boolean', description: '세그멘테이션 결과 이미지' },
    { label: '그래프 저장', type: 'boolean', description: '노드/엣지 그래프 데이터 저장' },
  ],
  line_detector: [
    { key: 'method', label: '검출 방법', type: 'select', options: [{ value: 'lsd', label: 'LSD (정밀)' }, { value: 'hough', label: 'Hough (빠름)' }, { value: 'combined', label: 'Combined (최고 정확도)' }], description: '라인 검출 알고리즘' },
    { key: 'min_length', label: '최소 라인 길이', type: 'number', min: 0, max: 500, step: 10, description: '최소 라인 픽셀 길이 (0=필터링 안함)' },
    { key: 'max_lines', label: '최대 라인 수', type: 'number', min: 0, max: 5000, step: 100, description: '최대 라인 수 제한 (0=제한 없음)' },
    { key: 'merge_threshold', label: '병합 거리', type: 'number', min: 5, max: 50, step: 5, description: '동일선상 라인 병합 거리 (픽셀)' },
    { key: 'classify_types', label: '타입 분류', type: 'boolean', description: '배관 vs 신호선 분류' },
    { key: 'classify_colors', label: '색상 분류', type: 'boolean', description: '색상 기반 라인 분류' },
    { key: 'classify_styles', label: '스타일 분류', type: 'boolean', description: '실선/점선/일점쇄선 분류' },
    { key: 'detect_intersections', label: '교차점 검출', type: 'boolean', description: '라인 교차점 검출' },
    { key: 'detect_regions', label: '영역 검출', type: 'boolean', description: '점선 박스 영역 검출 (SIGNAL FOR BWMS 등)' },
    { key: 'region_line_styles', label: '영역 라인 스타일', type: 'text', description: '영역 검출에 사용할 스타일 (쉼표 구분)' },
    { key: 'min_region_area', label: '최소 영역 크기', type: 'number', min: 1000, max: 100000, step: 1000, description: '최소 영역 크기 (픽셀^2)' },
    { key: 'visualize', label: '시각화 생성', type: 'boolean', description: '라인 시각화 이미지 생성' },
    { key: 'visualize_regions', label: '영역 시각화', type: 'boolean', description: '검출된 영역 시각화 포함' },
  ],
  paddleocr: [
    { label: '텍스트 검출 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '텍스트 검출 감도' },
    { label: '박스 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '바운딩 박스 신뢰도' },
    { label: '최소 신뢰도', type: 'number', min: 0, max: 1, step: 0.05, description: '인식 결과 필터링' },
    { label: '회전 텍스트 감지', type: 'boolean', description: '텍스트 방향 자동 보정' },
  ],
  tesseract: [
    { label: '언어', type: 'select', options: [{ value: 'kor', label: '한국어' }, { value: 'eng', label: '영어' }, { value: 'kor+eng', label: '한영 혼합' }], description: '인식 언어' },
    { label: 'PSM 모드', type: 'select', options: [{ value: '3', label: '자동 페이지 분할' }, { value: '6', label: '단일 블록' }, { value: '11', label: '희소 텍스트' }], description: '페이지 분할 모드' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
  ],
  trocr: [
    { label: '모델 크기', type: 'select', options: [{ value: 'base', label: 'Base (빠름)' }, { value: 'large', label: 'Large (정밀)' }], description: 'TrOCR 모델 크기' },
    { label: '최대 길이', type: 'number', min: 16, max: 128, step: 8, description: '최대 토큰 길이' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
  ],
  ocr_ensemble: [
    { label: '엔진 선택', type: 'select', options: [{ value: 'all', label: '전체 엔진' }, { value: 'fast', label: '빠른 엔진만' }, { value: 'accurate', label: '정밀 엔진만' }], description: '사용할 OCR 엔진 조합' },
    { label: '투표 방식', type: 'select', options: [{ value: 'weighted', label: '가중 투표' }, { value: 'majority', label: '다수결' }], description: '앙상블 투표 방식' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
  ],
  surya_ocr: [
    { label: '언어', type: 'select', options: [{ value: 'ko', label: '한국어' }, { value: 'en', label: '영어' }, { value: 'ja', label: '일본어' }, { value: 'zh', label: '중국어' }], description: '인식 언어' },
    { label: '레이아웃 분석', type: 'boolean', description: '문서 레이아웃 분석 활성화' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
  ],
  doctr: [
    { label: '텍스트 검출 모델', type: 'select', options: [{ value: 'db_resnet50', label: 'DB ResNet50' }, { value: 'linknet_resnet18', label: 'LinkNet ResNet18' }], description: '텍스트 검출 모델 선택' },
    { label: '인식 모델', type: 'select', options: [{ value: 'crnn_vgg16_bn', label: 'CRNN VGG16' }, { value: 'master', label: 'MASTER' }], description: '텍스트 인식 모델 선택' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
  ],
  easyocr: [
    { label: '언어', type: 'select', options: [{ value: 'ko', label: '한국어' }, { value: 'en', label: '영어' }, { value: 'ja', label: '일본어' }, { value: 'ch_sim', label: '중국어 간체' }], description: '인식 언어' },
    { label: '최소 신뢰도', type: 'number', min: 0, max: 1, step: 0.05, description: '최소 인식 신뢰도' },
    { label: '단락 분리', type: 'boolean', description: '텍스트를 단락으로 분리' },
  ],
  esrgan: [
    { label: '업스케일 배율', type: 'select', options: [{ value: '2', label: '2x' }, { value: '4', label: '4x' }], description: '이미지 업스케일 배율' },
    { label: '타일 크기', type: 'number', min: 128, max: 512, step: 64, description: '처리 타일 크기 (VRAM 절약)' },
  ],
  skinmodel: [
    { label: '재질', type: 'select', options: [{ value: 'steel', label: '강철' }, { value: 'aluminum', label: '알루미늄' }, { value: 'titanium', label: '티타늄' }, { value: 'plastic', label: '플라스틱' }], description: '부품 재질' },
    { label: '제조 공정', type: 'select', options: [{ value: 'machining', label: '기계 가공' }, { value: 'casting', label: '주조' }, { value: '3d_printing', label: '3D 프린팅' }, { value: 'forging', label: '단조' }], description: '제조 방식' },
    { label: '상관 길이', type: 'number', min: 1, max: 100, step: 0.5, description: '공간적 상관 길이 (mm)' },
  ],
  pid_analyzer: [
    { label: '연결 거리', type: 'number', min: 10, max: 100, step: 5, description: '심볼-라인 연결 거리 임계값 (px)' },
    { label: 'BOM 생성', type: 'boolean', description: 'Bill of Materials 생성' },
    { label: '시각화 생성', type: 'boolean', description: '연결 분석 시각화' },
  ],
  design_checker: [
    { label: '규칙셋', type: 'select', options: [{ value: 'standard', label: '표준 규칙' }, { value: 'strict', label: '엄격 규칙' }, { value: 'custom', label: '사용자 정의' }], description: '적용할 설계 규칙셋' },
    { label: '경고 포함', type: 'boolean', description: '경고 수준 이슈도 보고' },
  ],
  knowledge: [
    { label: '검색 모드', type: 'select', options: [{ value: 'hybrid', label: '하이브리드 (벡터+그래프)' }, { value: 'vector', label: '벡터 검색만' }, { value: 'graph', label: '그래프 검색만' }], description: 'GraphRAG 검색 모드' },
    { label: '검색 깊이', type: 'number', min: 1, max: 5, step: 1, description: '그래프 탐색 깊이' },
    { label: 'Top K', type: 'number', min: 3, max: 20, step: 1, description: '반환할 결과 수' },
  ],
  vl: [
    {
      key: 'model',
      label: '모델',
      type: 'select',
      options: [
        // Local models (항상 표시)
        { value: 'qwen-vl', label: 'Qwen-VL (Local)' },
        { value: 'llava', label: 'LLaVA (Local)' },
        // 외부 API 모델은 동적으로 추가됨 (getEnhancedHyperparamDefs에서 처리)
      ],
      description: 'Vision-Language 모델 선택'
    },
    { key: 'max_tokens', label: '최대 토큰', type: 'number', min: 100, max: 4096, step: 100, description: '생성 최대 토큰 수' },
    { key: 'temperature', label: '온도', type: 'number', min: 0, max: 2, step: 0.1, description: '생성 다양성 (높을수록 다양)' },
  ],
  blueprint_ai_bom: [
    { key: 'symbol_detection', label: '심볼 검출', type: 'boolean', description: 'YOLO 기반 심볼 검출' },
    { key: 'dimension_ocr', label: '치수 OCR', type: 'boolean', description: 'eDOCr2 기반 치수 인식' },
    { key: 'gdt_parsing', label: 'GD&T 파싱', type: 'boolean', description: '기하공차/데이텀 파싱' },
    { key: 'human_in_the_loop', label: 'Human-in-the-Loop', type: 'boolean', description: '수동 검증 큐 활성화' },
    { key: 'confidence_threshold', label: '신뢰도 임계값', type: 'number', min: 0.5, max: 1, step: 0.05, description: '자동 승인 신뢰도 임계값' },
  ],
};
