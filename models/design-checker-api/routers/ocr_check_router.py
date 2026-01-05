"""
OCR Check Router - OCR 기반 설계 검증 엔드포인트
이미지에서 직접 태그를 추출하여 existence 규칙 검증
"""
import io
import json
import time
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse

from schemas import ProcessResponse
from services.ocr_service import ocr_service
from services.tag_extractor import tag_extractor, TAG_PATTERNS
from services.equipment_mapping import equipment_mapper
from services.excel_report import excel_report_service
from services.pdf_report import pdf_report_service
from rule_loader import rule_loader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/check", tags=["ocr-check"])


@router.post("/ocr")
async def check_with_ocr(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    product_type: str = Form(default="AUTO", description="제품 유형 (ECS, HYCHLOR, AUTO)"),
    lang: str = Form(default="en", description="OCR 언어 (en, korean)"),
    min_confidence: float = Form(default=0.5, description="최소 OCR 신뢰도"),
    check_existence: bool = Form(default=True, description="existence 규칙 검사 여부")
):
    """
    OCR 기반 설계 검증

    이미지에서 직접 태그를 추출하여 규칙 검증 수행
    YOLO 없이 OCR만으로 existence 규칙 검증 가능
    """
    start_time = time.time()

    try:
        # 이미지 읽기
        image_data = await file.read()
        logger.info(f"Received image: {file.filename}, size={len(image_data)} bytes")

        # OCR 실행
        ocr_results = await ocr_service.extract_text_from_image(image_data, lang)

        if not ocr_results:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error="OCR 결과가 없습니다. 이미지를 확인해주세요."
            )

        # 태그 추출
        extraction_result = tag_extractor.extract_from_ocr_results(
            [vars(r) for r in ocr_results],
            min_confidence=min_confidence
        )

        # 제품 유형 결정
        detected_product_type = extraction_result.product_type
        if product_type.upper() != "AUTO":
            detected_product_type = product_type.upper()

        # existence 규칙 검증 (equipment_mapper 사용)
        violations = []
        passed_rules = []

        # OCR 텍스트 리스트 준비
        ocr_texts = [r.text for r in ocr_results]

        if check_existence:
            # 해당 제품 유형의 규칙 로드
            rules = rule_loader.get_rules_by_product_type(detected_product_type)

            for rule in rules:
                if rule.get("check_type") == "existence":
                    equipment = rule.get("equipment", "")
                    equipment_list = [e.strip() for e in equipment.split(",")]

                    for eq in equipment_list:
                        # 1. equipment_mapper로 매핑 검색
                        match = equipment_mapper.find_tags_for_equipment(eq, ocr_texts)

                        # 2. 매핑 결과 없으면 기존 tag_extractor 사용
                        if not match.matched_tags:
                            exists, tags = tag_extractor.check_equipment_exists(
                                extraction_result, eq
                            )
                            detected_tags = [t.tag for t in tags] if tags else []
                        else:
                            exists = True
                            detected_tags = match.matched_tags

                        if not exists:
                            violations.append({
                                "rule_id": rule.get("rule_id", ""),
                                "rule_name": rule.get("name", ""),
                                "rule_name_en": rule.get("name_en", ""),
                                "severity": rule.get("severity", "warning"),
                                "category": rule.get("category", ""),
                                "equipment": eq,
                                "check_type": "existence",
                                "description": rule.get("description", ""),
                                "suggestion": rule.get("suggestion", ""),
                                "detected": False,
                                "auto_checkable": rule.get("auto_checkable", True),
                                "match_type": match.match_type,
                            })
                        else:
                            passed_rules.append({
                                "rule_id": rule.get("rule_id", ""),
                                "rule_name": rule.get("name", ""),
                                "equipment": eq,
                                "detected": True,
                                "detected_tags": detected_tags,
                                "match_type": match.match_type,
                                "match_confidence": match.confidence,
                            })

        # 고유 장비 목록
        unique_equipment = tag_extractor.get_unique_equipment(extraction_result)

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data={
                "ocr": {
                    "total_texts": extraction_result.total_texts,
                    "total_tags": extraction_result.total_tags,
                    "product_type_detected": extraction_result.product_type,
                    "product_type_used": detected_product_type,
                },
                "equipment": {
                    "detected": unique_equipment,
                    "count": sum(len(v) for v in unique_equipment.values()),
                    "types": list(unique_equipment.keys()),
                },
                "tags": [
                    {
                        "tag": t.tag,
                        "type": t.tag_type,
                        "confidence": t.confidence,
                        "position": {"x": t.x, "y": t.y},
                    }
                    for t in extraction_result.tags
                ],
                "validation": {
                    "rules_checked": len(violations) + len(passed_rules),
                    "violations": violations,
                    "passed": passed_rules,
                    "violation_count": len(violations),
                    "pass_count": len(passed_rules),
                },
            },
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"OCR check error: {e}", exc_info=True)
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.post("/ocr/tags")
async def extract_tags_only(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    lang: str = Form(default="en", description="OCR 언어"),
    min_confidence: float = Form(default=0.5, description="최소 OCR 신뢰도")
):
    """
    태그 추출만 수행 (규칙 검증 없음)

    이미지에서 BWMS 장비 태그만 추출
    """
    start_time = time.time()

    try:
        image_data = await file.read()

        # OCR 실행
        ocr_results = await ocr_service.extract_text_from_image(image_data, lang)

        if not ocr_results:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error="OCR 결과가 없습니다."
            )

        # 태그 추출
        extraction_result = tag_extractor.extract_from_ocr_results(
            [vars(r) for r in ocr_results],
            min_confidence=min_confidence
        )

        unique_equipment = tag_extractor.get_unique_equipment(extraction_result)

        return ProcessResponse(
            success=True,
            data={
                "product_type": extraction_result.product_type,
                "total_texts": extraction_result.total_texts,
                "total_tags": extraction_result.total_tags,
                "equipment": unique_equipment,
                "tags": [
                    {
                        "tag": t.tag,
                        "type": t.tag_type,
                        "number": t.tag_number,
                        "confidence": round(t.confidence, 3),
                        "position": {
                            "x": round(t.x, 1),
                            "y": round(t.y, 1),
                            "width": round(t.width, 1),
                            "height": round(t.height, 1),
                        },
                        "product_type": t.product_type,
                    }
                    for t in extraction_result.tags
                ],
            },
            processing_time=round(time.time() - start_time, 3)
        )

    except Exception as e:
        logger.error(f"Tag extraction error: {e}", exc_info=True)
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.get("/ocr/patterns")
async def get_tag_patterns():
    """
    지원하는 태그 패턴 목록 조회
    """
    patterns = []
    for tag_type, config in TAG_PATTERNS.items():
        patterns.append({
            "tag_type": tag_type,
            "pattern": config["pattern"],
            "description": config["description"],
            "product_type": config["product_type"],
            "priority": config["priority"],
        })

    # 제품 유형별 분류
    ecs_patterns = [p for p in patterns if p["product_type"] == "ECS"]
    hychlor_patterns = [p for p in patterns if p["product_type"] == "HYCHLOR"]
    common_patterns = [p for p in patterns if p["product_type"] == "ALL"]

    return ProcessResponse(
        success=True,
        data={
            "total_patterns": len(patterns),
            "by_product_type": {
                "ECS": len(ecs_patterns),
                "HYCHLOR": len(hychlor_patterns),
                "ALL": len(common_patterns),
            },
            "patterns": {
                "ECS": ecs_patterns,
                "HYCHLOR": hychlor_patterns,
                "ALL": common_patterns,
            },
        }
    )


