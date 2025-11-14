# 📚 문서 색인 (Documentation Index)

> **AX 실증산단 프로젝트 - 전체 문서 가이드**
>
> 최종 업데이트: 2025-11-12

---

## 🎯 **문서 구조 개요**

모든 프로젝트 문서는 **용도별로 7개 카테고리**로 분류되어 있습니다.

```
docs/
├── 📖 user/           # 사용자를 위한 가이드
├── 👨‍💻 developer/      # 개발자를 위한 가이드
├── 🔧 technical/      # 기술 구현 가이드
├── 🏗️ architecture/   # 시스템 아키텍처 & 분석
├── 📋 reports/        # 최종 보고서
├── 📦 archive/        # 과거 완료된 문서
└── 🔓 opensource/     # 오픈소스 관련
```

---

## 📖 **user/ - 사용자 가이드**

> 시스템 사용법, API 활용법, 문제 해결

| 문서 | 설명 | 대상 |
|------|------|------|
| [USER_GUIDE.md](user/USER_GUIDE.md) | 상세 사용자 매뉴얼 | 일반 사용자 |
| [API_USAGE_MANUAL.md](user/API_USAGE_MANUAL.md) | API 엔드포인트 및 사용법 | API 사용자 |
| [TROUBLESHOOTING_GUIDE.md](user/TROUBLESHOOTING_GUIDE.md) | 문제 해결 가이드 (FAQ) | 모든 사용자 |
| [KOREAN_EXECUTION_GUIDE.md](user/KOREAN_EXECUTION_GUIDE.md) | 한국어 실행 가이드 | 한국 사용자 |

---

## 👨‍💻 **developer/ - 개발자 가이드**

> 기여 방법, Git 워크플로우, AI 활용

| 문서 | 설명 | 대상 |
|------|------|------|
| [CLAUDE.md](developer/CLAUDE.md) | Claude AI 활용 가이드 (English) | 개발자 |
| [CLAUDE_KR.md](developer/CLAUDE_KR.md) | Claude AI 활용 가이드 (한국어) | 한국 개발자 |
| [CONTRIBUTING.md](developer/CONTRIBUTING.md) | 기여 가이드 (코드 스타일, PR 규칙) | 기여자 |
| [GIT_WORKFLOW.md](developer/GIT_WORKFLOW.md) | Git 브랜치 전략 & 워크플로우 | 개발자 |

---

## 🔧 **technical/ - 기술 구현 가이드**

> 각 AI 모듈의 구현 방법, 배포 가이드

### **📁 yolo/ - YOLO 객체 검출**

| 문서 | 설명 |
|------|------|
| [IMPLEMENTATION_GUIDE.md](technical/yolo/IMPLEMENTATION_GUIDE.md) | YOLOv11 상세 구현 가이드 |
| [QUICKSTART.md](technical/yolo/QUICKSTART.md) | YOLO 빠른 시작 (5분) |

### **📁 ocr/ - OCR 엔진**

| 문서 | 설명 |
|------|------|
| [EDOCR_V1_V2_DEPLOYMENT.md](technical/ocr/EDOCR_V1_V2_DEPLOYMENT.md) | eDOCr v1/v2 배포 가이드 |
| [OCR_IMPROVEMENT_STRATEGY.md](technical/ocr/OCR_IMPROVEMENT_STRATEGY.md) | OCR 성능 개선 전략 (멀티 모델 파이프라인) |

### **🔧 기타 기술 가이드**

| 문서 | 설명 |
|------|------|
| [VL_API_IMPLEMENTATION_GUIDE.md](technical/VL_API_IMPLEMENTATION_GUIDE.md) | Vision Language Model API 구현 |
| [SYNTHETIC_DATA_STRATEGY.md](technical/SYNTHETIC_DATA_STRATEGY.md) | 합성 데이터 생성 전략 |

---

## 🏗️ **architecture/ - 아키텍처 & 분석**

> 시스템 구조, 배포 현황, 프로덕션 준비도

| 문서 | 설명 | 용도 |
|------|------|------|
| [PROJECT_STRUCTURE_ANALYSIS.md](architecture/PROJECT_STRUCTURE_ANALYSIS.md) | 프로젝트 구조 상세 분석 | 온보딩, 구조 이해 |
| [DEPLOYMENT_STATUS.md](architecture/DEPLOYMENT_STATUS.md) | 현재 배포 상태 | 운영 관리 |
| [PRODUCTION_READINESS_ANALYSIS.md](architecture/PRODUCTION_READINESS_ANALYSIS.md) | 프로덕션 준비도 평가 | 배포 전 체크리스트 |
| [IMPLEMENTATION_STATUS.md](architecture/IMPLEMENTATION_STATUS.md) | 구현 진행 현황 | 프로젝트 관리 |
| [DECISION_MATRIX.md](architecture/DECISION_MATRIX.md) | 기술 의사결정 기록 | 아키텍처 결정 참고 |

