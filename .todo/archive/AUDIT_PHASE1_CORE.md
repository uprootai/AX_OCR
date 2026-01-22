# Phase 1: 핵심 코드 조사 결과

> **조사일**: 2026-01-17
> **총 용량**: 2.5GB
> **디렉토리 수**: 4개

---

## 요약

| 디렉토리 | 용량 | 판정 | 정리 가능 용량 |
|----------|------|------|----------------|
| `web-ui/` | 487MB | ✅ 유지 | ~12MB (test-results, playwright-report) |
| `gateway-api/` | 19MB | ✅ 유지 | ~16MB (results, htmlcov) |
| `models/` | 1.8GB | ✅ 유지 | ~800MB (uploads, results, training) |
| `blueprint-ai-bom/` | 1.2GB | ✅ 유지 | ~3MB (uploads, results) |

**총 정리 가능**: ~830MB (런타임 아티팩트)

---

## 1. web-ui/ (487MB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/web-ui/` |
| 용량 | 487MB |
| 최종 수정 | 2026-01-17 (활발) |
| 기술 스택 | React 19 + TypeScript + Vite |

### 용량 분석

| 디렉토리 | 용량 | 비율 | 설명 |
|----------|------|------|------|
| `node_modules/` | 463MB | 95.1% | npm 패키지 (빌드 필수) |
| `dist/` | 11MB | 2.3% | 프로덕션 빌드 결과 |
| `public/` | 6.8MB | 1.4% | 정적 파일 (샘플 이미지) |
| `e2e/` | 2.3MB | 0.5% | E2E 테스트 코드 |
| `src/` | 1.7MB | 0.3% | 소스 코드 |
| `test-results/` | 1MB | 0.2% | Playwright 스크린샷 |
| `playwright-report/` | 512KB | 0.1% | 테스트 리포트 |
| 기타 | ~1MB | 0.1% | 설정 파일 등 |

### 구조

```
web-ui/
├── node_modules/     # 463MB - npm 패키지
├── dist/             # 11MB - 빌드 결과
├── public/           # 6.8MB - 정적 파일
│   └── samples/      # 테스트용 샘플 이미지
├── e2e/              # 2.3MB - E2E 테스트
│   ├── *.spec.ts     # 테스트 파일
│   ├── fixtures/     # 테스트 픽스처
│   └── plan/         # 테스트 계획 문서
├── src/              # 1.7MB - 소스 코드
│   ├── components/
│   ├── config/
│   ├── pages/
│   ├── services/
│   └── store/
├── test-results/     # 1MB - 테스트 결과
└── playwright-report/ # 512KB - 리포트
```

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ✅ 유지 |
| **사유** | 프로젝트 메인 프론트엔드. 필수 |
| **정리 가능** | test-results, playwright-report (~1.5MB) |

### 정리 명령어

```bash
# 테스트 결과물 정리
rm -rf web-ui/test-results/*
rm -rf web-ui/playwright-report/*

# node_modules 재설치 (필요 시)
cd web-ui && rm -rf node_modules && npm install
```

---

## 2. gateway-api/ (19MB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/gateway-api/` |
| 용량 | 19MB |
| 최종 수정 | 2026-01-17 (활발) |
| 기술 스택 | FastAPI + Python 3.11 |

### 용량 분석

| 디렉토리 | 용량 | 비율 | 설명 |
|----------|------|------|------|
| `results/` | 13MB | 68.4% | 처리 결과물 |
| `htmlcov/` | 3.2MB | 16.8% | 테스트 커버리지 |
| `blueprintflow/` | 732KB | 3.9% | BlueprintFlow 엔진 |
| `tests/` | 388KB | 2.0% | 테스트 코드 |
| `routers/` | 252KB | 1.3% | API 라우터 |
| `utils/` | 208KB | 1.1% | 유틸리티 |
| `api_specs/` | 188KB | 1.0% | OpenAPI 스펙 |
| `services/` | 148KB | 0.8% | 서비스 레이어 |
| `docs/` | 68KB | 0.4% | 문서 |

### 구조

