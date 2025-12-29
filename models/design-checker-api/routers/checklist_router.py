"""
Checklist Router - 체크리스트 관리 엔드포인트
/api/v1/checklist 관련 엔드포인트
"""
import os
import logging
from typing import List
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from schemas import ProcessResponse
from excel_parser import excel_parser, create_excel_template, ChecklistRule, OPENPYXL_AVAILABLE
from bwms_rules import bwms_checker
from rule_loader import rule_loader, CATEGORIES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/checklist", tags=["checklist"])


def _reload_bwms_rules_from_checklist(rules: List[ChecklistRule]) -> int:
    """체크리스트 규칙을 BWMS checker에 로드"""
    if not hasattr(bwms_checker, '_dynamic_rules'):
        bwms_checker._dynamic_rules = {}

    loaded_count = 0
    for rule in rules:
        rule_dict = {
            "rule_id": rule.rule_id,
            "id": rule.rule_id,
            "name": rule.name,
            "name_en": rule.name_en or rule.name,
            "severity": rule.severity,
            "check_type": rule.check_type,
            "category": rule.category,
            "equipment": rule.equipment,
            "condition": rule.condition,
            "condition_value": rule.condition_value,
            "description": rule.description,
            "suggestion": rule.suggestion,
            "auto_checkable": rule.auto_checkable,
            "standard": rule.standard,
            "product_type": rule.product_type
        }
        bwms_checker._dynamic_rules[rule.rule_id] = rule_dict
        loaded_count += 1

    logger.info(f"Loaded {loaded_count} rules from checklist")
    return loaded_count


@router.get("/template")
async def download_checklist_template():
    """
    체크리스트 템플릿 Excel 파일 다운로드
    """
    if not OPENPYXL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Excel 기능을 사용할 수 없습니다 (openpyxl 미설치)"
        )

    try:
        # 템플릿 생성
        template_path = create_excel_template()
        return FileResponse(
            path=template_path,
            filename="bwms_checklist_template.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        logger.error(f"Template creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_checklist(
    file: UploadFile = File(..., description="체크리스트 Excel 파일"),
    category: str = Form(default="common", description="카테고리 (common, ecs, hychlor, custom)"),
    product_type: str = Form(default="ALL", description="제품 타입 (ALL, ECS, HYCHLOR)")
):
    """
    체크리스트 Excel 파일 업로드 및 규칙 등록

    카테고리별 YAML 파일로 저장됩니다.
    """
    if not OPENPYXL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Excel 기능을 사용할 수 없습니다 (openpyxl 미설치)"
        )

    # 카테고리 검증
    if category not in CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {category}. Must be one of {list(CATEGORIES.keys())}"
        )

    try:
        # 파일 저장
        content = await file.read()

        # 임시 파일로 저장 후 파싱
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Excel 파싱
            rules, errors = excel_parser.parse_checklist(tmp_path)

            if errors:
                logger.warning(f"Parse warnings: {errors}")

            if not rules:
                return ProcessResponse(
                    success=False,
                    data={"errors": errors},
                    error="규칙을 파싱할 수 없습니다"
                )

            # 규칙을 딕셔너리 리스트로 변환
            rules_dicts = []
            for rule in rules:
                rule_dict = {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "name_en": rule.name_en or rule.name,
                    "severity": rule.severity,
                    "check_type": rule.check_type,
                    "category": rule.category,
                    "equipment": rule.equipment,
                    "condition": rule.condition,
                    "condition_value": rule.condition_value,
                    "description": rule.description,
                    "suggestion": rule.suggestion,
                    "auto_checkable": rule.auto_checkable,
                    "standard": rule.standard,
                    "product_type": product_type  # 폼에서 받은 값 사용
                }
                rules_dicts.append(rule_dict)

            # 카테고리 폴더에 YAML로 저장
            filename = f"{category}_rules_{file.filename.replace('.xlsx', '')}.yaml"
            if not filename.endswith('.yaml'):
                filename = f"{category}_rules.yaml"

            metadata = {
                "original_file": file.filename,
                "product_type": product_type
            }

            saved_path = rule_loader.save_rules(
                rules=rules_dicts,
                category=category,
                filename=filename,
                metadata=metadata
            )

            # BWMS checker에도 로드
            loaded_count = _reload_bwms_rules_from_checklist(rules)

            return ProcessResponse(
                success=True,
                data={
                    "rules_loaded": loaded_count,
                    "rules": [
                        {
                            "rule_id": r.rule_id,
                            "name": r.name,
                            "severity": r.severity,
                            "check_type": r.check_type,
                            "auto_checkable": r.auto_checkable
                        }
                        for r in rules
                    ],
                    "warnings": errors if errors else None,
                    "saved_to": saved_path,
                    "category": category,
                    "product_type": product_type
                }
            )

        finally:
            # 임시 파일 삭제
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.get("/files")
async def list_checklist_files():
    """
    업로드된 체크리스트 파일 목록 조회

    NOTE: 이제 rule_loader를 통해 관리됩니다.
    """
    try:
        files = rule_loader.list_files()
        return ProcessResponse(
            success=True,
            data={
                "files": files,
                "total": len(files)
            }
        )
    except Exception as e:
        logger.error(f"List files error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.post("/load")
async def load_checklist_file(
    filename: str = Form(..., description="로드할 파일명 (config 폴더 내)")
):
    """
    저장된 체크리스트 파일 로드

    규칙을 BWMS checker에 로드합니다.
    """
    try:
        # 전체 경로 또는 카테고리/파일명 형식 지원
        if "/" not in filename:
            # 파일 검색
            files = rule_loader.list_files()
            matching = [f for f in files if f["filename"] == filename]
            if not matching:
                return ProcessResponse(
                    success=False,
                    data={},
                    error=f"파일을 찾을 수 없습니다: {filename}"
                )
            profile_path = matching[0]["path"]
        else:
            profile_path = filename

        # 활성화 목록에 추가
        rule_loader._add_to_active(profile_path)

        # 규칙 다시 로드
        loaded_rules = rule_loader.load_all_rules()
        bwms_checker._dynamic_rules = dict(loaded_rules)

        return ProcessResponse(
            success=True,
            data={
                "loaded_file": profile_path,
                "rules_count": len(loaded_rules)
            }
        )

    except Exception as e:
        logger.error(f"Load file error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.get("/current")
async def get_current_checklist():
    """
    현재 로드된 체크리스트 규칙 조회
    """
    try:
        dynamic_rules = getattr(bwms_checker, '_dynamic_rules', {})

        rules_list = []
        for rule_id, rule in dynamic_rules.items():
            rules_list.append({
                "rule_id": rule_id,
                "name": rule.get("name", rule_id),
                "name_en": rule.get("name_en", ""),
                "severity": rule.get("severity", "warning"),
                "check_type": rule.get("check_type", ""),
                "equipment": rule.get("equipment", ""),
                "condition": rule.get("condition", ""),
                "auto_checkable": rule.get("auto_checkable", True),
                "product_type": rule.get("product_type", "ALL")
            })

        return ProcessResponse(
            success=True,
            data={
                "rules": rules_list,
                "total": len(rules_list),
                "source": "dynamic_rules"
            }
        )
    except Exception as e:
        logger.error(f"Get current checklist error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )
