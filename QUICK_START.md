# Quick Start Guide

**5분 안에 프로젝트 파악하기** | 최종 업데이트: 2025-12-26

---

## What Is This?

**기계 도면 자동 분석 및 제조 견적 생성 시스템**

```
도면 이미지 → YOLO 검출 → OCR 추출 → 공차 분석 → 자동 견적서
```

---

## Architecture (30초 이해)

```
Web UI (React 19) → Gateway API → [ 19개 AI API 서비스 ]
     :5173              :8000         :5002-5020
```

**BlueprintFlow**: 비주얼 워크플로우 빌더 (http://localhost:5173/blueprintflow)
**Blueprint AI BOM**: Human-in-the-Loop BOM 생성 (http://localhost:3000)

---

## API Services (20개)

| 카테고리 | 서비스 | 포트 | 용도 |
|----------|--------|------|------|
| **Orchestrator** | Gateway | 8000 | API 오케스트레이터 |
| **Detection** | YOLO | 5005 | 14가지 심볼 검출 |
| **Detection** | YOLO-PID | 5017 | P&ID 60종 심볼 |
| **OCR** | eDOCr2 | 5002 | 한국어 치수 |
| **OCR** | PaddleOCR | 5006 | 다국어 OCR |
| **OCR** | Tesseract | 5008 | 문서 OCR |
| **OCR** | TrOCR | 5009 | 필기체 OCR |
| **OCR** | OCR Ensemble | 5011 | 4엔진 가중투표 |
| **OCR** | Surya OCR | 5013 | 90+ 언어 |
| **OCR** | DocTR | 5014 | 2단계 파이프라인 |
| **OCR** | EasyOCR | 5015 | CPU 친화적 |
| **Segmentation** | EDGNet | 5012 | 엣지 세그멘테이션 |
| **Segmentation** | Line Detector | 5016 | P&ID 라인 |
| **Preprocessing** | ESRGAN | 5010 | 4x 업스케일링 |
| **Analysis** | SkinModel | 5003 | 공차 분석 |
| **Analysis** | PID Analyzer | 5018 | P&ID BOM |
| **Analysis** | Design Checker | 5019 | 설계 검증 |
| **Analysis** | Blueprint AI BOM | 5020 | 도면 BOM |
| **Knowledge** | Knowledge | 5007 | GraphRAG |
| **AI** | VL | 5004 | Vision-Language |

---

## Quick Commands

```bash
# 서비스 시작
docker-compose up -d

# 상태 확인
curl http://localhost:8000/api/v1/health

# 로그 확인
docker logs gateway-api -f

# 개발 서버 (프론트엔드)
cd web-ui && npm run dev
```

---

## GPU 설정 (선택)

GPU 설정은 `docker-compose.override.yml`에서 관리합니다.

```bash
# 템플릿 복사
cp docker-compose.override.yml.example docker-compose.override.yml

# 서비스 재시작
docker-compose up -d
```

또는 Dashboard (http://localhost:5173/admin/api/{api-id})에서 실시간 설정 가능.

---

## Project Structure

```
/home/uproot/ax/poc/
├── gateway-api/           # Gateway API (Port 8000)
├── web-ui/                # React 프론트엔드 (Port 5173)
├── blueprint-ai-bom/      # Blueprint AI BOM (Port 3000, 5020)
└── models/                # 개별 AI API 서비스들
    ├── yolo-api/
    ├── edocr2-v2-api/
    └── ...
```

---

## Documentation

| 문서 | 내용 |
|------|------|
| [CLAUDE.md](CLAUDE.md) | 프로젝트 가이드 (LLM 최적화) |
| [KNOWN_ISSUES.md](KNOWN_ISSUES.md) | 알려진 이슈 |
| [docs/](docs/) | 상세 문서 |

---

## Having Issues?

1. `docker-compose ps` - 컨테이너 상태 확인
2. `docker logs <service>` - 로그 확인
3. [KNOWN_ISSUES.md](KNOWN_ISSUES.md) - 알려진 이슈 확인

---

**Version**: 14.0 | **Managed By**: Claude Code
