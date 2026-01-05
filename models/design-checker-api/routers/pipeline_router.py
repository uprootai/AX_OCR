"""
Pipeline Router - YOLO + OCR + Design Checker 통합 파이프라인
이미지 하나로 심볼 검출부터 설계 검증까지 자동 수행

OCR 소스:
- paddleocr: PaddleOCR (범용 OCR)
- edocr2: eDOCr2 (기계도면 특화 - 치수/GD&T 추출)
- both: 두 OCR 결과 통합
"""
import io
import json
import time
import logging
from datetime import datetime
from typing import Optional, Literal

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse

from schemas import ProcessResponse
from services.yolo_service import yolo_service
from services.ocr_service import ocr_service
from services.edocr2_service import edocr2_service
from services.tag_extractor import tag_extractor
from services.equipment_mapping import equipment_mapper
from services.excel_report import excel_report_service
from services.pdf_report import pdf_report_service
from rule_loader import rule_loader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

# OCR 소스 타입
OCRSource = Literal["paddleocr", "edocr2", "both"]


@router.post("/detect")
async def detect_pid_symbols(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    model_type: str = Form(default="pid_class_aware", description="YOLO 모델 타입"),
    confidence: float = Form(default=0.1, description="검출 신뢰도 임계값"),
    use_sahi: bool = Form(default=True, description="SAHI 슬라이싱 사용"),
    visualize: bool = Form(default=True, description="시각화 이미지 생성"),
):
    """
    YOLO로 P&ID 심볼 검출만 수행

    이미지에서 P&ID 심볼을 검출하고 장비 매핑 결과 반환
    """
    start_time = time.time()

    try:
        image_data = await file.read()
        logger.info(f"Received image: {file.filename}, size={len(image_data)} bytes")

        # YOLO 검출
        yolo_result = await yolo_service.detect_pid_symbols(
            image_data=image_data,
            model_type=model_type,
            confidence=confidence,
            use_sahi=use_sahi,
            visualize=visualize,
        )

        if not yolo_result.success:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error=yolo_result.error,
            )

        # 장비 매핑
        equipment_map = yolo_service.map_symbols_to_equipment(yolo_result.detections)
        equipment_list = yolo_service.get_detected_equipment_list(yolo_result.detections)

        return ProcessResponse(
            success=True,
            data={
                "yolo": {
                    "model_type": model_type,
                    "total_detections": yolo_result.total_detections,
                    "class_counts": yolo_result.class_counts,
                    "processing_time": yolo_result.processing_time,
                },
                "detections": [
                    {
                        "class_name": d.class_name,
                        "class_id": d.class_id,
                        "confidence": round(d.confidence, 3),
                        "bbox": d.bbox,
                        "center": d.center,
                    }
                    for d in yolo_result.detections
                ],
                "equipment": {
                    "detected": equipment_list,
                    "count": len(equipment_list),
                    "mapping": equipment_map,
                },
                "visualized_image": yolo_result.visualized_image,
            },
            processing_time=round(time.time() - start_time, 3),
        )

    except Exception as e:
        logger.error(f"YOLO detection error: {e}", exc_info=True)
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e),
        )


