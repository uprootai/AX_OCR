---
paths:
  - "models/**"
  - "gateway-api/**"
  - "docker-compose*.yml"
---

# API 서비스 (21개)

| 카테고리 | 서비스 | 포트 | 용도 |
|----------|--------|------|------|
| **Detection** | YOLO | 5005 | 객체 검출 |
| **Detection** | Table Detector | 5022 | 테이블 검출 및 추출 |
| **OCR** | eDOCr2 | 5002 | 한국어 치수 인식 |
| **OCR** | PaddleOCR | 5006 | 다국어 OCR |
| **OCR** | Tesseract | 5008 | 문서 OCR |
| **OCR** | TrOCR | 5009 | 필기체 OCR |
| **OCR** | OCR Ensemble | 5011 | 4엔진 가중 투표 |
| **OCR** | Surya OCR | 5013 | 90+ 언어 |
| **OCR** | DocTR | 5014 | 2단계 파이프라인 |
| **OCR** | EasyOCR | 5015 | 80+ 언어 |
| **Segmentation** | EDGNet | 5012 | 엣지 세그멘테이션 |
| **Segmentation** | Line Detector | 5016 | P&ID 라인 검출 |
| **Preprocessing** | ESRGAN | 5010 | 4x 업스케일링 |
| **Analysis** | SkinModel | 5003 | 공차 분석 |
| **Analysis** | PID Analyzer | 5018 | P&ID 연결 분석 |
| **Analysis** | Design Checker | 5019 | P&ID 설계 검증 |
| **Analysis** | Blueprint AI BOM | 5020 | Human-in-the-Loop BOM |
| **Visualization** | PID Composer | 5021 | SVG 오버레이 |
| **Knowledge** | Knowledge | 5007 | Neo4j + GraphRAG |
| **AI** | VL | 5004 | Vision-Language |
| **Orchestrator** | Gateway | 8000 | 파이프라인 조정 |

## 핵심 파일 위치

### 백엔드 (gateway-api/)

| 목적 | 파일 경로 |
|------|----------|
| **API 서버** | `api_server.py` |
| **API 스펙** | `api_specs/*.yaml` |
| **Executor 레지스트리** | `blueprintflow/executors/executor_registry.py` |
| **서비스 레이어** | `services/yolo_service.py`, `services/edocr2_service.py` |

### API 소스코드 (models/)

| 목적 | 파일 경로 |
|------|----------|
| **YOLO API** | `models/yolo-api/api_server.py` |
| **eDOCr2 API** | `models/edocr2-v2-api/api_server.py` |
| **기타 API** | `models/{api-id}-api/api_server.py` |
| **스캐폴딩** | `scripts/create_api.py` |

## 주의 사항

- **confidence_threshold**: 기본값 0.4 사용 (0.5 아님)
- **Docker 서비스명**: `blueprint-ai-bom-backend` (backend 아님)
- **Gateway 헬스체크**: `/api/v1/health` (루트 아님)
