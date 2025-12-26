"""GD&T Router - GD&T 파싱 및 표제란 OCR API

GD&T (기하공차) 및 표제란 관련 기능:
- GD&T 파싱 실행/조회
- FCF (Feature Control Frame) CRUD
- 데이텀 관리
- 표제란 OCR
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
import logging

from schemas.gdt import (
    GDTParsingConfig,
    GDTParsingResult,
    FCFUpdate,
    BulkFCFUpdate,
    ManualFCF,
    ManualDatum,
    GDTListResponse,
    GDTSummary,
    FeatureControlFrame,
    DatumFeature,
)
from schemas.region import (
    RegionSegmentationConfig,
    TitleBlockData,
    RegionType,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["GD&T & Title Block"])

# 서비스 전역 변수
_gdt_parser = None


def set_gdt_services(gdt_parser):
    """GD&T 파서 서비스 설정"""
    global _gdt_parser
    _gdt_parser = gdt_parser


def get_gdt_parser():
    if _gdt_parser is None:
        raise HTTPException(status_code=500, detail="GDT parser not initialized")
    return _gdt_parser


def get_session_service():
    """core_router에서 세션 서비스 가져오기"""
    from .core_router import get_session_service as _get_session_service
    return _get_session_service()


def get_region_segmenter():
    """region_router에서 영역 분할 서비스 가져오기"""
    from .region_router import get_region_segmenter as _get_region_segmenter
    return _get_region_segmenter()


# ==================== GD&T 파싱 API ====================

@router.post("/gdt/{session_id}/parse", response_model=GDTParsingResult)
async def parse_gdt(
    session_id: str,
    config: Optional[GDTParsingConfig] = None,
) -> GDTParsingResult:
    """
    GD&T (기하공차) 파싱 실행

    도면에서 다음 요소를 검출:
    - Feature Control Frame (FCF): 기하공차 프레임
    - 14가지 기하 특성 (직진도, 평면도, 원통도 등)
    - 데이텀 참조 (A, B, C 등)
    - 재료 조건 수정자 (MMC, LMC, RFS)
    """
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    image_path = session.get("file_path")
    if not image_path:
        raise HTTPException(status_code=400, detail="이미지 파일이 없습니다")

    ocr_results = session.get("ocr_results")

    try:
        result = await gdt_parser.parse(
            session_id=session_id,
            image_path=image_path,
            config=config,
            ocr_results=ocr_results,
        )

        session_service.update_session(session_id, {
            "gdt_fcf_list": [fcf.model_dump() for fcf in result.fcf_list],
            "gdt_datums": [d.model_dump() for d in result.datums],
            "gdt_fcf_count": result.total_fcf,
            "gdt_datum_count": result.total_datums,
        })

        return result

    except Exception as e:
        logger.error(f"GD&T 파싱 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gdt/{session_id}", response_model=GDTListResponse)
async def get_gdt(session_id: str) -> GDTListResponse:
    """세션의 GD&T 결과 조회"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    fcf_list = gdt_parser.get_fcf_list(session_id)
    datums = gdt_parser.get_datums(session_id)

    return GDTListResponse(
        session_id=session_id,
        fcf_list=fcf_list,
        datums=datums,
        total_fcf=len(fcf_list),
        total_datums=len(datums),
    )


@router.get("/gdt/{session_id}/fcf/{fcf_id}", response_model=FeatureControlFrame)
async def get_fcf(session_id: str, fcf_id: str) -> FeatureControlFrame:
    """특정 FCF 조회"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    fcf = gdt_parser.get_fcf(session_id, fcf_id)
    if not fcf:
        raise HTTPException(status_code=404, detail="FCF를 찾을 수 없습니다")

    return fcf


@router.put("/gdt/{session_id}/fcf/{fcf_id}", response_model=FeatureControlFrame)
async def update_fcf(
    session_id: str,
    fcf_id: str,
    update: FCFUpdate,
) -> FeatureControlFrame:
    """FCF 업데이트"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    update.fcf_id = fcf_id

    updated = gdt_parser.update_fcf(session_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="FCF를 찾을 수 없습니다")

    return updated