@router.post("/ocr")
async def extract_ocr_text(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    ocr_source: str = Form(default="edocr2", description="OCR 소스 (paddleocr, edocr2, both)"),
    extract_dimensions: bool = Form(default=True, description="치수 추출 (eDOCr2)"),
    extract_gdt: bool = Form(default=True, description="GD&T 추출 (eDOCr2)"),
    extract_text: bool = Form(default=True, description="텍스트 추출"),
    visualize: bool = Form(default=False, description="시각화 이미지 생성"),
):
    """
    OCR 텍스트 추출 (eDOCr2 또는 PaddleOCR)

    - eDOCr2: 기계도면 특화 (치수, GD&T, 텍스트)
    - PaddleOCR: 범용 OCR
    - both: 두 결과 통합
    """
    start_time = time.time()

    try:
        image_data = await file.read()
        logger.info(f"OCR extraction: {file.filename}, source={ocr_source}")

        paddle_texts = []
        edocr2_texts = []
        edocr2_data = {}

        # PaddleOCR
        if ocr_source in ["paddleocr", "both"]:
            paddle_results = await ocr_service.extract_text_from_image(image_data, "en")
            if paddle_results:
                paddle_texts = [r.text for r in paddle_results]
                logger.info(f"PaddleOCR: {len(paddle_texts)} texts")

        # eDOCr2
        if ocr_source in ["edocr2", "both"]:
            edocr2_result = await edocr2_service.extract_from_image(
                image_data=image_data,
                extract_dimensions=extract_dimensions,
                extract_gdt=extract_gdt,
                extract_text=extract_text,
                visualize=visualize,
            )

            if edocr2_result.success:
                edocr2_texts = edocr2_service.get_all_texts(edocr2_result)
                edocr2_data = {
                    "dimensions": [
                        {
                            "value": d.value,
                            "tolerance": d.tolerance,
                            "unit": d.unit,
                            "type": d.dim_type,
                            "bbox": d.bbox,
                            "confidence": d.confidence,
                        }
                        for d in edocr2_result.dimensions
                    ],
                    "gdt_symbols": [
                        {
                            "symbol": g.symbol,
                            "type": g.gdt_type,
                            "tolerance": g.tolerance,
                            "datum": g.datum,
                            "bbox": g.bbox,
                            "confidence": g.confidence,
                        }
                        for g in edocr2_result.gdt_symbols
                    ],
                    "text_blocks": [
                        {
                            "text": t.text,
                            "bbox": t.bbox,
                            "confidence": t.confidence,
                        }
                        for t in edocr2_result.text_blocks
                    ],
                    "drawing_number": edocr2_result.drawing_number,
                    "material": edocr2_result.material,
                    "visualized_image": edocr2_result.visualized_image,
                    "processing_time": edocr2_result.processing_time,
                }
                logger.info(f"eDOCr2: {len(edocr2_texts)} texts, {len(edocr2_result.dimensions)} dims, {len(edocr2_result.gdt_symbols)} GD&T")

        # 통합
        combined_texts = list(set(paddle_texts + edocr2_texts))

        # 태그 추출
        extraction_result = tag_extractor.extract_from_texts(combined_texts)
        tags = [t.tag for t in extraction_result.tags]

        return ProcessResponse(
            success=True,
            data={
                "ocr_source": ocr_source,
                "paddleocr": {
                    "texts": paddle_texts,
                    "count": len(paddle_texts),
                } if ocr_source in ["paddleocr", "both"] else None,
                "edocr2": edocr2_data if ocr_source in ["edocr2", "both"] else None,
                "combined": {
                    "texts": combined_texts,
                    "count": len(combined_texts),
                    "tags": tags,
                    "tag_count": len(tags),
                    "product_type": extraction_result.product_type,
                },
            },
            processing_time=round(time.time() - start_time, 3),
        )

    except Exception as e:
        logger.error(f"OCR extraction error: {e}", exc_info=True)
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e),
        )


