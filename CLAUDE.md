# AX POC - Claude Code Project Guide

> **LLM 최적화 프로젝트 가이드** | 마지막 업데이트: 2025-12-31
> 모든 문서: <100줄, 모듈식 구조, 계층적 구성

---

## 프로젝트 개요

**기계 도면 자동 분석 및 제조 견적 생성 시스템**

```
도면 이미지 → VLM 분류 → YOLO 검출 → OCR 추출 → 공차 분석 → 리비전 비교 → 견적 PDF
```

| 항목 | 값 |
|------|-----|
| **기술 스택** | FastAPI + React 19 + YOLO v11 + eDOCr2 + Docker |
| **프론트엔드** | http://localhost:5173 |
| **백엔드** | http://localhost:8000 |
| **Blueprint AI BOM** | http://localhost:5020 (v10.5) |
| **상태** | ✅ 전체 정상 (18/18 API healthy) |

---

## 핵심 파일 위치

### 프론트엔드 (web-ui/)

| 목적 | 파일 경로 |
|------|----------|
| **API 레지스트리** | `src/config/apiRegistry.ts` ⭐ 중앙화된 API 정의 |
| **노드 정의** | `src/config/nodeDefinitions.ts` |
| **스펙 서비스** | `src/services/specService.ts` |
| **노드 훅** | `src/hooks/useNodeDefinitions.ts` |
| **API 클라이언트** | `src/lib/api.ts` |
| **스토어** | `src/store/workflowStore.ts`, `apiConfigStore.ts` |
| **BlueprintFlow** | `src/pages/blueprintflow/BlueprintFlowBuilder.tsx` |
| **Dashboard 모니터링** | `src/components/monitoring/APIStatusMonitor.tsx` |
| **Dashboard 설정** | `src/pages/admin/APIDetail.tsx` |
| **테스트** | `src/config/nodeDefinitions.test.ts`, `src/store/apiConfigStore.test.ts` |
| **번역** | `src/locales/ko.json`, `src/locales/en.json` |
| **ESLint** | `eslint.config.js` |
| **Vite 설정** | `vite.config.ts` |

### 백엔드 (gateway-api/)

| 목적 | 파일 경로 |
|------|----------|
| **API 서버** | `api_server.py` |
| **API 스펙** | `api_specs/*.yaml` |
| **Executor 레지스트리** | `blueprintflow/executors/executor_registry.py` |
| **YOLO Executor** | `blueprintflow/executors/yolo_executor.py` |
| **서비스 레이어** | `services/yolo_service.py`, `services/edocr2_service.py` |
| **테스트** | `tests/test_executor_registry.py` |

### API 소스코드 (models/)

| 목적 | 파일 경로 |
|------|----------|
| **YOLO API** | `models/yolo-api/api_server.py` |
| **eDOCr2 API** | `models/edocr2-v2-api/api_server.py` |
| **기타 API** | `models/{api-id}-api/api_server.py` |

### 스크립트 (scripts/)

| 목적 | 파일 경로 |
|------|----------|
| **API 스캐폴딩** | `scripts/create_api.py` |

---

## API 서비스 (19개)

| 카테고리 | 서비스 | 포트 | 용도 |
|----------|--------|------|------|
| **Detection** | YOLO | 5005 | 객체 검출 (model_type: engineering, pid_class_aware, bom_detector 등) |
| **OCR** | eDOCr2 | 5002 | 한국어 치수 인식 |
| **OCR** | PaddleOCR | 5006 | 다국어 OCR |
| **OCR** | Tesseract | 5008 | 문서 OCR |
| **OCR** | TrOCR | 5009 | 필기체 OCR |
| **OCR** | OCR Ensemble | 5011 | 4엔진 가중 투표 |
| **OCR** | Surya OCR | 5013 | 90+ 언어, 레이아웃 분석 |
| **OCR** | DocTR | 5014 | 2단계 파이프라인 |
| **OCR** | EasyOCR | 5015 | 80+ 언어, CPU 친화적 |
| **Segmentation** | EDGNet | 5012 | 엣지 세그멘테이션 |
| **Segmentation** | Line Detector | 5016 | P&ID 라인 검출, 스타일 분류, 영역 검출 |
| **Preprocessing** | ESRGAN | 5010 | 4x 업스케일링 |
| **Analysis** | SkinModel | 5003 | 공차 분석 |
| **Analysis** | PID Analyzer | 5018 | P&ID 연결 분석, BOM 생성 |
| **Analysis** | Design Checker | 5019 | P&ID 설계 규칙 검증 |
| **Analysis** | Blueprint AI BOM | 5020 | 도면 BOM 생성, Human-in-the-Loop |
| **Knowledge** | Knowledge | 5007 | Neo4j + GraphRAG |
| **AI** | VL | 5004 | Vision-Language 모델 |
| **Orchestrator** | Gateway | 8000 | 파이프라인 조정 |

---

## 개발 명령어

```bash
# 프론트엔드
cd web-ui
npm run dev          # 개발 서버
npm run build        # 프로덕션 빌드
npm run lint         # ESLint 검사
npm run test:run     # 테스트 실행

# 백엔드
cd gateway-api
pytest tests/ -v     # 테스트 실행

# Docker
docker-compose up -d          # 전체 서비스 시작
docker logs gateway-api -f    # 로그 확인
```

---

## 코드 품질 기준

### TypeScript

| 항목 | 상태 | 기준 |
|------|------|------|
| 빌드 | ✅ | 에러 0개 |
| ESLint | ✅ | 에러 0개, 경고 3개 |
| 테스트 | ✅ | 141개 통과 |

### 카테고리 타입

```typescript
type NodeCategory =
  | 'input' | 'detection' | 'ocr' | 'segmentation'
  | 'preprocessing' | 'analysis' | 'knowledge' | 'ai' | 'control';
```

**주의**: `'api'` 타입은 더 이상 사용하지 않음. 반드시 위 카테고리 중 하나 사용.

---

## 파일 크기 및 모듈화 규칙 (LLM 최적화)

> **핵심 원칙**: 모든 소스 파일은 **1,000줄 이하**로 유지

### 디자인 패턴 점수 (2025-12-31)

| 영역 | 점수 | 비고 |
|------|------|------|
| 모듈 & 책임 분리 | **25/25** | admin_router 추가 분리 (docker, results) ✅ |
| **파일 크기 (LLM 친화성)** | **25/25** | **모든 1000줄+ 파일 분리 완료 ✅** |
| 설정 관리 | **15/15** | constants/ SSOT, YAML 스펙 기반 ✅ |
| 공통 패턴 | **15/15** | subprocess_utils.py 추출, lifespan ✅ |
| 테스트 & 문서 | **10/10** | **505개 테스트 통과** (gateway 364, web-ui 141) ✅ |
| 코드 중복 제거 | **10/10** | SSOT + Response Model 네이밍 충돌 해결 ✅ |
| **총점** | **100/100** | **🎯 목표 달성!** |

### 우선순위별 분리 대상 파일 (9개) - 모두 완료 ✅

| 우선순위 | 파일 | 변경 | 분리 결과 | 상태 |
|----------|------|------|----------|------|
| **P0** | `gateway-api/api_server.py` | ~~2,044줄~~ → 335줄 | 4개 라우터 분리 | ✅ 완료 |
| **P0** | `blueprint-ai-bom/frontend/src/lib/api.ts` | ~~1,806줄~~ → 14개 파일 | 도메인별 분리 (최대 401줄) | ✅ 완료 |
| **P1** | `web-ui/src/pages/dashboard/Guide.tsx` | ~~1,235줄~~ → 151줄 | `guide/` 디렉토리 (hooks, sections) | ✅ 완료 |
| **P1** | `web-ui/src/pages/admin/APIDetail.tsx` | ~~1,197줄~~ → 248줄 | `api-detail/` 디렉토리 (components, hooks, config) | ✅ 완료 |
| **P1** | `blueprint-ai-bom/.../pid_features_router.py` | ~~1,101줄~~ → 118줄 | `pid_features/` 디렉토리 (6개 라우터) | ✅ 완료 |
| **P2** | `models/pid-analyzer-api/region_extractor.py` | ~~1,082줄~~ → 57줄 | `region/` 디렉토리 (5개 모듈) | ✅ 완료 |
| **P2** | `models/edocr2-v2-api/api_server_edocr_v1.py` | ~~1,068줄~~ → 97줄 | `edocr_v1/` 디렉토리 (routers, services) | ✅ 완료 |
| **P2** | `models/design-checker-api/bwms_rules.py` | ~~1,031줄~~ → 89줄 | `bwms/` 디렉토리 (8개 모듈) | ✅ 완료 |
| **P2** | `web-ui/.../blueprintflow/NodePalette.tsx` | ~~1,024줄~~ → 189줄 | `node-palette/` 디렉토리 (components, hooks) | ✅ 완료 |

### 개선 로드맵

