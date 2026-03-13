"""
Result Manager - Core
ResultManager 클래스: 세션 생성, 노드 결과 저장, 메타데이터, 통계, 정리
"""
import json
import base64
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .constants import DEFAULT_RESULT_DIR, DEFAULT_RETENTION_DAYS, DEFAULT_UPLOAD_DIR, DEFAULT_UPLOAD_TTL_HOURS

logger = logging.getLogger(__name__)


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
            # indent 제거 - 대용량 JSON 저장 성능 개선 (2MB JSON에서 100초+ → 1초)
            json.dump(json_result, f, ensure_ascii=False, default=str)
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

    def cleanup_old_uploads(
        self,
        upload_dir: str = DEFAULT_UPLOAD_DIR,
        max_age_hours: int = DEFAULT_UPLOAD_TTL_HOURS,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        업로드 파일 자동 삭제 (TTL 기반)

        Args:
            upload_dir: 업로드 디렉토리 경로
            max_age_hours: 보관 기간 (시간)
            dry_run: True면 실제 삭제 없이 목록만 반환
        """
        from pathlib import Path as _Path
        upload_path = _Path(upload_dir)
        if not upload_path.exists():
            return {"deleted_count": 0, "total_size_bytes": 0, "max_age_hours": max_age_hours}

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        deleted_files = []
        total_size = 0

        for file_path in upload_path.rglob('*'):
            if not file_path.is_file():
                continue

            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    total_size += file_size

                    if not dry_run:
                        file_path.unlink()
                        logger.info(
                            f"업로드 파일 삭제: {file_path.name} "
                            f"(크기: {file_size / 1024:.1f} KB, "
                            f"수정: {mtime.isoformat()})"
                        )

                    deleted_files.append({
                        "path": str(file_path),
                        "size_bytes": file_size,
                        "modified": mtime.isoformat(),
                        "scheduled_deletion": (mtime + timedelta(hours=max_age_hours)).isoformat()
                    })
            except Exception as e:
                logger.error(f"업로드 파일 삭제 실패: {file_path} - {e}")

        return {
            "deleted_count": len(deleted_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "max_age_hours": max_age_hours,
            "dry_run": dry_run,
            "deleted_files": deleted_files
        }
