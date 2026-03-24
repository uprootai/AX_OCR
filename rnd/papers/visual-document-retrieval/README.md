# Visual Document Retrieval & AutoRAG Research

> **작성일**: 2026-03-24
> **출처**: 테디노트 유튜브 라이브 방송 녹취록 기반
> **범위**: 시각적 문서 검색(VDR), VisRAG, AutoRAG Research, 에이전틱 RAG

---

## 1. 배경: 파일 시스템 vs 벡터 DB

| 환경 | 최적 방식 | 비고 |
|------|-----------|------|
| 개인 PC / 소규모 레포 | 파일 시스템 (Claude Code 등) | 모델이 파일 시스템 탐색에 최적화됨 |
| 10만~200만건 기업 데이터 | 벡터 DB + 그래프 | 파일 시스템만으로 한계 |
| 수백 페이지 PDF | 벡터 DB + VDR | 시각적 정보 손실 방지 |

**향후 방향**: 파일 시스템 + 벡터 DB + 그래프 → **하이브리드** 진화

---

## 2. 시각적 문서 검색 (Visual Document Retrieval)

### 기존 RAG의 문제

```
PDF → OCR → 레이아웃 디텍션 → 텍스트 변환 → 청킹 → 임베딩 → 검색
                    ↑
              표/차트/다이어그램에서 정보 손실 심각
```

### VDR 접근법

```
PDF 페이지 → 이미지 그대로 → VLM으로 임베딩 → 검색
                    ↑
              OCR 없음, 파싱 없음, 정보 손실 없음
```

### 작동 원리: MaxSim (Late Interaction)

1. 이미지를 **1024개 패치 토큰**으로 분할
2. 각 패치를 **128차원 벡터**로 임베딩
3. 검색 시 텍스트 쿼리 토큰 ↔ 이미지 패치 토큰 간 **코사인 유사도** 전수 계산
4. 각 쿼리 토큰별 **최대 유사도(Max)**를 합산 → 최종 점수

```
쿼리 토큰 [q1, q2, q3]
문서 패치 [p1, p2, ..., p1024]

score = sum(max(cos(qi, pj) for j in 1..1024) for i in 1..3)
```

---

## 3. 핵심 모델

### 3.1 ColPali (콜팔리)

| 항목 | 값 |
|------|---|
| 역할 | VDR 분야를 연 기념비적 모델 |
| 기반 | ColBERT의 Late Interaction을 이미지 패치로 확장 |
| 인덱싱 속도 | **0.39초** (엔드투엔드, 파싱 불필요) |
| 패치 수 | 1024개 |

### 3.2 ColQwen (콜큐엔)

| 항목 | 값 |
|------|---|
| 기반 | 알리바바 Qwen 백본 파인튜닝 |
| 성능 | **현재 SOTA** |
| 버전 | ColQwen 2.5, 3 |

### 3.3 ColPlo (콜플로)

| 항목 | 값 |
|------|---|
| 파라미터 | **174M** (ColQwen 7B의 1/40) |
| 패치 수 | ~500개 (절반) |
| 성능 저하 | 최소화 |
| 용도 | 검색 속도 + 저장 용량 효율 극대화 |

### 3.4 ColBERT (원조)

| 항목 | 값 |
|------|---|
| 역할 | MaxSim (Late Interaction) 최초 제안 |
| 방식 | 텍스트 토큰 기반 (ColPali가 이를 이미지 패치로 확장) |

---

## 4. 시각적 RAG 파이프라인

### 4.1 VisRAG (비즈레그)

```
쿼리 → ColPali 검색 → 이미지 결과 → VLM에 이미지 그대로 입력 → 답변 생성
                                        ↑
                              텍스트 변환 없이 이미지 직접 사용
```

- 속도 개선: MaxSim 대신 **Average Pooling** (패치 임베딩 평균) 옵션

### 4.2 VDoc-RAG (브이독레그)

- **모달리티 격차(Modality Gap)** 해소에 집중
- 프리트레이닝: 이미지 인코더 ↔ 텍스트 인코더 간 격차 축소
- **EOS 토큰**에 이미지 정보 압축 → 효율적 검색

---

## 5. 한계점 및 고려사항

### 연산량 및 벡터 DB

| 문제 | 설명 |
|------|------|
| MaxSim 연산량 | 쿼리 토큰 × 패치 토큰 전수 유사도 계산 → 연산 비용 높음 |
| 멀티벡터 저장 | 문서 1개 = 벡터 1024개 → **Qdrant**, **pgvecto.rs** 등 특정 DB만 지원 |
| 대규모 검색 | 수백만 페이지에서 병목 가능 |

