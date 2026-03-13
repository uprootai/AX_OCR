"""
Result Manager - 자동 정리 스케줄러
매일 지정 시간(기본 새벽 2시)에 오래된 결과 및 업로드 파일을 자동 삭제합니다.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from .constants import DEFAULT_RETENTION_DAYS, CLEANUP_HOUR

logger = logging.getLogger(__name__)

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
            from .singleton import get_result_manager
            manager = get_result_manager()
            result = manager.cleanup_old_results(max_age_days=DEFAULT_RETENTION_DAYS)

            # 업로드 파일 정리
            upload_result = manager.cleanup_old_uploads()
            if upload_result["deleted_count"] > 0:
                logger.info(
                    f"🗑️ 업로드 파일 정리: {upload_result['deleted_count']}개 삭제 "
                    f"({upload_result.get('total_size_mb', 0):.2f} MB)"
                )

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