@router.post("/ocr/validate-rules")
async def validate_with_ocr_data(
    ocr_texts: str = Form(..., description="OCR 텍스트 목록 (JSON)"),
    product_type: str = Form(default="AUTO", description="제품 유형"),
    rule_ids: str = Form(default="", description="검사할 규칙 ID (쉼표 구분)")
):
    """
    OCR 텍스트 데이터로 규칙 검증

    이미 OCR을 수행한 경우, 텍스트 데이터만으로 규칙 검증
    """
    start_time = time.time()

    try:
        texts_data = json.loads(ocr_texts)

        # 태그 추출
        extraction_result = tag_extractor.extract_from_ocr_results(
            texts_data, min_confidence=0.0
        )

        # 제품 유형 결정
        detected_product_type = extraction_result.product_type
        if product_type.upper() != "AUTO":
            detected_product_type = product_type.upper()

        # 규칙 로드
        rules = rule_loader.get_rules_by_product_type(detected_product_type)

        # 규칙 ID 필터링
        if rule_ids:
            rule_id_list = [r.strip() for r in rule_ids.split(",")]
            rules = [r for r in rules if r.get("rule_id") in rule_id_list]

        # existence 규칙만 검증
        violations = []
        passed = []

        for rule in rules:
            if rule.get("check_type") != "existence":
                continue

            equipment = rule.get("equipment", "")
            equipment_list = [e.strip() for e in equipment.split(",")]

            for eq in equipment_list:
                exists, tags = tag_extractor.check_equipment_exists(
                    extraction_result, eq
                )

                result_item = {
                    "rule_id": rule.get("rule_id"),
                    "equipment": eq,
                    "detected": exists,
                }

                if exists:
                    result_item["tags"] = [t.tag for t in tags]
                    passed.append(result_item)
                else:
                    result_item["severity"] = rule.get("severity", "warning")
                    result_item["suggestion"] = rule.get("suggestion", "")
                    violations.append(result_item)

        return ProcessResponse(
            success=True,
            data={
                "product_type": detected_product_type,
                "rules_checked": len(violations) + len(passed),
                "violations": violations,
                "passed": passed,
                "summary": {
                    "total": len(violations) + len(passed),
                    "violations": len(violations),
                    "passed": len(passed),
                    "pass_rate": round(
                        len(passed) / (len(violations) + len(passed)) * 100, 1
                    ) if violations or passed else 0,
                },
            },
            processing_time=round(time.time() - start_time, 3)
        )

    except json.JSONDecodeError as e:
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=f"JSON 파싱 오류: {e}"
        )
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.get("/ocr/mappings")
async def get_equipment_mappings():
    """
    장비명↔OCR 태그 매핑 테이블 조회

    규칙의 equipment 필드와 OCR 태그 간의 매핑 정보 반환
    """
    mappings = equipment_mapper.get_all_mappings()

    return ProcessResponse(
        success=True,
        data={
            "total_equipment": mappings["total_equipment"],
            "total_tags": mappings["total_tags"],
            "equipment_to_tags": mappings["equipment_to_tags"],
            "tag_to_equipment": mappings["tag_to_equipment"],
        }
    )