```
시작: 72점
  ↓ P0 완료 (+5점)
Phase 1: 77점 ✅
  ↓ P1 완료 (+5점)
Phase 2: 82점 ✅
  ↓ P2 완료 (+8점) + 테스트 확대
Phase 3: 90점 ✅
  ↓ SSOT 강화 + subprocess_utils 추출
Phase 4: 98점 ✅
  ↓ Response Model 네이밍 충돌 해결
Phase 5: 99점 ✅
  ↓ 라우터별 테스트 추가 (34개)
🎯 목표 달성: 100점 ✅
```

### 파일 크기 기준

| 라인 수 | 상태 | 조치 |
|---------|------|------|
| < 300줄 | ✅ 이상적 | 유지 |
| 300-500줄 | ✅ 양호 | 유지 |
| 500-800줄 | ⚠️ 주의 | 리팩토링 고려 |
| 800-1000줄 | ⚠️ 경고 | 리팩토링 권장 |
| > 1000줄 | ❌ 위반 | **즉시 분리 필수** |

### 분리 전략

**React 컴포넌트 (TSX)**:
```
BigComponent.tsx (1500줄)
    ↓ 분리
├── hooks/
│   ├── useComponentState.ts      # useState 중앙화
│   ├── useComponentEffects.ts    # useEffect 중앙화
│   └── useComponentHandlers.ts   # 이벤트 핸들러
├── sections/
│   ├── SectionA.tsx              # UI 섹션 분리
│   └── SectionB.tsx
├── components/
│   └── SubComponent.tsx          # 재사용 컴포넌트
└── BigComponent.tsx              # 조합만 담당 (300줄 이하)
```

**FastAPI 라우터 (Python)**:
```
big_router.py (2800줄)
    ↓ 분리
├── routers/
│   ├── feature_a_router.py       # 기능별 분리
│   ├── feature_b_router.py
│   └── __init__.py               # 라우터 통합
└── services/
    └── feature_service.py        # 비즈니스 로직
```

### 모듈화 체크리스트

새 기능 추가 시:
- [ ] 파일이 500줄 이상이면 분리 계획 수립
- [ ] 상태 관리 → 커스텀 훅으로 추출
- [ ] 반복 UI → 별도 컴포넌트로 추출
- [ ] 비즈니스 로직 → 서비스 레이어로 이동
- [ ] index.ts에 모든 export 등록

### 이점

1. **LLM 컨텍스트 효율성**: 작은 파일 = 정확한 코드 생성
2. **병렬 개발**: 여러 파일 동시 수정 가능
3. **테스트 용이**: 단위 테스트 작성 간편
4. **코드 재사용**: 훅/컴포넌트 다른 곳에서 import

### 예시: Blueprint AI BOM 리팩토링

```
Before (2025-12-24):
├── WorkflowPage.tsx          4,599줄  ❌
└── analysis_router.py        2,866줄  ❌

After (2025-12-26):
├── WorkflowPage.tsx            595줄  ✅
├── workflow/
│   ├── hooks/ (9개)          1,200줄
│   ├── sections/ (16개)      3,200줄
│   ├── components/ (3개)       700줄
│   └── 평균 파일 크기         ~190줄  ✅
└── routers/
    ├── analysis/ (6개)       1,915줄
    ├── midterm_router.py       580줄
    └── longterm_router.py      458줄  ✅
```

---

## 자주 하는 작업

### 1. 새 API 추가 (스캐폴딩 스크립트 사용)

```bash
# 스크립트 실행 - 자동으로 모든 파일 생성
python scripts/create_api.py my-detector --port 5015 --category detection

# 생성되는 파일:
# - models/my-detector-api/api_server.py    ← 실제 로직 구현
# - models/my-detector-api/Dockerfile
# - models/my-detector-api/requirements.txt
# - gateway-api/api_specs/my-detector.yaml  ← BlueprintFlow 메타데이터

# 다음 단계:
# 1. api_server.py의 process() 함수에 실제 로직 구현
# 2. docker-compose.yml에 서비스 추가
# 3. docker-compose up --build my-detector-api
```

**카테고리 옵션**: detection, ocr, segmentation, preprocessing, analysis, knowledge, ai, control

### 1-1. 참조 논문 추가 (새 API 추가 시 필수)

새 API를 추가할 때는 해당 기술의 참조 논문도 함께 정리해야 합니다.

```bash
# 1. 논문 검색 (WebSearch 사용)
# 검색 쿼리: "[기술명] paper arxiv [년도]"

# 2. 논문 파일 생성
cp docs/papers/TEMPLATE.md docs/papers/XX_[기술명]_[카테고리].md

# 3. 논문 내용 작성 (템플릿 섹션 채우기)
# - 논문 정보 (arXiv, 저자, 게재지)
# - 연구 배경
# - 핵심 방법론
# - AX 시스템 적용

# 4. Docs 페이지 업데이트
# web-ui/src/pages/docs/Docs.tsx의 docStructure에 추가

# 5. papers/README.md 논문 목록 업데이트
```

