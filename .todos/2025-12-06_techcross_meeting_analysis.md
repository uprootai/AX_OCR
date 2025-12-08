# Techcross 미팅 분석 및 API Gap 분석

> 작성일: 2025-12-06
> 미팅 대상: Techcross (테크로스)
> 프로젝트: P&ID 기반 도면 분석 및 체크리스트 자동 생성

---

## 1. 미팅 핵심 요약

### 1.1 고객사 현황
- **Techcross**: 해양/조선 기자재 기업
- **주요 니즈**: P&ID 도면 기반 자동화 시스템
- **프로젝트 규모**: 2년 과제
- **연관 기업**: 파나시아, 현대, 한전, 삼성

### 1.2 주요 요구사항 (우선순위 순)

| 순위 | 요구사항 | 설명 | 난이도 |
|------|----------|------|--------|
| 1 | **P&ID 인식 및 체크리스트** | P&ID 심볼 인식 → 체크리스트 자동 생성 | 상 |
| 2 | **밸브 시그널 리스트** | 밸브 정보 추출 → 시그널 리스트 작성 | 상 |
| 3 | **장비 리스트 (Equipment List)** | 도면에서 장비 정보 추출 | 중 |
| 4 | **Deviation 리스트** | 조선소 요구사항 vs 자사 표준 비교 | 상 |
| 5 | **설계 오류 검출** | AI 기반 도면 오작 검출 | 상 |
| 6 | **BOM 자동 추출** | 도면 → Bill of Materials 생성 | 중 |

### 1.3 기술적 핵심 포인트

#### 멀티 엔진 앙상블 접근법
- **텍스트**: eDOCr2, PaddleOCR
- **심볼**: YOLO
- **특수 기호/공차**: 전용 엔진
- **도면별 가중치 조정** 필요

#### Graph RAG (핵심 기술)
```
"그래프 레그가 사실상 핵심 중에 하나"
```
- 도메인 지식 그래프 구축
- KR 선급 규정, ISO 표준, 조선소 요구사항 연결
- 용어 간 관계 매핑

#### 레이어 분리 분석
```
"형상 치수 공차 주소기 레이어가 여러 가지 들어갔다"
```
- 도면을 영역별로 구분
- Shape, Dimension, Tolerance, Annotation 레이어 분리
- 각 레이어별 전문 처리

#### Human-in-the-Loop
```
"작업자가 이걸 보고 승인 수정 반려를 할 수 있게끔"
```
- 100% 자동화 불가능
- 사람 검증 → AI 재학습 루프
- 회사만의 데이터 축적

---

## 2. 현재 AX POC API 현황

### 2.1 보유 API (14개)

| 카테고리 | API | 설명 | P&ID 적용 가능성 |
|----------|-----|------|------------------|
| Detection | YOLO | 심볼 검출 (14 클래스) | **부분** - 기계도면용 |
| OCR | eDOCr2 | 한국어 OCR | **가능** |
| OCR | PaddleOCR | 다국어 OCR | **가능** |
| OCR | Tesseract | 문서 OCR | 가능 |
| OCR | TrOCR | Transformer OCR | 가능 |
| OCR | Surya OCR | 90+ 언어 OCR | **가능** |
| OCR | DocTR | 문서 OCR | 가능 |
| OCR | EasyOCR | 다국어 OCR | 가능 |
| OCR | OCR Ensemble | 4엔진 앙상블 | **가능** |
| Segmentation | EDGNet | 엣지 세그멘테이션 | 가능 |
| Preprocessing | ESRGAN | 이미지 업스케일링 | 가능 |
| Analysis | SkinModel | 공차 분석 | **가능** |
| AI | VL | Vision-Language | **가능** |
| Knowledge | Knowledge | Neo4j + GraphRAG | **핵심** |

### 2.2 강점
1. **멀티 OCR 앙상블** - 이미 4개 엔진 가중 투표 구현
2. **Knowledge Engine** - Neo4j + GraphRAG 기반
3. **SkinModel** - 공차 분석 기능
4. **BlueprintFlow** - 워크플로우 빌더

---

## 3. 부족한 API/기능 (Gap Analysis)

### 3.1 필수 추가 API

#### 🔴 P1: P&ID 심볼 디텍터 (신규 필요)
```
현재: YOLO는 기계도면 14클래스 (용접, 베어링, 기어 등)
필요: P&ID 50+ 클래스 (밸브, 펌프, 계기, 배관 등)
```

| 항목 | 상세 |
|------|------|
| 기술 | YOLOv8/v11 + P&ID 데이터셋 |
| 클래스 예시 | Gate Valve, Ball Valve, Check Valve, Pump, Compressor, Heat Exchanger, Flow Meter, Pressure Gauge, Control Valve 등 |
| 참고 논문 | "Improved P&ID Symbol Detection Based on YOLOv5" (ResearchGate) |
| 데이터셋 | Roboflow P&ID Detection, Digitize-PID (Microsoft) |
| 예상 정확도 | 94.52% (YOLOv5 + SE 기준) |

