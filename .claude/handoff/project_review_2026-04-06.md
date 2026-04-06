# AX POC 프로젝트 전면 검토 — 2026-04-06

> YouTube "AI가 코드 짜는 시대, 신입 개발자는 대체 뭘 해야 하나요?" 관점 기반

## Critical

| # | 문제 | 위치 | 영향 |
|---|------|------|------|
| 1 | **Docker 소켓 노출 + 인증 없음** | docker-compose.yml#L223, docker_router.py | 컨테이너 start/stop/recreate 외부 노출 |
| 2 | **API 키 암호화 폴백 = base64** | crypto.py, api_key_service.py | cryptography 미설치 시 평문 저장 |
| 3 | **1000줄 초과 파일 7개** | dimension_ensemble(1042), s08_ocr(1155), s08_fullpage(1106) 등 | CLAUDE.md 규칙 위반, 유지보수 어려움 |
| 4 | **절대경로 하드코딩 9곳** | scripts/*.py `/home/uproot/ax/poc/...` | 이식성 0 |

## High

| # | 문제 | 위치 | 영향 |
|---|------|------|------|
| 5 | **Gateway↔BOM Docker 통신 기본값 깨짐** | template_routes.py `localhost:5020` | Docker 네트워크에서 미도달 |
| 6 | **base64 이미지 전송 금지 규칙 위반** | template_routes.py, yolo_executor.py, sessionStore.ts | CLAUDE.md 명시 금지인데 핵심 파이프라인에서 사용 |
| 7 | **Line Detector 도메인 정보 손실** | classification_service → line_detector_service.py | centerline/pipe 분류가 BOM에서 버려짐 |
| 8 | **치수선/구조선 구분 없음** | line_detector_service.py#L389 | 텍스트 근처 선 = 치수선 휴리스틱 |
| 9 | **suryaocr 서비스명 오타** | api_registry.py `suryaocr-api` vs compose `surya-ocr-api` | 헬스체크 실패 |
| 10 | **confidence_threshold 드리프트** | backend 0.4, frontend 0.5, table 0.7 | SSOT 없이 4곳에서 다른 값 |
| 11 | **GT 자동 검증 CI 미연결** | tests/eval/ 8케이스만, CI에서 실행 안 함 | 회귀 감지 불가 |

## Medium

| # | 문제 | 영향 |
|---|------|------|
| 12 | CI가 BOM backend 테스트 미실행, tsc `continue-on-error: true` | 규칙 미강제 |
| 13 | CD 파이프라인 SSH/헬스체크 placeholder | 실배포 불가 |
| 14 | .todo/ACTIVE.md "600줄 이하" 거짓 기록 | 상태 추적 불신뢰 |
| 15 | ASSY/단품 처리 로직 문자열 기반 흩어짐 | 중앙 정책 없음 |
| 16 | 포트 문서 드리프트 (5173 vs 5021 vs 3000) | 설정 혼란 |
| 17 | 실험 스크립트 6개 중복 로직 | s08_cardinal_v3_*.py 공통 모듈화 안 됨 |

## Low

| # | 문제 |
|---|------|
| 18 | 버전 정보 불일치 (docs v8.0, app 10.6.0, root 8.0.0) |

## 우선순위 권장

1. **보안**: Docker surface 폐쇄 + API key 실제 암호화
2. **정합성**: base64 금지 실행 + confidence SSOT + 포트 문서 통일
3. **품질**: 1000줄 파일 분리 + 절대경로 제거 + 실험 스크립트 모듈화
4. **검증**: GT eval CI 연결 + BOM backend 테스트 강제 + tsc 에러 0
5. **도메인**: 치수선/구조선 구분 로직 + ASSY/단품 중앙 정책

---
**검토자**: Claude Opus 4.6 + Codex gpt-5.4 xhigh
**생성일**: 2026-04-06