**참조**: `docs/papers/README.md` - 전체 논문 목록 및 가이드

### 1-2. Dashboard 설정 추가 (새 API 추가 시 필수)

Dashboard에서 새 API의 모니터링 및 설정을 위해 다음 파일을 업데이트해야 합니다:

**1. `web-ui/src/components/monitoring/APIStatusMonitor.tsx`**:
- `DEFAULT_APIS` 배열에 API 정보 추가
- `apiToContainerMap`에 컨테이너 매핑 추가
- `apiToSpecIdMap`에 스펙 ID 매핑 추가

**2. `web-ui/src/pages/admin/APIDetail.tsx`**:
- `DEFAULT_APIS` 배열에 API 정보 추가
- `HYPERPARAM_DEFINITIONS`에 하이퍼파라미터 UI 정의 추가
- `DEFAULT_HYPERPARAMS`에 기본값 추가

**예시** (Line Detector 추가):
```typescript
// DEFAULT_APIS
{ id: 'line_detector', name: 'line_detector', display_name: 'Line Detector',
  base_url: 'http://localhost:5016', port: 5016,
  status: 'unknown', category: 'segmentation',
  description: 'P&ID 라인 검출', icon: '📐', color: '#7c3aed' }

// HYPERPARAM_DEFINITIONS
line_detector: [
  { label: '검출 방식', type: 'select', options: ['lsd', 'hough', 'combined'], description: '...' },
  { label: '라인 유형 분류', type: 'boolean', description: '...' },
]

// DEFAULT_HYPERPARAMS
line_detector: { method: 'lsd', classify_types: true, visualize: true }
```

### 1-3. 웹에서 컨테이너 GPU/메모리 설정

Dashboard에서 직접 컨테이너 GPU/메모리 설정을 변경하고 적용할 수 있습니다:

1. Dashboard → API 상세 페이지 접속
2. "현재 컨테이너 상태" 패널에서 실시간 GPU/CPU 상태 확인
3. 연산 장치를 CPU/CUDA로 변경
4. GPU 메모리 제한 설정 (예: 4g, 6g)
5. 저장 버튼 클릭 → 컨테이너 자동 재생성 (5-10초)

**API 엔드포인트**:
- `GET /admin/container/status/{service}` - 컨테이너 상태 조회
- `POST /admin/container/configure/{service}` - GPU/메모리 설정 및 재생성

**참고**: 설정은 `docker-compose.override.yml`에 저장되어 원본 docker-compose.yml을 수정하지 않습니다.

### 1-4. GPU Override 시스템 (docker-compose.override.yml)

GPU 설정은 `docker-compose.yml`에 하드코딩하지 않고, `docker-compose.override.yml`에서 동적으로 관리합니다.

#### 왜 GPU가 기본적으로 OFF인가?

| 이유 | 설명 |
|------|------|
| **VRAM 고갈** | 8개 API가 동시에 GPU 모드로 시작하면 모델을 VRAM에 미리 로드하여 GPU 메모리 고갈 |
| **필요시 활성화** | 실제 추론 시에만 특정 API의 GPU 활성화가 효율적 |
| **개발 환경 호환** | GPU 없는 환경에서도 바로 실행 가능 |

#### GPU 지원 API (8개)

| 서비스명 | 컨테이너 | 용도 |
|----------|----------|------|
| YOLO | yolo-api | 객체 검출 |
| eDOCr2 | edocr2-v2-api | OCR |
| PaddleOCR | paddleocr-api | OCR |
| TrOCR | trocr-api | OCR |
| EDGNet | edgnet-api | 세그멘테이션 |
| ESRGAN | esrgan-api | 업스케일링 |
| Line Detector | line-detector-api | 라인 검출 |
| Blueprint AI BOM | blueprint-ai-bom-backend | BOM 생성 |

#### 새 환경 설정 (템플릿 사용)

```bash
# 1. 템플릿 복사
cp docker-compose.override.yml.example docker-compose.override.yml

# 2. 필요한 서비스만 GPU 활성화 (파일 편집)
# 또는 Dashboard에서 동적으로 설정

# 3. 서비스 재시작
docker-compose up -d
```

#### 파일 구조

