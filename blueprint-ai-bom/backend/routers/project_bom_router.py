"""Project BOM Router - BOM 계층 워크플로우 API

프로젝트 기반 BOM PDF 파싱, 계층 관리, 도면 매칭, 세션 일괄 생성
"""

import logging
import shutil
from typing import Optional, List, Dict
from pathlib import Path
from collections import defaultdict

from fastapi import APIRouter, HTTPException, UploadFile, File

from schemas.project import ProjectUpdate
from schemas.bom_item import (
    BOMHierarchyResponse,
    DrawingMatchRequest,
    DrawingMatchResult,
    SessionBatchCreateRequest,
    SessionBatchCreateResponse,
)
from services.project_service import get_project_service, ProjectService
from services.template_service import get_template_service, TemplateService
from services.bom_pdf_parser import BOMPDFParser
from services.drawing_matcher import DrawingMatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects-bom"])


def get_services():
    """서비스 의존성"""
    data_dir = Path("/app/data")
    return {
        "project_service": get_project_service(data_dir),
        "template_service": get_template_service(data_dir),
    }


@router.post("/{project_id}/import-bom")
async def import_bom_pdf(
    project_id: str,
    file: UploadFile = File(...),
):
    """BOM PDF 업로드 → 파싱 → 계층 구조 생성

    BOM PDF의 테이블을 추출하고 행 배경색으로 계층을 분류합니다.
    - PINK: Assembly (조립체)
    - BLUE: Subassembly (하위 조립체)
    - WHITE: Part (단품, 견적 대상)

    Args:
        project_id: 프로젝트 ID
        file: BOM PDF 파일

    Returns:
        파싱된 BOM 계층 데이터
    """
    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    # PDF 확장자 확인
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 지원합니다")

    # BOM PDF 저장
    project_dir = project_service.projects_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    bom_pdf_path = project_dir / "bom_source.pdf"
    content = await file.read()
    with open(bom_pdf_path, "wb") as f:
        f.write(content)

    # BOM PDF 파싱
    try:
        parser = BOMPDFParser()
        bom_data = parser.parse_bom_pdf(str(bom_pdf_path))
    except Exception as e:
        logger.error(f"BOM PDF 파싱 실패: {e}")
        raise HTTPException(status_code=500, detail=f"BOM PDF 파싱 실패: {str(e)}")

    # BOM 데이터 저장
    parser.save_bom_items(project_dir, bom_data)

    # 프로젝트 메타데이터 업데이트
    project_service.update_project(project_id, ProjectUpdate(
        bom_source=file.filename,
    ))
    # 통계 직접 업데이트 (schema 외 필드)
    proj = project_service.get_project(project_id)
    proj["bom_item_count"] = bom_data["total_items"]
    proj["quotation_item_count"] = bom_data["part_count"]
    project_service._save_project(project_id)

    logger.info(f"BOM PDF import 완료: {project_id} → {bom_data['total_items']}개 항목")

    return {
        "project_id": project_id,
        "source_file": file.filename,
        "total_items": bom_data["total_items"],
        "assembly_count": bom_data["assembly_count"],
        "subassembly_count": bom_data["subassembly_count"],
        "part_count": bom_data["part_count"],
        "items": bom_data["items"],
    }


@router.get("/{project_id}/bom-hierarchy", response_model=BOMHierarchyResponse)
async def get_bom_hierarchy(project_id: str):
    """BOM 계층 트리 조회

    Args:
        project_id: 프로젝트 ID

    Returns:
        BOM 계층 트리 + 통계
    """
    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    # BOM 데이터 로드
    project_dir = project_service.projects_dir / project_id
    parser = BOMPDFParser()
    bom_data = parser.load_bom_items(project_dir)

    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM 데이터가 없습니다. 먼저 import-bom을 실행하세요.")

    # bom_items.json이 리스트(직접 아이템 배열) 또는 dict 형태 모두 지원
    if isinstance(bom_data, list):
        bom_items = bom_data
        bom_source = project.get("bom_source", "")
        assembly_count = sum(1 for i in bom_items if i.get("level") == "assembly")
        subassembly_count = sum(1 for i in bom_items if i.get("level") == "subassembly")
        part_count = sum(1 for i in bom_items if i.get("level") == "part")
    else:
        bom_items = bom_data.get("items", [])
        bom_source = bom_data.get("source_file", "")
        assembly_count = bom_data.get("assembly_count", 0)
        subassembly_count = bom_data.get("subassembly_count", 0)
        part_count = bom_data.get("part_count", 0)

    return BOMHierarchyResponse(
        project_id=project_id,
        bom_source=bom_source,
        total_items=len(bom_items),
        assembly_count=assembly_count,
        subassembly_count=subassembly_count,
        part_count=part_count,
        items=bom_items,
        hierarchy=bom_data.get("hierarchy", []) if isinstance(bom_data, dict) else [],
    )


