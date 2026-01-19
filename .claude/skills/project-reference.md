# 프로젝트 레퍼런스

이 스킬은 R&D 논문, API 스펙 시스템, 문서 구조에 대한 참조 정보입니다.

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
├── yolo.yaml               # YOLO Detection
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
├── blueprint-ai-bom.yaml   # Blueprint AI BOM
└── pid-composer.yaml       # PID Composer
```

### API 엔드포인트

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
| ESLint any 경고 158개 | 경고 | error → warn 변경됨 |
| 번들 크기 경고 | 경고 | chunkSizeWarningLimit: 600 |
