# Claude Development Guidelines for Drawing BOM Extractor

## 프로젝트 개요
이 프로젝트는 YOLOv8 딥러닝 모델을 활용하여 CAD/PDF 도면에서 산업 부품을 자동 인식하고 BOM을 생성하는 시스템입니다.

## OCR 서비스 아키텍처 (2025-01-20 최적화)

### 단일 PaddleOCR API
- **포트**: 8001
- **성능**: 멀티모달 LLM 기준 90% 유사도 달성
- **특징**: 스케일링 불필요, CPU 모드 최적화
- **제거된 구성요소**: EasyOCR API (10% 성능), Scaler API (불필요)

### OCR 서비스 명령어
```bash
# OCR 서비스 시작
cd restapi && docker-compose up -d

# OCR 테스트
python3 test_paddleocr_only.py

# 서비스 상태 확인
curl http://localhost:8001/health
```

## 중요 개발 지침

### 1. Playwright 테스트 관련 (필수)
**⚠️ 매우 중요: Playwright 테스트 시 절대 .py 파일을 생성하지 마세요!**

- ❌ **하지 말아야 할 것**: `test_playwright.py` 같은 Python 파일 생성
- ✅ **반드시 해야 할 것**: MCP Playwright 도구 사용

```bash
# 올바른 예시:
# MCP Playwright 도구를 직접 사용하여 테스트
# Claude는 내장된 MCP Playwright 기능을 활용해야 합니다

# 잘못된 예시:
# python test_playwright.py (X)
# pytest test_*.py (X)
```

### 2. 프로젝트 구조
```
DrawingBOMExtractor/
├── real_ai_app.py          # 메인 Streamlit 애플리케이션
├── model/                   # YOLO 모델 파일
│   └── best.pt             # 학습된 YOLOv8 모델
├── test_drawings/          # 테스트용 도면 이미지
├── classes_info_with_pricing.json  # 부품 가격 정보
├── restapi/                # OCR API 서비스
│   ├── docker-compose.yml  # PaddleOCR 단독 서비스
│   ├── paddleocr/          # PaddleOCR API
│   └── README.md           # OCR 서비스 문서
├── class_examples/         # CAD 심볼 테스트 이미지
├── ocr_performance_report_ko.md  # OCR 성능 분석 보고서
└── test_paddleocr_only.py  # PaddleOCR 단독 테스트
```

### 3. 핵심 기능
1. **AI 심볼 인식**: YOLOv8 모델로 27가지 산업 부품 검출
2. **심볼 검증**: 개별/일괄 승인, 거부, 수정 기능
3. **BOM 생성**: 검출된 부품으로 자재명세서 자동 생성
4. **견적 산출**: 부품별 가격 정보 기반 견적서 생성
5. **Excel 내보내기**: BOM을 Excel 형식으로 저장

### 4. 테스트 체크리스트
웹 인터페이스 테스트 시 확인해야 할 사항:
- [ ] 파일 업로드 기능 (PDF/이미지)
- [ ] AI 검출 실행 및 결과 표시
- [ ] 심볼 개별 승인/거부/수정
- [ ] 심볼 일괄 승인/거부
- [ ] 수동 편집 기능
- [ ] BOM 테이블 생성
- [ ] Excel 다운로드
- [ ] 가격 계산 및 견적서

### 5. Docker 실행
```bash
# Docker 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 웹 접속
http://localhost:8501
```

### 6. 개발 시 주의사항
- 모든 경로는 Docker 컨테이너 내부 경로 기준 (/app/)
- GPU 사용 가능 시 자동 감지하여 활용
- 테스트 시 test_drawings/ 폴더의 샘플 이미지 활용
- 심볼 검증 기능은 탭 3번째에 위치

### 7. 린트 및 타입체크 명령어
```bash
# Python 코드 품질 검사
ruff check real_ai_app.py
pylint real_ai_app.py

# 타입 체크 (mypy가 설치된 경우)
mypy real_ai_app.py
```

## 문의사항
기술적 문의나 버그 리포트는 프로젝트 관리자에게 연락하세요.