@router.post("/validate")
async def validate_pid_with_yolo(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    model_type: str = Form(default="pid_class_aware", description="YOLO 모델 타입"),
    confidence: float = Form(default=0.1, description="YOLO 검출 신뢰도"),
    product_type: str = Form(default="AUTO", description="제품 유형 (ECS, HYCHLOR, AUTO)"),
    ship_type: str = Form(default=None, description="선종"),
    class_society: str = Form(default=None, description="선급"),
    project_type: str = Form(default=None, description="프로젝트 유형"),
    use_ocr: bool = Form(default=True, description="OCR 추가 검증 사용"),
    ocr_source: str = Form(default="edocr2", description="OCR 소스 (paddleocr, edocr2, both)"),
):
    """
    YOLO + OCR 통합 P&ID 설계 검증

    1. YOLO로 심볼 검출
    2. (선택) OCR로 텍스트 추출
    3. 검출 결과 통합
    4. 설계 규칙 검증
    """
    start_time = time.time()

    try:
        image_data = await file.read()
        logger.info(f"Pipeline validation: {file.filename}, size={len(image_data)} bytes")

        # ========== Step 1: YOLO 검출 ==========
        yolo_result = await yolo_service.detect_pid_symbols(
            image_data=image_data,
            model_type=model_type,
            confidence=confidence,
            use_sahi=True,
            visualize=True,
        )

        yolo_equipment = []
        yolo_texts = []

        if yolo_result.success:
            yolo_equipment = yolo_service.get_detected_equipment_list(
                yolo_result.detections, min_confidence=0.3
            )
            yolo_texts = yolo_service.generate_ocr_texts_from_detections(
                yolo_result.detections
            )
            logger.info(f"YOLO detected {len(yolo_equipment)} equipment types")

        # ========== Step 2: OCR 텍스트 추출 (선택) ==========
        ocr_texts = []
        ocr_tags = []
        edocr2_data = {}

        if use_ocr:
            # PaddleOCR
            if ocr_source in ["paddleocr", "both"]:
                paddle_results = await ocr_service.extract_text_from_image(image_data, "en")
                if paddle_results:
                    ocr_texts.extend([r.text for r in paddle_results])
                    logger.info(f"PaddleOCR: {len(paddle_results)} texts")

            # eDOCr2
            if ocr_source in ["edocr2", "both"]:
                edocr2_result = await edocr2_service.extract_from_image(
                    image_data=image_data,
                    extract_dimensions=True,
                    extract_gdt=True,
                    extract_text=True,
                    visualize=False,
                )

                if edocr2_result.success:
                    edocr2_texts = edocr2_service.get_all_texts(edocr2_result)
                    ocr_texts.extend(edocr2_texts)
                    edocr2_data = {
                        "dimensions_count": len(edocr2_result.dimensions),
                        "gdt_count": len(edocr2_result.gdt_symbols),
                        "text_blocks_count": len(edocr2_result.text_blocks),
                        "drawing_number": edocr2_result.drawing_number,
                        "processing_time": edocr2_result.processing_time,
                    }
                    logger.info(f"eDOCr2: {len(edocr2_texts)} texts, {len(edocr2_result.dimensions)} dims")

            # 중복 제거
            ocr_texts = list(set(ocr_texts))

            # 태그 추출
            extraction_result = tag_extractor.extract_from_texts(ocr_texts)
            ocr_tags = [t.tag for t in extraction_result.tags]

            # 제품 유형 자동 결정
            if product_type.upper() == "AUTO":
                product_type = extraction_result.product_type

        logger.info(f"OCR extracted {len(ocr_texts)} texts, {len(ocr_tags)} tags (source: {ocr_source})")

        # ========== Step 3: 검출 결과 통합 ==========
        # YOLO + OCR 결과 병합
        combined_texts = list(set(yolo_texts + ocr_texts + ocr_tags))

        # 제품 유형 결정
        detected_product_type = product_type.upper() if product_type.upper() != "AUTO" else "ECS"

        # ========== Step 4: 규칙 검증 ==========
        rules = rule_loader.get_rules_filtered(
            product_type=detected_product_type,
            ship_type=ship_type,
            class_society=class_society,
            project_type=project_type,
        )

        violations = []
        passed = []
        skipped = []

        # 장비 존재 여부 캐시
        equipment_exists_cache = {}

        def check_equipment_exists(eq_name: str) -> tuple:
            if eq_name in equipment_exists_cache:
                return equipment_exists_cache[eq_name]

            # 1. YOLO 검출 결과에서 확인
            if eq_name in yolo_equipment:
                equipment_exists_cache[eq_name] = (True, [eq_name], "yolo")
                return True, [eq_name], "yolo"

            # 2. equipment_mapper로 텍스트 매칭
            match = equipment_mapper.find_tags_for_equipment(eq_name, combined_texts)
            if match.matched_tags:
                equipment_exists_cache[eq_name] = (True, match.matched_tags, match.match_type)
                return True, match.matched_tags, match.match_type

            # 3. 직접 텍스트 검색
            for text in combined_texts:
                if eq_name.upper() in text.upper():
                    equipment_exists_cache[eq_name] = (True, [text], "text_match")
                    return True, [text], "text_match"

            equipment_exists_cache[eq_name] = (False, [], "not_found")
            return False, [], "not_found"

        # 규칙별 검증
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

            # check_logic 처리
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
                    exists, tags, match_type = check_equipment_exists(eq)
                    if exists:
                        any_exists = True
                        passed.append({
                            "rule_id": rule.get("rule_id"),
                            "rule_name": rule.get("name"),
                            "equipment": eq,
                            "match_type": f"or_exists ({match_type})",
                            "matched_tags": tags,
                        })
                        break
                if not any_exists:
                    context_check = rule.get("context_check", "")
                    if context_check and not any(context_check.upper() in t.upper() for t in combined_texts):
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
                    exists, tags, match_type = check_equipment_exists(eq)
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
                    exists, tags, match_type = check_equipment_exists(eq)
                    passed.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "match_type": "optional" if not exists else match_type,
                        "matched_tags": tags if exists else [],
                        "reason": "옵션 장비" if not exists else None,
                    })
                continue

            # exists (기본)
            for eq in equipment_list:
                exists, tags, match_type = check_equipment_exists(eq)
                if exists:
                    passed.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "match_type": match_type,
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

        total_checked = len(violations) + len(passed)
        pass_rate = round(len(passed) / total_checked * 100, 1) if total_checked > 0 else 0

        return ProcessResponse(
            success=True,
            data={
                "pipeline": {
                    "yolo_enabled": True,
                    "ocr_enabled": use_ocr,
                    "ocr_source": ocr_source if use_ocr else None,
                    "model_type": model_type,
                },
                "detection": {
                    "yolo_detections": yolo_result.total_detections if yolo_result.success else 0,
                    "yolo_equipment": yolo_equipment,
                    "ocr_texts": len(ocr_texts),
                    "ocr_tags": len(ocr_tags),
                    "combined_sources": len(combined_texts),
                    "edocr2": edocr2_data if edocr2_data else None,
                },
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
                "visualized_image": yolo_result.visualized_image if yolo_result.success else None,
            },
            processing_time=round(time.time() - start_time, 3),
        )

    except Exception as e:
        logger.error(f"Pipeline validation error: {e}", exc_info=True)
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e),
        )


