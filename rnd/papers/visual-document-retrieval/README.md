# Visual Document Retrieval — 실용성 중심 정리

> **작성일**: 2026-03-24 | **재편성**: 2026-03-24
> **출처**: 테디노트 유튜브 라이브 방송 녹취록 + 논문 12편 정독
> **평가 기준**: RTX 3080 8GB / 유료 API 없음 / 로컬 전용 / DSE Bearing·BMT 프로젝트

---

## TL;DR — 3줄 요약

1. **지금 쓸 것**: AutoRAG (파이프라인 최적화), ViDoRAG의 GMM Dynamic Top-K (알고리즘만 차용)
2. **도면 DB 커지면**: ColFlor (174M, RTX 3080 여유) → 도면 시각 검색
3. **무시해도 됨**: MAHA/MegaRAG (KG 구축 비용 >> 이득), SERVAL (유료 API 필수)

---

## 제약 조건 (우리 환경)

| 항목 | 값 |
|------|---|
| GPU | RTX 3080 8GB (VRAM 한계) |
| 유료 API | **없음** (GPT-4o, Claude API 등 사용 안 함) |
| 모델 운영 | 18개 서비스 전부 로컬 |
| 도면 규모 | DSE Bearing ~100장, BMT ~수십장 (현재 소규모) |
| 도면 형태 | DSE: 스캔본 (이미지), BMT: 벡터 PDF (텍스트 레이어 존재) |

---

## Tier 1: 지금 바로 적용 가능

### 1.1 AutoRAG — `autorag_2410.20878.pdf`

> **AutoRAG: Automated Framework for optimization of Retrieval Augmented Generation Pipeline** (2024)
> Markr Inc. (한국)

**왜 1순위인가**:
- 우리 파이프라인에 OCR, YOLO, VLM 분류, 앙상블 등 **조합 가능한 단계가 이미 많음**
- GT 데이터 보유 (DSE 87도면, BMT BOM)
- AutoML처럼 조합을 자동 탐색 → 수작업 튜닝 시간 **90% 절감**
- GPU 부담 없음 (평가 프레임워크, 별도 모델 학습 아님)
- **한국 회사** → 한국어 문서, 커뮤니티 지원

**작동 방식**:
1. QA 쌍 + 정답 문서(GT) 준비
2. 각 단계별 후보 조합 자동 탐색 (임베딩 3종 × 청킹 4종 × 리랭커 2종 등)
3. Recall, MRR, F1 등으로 자동 평가
4. 최적 파이프라인을 YAML로 출력

**핵심 발견**: 도메인별 최적 RAG 구성이 완전히 다름 (의료 ≠ 법률 ≠ 기술 문서). 즉, **우리 도면 도메인 전용 최적 조합**을 찾아야 함.

**적용 시나리오**:
- DSE Bearing: 치수 추출 파이프라인 (OCR → 앙상블 → 검증)의 최적 조합 탐색
- BMT: BOM 매칭 정확도 개선을 위한 파싱/검색/매칭 단계 최적화

---

### 1.2 GMM Dynamic Top-K (ViDoRAG에서 알고리즘만 차용)

> **ViDoRAG** 논문의 GMM 기법을 우리 앙상블 투표 시스템에 적용

**현재 문제**: 앙상블에서 고정 Top-K나 고정 임계값을 사용 → 쉬운 도면에 과도한 후보, 어려운 도면에 부족한 후보

**GMM 아이디어**:
- 유사도 점수 분포를 가우시안 혼합 모델로 분석
- 고확신 클러스터 vs 저확신 클러스터의 경계를 **자동 결정**
- 도면별로 K값(후보 수)을 동적 조절

**구현 난이도**: 낮음 (`sklearn.mixture.GaussianMixture` 몇 줄이면 됨)
**GPU 필요**: 없음 (CPU 연산)
**기대 효과**: 앙상블 v5+ 투표 정확도 개선

---

## Tier 2: 도면 DB 확장 시 유망 (중기)

### 2.1 ColFlor/ColPlo — `colflor_colplo.pdf`

