"""
Base Node Executor
모든 노드 실행기의 추상 기반 클래스
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import time
import logging
import asyncio
import random

import httpx

logger = logging.getLogger(__name__)


# =====================
# API 호출 Mixin (재시도/타임아웃 표준화)
# =====================

class APICallerMixin:
    """
    API 호출 공통 로직 (재시도, 타임아웃, 에러 처리)

    Executor에서 상속받아 사용:
        class MyExecutor(BaseNodeExecutor, APICallerMixin):
            async def execute(self, inputs, context):
                success, data, error = await self._api_call_with_retry(
                    "POST", "/endpoint", json_data={...}
                )
    """

    # 기본 설정 (서브클래스에서 오버라이드 가능)
    API_BASE_URL: str = ""
    DEFAULT_TIMEOUT: int = 60
    DEFAULT_MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: float = 1.0  # 첫 번째 재시도 대기 시간 (초)
    RETRY_BACKOFF_MAX: float = 30.0  # 최대 대기 시간 (초)

    async def _api_call_with_retry(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict] = None,
        files: Optional[dict] = None,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        raise_on_error: bool = False,
        base_url: Optional[str] = None,
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        재시도 로직이 포함된 API 호출

        Args:
            method: HTTP 메서드 (GET, POST, PATCH, DELETE)
            endpoint: API 엔드포인트 (예: "/sessions/upload")
            json_data: JSON 바디
            files: 파일 업로드 (httpx files 형식)
            data: form data
            params: 쿼리 파라미터
            timeout: 타임아웃 (초), 기본값: DEFAULT_TIMEOUT
            max_retries: 최대 재시도 횟수, 기본값: DEFAULT_MAX_RETRIES
            raise_on_error: 최종 실패 시 예외 발생 여부
            base_url: API 베이스 URL (기본값: self.API_BASE_URL)

        Returns:
            Tuple[bool, Optional[dict], Optional[str]]: (성공여부, 응답JSON, 에러메시지)
        """
        _base_url = base_url or getattr(self, 'API_BASE_URL', '') or getattr(self, 'BASE_URL', '')
        _timeout = timeout or getattr(self, 'DEFAULT_TIMEOUT', 60)
        _max_retries = max_retries if max_retries is not None else getattr(self, 'DEFAULT_MAX_RETRIES', 3)

        url = f"{_base_url}{endpoint}"
        last_error = None

        for attempt in range(_max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=float(_timeout)) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, params=params)
                    elif method.upper() == "POST":
                        response = await client.post(
                            url, json=json_data, files=files, data=data, params=params
                        )
                    elif method.upper() == "PATCH":
                        response = await client.patch(url, json=json_data, params=params)
                    elif method.upper() == "DELETE":
                        response = await client.delete(url, params=params)
                    else:
                        raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")

                    if response.status_code >= 400:
                        error_msg = f"{method} {endpoint} 실패: {response.status_code} - {response.text[:200]}"
                        # 4xx 에러는 재시도하지 않음 (클라이언트 에러)
                        if 400 <= response.status_code < 500:
                            logger.warning(error_msg)
                            if raise_on_error:
                                response.raise_for_status()
                            return False, None, error_msg
                        # 5xx 에러는 재시도
                        last_error = error_msg
                        logger.warning(f"{error_msg} (시도 {attempt + 1}/{_max_retries + 1})")
                    else:
                        # 성공
                        try:
                            result = response.json()
                        except Exception:
                            result = {"status_code": response.status_code}
                        return True, result, None

            except httpx.TimeoutException as e:
                last_error = f"{method} {endpoint} 타임아웃: {e}"
                logger.warning(f"{last_error} (시도 {attempt + 1}/{_max_retries + 1})")
            except httpx.ConnectError as e:
                last_error = f"{method} {endpoint} 연결 실패: {e}"
                logger.warning(f"{last_error} (시도 {attempt + 1}/{_max_retries + 1})")
            except Exception as e:
                last_error = f"{method} {endpoint} 오류: {type(e).__name__}: {e}"
                logger.warning(f"{last_error} (시도 {attempt + 1}/{_max_retries + 1})")

            # 재시도 대기 (마지막 시도가 아닌 경우)
            if attempt < _max_retries:
                backoff = min(
                    self.RETRY_BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 1),
                    self.RETRY_BACKOFF_MAX
                )
                logger.info(f"  {backoff:.1f}초 후 재시도...")
                await asyncio.sleep(backoff)

        # 모든 재시도 실패
        logger.error(f"{method} {endpoint} 최종 실패 (총 {_max_retries + 1}회 시도): {last_error}")
        if raise_on_error:
            raise httpx.HTTPStatusError(
                last_error or "Unknown error",
                request=None,
                response=None
            )
        return False, None, last_error

    # 편의 메서드
    async def _get_api(self, endpoint: str, **kwargs) -> Tuple[bool, Optional[dict], Optional[str]]:
        """GET API 호출"""
        return await self._api_call_with_retry("GET", endpoint, **kwargs)

    async def _post_api_retry(self, endpoint: str, **kwargs) -> Tuple[bool, Optional[dict], Optional[str]]:
        """POST API 호출 (재시도 포함)"""
        return await self._api_call_with_retry("POST", endpoint, **kwargs)

    async def _patch_api_retry(self, endpoint: str, **kwargs) -> Tuple[bool, Optional[dict], Optional[str]]:
        """PATCH API 호출 (재시도 포함)"""
        return await self._api_call_with_retry("PATCH", endpoint, **kwargs)

    async def _delete_api(self, endpoint: str, **kwargs) -> Tuple[bool, Optional[dict], Optional[str]]:
        """DELETE API 호출"""
        return await self._api_call_with_retry("DELETE", endpoint, **kwargs)


