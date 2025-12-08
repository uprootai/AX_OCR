"""
Result Manager
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
import os
import json
import base64
import shutil
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# 기본 결과 저장 디렉토리
DEFAULT_RESULT_DIR = os.getenv("RESULT_SAVE_DIR", "/tmp/gateway/results")

# 기본 보관 기간 (일)
DEFAULT_RETENTION_DAYS = int(os.getenv("RESULT_RETENTION_DAYS", "7"))


class ResultManager:
    """파이프라인 결과 저장 및 정리 관리자"""

    def __init__(self, base_dir: str = DEFAULT_RESULT_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_dir: Optional[Path] = None

    def create_session(self, workflow_name: str = "workflow") -> Path:
        """
        새 저장 세션 생성

        Args:
            workflow_name: 워크플로우 이름

        Returns:
            세션 디렉토리 경로
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")

        # 워크플로우 이름 정리 (파일명에 사용 가능하도록)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in workflow_name)
        safe_name = safe_name[:50]  # 길이 제한

        session_name = f"{time_str}_{safe_name}"
        session_dir = self.base_dir / date_str / session_name
        session_dir.mkdir(parents=True, exist_ok=True)

        self.current_session_dir = session_dir
        logger.info(f"결과 저장 세션 생성: {session_dir}")

        return session_dir

    def save_node_result(
        self,
        node_id: str,
        node_type: str,
        result: Dict[str, Any],
        execution_order: int = 0,
        session_dir: Optional[Path] = None
    ) -> Dict[str, str]:
        """
        노드 실행 결과 저장

        Args:
            node_id: 노드 ID
            node_type: 노드 타입
            result: 실행 결과 딕셔너리
            execution_order: 실행 순서
            session_dir: 저장 디렉토리 (None이면 current_session_dir 사용)

        Returns:
            저장된 파일 경로 딕셔너리
        """
        save_dir = session_dir or self.current_session_dir
        if not save_dir:
            logger.warning("저장 세션이 없습니다. create_session()을 먼저 호출하세요.")
            return {}

        saved_files = {}
        prefix = f"node_{execution_order:02d}_{node_type}"

        # 1. JSON 결과 저장 (이미지 데이터 제외)
        json_path = save_dir / f"{prefix}.json"
        json_result = self._prepare_json_result(result, node_id, node_type)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2, default=str)
        saved_files['json'] = str(json_path)
        logger.debug(f"JSON 저장: {json_path}")

        # 2. 오버레이 이미지 저장
        image_data = self._extract_image_data(result)
        if image_data:
            image_path = save_dir / f"{prefix}.jpg"
            self._save_base64_image(image_data, image_path)
            saved_files['image'] = str(image_path)
            logger.debug(f"이미지 저장: {image_path}")

        # 3. 원본 이미지도 별도 저장 (있는 경우)
        original_image = result.get('original_image')
        if original_image and original_image != image_data:
            original_path = save_dir / f"{prefix}_original.jpg"
            self._save_base64_image(original_image, original_path)
            saved_files['original'] = str(original_path)

        return saved_files

    def save_workflow_metadata(
        self,
        workflow_name: str,
        nodes: List[Dict[str, Any]],
        execution_time: float,
        status: str = "completed",
        session_dir: Optional[Path] = None
    ):
        """
        워크플로우 메타데이터 저장

        Args:
            workflow_name: 워크플로우 이름
            nodes: 노드 목록
            execution_time: 총 실행 시간 (초)
            status: 실행 상태
            session_dir: 저장 디렉토리
        """
        save_dir = session_dir or self.current_session_dir
        if not save_dir:
            return

        metadata = {
            "workflow_name": workflow_name,
            "executed_at": datetime.now().isoformat(),
            "execution_time_seconds": execution_time,
            "status": status,
            "total_nodes": len(nodes),
            "nodes": [
                {
                    "id": n.get("id"),
                    "type": n.get("type"),
                    "label": n.get("label", n.get("type")),
                }
                for n in nodes
            ]
        }

        metadata_path = save_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"워크플로우 메타데이터 저장: {metadata_path}")

    def _prepare_json_result(
        self,
        result: Dict[str, Any],
        node_id: str,
        node_type: str
    ) -> Dict[str, Any]:
        """JSON 저장용 결과 준비 (대용량 이미지 데이터 제외)"""
        json_result = {
            "node_id": node_id,
            "node_type": node_type,
            "saved_at": datetime.now().isoformat(),
        }

        # 이미지 필드 제외하고 복사
        image_fields = {'image', 'visualized_image', 'original_image', 'overlay_image'}

        for key, value in result.items():
            if key in image_fields:
                # 이미지 필드는 존재 여부만 기록
                json_result[f"{key}_saved"] = bool(value)
            elif key == 'raw_response':
                # raw_response에서도 이미지 제외
                if isinstance(value, dict):
                    cleaned = {k: v for k, v in value.items() if k not in image_fields}
                    json_result[key] = cleaned
            else:
                json_result[key] = value

        return json_result

    def _extract_image_data(self, result: Dict[str, Any]) -> Optional[str]:
        """결과에서 오버레이 이미지 데이터 추출"""
        # 우선순위: visualized_image > image > overlay_image
        for field in ['visualized_image', 'image', 'overlay_image']:
            image_data = result.get(field)
            if image_data and isinstance(image_data, str) and len(image_data) > 100:
                return image_data
        return None

    def _save_base64_image(self, base64_data: str, file_path: Path):
        """Base64 이미지를 파일로 저장"""
        try:
            # Data URL prefix 제거
            if base64_data.startswith('data:'):
                if ',' in base64_data:
                    base64_data = base64_data.split(',', 1)[1]

            image_bytes = base64.b64decode(base64_data)
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
        except Exception as e:
            logger.error(f"이미지 저장 실패: {e}")

    def cleanup_old_results(
        self,
        max_age_days: int = DEFAULT_RETENTION_DAYS,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        오래된 결과 정리

        Args:
            max_age_days: 보관 기간 (일)
            dry_run: True면 실제 삭제 없이 목록만 반환

        Returns:
            정리 결과 통계
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_dirs = []
        total_size = 0

        for date_dir in self.base_dir.iterdir():
            if not date_dir.is_dir():
                continue

            try:
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                if dir_date < cutoff_date:
                    # 디렉토리 크기 계산
                    dir_size = sum(f.stat().st_size for f in date_dir.rglob('*') if f.is_file())
                    total_size += dir_size

                    if not dry_run:
                        shutil.rmtree(date_dir)
                        logger.info(f"삭제됨: {date_dir} ({dir_size / 1024:.1f} KB)")

                    deleted_dirs.append({
                        "path": str(date_dir),
                        "date": date_dir.name,
                        "size_bytes": dir_size
                    })
            except ValueError:
                # 날짜 형식이 아닌 디렉토리는 무시
                continue

        result = {
            "deleted_count": len(deleted_dirs),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "max_age_days": max_age_days,
            "dry_run": dry_run,
            "deleted_directories": deleted_dirs
        }

        logger.info(
            f"결과 정리 완료: {len(deleted_dirs)}개 디렉토리 "
            f"({total_size / (1024 * 1024):.2f} MB) "
            f"{'(dry run)' if dry_run else '삭제됨'}"
        )

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """결과 저장소 통계"""
        total_size = 0
        total_files = 0
        date_counts = {}

        for date_dir in self.base_dir.iterdir():
            if not date_dir.is_dir():
                continue

            try:
                datetime.strptime(date_dir.name, "%Y-%m-%d")
                session_count = sum(1 for d in date_dir.iterdir() if d.is_dir())
                file_count = sum(1 for f in date_dir.rglob('*') if f.is_file())
                dir_size = sum(f.stat().st_size for f in date_dir.rglob('*') if f.is_file())

                date_counts[date_dir.name] = {
                    "sessions": session_count,
                    "files": file_count,
                    "size_bytes": dir_size
                }
                total_size += dir_size
                total_files += file_count
            except ValueError:
                continue

        return {
            "base_dir": str(self.base_dir),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_files": total_files,
            "dates": date_counts,
            "retention_days": DEFAULT_RETENTION_DAYS
        }

    def list_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 세션 목록"""
        sessions = []

        for date_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue

            try:
                datetime.strptime(date_dir.name, "%Y-%m-%d")
                for session_dir in sorted(date_dir.iterdir(), reverse=True):
                    if not session_dir.is_dir():
                        continue

                    metadata_path = session_dir / "metadata.json"
                    metadata = {}
                    if metadata_path.exists():
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                    sessions.append({
                        "path": str(session_dir),
                        "date": date_dir.name,
                        "session": session_dir.name,
                        "workflow_name": metadata.get("workflow_name", "unknown"),
                        "executed_at": metadata.get("executed_at"),
                        "status": metadata.get("status", "unknown"),
                        "total_nodes": metadata.get("total_nodes", 0)
                    })

                    if len(sessions) >= limit:
                        return sessions
            except ValueError:
                continue

        return sessions


# 싱글톤 인스턴스
_result_manager: Optional[ResultManager] = None


def get_result_manager() -> ResultManager:
    """ResultManager 싱글톤 인스턴스 반환"""
    global _result_manager
    if _result_manager is None:
        _result_manager = ResultManager()
    return _result_manager


def cleanup_results(max_age_days: int = DEFAULT_RETENTION_DAYS, dry_run: bool = False):
    """
    결과 정리 헬퍼 함수

    사용 예:
        from utils.result_manager import cleanup_results
        cleanup_results(max_age_days=7)
    """
    manager = get_result_manager()
    return manager.cleanup_old_results(max_age_days=max_age_days, dry_run=dry_run)


# =============================================================================
# 자동 정리 스케줄러
# =============================================================================

# 정리 스케줄 설정
CLEANUP_INTERVAL_HOURS = int(os.getenv("RESULT_CLEANUP_INTERVAL_HOURS", "24"))  # 기본 24시간
CLEANUP_HOUR = int(os.getenv("RESULT_CLEANUP_HOUR", "2"))  # 기본 새벽 2시

_cleanup_task: Optional[asyncio.Task] = None


async def _scheduled_cleanup_loop():
    """
    스케줄된 정리 루프

    매일 지정된 시간(기본 새벽 2시)에 오래된 결과를 자동 삭제합니다.
    """
    logger.info(f"🗑️ 결과 자동 정리 스케줄러 시작 (매일 {CLEANUP_HOUR}시, 보관기간: {DEFAULT_RETENTION_DAYS}일)")

    while True:
        try:
            # 다음 정리 시간 계산
            now = datetime.now()
            next_cleanup = now.replace(hour=CLEANUP_HOUR, minute=0, second=0, microsecond=0)

            # 이미 지난 시간이면 다음 날로
            if next_cleanup <= now:
                next_cleanup += timedelta(days=1)

            # 대기 시간 계산
            wait_seconds = (next_cleanup - now).total_seconds()
            logger.info(f"🗑️ 다음 정리 예정: {next_cleanup.strftime('%Y-%m-%d %H:%M')} ({wait_seconds/3600:.1f}시간 후)")

            # 대기
            await asyncio.sleep(wait_seconds)

            # 정리 실행
            logger.info("🗑️ 자동 정리 시작...")
            manager = get_result_manager()
            result = manager.cleanup_old_results(max_age_days=DEFAULT_RETENTION_DAYS)

            if result["deleted_count"] > 0:
                logger.info(
                    f"🗑️ 자동 정리 완료: {result['deleted_count']}개 디렉토리 삭제 "
                    f"({result['total_size_mb']:.2f} MB 확보)"
                )
            else:
                logger.info("🗑️ 자동 정리 완료: 삭제할 항목 없음")

        except asyncio.CancelledError:
            logger.info("🗑️ 결과 자동 정리 스케줄러 중지됨")
            break
        except Exception as e:
            logger.error(f"🗑️ 자동 정리 중 오류: {e}")
            # 오류 발생 시 1시간 후 재시도
            await asyncio.sleep(3600)


def start_cleanup_scheduler():
    """
    자동 정리 스케줄러 시작

    Gateway API startup에서 호출됩니다.
    """
    global _cleanup_task

    if _cleanup_task is not None and not _cleanup_task.done():
        logger.warning("🗑️ 정리 스케줄러가 이미 실행 중입니다")
        return

    _cleanup_task = asyncio.create_task(_scheduled_cleanup_loop())
    logger.info("🗑️ 결과 자동 정리 스케줄러 등록됨")


def stop_cleanup_scheduler():
    """
    자동 정리 스케줄러 중지

    Gateway API shutdown에서 호출됩니다.
    """
    global _cleanup_task

    if _cleanup_task is not None and not _cleanup_task.done():
        _cleanup_task.cancel()
        logger.info("🗑️ 결과 자동 정리 스케줄러 중지 요청됨")
