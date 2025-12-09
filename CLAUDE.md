# AX POC - Claude Code Project Guide

> **LLM 최적화 프로젝트 가이드** | 마지막 업데이트: 2025-12-09
> 모든 문서: <100줄, 모듈식 구조, 계층적 구성

---

## 프로젝트 개요

**기계 도면 자동 분석 및 제조 견적 생성 시스템**

```
도면 이미지 → YOLO 검출 → OCR 추출 → 공차 분석 → 견적 PDF
```

| 항목 | 값 |
|------|-----|
| **기술 스택** | FastAPI + React 19 + YOLO v11 + eDOCr2 + Docker |
| **프론트엔드** | http://localhost:5173 |
| **백엔드** | http://localhost:8000 |
| **상태** | Phase 6 진행 중 (테스트 & 최적화) |

---

## 핵심 파일 위치

### 프론트엔드 (web-ui/)

| 목적 | 파일 경로 |
|------|----------|
| **노드 정의** | `src/config/nodeDefinitions.ts` |
| **스펙 서비스** | `src/services/specService.ts` |
| **노드 훅** | `src/hooks/useNodeDefinitions.ts` |
| **API 클라이언트** | `src/lib/api.ts` |
| **스토어** | `src/store/workflowStore.ts`, `apiConfigStore.ts` |
| **BlueprintFlow** | `src/pages/blueprintflow/BlueprintFlowBuilder.tsx` |
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
| **Detection** | YOLO | 5005 | 객체 검출 (14가지 심볼) |
| **Detection** | YOLO-PID | 5017 | P&ID 심볼 검출 (60종) |
| **OCR** | eDOCr2 | 5002 | 한국어 치수 인식 |
| **OCR** | PaddleOCR | 5006 | 다국어 OCR |
| **OCR** | Tesseract | 5008 | 문서 OCR |
| **OCR** | TrOCR | 5009 | 필기체 OCR |
| **OCR** | OCR Ensemble | 5011 | 4엔진 가중 투표 |
| **OCR** | Surya OCR | 5013 | 90+ 언어, 레이아웃 분석 |
| **OCR** | DocTR | 5014 | 2단계 파이프라인 |
| **OCR** | EasyOCR | 5015 | 80+ 언어, CPU 친화적 |
| **Segmentation** | EDGNet | 5012 | 엣지 세그멘테이션 |
| **Segmentation** | Line Detector | 5016 | P&ID 라인 검출 |
| **Preprocessing** | ESRGAN | 5010 | 4x 업스케일링 |
| **Analysis** | SkinModel | 5003 | 공차 분석 |
| **Analysis** | PID Analyzer | 5018 | P&ID 연결 분석, BOM 생성 |
| **Analysis** | Design Checker | 5019 | P&ID 설계 규칙 검증 |
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
| ESLint | ⚠️ | 에러 0개 (경고 허용) |
| 테스트 | ✅ | 31개 통과 |

### 카테고리 타입

```typescript
type NodeCategory =
  | 'input' | 'detection' | 'ocr' | 'segmentation'
  | 'preprocessing' | 'analysis' | 'knowledge' | 'ai' | 'control';
```

**주의**: `'api'` 타입은 더 이상 사용하지 않음. 반드시 위 카테고리 중 하나 사용.

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

### 2. 기존 방식 (수동)

1. `models/{api-id}-api/api_server.py` 생성
2. `gateway-api/api_specs/{api-id}.yaml` 생성
3. docker-compose.yml에 서비스 추가

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

### 노드 타입 (20개)

| 카테고리 | 노드 |
|----------|------|
| Input | ImageInput, TextInput |
| Detection | YOLO, YOLO-PID |
| OCR | eDOCr2, PaddleOCR, Tesseract, TrOCR, OCR Ensemble |
| Segmentation | EDGNet, Line Detector |
| Preprocessing | ESRGAN |
| Analysis | SkinModel, PID Analyzer, Design Checker |
| Knowledge | Knowledge |
| AI | VL |
| Control | IF, Loop, Merge |

### 파라미터 커버리지 (100%)

총 50개 파라미터가 nodeDefinitions.ts에 정의됨.

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

## API 스펙 시스템

새 API 추가 시 자동 통합을 위한 YAML 기반 스펙 시스템:

```
gateway-api/api_specs/
├── api_spec_schema.json    # JSON Schema (검증용)
├── yolo.yaml               # YOLO Detection
├── yolo-pid.yaml           # YOLO-PID Symbol Detection
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
└── easyocr.yaml            # EasyOCR (80+ 언어)
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
| 9.0 | 2025-12-09 | 동적 리소스 로딩 시스템, 인사이트 아카이브 (benchmarks, lessons-learned) |
| 8.0 | 2025-12-06 | P&ID 분석 시스템 (YOLO-PID, Line Detector, PID Analyzer, Design Checker) |
| 7.0 | 2025-12-03 | API 스펙 표준화 시스템, 스캐폴딩 스크립트 |
| 6.0 | 2025-12-03 | 테스트 체계 구축, ESLint 정리, 번들 최적화 |
| 5.0 | 2025-12-01 | 5개 신규 API 추가 (Knowledge, Tesseract, TrOCR, ESRGAN, OCR Ensemble) |
| 4.0 | 2025-11-22 | TextInput 노드, 병렬 실행 |

---

**Managed By**: Claude Code (Opus 4.5)
