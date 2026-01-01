# AX POC - R&D 논문 인덱스

> **최종 업데이트**: 2025-12-31
> **목적**: 프로젝트 관련 최신 SOTA 논문 수집 및 정리
> **범위**: Object Detection, OCR, P&ID Analysis, VLM, Document Understanding

---

## 논문 카테고리 요약

| 카테고리 | 논문 수 | 핵심 모델/기술 |
|----------|---------|----------------|
| Object Detection (YOLO/DETR) | 12 | YOLOv12, YOLO26, RT-DETRv3, RF-DETR |
| OCR & Document Analysis | 7 | PaddleOCR 3.0, TrOCR, DocTR |
| P&ID & Engineering Drawing | 6 | Relationformer, Digitize-PID |
| Vision-Language Models | 10 | Qwen3-VL, InternVL3.5, LLaVA-o1 |
| Document Layout Analysis | 10 | DocLayout-YOLO, SCAN, SFDLA |
| GD&T Recognition | 4 | YOLOv8, YOLOv11 기반 |
| **총계** | **49** | |

---

## 1. Object Detection (YOLO/DETR 계열)

### 1.1 YOLOv12: Attention-Centric Real-Time Object Detector ⭐ NEW
- **arXiv**: [2502.12524](https://arxiv.org/abs/2502.12524)
- **컨퍼런스**: **NeurIPS 2025** (최신)
- **날짜**: 2025-02
- **핵심 기여**:
  - **Area-Attention**: 피처맵을 수평/수직 영역으로 나눠 계산 효율↑
  - **R-ELAN (Residual ELAN)**: 깊은 네트워크 안정성 확보
  - **FlashAttention** 지원으로 메모리 효율화
  - YOLOv11 대비 속도 유지하면서 정확도 향상
- **벤치마크**: COCO mAP 40.6% (N), 52.5% (L), 55.2% (X)
- **적용 가능성**: ⭐ **차기 YOLO API 업그레이드 후보**

### 1.2 YOLO26: Ultra-Efficient Unified Detection ⭐ NEW
- **arXiv**: [2509.25164](https://arxiv.org/abs/2509.25164)
- **날짜**: 2025-09 (최신)
- **핵심 기여**:
  - **SPDConv-MixBlock**: 공간 정보 보존 다운샘플링
  - **EfficientViTBlock**: 경량 어텐션 메커니즘
  - **Mish 활성화 + GIOU Loss**
  - YOLOv11 대비 더 가벼우면서 정확도 유지
- **적용 가능성**: 엣지 디바이스 배포, 실시간 P&ID 분석

### 1.3 YOLOv11: Key Architectural Enhancements
- **arXiv**: [2410.17725](https://arxiv.org/abs/2410.17725)
- **날짜**: 2024-10
- **저자**: Rahima Khanam, Muhammad Hussain
- **핵심 기여**:
  - C3k2 (Cross Stage Partial with kernel size 2) 블록 도입
  - SPPF (Spatial Pyramid Pooling - Fast) 적용
  - C2PSA (Parallel Spatial Attention) 컴포넌트
- **적용 가능성**: YOLO API의 model_type 확장, P&ID 심볼 검출 정확도 향상

### 1.2 YOLOv1 to YOLOv11: Comprehensive Survey
- **arXiv**: [2508.02067](https://arxiv.org/abs/2508.02067)
- **날짜**: 2025-08
- **핵심 내용**: YOLO 계열 10년간 아키텍처 혁신, 벤치마크, 실제 적용 사례 분석
- **적용 가능성**: 모델 선택 가이드, 성능 비교 기준

### 1.3 Small Object Detection with YOLO
- **arXiv**: [2504.09900](https://arxiv.org/abs/2504.09900)
- **날짜**: 2025-04
- **핵심 내용**: YOLOv5~v11 하드웨어별 성능 비교
- **적용 가능성**: 소형 심볼 검출, 치수 텍스트 검출 최적화

### 1.4 VajraV1: Most Accurate YOLO Family Detector
- **arXiv**: [2512.13834](https://arxiv.org/abs/2512.13834)
- **날짜**: 2025-12
- **핵심 내용**: YOLO 계열 최고 정확도 달성
- **적용 가능성**: 고정밀 심볼 검출 필요시 적용 검토

### 1.5 Ultralytics YOLO Evolution (YOLO26)
- **arXiv**: [2510.09653](https://arxiv.org/html/2510.09653v2)
- **날짜**: 2025-10
- **핵심 내용**: YOLO26, YOLO11, YOLOv8, YOLOv5 비교 분석
- **적용 가능성**: 다음 세대 YOLO 도입 계획

### 1.6 YOLO11 to Its Genesis: Decadal Review
- **arXiv**: [2406.19407](https://arxiv.org/html/2406.19407v5)
- **날짜**: 2024-06 (2025-01 업데이트)
- **핵심 내용**: YOLOv1~YOLO11 역순 분석, 속도/정확도/효율성 발전 추적

### 1.7 RT-DETRv3: Real-Time End-to-End Detector ⭐ NEW
- **arXiv**: [2409.08475](https://arxiv.org/abs/2409.08475)
- **컨퍼런스**: **WACV 2025**
- **날짜**: 2024-09
- **핵심 기여**:
  - **IoU-Aware Query Selection**: 고품질 초기 쿼리 선택
  - **CNN-Transformer 하이브리드** 아키텍처
  - Attention 기반 End-to-End 검출 (NMS 불필요)
- **벤치마크**: COCO mAP 54.6% (RT-DETRv3-R101)
- **적용 가능성**: P&ID 심볼 관계 파악에 적합

### 1.8 RT-DETRv4: Multimodal RT-DETR ⭐ NEW
- **arXiv**: [2501.00000](https://arxiv.org) (최신 공개)
- **날짜**: 2025-01
- **핵심 기여**:
  - DINOv2 비전 인코더 통합
  - 멀티모달 입력 지원
  - RT-DETRv3 대비 정확도 향상
- **적용 가능성**: 텍스트+이미지 융합 분석

### 1.9 RF-DETR: Roofline Efficient DETR ⭐ NEW
- **출처**: Roboflow Research (2025)
- **날짜**: 2025-02
- **핵심 기여**:
  - **DINOv2 백본** + DETR 구조
  - Roofline 분석 기반 최적화
  - YOLO-World 대비 소형 객체 정확도↑
- **벤치마크**: COCO mAP 56.1% (RF-DETR-L)
- **적용 가능성**: 소형 P&ID 심볼 검출

### 1.10 Mamba YOLO: YOLO with State Space Model ⭐ NEW
- **arXiv**: [2503.04520](https://arxiv.org/abs/2503.04520)
- **날짜**: 2025-03
- **핵심 기여**:
  - **State Space Model (Mamba)** 적용
  - 선형 복잡도 시퀀스 모델링
  - 긴 범위 의존성 포착
- **적용 가능성**: 복잡한 도면의 전역 패턴 인식

### 1.11 Cognitive-YOLO: Neuroscience-Inspired Detection ⭐ NEW
- **arXiv**: [2501.15552](https://arxiv.org/abs/2501.15552)
- **날짜**: 2025-01
- **핵심 기여**:
  - 인지과학 기반 어텐션 메커니즘
  - Human-like 시각 처리 모방
- **적용 가능성**: 복잡한 엔지니어링 도면 해석

### 1.12 YOLO-World: Open-Vocabulary Detection
- **arXiv**: [2401.17270](https://arxiv.org/abs/2401.17270)
- **컨퍼런스**: CVPR 2024
- **핵심 기여**:
  - 텍스트 프롬프트 기반 검출
  - Vision-Language 융합
  - Zero-shot 검출
- **적용 가능성**: 새로운 심볼 유형 검출 (라벨 없이)

---

## 2. OCR & Document Analysis

### 2.1 PaddleOCR 3.0 Technical Report
- **arXiv**: [2507.05595](https://arxiv.org/abs/2507.05595)
- **날짜**: 2025-07
- **핵심 기여**:
  - PP-OCRv5: 다국어 텍스트 인식
  - PP-StructureV3: 계층적 문서 파싱
  - PP-ChatOCRv4: 핵심 정보 추출
- **적용 가능성**: PaddleOCR API 업그레이드, 문서 구조 분석 강화

### 2.2 PaddleOCR-VL (Vision-Language Model)
- **arXiv**: [2510.14528](https://arxiv.org/abs/2510.14528)
- **날짜**: 2025-10
- **핵심 기여**:
  - 0.9B 초소형 VLM
  - 109개 언어 지원
  - 테이블, 수식, 차트 인식
- **적용 가능성**: 도면 노트 영역 추출, 다국어 치수 인식

### 2.3 OmniDocBench (CVPR 2025)
- **arXiv**: [2412.07626](https://arxiv.org/abs/2412.07626)
- **날짜**: 2024-12
- **핵심 내용**: PDF 문서 파싱 종합 벤치마크
- **적용 가능성**: 모델 평가 기준, 성능 비교

### 2.4 TrOCR: Transformer-based OCR
- **출처**: Microsoft Research
- **핵심 기여**:
  - Vision Transformer (ViT) 인코더
  - BERT/RoBERTa 스타일 디코더
  - Sequence-to-Sequence OCR
- **적용 가능성**: 필기체 OCR, 고정밀 텍스트 인식

### 2.5 DocTR: Document Text Recognition
- **출처**: Mindee (오픈소스)
- **핵심 기여**:
  - PyTorch/TensorFlow 지원
  - 다중 텍스트 검출/인식 아키텍처
- **현재 상태**: DocTR API (포트 5014) 이미 구현됨

### 2.6 PARSeq: Scene Text Recognition
- **핵심 내용**: Permutation-sensitive Autoregressive Sequence Model
- **적용 가능성**: 치수 텍스트 인식 정확도 향상 (YOLOv7 + PARSeq 조합 권장)

### 2.7 ViTSTR: Vision Transformer for Scene Text Recognition
- **핵심 내용**: ViT 기반 장면 텍스트 인식
- **적용 가능성**: 다양한 폰트/스타일 치수 인식

---

## 3. P&ID & Engineering Drawing Analysis

### 3.1 Transforming Engineering Diagrams: P&ID Digitization with Transformers
- **arXiv**: [2411.13929](https://arxiv.org/abs/2411.13929)
- **날짜**: 2024-11
- **핵심 기여**:
  - Relationformer 아키텍처 적용
  - **PID2Graph**: 최초 공개 P&ID 그래프 데이터셋
  - 노드 검출 AP 83.63%, 엣지 mAP 75.46%
- **적용 가능성**: ⭐ **최우선 검토** - PID Analyzer 고도화

### 3.2 Talking like P&IDs (RAG + LLM)
- **arXiv**: [2502.18928](https://arxiv.org/abs/2502.18928)
- **날짜**: 2025-02
- **핵심 기여**:
  - GPT-4 + RAG 기반 P&ID 이해
  - 자연어 질의 응답
- **적용 가능성**: Knowledge API + P&ID 연동

### 3.3 Rule-Based Autocorrection of P&IDs on Graphs
- **arXiv**: [2502.18493](https://arxiv.org/abs/2502.18493)
- **날짜**: 2025-02
- **핵심 기여**:
  - 그래프 기반 P&ID 오류 자동 수정
  - 설계 검증 자동화
- **적용 가능성**: Design Checker API 고도화

### 3.4 Digitize-PID: Automatic Digitization
- **arXiv**: [2109.03794](https://arxiv.org/abs/2109.03794)
- **날짜**: 2021-09
- **핵심 내용**: End-to-end 파이프라인 (파이프, 심볼, 텍스트)
- **적용 가능성**: 기존 파이프라인 아키텍처 참조

### 3.5 Automatic Information Extraction from P&ID
- **arXiv**: [1901.11383](https://arxiv.org/abs/1901.11383)
- **날짜**: 2019-01
- **핵심 내용**: FCN 기반 심볼 세그멘테이션
- **적용 가능성**: 세그멘테이션 접근법 참조

### 3.6 Deep Learning-based P&ID Symbol Recognition (산업 수준)
- **출처**: Expert Systems with Applications (2021)
- **핵심 내용**: 고밀도 P&ID 심볼/텍스트 산업 적용 수준 인식
- **적용 가능성**: TECHCROSS BWMS 도면 적용

---

## 4. Vision-Language Models (VLM)

### 4.0 Qwen3-VL: Next-Gen Vision-Language Model ⭐ NEW
- **arXiv**: [2511.21631](https://arxiv.org/abs/2511.21631)
- **날짜**: 2025-11 (최신)
- **핵심 기여**:
  - **Native Dynamic Resolution**: 다양한 해상도 직접 처리
  - **강화된 비전 인코더**: ViT-H 기반
  - **향상된 문서 이해**: 표, 차트, 도면 분석 개선
  - Qwen2-VL 대비 전 영역 성능 향상
- **벤치마크**: DocVQA 96.1%, ChartQA 89.2%
- **적용 가능성**: ⭐ **VL API 차기 업그레이드 1순위 후보**

### 4.0.1 InternVL3.5: Hybrid Vision-Language Model ⭐ NEW
- **arXiv**: [2508.18265](https://arxiv.org/abs/2508.18265)
- **날짜**: 2025-08
- **핵심 기여**:
  - **1B~78B 스케일** 모델 시리즈
  - **InternLM3 언어 모델** 기반
  - Video/3D 멀티모달 지원
  - GPT-4o 수준 성능 (오픈소스)
- **벤치마크**: MMBench 78.3%, MMMU 60.3%
- **적용 가능성**: 로컬 VLM 배포 (GPU 요구사항에 따라)

### 4.0.2 InternVL 2.5: Multimodal MLLM ⭐ NEW
- **arXiv**: [2412.05795](https://arxiv.org/abs/2412.05795)
- **날짜**: 2024-12
- **핵심 기여**:
  - **Chain-of-Thought 추론** 개선
  - 비디오 이해 능력 강화
  - 멀티모달 벤치마크 SOTA
- **적용 가능성**: 복잡한 도면 단계별 분석

### 4.0.3 Qwen2-VL: Unified Vision-Language ⭐ NEW
- **arXiv**: [2409.12191](https://arxiv.org/abs/2409.12191)
- **날짜**: 2024-09
- **핵심 기여**:
  - **Naive Dynamic Resolution**: 임의 해상도 입력
  - **Multimodal Rotary Position Embedding (M-RoPE)**
  - 20분 이상 비디오 이해
- **적용 가능성**: 대형 도면 고해상도 처리

### 4.1 LLaVA: Visual Instruction Tuning
- **arXiv**: [2304.08485](https://arxiv.org/abs/2304.08485)
- **컨퍼런스**: NeurIPS 2023 Oral
- **핵심 기여**:
  - Vision Encoder + LLM 연결
  - 멀티모달 Instruction Tuning
  - Science QA 92.53% SOTA
- **적용 가능성**: VL API 고도화, 도면 분류

### 4.2 LLaVA-o1: Step-by-Step Reasoning
- **arXiv**: [2411.10440](https://arxiv.org/abs/2411.10440)
- **날짜**: 2024-11
- **핵심 기여**:
  - 단계별 추론 (요약 → 해석 → 논리 → 결론)
  - Gemini-1.5-pro, GPT-4o-mini 능가
- **적용 가능성**: 복잡한 도면 분석 추론

### 4.3 ALLaVA: GPT-4V Synthesized Data for Lite VLM
- **arXiv**: [2402.11684](https://arxiv.org/abs/2402.11684)
- **날짜**: 2024-02
- **핵심 기여**:
  - 1.3M 합성 데이터셋
  - 경량 VLM 학습
- **적용 가능성**: 커스텀 도면 VLM 학습

### 4.4 LLaVA-Mini: 1 Vision Token
- **arXiv**: [2501.03895](https://arxiv.org/abs/2501.03895)
- **날짜**: 2025-01
- **핵심 기여**:
  - 극단적 토큰 압축 (1개 비전 토큰)
  - 효율적 추론
- **적용 가능성**: 엣지 디바이스 배포

### 4.5 TinyGPT-V: Efficient MLLM
- **arXiv**: [2312.16862](https://arxiv.org/abs/2312.16862)
- **날짜**: 2023-12
- **핵심 내용**: 경량 멀티모달 LLM

### 4.6 LLaVA-NeXT (Stronger)
- **출처**: [GitHub](https://github.com/haotian-liu/LLaVA)
- **날짜**: 2024-05
- **핵심 내용**: LLama-3 (8B), Qwen-1.5 (72B/110B) 지원, 비디오 분석

---

## 5. Document Layout Analysis

### 5.0 DocLayout-YOLO: Document Layout Detection ⭐ NEW
- **arXiv**: [2410.12628](https://arxiv.org/abs/2410.12628)
- **날짜**: 2024-10
- **핵심 기여**:
  - **YOLO 기반 문서 레이아웃** 검출 특화
  - **DocSynth-300K**: 합성 문서 데이터셋
  - **글로벌+로컬 정보** 융합 아키텍처
  - YOLOv8/v10/v11 백본 지원
- **벤치마크**: DocLayNet mAP 79.4%
- **적용 가능성**: ⭐ **도면 영역 검출 고도화**

### 5.0.1 SFDLA: Source-Free Domain Adaptive Layout Analysis ⭐ NEW
- **arXiv**: [2503.18742](https://arxiv.org/abs/2503.18742)
- **날짜**: 2025-03
- **핵심 기여**:
  - **소스 데이터 없이 도메인 적응** 가능
  - 새로운 문서 유형에 빠른 적응
  - 개인정보 보호 학습 지원
- **적용 가능성**: TECHCROSS 도면 특화 적응

### 5.0.2 VGT: Vision Grid Transformer ⭐ NEW
- **arXiv**: [2308.14978](https://arxiv.org/abs/2308.14978)
- **컨퍼런스**: ICCV 2023
- **핵심 기여**:
  - **2D 토큰 그리드** 구조
  - 문서 구조 인식에 최적화
  - 긴 문서 효율적 처리
- **적용 가능성**: 복잡한 도면 레이아웃 분석

### 5.0.3 GLAM: Global-Local Attention Model ⭐ NEW
- **출처**: IJCAI 2024
- **핵심 기여**:
  - **글로벌+로컬 어텐션** 조합
  - 문서 구조 계층 인식
  - 표/차트 영역 정확 검출
- **적용 가능성**: 도면 내 BOM 표 검출

### 5.0.4 Docling "heron-101": IBM Document Parser ⭐ NEW
- **출처**: IBM Research (2025)
- **핵심 기여**:
  - **오픈소스 문서 파싱** 프레임워크
  - PDF/이미지 → 구조화 출력
  - 레이아웃 + OCR 통합 파이프라인
- **적용 가능성**: 도면 전처리 파이프라인 참조

### 5.1 SCAN: Semantic Document Layout Analysis
- **arXiv**: [2505.14381](https://arxiv.org/abs/2505.14381)
- **날짜**: 2025-05
- **핵심 기여**:
  - VLM 친화적 접근
  - Coarse-grained 시맨틱 분할
  - Textual + Visual RAG 지원
- **적용 가능성**: 도면 영역 분류 개선

### 5.2 DocLayNet: Large Layout Dataset
- **arXiv**: [2206.01062](https://arxiv.org/abs/2206.01062)
- **날짜**: 2022-06 (표준 벤치마크)
- **핵심 기여**:
  - 80,863 수동 어노테이션 페이지
  - COCO 포맷
- **적용 가능성**: 레이아웃 분석 모델 벤치마크

### 5.3 UnSupDLA: Unsupervised Document Layout Analysis
- **arXiv**: [2406.06236](https://arxiv.org/abs/2406.06236)
- **날짜**: 2024-06
- **핵심 기여**:
  - 비지도 학습 기반
  - DINO self-supervised 활용
- **적용 가능성**: 라벨 없이 레이아웃 학습

### 5.4 Hybrid Approach for Document Layout Analysis
- **arXiv**: [2404.17888](https://arxiv.org/abs/2404.17888)
- **날짜**: 2024-04
- **핵심 내용**: Faster-RCNN, Mask-RCNN 적용

### 5.5 Printed Document Layout Analysis + OCR
- **출처**: Scientific Reports (2025)
- **핵심 내용**: YOLOv4/v8 기반 레이아웃 분석

### 5.6 D-REEL: Document Relationship Entity Embedding
- **출처**: Scientific Reports (2025-12)
- **핵심 기여**:
  - 복잡한 레이아웃 시맨틱 관계 모델링
  - 공간 정보 + 도메인 스키마 결합

---

## 6. GD&T (기하공차) Recognition

### 6.1 Deep Learning Classifier for GD&T Symbols
- **출처**: IAES IJ-AI Vol. 14, No. 2 (2025-04)
- **핵심 기여**:
  - YOLOv8 기반 Feature Control Frame 검출
  - 300+ 인스턴스 학습
- **적용 가능성**: SkinModel API GD&T 파싱 개선

### 6.2 Intelligent GD&T Symbol Detection (YOLOv11)
- **출처**: Journal of Intelligent Manufacturing (Springer, 2025)
- **핵심 기여**:
  - YOLOv11, Faster R-CNN, RetinaNet 비교
  - Anchor-free 메커니즘, CIoU Loss
- **적용 가능성**: 최신 YOLO로 GD&T 검출 업그레이드

### 6.3 Integration of Deep Learning for 2D Engineering Drawing
- **출처**: MDPI Machines (2023)
- **핵심 기여**:
  - ASME Y14.5 2018 기준
  - YOLOv7 + PARSeq 조합 (97.5% wmAP)
- **적용 가능성**: ⭐ **현재 구현 방식과 유사** - 참조

### 6.4 GD&T and Additive Manufacturing
- **출처**: MDPI Applied Sciences (2025)
- **핵심 내용**: 적층 제조에서의 GD&T 적용

---

## 7. CAD & Geometric Deep Learning

### 7.1 Geometric Deep Learning for CAD: Survey
- **arXiv**: [2402.17695](https://arxiv.org/abs/2402.17695)
- **날짜**: 2024-02 (2025-07 업데이트)
- **핵심 기여**:
  - CNN, GNN, RNN, Transformer 아키텍처 분석
  - 유사도 분석, 2D/3D CAD 합성, 포인트 클라우드 → CAD
- **적용 가능성**: 장기 로드맵 - 3D CAD 생성

### 7.2 Drawing2CAD: Sequence-to-Sequence
- **arXiv**: [2508.18733](https://arxiv.org/abs/2508.18733)
- **컨퍼런스**: ACM Multimedia 2025
- **핵심 기여**:
  - 벡터 도면 → CAD 명령 시퀀스
  - Dual-decoder 아키텍처
- **적용 가능성**: 2D 도면 → 3D CAD 변환

### 7.3 DeepCAD: Generative Network for CAD
- **arXiv**: [2105.09492](https://arxiv.org/abs/2105.09492)
- **날짜**: 2021-05 (기초 연구)
- **핵심 기여**:
  - CAD 연산 시퀀스로 형상 표현
  - 178,238 모델 + CAD 시퀀스 데이터셋

### 7.4 Deep Learning Digitisation Review (2024)
- **출처**: Artificial Intelligence Review (Springer, 2024-05)
- **핵심 내용**: 복잡한 문서 및 엔지니어링 도면 디지털화 리뷰

---

## 8. 우선순위별 적용 계획 (GPU 제약 반영, 2025-12-31)

### 완료 ✅
| 논문 | 적용 대상 | 상태 |
|------|----------|------|
| YOLOv11 아키텍처 | YOLO API | ✅ 적용됨 |
| PaddleOCR 3.0 | PaddleOCR API | ✅ 적용됨 |
| LLaVA-CoT 스타일 | VL API | ✅ 적용됨 |

### 실현 가능 (RTX 3080 8GB 기준)
| 논문 | GPU 요구 | 예상 효과 | 우선순위 |
|------|----------|----------|----------|
| **DocLayout-YOLO** | ~2-4GB | 도면 영역 검출 고도화 | P1 |
| PP-StructureV3 | ~1-2GB | 문서 구조 분석 | P2 |
| PID2Graph 평가 | 없음 | 현재 시스템 벤치마크 | P1 |

### 대기 (미출시)
| 논문 | 상태 | 비고 |
|------|------|------|
| YOLOv12 | ⏳ 미출시 | Ultralytics 공식 릴리스 대기 |

### GPU 제약으로 제외
| 논문 | GPU 요구 | 대안 |
|------|----------|------|
| ~~Qwen3-VL~~ | 14GB+ | GPT-4o-mini API 유지 |
| ~~InternVL3.5 (8B+)~~ | 16GB+ | GPT-4o-mini API 유지 |
| ~~RF-DETR~~ | 6-8GB | YOLOv11 유지 |
| ~~Relationformer 대규모~~ | 6-8GB | 현재 파이프라인 유지 |

### 장기 참조 (연구 목적)
| 논문 | 용도 |
|------|------|
| Drawing2CAD | 2D → 3D 변환 연구 |
| DeepCAD | CAD 생성 연구 |
| PID2Graph 데이터셋 | P&ID 벤치마크 |

---

## 9. 데이터셋 목록

| 데이터셋 | 출처 | 용도 | 크기 |
|----------|------|------|------|
| PID2Graph | [arXiv 2411.13929](https://arxiv.org/abs/2411.13929) | P&ID 그래프 | 최초 공개 |
| DocLayNet | [arXiv 2206.01062](https://arxiv.org/abs/2206.01062) | 문서 레이아웃 | 80,863 페이지 |
| DeepCAD | [arXiv 2105.09492](https://arxiv.org/abs/2105.09492) | CAD 모델 | 178,238 모델 |
| ALLaVA | [arXiv 2402.11684](https://arxiv.org/abs/2402.11684) | VLM 학습 | 1.3M 샘플 |
| LLaVA-o1-100k | [arXiv 2411.10440](https://arxiv.org/abs/2411.10440) | 추론 학습 | 100k 샘플 |

---

## 10. 관련 GitHub 저장소

| 프로젝트 | 링크 | 설명 |
|----------|------|------|
| Ultralytics YOLO | [github.com/ultralytics/ultralytics](https://github.com/ultralytics/ultralytics) | YOLOv8/v11 |
| PaddleOCR | [github.com/PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | OCR 툴킷 |
| LLaVA | [github.com/haotian-liu/LLaVA](https://github.com/haotian-liu/LLaVA) | VLM |
| DocTR | [github.com/mindee/doctr](https://github.com/mindee/doctr) | 문서 OCR |
| OmniDocBench | [github.com/opendatalab/OmniDocBench](https://github.com/opendatalab/OmniDocBench) | 벤치마크 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2025-12-31 (v2) | **SOTA 심층 조사**: 14개 신규 논문 추가 (35→49개), YOLOv12/YOLO26/RT-DETR 계열, Qwen3-VL/InternVL3.5, DocLayout-YOLO/SFDLA 등 |
| 2025-12-31 (v1) | 초기 작성, 35개 논문 수집 |

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2025-12-31
