"""
표준 스키마 정의
모든 API 서비스에서 공통으로 사용하는 Pydantic 모델
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class StandardHealthResponse(BaseModel):
    """
    표준 헬스체크 응답

    모든 API 서비스에서 동일한 포맷으로 헬스체크 응답을 반환합니다.

    필수 필드:
    - status: "healthy" 또는 "unhealthy"
    - service: 서비스 이름 (예: "yolo-api")
    - version: 서비스 버전
    - timestamp: ISO 형식 타임스탬프

    선택 필드:
    - gpu_available: GPU 사용 가능 여부
    - model_loaded: 모델 로드 상태
    - details: 추가 상세 정보
    """
    status: str = Field(
        default="healthy",
        description="서비스 상태 (healthy/unhealthy)"
    )
    service: str = Field(
        ...,
        description="서비스 이름"
    )
    version: str = Field(
        default="1.0.0",
        description="서비스 버전"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="응답 시간 (ISO 8601)"
    )
    gpu_available: Optional[bool] = Field(
        default=None,
        description="GPU 사용 가능 여부"
    )
    model_loaded: Optional[bool] = Field(
        default=None,
        description="모델 로드 상태"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="추가 상세 정보"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "yolo-api",
                "version": "1.0.0",
                "timestamp": "2026-01-16T18:30:00.000000",
                "gpu_available": True,
                "model_loaded": True,
                "details": {
                    "gpu_name": "NVIDIA GeForce RTX 3090",
                    "model_path": "/models/yolo11n.pt"
                }
            }
        }


def create_health_response(
    service: str,
    version: str = "1.0.0",
    status: str = "healthy",
    gpu_available: Optional[bool] = None,
    model_loaded: Optional[bool] = None,
    **extra_details
) -> StandardHealthResponse:
    """
    헬스체크 응답 생성 헬퍼 함수

    Args:
        service: 서비스 이름
        version: 서비스 버전
        status: 상태 (healthy/unhealthy)
        gpu_available: GPU 사용 가능 여부
        model_loaded: 모델 로드 상태
        **extra_details: 추가 상세 정보

    Returns:
        StandardHealthResponse 인스턴스

    Example:
        >>> response = create_health_response(
        ...     service="yolo-api",
        ...     version="1.0.0",
        ...     gpu_available=True,
        ...     model_loaded=True,
        ...     gpu_name="NVIDIA RTX 3090"
        ... )
    """
    details = extra_details if extra_details else None

    return StandardHealthResponse(
        status=status,
        service=service,
        version=version,
        timestamp=datetime.now().isoformat(),
        gpu_available=gpu_available,
        model_loaded=model_loaded,
        details=details
    )
