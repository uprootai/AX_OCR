"""
Rules Router - 규칙 관리 엔드포인트
/api/v1/rules 관련 엔드포인트
"""
import os
import logging
from typing import Optional

from fastapi import APIRouter, Form

from schemas import ProcessResponse
from constants import DESIGN_RULES
from bwms_rules import bwms_checker, BWMS_DESIGN_RULES
from rule_loader import rule_loader, CATEGORIES

logger = logging.getLogger(__name__)
API_PORT = int(os.getenv("DESIGN_CHECKER_PORT", "5019"))

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


@router.get("")
async def get_rules():
    """
    사용 가능한 설계 규칙 목록 조회
    """
    rules_list = []
    for rule_id, rule in DESIGN_RULES.items():
        rules_list.append({
            "id": rule_id,
            "name": rule["name"],
            "name_en": rule["name_en"],
            "description": rule["description"],
            "category": rule["category"].value,
            "severity": rule["severity"].value,
            "standard": rule["standard"]
        })

    return ProcessResponse(
        success=True,
        data={
            "rules": rules_list,
            "total": len(rules_list),
            "categories": list(set(r["category"] for r in rules_list)),
            "api_info": {
                "name": "design-checker",
                "version": "1.0.0",
                "base_url": f"http://localhost:{API_PORT}",
                "endpoints": [
                    "/api/v1/check",
                    "/api/v1/check/bwms",
                    "/api/v1/rules",
                    "/api/v1/rules/bwms"
                ]
            }
        }
    )


@router.get("/bwms")
async def get_bwms_rules():
    """
    BWMS 전용 규칙 목록 조회
    """
    bwms_rules = []
    for rule_id, rule in BWMS_DESIGN_RULES.items():
        bwms_rules.append({
            "id": rule_id,
            "name": rule["name"],
            "name_en": rule["name_en"],
            "description": rule["description"],
            "standard": rule.get("standard", "TECHCROSS BWMS"),
            "severity": rule.get("severity", "warning"),
            "auto_checkable": rule.get("auto_checkable", True)
        })

    # 동적 로드된 규칙 추가
    dynamic_rules = getattr(bwms_checker, '_dynamic_rules', {})
    for rule_id, rule in dynamic_rules.items():
        bwms_rules.append({
            "id": rule_id,
            "name": rule.get("name", rule_id),
            "name_en": rule.get("name_en", rule_id),
            "description": rule.get("description", ""),
            "standard": rule.get("standard", "TECHCROSS BWMS"),
            "severity": rule.get("severity", "warning"),
            "auto_checkable": rule.get("auto_checkable", True),
            "source": "dynamic"
        })

    return ProcessResponse(
        success=True,
        data={
            "rules": bwms_rules,
            "total": len(bwms_rules),
            "builtin_count": len(BWMS_DESIGN_RULES),
            "dynamic_count": len(dynamic_rules)
        }
    )


@router.get("/status")
async def get_rules_status():
    """
    규칙 상태 조회 (카테고리별 YAML 관리)
    """
    try:
        status = rule_loader.get_status()
        return ProcessResponse(
            success=True,
            data=status
        )
    except Exception as e:
        logger.error(f"Rules status error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.get("/files")
async def list_rule_files(category: Optional[str] = None):
    """
    규칙 파일 목록 조회
    """
    try:
        files = rule_loader.list_files(category)
        return ProcessResponse(
            success=True,
            data={
                "files": files,
                "total": len(files),
                "categories": list(CATEGORIES.keys())
            }
        )
    except Exception as e:
        logger.error(f"List files error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.post("/reload")
async def reload_rules():
    """
    YAML에서 규칙 다시 로드
    """
    try:
        loaded_rules = rule_loader.load_all_rules()

        # bwms_checker에 동적 규칙으로 로드
        if not hasattr(bwms_checker, '_dynamic_rules'):
            bwms_checker._dynamic_rules = {}

        bwms_checker._dynamic_rules.clear()
        for rule_id, rule_dict in loaded_rules.items():
            bwms_checker._dynamic_rules[rule_id] = rule_dict

        return ProcessResponse(
            success=True,
            data={
                "rules_loaded": len(loaded_rules),
                "message": f"{len(loaded_rules)}개 규칙이 로드되었습니다"
            }
        )
    except Exception as e:
        logger.error(f"Reload rules error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.post("/profile/activate")
async def activate_profile(profile_path: str = Form(..., description="활성화할 프로필 경로 (예: ecs/ecs_rules.yaml)")):
    """
    규칙 프로필 활성화

    특정 규칙 파일을 활성화 목록에 추가합니다.
    """
    try:
        rule_loader._add_to_active(profile_path)

        # 규칙 다시 로드
        loaded_rules = rule_loader.load_all_rules()
        bwms_checker._dynamic_rules = dict(loaded_rules)

        return ProcessResponse(
            success=True,
            data={
                "activated": profile_path,
                "total_rules": len(loaded_rules)
            }
        )
    except Exception as e:
        logger.error(f"Activate profile error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.post("/profile/deactivate")
async def deactivate_profile(profile_path: str = Form(..., description="비활성화할 프로필 경로")):
    """
    규칙 프로필 비활성화

    특정 규칙 파일을 활성화 목록에서 제거합니다.
    """
    try:
        rule_loader.remove_from_active(profile_path)

        # 규칙 다시 로드
        loaded_rules = rule_loader.load_all_rules()
        bwms_checker._dynamic_rules = dict(loaded_rules)

        return ProcessResponse(
            success=True,
            data={
                "deactivated": profile_path,
                "total_rules": len(loaded_rules)
            }
        )
    except Exception as e:
        logger.error(f"Deactivate profile error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.post("/disable")
async def disable_rule(rule_id: str = Form(..., description="비활성화할 규칙 ID")):
    """
    개별 규칙 비활성화

    특정 규칙을 비활성화합니다 (파일에서 삭제하지 않음).
    """
    try:
        rule_loader.disable_rule(rule_id)

        # 규칙 다시 로드
        loaded_rules = rule_loader.load_all_rules()
        bwms_checker._dynamic_rules = dict(loaded_rules)

        return ProcessResponse(
            success=True,
            data={
                "disabled": rule_id,
                "total_rules": len(loaded_rules)
            }
        )
    except Exception as e:
        logger.error(f"Disable rule error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.post("/enable")
async def enable_rule(rule_id: str = Form(..., description="활성화할 규칙 ID")):
    """
    개별 규칙 활성화

    비활성화된 규칙을 다시 활성화합니다.
    """
    try:
        rule_loader.enable_rule(rule_id)

        # 규칙 다시 로드
        loaded_rules = rule_loader.load_all_rules()
        bwms_checker._dynamic_rules = dict(loaded_rules)

        return ProcessResponse(
            success=True,
            data={
                "enabled": rule_id,
                "total_rules": len(loaded_rules)
            }
        )
    except Exception as e:
        logger.error(f"Enable rule error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            error=str(e)
        )