```
docker-compose.yml              # 기본 설정 (GPU 없음)
docker-compose.override.yml     # GPU 설정 (로컬용, .gitignore)
docker-compose.override.yml.example  # 템플릿 (Git 추적)
```

#### 수동 GPU 설정 예시

```yaml
# docker-compose.override.yml
services:
  yolo-api:
    deploy:
      resources:
        reservations:
          devices:
          - capabilities: [gpu]
            count: 1
            driver: nvidia
```

**주의**: `docker-compose.override.yml`은 `.gitignore`에 포함되어 있어 각 환경마다 별도로 설정해야 합니다.

### 2. 기존 방식 (수동)

1. `models/{api-id}-api/api_server.py` 생성
2. `gateway-api/api_specs/{api-id}.yaml` 생성
3. docker-compose.yml에 서비스 추가
4. Dashboard 설정 추가 (위 1-2 참조)

### 3. 파라미터 수정

1. `gateway-api/api_specs/{api-id}.yaml` - 스펙 파일 수정
2. 또는 `nodeDefinitions.ts` - 프론트엔드 직접 수정 (정적 정의가 우선)
3. `*_executor.py` - 백엔드 처리 로직

### 4. 테스트 추가

```typescript
// 프론트엔드: src/**/*.test.ts
import { describe, it, expect } from 'vitest';

describe('TestName', () => {
  it('should do something', () => {
    expect(true).toBe(true);
  });
});
```

```python
# 백엔드: tests/test_*.py
import pytest

class TestName:
    def test_something(self):
        assert True
```

---

## BlueprintFlow

### 노드 타입 (28개)

| 카테고리 | 노드 |
|----------|------|
| Input | ImageInput, TextInput |
| Detection | YOLO (model_type으로 P&ID 검출 지원) |
| OCR | eDOCr2, PaddleOCR, Tesseract, TrOCR, OCR Ensemble, SuryaOCR, DocTR, EasyOCR |
| Segmentation | EDGNet, Line Detector |
| Preprocessing | ESRGAN |
| Analysis | SkinModel, PID Analyzer, Design Checker |
| Analysis (신규) | **GT Comparison**, **PDF Export**, **Excel Export**, **PID Features**, **Verification Queue** |
| BOM | Blueprint AI BOM |
| Knowledge | Knowledge |
| AI | VL |
| Control | IF, Loop, Merge |

### 신규 노드 (2025-12-31)

| 노드 | 타입 | 설명 |
|------|------|------|
| GT Comparison | `gtcomparison` | 검출 성능 평가 (Precision/Recall/F1) |
| PDF Export | `pdfexport` | P&ID 분석 PDF 리포트 생성 |
| Excel Export | `excelexport` | P&ID 분석 Excel 스프레드시트 |
| PID Features | `pidfeatures` | TECHCROSS 통합 분석 (Valve/Equipment/Checklist) |
| Verification Queue | `verificationqueue` | Human-in-the-Loop 검증 큐 관리 |

### 파라미터 커버리지 (100%)

총 70개+ 파라미터가 nodeDefinitions.ts에 정의됨.

---

## CI/CD

`.github/workflows/ci.yml`:
- Node.js 20 + npm ci
- ESLint, TypeScript build, Vitest
- Python 3.11 + ruff + pytest

---

## 번들 최적화

`vite.config.ts`에서 코드 분할 적용:

| 청크 | 포함 라이브러리 |
|------|----------------|
| vendor-react | react, react-dom, react-router-dom |
| vendor-charts | recharts, mermaid |
| vendor-flow | reactflow |
| vendor-utils | axios, zustand, date-fns, i18next |

**결과**: 2.2MB → 1.18MB (46% 감소)

---

## 알려진 이슈

| 이슈 | 상태 | 해결책 |
|------|------|--------|
| ESLint any 경고 158개 | ⚠️ | error → warn 변경됨 |
| 번들 크기 경고 | ⚠️ | chunkSizeWarningLimit: 600 |

---

## 문서 구조

```
docs/
├── 00_INDEX.md           # 전체 인덱스
├── api/                  # API별 문서
│   ├── yolo/
│   ├── edocr2/
│   └── ...
├── blueprintflow/        # BlueprintFlow 문서
│   ├── 01_overview.md
│   ├── 02_node_types.md
│   └── ...
├── insights/             # 벤치마크 & 인사이트 아카이브
│   ├── README.md
│   ├── benchmarks/       # 성능 측정 결과
│   ├── optimizations/    # 최적화 실험
│   ├── model-comparisons/# 모델 비교 분석
│   └── lessons-learned/  # 베스트 프랙티스
└── papers/               # 참조 논문 정리
```