@router.post("/{project_id}/match-drawings", response_model=DrawingMatchResult)
async def match_drawings(
    project_id: str,
    request: DrawingMatchRequest,
):
    """도면번호 → PJT 폴더 매칭

    BOM 항목의 도면번호를 지정된 폴더에서 검색하여 매칭합니다.

    Args:
        project_id: 프로젝트 ID
        request: 도면 폴더 경로

    Returns:
        매칭 결과 (매칭 성공/실패 항목별)
    """
    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    # BOM 데이터 로드
    project_dir = project_service.projects_dir / project_id
    parser = BOMPDFParser()
    bom_data = parser.load_bom_items(project_dir)

    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM 데이터가 없습니다. 먼저 import-bom을 실행하세요.")

    # 도면 매칭
    folder_path = Path(request.drawing_folder)
    if not folder_path.exists():
        raise HTTPException(status_code=400, detail=f"도면 폴더를 찾을 수 없습니다: {request.drawing_folder}")

    matcher = DrawingMatcher()
    items = bom_data["items"]
    matched_items = matcher.match_drawings(items, request.drawing_folder)

    # BOM 데이터 업데이트 (매칭 결과 저장)
    bom_data["items"] = matched_items
    parser.save_bom_items(project_dir, bom_data)

    # 프로젝트에 drawing_folder 저장
    project_service.update_project(project_id, ProjectUpdate(
        drawing_folder=request.drawing_folder,
    ))

    summary = matcher.get_match_summary(matched_items)

    return DrawingMatchResult(
        project_id=project_id,
        total_items=summary["total_items"],
        matched_count=summary["matched_count"],
        unmatched_count=summary["unmatched_count"],
        items=matched_items,
    )


def _get_subtree_items(items: list, root_drawing_number: str) -> list:
    """특정 어셈블리의 하위 항목만 필터링

    BOM 계층에서 root_drawing_number에 해당하는 ASSY를 찾고,
    parent_item_no 체인을 따라 모든 자손 항목을 수집합니다.

    Args:
        items: 전체 BOM 항목 리스트
        root_drawing_number: 루트 어셈블리 도면번호

    Returns:
        해당 어셈블리의 모든 하위 항목 (루트 포함)
    """
    # 1. root item 찾기
    root_item = None
    for item in items:
        if item.get("drawing_number") == root_drawing_number:
            root_item = item
            break

    if not root_item:
        return []

    root_item_no = root_item.get("item_no")

    # 2. 모든 자손 item_no 수집 (BFS)
    subtree_item_nos = {root_item_no}
    queue = [root_item_no]

    while queue:
        current = queue.pop(0)
        for item in items:
            parent = item.get("parent_item_no")
            if parent == current and item.get("item_no") not in subtree_item_nos:
                subtree_item_nos.add(item.get("item_no"))
                queue.append(item.get("item_no"))

    # 3. 서브트리 항목 반환
    return [item for item in items if item.get("item_no") in subtree_item_nos]


