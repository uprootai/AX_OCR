# S01: 크롭 이미지 생성 + API (백엔드)

> Min-Content 크롭 → 이미지 저장 → REST API

## 상태: ✅ Done (2026-03-27)

## 구현 내용
- `blueprint-ai-bom/backend/routers/bmt_router.py` 신규 생성
- `api_server.py`에 라우터 등록
- Docker 배포 완료

## API 엔드포인트
- GET /bmt/{session_id}/crops — 9개 크롭 목록
- GET /bmt/{session_id}/crops/{index}/tags — 크롭별 TAG (좌표+BOM상태)
- PUT /bmt/{session_id}/tags/{tag_id} — TAG 승인/수정/삭제
- GET /bmt/{session_id}/bom-match — BOM 매칭 결과
- PUT /bmt/{session_id}/bom-match/{tag} — 불일치 판정
- GET /bmt/{session_id}/summary — 전체 요약 + Review 진행률

## 완료 조건
- [x] 구현 완료
- [x] Docker 배포 후 API 테스트 통과
