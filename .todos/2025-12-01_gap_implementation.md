# PPT vs POC 갭 해소 구현 계획

**작성일**: 2025-12-01
**목표**: PPT 발표자료에서 제시한 핵심 기능들을 BlueprintFlow 기반으로 구현

---

## 우선순위 1: 도메인 지식 엔진 (Critical) ✅ COMPLETED 2025-12-01

### 1.1 Neo4j 그래프 DB 구축 ✅
- [x] Neo4j Docker 컨테이너 추가 (docker-compose.yml)
- [x] 도면 전용 스키마 설계
  - Component → Dimension → Tolerance → Process 관계
  - HAS_DIM, HAS_TOL, REQUIRES 관계 정의
- [x] Neo4j API 서비스 생성 (models/knowledge-api/) - 통합 Knowledge API로 구현
- [x] BlueprintFlow용 Knowledge 노드 생성 (nodeDefinitions.ts, NodePalette.tsx)

### 1.2 GraphRAG 구현 ✅
- [x] Neo4j 기반 그래프 탐색 로직 (services/graphrag_service.py)
- [x] 유사 부품 검색 기능 (find_similar_parts)
- [x] 과거 프로젝트 매칭 기능 (코드 구현 완료)
- [x] BlueprintFlow용 Knowledge 노드에 통합

### 1.3 VectorRAG (FAISS) 구현 ✅
- [x] FAISS 인덱스 구축 (services/vectorrag_service.py)
- [x] 도면 텍스트 임베딩 생성 (OpenAI text-embedding-3-small)
- [x] 자연어 유사도 검색 기능 (search)
- [x] BlueprintFlow용 Knowledge 노드에 통합

### 1.4 하이브리드 RAG 통합 ✅
- [x] GraphRAG + VectorRAG 결합 로직 (api_server.py hybrid_search)
- [x] 가중치 기반 결과 병합 (graph_weight 파라미터)
- [x] BlueprintFlow용 Knowledge 노드에 통합 (search_mode: hybrid)

### 1.5 ISO/ASME 규격 검증 ✅
- [x] ISO 286-2 공차 검증 (services/standard_validator.py)
- [x] ISO 4287 표면조도 검증
- [x] GD&T 기호 검증 (ISO 1101, ASME Y14.5)
- [x] 나사 규격 검증 (Metric, UNC, UNF, BSP, NPT)
- [x] BlueprintFlow Knowledge 노드에 validate_standards 파라미터로 통합

---

## 우선순위 2: 멀티 엔진 앙상블 고도화 (High) ✅ COMPLETED 2025-12-01

### 2.1 Tesseract OCR 통합 ✅
- [x] Tesseract API 서비스 생성 (models/tesseract-api/)
- [x] Docker 컨테이너 추가 (Port: 5008)
- [x] BlueprintFlow용 Tesseract 노드 생성
- [x] nodeDefinitions.ts에 Tesseract 추가

### 2.2 TrOCR 통합 ✅
- [x] TrOCR API 서비스 생성 (models/trocr-api/)
- [x] Hugging Face Transformers 기반 구현 (microsoft/trocr-base-printed)
- [x] Docker 컨테이너 추가 (Port: 5009)
- [x] BlueprintFlow용 TrOCR 노드 생성

### 2.3 가중 투표 시스템 구현 ✅
- [x] 4-way OCR 앙상블 로직 (eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%)
- [x] 신뢰도 기반 결과 선택 (가중 평균)
- [x] 중복 제거 및 결과 병합 (텍스트 유사도 기반 그룹화)
- [x] BlueprintFlow용 OCR Ensemble 노드 생성 (ocr_ensemble)
- [x] Docker 컨테이너 추가 (Port: 5011)

---

## 우선순위 3: 전처리 고도화 (High) ✅ COMPLETED 2025-12-01

### 3.1 ESRGAN 업스케일링 ✅
- [x] ESRGAN API 서비스 생성 (models/esrgan-api/)
- [x] Real-ESRGAN 4x 업스케일링 구현 (CPU fallback: Lanczos4)
- [x] Docker 컨테이너 추가 (Port: 5010)
- [x] BlueprintFlow용 ESRGAN 노드 생성

### 3.2 전처리 파이프라인 통합 ✅
- [x] ESRGAN → CLAHE → 노이즈제거 파이프라인 (/api/v1/enhance 엔드포인트)
- [x] BlueprintFlow용 preprocessing 카테고리 추가
- [x] 저품질 스캔 도면 업스케일링 지원

---

## 우선순위 4: 비용 산정 고도화 (Medium)

### 4.1 재질 DB 구축
- [ ] 재질 데이터베이스 설계 (PostgreSQL 또는 Neo4j)
- [ ] 재질별 단가 테이블
- [ ] 재질 자동 인식 및 매칭

### 4.2 공차 등급 테이블
- [ ] ISO 공차 등급 테이블 구축 (IT01-IT18)
- [ ] 공차 난이도 → 가공시간 변환 로직
- [ ] 정밀 공차 가공비 계산

