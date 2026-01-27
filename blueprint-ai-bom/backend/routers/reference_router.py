"""참조 도면 라우터

사용자 정의 참조 도면 세트 관리 API
- 업로드 (ZIP)
- 조회 / 수정 / 삭제
- 이미지 개별 관리
"""

import os
import json
import shutil
import zipfile
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/reference-sets", tags=["Reference Sets"])

# 참조 도면 저장 경로
REFERENCE_SETS_DIR = Path("uploads/reference_sets")
REFERENCE_SETS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Pydantic 스키마
# ============================================================================

class ReferenceImage(BaseModel):
    """참조 이미지 정보"""
    filename: str
    class_name: str
    file_path: str
    size_bytes: int


class ReferenceSet(BaseModel):
    """참조 도면 세트"""
    id: str
    name: str
    description: Optional[str] = None
    image_count: int
    created_at: str
    updated_at: str
    is_builtin: bool = False


class ReferenceSetDetail(ReferenceSet):
    """참조 도면 세트 상세"""
    images: List[ReferenceImage]


class CreateReferenceSetRequest(BaseModel):
    """참조 세트 생성 요청 (메타데이터)"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class UpdateReferenceSetRequest(BaseModel):
    """참조 세트 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


# ============================================================================
# 헬퍼 함수
# ============================================================================

def _get_metadata_path(set_id: str) -> Path:
    """메타데이터 파일 경로"""
    return REFERENCE_SETS_DIR / set_id / "metadata.json"


