# VDR (Visual Document Retrieval) 연구 검토

> **작성일**: 2026-03-24
> **상태**: 검토 완료, 적용 시점 대기
> **관련 자료**: `rnd/papers/visual-document-retrieval/` (논문 12편 + 실용성 분석)

---

## 요약

PDF/도면을 이미지 그대로 검색·분석하는 VDR 기술 12편을 검토했습니다.
유료 API 없이 RTX 3080 8GB 로컬 환경에서 실제 적용 가능한 것만 추렸습니다.

---

## 적용 가능 기술

### 1. AutoRAG — 파이프라인 자동 최적화 (즉시 적용 가능)

- **내용**: OCR × 앙상블 × 검증 등 단계별 조합을 AutoML처럼 자동 탐색하여 최적 파이프라인 도출
- **왜 가능**: GPU 부담 없음 (평가 프레임워크), GT 데이터 보유 (DSE 87도면, BMT BOM)
- **한국 회사** (Markr) — 한국어 지원, 커뮤니티 활성
- **적용 대상**: DSE Bearing 치수 추출, BMT BOM 매칭 정확도 개선
- **논문**: `rnd/papers/visual-document-retrieval/autorag_2410.20878.pdf`

### 2. GMM Dynamic Top-K — 앙상블 투표 개선 (즉시 적용 가능)

- **내용**: 고정 임계값 대신 유사도 점수 분포를 GMM으로 분석, 도면별로 후보 수를 동적 조절
- **왜 가능**: CPU 연산, sklearn 몇 줄 구현
- **적용 대상**: DSE Bearing 앙상블 v6 투표 정확도 개선
- **논문**: `rnd/papers/visual-document-retrieval/vidorag_agentic_rag_gmm_topk_2502.18017.pdf`

### 3. ColFlor — 경량 도면 시각 검색 (도면 DB 확대 시)

- **내용**: 174M 파라미터로 도면 이미지를 임베딩, "유사 도면 검색" 가능
- **왜 가능**: RTX 3080 VRAM 2GB로 충분, ColPali 대비 성능 98.2% 유지
- **적용 시점**: 도면이 수백~수천장으로 확대될 때
- **논문**: `rnd/papers/visual-document-retrieval/colflor_colplo.pdf`

---

## 검토했으나 현재 불필요한 기술

| 기술 | 이유 |
|------|------|
| MAHA / MegaRAG (Knowledge Graph) | 소규모 도면에서 KG 구축 비용 >> 이득 |
| SERVAL (VLM 캡셔닝) | GPT-4o API 필수 → 유료 API 원칙 위반 |
| ViDoRAG 에이전트 | VLM 호출 3배 증가, 배치 처리에 부적합 |

---

## 고객별 연관성

| 고객 | 적용 가능 기술 | 비고 |
|------|---------------|------|
| **동서기연** | AutoRAG, GMM Dynamic Top-K, ColFlor | 스캔본 도면 → VDR 직접 활용 가능 |
| **BMT** | AutoRAG | 벡터 PDF → VDR 불필요, 파이프라인 최적화만 |
| **파나시아** | — | P&ID는 별도 심볼 검출 파이프라인 |
| **테크로스** | — | P&ID, 위와 동일 |

---

## 자료 위치

| 자료 | 경로 |
|------|------|
| 논문 원문 (PDF 12편) | `rnd/papers/visual-document-retrieval/*.pdf` |
| 실용성 분석 (Tier 1/2/3 + 로드맵) | `rnd/papers/visual-document-retrieval/README.md` |
| 전체 논문 인덱스 (62편) | `rnd/papers/README.md` |
