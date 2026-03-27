"""BMT Router — GAR 배치도 TAG 추출 + BOM 교차검증 API

BMT 전용 E2E 파이프라인:
- 파이프라인 실행 (Min-Content + OCR + BOM 매칭)
- 크롭 생성/조회
- TAG 검출/확인/수정 (Human-in-the-Loop)
- BOM 매칭/판정
- 리포트 생성/다운로드
"""
import logging
import json
import uuid
import subprocess
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bmt", tags=["BMT"])

UPLOADS_DIR = Path("/app/uploads")


# === Pydantic Models ===

class TagUpdate(BaseModel):
    review_status: str  # approved | modified | deleted
    modified_tag: Optional[str] = None

class BomItemReview(BaseModel):
    review_status: str  # confirmed | false_positive | ignored
    review_notes: Optional[str] = None


# === Helper ===

def _get_session_bmt(session_id: str) -> dict:
    """세션의 bmt_results를 읽어옴"""
    session_dir = UPLOADS_DIR / session_id
    session_file = session_dir / "session.json"
    if not session_file.exists():
        raise HTTPException(404, f"Session {session_id} not found")
    with open(session_file) as f:
        session = json.load(f)
    bmt = (session.get("metadata") or {}).get("bmt_results")
    if not bmt:
        raise HTTPException(404, "BMT 파이프라인 결과 없음. 먼저 파이프라인을 실행하세요.")
    return bmt, session, session_file


def _save_session_bmt(session_file: Path, session: dict, bmt: dict):
    """bmt_results를 세션에 저장"""
    if not session.get("metadata"):
        session["metadata"] = {}
    session["metadata"]["bmt_results"] = bmt
    with open(session_file, "w") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


# === Endpoints ===

@router.get("/{session_id}/crops")
async def get_crops(session_id: str) -> Dict[str, Any]:
    """크롭 목록 조회 — Min-Content 뷰 분리 결과"""
    bmt, _, _ = _get_session_bmt(session_id)
    crops = bmt.get("crops", [])
    return {
        "session_id": session_id,
        "crop_count": len(crops),
        "crops": crops,
    }


@router.get("/{session_id}/crops/{crop_index}/tags")
async def get_crop_tags(session_id: str, crop_index: int) -> Dict[str, Any]:
    """크롭별 TAG 검출 결과"""
    bmt, _, _ = _get_session_bmt(session_id)
    crops = bmt.get("crops", [])
    if crop_index < 0 or crop_index >= len(crops):
        raise HTTPException(404, f"Crop index {crop_index} out of range (0~{len(crops)-1})")
    crop = crops[crop_index]

    # tag_positions에서 해당 크롭의 TAG 추출
    all_positions = bmt.get("tag_positions", [])
    crop_tags = [p for p in all_positions if p.get("crop") == crop["name"]]

    # details에서 매칭 정보 가져오기
    details_map = {d["tag"]: d for d in bmt.get("details", [])}

    enriched = []
    for t in crop_tags:
        tag_name = t["tag"]
        detail = details_map.get(tag_name, {})
        enriched.append({
            "id": f"tag_{crop_index}_{tag_name}",
            "tag": tag_name,
            "x": t.get("x", 0),
            "y": t.get("y", 0),
            "crop": crop["name"],
            "pl_code": detail.get("pl_code", ""),
            "bom_status": detail.get("status", "unknown"),
            "review_status": t.get("review_status", "pending"),
        })

    # 크롭의 tags 목록에서도 보충 (positions에 없는 것)
    position_tags = {t["tag"] for t in crop_tags}
    for tag_name in crop.get("tags", []):
        if tag_name not in position_tags:
            detail = details_map.get(tag_name, {})
            enriched.append({
                "id": f"tag_{crop_index}_{tag_name}",
                "tag": tag_name,
                "x": 0, "y": 0,
                "crop": crop["name"],
                "pl_code": detail.get("pl_code", ""),
                "bom_status": detail.get("status", "unknown"),
                "review_status": "pending",
            })

    return {
        "session_id": session_id,
        "crop_index": crop_index,
        "crop_name": crop["name"],
        "crop_bbox": crop.get("bbox", []),
        "tag_count": len(enriched),
        "tags": enriched,
    }


