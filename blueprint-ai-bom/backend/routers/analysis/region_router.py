"""Region Router - 영역 분할 API (Phase 5)

영역 분할 및 처리 기능:
- 도면 영역 자동 분할
- 영역 CRUD
- 영역별 처리 실행
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
import logging

from schemas.region import (
    Region,
    RegionSegmentationConfig,
    RegionSegmentationResult,
    RegionUpdate,
    BulkRegionUpdate,
    ManualRegion,
    RegionProcessingResult,
    RegionListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Regions"])

# 서비스 전역 변수
_region_segmenter = None


def set_region_services(region_segmenter):
    """영역 분할 서비스 설정"""
    global _region_segmenter
    _region_segmenter = region_segmenter


def get_region_segmenter():
    if _region_segmenter is None:
        raise HTTPException(status_code=500, detail="Region segmenter not initialized")
    return _region_segmenter


def get_session_service():
    """core_router에서 세션 서비스 가져오기"""
    from .core_router import get_session_service as _get_session_service
    return _get_session_service()


# ==================== 영역 분할 API ====================

@router.post("/regions/{session_id}/segment", response_model=RegionSegmentationResult)
async def segment_regions(
    session_id: str,
    config: Optional[RegionSegmentationConfig] = None,
    use_vlm: bool = False,
) -> RegionSegmentationResult:
    """
    도면 영역 분할 실행

    도면을 다음 영역으로 분할:
    - 표제란 (Title Block): 메타데이터 추출
    - 메인 뷰 (Main View): YOLO + OCR 적용
    - BOM 테이블: 테이블 파싱
    - 범례 (Legend): 심볼 매칭
    - 노트/주석 영역: OCR 적용
    """
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    try:
        result = await segmenter.segment(
            session_id=session_id,
            image_path=image_path,
            config=config,
            use_vlm=use_vlm,
        )

        session_service.update_session(session_id, {
            "regions": [r.model_dump() for r in result.regions],
            "region_stats": result.region_stats,
        })

        return result

    except Exception as e:
        logger.error(f"영역 분할 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regions/{session_id}", response_model=RegionListResponse)
async def get_regions(session_id: str) -> RegionListResponse:
    """세션의 영역 목록 조회"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    regions = segmenter.get_regions(session_id)

    return RegionListResponse(
        session_id=session_id,
        regions=regions,
        total=len(regions),
    )


@router.get("/regions/{session_id}/{region_id}", response_model=Region)
async def get_region(session_id: str, region_id: str) -> Region:
    """특정 영역 조회"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    region = segmenter.get_region(session_id, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="영역을 찾을 수 없습니다")

    return region


@router.put("/regions/{session_id}/{region_id}", response_model=Region)
async def update_region(
    session_id: str,
    region_id: str,
    update: RegionUpdate,
) -> Region:
    """영역 업데이트"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    update.region_id = region_id

    updated = segmenter.update_region(session_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="영역을 찾을 수 없습니다")

    return updated


@router.put("/regions/{session_id}/bulk", response_model=List[Region])
async def bulk_update_regions(
    session_id: str,
    bulk_update: BulkRegionUpdate,
) -> List[Region]:
    """일괄 영역 업데이트"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    results = []
    for update in bulk_update.updates:
        updated = segmenter.update_region(session_id, update)
        if updated:
            results.append(updated)

    return results


@router.post("/regions/{session_id}/add", response_model=Region)
async def add_manual_region(
    session_id: str,
    manual_region: ManualRegion,
) -> Region:
    """수동 영역 추가"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_width = session.get("image_width")
    image_height = session.get("image_height")

    if not image_width or not image_height:
        from PIL import Image
        file_path = session.get("file_path")
        if file_path:
            try:
                with Image.open(file_path) as img:
                    image_width, image_height = img.size
                    session_service.update_session(session_id, {
                        "image_width": image_width,
                        "image_height": image_height,
                    })
            except Exception:
                image_width = 1000
                image_height = 1000
        else:
            image_width = 1000
            image_height = 1000

    region = segmenter.add_region(
        session_id=session_id,
        manual_region=manual_region,
        image_width=image_width,
        image_height=image_height,
    )

    return region


@router.delete("/regions/{session_id}/{region_id}")
async def delete_region(session_id: str, region_id: str) -> Dict[str, Any]:
    """영역 삭제"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    deleted = segmenter.delete_region(session_id, region_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="영역을 찾을 수 없습니다")

    return {"deleted": True, "region_id": region_id}


@router.post("/regions/{session_id}/{region_id}/process", response_model=RegionProcessingResult)
async def process_region(
    session_id: str,
    region_id: str,
) -> RegionProcessingResult:
    """
    단일 영역 처리

    영역 타입과 처리 전략에 따라 적절한 처리 수행:
    - YOLO_OCR: YOLO 검출 + OCR
    - OCR_ONLY: OCR만 적용
    - TABLE_PARSE: 테이블 파싱
    - METADATA_EXTRACT: 메타데이터 추출 (표제란)
    - SYMBOL_MATCH: 심볼 매칭 (범례)
    """
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    result = await segmenter.process_region(session_id, region_id, image_path)
    if not result:
        raise HTTPException(status_code=404, detail="영역을 찾을 수 없습니다")

    return result


@router.post("/regions/{session_id}/process-all")
async def process_all_regions(session_id: str) -> Dict[str, Any]:
    """모든 영역 처리"""
    session_service = get_session_service()
    segmenter = get_region_segmenter()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    regions = segmenter.get_regions(session_id)
    results = []
    success_count = 0
    error_count = 0

    for region in regions:
        result = await segmenter.process_region(session_id, region.id, image_path)
        if result:
            results.append(result.model_dump())
            if result.success:
                success_count += 1
            else:
                error_count += 1

    return {
        "session_id": session_id,
        "total_regions": len(regions),
        "processed": success_count + error_count,
        "success": success_count,
        "errors": error_count,
        "results": results,
    }
