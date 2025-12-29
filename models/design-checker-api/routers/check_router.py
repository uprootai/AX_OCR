"""
Check Router - 설계 검증 엔드포인트
/api/v1/check, /api/v1/check/bwms, /api/v1/process
"""
import json
import time
import logging
from typing import Optional

from fastapi import APIRouter, Form

from schemas import ProcessResponse
from constants import DESIGN_RULES
from checker import design_checker
from bwms_rules import bwms_checker, BWMS_DESIGN_RULES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["check"])


@router.post("/check/bwms")
async def check_bwms_design(
    symbols: str = Form(..., description="심볼 목록 (JSON)"),
    connections: str = Form(default="[]", description="연결 정보 (JSON)"),
    lines: str = Form(default="[]", description="라인 정보 (JSON)"),
    texts: str = Form(default="[]", description="OCR 텍스트 (JSON)"),
    enabled_rules: str = Form(default="", description="활성화할 BWMS 규칙 (쉼표 구분)")
):
    """
    BWMS 전용 설계 검증 실행

    TECHCROSS BWMS P&ID 도면에 대한 전용 규칙 검사
    """
    start_time = time.time()

    try:
        # JSON 파싱
        symbols_data = json.loads(symbols)
        connections_data = json.loads(connections)
        lines_data = json.loads(lines) if lines else []
        texts_data = json.loads(texts) if texts else []

        logger.info(f"BWMS check: {len(symbols_data)} symbols, {len(connections_data)} connections, {len(texts_data)} texts")

        # BWMS 규칙 필터링
        rules_to_check = None
        if enabled_rules:
            rules_to_check = [r.strip() for r in enabled_rules.split(",")]

        # BWMS 검사 실행
        bwms_violations, summary = bwms_checker.run_all_checks(
            symbols=symbols_data,
            connections=connections_data,
            lines=lines_data,
            texts=texts_data,
            enabled_rules=rules_to_check
        )

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data={
                "violations": [
                    {
                        "rule_id": v.rule_id,
                        "rule_name": v.rule_name,
                        "rule_name_en": v.rule_name_en,
                        "category": "bwms",
                        "severity": v.severity,
                        "standard": v.standard,
                        "description": v.description,
                        "location": v.location,
                        "affected_elements": v.affected_elements,
                        "suggestion": v.suggestion
                    }
                    for v in bwms_violations
                ],
                "summary": summary,
                "rules_available": list(BWMS_DESIGN_RULES.keys()),
                "rules_checked": summary.get("rules_checked", 0)
            },
            processing_time=round(processing_time, 3)
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=f"JSON 파싱 오류: {str(e)}"
        )
    except Exception as e:
        logger.error(f"BWMS check error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.post("/check")
async def check_design(
    symbols: str = Form(..., description="심볼 목록 (JSON)"),
    connections: str = Form(default="[]", description="연결 정보 (JSON)"),
    lines: str = Form(default="[]", description="라인 정보 (JSON)"),
    texts: str = Form(default="[]", description="OCR 텍스트 (JSON, BWMS 검사용)"),
    categories: str = Form(default="", description="검사할 카테고리 (쉼표 구분)"),
    severity_threshold: str = Form(default="info", description="최소 심각도"),
    include_bwms: bool = Form(default=True, description="BWMS 규칙 포함 여부")
):
    """
    설계 검증 실행

    symbols와 connections는 이전 단계 API(YOLO, PID-Analyzer)의 출력을 사용
    """
    start_time = time.time()

    try:
        # JSON 파싱
        symbols_data = json.loads(symbols)
        connections_data = json.loads(connections)
        lines_data = json.loads(lines) if lines else []
        texts_data = json.loads(texts) if texts else []

        logger.info(f"Design check: {len(symbols_data)} symbols, {len(connections_data)} connections")

        # 설계 검사 실행
        result = design_checker.run_all_checks(
            symbols=symbols_data,
            connections=connections_data,
            lines=lines_data,
            texts=texts_data,
            include_bwms=include_bwms
        )

        # 카테고리 필터링
        violations = result.violations
        if categories:
            cat_list = [c.strip().lower() for c in categories.split(",")]
            violations = [v for v in violations if v.category.lower() in cat_list]

        # 심각도 필터링
        severity_order = {"error": 3, "warning": 2, "info": 1}
        threshold = severity_order.get(severity_threshold.lower(), 0)
        violations = [v for v in violations if severity_order.get(v.severity, 0) >= threshold]

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data={
                "violations": [v.dict() for v in violations],
                "summary": result.summary.dict(),
                "rules_checked": result.rules_checked,
                "checked_at": result.checked_at
            },
            processing_time=round(processing_time, 3)
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=f"JSON 파싱 오류: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Design check error: {e}")
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.post("/process", response_model=ProcessResponse)
async def process(
    symbols: str = Form(..., description="심볼 목록 (JSON)"),
    connections: str = Form(default="[]", description="연결 정보 (JSON)"),
    lines: str = Form(default="[]", description="라인 정보 (JSON)")
):
    """
    기본 처리 엔드포인트 (BlueprintFlow 호환)
    """
    start_time = time.time()

    try:
        symbols_data = json.loads(symbols)
        connections_data = json.loads(connections)
        lines_data = json.loads(lines) if lines else []

        result = design_checker.run_all_checks(
            symbols=symbols_data,
            connections=connections_data,
            lines=lines_data
        )

        return ProcessResponse(
            success=True,
            data={
                "violations": [v.dict() for v in result.violations],
                "summary": result.summary.dict(),
                "rules_checked": result.rules_checked
            },
            processing_time=round(time.time() - start_time, 3)
        )

    except Exception as e:
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )
