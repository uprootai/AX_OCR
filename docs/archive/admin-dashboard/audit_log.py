#!/usr/bin/env python3
"""
감사 로그 (Audit Log) 시스템
모든 중요한 시스템 작업을 추적하고 기록
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """감사 로그 작업 유형"""

    # 인증 및 인가
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGED = "auth.password.changed"
    SESSION_EXPIRED = "auth.session.expired"

    # 사용자 관리
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ENABLED = "user.enabled"
    USER_DISABLED = "user.disabled"

    # 모델 관리
    MODEL_TRAINED = "model.trained"
    MODEL_DEPLOYED = "model.deployed"
    MODEL_DELETED = "model.deleted"
    MODEL_DOWNLOADED = "model.downloaded"
    MODEL_UPLOADED = "model.uploaded"

    # API 관리
    API_TESTED = "api.tested"
    API_CONFIGURED = "api.configured"
    API_RESTARTED = "api.restarted"

    # Docker 관리
    DOCKER_CONTAINER_STARTED = "docker.container.started"
    DOCKER_CONTAINER_STOPPED = "docker.container.stopped"
    DOCKER_CONTAINER_RESTARTED = "docker.container.restarted"
    DOCKER_IMAGE_PULLED = "docker.image.pulled"
    DOCKER_IMAGE_REMOVED = "docker.image.removed"

    # 시스템 관리
    SYSTEM_CONFIG_CHANGED = "system.config.changed"
    SYSTEM_BACKUP_CREATED = "system.backup.created"
    SYSTEM_RESTORED = "system.restored"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_REBOOT = "system.reboot"

    # 로그 관리
    LOG_VIEWED = "log.viewed"
    LOG_DOWNLOADED = "log.downloaded"
    LOG_DELETED = "log.deleted"

    # 데이터 관리
    DATA_UPLOADED = "data.uploaded"
    DATA_DELETED = "data.deleted"
    DATA_EXPORTED = "data.exported"

    # 보안 이벤트
    UNAUTHORIZED_ACCESS = "security.unauthorized_access"
    PERMISSION_DENIED = "security.permission_denied"
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"


class AuditLevel(str, Enum):
    """감사 로그 심각도"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SECURITY = "security"


@dataclass
class AuditEntry:
    """감사 로그 엔트리"""

    timestamp: str
    action: str
    level: str
    username: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource: Optional[str]
    details: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict())