### 한국어 한계

- 영어/프랑스어 등 다국어 성능 검증됨
- **한국어 학습 데이터 극히 부족** → 별도 SFT(LoRA 파인튜닝) 권장

### VLM 성능 한계 (Oracle 격차)

- ViDoRe V3 벤치마크: 정답 문서를 찾아줘도 VLM이 답 못 맞히는 비율 **~35%**
- 바운딩 박스 정확도: AI vs 사람 격차 아직 큼

---

## 6. 최신 하이브리드 / 에이전트 결합 기법

### 6.1 동적 Top-K (GMM 기반)

- 고정 Top-K 대신 유사도 점수 분포를 **GMM(가우시안 혼합 모델)**로 분석
- 쿼리별로 K값을 **동적으로 조절**

### 6.2 에이전틱 RAG (Agentic RAG)

```
[Seeker] → 문서 검색
    ↓
[Inspector] → 검색 결과 검증 (충분한가?)
    ↓ (불충분 → Seeker로 반복)
[Answer] → 최종 답변 생성
```

- **Test-Time Scaling**: 시간 더 쓰더라도 정확도 극대화
- "RAG는 죽었다" → 아님, **RAG + 에이전트 결합**이 미래

### 6.3 멀티모달 지식 그래프

- 이미지 + 레이아웃 + 텍스트 임베딩 + **Knowledge Graph** 융합
- 벤치마크 리콜률 **98%** (이론적)
- 실제 구축 난이도 **극도로 높음**

### 6.4 반론: SeVaL 등

- VLM으로 **비주얼 캡셔닝**(이미지→텍스트 설명)을 잘 하거나
- 텍스트 임베딩 모델 **차원 크기만 늘려도** VDR보다 좋을 수 있다는 반박

---

## 7. AutoRAG Research

### 기존 문제

- 최신 RAG 논문 쏟아지지만 데이터 포맷/코드 환경이 제각각
- 재현(Reproduction)이 매우 어려움

### AutoRAG Research 특징

| 항목 | 값 |
|------|---|
| 벤치마크 | ViDoRe 등 다양한 데이터셋 내장 |
| 임베딩 | 사전 계산(Pre-embedded) 제공 |
| DB | **PostgreSQL** 기반 재구축 |
| 설계 | **CLI 중심** (AI 에이전트 친화적) |
| 지원 | 에이전틱 RAG 파이프라인 |

### AutoRAG Data (별도 앱)

- **GUI 기반 Mac 앱** — 도메인 전문가용
- 평가 데이터셋(Ground Truth) 생성 도구
- 복잡한 로직 반영 가능 (예: A AND B 조건)

---

## 8. AI 시대 개발자 생존 전략

| 줄어드는 가치 | 늘어나는 가치 |
|--------------|--------------|
| 단순 코딩 구현 | **문제 정의 능력** |
| "어떻게 만들 것인가" | **"무엇을 만들 것인가"** |
| | 아키텍처 설계 능력 |

**방법**: 짧은 시간 안에 최대한 많은 오픈소스 프로젝트를 직접 만들어보기

---

## 9. 논문 목록

### 핵심 VDR 모델 (PDF 다운로드 완료)

