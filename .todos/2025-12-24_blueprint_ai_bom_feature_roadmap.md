# Blueprint AI BOM - 기능 로드맵

> **목표**: 도면 분석 및 BOM 생성을 위한 기능 확장 계획
> **작성일**: 2025-12-24
> **최종 업데이트**: 2025-12-26
> **버전**: v2.1

---

## 현재 기능 현황 (v9.1)

### 구현 완료된 기능 (20개)

> **2025-12-26 업데이트**: 장기 로드맵 4개 완료 + SSOT 리팩토링 완료
> 현재 `FEATURE_BADGE_CONFIG`에 20개 기능 정의됨

**기존 7개 + 단기 3개 + 장기 4개 + 중기 4개(미구현) + 기타 2개 = 20개**

### 완료된 핵심 기능 (15개)

| # | 기능 ID | 기능명 | 설명 | 관련 노드 | 상태 |
|---|---------|--------|------|-----------|------|
| 1 | `symbol_detection` | 🎯 심볼 검출 | YOLO로 부품/심볼 위치 검출 | YOLO (model_type) | ✅ 완료 |
| 2 | `symbol_verification` | ✅ 심볼 검증 | 검출 결과 승인/거부/수정 | - (Human-in-the-Loop) | ✅ 완료 |
| 3 | `dimension_ocr` | 📏 치수 OCR | 치수값 텍스트 인식 | eDOCr2, PaddleOCR | ✅ 완료 |
| 4 | `dimension_verification` | ✅ 치수 검증 | OCR 결과 승인/거부/수정 | - (Human-in-the-Loop) | ✅ 완료 |
| 5 | `gt_comparison` | 📊 GT 비교 | Ground Truth와 비교 (정밀도/재현율) | - | ✅ 완료 |
| 6 | `bom_generation` | 📋 BOM 생성 | AI 기반 부품 목록 생성 | Blueprint AI BOM | ✅ 완료 |
| 7 | `gdt_parsing` | 📐 GD&T 파싱 | 기하공차 기호 파싱 | SkinModel | ✅ 완료 |

---

## 단기 로드맵 (1-2주)

### 즉시 추가 가능한 기능 (기존 인프라 활용)

#### 1. 📝 표제란 OCR (`title_block_ocr`)

**목적**: 도면의 메타데이터를 자동 추출하여 BOM에 활용

| 항목 | 내용 |
|------|------|
| **추출 대상** | 도면번호, 리비전, 재질, 작성자, 작성일, 스케일, 회사명 |
| **구현 방법** | eDOCr2 + 영역 템플릿 (표제란 위치 학습) |
| **의존 노드** | eDOCr2 (이미 존재) |
| **난이도** | ⭐ 쉬움 |
| **예상 기간** | 3-5일 |

**구현 상세**:
```
1. 표제란 영역 검출 (우하단 고정 위치 또는 YOLO 학습)
2. 영역 내 필드별 OCR (도면번호, 리비전 등)
3. 정규식 기반 후처리 (날짜 형식, 리비전 패턴)
4. BOM 메타데이터에 자동 연결
```

