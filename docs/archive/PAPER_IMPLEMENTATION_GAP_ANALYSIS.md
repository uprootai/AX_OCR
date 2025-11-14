# 논문 구현 GAP 분석

**작성일**: 2025-10-31
**목적**: 각 논문에서 제안된 기능들과 현재 구현 상태 비교 분석

---

## 📋 목차

1. [eDOCr 논문 - 구현 GAP](#1-edocr-논문---구현-gap)
2. [EDGNet 논문 - 구현 GAP](#2-edgnet-논문---구현-gap)
3. [Skin Model 논문 - 구현 GAP](#3-skin-model-논문---구현-gap)
4. [과업지시서 요구사항 - 구현 GAP](#4-과업지시서-요구사항---구현-gap)
5. [우선순위 기반 구현 로드맵](#5-우선순위-기반-구현-로드맵)

---

## 1. eDOCr 논문 - 구현 GAP

### 📚 논문 출처
**제목**: 기계 도면의 텍스트 인식 최적화: 포괄적 접근
**파일**: `/home/uproot/ax/paper/기계_도면의_텍스트_인식_최적화_포괄적_접근/`

### ✅ 구현된 기능

| 기능 | 구현 위치 | 구현 상태 |
|------|----------|----------|
| CRAFT 텍스트 검출 | `edocr2-api/` | ✅ v1, v2 모두 구현 |
| CRNN 텍스트 인식 | `edocr2-api/` | ✅ v1, v2 모두 구현 |
| Table OCR (Pytesseract) | `edocr2-api/api_server_edocr_v2.py` | ✅ v2 구현 (버그 있음) |
| FCF Block 검출 | `edocr2-api/` | ✅ v1 구현 |
| Dimension Pipeline | `edocr2-api/` | ✅ v1 구현 |

### ❌ 구현 안된 기능

#### 🔴 Priority 1 (High Impact)

**1.1 Vision Language 모델을 통한 Information Block 데이터 추출**
- **논문 섹션**: 4.1
- **제안 내용**:
  - Qwen2-VL-7B 또는 GPT-4o를 사용한 Information Block에서 특정 항목 추출
  - Python Dictionary 형식으로 깔끔하게 반환
  - Query: `"Based on the image, return only a python dictionary extracting this information: ['name', 'part number', 'material']"`
- **현재 상태**:
  - Pytesseract만 사용 (모든 텍스트 반환, 구조화 없음)
  - VL 모델 통합 없음
- **구현 필요 사항**:
  ```python
  # gateway-api 또는 별도 서비스
  async def extract_info_block_with_vl(
      image: bytes,
      query_fields: List[str],  # ['name', 'part number', 'material', ...]
      model: str = "qwen2-vl-7b"  # or "gpt-4o"
  ) -> Dict[str, str]:
      """
      VL 모델을 사용하여 Information Block에서 특정 정보 추출
      """
      prompt = f"Based on the image, return only a python dictionary extracting this information: {query_fields}"
      # 모델 호출
      # 결과 파싱
      return parsed_dict
  ```
- **예상 성능 향상**:
  - 재질 추출 정확도: 60% → 90%
  - 부품번호 추출 정확도: 70% → 95%
  - 표면처리 추출 정확도: 50% → 85%

**1.2 제조 공정 추론 (Manufacturing Context Information Understanding)**
- **논문 섹션**: 4.2
- **제안 내용**:
  - GPT-4 또는 Claude에게 Information Block + Part Views를 제공
  - 제조 공정 순서를 Python Dictionary로 반환
  - Query: `"You are getting the information block of the drawing in the first image and the views of the part in the second. I need you to return a python dictionary with the manufacturing processes (keys) and short description (values) that are best for this part."`
- **현재 상태**: 구현 없음
- **구현 필요 사항**:
  ```python
  async def infer_manufacturing_process(
      info_block_image: bytes,
      part_views_image: bytes,
      model: str = "gpt-4"
  ) -> Dict[str, str]:
      """
      도면에서 최적 제조 공정 추론

      Returns:
          {
              "Turning": "Used for creating the cylindrical shape...",
              "Drilling/Boring": "To achieve the internal diameter...",
              "Milling": "For creating the flat surfaces...",
              ...
          }
      """
      pass
  ```
- **비즈니스 가치**:
  - **견적서 자동 생성**에 직접 연결
  - 공정별 비용 산정 자동화
  - 리드타임 예측 개선

**1.3 Quality Control Checklist 자동 생성**
- **논문 섹션**: 4.3
- **제안 내용**:
  - GPT-4에게 품질 관리 시 확인해야 할 치수만 추출 요청
  - Query: `"I need you to provide a Python list containing only the measurements—numerical values and tolerances—that need to be checked in the quality control process."`
  - 응답 예: `["Ø21.5 ± 0.1", "Ø38 H12"]`
- **현재 상태**: 구현 없음
- **구현 필요 사항**:
  ```python
  async def generate_qc_checklist(
      drawing_image: bytes,
      model: str = "gpt-4"
  ) -> List[str]:
      """
      품질 관리 체크리스트 자동 생성

      Returns:
          ["Ø21.5 ± 0.1", "Ø38 H12", ...]
      """
      pass
  ```
- **비즈니스 가치**:
  - 품질 관리 자동화
  - 검사 누락 방지
  - 검사 계획 수립 시간 단축

#### 🟠 Priority 2 (Medium Impact)

**1.4 VL 모델로 Dimension Pipeline 대체**
- **논문 섹션**: 4.4
- **제안 내용**:
  - CRAFT + CRNN 대신 Qwen2-VL-7B 또는 GPT-4로 치수 추출
  - System Role: `"You are a specialized OCR system capable of reading mechanical drawings..."`
  - Query: `"Based on the image, return only a python list of strings extracting dimensions."`
- **현재 상태**:
  - eDOCr v1의 Dimension Pipeline 사용
  - 하지만 **F1 Score 8.3%로 완전 실패**
- **구현 필요 사항**:
  ```python
  async def extract_dimensions_with_vl(
      drawing_image: bytes,
      model: str = "gpt-4"
  ) -> List[str]:
      """
      VL 모델로 치수 추출 (eDOCr 대체)
      """
      system_role = "You are a specialized OCR system capable of reading mechanical drawings..."
      query = "Based on the image, return only a python list of strings extracting dimensions."
      # 모델 호출
      return dimensions_list
  ```
- **예상 성능**:
  - 논문 결과: GPT-4가 eDOCr2와 유사한 Recall, 더 나은 Context 이해
  - 예상: F1 8.3% → 70-85% (Multimodal LLM 강점)

**1.5 멀티 OCR 엔진 앙상블**
- **과업지시서 요구**: 3개 이상의 OCR 엔진을 가중치 기반 투표로 앙상블
- **현재 상태**:
  - v1/v2 앙상블만 테스트 (성능 개선 없음)
  - 가중치 기반 투표 없음
- **구현 필요 사항**:
  ```python
  async def ensemble_ocr(
      image: bytes,
      engines: List[str] = ["edocr_v1", "edocr_v2", "gpt4v"]
  ) -> Dict[str, Any]:
      """
      멀티 OCR 엔진 앙상블

      가중치:
      - edocr_v1: 40% (도면 특화)
      - edocr_v2: 35% (테이블, FCF 강점)
      - gpt4v: 25% (VL 검증)
      """
      results = await asyncio.gather(
          call_edocr_v1(image),
          call_edocr_v2(image),
          call_gpt4v(image)
      )

      # 가중치 투표
      ensemble_result = weighted_voting(results, weights=[0.4, 0.35, 0.25])
      return ensemble_result
  ```

---

## 2. EDGNet 논문 - 구현 GAP

### 📚 논문 출처
**제목**: 그래프 합성곱 신경망을 이용한 공학 도면의 구성요소 분할
**파일**: `/home/uproot/ax/paper/그래프_합성곱_신경망을_이용한_공학_도면의_구성요소_분할/`

### ✅ 구현된 기능

| 기능 | 구현 위치 | 구현 상태 |
|------|----------|----------|
| GraphSAGE 세그멘테이션 | `edgnet-api/` | ✅ 구현됨 |
| Contour 검출 | `edgnet-api/` | ✅ 구현됨 |
| Text/Dimension 분류 | `edgnet-api/` | ✅ 구현됨 |
| 그래프 구조 반환 | `edgnet-api/` | ✅ 구현됨 |

### ❌ 구현 안된 기능

#### 🔴 Priority 1

**2.1 EDGNet을 eDOCr의 전처리로 활용**
- **현재 상태**:
  - EDGNet과 eDOCr가 독립적으로 동작
  - 통합 파이프라인 없음
- **제안 내용**:
  ```
  EDGNet Segmentation → Dimension 영역만 크롭 → eDOCr OCR
  ```
- **예상 개선**:
  - 처리 시간: 34초 → 25초
  - 정확도: F1 8.3% → 15-20% (여전히 낮지만 개선)
- **구현 필요 사항**:
  ```python
  async def edgnet_to_edocr_pipeline(image: bytes):
      # 1. EDGNet으로 세그멘테이션
      segments = await call_edgnet(image)

      # 2. Dimension 영역만 추출
      dimension_regions = [s for s in segments['segments']
                          if s['class'] == 'dimension']

      # 3. 각 영역에 대해 eDOCr 실행
      results = []
      for region in dimension_regions:
          cropped = crop_image(image, region['bbox'])
          ocr_result = await call_edocr(cropped)
          results.append(ocr_result)

      return aggregate_results(results)
  ```

#### 🟡 Priority 3 (Low Priority)

**2.2 PDF 지원**
- **현재 상태**: EDGNet이 PDF 파일 처리 시 400 에러
- **필요 작업**: PDF → Image 변환 후 처리 (Gateway에서 이미 구현됨)

---

## 3. Skin Model 논문 - 구현 GAP

### 📚 논문 출처
**제목**: 금속 적층 제조 공정의 기하 공차 및 제조 조립성 추정
**파일**: `/home/uproot/ax/paper/금속_적층_제조_공정의_기하_공차_및_제조_조립성_추정/`

### ✅ 구현된 기능 (Mock)

| 기능 | 구현 위치 | 구현 상태 |
|------|----------|----------|
| API 서버 | `skinmodel-api/api_server.py` | ✅ Mock 데이터 반환 |
| 공차 예측 API | `/api/v1/predict_tolerance` | ✅ Mock 구현 |
| GD&T 검증 API | `/api/v1/validate_gdt` | ✅ Mock 구현 |

### ❌ 구현 안된 기능 (실제 로직)

#### 🔴 Priority 1

**3.1 스킨 모델 형상(Skin Model Shapes) 생성**
- **논문 내용**:
  - 공칭 형상 + 편차 = 스킨 모델
  - 예측 단계: Random Field + 수축 모델
  - 관찰 단계: FEM 시뮬레이션 + PCA
- **현재 상태**: 완전히 미구현
- **구현 필요 사항**:
  ```python
  class SkinModelGenerator:
      def generate_prediction_samples(
          self,
          stl_file: str,
          n_samples: int = 1000000,
          shrinkage: float = 0.98,
          random_std: float = 0.02,
          correlation_length: float = 5.0
      ) -> List[SkinModelSample]:
          """
          예측 단계: Random Field 기반 샘플 생성
          """
          # 1. STL 읽기
          # 2. 수축 적용
          # 3. 상관 행렬 계산 (Cholesky 분해)
          # 4. 가우스 랜덤 벡터 생성
          # 5. 법선 방향으로 변위
          pass

      def generate_observation_samples(
          self,
          fem_results: List[FEMResult],
          nominal_stl: str,
          n_samples: int = 1000000
      ) -> List[SkinModelSample]:
          """
          관찰 단계: FEM 기반 샘플 생성
          """
          # 1. FEM 편차 행렬 구성
          # 2. PCA 수행
          # 3. 각 주성분의 분포 추정
          # 4. 샘플 생성 (역변환)
          pass
  ```

**3.2 GD&T 특성 자동 추출 알고리즘**
- **논문 내용**:
  - 평면도 (Flatness): 최소 제곱 평면 적합
  - 원통도 (Cylindricity): PCA 또는 최소 제곱 원통 적합
  - 수직도 (Perpendicularity): 벡터 내적으로 각도 계산
  - 진위치 (True Position): 위치 편차 + MMC 보너스
- **현재 상태**: Mock 값만 반환
- **구현 필요 사항**:
  ```python
  class GDTCalculator:
      @staticmethod
      def flatness(points: np.ndarray) -> float:
          """평면도 계산 (ISO 1101)"""
          # SVD로 최소 제곱 평면 적합
          # max(distance) - min(distance)
          pass

      @staticmethod
      def cylindricity(points: np.ndarray) -> Tuple[float, np.ndarray, np.ndarray]:
          """원통도 계산"""
          # PCA로 축 찾기
          # 반경 거리 계산
          pass

      @staticmethod
      def perpendicularity(
          feature_axis: np.ndarray,
          feature_length: float,
          datum_normal: np.ndarray
      ) -> float:
          """수직도 계산"""
          # 각도 계산
          # length × sin(θ_dev)
          pass

      @staticmethod
      def true_position(
          actual_center: np.ndarray,
          theoretical_center: np.ndarray,
          actual_dia: float,
          mmc_dia: float,
          feature_type: str = 'hole'
      ) -> Tuple[float, float]:
          """진위치 계산 (MMC 적용)"""
          # 위치 편차 계산
          # MMC 보너스 계산
          pass
  ```

**3.3 조립성 평가 (Assemblability)**
- **논문 내용**:
  - 핀/홀 간극 계산
  - 100만 샘플 시뮬레이션하여 조립 성공률 계산
- **현재 상태**: Mock 값 (0.92) 반환
- **구현 필요 사항**:
  ```python
  def evaluate_assemblability(
      pin_samples: List[SkinModelSample],
      hole_samples: List[SkinModelSample],
      clearance_fit: str = 'H11/c11'
  ) -> Dict[str, Any]:
      """
      조립성 평가

      Returns:
          {
              "score": 0.92,
              "clearance_min": 0.055,
              "clearance_max": 0.375,
              "interference_risk": "Low"
          }
      """
      pass
  ```

#### 🟠 Priority 2

**3.4 FEM 시뮬레이션 통합**
- **논문 내용**:
  - Autodesk Netfabb 또는 ANSYS로 열-기계적 시뮬레이션
  - 레이저 출력, 스캔 속도, 층 두께 등 매개변수 변동
  - 20회 시뮬레이션 → PCA로 주요 모드 추출
- **현재 상태**: 완전히 미구현
- **구현 필요 사항**:
  - FEM 소프트웨어 연동 (Netfabb/ANSYS API)
  - 시뮬레이션 결과 파싱
  - PCA 분석 파이프라인

---

## 4. 과업지시서 요구사항 - 구현 GAP

### 📚 출처
**파일**: `/home/uproot/ax/paper/AX실증산단_과업지시서_기술요구사항.md`

### ❌ 구현 안된 핵심 요구사항

#### 🔴 Priority 1 (High Impact)

**4.1 Graph RAG / Vector RAG 기반 비용 산정 엔진**
- **요구사항**:
  - Neo4j, ArangoDB로 부품-공정-비용 지식 그래프 구축
  - Cypher 쿼리로 비용 추론
  - Vector Store (Chroma, Pinecone)로 유사 도면 검색
  - 과거 견적 데이터 기반 리드타임 예측
- **현재 상태**: 완전히 미구현
- **구현 필요 사항**:
  ```python
  # Graph RAG
  class KnowledgeGraphRAG:
      def __init__(self, neo4j_url: str):
          self.driver = GraphDatabase.driver(neo4j_url)

      def estimate_cost(
          self,
          part_metadata: Dict[str, Any]
      ) -> Dict[str, float]:
          """
          지식 그래프 기반 비용 산정

          Query:
          MATCH (p:Part {material: $material})-[:REQUIRES]->(proc:Process)
          MATCH (proc)-[:COSTS]->(cost:Cost)
          RETURN proc.name, cost.unit_price, cost.time_minutes
          """
          pass

  # Vector RAG
  class VectorStoreRAG:
      def __init__(self, store: VectorStore):
          self.store = store

      def find_similar_quotes(
          self,
          drawing_embedding: np.ndarray,
          top_k: int = 5
      ) -> List[Dict]:
          """
          유사 도면 검색하여 견적 예측
          """
          pass
  ```

**4.2 견적서 자동 생성 (PDF)**
- **요구사항**:
  - ReportLab, WeasyPrint로 PDF 견적서 생성
  - 템플릿 기반 문서 생성
  - 견적 번호, 날짜, 부품 정보, 재질, 공정별 비용, 총액, 리드타임 포함
- **현재 상태**: Gateway API에 `/api/v1/generate_quote` 엔드포인트만 존재, 실제 PDF 생성 없음
- **구현 필요 사항**:
  ```python
  from reportlab.lib.pagesizes import A4
  from reportlab.platypus import SimpleDocTemplate, Table, Paragraph

  def generate_pdf_quote(
      quote_data: Dict[str, Any],
      template: str = "standard"
  ) -> bytes:
      """
      PDF 견적서 생성

      Args:
          quote_data: {
              "quote_number": "Q-2025-001",
              "date": "2025-10-31",
              "part_name": "Intermediate Shaft",
              "material": "STS304",
              "processes": [
                  {"name": "Turning", "cost": 150.0, "time": "2h"},
                  {"name": "Drilling", "cost": 80.0, "time": "1h"}
              ],
              "total_cost": 230.0,
              "lead_time": "5 days"
          }

      Returns:
          PDF 파일의 bytes
      """
      pass
  ```

**4.3 배치 처리 및 병렬 처리**
- **요구사항**:
  - 하루 100장 이상 처리 가능
  - GPU 병렬 처리, 멀티프로세싱
  - 목표: 1장당 평균 10초 이하
  - 처리 큐, 작업 스케줄러, 진행 상황 모니터링
- **현재 상태**: Gateway API에 백그라운드 태스크만 존재, 실제 큐 시스템 없음
- **구현 필요 사항**:
  ```python
  from celery import Celery

  celery_app = Celery('gateway', broker='redis://localhost:6379/0')

  @celery_app.task
  def process_drawing_batch(file_paths: List[str]):
      """
      배치 처리 태스크
      """
      for file_path in file_paths:
          process_single_drawing.delay(file_path)

  @celery_app.task
  def process_single_drawing(file_path: str):
      """
      단일 도면 처리 (병렬 실행)
      """
      pass
  ```

#### 🟠 Priority 2

**4.4 합성 데이터(Synthetic Data) 생성 파이프라인**
- **요구사항**:
  - GD&T 기호, 치수, 공차를 랜덤 조합
  - 10,000장 이상의 합성 이미지 생성
  - 폰트, 크기, 회전, 노이즈, 배경 변화
  - Domain Adaptation, Style Transfer로 Sim-to-Real Gap 감소
- **현재 상태**: 완전히 미구현
- **구현 필요 사항**:
  ```python
  class SyntheticDrawingGenerator:
      def generate_gdt_samples(
          self,
          n_samples: int = 10000,
          output_dir: str = "./synthetic_data"
      ):
          """
          합성 GD&T 샘플 생성
          """
          for i in range(n_samples):
              # 1. 랜덤 GD&T 기호 선택
              # 2. 랜덤 치수 값 생성
              # 3. 랜덤 공차 생성
              # 4. 캔버스에 렌더링
              # 5. 노이즈/변형 추가
              # 6. 저장
              pass
  ```

**4.5 지속적 학습(Continual Learning)**
- **요구사항**:
  - 실증 기업 피드백 데이터로 모델 재학습
  - Catastrophic Forgetting 방지 (EWC, Replay Buffer)
  - A/B 테스트로 신규 모델 검증
- **현재 상태**: 완전히 미구현

**4.6 모델 버전 관리 및 실험 추적**
- **요구사항**:
  - MLflow, Weights & Biases, DVC 통합
  - 하이퍼파라미터 관리
  - CI/CD 파이프라인
  - Blue-Green, Canary Deployment
- **현재 상태**: 완전히 미구현

**4.7 보안 및 암호화**
- **요구사항**:
  - AES-256 암호화 저장
  - TLS 1.3 전송 암호화
  - ISO 27001 인증
  - RBAC (역할 기반 접근 제어)
  - 감사 로그
- **현재 상태**: 기본 CORS만 설정됨, 보안 기능 없음

**4.8 업종별 커스터마이징 플러그인 시스템**
- **요구사항**:
  - 기계, 조선, 건축, 전기, 화학 등 업종별 설정
  - 도면 표준(ISO, ASME, KS, JIS) 전환 가능
  - 플러그인 방식으로 확장
- **현재 상태**: 하드코딩된 설정만 존재

**4.9 API 문서 및 SDK**
- **요구사항**:
  - OpenAPI/Swagger 문서
  - Python SDK 제공
  - Webhook, 이벤트 기반 아키텍처
- **현재 상태**:
  - FastAPI 자동 문서 (/docs) 존재
  - SDK 없음

---

## 5. 우선순위 기반 구현 로드맵

### 🎯 즉시 실행 (1-2주)

**Week 1: Critical Path (eDOCr 대체)**

1. **Multimodal LLM 통합** ⭐⭐⭐⭐⭐
   - GPT-4V 또는 Claude 3 Sonnet API 연동
   - Information Block 추출 (4.1 섹션)
   - 치수 추출 대체 (4.4 섹션)
   - **예상 성능**: F1 8.3% → 70-85%
   - **예상 시간**: 3-4일

2. **제조 공정 추론 + 비용 산정 기본 구현** ⭐⭐⭐⭐
   - GPT-4로 제조 공정 추론 (4.2 섹션)
   - 간단한 Rule-based 비용 계산
   - **비즈니스 가치**: 견적서 생성 기능 활성화
   - **예상 시간**: 2-3일

**Week 2: 견적 자동화**

3. **견적서 PDF 자동 생성** ⭐⭐⭐⭐
   - ReportLab 통합
   - 템플릿 기반 PDF 생성
   - **예상 시간**: 2일

4. **QC Checklist 자동 생성** ⭐⭐⭐
   - GPT-4로 품질 관리 항목 추출 (4.3 섹션)
   - **예상 시간**: 1일

### 📅 단기 (3-4주)

**Week 3-4: 파이프라인 최적화**

5. **배치 처리 시스템** ⭐⭐⭐⭐
   - Celery + Redis 큐 시스템
   - 병렬 처리 (멀티프로세싱)
   - 진행 상황 모니터링
   - **목표**: 100장 / 30분
   - **예상 시간**: 5일

6. **EDGNet → eDOCr 통합 파이프라인** ⭐⭐⭐
   - EDGNet 전처리 활용
   - **예상 개선**: 처리 시간 34초 → 25초
   - **예상 시간**: 3일

### 📅 중기 (1-3개월)

**Month 2: 지식 그래프 및 RAG**

7. **Graph RAG 비용 산정 엔진** ⭐⭐⭐⭐⭐
   - Neo4j 지식 그래프 구축
   - 부품-공정-비용 관계 모델링
   - Cypher 쿼리 기반 추론
   - **예상 시간**: 2주

8. **Vector RAG 유사 도면 검색** ⭐⭐⭐⭐
   - Chroma 또는 Pinecone Vector Store
   - 도면 임베딩 (CLIP, ViT)
   - 과거 견적 기반 예측
   - **예상 시간**: 1주

**Month 3: Skin Model 실제 구현**

9. **스킨 모델 형상 생성** ⭐⭐⭐
   - Random Field 샘플 생성
   - 수축 모델 적용
   - **예상 시간**: 2주

10. **GD&T 자동 계산 알고리즘** ⭐⭐⭐⭐
    - 평면도, 원통도, 수직도, 진위치
    - ISO 1101, ASME Y14.5 표준 준수
    - **예상 시간**: 2주

### 📅 장기 (3-6개월)

**Month 4-5: 데이터 파이프라인**

11. **합성 데이터 생성 시스템** ⭐⭐⭐⭐
    - GD&T 합성 이미지 10,000장
    - Domain Adaptation
    - **예상 시간**: 3주

12. **지속적 학습 파이프라인** ⭐⭐⭐
    - Continual Learning 구현
    - EWC, Replay Buffer
    - A/B 테스트
    - **예상 시간**: 2주

**Month 6: 보안 및 확장성**

13. **보안 강화** ⭐⭐⭐⭐
    - AES-256 암호화
    - TLS 1.3
    - RBAC, 감사 로그
    - **예상 시간**: 2주

14. **모델 버전 관리** ⭐⭐⭐
    - MLflow 통합
    - CI/CD 파이프라인
    - Blue-Green Deployment
    - **예상 시간**: 1주

15. **업종별 커스터마이징** ⭐⭐⭐
    - 플러그인 시스템
    - 도면 표준 전환
    - **예상 시간**: 2주

---

## 📊 구현 GAP 요약 테이블

| 분류 | 논문/요구사항 | 구현 여부 | 우선순위 | 예상 시간 | 비즈니스 가치 |
|------|--------------|----------|---------|----------|--------------|
| **eDOCr** | VL 모델 Info Block 추출 | ❌ | P1 | 3-4일 | ⭐⭐⭐⭐⭐ |
| **eDOCr** | 제조 공정 추론 | ❌ | P1 | 2-3일 | ⭐⭐⭐⭐ |
| **eDOCr** | QC Checklist 생성 | ❌ | P1 | 1일 | ⭐⭐⭐ |
| **eDOCr** | VL 모델 치수 추출 | ❌ | P1 | 3-4일 | ⭐⭐⭐⭐⭐ |
| **eDOCr** | 멀티 OCR 앙상블 | ❌ | P2 | 3일 | ⭐⭐⭐ |
| **EDGNet** | eDOCr 통합 파이프라인 | ❌ | P2 | 3일 | ⭐⭐⭐ |
| **Skin Model** | 스킨 모델 형상 생성 | ❌ | P2 | 2주 | ⭐⭐⭐ |
| **Skin Model** | GD&T 자동 계산 | ❌ | P1 | 2주 | ⭐⭐⭐⭐ |
| **Skin Model** | 조립성 평가 | ❌ | P3 | 1주 | ⭐⭐ |
| **Skin Model** | FEM 시뮬레이션 통합 | ❌ | P3 | 3주 | ⭐⭐ |
| **과업지시서** | Graph RAG 비용 산정 | ❌ | P1 | 2주 | ⭐⭐⭐⭐⭐ |
| **과업지시서** | Vector RAG 유사 검색 | ❌ | P1 | 1주 | ⭐⭐⭐⭐ |
| **과업지시서** | 견적서 PDF 생성 | ❌ | P1 | 2일 | ⭐⭐⭐⭐ |
| **과업지시서** | 배치 처리 시스템 | ❌ | P1 | 5일 | ⭐⭐⭐⭐ |
| **과업지시서** | 합성 데이터 생성 | ❌ | P2 | 3주 | ⭐⭐⭐⭐ |
| **과업지시서** | 지속적 학습 | ❌ | P2 | 2주 | ⭐⭐⭐ |
| **과업지시서** | 모델 버전 관리 | ❌ | P2 | 1주 | ⭐⭐⭐ |
| **과업지시서** | 보안 강화 | ❌ | P2 | 2주 | ⭐⭐⭐⭐ |
| **과업지시서** | 업종별 커스터마이징 | ❌ | P3 | 2주 | ⭐⭐⭐ |

---

## 🎯 핵심 결론

### 1. **가장 큰 GAP: eDOCr의 완전한 실패**

**현실**:
- eDOCr v1/v2: F1 Score 8.3% / 0.0%
- 주요 치수 완전 누락
- 오검출 비율 66%

**논문에서 제안한 해결책**:
- **VL 모델(GPT-4V, Qwen2-VL-7B)로 대체**
- 예상 성능: F1 70-85%

**즉시 실행 필요**: Week 1에 GPT-4V/Claude 3 통합

### 2. **비즈니스 가치가 가장 높은 미구현 기능**

1. **Multimodal LLM 통합** (eDOCr 대체)
2. **Graph RAG 비용 산정 엔진**
3. **견적서 자동 생성**
4. **제조 공정 추론**
5. **배치 처리 시스템**

이 5가지를 구현하면 **실제 사업화 가능**.

### 3. **Skin Model은 Optional**

- 논문 내용이 매우 전문적 (FEM, PCA, 상관 함수)
- 구현 복잡도 높음
- 비즈니스 가치는 중간 수준
- **우선순위 낮음** (P2-P3)

### 4. **과업지시서 요구사항의 50% 미구현**

특히 다음이 완전히 없음:
- Graph/Vector RAG
- 합성 데이터 생성
- 지속적 학습
- 보안 강화
- 플러그인 시스템

---

**작성자**: Claude 3.7 Sonnet
**분석 기준**: 논문 원문 + 과업지시서 + 현재 코드베이스
**다음 단계**: 우선순위 P1 항목부터 구현 시작

**최종 권장**: GPT-4V/Claude 3 통합을 가장 먼저 구현하여 eDOCr 대체 🚀
