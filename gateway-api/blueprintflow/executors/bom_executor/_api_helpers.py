"""
BOMExecutor API 호출 헬퍼 메서드
_call_api, _post_api, _patch_api (레거시 호환 + 재시도 지원)
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class BOMAPIHelpersMixin:
    """BOM API 호출 헬퍼 메서드 믹스인"""

    async def _call_api(
        self,
        method: str,
        endpoint: str,
        json_data: dict = None,
        files: dict = None,
        data: dict = None,
        timeout: int = 60,
        raise_on_error: bool = False,
        max_retries: int = 3,
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """API 호출 헬퍼 메서드 (재시도 로직 포함)

        Args:
            method: HTTP 메서드 (GET, POST, PATCH, DELETE)
            endpoint: API 엔드포인트 (BASE_URL 이후 경로, 예: "/sessions/upload")
            json_data: JSON 바디
            files: 파일 업로드 (httpx files 형식)
            data: form data
            timeout: 타임아웃 (초)
            raise_on_error: 에러 시 예외 발생 여부
            max_retries: 최대 재시도 횟수 (기본값: 3)

        Returns:
            Tuple[bool, Optional[dict], Optional[str]]: (성공여부, 응답JSON, 에러메시지)
        """
        return await self._api_call_with_retry(
            method=method,
            endpoint=endpoint,
            json_data=json_data,
            files=files,
            data=data,
            timeout=timeout,
            max_retries=max_retries,
            raise_on_error=raise_on_error,
        )

    async def _post_api(
        self,
        endpoint: str,
        json_data: dict = None,
        files: dict = None,
        data: dict = None,
        timeout: int = 60,
        raise_on_error: bool = False
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """POST API 호출 편의 메서드 (재시도 포함)"""
        return await self._call_api("POST", endpoint, json_data, files, data, timeout, raise_on_error)

    async def _patch_api(
        self,
        endpoint: str,
        json_data: dict = None,
        timeout: int = 60,
        raise_on_error: bool = False
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """PATCH API 호출 편의 메서드 (재시도 포함)"""
        return await self._call_api("PATCH", endpoint, json_data, None, None, timeout, raise_on_error)
