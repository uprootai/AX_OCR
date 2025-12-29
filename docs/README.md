# AX BlueprintFlow Documentation

> 기계 도면 자동 분석 및 제조 견적 생성 시스템 문서
> **최종 업데이트**: 2025-12-28 | **버전**: v10.0

---

## Quick Links

| 목적 | 문서 |
|------|------|
| 시스템 설치 | [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) |
| 문제 해결 | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| API 사용법 | [user/API_USAGE_MANUAL.md](user/API_USAGE_MANUAL.md) |
| 사용자 가이드 | [user/USER_GUIDE.md](user/USER_GUIDE.md) |
| **Blueprint AI BOM** | [blueprint-ai-bom/docs/](../blueprint-ai-bom/docs/README.md) |

---

## Documentation Structure

```
docs/
├── 설치 & 운영
│   ├── INSTALLATION_GUIDE.md     # 시스템 설치
│   ├── DEPLOYMENT_GUIDE.md       # 배포 가이드
│   ├── ADMIN_MANUAL.md           # 관리자 매뉴얼
│   ├── GPU_CONFIGURATION_EXPLAINED.md
│   └── TROUBLESHOOTING.md        # 문제 해결
│
├── 사용자 가이드 (user/)
│   ├── USER_GUIDE.md             # 상세 사용 가이드
│   ├── API_USAGE_MANUAL.md       # API 사용법
│   └── KOREAN_EXECUTION_GUIDE.md # 한국어 실행 가이드
│
├── 개발자 가이드 (developer/)
│   ├── CLAUDE.md                 # Claude Code 가이드
│   ├── API_SPEC_SYSTEM_GUIDE.md  # API 스펙 시스템
│   └── VL_API_SETUP_GUIDE.md     # VL API 설정
│
├── API 레퍼런스 (api/)
│   └── {api}/parameters.md       # 각 API 파라미터 (11개)
│
├── BlueprintFlow (blueprintflow/)
│   ├── README.md                 # BlueprintFlow 개요
│   ├── 04_optimization/          # 최적화 가이드
│   ├── 08_textinput_node_guide.md
│   └── 09_vl_textinput_integration.md
│
├── 기술 문서 (technical/)
│   ├── yolo/QUICKSTART.md        # YOLO 빠른 시작
│   └── ocr/EDOCR_V1_V2_DEPLOYMENT.md
│
├── 배포 가이드 (dockerization/)
│   └── *.md                      # Docker 배포 가이드
│
├── 오픈소스 (opensource/)
│   └── MODEL_DOWNLOAD_INFO.md    # 모델 다운로드 정보
│
├── 연구 논문 (papers/)
│   ├── 01_OCR_Engineering_Drawings.md      # eDOCr v1
│   ├── 02_eDOCr2_Vision_Language_Integration.md  # eDOCr v2
│   ├── 03_Geometric_Tolerance_Additive_Manufacturing.md  # Skin Model
│   └── 04_Graph_Neural_Network_Engineering_Drawings.md   # EDGNet
│
└── 참조 자료 (references/)
    └── *.pdf                     # 프로젝트 관련 PDF
```

---

## API Services (18개) ✅ 전체 정상

| Category | Service | Port | Parameters |
|----------|---------|------|------------|
| Detection | YOLO | 5005 | [yolo/parameters.md](api/yolo/parameters.md) (model_type으로 P&ID 지원) |
| OCR | eDOCr2 | 5002 | [edocr2/parameters.md](api/edocr2/parameters.md) |
| OCR | PaddleOCR | 5006 | [paddleocr/parameters.md](api/paddleocr/parameters.md) |
| OCR | Tesseract | 5008 | [tesseract/parameters.md](api/tesseract/parameters.md) |
| OCR | TrOCR | 5009 | [trocr/parameters.md](api/trocr/parameters.md) |
| OCR | OCR Ensemble | 5011 | [ocr-ensemble/parameters.md](api/ocr-ensemble/parameters.md) |
| OCR | Surya OCR | 5013 | [surya-ocr/parameters.md](api/surya-ocr/parameters.md) |
| OCR | DocTR | 5014 | [doctr/parameters.md](api/doctr/parameters.md) |
| OCR | EasyOCR | 5015 | [easyocr/parameters.md](api/easyocr/parameters.md) |
| Segmentation | EDGNet | 5012 | [edgnet/parameters.md](api/edgnet/parameters.md) |
| Segmentation | Line Detector | 5016 | [line-detector/parameters.md](api/line-detector/parameters.md) |
| Preprocessing | ESRGAN | 5010 | [esrgan/parameters.md](api/esrgan/parameters.md) |
| Analysis | SkinModel | 5003 | [skinmodel/parameters.md](api/skinmodel/parameters.md) |
| Analysis | PID Analyzer | 5018 | [pid-analyzer/parameters.md](api/pid-analyzer/parameters.md) |
| Analysis | Design Checker | 5019 | [design-checker/parameters.md](api/design-checker/parameters.md) |
| Analysis | **Blueprint AI BOM** | 5020 | [blueprint-ai-bom/](../blueprint-ai-bom/docs/README.md) |
| Knowledge | Knowledge | 5007 | [knowledge/parameters.md](api/knowledge/parameters.md) |
| AI | VL | 5004 | [vl/parameters.md](api/vl/parameters.md) |
| Orchestrator | Gateway | 8000 | - |

---

## For Users

1. **시스템 설치**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
2. **사용 방법**: [user/USER_GUIDE.md](user/USER_GUIDE.md)
3. **API 호출**: [user/API_USAGE_MANUAL.md](user/API_USAGE_MANUAL.md)
4. **문제 해결**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## For Developers

1. **API 스펙 시스템**: [developer/API_SPEC_SYSTEM_GUIDE.md](developer/API_SPEC_SYSTEM_GUIDE.md)
2. **새 API 추가**: `python scripts/create_api.py <api-id> --port <port>`
3. **Claude Code 가이드**: [developer/CLAUDE.md](developer/CLAUDE.md)
4. **VL API 설정**: [developer/VL_API_SETUP_GUIDE.md](developer/VL_API_SETUP_GUIDE.md)

---

## BlueprintFlow

Visual workflow builder for API composition.

- [Overview](blueprintflow/README.md)
- [Optimization Guide](blueprintflow/04_optimization/optimization_guide.md)
- [TextInput Node](blueprintflow/08_textinput_node_guide.md)
- [VL Integration](blueprintflow/09_vl_textinput_integration.md)

---

## Archived Documents

내부 보고서, deprecated 문서는 `archive/` 폴더에 있습니다.

```
archive/
├── internal-reports/   # 내부 분석/평가 보고서
└── deprecated/         # 더 이상 사용하지 않는 문서
```

---

**Last Updated**: 2025-12-24
**Managed By**: Claude Code (Opus 4.5)