```
gateway-api/
├── results/          # 13MB - 처리 결과 (정리 가능)
├── htmlcov/          # 3.2MB - 커버리지 리포트 (정리 가능)
├── blueprintflow/    # 732KB - 핵심 엔진
│   ├── executors/    # API Executor
│   └── engine/       # 워크플로우 엔진
├── tests/            # 388KB - 테스트 (364개 통과)
├── routers/          # 252KB - API 엔드포인트
├── api_specs/        # 188KB - YAML 스펙
├── services/         # 148KB - 비즈니스 로직
├── utils/            # 208KB - 유틸리티
└── api_server.py     # 메인 서버
```

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ✅ 유지 |
| **사유** | API 게이트웨이. 모든 API 요청 처리 |
| **정리 가능** | results/, htmlcov/ (~16MB) |

### 정리 명령어

```bash
# 처리 결과물 정리
rm -rf gateway-api/results/*
rm -rf gateway-api/htmlcov/
```

---

## 3. models/ (1.8GB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/models/` |
| 용량 | 1.8GB |
| API 서비스 | 20개 |
| 기술 스택 | FastAPI + ML 모델 |

### 용량 분석 (상위 15개)

| 디렉토리 | 용량 | 설명 | 정리 가능 |
|----------|------|------|-----------|
| `yolo-api/` | **1.1GB** | YOLO 객체 검출 | 775MB |
| `edgnet-api/` | 370MB | 엣지 세그멘테이션 | 13MB |
| `edocr2-v2-api/` | 310MB | 한국어 OCR | 24MB |
| `skinmodel-api/` | 6.1MB | 공차 분석 | - |
| `design-checker-api/` | 976KB | 설계 검증 | - |
| `pid-analyzer-api/` | 652KB | P&ID 분석 | - |
| `line-detector-api/` | 372KB | 라인 검출 | - |
| `knowledge-api/` | 196KB | GraphRAG | - |
| `paddleocr-api/` | 180KB | 다국어 OCR | - |
| `vl-api/` | 132KB | Vision-Language | - |
| 기타 10개 | ~500KB | OCR 변형 등 | - |

### yolo-api/ 상세 분석 (1.1GB)

| 디렉토리 | 용량 | 설명 | 상태 |
|----------|------|------|------|
| `uploads/` | 709MB | 업로드 이미지 | ⚠️ 정리 가능 |
| `training/` | 249MB | 학습 데이터 | ⚠️ 정리 가능 |
| `results/` | 66MB | 검출 결과 | ⚠️ 정리 가능 |
| `models/` | 34MB | 모델 웨이트 | ✅ 필수 |
| `소스 코드` | ~250KB | routers, services | ✅ 필수 |

### edgnet-api/ 상세 분석 (370MB)

| 디렉토리 | 용량 | 설명 | 상태 |
|----------|------|------|------|
| `models/` | 356MB | 모델 웨이트 | ✅ 필수 |
| `training/` | 13MB | 학습 데이터 | ⚠️ 정리 가능 |
| `uploads/` | 1.1MB | 업로드 | ⚠️ 정리 가능 |

### edocr2-v2-api/ 상세 분석 (310MB)

| 디렉토리 | 용량 | 설명 | 상태 |
|----------|------|------|------|
| `edocr2_src/` | 151MB | eDOCr2 소스 | ✅ 필수 |
| `models/` | 135MB | 모델 웨이트 | ✅ 필수 |
| `results/` | 23MB | 처리 결과 | ⚠️ 정리 가능 |
| `uploads/` | 1.3MB | 업로드 | ⚠️ 정리 가능 |

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ✅ 유지 |
| **사유** | 20개 AI API 서비스. 프로젝트 핵심 |
| **정리 가능** | uploads, results, training (~800MB) |

### 정리 명령어