---

## 📋 **reports/ - 최종 보고서**

> 프로젝트 종합 보고서, 평가 결과

| 문서 | 설명 | 용도 |
|------|------|------|
| [FINAL_COMPREHENSIVE_REPORT.md](reports/FINAL_COMPREHENSIVE_REPORT.md) | 최종 종합 보고서 (전체 구현 요약) | 프로젝트 완료 보고 |
| [COMPREHENSIVE_EVALUATION_REPORT.md](reports/COMPREHENSIVE_EVALUATION_REPORT.md) | 종합 평가 보고서 (성능 평가) | 성과 분석 |

---

## 📦 **archive/ - 과거 완료 문서**

> 완료된 작업 기록, 과거 이슈 분석 (참고용)

| 문서 | 설명 | 완료 시점 |
|------|------|-----------|
| [ANALYZE_ISSUE_REPORT.md](archive/ANALYZE_ISSUE_REPORT.md) | 이슈 분석 보고서 | 과거 |
| [BBOX_VERIFICATION_REPORT.md](archive/BBOX_VERIFICATION_REPORT.md) | BBox 검증 보고서 | 완료 |
| [BBOX_INDEX_MISMATCH_FIX.md](archive/BBOX_INDEX_MISMATCH_FIX.md) | BBox 인덱스 불일치 수정 기록 | 완료 |
| [OCR_TEST_CONCLUSION.md](archive/OCR_TEST_CONCLUSION.md) | OCR 테스트 결론 | 완료 |
| [PAPER_IMPLEMENTATION_GAP_ANALYSIS.md](archive/PAPER_IMPLEMENTATION_GAP_ANALYSIS.md) | 논문 대비 구현 갭 분석 | 초기 분석 |
| [PERFORMANCE_VALIDATION_REPORT.md](archive/PERFORMANCE_VALIDATION_REPORT.md) | 성능 검증 보고서 | 완료 |
| [FINAL_USER_VALIDATION.md](archive/FINAL_USER_VALIDATION.md) | 최종 사용자 검증 | 완료 |
| [FINAL_VALIDATION_RESULT.md](archive/FINAL_VALIDATION_RESULT.md) | 최종 검증 결과 | 완료 |
| [EDGNET_INTEGRATION_COMPLETE.md](archive/EDGNET_INTEGRATION_COMPLETE.md) | EDGNet 통합 완료 기록 | 완료 |
| [WEB_UI_PLANNING.md](archive/WEB_UI_PLANNING.md) | Web UI 기획 문서 | 초기 기획 |
| [WEB_UI_STATUS.md](archive/WEB_UI_STATUS.md) | Web UI 개발 현황 | 과거 |
| [WEB_UI_DEBUGGING_SPEC.md](archive/WEB_UI_DEBUGGING_SPEC.md) | Web UI 디버깅 명세 | 완료 |

---

## 🔓 **opensource/ - 오픈소스 관련**

> eDOCr2 등 오픈소스 모델 관련 문서

| 문서 | 설명 |
|------|------|
| [README.md](opensource/README.md) | 오픈소스 개요 |
| [COMPARISON_REPORT.md](opensource/COMPARISON_REPORT.md) | 모델 비교 보고서 |
| [MODEL_DOWNLOAD_INFO.md](opensource/MODEL_DOWNLOAD_INFO.md) | 모델 다운로드 정보 |
| [PROGRESS_REPORT.md](opensource/PROGRESS_REPORT.md) | 진행 상황 보고 |
| [SOLUTION.md](opensource/SOLUTION.md) | 솔루션 설명 |

---

## 🚀 **빠른 시작 - 어떤 문서를 읽어야 할까?**

### **처음 시작하는 사용자**
1. [../README.md](../README.md) - 프로젝트 소개
2. [../QUICKSTART.md](../QUICKSTART.md) - 5분 빠른 시작
3. [user/USER_GUIDE.md](user/USER_GUIDE.md) - 상세 사용법

