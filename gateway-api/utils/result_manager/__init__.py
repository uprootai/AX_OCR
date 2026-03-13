"""
Result Manager Package
파이프라인 실행 결과 저장 및 정리 관리

저장 구조:
/tmp/gateway/results/
  └── 2025-12-08/
      └── 14-30-25_workflow-name/
          ├── metadata.json          # 워크플로우 메타정보
          ├── node_1_imageinput.json  # 노드별 JSON 결과
          ├── node_1_imageinput.jpg   # 노드별 오버레이 이미지
          ├── node_2_edocr2.json
          ├── node_2_edocr2.jpg
          └── ...

자동 정리:
- Gateway API 시작 시 스케줄러 시작
- 매일 새벽 2시에 오래된 결과 자동 삭제
- 기본 보관 기간: 7일
"""

# 상수
from .constants import (
    DEFAULT_RESULT_DIR,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_UPLOAD_DIR,
    DEFAULT_UPLOAD_TTL_HOURS,
    CLEANUP_INTERVAL_HOURS,
    CLEANUP_HOUR,
)

# 핵심 클래스
from .core import ResultManager

# 싱글톤 및 헬퍼
from .singleton import get_result_manager, cleanup_results

# 스케줄러
from .scheduler import start_cleanup_scheduler, stop_cleanup_scheduler

__all__ = [
    # 상수
    "DEFAULT_RESULT_DIR",
    "DEFAULT_RETENTION_DAYS",
    "DEFAULT_UPLOAD_DIR",
    "DEFAULT_UPLOAD_TTL_HOURS",
    "CLEANUP_INTERVAL_HOURS",
    "CLEANUP_HOUR",
    # 핵심 클래스
    "ResultManager",
    # 싱글톤 및 헬퍼
    "get_result_manager",
    "cleanup_results",
    # 스케줄러
    "start_cleanup_scheduler",
    "stop_cleanup_scheduler",
]