@router.post("/{project_id}/create-sessions", response_model=SessionBatchCreateResponse)
async def create_sessions_from_bom(
    project_id: str,
    request: SessionBatchCreateRequest = None,
):
    """매칭된 도면 → 세션 일괄 생성

    WHITE(part) 항목 중 매칭된 도면이 있는 항목에 대해 세션을 생성합니다.
    각 세션에는 BOM 메타데이터(drawing_number, material, quantity 등)가 태깅됩니다.

    Args:
        project_id: 프로젝트 ID
        request: 세션 생성 옵션

    Returns:
        생성된 세션 목록
    """
    from routers.session_router import get_session_service
    import uuid

    if request is None:
        request = SessionBatchCreateRequest()

    services = get_services()
    project_service = services["project_service"]
    template_service = services["template_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    # 템플릿 조회 (이름으로 검색)
    template = None
    template_id = None
    if request.template_name:
        for t in template_service.list_templates():
            if t.get("name") == request.template_name:
                template_id = t.get("template_id")
                template = template_service.get_template(template_id)
                break
        if not template:
            logger.warning(f"템플릿을 찾을 수 없음: {request.template_name}, 기본값 사용")

    # 프로젝트 타입 기반 프리셋 (우선순위: 템플릿 > 프로젝트 default_features > 타입 프리셋)
    from services.project_service import get_default_features_for_type
    preset = get_default_features_for_type(project.get("project_type", "general"))

    if template:
        tmpl_drawing_type = template.get("drawing_type", preset["drawing_type"])
        tmpl_features = template.get("features", preset["features"])
    elif project.get("default_features"):
        tmpl_drawing_type = preset["drawing_type"]
        tmpl_features = project["default_features"]
    else:
        tmpl_drawing_type = preset["drawing_type"]
        tmpl_features = preset["features"]

    # BOM 데이터 로드
    project_dir = project_service.projects_dir / project_id
    bom_parser = BOMPDFParser()
    bom_data = bom_parser.load_bom_items(project_dir)

    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM 데이터가 없습니다. 먼저 import-bom을 실행하세요.")

    # 세션 서비스 가져오기
    try:
        session_service = get_session_service()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="세션 서비스가 초기화되지 않았습니다"
        )

    all_items = bom_data["items"]

    # 어셈블리 스코프 필터
    if request.root_drawing_number:
        all_items = _get_subtree_items(all_items, request.root_drawing_number)
        if not all_items:
            raise HTTPException(
                status_code=404,
                detail=f"어셈블리를 찾을 수 없습니다: {request.root_drawing_number}"
            )

    # WHITE(part) 항목만 필터
    part_items = [
        item for item in all_items
        if item.get("needs_quotation", False)
    ]

    # 도면번호 기준 중복 제거 및 수량 합산
    drawing_groups: Dict[str, list] = defaultdict(list)
    for item in part_items:
        dwg = item.get("drawing_number", "")
        if dwg:
            drawing_groups[dwg].append(item)

    created_sessions = []
    skipped = 0
    failed = 0

    for drawing_number, group_items in drawing_groups.items():
        # 이미 세션이 생성된 도면은 건너뛰기
        existing_session = next(
            (it.get("session_id") for it in group_items if it.get("session_id")),
            None,
        )
        if existing_session:
            skipped += len(group_items)
            continue

        # 대표 항목 선택 (matched_file 있는 것 우선)
        rep = next(
            (it for it in group_items if it.get("matched_file")),
            group_items[0],
        )
        matched_file = rep.get("matched_file")

        # 매칭된 파일이 없으면 건너뛰기
        if request.only_matched and not matched_file:
            skipped += len(group_items)
            continue

        # 수량 합산 및 item_no 목록 수집
        total_qty = sum(it.get("quantity", 1) for it in group_items)
        all_item_nos = [it.get("item_no", "") for it in group_items]

        try:
            session_id = str(uuid.uuid4())

            # 매칭된 도면 파일을 세션 디렉토리에 복사
            upload_dir = Path("/app/data")
            session_dir = upload_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            file_path = ""
            image_width, image_height = None, None

            if matched_file and Path(matched_file).exists():
                src_path = Path(matched_file)
                dest_path = session_dir / f"original{src_path.suffix}"
                shutil.copy2(str(src_path), str(dest_path))
                file_path = str(dest_path)

                # PDF → PNG 변환 (ML 모델은 이미지만 처리 가능)
                if src_path.suffix.lower() == ".pdf":
                    try:
                        import fitz
                        doc = fitz.open(str(dest_path))
                        page = doc[0]
                        # 300 DPI 렌더링 (OCR 정확도 향상)
                        mat = fitz.Matrix(300 / 72, 300 / 72)
                        pix = page.get_pixmap(matrix=mat)
                        png_path = session_dir / "original.png"
                        pix.save(str(png_path))
                        image_width, image_height = pix.width, pix.height
                        file_path = str(png_path)
                        doc.close()
                        logger.info(f"PDF→PNG 변환 완료: {drawing_number} ({image_width}x{image_height})")
                    except Exception as e:
                        logger.error(f"PDF→PNG 변환 실패: {drawing_number}: {e}")

                # 이미지인 경우 크기 추출
                elif src_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".tif"}:
                    try:
                        from PIL import Image
                        with Image.open(dest_path) as img:
                            image_width, image_height = img.size
                    except Exception:
                        pass

            # 소속 어셈블리 목록 수집 (공유 도면 → 복수 어셈블리)
            assembly_refs = []
            seen_assy = set()
            for it in group_items:
                assy_dwg = it.get("assembly_drawing_number")
                if assy_dwg and assy_dwg not in seen_assy:
                    seen_assy.add(assy_dwg)
                    assembly_refs.append({
                        "assembly": assy_dwg,
                        "item_no": it.get("item_no"),
                        "quantity": it.get("quantity", 1),
                    })

            # BOM 메타데이터 구성 (수량 합산, item_no 목록)
            metadata = {
                "drawing_number": drawing_number,
                "bom_item_no": all_item_nos[0] if len(all_item_nos) == 1 else ",".join(all_item_nos),
                "bom_item_nos": all_item_nos,
                "bom_level": rep.get("level", "part"),
                "material": rep.get("material", ""),
                "bom_quantity": total_qty,
                "bom_line_count": len(group_items),
                "bom_description": rep.get("description", ""),
                "quote_status": "pending",
                # 어셈블리 귀속 및 개정 정보
                "assembly_refs": assembly_refs,
                "bom_revision": rep.get("bom_revision"),
                "doc_revision": rep.get("doc_revision"),
                "part_no": rep.get("part_no"),
                "size": rep.get("size"),
                "remark": rep.get("remark"),
            }

            # 세션 생성 (템플릿 설정 적용)
            session = session_service.create_session(
                session_id=session_id,
                filename=Path(matched_file).name if matched_file else f"{drawing_number}.pdf",
                file_path=file_path,
                drawing_type=tmpl_drawing_type,
                image_width=image_width,
                image_height=image_height,
                features=tmpl_features,
                project_id=project_id,
                metadata=metadata,
            )

            # 템플릿 상세 설정 적용 (model_type, detection_params 등)
            if template_id:
                template_service.apply_template_to_session(template_id, session)

            # 그룹 내 모든 BOM 항목에 동일 세션 ID 기록
            for it in group_items:
                it["session_id"] = session_id

            created_sessions.append({
                "session_id": session_id,
                "drawing_number": drawing_number,
                "description": rep.get("description"),
                "material": rep.get("material"),
                "quantity": total_qty,
                "line_count": len(group_items),
                "filename": session.get("filename"),
            })

        except Exception as e:
            logger.error(f"세션 생성 실패 ({drawing_number}): {e}")
            failed += 1

    # BOM 데이터 업데이트 (세션 ID 저장)
    bom_parser.save_bom_items(project_dir, bom_data)

    # 프로젝트 통계 업데이트
    proj = project_service.get_project(project_id)
    proj["session_count"] = proj.get("session_count", 0) + len(created_sessions)
    project_service._save_project(project_id)

    message = f"{len(created_sessions)}개 세션 생성 완료"
    if template:
        message += f" (템플릿: {request.template_name})"
    if skipped > 0:
        message += f", {skipped}개 건너뜀"
    if failed > 0:
        message += f", {failed}개 실패"

    logger.info(f"세션 일괄 생성: {project_id} → {message}")

    return SessionBatchCreateResponse(
        project_id=project_id,
        created_count=len(created_sessions),
        skipped_count=skipped,
        failed_count=failed,
        sessions=created_sessions,
        message=message,
    )
