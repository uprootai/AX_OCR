# Legacy Streamlit Code

이 폴더는 기존 Streamlit 기반 구현을 보존합니다.
새 React + FastAPI 구현이 완료된 후 삭제될 예정입니다.

## 파일 목록

| 파일 | 설명 |
|------|------|
| `real_ai_app.py` | 메인 Streamlit 앱 (3,200줄) |
| `real_ai_app_complete.py` | 전체 기능 버전 |
| `real_ai_app_backup_*.py` | 백업 버전들 |
| `patch_canvas.py` | Canvas 패치 |
| `utils/` | 유틸리티 함수들 |
| `restapi/` | REST API 참조 코드 |

## 마이그레이션 상태

- [x] 세션 관리 → `backend/services/session_service.py`
- [x] 검출 로직 → `backend/services/detection_service.py`
- [x] BOM 생성 → `backend/services/bom_service.py`
- [ ] Human-in-the-Loop UI → `frontend/` (진행중)

## 참고 사항

새 구현에서 참조할 주요 코드:
- 클래스 매핑: `real_ai_app.py` line 150-180
- BOM 생성 로직: `real_ai_app.py` line 2500-2800
- 검증 UI 상태: `real_ai_app.py` line 1800-2200