@router.post("/validate/export")
async def validate_and_export(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    model_type: str = Form(default="pid_class_aware", description="YOLO 모델 타입"),
    confidence: float = Form(default=0.1, description="YOLO 검출 신뢰도"),
    product_type: str = Form(default="AUTO", description="제품 유형"),
    ship_type: str = Form(default=None, description="선종"),
    class_society: str = Form(default=None, description="선급"),
    project_type: str = Form(default=None, description="프로젝트 유형"),
    ship_name: str = Form(default="", description="선명"),
    drawing_no: str = Form(default="", description="도면번호"),
    ocr_source: str = Form(default="edocr2", description="OCR 소스 (paddleocr, edocr2, both)"),
    export_format: str = Form(default="excel", description="내보내기 형식 (excel, pdf)"),
    report_type: str = Form(default="summary", description="리포트 유형 (summary, checklist)"),
):
    """
    YOLO + OCR 검증 후 리포트 내보내기

    파이프라인 검증 실행 후 Excel 또는 PDF 리포트 생성
    """
    try:
        image_data = await file.read()

        # 파이프라인 검증 실행 (내부 로직 재사용)
        # ... (validate_pid_with_yolo와 동일한 로직)

        # YOLO 검출
        yolo_result = await yolo_service.detect_pid_symbols(
            image_data=image_data,
            model_type=model_type,
            confidence=confidence,
            use_sahi=True,
            visualize=False,
        )

        yolo_equipment = []
        yolo_texts = []

        if yolo_result.success:
            yolo_equipment = yolo_service.get_detected_equipment_list(
                yolo_result.detections, min_confidence=0.3
            )
            yolo_texts = yolo_service.generate_ocr_texts_from_detections(
                yolo_result.detections
            )

        # OCR 추출 (ocr_source에 따라)
        ocr_texts = []

        # PaddleOCR
        if ocr_source in ["paddleocr", "both"]:
            paddle_results = await ocr_service.extract_text_from_image(image_data, "en")
            if paddle_results:
                ocr_texts.extend([r.text for r in paddle_results])

        # eDOCr2
        if ocr_source in ["edocr2", "both"]:
            edocr2_result = await edocr2_service.extract_from_image(
                image_data=image_data,
                extract_dimensions=True,
                extract_gdt=True,
                extract_text=True,
                visualize=False,
            )
            if edocr2_result.success:
                ocr_texts.extend(edocr2_service.get_all_texts(edocr2_result))

        # 중복 제거
        ocr_texts = list(set(ocr_texts))

        # 태그 추출
        extraction_result = tag_extractor.extract_from_texts(ocr_texts)
        ocr_tags = [t.tag for t in extraction_result.tags]

        if product_type.upper() == "AUTO":
            product_type = extraction_result.product_type if ocr_texts else "ECS"

        detected_product_type = product_type.upper()

        # 통합 텍스트
        combined_texts = list(set(yolo_texts + ocr_texts + ocr_tags))

        # 규칙 로드 및 검증
        rules = rule_loader.get_rules_filtered(
            product_type=detected_product_type,
            ship_type=ship_type,
            class_society=class_society,
            project_type=project_type,
        )

        violations = []
        passed = []
        skipped = []
        equipment_exists_cache = {}

        def check_equipment_exists(eq_name: str) -> tuple:
            if eq_name in equipment_exists_cache:
                return equipment_exists_cache[eq_name]

            if eq_name in yolo_equipment:
                equipment_exists_cache[eq_name] = (True, [eq_name], "yolo")
                return True, [eq_name], "yolo"

            match = equipment_mapper.find_tags_for_equipment(eq_name, combined_texts)
            if match.matched_tags:
                equipment_exists_cache[eq_name] = (True, match.matched_tags, match.match_type)
                return True, match.matched_tags, match.match_type

            equipment_exists_cache[eq_name] = (False, [], "not_found")
            return False, [], "not_found"

        # 규칙 검증 (간소화)
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

            if check_logic == "optional":
                for eq in equipment_list:
                    exists, tags, match_type = check_equipment_exists(eq)
                    passed.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "match_type": match_type if exists else "optional",
                        "matched_tags": tags,
                    })
                continue

            for eq in equipment_list:
                exists, tags, match_type = check_equipment_exists(eq)
                if exists:
                    passed.append({
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("name"),
                        "equipment": eq,
                        "match_type": match_type,
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

        # 결과 구성
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

        # 리포트 생성
        if export_format == "pdf":
            if report_type == "checklist":
                all_rules = rule_loader.load_all_rules()
                report_bytes = pdf_report_service.generate_checklist_report(
                    validation_data, list(all_rules.values()), project_info
                )
                filename = f"BWMS_Pipeline_Checklist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            else:
                report_bytes = pdf_report_service.generate_validation_report(
                    validation_data, project_info
                )
                filename = f"BWMS_Pipeline_Validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            media_type = "application/pdf"
        else:
            if report_type == "checklist":
                all_rules = rule_loader.load_all_rules()
                report_bytes = excel_report_service.generate_checklist_report(
                    validation_data, list(all_rules.values()), project_info
                )
                filename = f"BWMS_Pipeline_Checklist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            else:
                report_bytes = excel_report_service.generate_validation_report(
                    validation_data, project_info
                )
                filename = f"BWMS_Pipeline_Validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        return StreamingResponse(
            io.BytesIO(report_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Pipeline export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