| # | 논문/모델 | arXiv | 파일 | 핵심 |
|---|-----------|-------|------|------|
| 1 | **ColPali** (ICLR 2025) | [2407.01449](https://arxiv.org/abs/2407.01449) | `colpali_2407.01449.pdf` | VDR 개척, MaxSim + 이미지 패치 |
| 2 | **ColQwen** | ColPali 논문 v4~v6에 포함 | (위와 동일) | Qwen2-VL-2B 백본, 현재 SOTA |
| 3 | **ColFlor** (IEEE MLSP 2025) | [OpenReview](https://openreview.net/forum?id=DrvZsa2GpN) | `colflor_colplo.pdf` | 174M, ColPali 대비 17x 작고 9.8x 빠름, 성능 저하 1.8% |
| 4 | **VisRAG** | [2410.10594](https://arxiv.org/abs/2410.10594) | `visrag_2410.10594.pdf` | 이미지→VLM 직접 입력, Average Pooling |
| 5 | **VDoc-RAG** | [2504.09795](https://arxiv.org/abs/2504.09795) | `vdocrag_2504.09795.pdf` | 모달리티 격차 해소, EOS 토큰 압축 |
| 6 | **ColBERT** | [2004.12832](https://arxiv.org/abs/2004.12832) | `colbert_2004.12832.pdf` | MaxSim(Late Interaction) 원조 |

### 벤치마크 및 방법론 (PDF 다운로드 완료)

| # | 논문/모델 | arXiv | 파일 | 핵심 |
|---|-----------|-------|------|------|
| 7 | **ViDoRe V1** | ColPali 논문에 포함 | (위와 동일) | VDR 평가 벤치마크 원본 |
| 8 | **ViDoRe V2** | [2505.17166](https://arxiv.org/abs/2505.17166) | `vidore-v2_2505.17166.pdf` | 난이도 상향 |
| 9 | **ViDoRe V3** | [2601.08620](https://arxiv.org/abs/2601.08620) | `vidore-v3_2601.08620.pdf` | 바운딩 박스 IOU까지 측정 |
| 10 | **ViDoRAG** (Agentic + GMM) | [2502.18017](https://arxiv.org/abs/2502.18017) | `vidorag_agentic_rag_gmm_topk_2502.18017.pdf` | Seeker/Inspector/Answer 3-에이전트 + GMM Dynamic Top-K (같은 논문) |
| 11 | **MAHA** (멀티모달 KG) | [2510.14592](https://arxiv.org/abs/2510.14592) | `multimodal_kg_rag_2510.14592.pdf` | 지식그래프 + 하이브리드 검색 |
| 12 | **MegaRAG** (멀티모달 KG) | [2512.20626](https://arxiv.org/abs/2512.20626) | `mega_rag_multimodal_kg_2512.20626.pdf` | MLLM 기반 KG 자동 구축 |
| 13 | **SERVAL** (반론) | [2509.15432](https://arxiv.org/abs/2509.15432) | `serval_anti_vdr_2509.15432.pdf` | VLM 캡셔닝 + 텍스트 임베딩이 VDR 능가 (Zero-shot) |

### 도구 및 프로젝트

| # | 프로젝트 | 링크 | 파일 | 핵심 |
|---|----------|------|------|------|
| 14 | **AutoRAG** | [GitHub](https://github.com/Marker-Inc-Korea/AutoRAG) | `autorag_2410.20878.pdf` | RAG 파이프라인 자동 최적화 |
| 15 | **AutoRAG Research** | [GitHub](https://github.com/NomaDamas/AutoRAG-Research) | — | CLI 중심, PostgreSQL, 에이전틱 RAG 지원 |
| 16 | **AutoRAG Data** | Mac 앱 | — | GUI 기반 GT 데이터셋 생성 |

---

## 10. 논문 상세 요약

### 10.1 ColPali — `colpali_2407.01449.pdf`

> **ColPali: Efficient Document Retrieval with Vision Language Models** (ICLR 2025)
> 저자: Manuel Faysse 외 (Illuin Technology + HuggingFace)

**문제**: 기존 문서 검색은 PDF → OCR → 레이아웃 감지 → 텍스트 추출 → 청킹 → 임베딩의 복잡한 파이프라인을 거치면서, 표·차트·다이어그램 등 시각 정보가 손실됨.

**핵심 제안**:
- PDF 페이지를 **이미지 그대로** VLM(PaliGemma 3B)에 넣어 **1024개 패치 임베딩**(128차원)을 추출
- ColBERT의 **Late Interaction(MaxSim)** 매커니즘을 이미지 패치로 확장
- 쿼리 텍스트 토큰과 이미지 패치 토큰 간 코사인 유사도의 최댓값을 합산하여 점수 산출

**ViDoRe 벤치마크**: 논문과 함께 VDR 전용 평가 벤치마크 **ViDoRe**(Visual Document Retrieval) 제안. TabFQuAD, DocVQA, InfoVQA 등 다양한 문서 QA 데이터셋 포함.

**결과**: 인덱싱 속도 0.39초/페이지 (기존 파싱 파이프라인 대비 즉시), 기존 텍스트 기반 검색 대비 시각적 문서에서 **대폭 우위**.

**ColQwen** (v4~v6에 포함): PaliGemma 대신 **Qwen2-VL-2B** 백본으로 파인튜닝. ViDoRe에서 **현재 SOTA**. 다국어 성능 개선.

---

### 10.2 ColBERT — `colbert_2004.12832.pdf`

> **ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT** (SIGIR 2020)
> 저자: Omar Khattab, Matei Zaharia (Stanford)

**문제**: BERT 기반 리랭킹은 정확하지만 쿼리-문서를 매번 쌍으로 인코딩해야 해서 느림. 반면 단일 벡터 비-임베딩은 빠르지만 정보 손실 큼.

**핵심 제안 — Late Interaction**:
- 쿼리와 문서를 **독립적으로** BERT 인코딩 (문서 임베딩은 오프라인 사전 계산 가능)
- 검색 시 쿼리 토큰 × 문서 토큰 간 **MaxSim** 연산만 수행
- `score = Σ_i max_j (q_i · d_j)` — 각 쿼리 토큰에 대해 가장 유사한 문서 토큰의 유사도를 합산

**결과**: MS MARCO에서 BERT 리랭커 수준의 정확도를 유지하면서 **170배 빠른** 검색 속도. 이후 ColPali, ColQwen 등 VDR 모델의 이론적 기반이 됨.

---

### 10.3 VisRAG — `visrag_2410.10594.pdf`

> **VisRAG: Vision-based Retrieval-augmented Generation on Multi-modality Documents** (ICLR 2025)
> 저자: Shi Yu 외 (Renmin University + Baichuan)

**문제**: 기존 RAG는 문서를 텍스트로 변환(파싱)한 후 검색·생성하므로 시각 정보(레이아웃, 이미지, 표 서식)가 손실됨.

**VisRAG 파이프라인**:
1. **VisRAG-Ret**: 문서 페이지를 이미지 그대로 임베딩하여 검색 (ColPali 기반)
2. **VisRAG-Gen**: 검색된 페이지 이미지를 VLM(GPT-4o, MiniCPM-V 등)에 직접 입력하여 답변 생성
   - 텍스트 변환 없이 이미지 → VLM 직접 투입

**페이지 연결 전략**:
- **Page Concatenation**: 여러 페이지 이미지를 하나로 합쳐서 VLM에 입력 (토큰 절약)
- **Weighted Selection**: 검색 점수 기반으로 페이지 선택

**결과**: TextRAG 대비 **25~39% 성능 향상**. 약한 생성 모델에서도 검색 단계의 시각 정보 보존이 큰 효과. Average Pooling으로 검색 속도도 개선 가능.

---

### 10.4 VDoc-RAG — `vdocrag_2504.09795.pdf`

> **VDocRAG: Retrieval-Augmented Generation over Visually-Rich Documents** (2025)
> 저자: Ryota Tanaka 외 (NTT + Tohoku University)

**문제**: VDR 모델(ColPali 등)은 텍스트 쿼리와 이미지 문서 사이의 **모달리티 격차(Modality Gap)**가 크고, 생성 단계에서 VLM이 검색된 이미지를 제대로 활용하지 못함.

**핵심 기법**:
1. **Dual-stage 사전학습**:
   - Stage 1: 텍스트-이미지 정렬 학습 (모달리티 격차 축소)
   - Stage 2: RAG 전용 파인튜닝 (검색→생성 파이프라인 최적화)
2. **EOS 토큰 압축**: 이미지의 1024개 패치 임베딩을 **EOS 토큰 하나**에 압축 → 단일 벡터 검색 가능 (저장/속도 효율 극대화)
3. **OpenDocVQA**: 새로운 대규모 평가 데이터셋 제안 (14K 질문, 5K 문서 페이지)

**결과**: ViDoRe, DocVQA 등에서 기존 VDR+VLM 파이프라인 대비 개선. 특히 모달리티 격차 해소가 핵심 기여.

---

### 10.5 ColFlor — `colflor_colplo.pdf`

> **ColFlor: Efficient Visual Document Retrieval with Small Language Models** (IEEE MLSP 2025)
> 저자: Manuel Faysse 외 (Illuin Technology)

**문제**: ColPali(3B), ColQwen(7B)은 성능은 좋지만 모델 크기가 커서 대규모 배포/실시간 검색에 비용 부담.

**핵심 제안**:
- **174M 파라미터** (ColQwen 7B의 1/40, ColPali 3B의 1/17)
- Florence-2 VLM 백본 기반 파인튜닝
- 패치 수 ~500개 (ColPali 1024개의 절반) → 저장 공간 절반

**결과**: ViDoRe V1에서 ColPali 대비 **1.8% 성능 저하**만으로 **17배 작고 9.8배 빠름**. 엣지 디바이스, 대규모 검색 시스템에서 비용 효율적 VDR 가능.

---

### 10.6 ViDoRe V2 — `vidore-v2_2505.17166.pdf`

> **ViDoRe2: A Robust Benchmark for Visually Rich Document Retrieval** (2025)
> 저자: Illuin Technology 팀

**문제**: ViDoRe V1은 텍스트만으로도 높은 점수를 받을 수 있어 VDR의 진짜 시각적 이해를 평가하기 어려움.

**개선 사항**:
- **Blind Contextual Query**: 문서 이미지를 보지 않고도 텍스트만으로 답할 수 있는 쿼리를 제거
- **시각 의존성 강화**: 표, 차트, 다이어그램을 반드시 이해해야 답할 수 있는 쿼리만 포함
- **다국어**: 영어 외 프랑스어, 독일어, 스페인어 등

**결과**: 기존 SOTA 모델들의 점수가 V1 대비 **상당히 하락** → 시각적 이해력 차이를 더 잘 변별함.

---

### 10.7 ViDoRe V3 — `vidore-v3_2601.08620.pdf`

> **ViDoRe V3: A Comprehensive Benchmark for Visually Rich Document Retrieval and Answering** (2026)
> 저자: Illuin Technology + NVIDIA

**규모**: 26,000 페이지, 3,099 쿼리, 6개 언어, **12,000시간** 인간 어노테이션.

**새로운 평가 축**:
1. **검색 성능**: 기존 nDCG@5
2. **바운딩 박스 IOU**: 정답 영역을 문서 내에서 정확히 짚어내는 능력 (Grounding)
3. **답변 정확도**: 검색 후 VLM이 실제로 정답을 맞히는지 (Oracle Gap 측정)

**Oracle Gap 발견**: 정답 페이지를 제공해도 VLM이 답을 못 맞히는 비율이 **~35%**. 검색보다 **생성 단계가 병목**임을 입증.

---

### 10.8 ViDoRAG — `vidorag_agentic_rag_gmm_topk_2502.18017.pdf`

> **ViDoRAG: Visual Document Retrieval-Augmented Generation via Dynamic Multi-Modal Retrieval and Self-Reflective Agentic Reasoning** (2025)
> 저자: Alibaba Group

**문제**: 고정 Top-K 검색은 쿼리 난이도를 무시하고 일정한 수의 문서를 반환 → 쉬운 질문에 과도한 검색, 어려운 질문에 부족한 검색.

**2가지 핵심 기법**:

1. **GMM Dynamic Top-K**: 유사도 점수 분포를 **가우시안 혼합 모델(GMM)**로 분석하여 쿼리별로 K값을 동적 조절. 고유사도 클러스터와 저유사도 클러스터의 경계를 자동 결정.

2. **Agentic RAG (3-에이전트)**:
   - **Seeker**: 문서 검색 수행
   - **Inspector**: 검색 결과가 충분한지 검증 (불충분하면 Seeker에게 재검색 요청)
   - **Answer**: 최종 답변 생성

**결과**: ViDoRe 기반 실험에서 기존 방법 대비 **10% 이상 정확도 향상**. Test-Time Scaling 효과 — 추론 시간을 더 투자할수록 성능 개선.

---

### 10.9 MAHA — `multimodal_kg_rag_2510.14592.pdf`

> **MAHA: A Multimodal-Aware Hybrid-RAG Architecture** (2025)
> 저자: NIT Karnataka

**문제**: 텍스트 전용 RAG는 이미지/표/차트 정보 손실, 단일 검색 전략은 다양한 쿼리 유형에 대응 불가.

**아키텍처**:
1. **Knowledge Graph 구축**: 문서에서 엔티티/관계를 추출하여 그래프 구성
2. **멀티모달 임베딩**: 텍스트 + 이미지 + 레이아웃을 결합한 임베딩
3. **하이브리드 검색**: KG 기반 구조적 검색 + 벡터 유사도 검색을 쿼리 유형에 따라 동적 선택

**결과**: ROUGE-L 0.486, 벤치마크 리콜률 **98%** (이론적). 실제 구축 난이도는 극도로 높음 — KG 수동 구축/검증 비용.

---

### 10.10 MegaRAG — `mega_rag_multimodal_kg_2512.20626.pdf`

> **MegaRAG: A System for Multimodal Multi-hop Question Answering** (2025)
> 저자: NTU (Nanyang Technological University)

**문제**: 멀티모달 문서에서 여러 홉(multi-hop)을 거치는 복잡한 질문에 기존 RAG가 대응 불가.

**핵심 기법**:
1. **MLLM 기반 KG 자동 구축**: GPT-4V 등 멀티모달 LLM을 사용해 문서에서 엔티티·관계를 자동 추출하여 Knowledge Graph 구성 (수동 구축 대신)
2. **Cross-Modal Reasoning**: 텍스트 노드 → 이미지 노드 → 텍스트 노드로 이어지는 그래프 경로를 따라 추론
3. **Evidence Chain**: 질문을 하위 질문으로 분해 → 각 하위 질문별로 KG 탐색 → 증거 체인 구성 → 최종 답변

**결과**: MultimodalQA, WebQA 등에서 기존 RAG 대비 개선. 특히 2-3홉 질문에서 큰 차이.

---

### 10.11 SERVAL — `serval_anti_vdr_2509.15432.pdf`

> **SERVAL: Synergy Learning between Vertical Models and LLMs towards Oracle-Level Zero-shot Information Retrieval** (2025)
> 저자: University of Amsterdam

**핵심 주장 (VDR에 대한 반론)**:
- VDR 전용 모델(ColPali 등) 없이도 **VLM 캡셔닝 + 텍스트 임베딩**으로 동등하거나 더 나은 검색 가능

**방법 — Generate-then-Encode**:
1. VLM(GPT-4o 등)으로 문서 이미지의 **상세 텍스트 캡션** 생성
2. 생성된 캡션을 일반 **텍스트 임베딩 모델**(E5, BGE 등)로 인코딩
3. 기존 텍스트 검색 인프라로 검색

**결과**: ViDoRe에서 **63.4% nDCG@5** — ColPali(58.5%)를 **Zero-shot으로** 능가. 별도 파인튜닝 불필요.

**시사점**: VDR 전용 모델 학습/배포 대신 범용 VLM + 기존 텍스트 검색 인프라를 활용하는 것이 더 실용적일 수 있음. 단, VLM 캡셔닝 비용(API 호출)이 추가됨.

---

### 10.12 AutoRAG — `autorag_2410.20878.pdf`

> **AutoRAG: Automated Framework for optimization of Retrieval Augmented Generation Pipeline** (2024)
> 저자: Markr Inc. (한국)

**문제**: RAG 파이프라인의 구성 요소(청킹, 임베딩, 검색, 리랭킹, 프롬프트, 생성 모델)가 너무 많아서 최적 조합을 수동으로 찾기 어려움.

**AutoML 스타일 접근**:
1. **평가 데이터셋 기반**: QA 쌍 + 정답 문서(Ground Truth)를 준비
2. **조합 탐색**: 각 단계별 후보(임베딩 모델 3종, 청킹 전략 4종, 리랭커 2종 등)를 자동 조합
3. **자동 평가**: 각 조합의 성능을 Recall, MRR, F1 등으로 측정
4. **최적 파이프라인 출력**: 가장 성능 좋은 조합을 YAML로 내보내기

**결과**: 수작업 대비 **최적 조합 탐색 시간 90% 절감**. 도메인별 최적 RAG 구성이 크게 다름을 실증 (의료 vs 법률 vs 기술 문서).

---

## 11. AX POC 프로젝트 적용 가능성

| VDR 기술 | AX POC 적용 | 우선순위 |
|----------|------------|----------|
| ColPali/ColQwen | 대규모 도면 검색 시스템 | P2 (현재 소규모) |
| VisRAG | 도면 이미지 기반 Q&A | P3 (장기) |
| Agentic RAG | 복잡한 BOM 교차검증 자동화 | P2 |
| AutoRAG Research | RAG 파이프라인 평가/최적화 | P2 |
| Dynamic Top-K (GMM) | 검색 정확도 개선 | P3 |
| **BMT 도면-BOM 검증에 직접 적용** | pdfplumber로 충분 (VDR 불필요) | — |

### BMT 케이스와의 관계

BMT 도면은 벡터 PDF(텍스트 레이어 존재)이므로 VDR이 필요 없지만,
**스캔본 도면이 들어오거나** 대규모 도면 DB 검색이 필요해지면 ColPali/VisRAG가 직접적으로 적용 가능합니다.

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-24 | 초기 작성 — 테디노트 녹취록 기반 13개 논문/프로젝트 정리 |
| 2026-03-24 | 12개 논문 상세 요약 추가 (섹션 10) |

---

*작성자*: Claude Code (Opus 4.6)
*최종 업데이트*: 2026-03-24