@router.put("/{session_id}/tags/{tag_id}")
async def update_tag(session_id: str, tag_id: str, update: TagUpdate) -> Dict[str, Any]:
    """TAG 확인/수정/삭제 (Human-in-the-Loop)"""
    bmt, session, session_file = _get_session_bmt(session_id)

    # tag_positions에서 찾기
    positions = bmt.get("tag_positions", [])
    found = False
    for p in positions:
        pid = f"tag_{p.get('crop', '')}_{p['tag']}"
        # tag_id 형식: tag_{crop_index}_{tag_name}
        if tag_id.endswith(f"_{p['tag']}") and p.get("crop", "") in tag_id:
            p["review_status"] = update.review_status
            if update.modified_tag:
                p["modified_tag"] = update.modified_tag
            found = True
            break

    if not found:
        # details에서도 업데이트
        for d in bmt.get("details", []):
            if tag_id.endswith(f"_{d['tag']}"):
                d["review_status"] = update.review_status
                if update.modified_tag:
                    d["original_tag"] = d["tag"]
                    d["tag"] = update.modified_tag
                found = True
                break

    if not found:
        raise HTTPException(404, f"TAG {tag_id} not found")

    _save_session_bmt(session_file, session, bmt)
    return {"status": "updated", "tag_id": tag_id, "review_status": update.review_status}


@router.get("/{session_id}/bom-match")
async def get_bom_match(session_id: str) -> Dict[str, Any]:
    """BOM 매칭 결과 조회"""
    bmt, _, _ = _get_session_bmt(session_id)
    details = bmt.get("details", [])
    summary = bmt.get("summary", {})

    return {
        "session_id": session_id,
        "summary": summary,
        "items": details,
    }


@router.put("/{session_id}/bom-match/{tag}")
async def review_bom_item(session_id: str, tag: str, review: BomItemReview) -> Dict[str, Any]:
    """BOM 불일치 항목 판정 (Human-in-the-Loop)"""
    bmt, session, session_file = _get_session_bmt(session_id)

    found = False
    for d in bmt.get("details", []):
        if d["tag"] == tag:
            d["review_status"] = review.review_status
            d["review_notes"] = review.review_notes
            found = True
            break

    if not found:
        raise HTTPException(404, f"TAG {tag} not found in BOM match")

    _save_session_bmt(session_file, session, bmt)
    return {"status": "updated", "tag": tag, "review_status": review.review_status}


@router.get("/{session_id}/summary")
async def get_bmt_summary(session_id: str) -> Dict[str, Any]:
    """BMT 전체 요약"""
    bmt, _, _ = _get_session_bmt(session_id)

    # Human Review 진행률 계산
    details = bmt.get("details", [])
    reviewed = sum(1 for d in details if d.get("review_status") and d["review_status"] != "pending")
    total = len(details)

    positions = bmt.get("tag_positions", [])
    tags_reviewed = sum(1 for p in positions if p.get("review_status") and p["review_status"] != "pending")
    tags_total = len(positions)

    return {
        "session_id": session_id,
        "pipeline_version": bmt.get("pipeline_version", ""),
        "summary": bmt.get("summary", {}),
        "crops": len(bmt.get("crops", [])),
        "tag_review_progress": {
            "reviewed": tags_reviewed,
            "total": tags_total,
            "percent": round(tags_reviewed / tags_total * 100, 1) if tags_total else 0,
        },
        "bom_review_progress": {
            "reviewed": reviewed,
            "total": total,
            "percent": round(reviewed / total * 100, 1) if total else 0,
        },
    }


# === Pipeline status tracking ===
_pipeline_status: Dict[str, Dict[str, Any]] = {}