> **ColFlor: Efficient Visual Document Retrieval with Small Language Models** (IEEE MLSP 2025)
> Illuin Technology

**왜 ColPali/ColQwen이 아니라 ColFlor인가**:

| | ColPali | ColQwen | **ColFlor** |
|---|---------|---------|-------------|
| 파라미터 | 3B | 7B | **174M** |
| VRAM | ~12GB | ~16GB | **~2GB** |
| RTX 3080 | 빠듯 | **불가** | **여유** |
| 속도 | 1x | 0.8x | **9.8x** |
| 성능 (nDCG@5) | 기준 | +3% | **-1.8%** |
| 패치 수 | 1024개 | 1024개 | **~500개** (저장 절반) |

- Florence-2 VLM 백본 → 174M으로 ColPali 성능의 98.2% 달성
- RTX 3080 8GB에서 **충분히** 실시간 검색 가능

**적용 시점**: DSE Bearing 도면이 수백~수천장으로 확대될 때
**적용 시나리오**: "OD 150mm, 5000RPM 터빈 베어링 도면 찾아줘" → 시각적 유사 도면 검색

---

### 2.2 VisRAG — `visrag_2410.10594.pdf`

> **VisRAG: Vision-based Retrieval-augmented Generation on Multi-modality Documents** (ICLR 2025)
> Renmin University + Baichuan

**파이프라인**:
```
쿼리 → ColPali/ColFlor 검색 → 이미지 결과 → VLM에 직접 입력 → 답변 생성
                                                ↑
                                    텍스트 변환 없이 이미지 그대로
```

**왜 Tier 2인가**:
- 검색(Ret) 단계: ColFlor로 대체 가능 → OK
- 생성(Gen) 단계: VLM에 이미지 직접 투입 → **로컬 VLM 성능이 관건**
- MiniCPM-V 등 경량 VLM으로 Gen 가능하지만, **현재 우리 도면은 OCR+YOLO로 충분히 처리 중**

**TextRAG 대비 25~39% 향상**이라는 수치는 인상적이지만, 우리는 이미 도면 특화 파이프라인이 있어서 범용 RAG와의 비교는 의미가 제한적.

**적용 시점**: 도면 Q&A 시스템 구축 시 ("이 도면의 허용 공차는?")

---

### 2.3 VDoc-RAG — `vdocrag_2504.09795.pdf`

> **VDocRAG: Retrieval-Augmented Generation over Visually-Rich Documents** (2025)
> NTT + Tohoku University

**독자적 기여 — EOS 토큰 압축**:
- 이미지 1024개 패치 임베딩 → **EOS 토큰 1개로 압축**
- 멀티벡터(1024개) 대신 **단일 벡터** 검색 가능
- Qdrant 같은 특수 DB 불필요 → **기존 벡터 DB로 충분**

**왜 Tier 2인가**:
- 모달리티 격차(텍스트 쿼리 ↔ 이미지 문서) 해소가 핵심이지만
- Dual-stage 사전학습이 필요 → 직접 학습해야 하므로 GPU/시간 비용 있음
- EOS 압축 아이디어만 차용하면 ColFlor + 단일벡터 검색으로 활용 가능

---

## Tier 3: 과대평가 / 우리에겐 불필요

### 3.1 MAHA — `multimodal_kg_rag_2510.14592.pdf` ❌

> NIT Karnataka | 리콜률 98% (이론)

**과대평가 이유**:
- 98% 리콜은 **수동 구축한 KG 위에서** 달성 → KG 구축 비용이 숨겨져 있음
- 우리 도면 수백장 규모에서 Knowledge Graph 구축/유지 비용 >> 실제 이득
- 엔티티/관계 추출 품질이 도메인 전문성에 극도로 의존
- **수만건 이상 대기업 도면 DB가 아니면 ROI 없음**

**읽을 가치**: 하이브리드 검색(구조적 + 벡터) 아이디어 자체는 참고할 만함

---

### 3.2 MegaRAG — `mega_rag_multimodal_kg_2512.20626.pdf` ❌