@router.post("/ocr/validate-with-mapping")
async def validate_with_equipment_mapping(
    ocr_texts: str = Form(..., description="OCR 텍스트 목록 (JSON)"),
    product_type: str = Form(default="AUTO", description="제품 유형 (ECS, HYCHLOR, AUTO)"),
    ship_type: str = Form(default=None, description="선종 (BULKER, TANKER, CONTAINER, LNG, LPG, BARGE, GENERAL)"),
    class_society: str = Form(default=None, description="선급 (ABS, LR, DNV, BV, KR, NK, CCS)"),
    project_type: str = Form(default=None, description="프로젝트 유형 (NEWBUILD, RETROFIT)"),
):
    """
    장비명↔태그 매핑을 사용한 OCR 검증 (조건부 필터링 지원)

    Args:
        ocr_texts: OCR 텍스트 목록 (JSON)
        product_type: 제품 유형 (ECS, HYCHLOR, AUTO)
        ship_type: 선종 - BULKER 전용 규칙 등 필터링
        class_society: 선급 - ABS, DNV 등 선급별 규칙 필터링
        project_type: 프로젝트 유형 - RETROFIT 전용 규칙 등 필터링
    """
    start_time = time.time()

    try:
        texts_data = json.loads(ocr_texts)

        # 텍스트만 추출 (dict 또는 str)
        text_list = []
        for item in texts_data:
            if isinstance(item, dict):
                text_list.append(item.get("text", ""))
            else:
                text_list.append(str(item))

        # 태그 추출
        extraction_result = tag_extractor.extract_from_ocr_results(
            texts_data, min_confidence=0.0
        )

        # 제품 유형 결정
        detected_product_type = extraction_result.product_type
        if product_type.upper() != "AUTO":
            detected_product_type = product_type.upper()

        # 조건부 규칙 필터링
        rules = rule_loader.get_rules_filtered(
            product_type=detected_product_type,
            ship_type=ship_type if ship_type else None,
            class_society=class_society if class_society else None,
            project_type=project_type if project_type else None,
        )

        violations = []
        passed = []
        skipped = []

        # 먼저 모든 장비의 존재 여부 캐시
        equipment_exists_cache = {}

        def check_equipment_exists(eq_name: str) -> tuple:
            """장비 존재 여부 확인 (캐시 사용)"""
            if eq_name in equipment_exists_cache:
                return equipment_exists_cache[eq_name]

            match = equipment_mapper.find_tags_for_equipment(eq_name, text_list)
            if match.matched_tags:
                equipment_exists_cache[eq_name] = (True, match.matched_tags, match)
                return True, match.matched_tags, match

            # tag_extractor 폴백
            exists, tags = tag_extractor.check_equipment_exists(extraction_result, eq_name)
            if exists:
                equipment_exists_cache[eq_name] = (True, [t.tag for t in tags], match)
                return True, [t.tag for t in tags], match

            equipment_exists_cache[eq_name] = (False, [], match)
            return False, [], match

        for rule in rules:
            check_type = rule.get("check_type", "")
            equipment = rule.get("equipment", "")
            check_logic = rule.get("check_logic", "exists")  # 기본값: exists

            # existence 규칙만 자동 검증
            if check_type != "existence":
                skipped.append({
                    "rule_id": rule.get("rule_id"),
                    "check_type": check_type,
                    "category": rule.get("category", ""),
                    "reason": "자동 검증 불가 (existence 규칙만 지원)",
                })
                continue

            equipment_list = [e.strip() for e in equipment.split(",")]

            # ============================================================
            # check_logic 처리
            # ============================================================

            # 1. conditional: depends_on 장비가 있을 때만 검사
            if check_logic == "conditional":
                depends_on = rule.get("depends_on", "")
                if depends_on:
                    dep_exists, _, _ = check_equipment_exists(depends_on)
                    if not dep_exists:
                        # 의존 장비가 없으면 이 규칙 스킵 (통과 처리)
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": equipment,
                            "detected": False,
                            "match_type": "conditional_skip",
                            "confidence": 1.0,
                            "reason": f"{depends_on} 미검출로 규칙 스킵",
                        })
                        continue

            # 2. or_exists: 여러 장비 중 하나만 있으면 OK
            if check_logic == "or_exists":
                any_exists = False
                matched_eq = None
                matched_tags = []

                for eq in equipment_list:
                    exists, tags, match = check_equipment_exists(eq)
                    if exists:
                        any_exists = True
                        matched_eq = eq
                        matched_tags = tags
                        break

                if any_exists:
                    passed.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": matched_eq,
                        "detected": True,
                        "matched_tags": matched_tags,
                        "match_type": "or_exists",
                        "confidence": 1.0,
                    })
                else:
                    # context_check: OCR에서 특정 키워드 있으면 스킵
                    context_check = rule.get("context_check", "")
                    if context_check:
                        context_found = any(context_check.upper() in t.upper() for t in text_list)
                        if context_found:
                            # 컨텍스트가 있으면 이 규칙 적용 (위반)
                            pass
                        else:
                            # 컨텍스트가 없으면 스킵 (통과)
                            passed.append({
                                "rule_id": rule.get("rule_id"),
                                "rule_name": rule.get("name"),
                                "equipment": equipment,
                                "detected": False,
                                "match_type": "context_skip",
                                "confidence": 1.0,
                                "reason": f"'{context_check}' 컨텍스트 미검출로 규칙 스킵",
                            })
                            continue

                    violations.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": equipment,
                        "detected": False,
                        "severity": rule.get("severity", "warning"),
                        "suggestion": rule.get("suggestion", ""),
                        "match_type": "or_exists",
                        "reason": f"{equipment} 중 하나도 미검출",
                    })
                continue

            # 3. not_exists: 없어야 통과 (역논리)
            if check_logic == "not_exists":
                for eq in equipment_list:
                    exists, tags, match = check_equipment_exists(eq)

                    if not exists:
                        # 없으면 통과 (정상)
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": eq,
                            "detected": False,
                            "match_type": "not_exists_pass",
                            "confidence": 1.0,
                            "reason": f"{eq} 미적용 확인됨",
                        })
                    else:
                        # 있으면 위반 (있으면 안 됨)
                        violations.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": eq,
                            "detected": True,
                            "matched_tags": tags,
                            "severity": rule.get("severity", "warning"),
                            "suggestion": rule.get("suggestion", ""),
                            "match_type": "not_exists_violation",
                            "reason": f"{eq}가 검출됨 (미적용 규칙 위반)",
                        })
                continue

            # 4. optional: 없어도 위반 아님
            if check_logic == "optional":
                for eq in equipment_list:
                    exists, tags, match = check_equipment_exists(eq)

                    passed.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "detected": exists,
                        "matched_tags": tags if exists else [],
                        "match_type": "optional" if not exists else match.match_type,
                        "confidence": match.confidence if exists else 1.0,
                        "reason": "옵션 장비" if not exists else None,
                    })
                continue

            # 5. exists (기본): 있어야 통과
            for eq in equipment_list:
                exists, tags, match = check_equipment_exists(eq)

                result_item = {
                    "rule_id": rule.get("rule_id"),
                    "rule_name": rule.get("name"),
                    "equipment": eq,
                    "match_type": match.match_type,
                    "confidence": match.confidence,
                }

                if exists:
                    result_item["detected"] = True
                    result_item["matched_tags"] = tags
                    passed.append(result_item)
                else:
                    result_item["detected"] = False
                    result_item["severity"] = rule.get("severity", "warning")
                    result_item["suggestion"] = rule.get("suggestion", "")
                    violations.append(result_item)

        total_checked = len(violations) + len(passed)
        pass_rate = round(len(passed) / total_checked * 100, 1) if total_checked > 0 else 0

        return ProcessResponse(
            success=True,
            data={
                "filters": {
                    "product_type": detected_product_type,
                    "ship_type": ship_type,
                    "class_society": class_society,
                    "project_type": project_type,
                },
                "summary": {
                    "total_rules": len(rules),
                    "existence_checked": total_checked,
                    "passed": len(passed),
                    "violations": len(violations),
                    "skipped": len(skipped),
                    "pass_rate": pass_rate,
                },
                "passed": passed,
                "violations": violations,
                "skipped": skipped,
            },
            processing_time=round(time.time() - start_time, 3)
        )

    except json.JSONDecodeError as e:
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=f"JSON 파싱 오류: {e}"
        )
    except Exception as e:
        logger.error(f"Mapping validation error: {e}", exc_info=True)
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.post("/ocr/export/excel")
async def export_validation_to_excel(
    ocr_texts: str = Form(..., description="OCR 텍스트 목록 (JSON)"),
    product_type: str = Form(default="AUTO", description="제품 유형 (ECS, HYCHLOR, AUTO)"),
    ship_type: str = Form(default=None, description="선종"),
    class_society: str = Form(default=None, description="선급"),
    project_type: str = Form(default=None, description="프로젝트 유형"),
    ship_name: str = Form(default="", description="선명"),
    drawing_no: str = Form(default="", description="도면번호"),
    report_type: str = Form(default="summary", description="리포트 유형 (summary, checklist)"),
):
    """
    검증 결과를 Excel 파일로 내보내기

    Args:
        ocr_texts: OCR 텍스트 목록 (JSON)
        product_type: 제품 유형
        ship_type: 선종
        class_society: 선급
        project_type: 프로젝트 유형
        ship_name: 선명 (리포트에 표시)
        drawing_no: 도면번호 (리포트에 표시)
        report_type: 리포트 유형
            - summary: 요약 리포트 (통과/위반/스킵 시트)
            - checklist: 전체 체크리스트 (모든 규칙 포함)

    Returns:
        Excel 파일 (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
    """
    try:
        texts_data = json.loads(ocr_texts)

        # 텍스트만 추출
        text_list = []
        for item in texts_data:
            if isinstance(item, dict):
                text_list.append(item.get("text", ""))
            else:
                text_list.append(str(item))

        # 태그 추출
        extraction_result = tag_extractor.extract_from_ocr_results(
            texts_data, min_confidence=0.0
        )

        # 제품 유형 결정
        detected_product_type = extraction_result.product_type
        if product_type.upper() != "AUTO":
            detected_product_type = product_type.upper()

        # 조건부 규칙 필터링
        rules = rule_loader.get_rules_filtered(
            product_type=detected_product_type,
            ship_type=ship_type if ship_type else None,
            class_society=class_society if class_society else None,
            project_type=project_type if project_type else None,
        )

        # ===== 검증 로직 (validate-with-mapping과 동일) =====
        violations = []
        passed = []
        skipped = []

        equipment_exists_cache = {}

        def check_equipment_exists(eq_name: str) -> tuple:
            if eq_name in equipment_exists_cache:
                return equipment_exists_cache[eq_name]

            match = equipment_mapper.find_tags_for_equipment(eq_name, text_list)
            if match.matched_tags:
                equipment_exists_cache[eq_name] = (True, match.matched_tags, match)
                return True, match.matched_tags, match

            exists, tags = tag_extractor.check_equipment_exists(extraction_result, eq_name)
            if exists:
                equipment_exists_cache[eq_name] = (True, [t.tag for t in tags], match)
                return True, [t.tag for t in tags], match

            equipment_exists_cache[eq_name] = (False, [], match)
            return False, [], match

        for rule in rules:
            check_type = rule.get("check_type", "")
            equipment = rule.get("equipment", "")
            check_logic = rule.get("check_logic", "exists")

            if check_type != "existence":
                skipped.append({
                    "rule_id": rule.get("rule_id"),
                    "check_type": check_type,
                    "category": rule.get("category", ""),
                    "reason": "자동 검증 불가",
                })
                continue

            equipment_list = [e.strip() for e in equipment.split(",")]

            # check_logic 처리 (간소화)
            if check_logic == "conditional":
                depends_on = rule.get("depends_on", "")
                if depends_on:
                    dep_exists, _, _ = check_equipment_exists(depends_on)
                    if not dep_exists:
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": equipment,
                            "match_type": "conditional_skip",
                            "matched_tags": [],
                            "reason": f"{depends_on} 미검출로 스킵",
                        })
                        continue

            if check_logic == "or_exists":
                any_exists = False
                for eq in equipment_list:
                    exists, tags, match = check_equipment_exists(eq)
                    if exists:
                        any_exists = True
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": eq,
                            "match_type": "or_exists",
                            "matched_tags": tags,
                        })
                        break
                if not any_exists:
                    context_check = rule.get("context_check", "")
                    if context_check and not any(context_check.upper() in t.upper() for t in text_list):
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": equipment,
                            "match_type": "context_skip",
                            "matched_tags": [],
                            "reason": f"컨텍스트 미검출로 스킵",
                        })
                    else:
                        violations.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": equipment,
                            "severity": rule.get("severity", "warning"),
                            "suggestion": rule.get("suggestion", ""),
                        })
                continue

            if check_logic == "not_exists":
                for eq in equipment_list:
                    exists, tags, _ = check_equipment_exists(eq)
                    if not exists:
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": eq,
                            "match_type": "not_exists_pass",
                            "matched_tags": [],
                            "reason": f"{eq} 미적용 확인됨",
                        })
                    else:
                        violations.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": eq,
                            "severity": rule.get("severity", "warning"),
                            "suggestion": rule.get("suggestion", ""),
                            "matched_tags": tags,
                        })
                continue

            if check_logic == "optional":
                for eq in equipment_list:
                    exists, tags, match = check_equipment_exists(eq)
                    passed.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "match_type": "optional" if not exists else match.match_type,
                        "matched_tags": tags if exists else [],
                        "reason": "옵션 장비" if not exists else None,
                    })
                continue

            # exists (기본)
            for eq in equipment_list:
                exists, tags, match = check_equipment_exists(eq)
                if exists:
                    passed.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "match_type": match.match_type,
                        "matched_tags": tags,
                    })
                else:
                    violations.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "severity": rule.get("severity", "warning"),
                        "suggestion": rule.get("suggestion", ""),
                    })

        # 검증 결과 구성
        total_checked = len(violations) + len(passed)
        pass_rate = round(len(passed) / total_checked * 100, 1) if total_checked > 0 else 0

        validation_data = {
            "filters": {
                "product_type": detected_product_type,
                "ship_type": ship_type,
                "class_society": class_society,
                "project_type": project_type,
            },
            "summary": {
                "total_rules": len(rules),
                "existence_checked": total_checked,
                "passed": len(passed),
                "violations": len(violations),
                "skipped": len(skipped),
                "pass_rate": pass_rate,
            },
            "passed": passed,
            "violations": violations,
            "skipped": skipped,
        }

        project_info = {
            "ship_name": ship_name or "-",
            "drawing_no": drawing_no or "-",
            "product_type": detected_product_type,
            "ship_type": ship_type or "-",
            "class_society": class_society or "-",
        }

        # Excel 생성
        if report_type == "checklist":
            all_rules = rule_loader.load_all_rules()
            excel_bytes = excel_report_service.generate_checklist_report(
                validation_data,
                list(all_rules.values()),
                project_info
            )
            filename = f"BWMS_Checklist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        else:
            excel_bytes = excel_report_service.generate_validation_report(
                validation_data,
                project_info
            )
            filename = f"BWMS_Validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 파싱 오류: {e}")
    except Exception as e:
        logger.error(f"Excel export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/export/pdf")