### 4.3 공정 규칙 엔진
- [ ] 공차 + 표면조도 → 필요 공정 자동 판단
- [ ] 공정별 시간/비용 계산
- [ ] BlueprintFlow용 CostEstimator 노드 생성

### 4.4 유사 부품 기반 견적
- [ ] GraphRAG 검색 결과 활용
- [ ] 과거 프로젝트 비용 참조
- [ ] 견적 정확도 향상

---

## 우선순위 5: 규격 검증 (Medium)

### 5.1 ISO/ASME 규격 검증
- [ ] ISO 1101 GD&T 규격 DB
- [ ] ASME Y14.5 규격 DB
- [ ] 규격 위반 자동 검출
- [ ] BlueprintFlow용 StandardValidator 노드 생성

### 5.2 표준 규격 매칭
- [ ] 나사 규격 DB (M, UNC, UNF 등)
- [ ] 표면조도 규격 DB (Ra, Rz)
- [ ] 재질 규격 매칭

---

## 우선순위 6: 출력 및 연동 (Low)

### 6.1 견적서 생성 고도화
- [ ] Excel 견적서 템플릿 생성
- [ ] PDF 템플릿 고도화
- [ ] 다국어 지원 (한글/영문)

### 6.2 ERP/MES 연동
- [ ] 연동 API 인터페이스 설계
- [ ] 도면 자동 가져오기
- [ ] 견적서 자동 전송
- [ ] 부품 BOM 동기화

---

## 오늘 작업 목표 (2025-12-01) ✅ ALL COMPLETED

### 즉시 시작 ✅
1. [x] Neo4j Docker 컨테이너 추가
2. [x] 도면 전용 그래프 스키마 설계
3. [x] Knowledge API 서비스 생성 (통합 구현)
4. [x] BlueprintFlow Knowledge 노드 구현

### 추가 완료 작업
- [x] Gateway API Health Check에 Knowledge API 추가
- [x] Knowledge Executor 생성 및 등록
- [x] GraphRAG / VectorRAG / HybridRAG 서비스 구현
- [x] ISO/ASME 규격 검증 서비스 구현

### 병렬 작업 완료 ✅
- [x] Tesseract API 서비스 기본 구조 생성
- [x] TrOCR API 서비스 기본 구조 생성
- [x] ESRGAN API 서비스 기본 구조 생성
- [x] OCR Ensemble API 서비스 기본 구조 생성
- [x] Gateway API Executor 등록 (tesseract, trocr, esrgan, ocr_ensemble)
- [x] Dashboard 모니터링 연동 (12개 API 상태 표시)
- [x] NodePalette 카테고리 재구성 (9개 카테고리)

---

## BlueprintFlow 노드 현황 (2025-12-01 업데이트)

### 현재 구현된 노드 (16개)

| 노드명 | 카테고리 | 기능 | 상태 |
|--------|----------|------|------|
| ImageInput | input | 이미지 입력 | ✅ |
| TextInput | input | 텍스트/프롬프트 입력 | ✅ |
| YOLO | detection | 객체 탐지 | ✅ |
| eDOCr2 | ocr | 전용 OCR | ✅ |
| PaddleOCR | ocr | PaddleOCR | ✅ |
| Tesseract | ocr | Google Tesseract OCR | ✅ NEW |
| TrOCR | ocr | Microsoft Transformer OCR | ✅ NEW |
| OCR Ensemble | ocr | 4-way OCR 가중 투표 | ✅ NEW |
| EDGNet | segmentation | 엣지 세그멘테이션 | ✅ |
| SkinModel | analysis | 공차 분석 | ✅ |
| Knowledge | knowledge | GraphRAG + VectorRAG + 규격 검증 | ✅ NEW |
| ESRGAN | preprocessing | 이미지 업스케일링 | ✅ NEW |
| VL | ai | Vision-Language 모델 | ✅ |
| IF | control | 조건 분기 | ✅ |
| Loop | control | 반복 처리 | ✅ |
| Merge | control | 결과 병합 | ✅ |

### 카테고리 구조 (9개)

| 카테고리 | 노드 수 | 설명 |
|----------|---------|------|
| input | 2 | 입력 노드 |
| detection | 1 | 객체 탐지 |
| ocr | 5 | OCR 처리 |
| segmentation | 1 | 세그멘테이션 |
| preprocessing | 1 | 전처리 |
| analysis | 1 | 분석 |
| knowledge | 1 | 지식 엔진 |
| ai | 1 | AI 모델 |
| control | 3 | 제어 흐름 |

### 추가 예정 노드 (Phase 6+)

| 노드명 | 카테고리 | 기능 |
|--------|----------|------|
| StandardValidator | validation | ISO/ASME 규격 검증 (Knowledge에 일부 포함) |
| CostEstimator | quote | 비용 산정 |
| QuoteGenerator | quote | 견적서 생성 |