> NTU | MLLM 기반 KG 자동 구축

**MAHA보다 한 단계 진화** — GPT-4V로 KG를 자동 구축하므로 수동 비용 제거.

**그래도 불필요한 이유**:
- GPT-4V API 호출 필수 → **유료 API 없음** 원칙 위반
- 로컬 VLM으로 대체하면 KG 품질 급락
- Multi-hop 추론("A 베어링의 재질이 B 도면의 허용 하중과 호환되는가?")은 우리 현재 요구사항이 아님
- 도면 수가 수만건 이상이고 도면 간 관계가 복잡할 때나 의미 있음

---

### 3.3 SERVAL — `serval_anti_vdr_2509.15432.pdf` ❌

> University of Amsterdam | Zero-shot으로 ColPali 능가 (63.4% vs 58.5%)

**함정**:
- "VDR 모델 없이도 된다"는 주장이 매력적이지만
- **매 문서마다 GPT-4o 캡셔닝 API 호출 필수** → 유료 API 원칙 위반
- 로컬 VLM 캡셔닝으로 대체하면? → 캡션 품질 하락으로 이점 소멸
- 결국 "유료 API로 좋은 캡션 → 텍스트 검색"이 핵심인데, 우리는 유료 API를 안 씀

**읽을 가치**: Generate-then-Encode 패턴 자체는 로컬 VLM이 충분히 강해지면 재평가 가능

---

### 3.4 ViDoRAG (에이전트 부분) — `vidorag_agentic_rag_gmm_topk_2502.18017.pdf` ⚠️

> Alibaba | Seeker/Inspector/Answer 3-에이전트

**GMM Dynamic Top-K는 Tier 1으로 차용했지만**, 에이전트 부분은 별개:
- Seeker → Inspector → Answer 루프는 **VLM 호출을 3배 이상** 증가시킴
- "시간을 더 쓰면 정확도 올라간다" (Test-Time Scaling)는 사실이지만
- 우리 도면 분석은 **배치 처리** — 에이전트 루프의 실시간 대화형 이점이 적음
- 기존 3단계 검증 시스템(Agent Verification)이 이미 유사한 역할 수행 중

---

## 참고: 이론적 기반 (직접 적용은 아니지만 읽어둘 가치)

### ColBERT — `colbert_2004.12832.pdf`

> **Late Interaction (MaxSim) 원조** (SIGIR 2020, Stanford)

- 쿼리/문서를 독립 인코딩 → MaxSim으로 매칭
- `score = Σ_i max_j (q_i · d_j)`
- ColPali, ColQwen, ColFlor **전부 이 위에 세워짐**
- MS MARCO에서 BERT 리랭커 수준 정확도 + 170배 빠른 검색

**왜 직접 안 쓰는가**: 텍스트 전용 모델. 우리는 이미지(도면)를 다루므로 ColFlor 사용.

---

### ColPali — `colpali_2407.01449.pdf`

> **VDR의 기념비적 논문** (ICLR 2025, Illuin Technology)

- PDF 페이지 → 이미지 그대로 → PaliGemma 3B → 1024개 패치 × 128차원 임베딩
- ColBERT의 MaxSim을 이미지 패치로 확장
- **ViDoRe 벤치마크** 함께 제안
- 인덱싱 0.39초/페이지

**왜 ColFlor를 대신 추천하는가**: ColPali 3B은 RTX 3080에서 빠듯함. ColFlor가 1.8% 성능 양보로 17배 작고 9.8배 빠름.

---

### ViDoRe V2 — `vidore-v2_2505.17166.pdf`

> **시각 이해 변별력 강화 벤치마크** (Illuin Technology)

- V1 문제: 텍스트만으로도 높은 점수 가능 → 시각 이해 미평가
- V2: 시각 의존적 쿼리만 포함 (표/차트/다이어그램 필수 이해)
- 기존 SOTA 점수 **대폭 하락** → 진짜 실력 차이 드러남

---

### ViDoRe V3 — `vidore-v3_2601.08620.pdf`