---

## R&D (Research & Development)

SOTA 논문 수집, 실험 및 벤치마크 관리를 위한 R&D 디렉토리:

```
rnd/
├── README.md             # R&D 전체 개요
├── papers/               # SOTA 논문 인덱스 (35개)
│   └── README.md        # 논문 목록 및 적용 계획
├── experiments/          # 실험 기록 (향후)
├── benchmarks/           # 성능 벤치마크 (향후)
└── models/               # 커스텀 모델 실험 (향후)
```

### 수집된 SOTA 논문 (35개)

| 카테고리 | 수량 | 핵심 기술 |
|----------|------|-----------|
| Object Detection | 6 | YOLOv11, YOLO26, VajraV1 |
| OCR & Document | 7 | PaddleOCR 3.0, TrOCR, DocTR |
| P&ID Analysis | 6 | Relationformer, PID2Graph |
| Vision-Language | 6 | LLaVA-o1, GPT-4V, ALLaVA |
| Layout Analysis | 6 | SCAN, DocLayNet, UnSupDLA |
| GD&T Recognition | 4 | YOLOv8/v11 기반 |

### R&D 우선순위

| 우선순위 | 연구 주제 | 적용 대상 | 참조 논문 |
|----------|-----------|----------|----------|
| **P0** | YOLOv11 아키텍처 | YOLO API | arXiv 2410.17725 |
| **P0** | PaddleOCR 3.0 | PaddleOCR API | arXiv 2507.05595 |
| **P1** | Relationformer P&ID | PID Analyzer | arXiv 2411.13929 |
| **P1** | LLaVA-o1 추론 | VL API | arXiv 2411.10440 |
| **P2** | P&ID + RAG + LLM | Knowledge API | arXiv 2502.18928 |

**상세 문서**: [rnd/papers/README.md](rnd/papers/README.md)

---

## API 스펙 시스템

새 API 추가 시 자동 통합을 위한 YAML 기반 스펙 시스템:

```
gateway-api/api_specs/
├── api_spec_schema.json    # JSON Schema (검증용)
├── CONVENTIONS.md          # API 스펙 작성 컨벤션
├── yolo.yaml               # YOLO Detection (model_type으로 P&ID 지원)
├── edocr2.yaml             # eDOCr2 OCR
├── edgnet.yaml             # EDGNet Segmentation
├── line-detector.yaml      # P&ID Line Detection
├── vl.yaml                 # Vision-Language
├── skinmodel.yaml          # SkinModel Tolerance
├── pid-analyzer.yaml       # P&ID Connectivity & BOM
├── design-checker.yaml     # P&ID Design Validation
├── paddleocr.yaml          # PaddleOCR
├── knowledge.yaml          # Knowledge Engine
├── tesseract.yaml          # Tesseract OCR
├── trocr.yaml              # TrOCR
├── esrgan.yaml             # ESRGAN Upscaler
├── ocr-ensemble.yaml       # OCR Ensemble
├── suryaocr.yaml           # Surya OCR (90+ 언어)
├── doctr.yaml              # DocTR (2단계 파이프라인)
├── easyocr.yaml            # EasyOCR (80+ 언어)
└── blueprint-ai-bom.yaml   # Blueprint AI BOM (Human-in-the-Loop)
```

**API 엔드포인트**:
- `GET /api/v1/specs` - 모든 스펙 조회
- `GET /api/v1/specs/{api_id}` - 특정 스펙 조회
- `GET /api/v1/specs/{api_id}/blueprintflow` - 노드 메타데이터
- `GET /api/v1/specs/resources` - 모든 API 리소스 요구사항 (동적 로드)

### 리소스 스펙 (resources 섹션)

각 API 스펙 YAML 파일에 `resources` 섹션 포함 (Dashboard에서 동적 로드):

```yaml
resources:
  gpu:
    vram: "~2GB"           # 예상 VRAM
    minVram: 1500          # 최소 VRAM (MB)
    recommended: "RTX 3060 이상"
    cudaVersion: "11.8+"
  cpu:
    ram: "~3GB"            # 예상 RAM
    minRam: 2048           # 최소 RAM (MB)
    cores: 4
    note: "GPU 대비 10배 느림"
  parameterImpact:         # 하이퍼파라미터 영향
    - parameter: imgsz
      impact: "imgsz↑ → VRAM↑"
      examples: "640:1.5GB, 1280:2.5GB"
```

---