**UI 변경**:
- WorkflowPage에 "📝 표제란 정보" 섹션 추가
- 추출된 메타데이터 편집 UI

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **Werk24** | Commercial API | 독일 기업, 기계 도면 전문 파싱 API. 표제란, GD&T, 치수 자동 추출 | [werk24.io](https://werk24.io) |
| **Azure Document Intelligence** | Cloud API | MS Azure 기반, 커스텀 필드 추출 지원 | [Azure](https://azure.microsoft.com/services/form-recognizer) |
| **Donut** | Open Source | 네이버 클로바, OCR-free Document Understanding Transformer | [GitHub](https://github.com/clovaai/donut) |
| **LayoutLMv3** | Open Source | MS, 문서 레이아웃 이해 + 텍스트 추출 | [HuggingFace](https://huggingface.co/microsoft/layoutlmv3-base) |

---

#### 2. 🔗 P&ID 연결성 분석 (`pid_connectivity`)

**목적**: P&ID 도면에서 기기 간 연결 관계 분석

| 항목 | 내용 |
|------|------|
| **분석 대상** | 배관 연결, 밸브 위치, 기기 입출력 |
| **구현 방법** | Line Detector + PID Analyzer (이미 존재) |
| **의존 노드** | Line Detector (5016), PID Analyzer (5018) |
| **난이도** | ⭐ 쉬움 (통합만 필요) |
| **예상 기간** | 2-3일 |

**구현 상세**:
```
1. Line Detector로 배관선 추출
2. YOLO (P&ID 모드)로 기기/밸브 심볼 검출
3. PID Analyzer로 연결 관계 분석
4. 연결 그래프 시각화
```

**UI 변경**:
- WorkflowPage에 "🔗 P&ID 연결도" 섹션 추가
- 인터랙티브 플로우 다이어그램

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **NetworkX** | Python Library | 그래프 구조 분석, 경로 탐색, 연결 컴포넌트 분석 | [networkx.org](https://networkx.org) |
| **pyDEXPI** | Open Source | P&ID DEXPI 표준 데이터 교환 라이브러리 | [GitHub](https://github.com/Fraunhofer-ITWM/dexpi) |
| **Relationformer** | Research | CVPR 2022, 그래프 신경망 기반 관계 추출 | [arXiv](https://arxiv.org/abs/2203.12562) |
| **PID2Graph** | Dataset | P&ID 심볼-배관 연결 데이터셋 (학습용) | [Kaggle](https://kaggle.com) |
| **MS ISE P&ID Parser** | Reference | MS 산업 솔루션, P&ID 자동 디지털화 사례 | [MS Docs](https://docs.microsoft.com) |

---

#### 3. 📐 선 검출 (`line_detection`)

**목적**: P&ID/전기 도면의 선(배관, 전선) 추적

| 항목 | 내용 |
|------|------|
| **검출 대상** | 배관선, 전선, 연결선, 중심선 |
| **구현 방법** | Line Detector (이미 존재) |
| **의존 노드** | Line Detector (5016) |
| **난이도** | ⭐ 쉬움 (UI 연동만 필요) |
| **예상 기간** | 1-2일 |

**참고**: 현재 WorkflowPage에 "📐 선 검출" 섹션이 이미 존재하나, features 연동 필요

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **OpenCV HoughLinesP** | Library | 확률적 허프 변환 기반 선 검출 | [OpenCV](https://docs.opencv.org) |
| **MLSD** | Open Source | Mobile Line Segment Detection, 실시간 경량 모델 | [GitHub](https://github.com/navervision/mlsd) |
| **LETR** | Research | Transformer 기반 라인 세그먼트 검출 | [arXiv](https://arxiv.org/abs/2101.01909) |
| **DeepLSD** | Research | Deep Line Segment Detection, CVPR 2023 | [GitHub](https://github.com/cvg/DeepLSD) |

---

## 중기 로드맵 (2-4주)

### 새 모델/로직 개발 필요

#### 4. 🔩 용접 기호 파싱 (`welding_symbol_parsing`)

**목적**: 조립도/가공도의 용접 사양 자동 추출

| 항목 | 내용 |
|------|------|
| **파싱 대상** | 용접 타입, 크기, 깊이, 필렛/그루브, 현장/공장 |
| **구현 방법** | YOLO 학습 + OCR + 규칙 기반 파싱 |
| **의존 노드** | 신규 WeldingSymbol 노드 필요 |
| **난이도** | ⭐⭐ 중간 |
| **예상 기간** | 2주 |

**용접 기호 구조**:
```
        ┌─────────────────────────────┐
        │     용접 기호 구조           │
        ├─────────────────────────────┤
        │         ╱╲                  │
        │   ─────/  \─────  (화살표)  │
        │        ╲  ╱                  │
        │  [크기] │ [타입] │ [깊이]    │
        │         ↓                   │
        │    (기준선)                  │
        └─────────────────────────────┘
```

**학습 데이터 필요**:
- 용접 기호 이미지 500+ 장
- 바운딩 박스 + 타입 라벨링

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **Werk24** | Commercial API | 용접 기호 파싱 지원, ISO 2553 표준 | [werk24.io](https://werk24.io) |
| **YOLOv8-WD** | Research | 용접 결함 검출 특화 YOLO 변형 | [Papers](https://www.mdpi.com) |
| **DSF-YOLO** | Research | 다중 스케일 특징 융합, 용접 심볼 검출 | [arXiv](https://arxiv.org) |
| **LA-YOLO** | Research | 경량화된 어텐션 기반 용접 검출 | [IEEE](https://ieeexplore.ieee.org) |
| **Roboflow** | Platform | 용접 기호 데이터셋 호스팅 및 라벨링 | [roboflow.com](https://roboflow.com) |

---

#### 5. 🪨 표면 거칠기 파싱 (`surface_roughness_parsing`)

**목적**: 표면 거칠기 기호 및 수치 추출

| 항목 | 내용 |
|------|------|
| **파싱 대상** | Ra, Rz, Rmax 값, 가공 방법, 방향 기호 |
| **구현 방법** | 기호 검출 + OCR + 규칙 파싱 |
| **의존 노드** | SkinModel 확장 또는 신규 노드 |
| **난이도** | ⭐⭐ 중간 |
| **예상 기간** | 1.5주 |

**표면 거칠기 기호**:
```
    ╱│
   ╱ │ Ra 3.2
  ╱  │ ────
 ╱───┘
```

**파싱 결과 예시**:
```json
{
  "type": "Ra",
  "value": 3.2,
  "unit": "μm",
  "machining_method": "turning",
  "lay_direction": "parallel"
}
```

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **Werk24** | Commercial API | 표면 거칠기 기호 파싱, ISO 1302 표준 | [werk24.io](https://werk24.io) |
| **YOLOv11** | Open Source | 커스텀 학습으로 Ra/Rz 기호 검출 가능 | [Ultralytics](https://ultralytics.com) |
| **OpenCV Template Matching** | Library | 표면 거칠기 기호 템플릿 매칭 | [OpenCV](https://docs.opencv.org) |

---

#### 6. 🔢 수량 추출 (`quantity_extraction`)

**목적**: BOM 수량 정보 자동 인식

| 항목 | 내용 |
|------|------|
| **추출 대상** | 부품 수량, 세트 수량, 어셈블리 수량 |
| **구현 방법** | 벌룬 OCR + 표제란 파싱 + 패턴 매칭 |
| **의존 노드** | eDOCr2 |
| **난이도** | ⭐⭐ 중간 |
| **예상 기간** | 1주 |

**수량 패턴 예시**:
```
- "QTY: 4"
- "수량: 4 EA"
- "4 OFF"
- "×4" (벌룬 옆)
- "REQ'D: 4"
```

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **spaCy** | NLP Library | 패턴 매칭, 명명된 엔티티 인식 | [spacy.io](https://spacy.io) |
| **regex** | Python Library | 고급 정규식 패턴 매칭 | [PyPI](https://pypi.org/project/regex) |
| **Donut** | Open Source | 테이블 구조 내 수량 필드 추출 | [GitHub](https://github.com/clovaai/donut) |

---

#### 7. 🎈 벌룬 번호 매칭 (`balloon_matching`)

**목적**: 검출된 심볼과 부품번호(벌룬) 자동 연결

| 항목 | 내용 |
|------|------|
| **매칭 대상** | 벌룬 번호 ↔ 심볼 ↔ BOM 항목 |
| **구현 방법** | 벌룬 검출 + 지시선 추적 + 근접성 분석 |
| **의존 노드** | YOLO (벌룬 클래스 추가), eDOCr2 |
| **난이도** | ⭐⭐ 중간 |
| **예상 기간** | 2주 |

**매칭 알고리즘**:
```
1. 벌룬 원형 검출 (YOLO)
2. 벌룬 내 숫자 OCR
3. 지시선 끝점 추적
4. 가장 가까운 심볼과 연결
5. BOM 테이블의 번호와 매칭
```

**결과 예시**:
```json
{
  "balloon_number": "12",
  "symbol_id": "detection_045",
  "symbol_class": "valve",
  "bom_item": {
    "part_number": "VLV-001",
    "description": "Globe Valve 2\""
  }
}
```

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **OpenCV Contour Detection** | Library | 원형 벌룬 검출 | [OpenCV](https://docs.opencv.org) |
| **Scikit-learn KNN** | Library | 최근접 심볼 매칭 | [scikit-learn](https://scikit-learn.org) |
| **Graph Neural Networks** | Research | 벌룬-심볼 관계 학습 | [PyTorch Geometric](https://pytorch-geometric.readthedocs.io) |
| **Hungarian Algorithm** | Algorithm | 최적 일대일 매칭 (scipy.optimize.linear_sum_assignment) | [SciPy](https://docs.scipy.org) |

---

## 장기 로드맵 (1-2개월) - ✅ 전체 완료

### 복잡한 AI/ML 개발 필요 → **모두 구현 완료 (2025-12-24)**

#### 8. 🗺️ 도면 영역 세분화 (`drawing_region_segmentation`) - ✅ 완료

**목적**: 도면 내 각 뷰(정면도, 측면도, 단면도 등)를 자동 구분

| 항목 | 내용 |
|------|------|
| **세분화 대상** | 정면도, 측면도, 평면도, 단면도, 상세도, 표제란 |
| **구현 방법** | Semantic Segmentation (U-Net/Mask R-CNN) |
| **의존 노드** | ✅ RegionSegment 노드 구현 완료 |
| **난이도** | ⭐⭐⭐ 어려움 |
| **상태** | ✅ 완료 |

**학습 데이터 필요**:
- 도면 이미지 1000+ 장
- 영역별 마스크 라벨링

**활용 시나리오**:
```
1. 각 뷰별로 독립적인 치수 OCR 수행
2. 단면도에서만 내부 구조 분석
3. 상세도 확대 자동 매칭
4. 뷰 간 일관성 검증
```

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **SAM (Segment Anything)** | Open Source | Meta, 범용 세그멘테이션 모델 | [GitHub](https://github.com/facebookresearch/segment-anything) |
| **SAM 2** | Open Source | SAM의 비디오 확장, 2024년 공개 | [GitHub](https://github.com/facebookresearch/sam2) |
| **Detectron2** | Open Source | Meta, Mask R-CNN 구현 | [GitHub](https://github.com/facebookresearch/detectron2) |
| **MMSegmentation** | Open Source | OpenMMLab, 다양한 세그멘테이션 모델 | [GitHub](https://github.com/open-mmlab/mmsegmentation) |
| **U-Net** | Architecture | 의료/도면 세그멘테이션에 최적화 | [arXiv](https://arxiv.org/abs/1505.04597) |

---

#### 9. 📋 주석/노트 추출 (`notes_extraction`) - ✅ 완료

**목적**: 도면의 일반 노트 및 특수 지시사항 추출

| 항목 | 내용 |
|------|------|
| **추출 대상** | 일반 노트, 재료 사양, 열처리, 도금, 특수 지시 |
| **구현 방법** | 영역 검출 + OCR + NLP 분류 |
| **의존 노드** | ✅ eDOCr2 + LLM 연동 완료 |
| **난이도** | ⭐⭐⭐ 어려움 |
| **상태** | ✅ 완료 |

**노트 분류 카테고리**:
```
- MATERIAL: 재료 사양
- HEAT_TREATMENT: 열처리
- SURFACE_FINISH: 표면 처리
- TOLERANCE: 일반 공차
- ASSEMBLY: 조립 지시
- INSPECTION: 검사 요구사항
- GENERAL: 기타 일반 노트
```

**NLP 파이프라인**:
```
텍스트 추출 → 문장 분리 → 카테고리 분류 → 키-값 추출
```

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **LangChain** | Framework | LLM 기반 텍스트 분류 파이프라인 | [langchain.com](https://langchain.com) |
| **spaCy** | NLP Library | 문장 분리, 엔티티 추출 | [spacy.io](https://spacy.io) |
| **Hugging Face Transformers** | Library | 텍스트 분류 모델 (BERT, RoBERTa) | [HuggingFace](https://huggingface.co) |
| **OpenAI GPT-4** | API | 노트 분류 및 구조화 | [openai.com](https://openai.com) |
| **Claude API** | API | Anthropic, 긴 텍스트 처리에 강점 | [anthropic.com](https://anthropic.com) |

---

#### 10. 🔄 리비전 비교 (`revision_comparison`) - ✅ 완료

**목적**: 도면 버전 간 변경점 자동 감지 및 하이라이트

| 항목 | 내용 |
|------|------|
| **비교 대상** | 형상 변경, 치수 변경, 노트 변경, 추가/삭제 항목 |
| **구현 방법** | 이미지 정합 + 픽셀 차이 + 의미적 비교 |
| **의존 노드** | ✅ RevisionCompare 노드 구현 완료 |
| **난이도** | ⭐⭐⭐ 어려움 |
| **상태** | ✅ 완료 |

**비교 알고리즘**:
```
1. 이미지 정합 (SIFT/ORB 기반 정렬)
2. 픽셀 차이 맵 생성
3. 변경 영역 클러스터링
4. 치수 값 비교 (OCR 결과 diff)
5. 변경 타입 분류 (추가/삭제/수정)
```

**결과 시각화**:
```
- 🟢 추가된 항목 (녹색 하이라이트)
- 🔴 삭제된 항목 (빨간색 하이라이트)
- 🟡 수정된 항목 (노란색 하이라이트)
```

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **OpenCV SIFT/ORB** | Library | 특징점 기반 이미지 정합 | [OpenCV](https://docs.opencv.org) |
| **scikit-image** | Library | 이미지 차이 계산, 구조적 유사도 (SSIM) | [scikit-image](https://scikit-image.org) |
| **Diff-GT** | Research | 도면 비교 전문 도구 | [GitHub](https://github.com) |
| **Five Flute** | Commercial | 3D CAD 비교 도구 (도면 비교 참고) | [fiveflute.com](https://fiveflute.com) |
| **ImageMagick compare** | CLI Tool | 픽셀 단위 이미지 비교 | [imagemagick.org](https://imagemagick.org) |

---

#### 11. 🤖 VLM 자동 분류 (`vlm_auto_classification`) - ✅ 완료

**목적**: Vision-Language Model로 도면 타입 및 특성 자동 분류

| 항목 | 내용 |
|------|------|
| **분류 대상** | 도면 타입, 산업 분야, 복잡도, 필요 기능 추천 |
| **구현 방법** | GPT-4V / Claude 3.5 Vision API |
| **의존 노드** | ✅ VL 노드 (5004) 연동 완료 |
| **난이도** | ⭐⭐ 중간 (API 비용 이슈) |
| **상태** | ✅ 완료 |

**현재 상태**: ✅ WorkflowPage에 VLM 분류 UI 완전 구현

**개선 방향**:
```
1. Builder의 ImageInput에서 VL 노드 선택 시 자동 분류
2. 분류 결과로 features 자동 추천
3. 사용자 확인 후 적용
```

**관련 API/라이브러리**:
| 이름 | 유형 | 설명 | 링크 |
|------|------|------|------|
| **GPT-4V (Vision)** | Commercial API | OpenAI, 최고 수준 이미지 이해 | [openai.com](https://openai.com) |
| **Claude 3.5 Sonnet** | Commercial API | Anthropic, 빠른 응답, 비용 효율적 | [anthropic.com](https://anthropic.com) |
| **Gemini Pro Vision** | Commercial API | Google, 멀티모달 처리 | [ai.google.dev](https://ai.google.dev) |
| **Qwen2-VL** | Open Source | Alibaba, 오픈소스 VLM, 로컬 배포 가능 | [HuggingFace](https://huggingface.co/Qwen) |
| **LLaVA** | Open Source | 경량 VLM, RTX 3090에서 실행 가능 | [GitHub](https://github.com/haotian-liu/LLaVA) |
| **InternVL** | Open Source | 중국 연구팀, 강력한 도면 이해 능력 | [GitHub](https://github.com/OpenGVLab/InternVL) |

---

## 기능 우선순위 매트릭스

### 영향도 vs 구현 난이도

```
높음 ┌────────────────────────────────────────────┐
     │                        │                  │
영   │  🎈 벌룬 매칭          │ 🗺️ 영역 세분화   │
향   │  🔢 수량 추출          │ 📋 노트 추출     │
도   │                        │ 🔄 리비전 비교   │
     ├────────────────────────┼──────────────────┤
     │  📝 표제란 OCR         │ 🔩 용접 기호     │
     │  🔗 P&ID 연결성        │ 🪨 표면 거칠기   │
     │  📐 선 검출            │                  │
낮음 └────────────────────────┴──────────────────┘
        쉬움                        어려움
                   구현 난이도
```

---

## 추천 구현 순서

### Phase 1: 단기 (즉시 시작)
```
1. 📝 title_block_ocr      - BOM 필수 메타데이터
2. 🔗 pid_connectivity     - P&ID 고객사 요구
3. 📐 line_detection       - UI 연동만 필요
```

### Phase 2: 중기 (1개월 내)
```
4. 🎈 balloon_matching     - BOM 자동화 핵심
5. 🔢 quantity_extraction  - BOM 완성도 향상
6. 🔩 welding_symbol       - 제조 고객사 요구
```

### Phase 3: 장기 (분기 내) - ✅ 완료!
```
7. 🗺️ region_segmentation - 복잡 도면 처리      ✅ 완료
8. 📋 notes_extraction     - 전체 정보 추출       ✅ 완료
9. 🔄 revision_comparison  - 설계 변경 관리       ✅ 완료
10. 🤖 vlm_auto_classification - VLM 자동 분류   ✅ 완료
```

---

## 기술 스택 요구사항

### 단기 기능
- 기존 노드 활용 (eDOCr2, YOLO, Line Detector, PID Analyzer)
- 프론트엔드 UI 추가

### 중기 기능
- YOLO 추가 학습 (용접 기호, 벌룬)
- 규칙 기반 파서 개발
- 정규식 패턴 라이브러리

### 장기 기능
- Semantic Segmentation 모델 (PyTorch)
- LLM API 연동 (OpenAI/Anthropic)
- 이미지 정합 알고리즘 (OpenCV)

---

## API/라이브러리 종합 요약

### 🏢 상용 API (Commercial)

| API | 용도 | 비용 모델 | 권장 기능 |
|-----|------|----------|----------|
| **Werk24** | 기계 도면 전문 파싱 | 구독형 | 표제란, GD&T, 용접 기호 |
| **Azure Document Intelligence** | 커스텀 문서 추출 | 사용량 기반 | 표제란, 테이블 |
| **GPT-4V** | 도면 분류/분석 | API 호출당 | VLM 분류 |
| **Claude Vision** | 도면 분류/분석 | API 호출당 | VLM 분류, 노트 추출 |
| **Gemini Pro Vision** | 멀티모달 분석 | API 호출당 | VLM 분류 |
| **Five Flute** | CAD/도면 비교 | 라이선스 | 리비전 비교 |

### 🆓 오픈소스 라이브러리

| 라이브러리 | 용도 | 라이선스 | 권장 기능 |
|-----------|------|---------|----------|
| **Donut** | OCR-free 문서 이해 | MIT | 표제란, 수량 추출 |
| **SAM/SAM 2** | 범용 세그멘테이션 | Apache 2.0 | 영역 세분화 |
| **NetworkX** | 그래프 분석 | BSD | P&ID 연결성 |
| **OpenCV** | 이미지 처리 전반 | Apache 2.0 | 선 검출, 리비전 비교 |
| **spaCy** | NLP 파이프라인 | MIT | 노트 추출, 패턴 매칭 |
| **LangChain** | LLM 오케스트레이션 | MIT | 노트 분류 |
| **Qwen2-VL** | 오픈소스 VLM | Apache 2.0 | VLM 분류 (로컬) |
| **LLaVA** | 경량 VLM | Apache 2.0 | VLM 분류 (로컬) |

### 📚 연구 모델/데이터셋

| 이름 | 유형 | 용도 | 출처 |
|------|------|------|------|
| **Relationformer** | GNN 모델 | P&ID 관계 추출 | CVPR 2022 |
| **PID2Graph** | 데이터셋 | P&ID 심볼-배관 연결 | Kaggle |
| **YOLOv8-WD** | 특화 모델 | 용접 결함 검출 | MDPI |
| **DeepLSD** | 모델 | 라인 세그먼트 검출 | CVPR 2023 |
| **LayoutLMv3** | 모델 | 문서 레이아웃 이해 | Microsoft |

### 🛠️ 유틸리티/도구

| 도구 | 용도 | 플랫폼 |
|------|------|--------|
| **Roboflow** | 데이터셋 관리/라벨링 | 웹 |
| **Label Studio** | 범용 라벨링 도구 | 로컬/웹 |
| **ImageMagick** | 이미지 비교/처리 | CLI |
| **scikit-image** | 이미지 분석 | Python |
| **SciPy** | 최적화/매칭 알고리즘 | Python |

---

## 리소스 예상

| 기간 | 기능 수 | 개발 인력 | GPU 리소스 |
|------|---------|----------|------------|
| 단기 | 3개 | 1명 | 불필요 |
| 중기 | 4개 | 1-2명 | 학습용 (선택) |
| 장기 | 4개 | 2명 | 학습 필수 |

---

## 다음 단계

1. [ ] 고객사 요구사항 수집 (우선순위 재조정)
2. [ ] 단기 기능 3개 구현 시작
3. [ ] 용접 기호 학습 데이터 확보
4. [ ] VLM 비용 분석 (GPT-4V vs Claude)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-12-24 | v1.0 | 초기 로드맵 작성 |
| 2025-12-24 | v1.1 | 각 기능별 API/라이브러리 정보 추가, 종합 요약 섹션 추가 |
| 2025-12-24 | v2.0 | **장기 로드맵 4개 기능 전체 구현 완료** (영역 세분화, 노트 추출, 리비전 비교, VLM 자동 분류) |
| 2025-12-26 | v2.1 | **SSOT 리팩토링 완료** (features 정의 단일 소스화, 20개 기능 정의됨), routers/__init__.py 수정 |