> **가장 포괄적인 VDR 벤치마크** (Illuin + NVIDIA, 2026)

- 26,000 페이지, 3,099 쿼리, 6개 언어, 12,000시간 어노테이션
- **3가지 평가축**: 검색 nDCG@5 + 바운딩 박스 IOU + 답변 정확도

**핵심 발견 — Oracle Gap**:
- 정답 페이지를 줘도 VLM이 답 못 맞히는 비율 **~35%**
- **검색이 아니라 생성 단계가 병목** → 검색만 좋게 해봐야 한계 있음
- 우리 파이프라인에서도 동일: OCR/YOLO 검출 후 **해석/매칭 단계**가 더 중요

---

## 논문 파일 목록

| Tier | 논문 | 파일 | 핵심 한줄 |
|------|------|------|----------|
| **1** | AutoRAG | `autorag_2410.20878.pdf` | RAG 파이프라인 AutoML 최적화 (한국) |
| **1** | ViDoRAG (GMM만) | `vidorag_agentic_rag_gmm_topk_2502.18017.pdf` | Dynamic Top-K → 앙상블 투표 적용 |
| **2** | ColFlor | `colflor_colplo.pdf` | 174M, RTX 3080 OK, 도면 시각 검색 |
| **2** | VisRAG | `visrag_2410.10594.pdf` | 이미지→VLM 직접 RAG, 25~39% 향상 |
| **2** | VDoc-RAG | `vdocrag_2504.09795.pdf` | EOS 압축 → 단일벡터 검색 가능 |
| ❌ | MAHA | `multimodal_kg_rag_2510.14592.pdf` | KG 구축 비용 >> 이득 (소규모) |
| ❌ | MegaRAG | `mega_rag_multimodal_kg_2512.20626.pdf` | GPT-4V 필수, 유료 API 위반 |
| ❌ | SERVAL | `serval_anti_vdr_2509.15432.pdf` | GPT-4o 캡셔닝 필수, 유료 API 위반 |
| ⚠️ | ViDoRAG (에이전트) | (위와 동일) | 3배 VLM 호출, 배치에 부적합 |
| 참고 | ColBERT | `colbert_2004.12832.pdf` | MaxSim 원조, 이론적 기반 |
| 참고 | ColPali | `colpali_2407.01449.pdf` | VDR 개척, ColFlor의 기반 |
| 참고 | ViDoRe V2 | `vidore-v2_2505.17166.pdf` | 시각 이해 변별력 벤치마크 |
| 참고 | ViDoRe V3 | `vidore-v3_2601.08620.pdf` | Oracle Gap 35% 발견 |

---

## 실행 로드맵

```
Phase 1 (즉시)
├── AutoRAG로 현재 치수 추출 파이프라인 최적화
│   ├── DSE 87도면 GT 활용
│   └── OCR × 앙상블 × 검증 조합 탐색
└── GMM Dynamic Top-K를 앙상블 v6에 적용
    └── sklearn.mixture.GaussianMixture (CPU, 구현 ~50줄)

Phase 2 (도면 DB 확대 시)
├── ColFlor 도입 → "유사 도면 검색" 기능
│   ├── 174M 모델 → RTX 3080에서 실시간
│   └── Qdrant 또는 pgvecto.rs 멀티벡터 저장
└── VisRAG-Ret 파이프라인 (ColFlor 검색 + 로컬 VLM 생성)

Phase 3 (장기, 조건부)
├── VDoc-RAG EOS 압축 기법 → 단일벡터 검색 (저장 효율)
└── 로컬 VLM 성능 충분 시 SERVAL 재평가 (Generate-then-Encode)
```

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-24 | 초기 작성 — 테디노트 녹취록 기반 13개 논문/프로젝트 정리 |
| 2026-03-24 | 12개 논문 상세 요약 추가 |
| 2026-03-24 | **실용성 중심 재편성** — Tier 1/2/3 + 과대평가 분석 + 실행 로드맵 |

---

*작성자*: Claude Code (Opus 4.6)
*최종 업데이트*: 2026-03-24