class BaseNodeExecutor(ABC):
    """노드 실행기 기본 클래스"""

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
        """
        Args:
            node_id: 노드 고유 ID
            node_type: 노드 타입
            parameters: 노드 파라미터
        """
        self.node_id = node_id
        self.node_type = node_type
        self.parameters = parameters
        self.logger = logging.getLogger(f"{__name__}.{node_type}")

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        노드 실행 (추상 메서드)

        Args:
            inputs: 입력 데이터
            context: 실행 컨텍스트 (전역 변수, 이전 노드 결과 등)

        Returns:
            실행 결과

        Raises:
            Exception: 실행 중 에러 발생 시
        """
        pass

    @abstractmethod
    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """
        파라미터 유효성 검사

        Returns:
            (is_valid, error_message)
        """
        pass

    async def run(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        실행 래퍼 (로깅, 타이밍, 에러 처리 포함)

        Args:
            inputs: 입력 데이터
            context: 실행 컨텍스트

        Returns:
            실행 결과 (메타데이터 포함)
        """
        start_time = time.time()
        self.logger.info(f"노드 {self.node_id} ({self.node_type}) 실행 시작")

        try:
            # 파라미터 유효성 검사
            is_valid, error = self.validate_parameters()
            if not is_valid:
                raise ValueError(f"파라미터 검증 실패: {error}")

            # 실제 실행
            result = await self.execute(inputs, context)

            execution_time = time.time() - start_time
            self.logger.info(
                f"노드 {self.node_id} 실행 완료 (소요 시간: {execution_time:.2f}초)"
            )

            # 메타데이터 추가
            return {
                "success": True,
                "node_id": self.node_id,
                "node_type": self.node_type,
                "data": result,
                "execution_time_ms": execution_time * 1000,
                "timestamp": time.time(),
            }

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                f"노드 {self.node_id} 실행 실패: {str(e)}",
                exc_info=True
            )

            return {
                "success": False,
                "node_id": self.node_id,
                "node_type": self.node_type,
                "error": str(e),
                "execution_time_ms": execution_time * 1000,
                "timestamp": time.time(),
            }

    def get_input_schema(self) -> Dict[str, Any]:
        """
        입력 스키마 정의 (옵션)

        Returns:
            JSON Schema 형식의 입력 스키마
        """
        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> Dict[str, Any]:
        """
        출력 스키마 정의 (옵션)

        Returns:
            JSON Schema 형식의 출력 스키마
        """
        return {"type": "object", "properties": {}}