### **API 사용하려는 개발자**
1. [user/API_USAGE_MANUAL.md](user/API_USAGE_MANUAL.md) - API 사용법
2. [developer/CLAUDE_KR.md](developer/CLAUDE_KR.md) - AI 활용 가이드
3. [user/TROUBLESHOOTING_GUIDE.md](user/TROUBLESHOOTING_GUIDE.md) - 문제 해결

### **코드 기여하려는 개발자**
1. [developer/CONTRIBUTING.md](developer/CONTRIBUTING.md) - 기여 가이드
2. [developer/GIT_WORKFLOW.md](developer/GIT_WORKFLOW.md) - Git 워크플로우
3. [architecture/PROJECT_STRUCTURE_ANALYSIS.md](architecture/PROJECT_STRUCTURE_ANALYSIS.md) - 구조 분석

### **특정 기술 구현하려는 개발자**
- **YOLO**: [technical/yolo/IMPLEMENTATION_GUIDE.md](technical/yolo/IMPLEMENTATION_GUIDE.md)
- **OCR**: [technical/ocr/EDOCR_V1_V2_DEPLOYMENT.md](technical/ocr/EDOCR_V1_V2_DEPLOYMENT.md)
- **VLM**: [technical/VL_API_IMPLEMENTATION_GUIDE.md](technical/VL_API_IMPLEMENTATION_GUIDE.md)

### **프로젝트 관리자 / PM**
1. [architecture/IMPLEMENTATION_STATUS.md](architecture/IMPLEMENTATION_STATUS.md) - 구현 현황
2. [architecture/DEPLOYMENT_STATUS.md](architecture/DEPLOYMENT_STATUS.md) - 배포 현황
3. [reports/FINAL_COMPREHENSIVE_REPORT.md](reports/FINAL_COMPREHENSIVE_REPORT.md) - 최종 보고서

---

## 📝 **문서 업데이트 가이드**

### **문서 작성 규칙**

1. **Markdown 형식** 사용
2. **한글 우선**, 필요시 영문 병기
3. **코드 블록**은 언어 명시 (```python, ```bash)
4. **이미지**는 상대 경로 사용
5. **링크**는 상대 경로로 (예: `[문서](../user/USER_GUIDE.md)`)

### **문서 카테고리 선택 기준**

| 카테고리 | 대상 독자 | 내용 유형 |
|----------|-----------|-----------|
| user/ | 일반 사용자, API 사용자 | 사용법, FAQ, 튜토리얼 |
| developer/ | 코드 기여자 | 개발 환경, Git, 코딩 규칙 |
| technical/ | 기술 구현자 | AI 모델, 배포, 성능 최적화 |
| architecture/ | 시스템 설계자, PM | 구조, 의사결정, 배포 현황 |
| reports/ | 관리자, 의사결정자 | 종합 보고서, 평가 결과 |
| archive/ | 참고용 | 완료된 작업, 과거 이슈 |

### **새 문서 추가 시**

1. 적절한 카테고리 선택
2. 파일명: `대문자_언더스코어.md` (예: `NEW_FEATURE_GUIDE.md`)
3. 이 `docs/README.md`에 링크 추가
4. 프로젝트 루트 `README.md`에도 필요시 링크

---

## 🔍 **문서 검색 팁**

### **키워드별 문서 찾기**

- **배포**: `DEPLOYMENT_STATUS.md`, `EDOCR_V1_V2_DEPLOYMENT.md`, `PRODUCTION_READINESS_ANALYSIS.md`
- **성능 개선**: `OCR_IMPROVEMENT_STRATEGY.md`, `COMPREHENSIVE_EVALUATION_REPORT.md`
- **API 사용**: `API_USAGE_MANUAL.md`, `CLAUDE_KR.md`
- **문제 해결**: `TROUBLESHOOTING_GUIDE.md`, `ANALYZE_ISSUE_REPORT.md` (archive)
- **기여 방법**: `CONTRIBUTING.md`, `GIT_WORKFLOW.md`
- **YOLO**: `technical/yolo/*`
- **OCR**: `technical/ocr/*`
- **아키텍처**: `architecture/*`

---

## 📞 **피드백 & 문의**

- 문서 오류 발견 시: [GitHub Issues](링크 추가 필요)
- 문서 추가 요청: [CONTRIBUTING.md](developer/CONTRIBUTING.md)
- 문서 구조 개선 제안: 프로젝트 관리자에게 문의

---

**최종 업데이트**: 2025-11-12
**작성자**: Claude Code
**버전**: v2.0
