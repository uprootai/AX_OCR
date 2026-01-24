"""Export Schemas - 세션 Export 패키지 스키마

Phase 2E: 검증 완료된 세션을 패키지로 내보내기
- 템플릿 스냅샷 포함
- 이미지 + 검출 결과 + 검증 상태
- ZIP 패키지 생성
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExportManifest(BaseModel):
    """Export 패키지 매니페스트"""
    export_version: str = Field(default="2.0", description="Export 버전")
    export_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Export 시간"
    )

    # 세션 정보
    session_id: str
    session_filename: str
    drawing_type: Optional[str] = None

    # 템플릿 스냅샷
    template_snapshot: Optional[Dict[str, Any]] = Field(
        None,
        description="Export 시점의 워크플로우 템플릿 (고정)"
    )

    # 통계
    image_count: int = 0
    detection_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    modified_count: int = 0

    # 메타데이터
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    customer: Optional[str] = None
    exported_by: Optional[str] = None
    notes: Optional[str] = None


class ExportPreview(BaseModel):
    """Export 미리보기"""
    session_id: str
    can_export: bool = Field(description="Export 가능 여부")
    reason: Optional[str] = Field(None, description="Export 불가 사유")

    # 포함될 내용
    image_count: int = 0
    detection_count: int = 0
    approved_images: int = 0
    modified_images: int = 0
    rejected_images: int = 0
    pending_images: int = 0

    # 예상 파일 크기
    estimated_size_mb: float = 0.0

    # 템플릿 정보
    template_id: Optional[str] = None
    template_name: Optional[str] = None


class ExportRequest(BaseModel):
    """Export 요청"""
    include_images: bool = Field(
        default=True,
        description="이미지 파일 포함 여부"
    )
    include_thumbnails: bool = Field(
        default=True,
        description="썸네일 포함 여부"
    )
    include_rejected: bool = Field(
        default=False,
        description="거부된 검출 결과 포함 여부"
    )
    include_template: bool = Field(
        default=True,
        description="템플릿 스냅샷 포함 여부"
    )
    exported_by: Optional[str] = Field(
        None,
        description="Export 수행자"
    )
    notes: Optional[str] = Field(
        None,
        description="Export 메모"
    )


class ExportResponse(BaseModel):
    """Export 응답"""
    success: bool
    session_id: str
    export_id: str = Field(description="Export 고유 ID")
    filename: str = Field(description="생성된 파일명")
    file_path: str = Field(description="파일 경로")
    file_size_bytes: int = Field(description="파일 크기 (bytes)")
    created_at: str = Field(description="생성 시간")
    manifest: ExportManifest = Field(description="매니페스트 정보")


class ExportHistoryItem(BaseModel):
    """Export 이력 항목"""
    export_id: str
    session_id: str
    filename: str
    file_size_bytes: int
    created_at: str
    exported_by: Optional[str] = None
    image_count: int = 0
    detection_count: int = 0


class ExportHistoryResponse(BaseModel):
    """Export 이력 응답"""
    session_id: str
    exports: List[ExportHistoryItem]
    total: int


# =============================================================================
# Self-contained Export (Docker 이미지 포함)
# =============================================================================

class SelfContainedExportRequest(BaseModel):
    """Self-contained Export 요청"""
    include_images: bool = Field(
        default=True,
        description="세션 이미지 파일 포함 여부"
    )
    include_docker: bool = Field(
        default=True,
        description="Docker 이미지 포함 여부"
    )
    compress_images: bool = Field(
        default=True,
        description="Docker 이미지 gzip 압축 여부"
    )
    port_offset: int = Field(
        default=10000,
        description="포트 오프셋 (기존 서비스와 충돌 방지, 예: 5005 → 15005)"
    )
    container_prefix: str = Field(
        default="imported",
        description="컨테이너 이름 접두사 (예: imported-yolo-api)"
    )
    exported_by: Optional[str] = Field(
        None,
        description="Export 수행자"
    )
    notes: Optional[str] = Field(
        None,
        description="Export 메모"
    )


class DockerImageInfo(BaseModel):
    """Docker 이미지 정보"""
    service_name: str = Field(description="서비스 이름")
    image_name: str = Field(description="이미지 이름")
    file_name: str = Field(description="tar 파일명")
    size_mb: float = Field(description="파일 크기 (MB)")
    original_port: int = Field(description="원본 포트")
    mapped_port: int = Field(description="매핑된 포트 (오프셋 적용)")


class SelfContainedExportResponse(BaseModel):
    """Self-contained Export 응답"""
    success: bool
    session_id: str
    export_id: str = Field(description="Export 고유 ID")
    filename: str = Field(description="생성된 파일명")
    file_path: str = Field(description="파일 경로")
    file_size_bytes: int = Field(description="파일 크기 (bytes)")
    created_at: str = Field(description="생성 시간")

    # Self-contained 전용 필드
    included_services: List[str] = Field(description="포함된 Docker 서비스 목록")
    docker_images: List[DockerImageInfo] = Field(
        default=[],
        description="Docker 이미지 상세 정보"
    )
    docker_images_size_mb: float = Field(description="Docker 이미지 총 크기 (MB)")
    port_offset: int = Field(description="적용된 포트 오프셋")
    import_instructions: str = Field(description="Import 방법 안내")


class SelfContainedPreview(BaseModel):
    """Self-contained Export 미리보기"""
    session_id: str
    can_export: bool = Field(description="Export 가능 여부")
    reason: Optional[str] = Field(None, description="Export 불가 사유")

    # 필요 서비스 목록
    required_services: List[str] = Field(description="필요한 Docker 서비스")
    estimated_sizes_mb: Dict[str, float] = Field(description="서비스별 예상 크기 (MB)")
    total_estimated_size_mb: float = Field(description="총 예상 크기 (MB)")

    # 포트 매핑 (오프셋 적용)
    port_mapping: Dict[str, Dict[str, int]] = Field(
        default={},
        description="서비스별 포트 매핑 {서비스: {original: 5005, mapped: 15005}}"
    )

    # 워크플로우 정보
    workflow_node_types: List[str] = Field(
        default=[],
        description="워크플로우에 사용된 노드 타입"
    )
