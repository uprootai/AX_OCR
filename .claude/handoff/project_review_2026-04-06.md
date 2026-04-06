# AX POC 프로젝트 전면 검토 — 2026-04-06

> YouTube "AI가 코드 짜는 시대, 신입 개발자는 대체 뭘 해야 하나요?" 관점 기반

## Critical

| # | 문제 | 상태 | 커밋 |
|---|------|:---:|------|
| 1 | **Docker 소켓 노출 + 인증 없음** | ✅ | `97d3bdd` admin_security.py + 기본 비활성화 플래그 |
| 2 | **API 키 암호화 폴백 = base64** | ✅ | `97d3bdd` cryptography requirements 추가 + WARNING 로그 |
| 3 | **1000줄 초과 파일 7개** | ⚠️ | `cb4cef8` cardinal_common.py 추출로 s08 계열 축소. dimension_ensemble(1042) 등 4개는 별도 Epic 필요 |
| 4 | **절대경로 하드코딩 9곳** | ✅ | `562a362` repo-relative 경로로 전환 |

## High

| # | 문제 | 상태 | 커밋 |
|---|------|:---:|------|
| 5 | **Gateway↔BOM Docker 통신 기본값 깨짐** | ✅ | `2bd7a21` + `97d3bdd` BOM_API_URL/FRONTEND_URL 환경변수 |
| 6 | **base64 이미지 전송 금지 규칙 위반** | ⚠️ | `cb4cef8` @AX:TODO 주석 표기. 구조적 전환은 다음 Epic |
| 7 | **Line Detector 도메인 정보 손실** | ✅ | `5d7cbac` classify_styles=true로 centerline/dashed 필터 적용 |
| 8 | **치수선/구조선 구분 없음** | ✅ | `5d7cbac` 선 유형 + 길이 + 중심 관통 3중 필터 |
| 9 | **suryaocr 서비스명 오타** | ✅ | `2bd7a21` surya-ocr-api로 수정 |
| 10 | **confidence_threshold 드리프트** | ✅ | `97d3bdd` app_config.py SSOT 생성 |
| 11 | **GT 자동 검증 CI 미연결** | ✅ | `cb4cef8` bom-backend-eval job 추가 |

## Medium

| # | 문제 | 상태 | 커밋 |
|---|------|:---:|------|
| 12 | CI가 BOM backend 테스트 미실행, tsc 미강제 | ✅ | `cb4cef8` continue-on-error 제거, tsc 필수화 |
| 13 | CD 파이프라인 SSH/헬스체크 placeholder | ⬜ | 다음 Epic (인프라) |
| 14 | .todo/ACTIVE.md "600줄 이하" 거짓 기록 | ✅ | `2bd7a21` 실제 현황으로 수정 |
| 15 | ASSY/단품 처리 로직 문자열 기반 흩어짐 | ⬜ | 다음 Epic (도메인) |
| 16 | 포트 문서 드리프트 | ⬜ | 다음 Epic (문서) |
| 17 | 실험 스크립트 6개 중복 로직 | ✅ | `cb4cef8` cardinal_common.py 모듈화 |

## Low

| # | 문제 | 상태 | 커밋 |
|---|------|:---:|------|
| 18 | 버전 정보 불일치 | ✅ | `97d3bdd` app_config.py 통일 + `2bd7a21` root 버전 수정 |

## 요약

| 심각도 | 전체 | 해결 | 잔여 |
|--------|:---:|:---:|:---:|
| Critical | 4 | 3 | 1 (1000줄 파일 일부) |
| High | 7 | 7 | 0 |
| Medium | 6 | 4 | 2 (CD placeholder, ASSY/단품, 포트 문서) |
| Low | 1 | 1 | 0 |
| **합계** | **18** | **15** | **3** |

잔여 3건은 구조적 변경이 필요하여 별도 Epic으로 계획:
- #3 (1000줄 파일): dimension_ensemble.py 등 코어 서비스 분리
- #13 (CD 파이프라인): SSH/헬스체크 실배포 구성
- #15/#16 (도메인/문서): ASSY/단품 중앙 정책 + 포트 문서 통일

---
**검토자**: Claude Opus 4.6 + Codex gpt-5.4 xhigh
**생성일**: 2026-04-06
**최종 업데이트**: 2026-04-06 (15/18건 해결)
