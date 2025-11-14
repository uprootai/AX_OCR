# AX 도면 분석 시스템

**AI 기반 공학 도면 자동 분석 및 견적 생성 시스템**

---

## 🎯 시스템 개요

공학 도면(PDF/JPG)을 업로드하면 AI가 자동으로 치수, 공차, GD&T를 추출하고 제조 견적을 생성하는 마이크로서비스 기반 시스템입니다.

### 핵심 가치

| 기존 방식 | AI 시스템 | 개선 효과 |
|----------|----------|----------|
| 2-3시간 (수작업) | 30초-1분 (자동) | **⚡ 80% 시간 절감** |
| 오류 가능성 높음 | 일관된 90% 정확도 | **✅ 품질 향상** |
| 전문가 필요 | 누구나 사용 가능 | **👥 인력 효율화** |

---

## 🚀 빠른 시작

### 1. 시스템 접속

웹 브라우저에서 다음 주소 접속:
\`\`\`
http://localhost:5173
\`\`\`

### 2. 도면 분석

1. "시작하기" 클릭
2. 도면 파일 업로드 (PDF/JPG/PNG)
3. 분석 옵션 선택
4. "분석 시작" 클릭
5. 결과 확인 ✅

**소요 시간**: Basic 전략 ~30초, EDGNet ~45초

---

## 📚 문서 가이드

전체 문서는 **용도별로 7개 카테고리**로 정리되어 있습니다. 자세한 내용은 **[문서 색인](docs/README.md)** 참조.

### 사용자를 위한 문서

| 문서 | 대상 | 내용 | 링크 |
|------|------|------|------|
| **빠른 시작** | 신규 사용자 | 5분만에 시작하기 | [QUICKSTART.md](QUICKSTART.md) |
| **사용자 가이드** | 일반 사용자 | 완전 사용 가이드 (10분 숙달) | [docs/user/USER_GUIDE.md](docs/user/USER_GUIDE.md) |
| **API 사용 매뉴얼** | API 사용자 | API 엔드포인트 및 사용법 | [docs/user/API_USAGE_MANUAL.md](docs/user/API_USAGE_MANUAL.md) |
| **문제 해결 가이드** | 모든 사용자 | FAQ 및 트러블슈팅 | [docs/user/TROUBLESHOOTING_GUIDE.md](docs/user/TROUBLESHOOTING_GUIDE.md) |
| **한국어 실행 가이드** | 한국 사용자 | 처음부터 끝까지 전체 가이드 | [docs/user/KOREAN_EXECUTION_GUIDE.md](docs/user/KOREAN_EXECUTION_GUIDE.md) |

### 개발자를 위한 문서

| 문서 | 대상 | 내용 | 링크 |
|------|------|------|------|
| **프로젝트 구조** | 개발자/PM | 전체 디렉토리 및 파일 역할 | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) |
| **기여 가이드** | 기여자 | 코드 스타일, PR 규칙 | [docs/developer/CONTRIBUTING.md](docs/developer/CONTRIBUTING.md) |
| **Git 워크플로우** | 개발자 | Git 브랜치 전략 | [docs/developer/GIT_WORKFLOW.md](docs/developer/GIT_WORKFLOW.md) |
| **Claude AI 활용** | 개발자 | AI 활용 개발 가이드 | [docs/developer/CLAUDE_KR.md](docs/developer/CLAUDE_KR.md) |
| **스크립트 가이드** | 개발자 | 테스트/유틸리티 스크립트 사용법 | [scripts/README.md](scripts/README.md) |

### 기술 구현 가이드

| 문서 | 대상 | 내용 | 링크 |
|------|------|------|------|
| **YOLO 구현 가이드** | AI 엔지니어 | YOLOv11 상세 구현 | [docs/technical/yolo/IMPLEMENTATION_GUIDE.md](docs/technical/yolo/IMPLEMENTATION_GUIDE.md) |
| **OCR 배포 가이드** | 엔지니어 | eDOCr v1/v2 배포 | [docs/technical/ocr/EDOCR_V1_V2_DEPLOYMENT.md](docs/technical/ocr/EDOCR_V1_V2_DEPLOYMENT.md) |
| **VLM API 구현** | AI 엔지니어 | Vision Language Model API | [docs/technical/VL_API_IMPLEMENTATION_GUIDE.md](docs/technical/VL_API_IMPLEMENTATION_GUIDE.md) |

### 시스템 아키텍처 및 보고서

| 문서 | 대상 | 내용 | 링크 |
|------|------|------|------|
| **배포 현황** | 운영팀/PM | 현재 배포 상태 | [docs/architecture/DEPLOYMENT_STATUS.md](docs/architecture/DEPLOYMENT_STATUS.md) |
| **구현 현황** | PM | 기능별 구현 진행도 | [docs/architecture/IMPLEMENTATION_STATUS.md](docs/architecture/IMPLEMENTATION_STATUS.md) |
| **최종 종합 보고서** | 관리자 | 프로젝트 완료 보고 | [docs/reports/FINAL_COMPREHENSIVE_REPORT.md](docs/reports/FINAL_COMPREHENSIVE_REPORT.md) |
| **종합 평가 보고서** | 관리자 | 성능 평가 결과 | [docs/reports/COMPREHENSIVE_EVALUATION_REPORT.md](docs/reports/COMPREHENSIVE_EVALUATION_REPORT.md) |

---

## ✅ 현재 상태: Production Ready **95%** 🎉

### 검증 완료 항목

- ✅ EDGNet 모델 통합 (804개 컴포넌트 감지)
- ✅ Enhanced OCR 인프라 (4가지 전략)
- ✅ 모든 API 엔드포인트 작동
- ✅ Web UI 정상 접속
- ✅ 사용자 친화적 문서 완비

### 서비스 포트

| 서비스 | URL | 용도 |
|--------|-----|------|
| **Web UI** | http://localhost:5173 | 사용자 인터페이스 |
| **문서 포털** | http://localhost:5173/docs | 모든 문서 웹 접근 |
| **API 문서** | http://localhost:8000/docs | Swagger 문서 |

---

## 📊 4가지 분석 전략

| 전략 | 속도 | 정확도 | 비용 | 추천 상황 |
|------|------|--------|------|----------|
| **Basic** | ⚡⚡⚡ 23초 | ⭐⭐⭐ 85% | 무료 | 일반 도면 |
| **EDGNet** | ⚡⚡ 45초 | ⭐⭐⭐⭐ 90% | 무료 | 복잡한 도면 |
| **VL** | ⚡ 느림 | ⭐⭐⭐⭐⭐ 95% | 유료 | GD&T 많은 도면 |
| **Hybrid** | ⚡ 느림 | ⭐⭐⭐⭐⭐ 95%+ | 유료 | 중요 프로젝트 |

**💡 추천**: Basic으로 시작 → 필요시 EDGNet

---

## 🛠️ 빠른 명령어

\`\`\`bash
# 시스템 시작
docker-compose up -d

# 서비스 상태 확인
docker ps | grep -E "edocr2|edgnet"

# 헬스 체크
curl http://localhost:5001/api/v1/health

# 로그 확인
docker-compose logs -f
\`\`\`

---

## 📞 문제 해결

| 증상 | 해결책 |
|------|--------|
| 웹페이지 안 열림 | `docker-compose up -d` |
| 분석 느림 | Basic 전략 사용 |
| 결과 이상함 | 도면 품질 확인 (150-300 DPI) |

더 자세한 내용은 [사용자 가이드](USER_GUIDE.md) 또는 [빠른 참조 카드](QUICK_REFERENCE.md)를 참고하세요.

---

## 🆕 2025-11-08 개선사항

### Enhanced 모드 (보안 + 안정성 + 모니터링)

시스템에 다음 기능들이 추가되었습니다:

| 기능 | 설명 | 상태 |
|------|------|------|
| **API 인증** | API 키 기반 인증 시스템 | ✅ 완료 |
| **Rate Limiting** | DoS 공격 방지 (분/시간/일 제한) | ✅ 완료 |
| **Retry Logic** | Exponential backoff 자동 재시도 | ✅ 완료 |
| **Circuit Breaker** | 서비스 장애 시 요청 차단 | ✅ 완료 |
| **Prometheus** | 메트릭 수집 및 모니터링 | ✅ 완료 |
| **Grafana** | 성능 대시보드 | ✅ 완료 |

### Enhanced 모드로 시작하기

```bash
cd /home/uproot/ax/poc