def _load_metadata(set_id: str) -> Optional[Dict[str, Any]]:
    """메타데이터 로드"""
    path = _get_metadata_path(set_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_metadata(set_id: str, metadata: Dict[str, Any]):
    """메타데이터 저장"""
    path = _get_metadata_path(set_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def _get_images_in_set(set_id: str) -> List[ReferenceImage]:
    """세트 내 이미지 목록"""
    set_dir = REFERENCE_SETS_DIR / set_id
    if not set_dir.exists():
        return []

    images = []
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

    for file_path in set_dir.iterdir():
        if file_path.suffix.lower() in image_extensions:
            # 클래스명 = 파일명 (확장자 제외)
            class_name = file_path.stem
            images.append(ReferenceImage(
                filename=file_path.name,
                class_name=class_name,
                file_path=str(file_path),
                size_bytes=file_path.stat().st_size
            ))

    return sorted(images, key=lambda x: x.class_name)


def _get_builtin_sets() -> List[ReferenceSet]:
    """기본 제공 세트 목록"""
    return [
        ReferenceSet(
            id="electrical",
            name="전기 도면",
            description="전기 회로도, 배선도 심볼",
            image_count=0,  # 실제 개수는 class_examples에서 가져옴
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            is_builtin=True
        ),
        ReferenceSet(
            id="pid",
            name="P&ID",
            description="배관 계장도 심볼",
            image_count=0,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            is_builtin=True
        ),
        ReferenceSet(
            id="sld",
            name="SLD",
            description="단선 결선도 심볼",
            image_count=0,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            is_builtin=True
        ),
        ReferenceSet(
            id="mechanical",
            name="기계 도면",
            description="기계 부품도 심볼",
            image_count=0,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            is_builtin=True
        ),
    ]


# ============================================================================
# API 엔드포인트
# ============================================================================

@router.get("", response_model=List[ReferenceSet])
async def list_reference_sets(include_builtin: bool = True):
    """참조 도면 세트 목록 조회

    Args:
        include_builtin: 기본 제공 세트 포함 여부

    Returns:
        참조 세트 목록
    """
    sets = []

    # 기본 제공 세트
    if include_builtin:
        sets.extend(_get_builtin_sets())

    # 사용자 정의 세트
    if REFERENCE_SETS_DIR.exists():
        for set_dir in REFERENCE_SETS_DIR.iterdir():
            if set_dir.is_dir():
                metadata = _load_metadata(set_dir.name)
                if metadata:
                    images = _get_images_in_set(set_dir.name)
                    sets.append(ReferenceSet(
                        id=set_dir.name,
                        name=metadata.get("name", set_dir.name),
                        description=metadata.get("description"),
                        image_count=len(images),
                        created_at=metadata.get("created_at", ""),
                        updated_at=metadata.get("updated_at", ""),
                        is_builtin=False
                    ))

    return sets


@router.get("/{set_id}", response_model=ReferenceSetDetail)
async def get_reference_set(set_id: str):
    """참조 도면 세트 상세 조회

    Args:
        set_id: 세트 ID

    Returns:
        세트 상세 정보 (이미지 목록 포함)
    """
    # 기본 제공 세트인 경우
    builtin_sets = {s.id: s for s in _get_builtin_sets()}
    if set_id in builtin_sets:
        builtin = builtin_sets[set_id]
        return ReferenceSetDetail(
            id=builtin.id,
            name=builtin.name,
            description=builtin.description,
            image_count=builtin.image_count,
            created_at=builtin.created_at,
            updated_at=builtin.updated_at,
            is_builtin=True,
            images=[]  # 기본 세트는 class_examples API 사용
        )

    # 사용자 정의 세트
    metadata = _load_metadata(set_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"참조 세트를 찾을 수 없습니다: {set_id}")

    images = _get_images_in_set(set_id)

    return ReferenceSetDetail(
        id=set_id,
        name=metadata.get("name", set_id),
        description=metadata.get("description"),
        image_count=len(images),
        created_at=metadata.get("created_at", ""),
        updated_at=metadata.get("updated_at", ""),
        is_builtin=False,
        images=images
    )


@router.post("", response_model=ReferenceSet)
async def create_reference_set(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """참조 도면 세트 생성 (ZIP 업로드)

    ZIP 파일 내 이미지 파일명이 클래스명이 됩니다.
    예: valve_gate.png -> 클래스명: valve_gate

    Args:
        name: 세트 이름
        description: 세트 설명
        file: ZIP 파일

    Returns:
        생성된 세트 정보
    """
    # ZIP 파일 검증
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="ZIP 파일만 업로드 가능합니다")

    # 새 세트 ID 생성
    set_id = str(uuid.uuid4())[:8]
    set_dir = REFERENCE_SETS_DIR / set_id
    set_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ZIP 파일 저장 및 압축 해제
        zip_path = set_dir / "temp.zip"
        with open(zip_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 압축 해제
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        extracted_count = 0

        with zipfile.ZipFile(zip_path, "r") as zf:
            for zip_info in zf.infolist():
                if zip_info.is_dir():
                    continue

                filename = Path(zip_info.filename).name
                ext = Path(filename).suffix.lower()

                if ext in image_extensions:
                    # 이미지 파일만 추출
                    target_path = set_dir / filename
                    with zf.open(zip_info) as src, open(target_path, "wb") as dst:
                        dst.write(src.read())
                    extracted_count += 1

        # 임시 ZIP 삭제
        zip_path.unlink()

        if extracted_count == 0:
            shutil.rmtree(set_dir)
            raise HTTPException(status_code=400, detail="ZIP 파일 내 이미지가 없습니다")

        # 메타데이터 저장
        now = datetime.now().isoformat()
        metadata = {
            "name": name,
            "description": description,
            "created_at": now,
            "updated_at": now
        }
        _save_metadata(set_id, metadata)

        return ReferenceSet(
            id=set_id,
            name=name,
            description=description,
            image_count=extracted_count,
            created_at=now,
            updated_at=now,
            is_builtin=False
        )

    except zipfile.BadZipFile:
        shutil.rmtree(set_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="유효하지 않은 ZIP 파일입니다")
    except Exception as e:
        shutil.rmtree(set_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"세트 생성 실패: {str(e)}")


@router.put("/{set_id}", response_model=ReferenceSet)
async def update_reference_set(set_id: str, request: UpdateReferenceSetRequest):
    """참조 도면 세트 수정

    Args:
        set_id: 세트 ID
        request: 수정 요청

    Returns:
        수정된 세트 정보
    """
    # 기본 제공 세트는 수정 불가
    builtin_ids = {s.id for s in _get_builtin_sets()}
    if set_id in builtin_ids:
        raise HTTPException(status_code=400, detail="기본 제공 세트는 수정할 수 없습니다")

    metadata = _load_metadata(set_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"참조 세트를 찾을 수 없습니다: {set_id}")

    # 메타데이터 업데이트
    if request.name is not None:
        metadata["name"] = request.name
    if request.description is not None:
        metadata["description"] = request.description
    metadata["updated_at"] = datetime.now().isoformat()

    _save_metadata(set_id, metadata)

    images = _get_images_in_set(set_id)

    return ReferenceSet(
        id=set_id,
        name=metadata["name"],
        description=metadata.get("description"),
        image_count=len(images),
        created_at=metadata.get("created_at", ""),
        updated_at=metadata["updated_at"],
        is_builtin=False
    )


@router.delete("/{set_id}")
async def delete_reference_set(set_id: str):
    """참조 도면 세트 삭제

    Args:
        set_id: 세트 ID

    Returns:
        삭제 결과
    """
    # 기본 제공 세트는 삭제 불가
    builtin_ids = {s.id for s in _get_builtin_sets()}
    if set_id in builtin_ids:
        raise HTTPException(status_code=400, detail="기본 제공 세트는 삭제할 수 없습니다")

    set_dir = REFERENCE_SETS_DIR / set_id
    if not set_dir.exists():
        raise HTTPException(status_code=404, detail=f"참조 세트를 찾을 수 없습니다: {set_id}")

    shutil.rmtree(set_dir)

    return {"success": True, "message": f"세트가 삭제되었습니다: {set_id}"}


@router.post("/{set_id}/images")
async def add_image_to_set(
    set_id: str,
    class_name: str = Form(...),
    file: UploadFile = File(...)
):
    """세트에 이미지 추가

    Args:
        set_id: 세트 ID
        class_name: 클래스명
        file: 이미지 파일

    Returns:
        추가된 이미지 정보
    """
    # 기본 제공 세트는 수정 불가
    builtin_ids = {s.id for s in _get_builtin_sets()}
    if set_id in builtin_ids:
        raise HTTPException(status_code=400, detail="기본 제공 세트에는 이미지를 추가할 수 없습니다")

    set_dir = REFERENCE_SETS_DIR / set_id
    if not set_dir.exists():
        raise HTTPException(status_code=404, detail=f"참조 세트를 찾을 수 없습니다: {set_id}")

    # 파일 확장자 검증
    ext = Path(file.filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다")

    # 파일 저장 (클래스명 + 원본 확장자)
    filename = f"{class_name}{ext}"
    file_path = set_dir / filename

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 메타데이터 업데이트
    metadata = _load_metadata(set_id)
    if metadata:
        metadata["updated_at"] = datetime.now().isoformat()
        _save_metadata(set_id, metadata)

    return ReferenceImage(
        filename=filename,
        class_name=class_name,
        file_path=str(file_path),
        size_bytes=file_path.stat().st_size
    )


@router.delete("/{set_id}/images/{filename}")
async def delete_image_from_set(set_id: str, filename: str):
    """세트에서 이미지 삭제

    Args:
        set_id: 세트 ID
        filename: 파일명

    Returns:
        삭제 결과
    """
    # 기본 제공 세트는 수정 불가
    builtin_ids = {s.id for s in _get_builtin_sets()}
    if set_id in builtin_ids:
        raise HTTPException(status_code=400, detail="기본 제공 세트에서는 이미지를 삭제할 수 없습니다")

    file_path = REFERENCE_SETS_DIR / set_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"이미지를 찾을 수 없습니다: {filename}")

    file_path.unlink()

    # 메타데이터 업데이트
    metadata = _load_metadata(set_id)
    if metadata:
        metadata["updated_at"] = datetime.now().isoformat()
        _save_metadata(set_id, metadata)

    return {"success": True, "message": f"이미지가 삭제되었습니다: {filename}"}


@router.get("/{set_id}/images/{filename}")
async def get_image(set_id: str, filename: str):
    """이미지 파일 조회

    Args:
        set_id: 세트 ID
        filename: 파일명

    Returns:
        이미지 파일
    """
    file_path = REFERENCE_SETS_DIR / set_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"이미지를 찾을 수 없습니다: {filename}")

    return FileResponse(file_path)