async def export_validation_to_pdf(
    ocr_texts: str = Form(..., description="OCR 텍스트 목록 (JSON)"),
    product_type: str = Form(default="AUTO", description="제품 유형 (ECS, HYCHLOR, AUTO)"),
    ship_type: str = Form(default=None, description="선종"),
    class_society: str = Form(default=None, description="선급"),
    project_type: str = Form(default=None, description="프로젝트 유형"),
    ship_name: str = Form(default="", description="선명"),
    drawing_no: str = Form(default="", description="도면번호"),
    report_type: str = Form(default="summary", description="리포트 유형 (summary, checklist)"),
):
    """
    검증 결과를 PDF 파일로 내보내기

    Args:
        ocr_texts: OCR 텍스트 목록 (JSON)
        product_type: 제품 유형
        ship_type: 선종
        class_society: 선급
        project_type: 프로젝트 유형
        ship_name: 선명 (리포트에 표시)
        drawing_no: 도면번호 (리포트에 표시)
        report_type: 리포트 유형
            - summary: 요약 리포트
            - checklist: 전체 체크리스트 (모든 규칙 포함)

    Returns:
        PDF 파일 (application/pdf)
    """
    try:
        texts_data = json.loads(ocr_texts)

        # 텍스트만 추출
        text_list = []
        for item in texts_data:
            if isinstance(item, dict):
                text_list.append(item.get("text", ""))
            else:
                text_list.append(str(item))

        # 태그 추출
        extraction_result = tag_extractor.extract_from_ocr_results(
            texts_data, min_confidence=0.0
        )

        # 제품 유형 결정
        detected_product_type = extraction_result.product_type
        if product_type.upper() != "AUTO":
            detected_product_type = product_type.upper()

        # 조건부 규칙 필터링
        rules = rule_loader.get_rules_filtered(
            product_type=detected_product_type,
            ship_type=ship_type if ship_type else None,
            class_society=class_society if class_society else None,
            project_type=project_type if project_type else None,
        )

        # ===== 검증 로직 (validate-with-mapping과 동일) =====
        violations = []
        passed = []
        skipped = []

        equipment_exists_cache = {}

        def check_equipment_exists(eq_name: str) -> tuple:
            if eq_name in equipment_exists_cache:
                return equipment_exists_cache[eq_name]

            match = equipment_mapper.find_tags_for_equipment(eq_name, text_list)
            if match.matched_tags:
                equipment_exists_cache[eq_name] = (True, match.matched_tags, match)
                return True, match.matched_tags, match

            exists, tags = tag_extractor.check_equipment_exists(extraction_result, eq_name)
            if exists:
                equipment_exists_cache[eq_name] = (True, [t.tag for t in tags], match)
                return True, [t.tag for t in tags], match

            equipment_exists_cache[eq_name] = (False, [], match)
            return False, [], match

        for rule in rules:
            check_type = rule.get("check_type", "")
            equipment = rule.get("equipment", "")
            check_logic = rule.get("check_logic", "exists")

            if check_type != "existence":
                skipped.append({
                    "rule_id": rule.get("rule_id"),
                    "check_type": check_type,
                    "category": rule.get("category", ""),
                    "reason": "자동 검증 불가",
                })
                continue

            equipment_list = [e.strip() for e in equipment.split(",")]

            # check_logic 처리 (간소화)
            if check_logic == "conditional":
                depends_on = rule.get("depends_on", "")
                if depends_on:
                    dep_exists, _, _ = check_equipment_exists(depends_on)
                    if not dep_exists:
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": equipment,
                            "match_type": "conditional_skip",
                            "matched_tags": [],
                            "reason": f"{depends_on} 미검출로 스킵",
                        })
                        continue

            if check_logic == "or_exists":
                any_exists = False
                for eq in equipment_list:
                    exists, tags, match = check_equipment_exists(eq)
                    if exists:
                        any_exists = True
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": eq,
                            "match_type": "or_exists",
                            "matched_tags": tags,
                        })
                        break
                if not any_exists:
                    context_check = rule.get("context_check", "")
                    if context_check and not any(context_check.upper() in t.upper() for t in text_list):
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": equipment,
                            "match_type": "context_skip",
                            "matched_tags": [],
                            "reason": "컨텍스트 미검출로 스킵",
                        })
                    else:
                        violations.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": equipment,
                            "severity": rule.get("severity", "warning"),
                            "suggestion": rule.get("suggestion", ""),
                        })
                continue

            if check_logic == "not_exists":
                for eq in equipment_list:
                    exists, tags, _ = check_equipment_exists(eq)
                    if not exists:
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": eq,
                            "match_type": "not_exists_pass",
                            "matched_tags": [],
                            "reason": f"{eq} 미적용 확인됨",
                        })
                    else:
                        violations.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": eq,
                            "severity": rule.get("severity", "warning"),
                            "suggestion": rule.get("suggestion", ""),
                            "matched_tags": tags,
                        })
                continue

            if check_logic == "optional":
                for eq in equipment_list:
                    exists, tags, match = check_equipment_exists(eq)
                    passed.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "match_type": "optional" if not exists else match.match_type,
                        "matched_tags": tags if exists else [],
                        "reason": "옵션 장비" if not exists else None,
                    })
                continue

            # exists (기본)
            for eq in equipment_list:
                exists, tags, match = check_equipment_exists(eq)
                if exists:
                    passed.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "match_type": match.match_type,
                        "matched_tags": tags,
                    })
                else:
                    violations.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "severity": rule.get("severity", "warning"),
                        "suggestion": rule.get("suggestion", ""),
                    })

        # 검증 결과 구성
        total_checked = len(violations) + len(passed)
        pass_rate = round(len(passed) / total_checked * 100, 1) if total_checked > 0 else 0

        validation_data = {
            "filters": {
                "product_type": detected_product_type,
                "ship_type": ship_type,
                "class_society": class_society,
                "project_type": project_type,
            },
            "summary": {
                "total_rules": len(rules),
                "existence_checked": total_checked,
                "passed": len(passed),
                "violations": len(violations),
                "skipped": len(skipped),
                "pass_rate": pass_rate,
            },
            "passed": passed,
            "violations": violations,
            "skipped": skipped,
        }

        project_info = {
            "ship_name": ship_name or "-",
            "drawing_no": drawing_no or "-",
            "product_type": detected_product_type,
            "ship_type": ship_type or "-",
            "class_society": class_society or "-",
        }

        # PDF 생성
        if report_type == "checklist":
            all_rules = rule_loader.load_all_rules()
            pdf_bytes = pdf_report_service.generate_checklist_report(
                validation_data,
                list(all_rules.values()),
                project_info
            )
            filename = f"BWMS_Checklist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            pdf_bytes = pdf_report_service.generate_validation_report(
                validation_data,
                project_info
            )
            filename = f"BWMS_Validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 파싱 오류: {e}")
    except Exception as e:
        logger.error(f"PDF export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