class AuditLogger:
    """감사 로그 관리 클래스"""

    def __init__(self, log_dir: str = "logs/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 현재 날짜의 로그 파일
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"audit_{self.current_date}.jsonl"

        logger.info(f"감사 로그 시스템 초기화: {self.log_file}")

    def _rotate_log_if_needed(self):
        """날짜가 바뀌면 로그 파일 교체"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != self.current_date:
            self.current_date = current_date
            self.log_file = self.log_dir / f"audit_{self.current_date}.jsonl"
            logger.info(f"감사 로그 파일 교체: {self.log_file}")

    def log(
        self,
        action: AuditAction,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        level: AuditLevel = AuditLevel.INFO,
        error_message: Optional[str] = None,
    ):
        """감사 로그 기록"""
        self._rotate_log_if_needed()

        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action.value,
            level=level.value,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            details=details or {},
            success=success,
            error_message=error_message,
        )

        # JSONL 형식으로 저장 (각 줄이 하나의 JSON 객체)
        try:
            with open(self.log_file, "a") as f:
                f.write(entry.to_json() + "\n")

            # 보안 관련 로그는 별도 로거로도 기록
            if level == AuditLevel.SECURITY or level == AuditLevel.CRITICAL:
                logger.warning(
                    f"[AUDIT {level.value.upper()}] {action.value} | "
                    f"User: {username} | IP: {ip_address} | "
                    f"Success: {success} | Details: {details}"
                )

        except Exception as e:
            logger.error(f"감사 로그 기록 실패: {e}")

    def query(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        username: Optional[str] = None,
        action: Optional[str] = None,
        level: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """감사 로그 조회"""
        results = []

        # 날짜 범위 결정
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # 해당 날짜 범위의 로그 파일 읽기
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"))

        for log_file in log_files:
            # 파일명에서 날짜 추출
            file_date = log_file.stem.replace("audit_", "")

            # 날짜 범위 확인
            if file_date < start_date or file_date > end_date:
                continue

            try:
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())

                            # 필터링
                            if username and entry.get("username") != username:
                                continue
                            if action and entry.get("action") != action:
                                continue
                            if level and entry.get("level") != level:
                                continue
                            if success is not None and entry.get("success") != success:
                                continue

                            results.append(entry)

                            # 제한 확인
                            if len(results) >= limit:
                                return results

                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                logger.error(f"로그 파일 읽기 실패 {log_file}: {e}")

        return results

    def get_statistics(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """감사 로그 통계"""
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        stats = {
            "total_events": 0,
            "by_action": {},
            "by_level": {},
            "by_user": {},
            "success_count": 0,
            "failure_count": 0,
            "security_events": 0,
        }

        # 해당 날짜 범위의 로그 파일 읽기
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"))

        for log_file in log_files:
            file_date = log_file.stem.replace("audit_", "")

            if file_date < start_date or file_date > end_date:
                continue

            try:
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            stats["total_events"] += 1

                            # 작업 유형별 통계
                            action = entry.get("action", "unknown")
                            stats["by_action"][action] = (
                                stats["by_action"].get(action, 0) + 1
                            )

                            # 심각도별 통계
                            level = entry.get("level", "info")
                            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

                            # 사용자별 통계
                            username = entry.get("username", "anonymous")
                            stats["by_user"][username] = (
                                stats["by_user"].get(username, 0) + 1
                            )

                            # 성공/실패 통계
                            if entry.get("success"):
                                stats["success_count"] += 1
                            else:
                                stats["failure_count"] += 1

                            # 보안 이벤트 통계
                            if level == "security":
                                stats["security_events"] += 1

                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                logger.error(f"통계 생성 중 오류 {log_file}: {e}")

        return stats

    def cleanup_old_logs(self, days: int = 90):
        """오래된 로그 파일 삭제"""
        cutoff_date = datetime.now()
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        deleted_count = 0

        for log_file in self.log_dir.glob("audit_*.jsonl"):
            file_date = log_file.stem.replace("audit_", "")

            if file_date < cutoff_str:
                try:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"오래된 감사 로그 삭제: {log_file}")
                except Exception as e:
                    logger.error(f"로그 파일 삭제 실패 {log_file}: {e}")

        logger.info(f"감사 로그 정리 완료: {deleted_count} 파일 삭제")
        return deleted_count

    def export_to_csv(self, output_file: str, **query_params):
        """감사 로그를 CSV로 내보내기"""
        import csv

        entries = self.query(**query_params)

        try:
            with open(output_file, "w", newline="") as f:
                if not entries:
                    return 0

                fieldnames = entries[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                writer.writeheader()
                for entry in entries:
                    # details 필드는 JSON 문자열로 변환
                    if "details" in entry:
                        entry["details"] = json.dumps(entry["details"])
                    writer.writerow(entry)

            logger.info(f"감사 로그 CSV 내보내기 완료: {output_file} ({len(entries)} entries)")
            return len(entries)

        except Exception as e:
            logger.error(f"CSV 내보내기 실패: {e}")
            return 0


# 전역 감사 로거 인스턴스
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """감사 로거 인스턴스 가져오기"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_log(
    action: AuditAction,
    username: Optional[str] = None,
    **kwargs
):
    """감사 로그 기록 편의 함수"""
    logger_instance = get_audit_logger()
    logger_instance.log(action=action, username=username, **kwargs)