---

## 진행 상황 추적

- 시작일: 2025-12-01
- Phase 2 목표 완료일: 2026-03 (5개월)
- Phase 3 목표 완료일: 2026-06 (3개월)

### 완료된 작업

**2025-12-01 (오늘) - Part 1: 도메인 지식 엔진**
1. ✅ Neo4j 5.15.0 Docker 컨테이너 추가 (Port: 7474, 7687)
2. ✅ Knowledge API 통합 서비스 생성 (Port: 5007)
   - models/knowledge-api/api_server.py
   - models/knowledge-api/services/neo4j_service.py
   - models/knowledge-api/services/graphrag_service.py
   - models/knowledge-api/services/vectorrag_service.py
   - models/knowledge-api/services/standard_validator.py
3. ✅ BlueprintFlow Knowledge 노드 프론트엔드 추가
4. ✅ BlueprintFlow Knowledge Executor 백엔드 추가
5. ✅ Gateway API 연동

**2025-12-01 (오늘) - Part 2: 멀티 엔진 앙상블 + 전처리**
6. ✅ Tesseract OCR API 서비스 생성 (Port: 5008)
   - models/tesseract-api/api_server.py
   - Dockerfile, requirements.txt
7. ✅ TrOCR API 서비스 생성 (Port: 5009)
   - models/trocr-api/api_server.py
   - Microsoft TrOCR Transformer 모델 지원
8. ✅ ESRGAN Upscaler API 서비스 생성 (Port: 5010)
   - models/esrgan-api/api_server.py
   - Real-ESRGAN 4x + Fallback Lanczos4
   - 도면 전용 향상 파이프라인 (/api/v1/enhance)
9. ✅ OCR Ensemble API 서비스 생성 (Port: 5011)
   - models/ocr-ensemble-api/api_server.py
   - 4-way 가중 투표 시스템 (40/35/15/10)
   - 텍스트 유사도 기반 결과 그룹화/병합
10. ✅ Docker Compose 업데이트 (4개 새 서비스 추가)
11. ✅ BlueprintFlow 노드 추가
    - nodeDefinitions.ts: tesseract, trocr, esrgan, ocr_ensemble 정의
    - NodePalette.tsx: Preprocessing Nodes, OCR Nodes 섹션 추가
    - 새 카테고리: 'preprocessing', 'ocr'

### 이슈 및 블로커
- Neo4j/FAISS 미설치 환경에서는 Mock 데이터로 폴백 동작 (의도적 설계)
- OpenAI API 키 필요 (VectorRAG 임베딩용)
- TrOCR 첫 실행 시 모델 다운로드 필요 (~400MB)
- Real-ESRGAN 가중치 별도 다운로드 필요 (GPU 환경에서 권장)

### 신규 서비스 포트 정리
| 서비스 | 포트 | 설명 |
|--------|------|------|
| Neo4j Browser | 7474 | Neo4j 웹 UI |
| Neo4j Bolt | 7687 | Neo4j 연결 프로토콜 |
| Knowledge API | 5007 | GraphRAG + VectorRAG + 규격 검증 |
| Tesseract API | 5008 | Google Tesseract OCR |
| TrOCR API | 5009 | Microsoft Transformer OCR |
| ESRGAN API | 5010 | 이미지 업스케일링 |
| OCR Ensemble API | 5011 | 4-way OCR 가중 투표 |

---

## 최종 구현 현황 (2025-12-01 완료)

### 우선순위별 진행 상태

| 우선순위 | 항목 | 상태 | 완료율 |
|----------|------|------|--------|
| 1 | 도메인 지식 엔진 (Neo4j, GraphRAG, VectorRAG) | ✅ 완료 | 100% |
| 2 | 멀티 엔진 OCR 앙상블 (Tesseract, TrOCR, Ensemble) | ✅ 완료 | 100% |
| 3 | 전처리 고도화 (ESRGAN) | ✅ 완료 | 100% |
| 4 | 비용 산정 고도화 | ⏳ 예정 | 0% |
| 5 | 규격 검증 (일부 Knowledge에 포함) | ✅ 부분 완료 | 60% |
| 6 | 출력 및 연동 | ⏳ 예정 | 0% |

### 시스템 구성 요약

- **총 API 서비스**: 12개 (기존 7개 + 신규 5개)
- **BlueprintFlow 노드**: 16개 (기존 11개 + 신규 5개)
- **노드 카테고리**: 9개 (input, detection, ocr, segmentation, preprocessing, analysis, knowledge, ai, control)
- **Gateway Executor**: 17개 (모든 노드 지원)

### 다음 단계

1. **Phase 6**: 테스트 및 최적화
   - 전체 시스템 통합 테스트
   - 성능 프로파일링
   - 에러 핸들링 강화

2. **우선순위 4-6 구현** (2026년 계획)
   - 비용 산정 엔진
   - 견적서 생성
   - ERP/MES 연동