@router.put("/gdt/{session_id}/fcf/bulk")
async def bulk_update_fcf(
    session_id: str,
    bulk_update: BulkFCFUpdate,
) -> Dict[str, Any]:
    """일괄 FCF 업데이트"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    results = []
    for update in bulk_update.updates:
        updated = gdt_parser.update_fcf(session_id, update)
        results.append({
            "fcf_id": update.fcf_id,
            "updated": updated is not None,
        })

    return {
        "session_id": session_id,
        "results": results,
        "updated_count": sum(1 for r in results if r["updated"]),
    }


@router.post("/gdt/{session_id}/fcf/add", response_model=FeatureControlFrame)
async def add_manual_fcf(
    session_id: str,
    manual_fcf: ManualFCF,
) -> FeatureControlFrame:
    """수동 FCF 추가"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

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

    fcf = gdt_parser.add_fcf(
        session_id=session_id,
        manual_fcf=manual_fcf,
        image_width=image_width,
        image_height=image_height,
    )

    return fcf


@router.delete("/gdt/{session_id}/fcf/{fcf_id}")
async def delete_fcf(session_id: str, fcf_id: str) -> Dict[str, Any]:
    """FCF 삭제"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    deleted = gdt_parser.delete_fcf(session_id, fcf_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="FCF를 찾을 수 없습니다")

    return {"deleted": True, "fcf_id": fcf_id}


@router.post("/gdt/{session_id}/datum/add", response_model=DatumFeature)
async def add_manual_datum(
    session_id: str,
    manual_datum: ManualDatum,
) -> DatumFeature:
    """수동 데이텀 추가"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

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

    datum = gdt_parser.add_datum(
        session_id=session_id,
        manual_datum=manual_datum,
        image_width=image_width,
        image_height=image_height,
    )

    return datum


@router.delete("/gdt/{session_id}/datum/{datum_id}")
async def delete_datum(session_id: str, datum_id: str) -> Dict[str, Any]:
    """데이텀 삭제"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    deleted = gdt_parser.delete_datum(session_id, datum_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="데이텀을 찾을 수 없습니다")

    return {"deleted": True, "datum_id": datum_id}


@router.get("/gdt/{session_id}/summary", response_model=GDTSummary)
async def get_gdt_summary(session_id: str) -> GDTSummary:
    """GD&T 요약 정보 조회"""
    session_service = get_session_service()
    gdt_parser = get_gdt_parser()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    summary = gdt_parser.get_summary(session_id)
    return summary


# ==================== 표제란 OCR API ====================

@router.post("/title-block/{session_id}/extract")
async def extract_title_block(session_id: str) -> Dict[str, Any]:
    """
    표제란 OCR 실행

    도면의 우하단 표제란 영역을 검출하고 메타데이터를 추출합니다:
    - 도면번호, 리비전, 재질, 작성자, 작성일, 스케일 등
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
        config = RegionSegmentationConfig(
            detect_title_block=True,
            detect_bom_table=False,
            detect_legend=False,
            detect_notes=False,
            detect_detail_views=False,
        )

        seg_result = await segmenter.segment(
            session_id=session_id,
            image_path=image_path,
            config=config,
        )

        title_block_region = None
        for region in seg_result.regions:
            if region.region_type == RegionType.TITLE_BLOCK:
                title_block_region = region
                break

        if not title_block_region:
            return {
                "success": False,
                "message": "표제란을 찾을 수 없습니다",
                "title_block": None,
            }

        process_result = await segmenter.process_region(
            session_id=session_id,
            region_id=title_block_region.id,
            image_path=image_path,
        )

        title_block_data = TitleBlockData(
            raw_text=process_result.ocr_text,
            **(process_result.metadata or {})
        )

        session_service.update_session(session_id, {
            "title_block": title_block_data.model_dump(),
            "title_block_region_id": title_block_region.id,
        })

        return {
            "success": True,
            "message": "표제란 추출 완료",
            "title_block": title_block_data.model_dump(),
            "region": title_block_region.model_dump(),
        }

    except Exception as e:
        logger.error(f"표제란 OCR 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"표제란 OCR 실패: {str(e)}")


@router.get("/title-block/{session_id}")
async def get_title_block(session_id: str) -> Dict[str, Any]:
    """표제란 정보 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    title_block = session.get("title_block")
    if not title_block:
        return {
            "success": False,
            "message": "표제란 정보가 없습니다. 먼저 추출을 실행하세요.",
            "title_block": None,
        }

    return {
        "success": True,
        "title_block": title_block,
    }


@router.put("/title-block/{session_id}")
async def update_title_block(session_id: str, update: Dict[str, Any]) -> Dict[str, Any]:
    """표제란 정보 수동 수정"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    current = session.get("title_block", {})
    updated = {**current, **update}

    session_service.update_session(session_id, {"title_block": updated})

    return {
        "success": True,
        "title_block": updated,
    }