# 1. 환경 설정
cp .env.template .env

# 2. Enhanced 모드로 시작 (Prometheus + Grafana 포함)
docker-compose -f docker-compose.enhanced.yml up -d

# 3. 모니터링 접속
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

### 개선사항 문서

| 문서 | 내용 |
|------|------|
| **[docs/reports/FINAL_COMPREHENSIVE_REPORT.md](docs/reports/FINAL_COMPREHENSIVE_REPORT.md)** | 전체 개선사항 요약 (82점 → 95점) |
| **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** | 프로젝트 구조 및 명령어 가이드 |
| **[QUICKSTART.md](QUICKSTART.md)** | 빠른 시작 가이드 |
| **[scripts/README.md](scripts/README.md)** | 스크립트 및 테스트 가이드 |

### 테스트 및 검증

```bash
# 전체 API 테스트
python3 scripts/test/test_apis.py

# OCR 성능 비교
python3 scripts/test/test_ocr_performance_comparison.py

# CER 계산
python3 scripts/test/test_cer_calculation.py
```

**참고**: 이전 벤치마크 및 데모 스크립트는 `scripts/archive/`에 보관되어 있습니다.

---

**버전**: 3.0 | **업데이트**: 2025-11-08 | **상태**: Production Ready 95% + Enhanced ✅

**빠른 링크**: 🌐 [Web UI](http://localhost:5173) | 📚 [문서](http://localhost:5001/api/v1/docs) | 🔧 [API](http://localhost:8000/docs) | 📊 [Prometheus](http://localhost:9090) | 📈 [Grafana](http://localhost:3000)