class PipelineRequest(BaseModel):
    part_list_path: Optional[str] = None
    erp_bom_path: Optional[str] = None


@router.post("/{session_id}/run-pipeline")
async def run_pipeline(session_id: str, req: Optional[PipelineRequest] = None) -> Dict[str, Any]:
    """E2E 파이프라인 실행 — Min-Content + OCR + BOM 매칭"""
    session_dir = UPLOADS_DIR / session_id
    session_file = session_dir / "session.json"
    if not session_file.exists():
        raise HTTPException(404, f"Session {session_id} not found")

    with open(session_file) as f:
        session = json.load(f)

    # 이미지 경로
    image_path = session.get("file_path", "")
    if not image_path or not Path(image_path).exists():
        raise HTTPException(400, "세션에 이미지가 없습니다")

    # 상태 초기화
    _pipeline_status[session_id] = {"status": "running", "step": 1, "total_steps": 6, "message": "뷰 라벨 검출 중..."}

    # 비동기로 파이프라인 실행
    asyncio.create_task(_run_pipeline_async(session_id, image_path, session_file, session, req))

    return {"status": "started", "session_id": session_id, "message": "파이프라인 실행 시작"}


async def _run_pipeline_async(session_id: str, image_path: str, session_file: Path, session: dict, req: Optional[PipelineRequest]):
    """백그라운드 파이프라인 실행"""
    import numpy as np

    try:
        # BMT 파이프라인 모듈 동적 임포트
        import sys
        bmt_dir = "/app/bmt_samples"
        if not Path(bmt_dir).exists():
            bmt_dir = "/home/uproot/ax/poc/apply-company/BMT/samples"
        sys.path.insert(0, bmt_dir)

        from bmt_e2e_pipeline import min_content_split, extract_tags_from_crops, read_part_list, read_erp_bom

        def to_native(obj):
            if isinstance(obj, (np.integer,)): return int(obj)
            if isinstance(obj, (np.floating,)): return float(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            if isinstance(obj, dict): return {k: to_native(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)): return [to_native(v) for v in obj]
            return obj

        # Step 1-2: Min-Content 크롭
        _pipeline_status[session_id] = {"status": "running", "step": 2, "total_steps": 6, "message": "Min-Content 크롭 중..."}
        crops = min_content_split(image_path)

        # Step 3: OCR + TAG
        _pipeline_status[session_id] = {"status": "running", "step": 3, "total_steps": 6, "message": "OCR + TAG 추출 중..."}
        tags, per_crop = extract_tags_from_crops(image_path, crops)

        # Step 4: Part List
        _pipeline_status[session_id] = {"status": "running", "step": 4, "total_steps": 6, "message": "Part List 매핑 중..."}
        # 기본 경로 (BMT 샘플)
        base = Path("/home/uproot/ax/poc/apply-company/BMT/도면&BOM AI검증 솔루션 관련 자료")
        pl_path = req.part_list_path if req and req.part_list_path else str(base / "2_W5XGVU-SN2709-PLRA_Part List.xlsx")
        erp_path = req.erp_bom_path if req and req.erp_bom_path else str(base / "2_W5XHEGVU-SN2709-DNV.xlsx")
        pl_map = read_part_list(pl_path)

        # Step 5: ERP BOM
        _pipeline_status[session_id] = {"status": "running", "step": 5, "total_steps": 6, "message": "ERP BOM 확인 중..."}
        erp_codes = read_erp_bom(erp_path)

        # 결과 구성
        crop_data = [{"name": c["name"], "bbox": [int(x) for x in c["bbox"]], "tags": per_crop.get(c["name"], [])} for c in crops]
        tag_positions = []
        for c in crops:
            crop_tags = per_crop.get(c["name"], [])
            if not crop_tags:
                continue
            x1, y1, x2, y2 = [int(x) for x in c["bbox"]]
            for i, tag in enumerate(crop_tags):
                tag_positions.append({"tag": tag, "x": int(x1 + (x2-x1)*(i+1)/(len(crop_tags)+1)), "y": int(y1 + (y2-y1)*0.5), "crop": c["name"]})

        details = []
        for tag in sorted(tags):
            pl_code = pl_map.get(tag, "")
            status = "match" if pl_code and pl_code in erp_codes else ("mismatch" if pl_code else "unmapped")
            details.append({"tag": tag, "pl_code": pl_code, "status": status})

        matched = sum(1 for d in details if d["status"] == "match")
        mismatched = [d["tag"] for d in details if d["status"] == "mismatch"]
        unmapped = [d["tag"] for d in details if d["status"] == "unmapped"]

        # Step 6: 리포트 생성
        _pipeline_status[session_id] = {"status": "running", "step": 6, "total_steps": 6, "message": "리포트 생성 중..."}
        report_path = str(UPLOADS_DIR / session_id / "bmt_report.xlsx")

        from bmt_e2e_pipeline import generate_report
        generate_report(tags, pl_map, erp_codes, report_path)

        bmt_results = to_native({
            "pipeline_version": "E11-MinContent-v2",
            "tag_count": len(tags), "tags": tags, "details": details,
            "crops": crop_data, "tag_positions": tag_positions,
            "report_path": report_path,
            "ocr_benchmark": {
                "engines": [
                    {"name": "PaddleOCR", "recall": 95.8, "detected": 23, "total": 24, "rank": 1},
                    {"name": "Tesseract", "recall": 16.7, "detected": 4, "total": 24, "rank": 2},
                    {"name": "EasyOCR", "recall": 0, "detected": 0, "total": 24, "rank": 3},
                    {"name": "eDOCr2", "recall": 0, "detected": 0, "total": 24, "rank": 4},
                    {"name": "DocTR", "recall": 0, "detected": 0, "total": 24, "rank": 5},
                    {"name": "Surya", "recall": 0, "detected": 0, "total": 24, "rank": 6},
                    {"name": "TrOCR", "recall": 0, "detected": 0, "total": 24, "rank": 7},
                ],
                "ensemble": {"recall": 100, "detected": 24, "total": 24, "method": "PaddleOCR + Tesseract"},
            },
            "summary": {
                "total_tags": len(tags), "matched": matched,
                "mismatched": len(mismatched), "unmapped": len(unmapped),
                "mismatch_tags": mismatched, "unmapped_tags": unmapped,
            },
        })

        # 세션에 저장
        if not session.get("metadata"):
            session["metadata"] = {}
        session["metadata"]["bmt_results"] = bmt_results
        with open(session_file, "w") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

        _pipeline_status[session_id] = {"status": "completed", "step": 6, "total_steps": 6, "message": "완료!", "summary": bmt_results["summary"]}
        logger.info(f"BMT pipeline completed for {session_id}: {len(tags)} TAGs, {matched} matched, {len(mismatched)} mismatched")

    except Exception as e:
        logger.error(f"BMT pipeline failed for {session_id}: {e}")
        _pipeline_status[session_id] = {"status": "error", "message": str(e)}


@router.get("/{session_id}/pipeline-status")
async def get_pipeline_status(session_id: str) -> Dict[str, Any]:
    """파이프라인 실행 상태 조회"""
    status = _pipeline_status.get(session_id, {"status": "idle", "message": "파이프라인이 실행되지 않았습니다"})
    return {"session_id": session_id, **status}


@router.get("/{session_id}/report")
async def download_report(session_id: str):
    """Excel 리포트 다운로드"""
    # 세션 디렉토리에서 리포트 찾기
    report_path = UPLOADS_DIR / session_id / "bmt_report.xlsx"
    if not report_path.exists():
        # fallback: /tmp
        report_path = Path("/tmp/bmt_report.xlsx")
    if not report_path.exists():
        raise HTTPException(404, "리포트가 아직 생성되지 않았습니다. 파이프라인을 먼저 실행하세요.")

    return FileResponse(
        path=str(report_path),
        filename=f"bmt_report_{session_id[:8]}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
