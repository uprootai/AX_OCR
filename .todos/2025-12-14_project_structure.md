# AX POC 프로젝트 구조 정리

> **작성일**: 2025-12-14
> **목적**: 프로젝트 전체 구조 한눈에 파악

---

## 프로젝트 개요

**기계 도면 자동 분석 및 제조 견적 생성 시스템**

```
도면 이미지 → YOLO 검출 → OCR 추출 → 공차 분석 → 견적 PDF
```

| 항목 | 값 |
|------|-----|
| 기술 스택 | FastAPI + React 19 + YOLO v11 + eDOCr2 + Docker |
| 프론트엔드 | http://localhost:5173 |
| 백엔드 | http://localhost:8000 |
| API 서비스 | 19개 (포트 5002~5019) |

---

## 디렉토리 구조

```
/home/uproot/ax/poc/
├── web-ui/                    # 프론트엔드 (React 19 + Vite)
├── gateway-api/               # 백엔드 (FastAPI)
├── models/                    # API 마이크로서비스 (19개)
├── scripts/                   # 유틸리티 스크립트 (27개)
├── docs/                      # 문서 (40+ 파일)
├── monitoring/                # Prometheus + Grafana
├── .claude/                   # Claude Code 설정
├── .github/                   # CI/CD 워크플로우
├── .todos/                    # 작업 추적
├── docker-compose.yml         # 메인 오케스트레이션
├── docker-compose.override.yml # GPU/CPU 설정
└── CLAUDE.md                  # 프로젝트 가이드 (메인 참조)
```

---

## 프론트엔드 (web-ui/)

| 목적 | 경로 |
|------|------|
| API 레지스트리 | `src/config/apiRegistry.ts` |
| 노드 정의 | `src/config/nodeDefinitions.ts` |
| BlueprintFlow 빌더 | `src/pages/blueprintflow/BlueprintFlowBuilder.tsx` |
| API 모니터링 | `src/components/monitoring/APIStatusMonitor.tsx` |
| 상태 관리 | `src/store/workflowStore.ts`, `apiConfigStore.ts` |
| 번역 | `src/locales/ko.json`, `en.json` |
| 테스트 | `npm run test:run` (31개 통과) |

### 주요 페이지
- **Landing**: 랜딩 페이지
- **Dashboard**: 메인 대시보드
- **BlueprintFlow**: 워크플로우 빌더
- **Admin**: API 설정 및 GPU 관리
- **Docs**: 문서 뷰어

---

## 백엔드 (gateway-api/)

| 목적 | 경로 |
|------|------|
| API 서버 | `api_server.py` |
| Executor 레지스트리 | `blueprintflow/executors/executor_registry.py` |
| API 스펙 (20개) | `api_specs/*.yaml` |
| 서비스 레이어 | `services/*.py` |
| 테스트 | `tests/*.py` (9개) |

### Executor 종류 (30개)
- **Input**: ImageInput, TextInput
- **Detection**: YOLO, YOLO-PID
- **OCR**: eDOCr2, PaddleOCR, Tesseract, TrOCR, Surya, DocTR, EasyOCR, Ensemble
- **Segmentation**: EDGNet, LineDetector
- **Analysis**: SkinModel, PIDAnalyzer, DesignChecker
- **Control**: IF, Loop, Merge

---

## API 서비스 (models/)

| 카테고리 | 서비스 | 포트 |
|----------|--------|------|
| Detection | YOLO | 5005 |
| Detection | YOLO-PID | 5017 |
| OCR | eDOCr2 | 5002 |
| OCR | PaddleOCR | 5006 |
| OCR | Tesseract | 5008 |
| OCR | TrOCR | 5009 |
| OCR | OCR Ensemble | 5011 |
| OCR | Surya OCR | 5013 |
| OCR | DocTR | 5014 |
| OCR | EasyOCR | 5015 |
| Segmentation | EDGNet | 5012 |
| Segmentation | Line Detector | 5016 |
| Preprocessing | ESRGAN | 5010 |
| Analysis | SkinModel | 5003 |
| Analysis | PID Analyzer | 5018 |
| Analysis | Design Checker | 5019 |
| Knowledge | Knowledge | 5007 |
| AI | VL | 5004 |

### 각 API 구조
```
{service-api}/
├── api_server.py         # FastAPI 애플리케이션
├── requirements.txt      # 의존성
├── Dockerfile           # 컨테이너 설정
├── models/              # 학습된 모델
└── services/            # 비즈니스 로직
```

---

## 스크립트 (scripts/)

| 분류 | 주요 파일 |
|------|----------|
| API 생성 | `create_api.py` (자동 스캐폴딩) |
| 모델 학습 | `train_yolo.py`, `train_edgnet_*.py` |
| 데이터 준비 | `prepare_dataset.py`, `merge_datasets.py` |
| 배포 | `deployment/deploy.sh`, `bundle_models.sh` |

---

## 문서 (docs/)

```
docs/
├── api/                 # API별 문서
├── blueprintflow/       # BlueprintFlow 가이드
├── papers/              # 참조 논문 (17개)
├── insights/            # 벤치마크, 최적화 기록
├── technical/           # 아키텍처 문서
└── developer/           # 개발자 가이드
```

---

## 개발 명령어

```bash
# 프론트엔드
cd web-ui && npm run dev         # 개발 서버
cd web-ui && npm run build       # 프로덕션 빌드
cd web-ui && npm run test:run    # 테스트 실행

# 백엔드
cd gateway-api && pytest tests/ -v

# Docker
docker-compose up -d             # 전체 시작
docker logs gateway-api -f       # 로그 확인
```

---

## 주요 설정 파일

| 파일 | 용도 |
|------|------|
| `docker-compose.yml` | 19개 서비스 오케스트레이션 |
| `docker-compose.override.yml` | GPU/메모리 설정 (웹에서 수정 가능) |
| `docker-compose.monitoring.yml` | Prometheus + Grafana |
| `.github/workflows/ci.yml` | CI/CD 파이프라인 |

---

## 통계 요약

| 항목 | 수량 |
|------|------|
| API 마이크로서비스 | 19개 |
| 프론트엔드 소스 파일 | 87개 (.ts/.tsx) |
| 백엔드 소스 파일 | 84개 (.py) |
| Executor 타입 | 30개 |
| API 스펙 (YAML) | 20개 |
| 문서 | 40+ 개 |
| 스크립트 | 27개 |

---

## 참고 문서

- **메인 가이드**: `/home/uproot/ax/poc/CLAUDE.md`
- **아키텍처**: `/home/uproot/ax/poc/ARCHITECTURE.md`
- **배포 가이드**: `/home/uproot/ax/poc/DEPLOYMENT_GUIDE.md`
- **빠른 시작**: `/home/uproot/ax/poc/QUICK_START.md`
