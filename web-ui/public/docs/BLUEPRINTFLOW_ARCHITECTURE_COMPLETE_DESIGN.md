# BlueprintFlow 아키텍처 설계서

**버전**: 3.0
**최종 수정**: 2026-01-17
**상태**: ✅ **전체 구현 완료**

---

## 구현 현황

| 항목 | 상태 | 세부 사항 |
|------|------|----------|
| **Frontend** | ✅ Complete | 28개 노드, 템플릿, 저장/불러오기 |
| **Backend Engine** | ✅ Complete | DAG 실행, 파이프라인 엔진 |
| **Control Flow** | ✅ Complete | IF, Loop, Merge 노드 |
| **Dynamic API** | ✅ Complete | 런타임 API 등록 |
| **API Services** | ✅ Complete | 20/20 healthy (100%) |
| **Blueprint AI BOM** | ✅ Complete | v10.5 TECHCROSS 통합 |
| **디자인 패턴** | ✅ Complete | 100/100점 달성 |
| **테스트** | ✅ Complete | 505개 통과 |

---

## 시스템 개요

### 워크플로우 흐름

```
사용자 → [시각적 빌더] → 워크플로우 정의 → 파이프라인 엔진 → 동적 실행 → 결과
```

### 주요 기능

1. **시각적 워크플로우 빌더**: ReactFlow 기반 드래그 앤 드롭
2. **동적 파이프라인 엔진**: DAG 실행, 조건 분기, 병렬 실행
3. **워크플로우 관리**: JSON 저장/불러오기, 템플릿 라이브러리

---

## 노드 타입 (28개)

### Input (2개)
| 노드 | 용도 |
|------|------|
| ImageInput | 이미지 입력 |
| TextInput | 텍스트 입력 |

### Detection (1개)
| 노드 | 포트 | 모델 |
|------|------|------|
| YOLO | 5005 | engineering, pid_class_aware, pid_class_agnostic, bom_detector |

### OCR (8개)
| 노드 | 포트 | 용도 |
|------|------|------|
| eDOCr2 | 5002 | 한국어 치수/GD&T |
| PaddleOCR | 5006 | 다국어 |
| Tesseract | 5008 | 문서 |
| TrOCR | 5009 | 필기체 |
| OCR Ensemble | 5011 | 4-엔진 투표 |
| Surya OCR | 5013 | 90+ 언어 |
| DocTR | 5014 | 2단계 파이프라인 |
| EasyOCR | 5015 | 80+ 언어 |

### Segmentation (2개)
| 노드 | 포트 | 용도 |
|------|------|------|
| EDGNet | 5012 | 엣지 세그멘테이션 |
| Line Detector | 5016 | P&ID 라인 검출 |

### Preprocessing (1개)
| 노드 | 포트 | 용도 |
|------|------|------|
| ESRGAN | 5010 | 4x 업스케일링 |

### Analysis (7개)
| 노드 | 포트 | 용도 |
|------|------|------|
| SkinModel | 5003 | 공차 분석 |
| PID Analyzer | 5018 | P&ID 연결 분석 |
| Design Checker | 5019 | 설계 검증 |
| Blueprint AI BOM | 5020 | Human-in-the-Loop BOM |
| PID Features | 5020 | TECHCROSS 통합 분석 |
| GT Comparison | 5020 | Ground Truth 비교 |
| Verification Queue | 5020 | 검증 큐 |

### Export (2개)
| 노드 | 포트 | 용도 |
|------|------|------|
| PDF Export | 5020 | PDF 리포트 |
| Excel Export | 5020 | Excel 내보내기 |

### Knowledge & AI (2개)
| 노드 | 포트 | 용도 |
|------|------|------|
| Knowledge | 5007 | Neo4j + GraphRAG |
| VL | 5004 | Vision-Language |

