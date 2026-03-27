# S05: 파이프라인 실행 UI

> 버튼 하나로 실행 + 6단계 진행 표시

## 상태: ✅ Done (2026-03-27)

## 구현 내용
- 백엔드: POST /bmt/{session_id}/run-pipeline — 비동기 파이프라인 실행
- 백엔드: GET /bmt/{session_id}/pipeline-status — 실행 상태 폴링
- 프론트: 결과 없을 때 "파이프라인 실행" 버튼 표시
- 프론트: 실행 중 6단계 진행 바 + 단계별 메시지
- 프론트: 완료 시 자동 데이터 리로드

## 완료 조건
- [x] 구현 완료
- [x] tsc --noEmit 에러 0
- [x] Docker 배포