#### 🔴 P1: 라인 검출 및 연결성 분석 (신규 필요)
```
현재: 없음
필요: 배관 라인 검출 + 심볼 간 연결 관계 파악
```

| 항목 | 상세 |
|------|------|
| 기술 | GraphSAGE 기반 GNN + Line Detection |
| 기능 | 배관 vs 신호선 구분, 연결 토폴로지 추출 |
| 참고 논문 | "Classification of Functional Types of Lines in P&IDs Using a Graph Neural Network" |
| 출력 | 그래프 구조 (노드: 심볼, 엣지: 배관/신호선) |

#### 🔴 P1: BOM 추출기 (신규 필요)
```
현재: 없음
필요: 도면 → Bill of Materials 자동 생성
```

| 항목 | 상세 |
|------|------|
| 기술 | Mask R-CNN + Title Block Parser |
| 참고 논문 | "Generating integrated BOM using Mask R-CNN AI model" (mAP 98% @ IoU=50%) |
| 기능 | 부품 번호, 수량, 재질, 규격 추출 |

#### 🟡 P2: 설계 오류 검출기 (신규 필요)
```
현재: 없음
필요: 도면 규정 준수 여부 자동 검증
```

| 항목 | 상세 |
|------|------|
| 기술 | 규칙 기반 + AI 하이브리드 |
| 기능 | 배관 사이즈 오류, 밸브 유형 불일치, 연결 누락 등 |
| 참고 제품 | NexCAD AI Drawing Checker, CoLab AutoReview |

### 3.2 기능 확장 필요

#### 🟡 P2: Knowledge Engine 확장
```
현재: 기본 GraphRAG 구현
필요: 조선/해양 도메인 특화 지식 그래프
```

| 추가 필요 데이터 | 설명 |
|-----------------|------|
| KR 선급 규정 | 한국선급 표준/규정 |
| ISO 배관 표준 | ISO 1101, ISO 286-2 등 |
| 조선소 요구사항 | 선주별 Spec Sheet |
| P&ID 심볼 매핑 | 회사별 심볼 → 표준 심볼 |

#### 🟡 P2: Human-in-the-Loop 워크플로우
```
현재: 없음 (자동 처리만)
필요: 승인/수정/반려 + 피드백 학습
```

| 기능 | 설명 |
|------|------|
| 검증 UI | 인식 결과 확인/수정 인터페이스 |
| 피드백 루프 | 수정 내용 → 모델 재학습 |
| 이력 관리 | 검증 이력 저장 |

#### 🟢 P3: 색상 분석 기능
```
현재: 흑백 기반 처리
필요: 색상 코드 해석 (방향, 상태 등)
```

| 기능 | 설명 |
|------|------|
| 색상 추출 | RGB/HSV 기반 색상 분류 |
| 의미 매핑 | 색상 → 배관 유형, 방향 등 |

### 3.3 계산 엔진 (신규 필요)

#### 🟡 P2: 배관 사이징 계산기
```
"발라스트 펌프가 용량이 3천인데 유속을 얼마로 만들어줘야 하기 때문에
배관 사양은 몇 백 에이다"
```

| 항목 | 상세 |
|------|------|
| 기능 | 펌프 용량 → 유속 → 배관 직경 계산 |
| 입력 | 펌프 사양, 유체 종류, 거리 |
| 출력 | 권장 배관 사이즈, 압력 손실 |
| 검증 | 설계값 vs 계산값 비교 |

---

## 4. 구현 우선순위 및 로드맵

### Phase 1 (3개월): 기반 기술
| 항목 | 설명 | 예상 기간 |
|------|------|----------|
| P&ID Symbol Detector | YOLO v11 + P&ID 데이터셋 학습 | 4주 |
| Line Detector | 배관/신호선 검출 | 4주 |
| Connectivity Analyzer | GraphSAGE 기반 연결 분석 | 4주 |

### Phase 2 (3개월): 핵심 기능
| 항목 | 설명 | 예상 기간 |
|------|------|----------|
| BOM Extractor | Mask R-CNN 기반 BOM 추출 | 4주 |
| Checklist Generator | P&ID → 체크리스트 변환 | 4주 |
| Knowledge Graph 확장 | 조선/해양 도메인 지식 | 4주 |

### Phase 3 (3개월): 고급 기능
| 항목 | 설명 | 예상 기간 |
|------|------|----------|
| Design Error Detector | 규칙 기반 오류 검출 | 4주 |
| Calculation Engine | 배관 사이징 계산 | 4주 |
| Human-in-the-Loop UI | 검증 워크플로우 | 4주 |