## 버전 히스토리

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| **23.0** | **2025-12-31** | **코드 품질 개선**: ESLint 에러 0개 달성, Executor 단위 테스트 126개 추가, Feature Definition 동기화 자동화 스크립트, Executor 개발 가이드 문서. 총 505개 테스트 통과 (gateway 364, web-ui 141) |
| 22.0 | 2025-12-31 | BlueprintFlow 5개 신규 노드: GT Comparison, PDF Export, Excel Export, PID Features, Verification Queue. 총 28개 노드, 379개 테스트 통과 |
| 21.0 | 2025-12-31 | R&D 디렉토리 신설: SOTA 논문 35개 수집 (YOLO, OCR, P&ID, VLM, Layout, GD&T), 연구 로드맵 수립, TECHCROSS 문서 최신화 |
| 20.0 | 2025-12-31 | 🎯 디자인 패턴 100점 달성: Response Model 네이밍 충돌 해결, constants/ SSOT, subprocess_utils.py 추출, docker/results/gpu_config/admin 라우터 테스트 추가 (34개), 총 329개 테스트 통과 |
| 19.0 | 2025-12-31 | P0~P2 리팩토링 완료: 9개 대형 파일 모두 분리 (Guide.tsx 151줄, APIDetail.tsx 248줄, NodePalette.tsx 189줄 등), 디자인 패턴 점수 90/100점 |
| 18.0 | 2025-12-30 | TECHCROSS Human-in-the-Loop 워크플로우: Blueprint AI BOM v10.5에 TECHCROSS 1-1~1-4 통합, Valve Signal/Equipment/Checklist 검증, Active Learning 기반 검증 큐, Excel 내보내기 |
| 17.0 | 2025-12-29 | Design Checker v1.0 리팩토링: api_server.py 1,482줄→167줄 분리, BWMS 규칙 관리 시스템 (Excel 업로드, YAML 저장, 프로필 관리), lifespan 패턴 적용, 20개 엔드포인트 |
| 16.0 | 2025-12-28 | Line Detector v1.1: 라인 스타일 분류 (실선/점선/일점쇄선 등 6종), 점선 박스 영역 검출 (SIGNAL FOR BWMS 등), 라인 용도 분류 (ISO 10628 기반), 테스트 16개 통과 |
| 15.0 | 2025-12-27 | Blueprint AI BOM v10.3: 장기 로드맵 4/4 기능 완전 구현 (VLM 분류, 노트 추출, 영역 세분화, 리비전 비교), 테스트 59개 통과 |
| 14.0 | 2025-12-26 | GPU Override 시스템: docker-compose.override.yml 기반 동적 GPU 설정, Dashboard GPU 토글 버그 수정 |
| 13.0 | 2025-12-26 | 모듈화 리팩토링: 1000줄 제한 규칙, WorkflowPage 595줄로 분리, LLM 최적화 가이드 추가 |
| 12.0 | 2025-12-24 | Blueprint AI BOM v9.0: 장기 로드맵 API 스텁 생성 |
| 11.0 | 2025-12-24 | 18개 기능 체크박스 툴팁, 전체 API 18/18 healthy |
| 10.0 | 2025-12-10 | 웹 기반 컨테이너 GPU/메모리 설정, 실시간 컨테이너 상태 표시 |
| 9.0 | 2025-12-09 | 동적 리소스 로딩 시스템, 인사이트 아카이브 (benchmarks, lessons-learned) |
| 8.0 | 2025-12-06 | P&ID 분석 시스템 (YOLO model_type, Line Detector, PID Analyzer, Design Checker) |
| 7.0 | 2025-12-03 | API 스펙 표준화 시스템, 스캐폴딩 스크립트 |
| 6.0 | 2025-12-03 | 테스트 체계 구축, ESLint 정리, 번들 최적화 |
| 5.0 | 2025-12-01 | 5개 신규 API 추가 (Knowledge, Tesseract, TrOCR, ESRGAN, OCR Ensemble) |
| 4.0 | 2025-11-22 | TextInput 노드, 병렬 실행 |

---

## Blueprint AI BOM (v10.5)

**Human-in-the-Loop 도면 BOM 생성 시스템**

### 핵심 기능
| 기능 | 설명 |
|------|------|
| 심볼 검출 | YOLO v11 기반 27개 클래스 |
| 치수 OCR | eDOCr2 한국어 치수 인식 |
| GD&T 파싱 | 기하공차/데이텀 파싱 |
| Active Learning | 신뢰도 기반 검증 큐 |
| Feedback Loop | YOLO 재학습 데이터셋 내보내기 |