### Control (3개)
| 노드 | 용도 |
|------|------|
| IF | 조건 분기 |
| Loop | 반복 실행 |
| Merge | 결과 병합 |

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer (:5173)                    │
├─────────────────────────────────────────────────────────────┤
│  WorkflowBuilder  │  NodePalette  │  PropertyPanel  │ Exec  │
│    (ReactFlow)    │  (28 nodes)   │   (params)      │ Mon.  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Gateway Layer (:8000)                     │
├─────────────────────────────────────────────────────────────┤
│  Pipeline Engine  │  DAG Validator  │  Data Mapper  │ SSE  │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Detection   │   │      OCR      │   │   Analysis    │
│   YOLO:5005   │   │ eDOCr2:5002   │   │ Design:5019   │
│               │   │ Paddle:5006   │   │   BOM:5020    │
│               │   │ Tess:5008     │   │ Analyze:5018  │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## 파이프라인 엔진

### DAG 실행 알고리즘

1. **검증 단계**: 순환 참조, 고아 노드, 타입 검사
2. **계획 단계**: DAG 빌드, Topological Sort, 병렬화 최적화
3. **실행 단계**: 노드 스케줄링, 데이터 수집, 결과 저장
4. **모니터링**: SSE로 실시간 진행률 전송

### 데이터 매핑

```
YOLO 출력: { detections: [{bbox, class_name, confidence}] }
    ↓
데이터 매핑: $.detections[0].bbox → $.crop_region
    ↓
eDOCr2 입력: { crop_region: [x,y,w,h] }
```

---

## 워크플로우 정의 (JSON)

```json
{
  "workflow": {
    "id": "wf-12345",
    "name": "P&ID 분석 파이프라인",
    "nodes": [
      {
        "id": "node-1",
        "type": "yolo",
        "position": {"x": 100, "y": 100},
        "data": {
          "params": {
            "model_type": "pid_class_aware",
            "confidence": 0.25,
            "use_sahi": true
          }
        }
      },
      {
        "id": "node-2",
        "type": "pid-analyzer",
        "position": {"x": 300, "y": 100}
      }
    ],
    "edges": [
      {"source": "node-1", "target": "node-2"}
    ]
  }
}
```

---

## 파일 구조

### Frontend (web-ui/)

```
src/
├── pages/blueprintflow/
│   └── BlueprintFlowBuilder.tsx     # 메인 빌더
├── components/blueprintflow/
│   ├── Canvas.tsx                   # ReactFlow 캔버스
│   ├── node-palette/                # 노드 팔레트 (모듈화)
│   │   ├── NodePalette.tsx
│   │   └── constants.ts             # 노드 정의
│   ├── PropertyPanel.tsx            # 속성 패널
│   └── nodes/                       # 노드 컴포넌트
├── config/
│   ├── nodeDefinitions.ts           # 노드 메타데이터
│   ├── apiRegistry.ts               # API 레지스트리
│   └── nodes/                       # 카테고리별 노드 정의
│       ├── detectionNodes.ts
│       ├── ocrNodes.ts
│       └── analysisNodes.ts
└── store/
    └── workflowStore.ts             # Zustand 상태 관리
```

### Backend (gateway-api/)

```
├── api_server.py                    # 워크플로우 엔드포인트
├── blueprintflow/
│   ├── pipeline_engine.py           # 파이프라인 엔진
│   └── executors/
│       ├── executor_registry.py     # Executor 레지스트리
│       ├── yolo_executor.py
│       ├── edocr2_executor.py
│       └── ...
└── api_specs/                       # API 스펙 (YAML)
    ├── yolo.yaml
    ├── edocr2.yaml
    └── ...
```

---

## 권장 워크플로우

### 기계도면 치수 추출

```
ImageInput → YOLO (engineering) → eDOCr2 → SkinModel
```

### P&ID 분석

```
ImageInput → YOLO (pid_class_aware) → Line Detector → PID Analyzer → Design Checker
```

### TECHCROSS BWMS

```
ImageInput → PID Features → Verification Queue → Excel Export
```

---

## 성능

| 메트릭 | 값 |
|--------|-----|
| 노드 추가 지연 | < 50ms |
| 워크플로우 저장 | < 100ms |
| DAG 검증 | < 10ms |
| SSE 업데이트 주기 | 100ms |

---

## 접근 URL

- **BlueprintFlow Builder**: http://localhost:5173/blueprintflow/builder
- **API Dashboard**: http://localhost:5173/dashboard
- **Gateway API**: http://localhost:8000

---

**작성자**: Claude Code (Opus 4.5)