### Phase 4 (3개월): 최적화
| 항목 | 설명 | 예상 기간 |
|------|------|----------|
| 회사별 심볼 커스터마이징 | Techcross 전용 모델 | 4주 |
| 통합 테스트 | 전체 파이프라인 검증 | 4주 |
| 성능 최적화 | 처리 속도 개선 | 4주 |

---

## 5. 기술 참고자료

### 5.1 P&ID 관련 논문
- [Improved P&ID Symbol Detection Based on YOLOv5](https://www.researchgate.net/publication/377794229)
- [Advancing P&ID Digitization with YOLOv5](https://www.researchgate.net/publication/378079356)
- [Classification of Functional Types of Lines Using GNN](https://www.researchgate.net/publication/372434827)
- [Transforming P&ID using Transformers](https://arxiv.org/html/2411.13929v1)
- [Deep Learning for P&ID Recognition](https://www.nature.com/articles/s41598-025-25506-2)

### 5.2 BOM/도면 분석
- [Generating BOM using Mask R-CNN](https://www.sciencedirect.com/science/article/abs/pii/S0926580522005143)
- [AI-Based Engineering Drawing Information Extraction](https://link.springer.com/chapter/10.1007/978-3-031-18326-3_36)
- [Tolerance Information Extraction](https://www.sciencedirect.com/science/article/abs/pii/S1755581724000130)

### 5.3 설계 검증
- [Using AI to Find Design Errors](https://onlinelibrary.wiley.com/doi/10.1002/smr.2543)
- [Microsoft P&ID Digitization](https://devblogs.microsoft.com/ise/engineering-document-pid-digitization/)

### 5.4 조선/해양 AI
- [KR and HD Hyundai AI Ship Design](https://www.marinelog.com/technology/kr-and-hd-hyundai-samho-join-forces-to-bring-ai-into-ship-design/)

---

## 6. 데이터셋 및 도구

### 6.1 P&ID 데이터셋
| 데이터셋 | 설명 | 링크 |
|----------|------|------|
| Roboflow P&ID | 29개 밸브 이미지 | [링크](https://universe.roboflow.com/joel-castagne-rwrla/p-id-detection/) |
| Digitize-PID | 50+ 심볼 (Microsoft) | 합성 데이터셋 |
| PID2Graph | 그래프 구조 포함 | 학술용 |

### 6.2 상용 솔루션 벤치마크
| 제품 | 특징 | 정확도 |
|------|------|--------|
| Werk24 | 도면 → JSON | 95%+ |
| DeepVu | BOM 생성 자동화 | - |
| NexCAD | AI Drawing Checker | - |
| CoLab AutoReview | 설계 검증 | - |

---

## 7. 결론 및 권장사항

### 7.1 핵심 Gap
1. **P&ID 심볼 디텍터** - 현재 YOLO는 기계도면용, P&ID 전용 필요
2. **라인 연결성 분석** - GNN 기반 새로운 API 필요
3. **BOM 추출기** - Mask R-CNN 기반 개발 필요
4. **설계 오류 검출** - 규칙 기반 + AI 하이브리드
5. **Human-in-the-Loop** - 검증 워크플로우 구축

### 7.2 강점 활용
1. **Knowledge Engine** - GraphRAG 기반 확장
2. **OCR Ensemble** - 멀티 엔진 접근법 재활용
3. **BlueprintFlow** - P&ID 워크플로우 통합

### 7.3 즉시 실행 가능한 작업
1. P&ID 데이터셋 수집 시작 (Roboflow, Digitize-PID)
2. YOLO v11 P&ID 모델 학습 파이프라인 구축
3. Knowledge Engine에 KR 선급/ISO 규정 데이터 추가
4. Human-in-the-Loop UI 프로토타입 설계

---

## 부록: 미팅 핵심 인용

> "저희가 이제 도면 쪽에 보통은 저희가 조선 파나시아랑 이런 기업들 현대하고도 막 그런 기업들하고 기자재 기업들 만나서 얘기를 하는데 지금 저희 지금 첫 번째는 다른 거 다 제치고 일단 도면부터"

> "도면이 제일 관리가 안 되고 있더라고요. 다른 데이터는 그나마 좀 하려고 하는데 도면이 제일 중요한 데 비해서 제일 관리가 안 되고 있더라고요."

> "저희는 어떻게 하냐면 엔진들을 몇 개를 결합해서 멀티 엔진 앙상부를 제가 구축을 합니다."

> "그래프 레그라고 이렇게 성격별로 동그라미 만들어서 관계를 연결시켜 줘요."

> "전 세계 어디도 100% 없습니다... 작업자가 이걸 보고 승인 수정 반려를 할 수 있게끔 기능을 넣어놨어요."

> "이거는 저희가 다 따로 조절을 할 거고요. 멀티 엔진 앙상보 같은 경우에는 데이터 받아가지고 거기에 맞게끔 최적화시키는 게 우리의 특징이다."