### 장기 로드맵 (v10.3 전체 완료) ✅
| 기능 | 상태 | 구현 |
|------|------|------|
| 🤖 VLM 분류 | ✅ 완료 | GPT-4o-mini 멀티 프로바이더 |
| 📋 노트 추출 | ✅ 완료 | LLM + 정규식 폴백 |
| 🗺️ 영역 세분화 | ✅ 완료 | 휴리스틱 + VLM 하이브리드 |
| 🔄 리비전 비교 | ✅ 완료 | SSIM + 데이터 + VLM |

### TECHCROSS 워크플로우 (v10.5 신규) ✅
| 요구사항 | 기능 | 상태 | 구현 |
|----------|------|------|------|
| 1-1 | BWMS Checklist | ✅ 완료 | Design Checker 연동, 60개 항목 |
| 1-2 | Valve Signal List | ✅ 완료 | PID Analyzer 연동, Human-in-the-Loop |
| 1-3 | Equipment List | ✅ 완료 | PID Analyzer 연동, Human-in-the-Loop |
| 1-4 | Deviation List | 📋 계획됨 | 향후 구현 예정 |

#### TECHCROSS 엔드포인트 (10개)
| 그룹 | 엔드포인트 | 설명 |
|------|------------|------|
| Valve Signal | `POST /{session_id}/valve-signal/detect` | 밸브 신호 검출 |
| Equipment | `POST /{session_id}/equipment/detect` | 장비 검출 |
| Checklist | `POST /{session_id}/checklist/check` | 체크리스트 검증 |
| Verification | `GET /{session_id}/verify/queue` | 검증 큐 조회 |
| Verification | `POST /{session_id}/verify` | 단일 항목 검증 |
| Verification | `POST /{session_id}/verify/bulk` | 대량 검증 |
| Export | `POST /{session_id}/export` | Excel 내보내기 |
| Summary | `GET /{session_id}/summary` | 워크플로우 요약 |

### 테스트 현황
| 테스트 | 수량 | 상태 |
|--------|------|------|
| 단위 테스트 | 46개 | ✅ 통과 |
| 장기 로드맵 테스트 | 32개 | ✅ 통과 |
| **총계** | **59개** | **✅ 통과** |

**문서**: [blueprint-ai-bom/docs/](blueprint-ai-bom/docs/README.md)

---

## Design Checker API (v1.0)

**P&ID 도면 설계 오류 검출 및 규정 검증 API**

### 아키텍처 (리팩토링 완료)

```
models/design-checker-api/
├── api_server.py       (167줄)  # FastAPI 앱, lifespan
├── schemas.py          (81줄)   # Pydantic 모델
├── constants.py        (219줄)  # 규칙 정의 (20개)
├── checker.py          (354줄)  # 설계 검증 로직
├── bwms_rules.py       (822줄)  # BWMS 규칙 (7+동적)
├── rule_loader.py      (260줄)  # YAML 기반 규칙 관리
├── excel_parser.py     (210줄)  # 체크리스트 Excel 파싱
└── routers/
    ├── check_router.py    (220줄)  # /api/v1/check
    ├── rules_router.py    (295줄)  # /api/v1/rules/*
    └── checklist_router.py (311줄) # /api/v1/checklist/*
```

### 핵심 기능

| 기능 | 설명 |
|------|------|
| 설계 검증 | 20개 규칙 (connectivity, symbol, labeling 등) |
| BWMS 검증 | 7개 내장 규칙 + 동적 규칙 |
| 규칙 관리 | Excel 업로드, YAML 저장, 프로필 관리 |
| 제품 필터 | ALL / ECS / HYCHLOR 타입별 규칙 |

### 엔드포인트 (20개)

| 그룹 | 수량 | 주요 엔드포인트 |
|------|------|----------------|
| Health | 3개 | /health, /api/v1/info |
| Check | 3개 | /api/v1/check, /api/v1/check/bwms |
| Rules | 7개 | /api/v1/rules, /disable, /enable |
| Checklist | 5개 | /upload, /template, /current |
| Profile | 2개 | /activate, /deactivate |

### 지원 표준

| 표준 | 설명 |
|------|------|
| **ISO 10628** | P&ID 표준 |
| **ISA 5.1** | 계기 심볼 표준 |
| **TECHCROSS BWMS** | 선박평형수처리시스템 규정 |

### 규칙 파일 구조

```
config/
├── common/          # 공통 규칙
├── ecs/             # ECS 제품 전용
├── hychlor/         # HYCHLOR 제품 전용
└── custom/          # 사용자 정의
```

**문서**: [docs/api/design-checker/](docs/api/design-checker/)

---

**Managed By**: Claude Code (Opus 4.5)
