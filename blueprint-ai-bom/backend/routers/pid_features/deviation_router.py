"""P&ID Deviation Analysis Router

편차 분석 엔드포인트
"""

import os
import time
import json as json_module
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
import httpx

from schemas.pid_features import (
    DeviationCategory,
    DeviationSeverity,
    DeviationSource,
    DeviationItem,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["P&ID Deviation"])

# Configuration
DESIGN_CHECKER_URL = os.getenv("DESIGN_CHECKER_URL", "http://design-checker-api:5019")

# 서비스 의존성
_session_service = None


def set_session_service(session_service):
    """서비스 주입"""
    global _session_service
    _session_service = session_service


def get_session_service():
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


@router.post("/{session_id}/deviation/analyze")
async def analyze_deviations(
    session_id: str,
    request: Optional[Dict[str, Any]] = None
):
    """
    편차 분석 실행

    확장 가능한 분석 패턴:
    - revision_compare: 리비전 비교 (baseline_session_id 필요)
    - standard_check: 표준 검사 (ISO 10628, ISA 5.1 등)
    - design_spec_check: 설계 기준서 대비 검사
    - vlm_analysis: VLM 기반 분석

    향후 요구사항에 따라 각 분석 타입의 상세 로직 구현 가능
    """
    start_time = time.time()
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 요청 파라미터 파싱
    request = request or {}
    analysis_types = request.get("analysis_types", ["standard_check"])
    baseline_session_id = request.get("baseline_session_id")
    standards = request.get("standards", ["ISO_10628"])
    severity_threshold = request.get("severity_threshold", "low")
    include_info = request.get("include_info", True)
    profile = request.get("profile", "default")

    deviations = []
    standards_applied = []

    # 분석 타입별 처리 (확장 포인트)
    for analysis_type in analysis_types:

        if analysis_type == "revision_compare" and baseline_session_id:
            # 리비전 비교 분석 (기존 longterm_router의 revision comparison 활용 가능)
            logger.info(f"[Deviation] Revision compare: {session_id} vs {baseline_session_id}")

            # TODO: 실제 구현 시 longterm_router.compare_revisions 호출
            # 현재는 플레이스홀더 - 리비전 비교 결과를 DeviationItem으로 변환
            deviations.append(DeviationItem(
                id=f"dev_rev_{session_id[:8]}_001",
                category=DeviationCategory.REVISION_MODIFIED,
                severity=DeviationSeverity.INFO,
                source=DeviationSource.REVISION_COMPARE,
                title="리비전 비교 대기 중",
                description="리비전 비교 분석을 위해 베이스라인 세션이 설정되었습니다.",
                baseline_info=baseline_session_id,
                confidence=1.0,
                verification_status=VerificationStatus.PENDING
            ))

        elif analysis_type == "standard_check":
            # 표준 검사 (Design Checker API 활용)
            standards_applied.extend(standards)
            logger.info(f"[Deviation] Standard check with standards: {standards}")

            # Design Checker API 호출하여 표준 위반 사항 검출
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    # Design Checker는 Form 데이터를 기대함
                    symbols_data = session.get("detections", [])
                    lines_data = session.get("lines", [])
                    texts_data = session.get("ocr_results", [])

                    form_data = {
                        "symbols": json_module.dumps(symbols_data),
                        "connections": json_module.dumps([]),
                        "lines": json_module.dumps(lines_data),
                        "texts": json_module.dumps(texts_data),
                        "enabled_rules": ""  # 전체 규칙
                    }

                    response = await client.post(
                        f"{DESIGN_CHECKER_URL}/api/v1/check/bwms",
                        data=form_data
                    )

                    if response.status_code == 200:
                        result = response.json()
                        violations = result.get("data", {}).get("violations", [])

                        for idx, violation in enumerate(violations):
                            severity_map = {
                                "error": DeviationSeverity.HIGH,
                                "warning": DeviationSeverity.MEDIUM,
                                "info": DeviationSeverity.LOW
                            }
                            dev_severity = severity_map.get(
                                violation.get("severity", "warning"),
                                DeviationSeverity.MEDIUM
                            )

                            deviations.append(DeviationItem(
                                id=f"dev_std_{session_id[:8]}_{idx:03d}",
                                category=DeviationCategory.STANDARD_VIOLATION,
                                severity=dev_severity,
                                source=DeviationSource.STANDARD_CHECK,
                                title=violation.get("rule_name", "표준 위반"),
                                description=violation.get("description", ""),
                                location=str(violation.get("affected_elements", [])),
                                reference_standard=violation.get("rule_id", ""),
                                confidence=0.8,
                                action_required=violation.get("recommendation", "검토 필요"),
                                verification_status=VerificationStatus.PENDING
                            ))

            except httpx.RequestError as e:
                logger.warning(f"Design Checker connection failed: {e}")
                # 연결 실패 시 플레이스홀더 반환
                deviations.append(DeviationItem(
                    id=f"dev_std_{session_id[:8]}_err",
                    category=DeviationCategory.OTHER,
                    severity=DeviationSeverity.INFO,
                    source=DeviationSource.STANDARD_CHECK,
                    title="표준 검사 서비스 연결 실패",
                    description=f"Design Checker API 연결에 실패했습니다: {str(e)}",
                    confidence=1.0,
                    verification_status=VerificationStatus.PENDING
                ))

        elif analysis_type == "design_spec_check":
            # 설계 기준서 대비 검사 (향후 구현)
            logger.info(f"[Deviation] Design spec check (placeholder)")
            deviations.append(DeviationItem(
                id=f"dev_spec_{session_id[:8]}_001",
                category=DeviationCategory.DESIGN_MISSING,
                severity=DeviationSeverity.INFO,
                source=DeviationSource.DESIGN_SPEC_CHECK,
                title="설계 기준서 검사 대기 중",
                description="설계 기준서 ID가 설정되면 상세 검사가 진행됩니다.",
                confidence=1.0,
                verification_status=VerificationStatus.PENDING
            ))

        elif analysis_type == "vlm_analysis":
            # VLM 기반 분석 (향후 구현)
            logger.info(f"[Deviation] VLM analysis (placeholder)")
            deviations.append(DeviationItem(
                id=f"dev_vlm_{session_id[:8]}_001",
                category=DeviationCategory.OTHER,
                severity=DeviationSeverity.INFO,
                source=DeviationSource.VLM_ANALYSIS,
                title="VLM 분석 대기 중",
                description="Vision-Language Model 기반 편차 분석이 예정되어 있습니다.",
                confidence=1.0,
                verification_status=VerificationStatus.PENDING
            ))

    # 심각도 필터링
    severity_order = ["critical", "high", "medium", "low", "info"]
    threshold_idx = severity_order.index(severity_threshold.lower()) if severity_threshold.lower() in severity_order else 4

    if not include_info and threshold_idx == 4:
        threshold_idx = 3  # info 제외

    filtered_deviations = [
        d for d in deviations
        if severity_order.index(d.severity.value) <= threshold_idx
    ]

    # 세션에 저장
    session_service.update_session(session_id, {
        "pid_deviations": [d.model_dump() for d in filtered_deviations],
        "pid_deviation_count": len(filtered_deviations)
    })

    processing_time = time.time() - start_time

    # 통계 계산
    by_category = {}
    by_severity = {}
    by_source = {}
    for d in filtered_deviations:
        by_category[d.category.value] = by_category.get(d.category.value, 0) + 1
        by_severity[d.severity.value] = by_severity.get(d.severity.value, 0) + 1
        by_source[d.source.value] = by_source.get(d.source.value, 0) + 1

    return {
        "session_id": session_id,
        "deviations": [d.model_dump() for d in filtered_deviations],
        "total_count": len(filtered_deviations),
        "by_category": by_category,
        "by_severity": by_severity,
        "by_source": by_source,
        "analysis_types_used": analysis_types,
        "standards_applied": standards_applied,
        "baseline_session_id": baseline_session_id,
        "processing_time": round(processing_time, 3)
    }


@router.get("/{session_id}/deviation/list")
async def get_deviations(
    session_id: str,
    category: Optional[str] = Query(None, description="편차 카테고리 필터"),
    severity: Optional[str] = Query(None, description="심각도 필터"),
    source: Optional[str] = Query(None, description="소스 필터")
):
    """
    편차 목록 조회 (필터링 지원)
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    deviations = session.get("pid_deviations", [])

    # 필터링
    if category:
        deviations = [d for d in deviations if d.get("category") == category]
    if severity:
        deviations = [d for d in deviations if d.get("severity") == severity]
    if source:
        deviations = [d for d in deviations if d.get("source") == source]

    return {
        "session_id": session_id,
        "deviations": deviations,
        "total_count": len(deviations),
        "filters_applied": {
            "category": category,
            "severity": severity,
            "source": source
        }
    }