```bash
# yolo-api 임시 파일 정리 (775MB 절감)
rm -rf models/yolo-api/uploads/*
rm -rf models/yolo-api/training/*
rm -rf models/yolo-api/results/*

# edgnet-api 정리 (14MB 절감)
rm -rf models/edgnet-api/training/*
rm -rf models/edgnet-api/uploads/*

# edocr2-v2-api 정리 (24MB 절감)
rm -rf models/edocr2-v2-api/results/*
rm -rf models/edocr2-v2-api/uploads/*

# 전체 __pycache__ 정리 (~2MB 절감)
find models/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

---

## 4. blueprint-ai-bom/ (1.2GB)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 경로 | `/home/uproot/ax/poc/blueprint-ai-bom/` |
| 용량 | 1.2GB (표시: 203MB) |
| 버전 | v10.5 |
| 기술 스택 | FastAPI + React + YOLO/Detectron2 |

### 용량 분석

| 디렉토리 | 용량 | 비율 | 설명 |
|----------|------|------|------|
| `models/` | **988MB** | 82.3% | AI 모델 웨이트 |
| `frontend/` | 190MB | 15.8% | React 프론트엔드 |
| `backend/` | 9.4MB | 0.8% | FastAPI 백엔드 |
| `uploads/` | 3MB | 0.3% | 업로드 파일 |
| 기타 | ~10MB | 0.8% | 문서, 스크립트 |

### models/ 상세 분석 (988MB)

| 디렉토리 | 용량 | 내용 |
|----------|------|------|
| `yolo/` | 507MB | YOLO 모델들 |
| ├ `best.pt` | 137MB | 메인 모델 |
| ├ `v11l/` | 131MB | YOLO v11 Large |
| ├ `v8/` | 131MB | YOLO v8 |
| ├ `v11x/` | 110MB | YOLO v11 Extra |
| └ `v11n/` | 5.3MB | YOLO v11 Nano |
| `detectron2/` | 481MB | Detectron2 모델 |
| └ `model_final.pth` | 480MB | 학습된 모델 |

### frontend/ 상세 분석 (190MB)

| 디렉토리 | 용량 | 설명 |
|----------|------|------|
| `node_modules/` | 188MB | npm 패키지 |
| `src/` | 992KB | 소스 코드 |
| `dist/` | 688KB | 빌드 결과 |

### 판정

| 항목 | 판정 |
|------|------|
| **결론** | ✅ 유지 |
| **사유** | Blueprint AI BOM v10.5. Human-in-the-Loop BOM 생성 |
| **정리 가능** | uploads/, results/ (~3MB) |

### 모델 최적화 옵션

1. **선택적 모델 삭제** (필요 시):
   - `v11l/`, `v8/`, `v11x/` 중 미사용 버전 삭제 시 ~370MB 절감
   - 단, 모델 선택 기능 사용 시 유지 필요

2. **Detectron2 대안**:
   - 현재 미사용 시 481MB 절감 가능
   - 단, 레이아웃 분석 기능 사용 시 필수

---

## Phase 1 최종 요약

### 용량 분석

| 상태 | 용량 | 비율 |
|------|------|------|
| ✅ 필수 유지 | 2.5GB | 100% |
| ⚠️ 런타임 아티팩트 | ~830MB | 정리 가능 |

### 정리 가능 용량

| 디렉토리 | 정리 대상 | 용량 |
|----------|-----------|------|
| `web-ui/` | test-results, playwright-report | ~1.5MB |
| `gateway-api/` | results, htmlcov | ~16MB |
| `models/yolo-api/` | uploads, training, results | ~775MB |
| `models/edgnet-api/` | training, uploads | ~14MB |
| `models/edocr2-v2-api/` | results, uploads | ~24MB |
| `blueprint-ai-bom/` | uploads, results | ~3MB |
| **합계** | | **~830MB** |

### 권장사항

1. **즉시 가능** (830MB 절감):
   ```bash
   # 전체 정리 스크립트
   rm -rf web-ui/test-results/* web-ui/playwright-report/*
   rm -rf gateway-api/results/* gateway-api/htmlcov/
   rm -rf models/yolo-api/uploads/* models/yolo-api/training/* models/yolo-api/results/*
   rm -rf models/edgnet-api/training/* models/edgnet-api/uploads/*
   rm -rf models/edocr2-v2-api/results/* models/edocr2-v2-api/uploads/*
   rm -rf blueprint-ai-bom/uploads/* blueprint-ai-bom/results/*
   find models/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
   ```

2. **정기 정리**: 위 명령어를 cron 또는 pre-commit hook으로 자동화

3. **node_modules 최적화**:
   - `npm ci` 사용 권장 (clean install)
   - `npm prune --production` 으로 dev 의존성 제거 가능

---

**다음**: Phase 2 (설정 및 인프라) 조사
