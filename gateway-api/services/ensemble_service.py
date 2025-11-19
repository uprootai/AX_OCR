"""
Ensemble Service

YOLO Crop OCR and ensemble strategies
"""
import time
import asyncio
import logging
import difflib
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


async def process_yolo_crop_ocr(
    image_bytes: bytes,
    yolo_detections: List[Dict],
    call_edocr2_ocr_func,
    crop_bbox_func,
    is_false_positive_func,
    dimension_class_ids: List[int] = [0, 1, 2, 3, 4, 5, 6],
    min_confidence: float = 0.5,
    padding: float = 0.1
) -> Dict[str, Any]:
    """
    YOLO 검출 객체별 개별 eDOCr2 OCR 처리

    각 YOLO 검출 영역을 crop하여 eDOCr2로 개별 OCR 수행

    Args:
        image_bytes: 원본 이미지
        yolo_detections: YOLO 검출 결과 리스트
        call_edocr2_ocr_func: eDOCr2 호출 함수
        crop_bbox_func: crop 함수
        is_false_positive_func: False positive 필터 함수
        dimension_class_ids: 치수 관련 클래스 ID 리스트
        min_confidence: OCR 최소 신뢰도 (현재 사용 안 함)
        padding: crop 시 패딩 비율

    Returns:
        OCR 결과 집계 (dimensions, total_texts, processing_time 등)
    """
    start_time = time.time()

    # 치수 관련 객체만 필터링
    dimension_detections = [
        d for d in yolo_detections
        if d.get('class_id', 99) in dimension_class_ids
    ]

    logger.info(f"YOLO Crop OCR: {len(dimension_detections)} dimension objects to process")

    if len(dimension_detections) == 0:
        return {
            "dimensions": [],
            "total_texts": 0,
            "crop_count": 0,
            "successful_crops": 0,
            "processing_time": time.time() - start_time
        }

    # 각 detection을 crop하고 병렬 OCR 처리
    crop_tasks = []
    task_metadata = []

    for idx, det in enumerate(dimension_detections):
        try:
            bbox = det['bbox']
            cropped_bytes = crop_bbox_func(image_bytes, bbox, padding)

            # 비동기 eDOCr2 OCR 호출 태스크 생성
            task = call_edocr2_ocr_func(
                cropped_bytes,
                f"crop_{idx}.png",
                extract_dimensions=True,
                extract_gdt=False,
                extract_text=True,
                extract_tables=False,
                visualize=False,
                language='eng',
                cluster_threshold=20
            )
            crop_tasks.append(task)
            task_metadata.append((idx, det))
        except Exception as e:
            logger.error(f"Crop failed for detection {idx}: {e}")
            continue

    # crop 실패로 tasks가 비어있으면 조기 반환
    if len(crop_tasks) == 0:
        logger.warning("All crops failed - no tasks to process")
        return {
            "dimensions": [],
            "total_texts": 0,
            "crop_count": len(dimension_detections),
            "successful_crops": 0,
            "processing_time": time.time() - start_time
        }

    # 진정한 병렬 실행 (asyncio.gather로 모든 태스크를 동시 실행)
    logger.info(f"Running {len(crop_tasks)} OCR tasks in parallel with asyncio.gather()")
    ocr_raw_results = await asyncio.gather(*crop_tasks, return_exceptions=True)

    # 결과 정리
    ocr_results = []
    for (idx, det), result in zip(task_metadata, ocr_raw_results):
        if isinstance(result, Exception):
            logger.error(f"OCR failed for crop {idx}: {result}")
            ocr_results.append({
                "crop_idx": idx,
                "yolo_detection": det,
                "status": "error",
                "error": str(result)
            })
        else:
            ocr_results.append({
                "crop_idx": idx,
                "yolo_detection": det,
                "ocr_result": result,
                "status": "success"
            })

    # 결과 집계 및 필터링
    all_dimensions = []
    successful_crops = sum(1 for r in ocr_results if r['status'] == 'success')

    for result in ocr_results:
        if result['status'] != 'success':
            continue

        ocr_data = result['ocr_result']

        # eDOCr2 응답 형식: dimensions 배열 직접 확인
        dimensions = ocr_data.get('dimensions', [])

        for dim in dimensions:
            # eDOCr2 dimension 구조: {value: str, unit: str, type: str, bbox: {...}, confidence: float}
            value = dim.get('value', '').strip()
            conf = dim.get('confidence', 1.0)

            # 필터링: 숫자 포함된 값만
            if any(c.isdigit() for c in value) and len(value) >= 1:
                # False Positive 필터링: 도면 메타데이터 제외
                if is_false_positive_func(value):
                    logger.debug(f"Filtered False Positive: '{value}'")
                    continue

                all_dimensions.append({
                    "value": value,
                    "unit": dim.get('unit', 'mm'),
                    "type": dim.get('type', 'dimension'),
                    "confidence": conf,
                    "crop_idx": result['crop_idx'],
                    "yolo_class": result['yolo_detection']['class_name'],
                    "bbox": dim.get('bbox')
                })

    # 신뢰도 순 정렬
    all_dimensions.sort(key=lambda x: x['confidence'], reverse=True)

    processing_time = time.time() - start_time

    failed_crops = len(dimension_detections) - successful_crops
    success_rate = (successful_crops / len(dimension_detections) * 100) if len(dimension_detections) > 0 else 0

    logger.info(
        f"YOLO Crop OCR completed: {len(all_dimensions)} dimensions from "
        f"{successful_crops}/{len(dimension_detections)} crops "
        f"({success_rate:.1f}% success) in {processing_time:.2f}s"
    )

    # 실패한 crop 정보 수집
    failed_crop_details = [
        {
            "crop_idx": r["crop_idx"],
            "yolo_class": r["yolo_detection"]["class_name"],
            "error": r["error"]
        }
        for r in ocr_results if r["status"] == "error"
    ]

    return {
        "dimensions": all_dimensions,
        "total_texts": len(all_dimensions),
        "crop_count": len(dimension_detections),
        "successful_crops": successful_crops,
        "failed_crops": failed_crops,
        "success_rate": success_rate,
        "failed_crop_details": failed_crop_details if failed_crops > 0 else [],
        "processing_time": processing_time
    }


def ensemble_ocr_results(
    yolo_crop_results: List[Dict],
    edocr_results: List[Dict],
    yolo_weight: float = 0.6,
    edocr_weight: float = 0.4,
    similarity_threshold: float = 0.7
) -> List[Dict]:
    """
    YOLO Crop OCR과 eDOCr v2 결과를 앙상블 융합

    전략:
    1. 두 결과에서 모두 발견된 치수: 높은 신뢰도로 채택
    2. 한쪽에만 있는 치수: 가중치 적용 후 임계값 이상이면 채택
    3. 유사한 치수 값: 더 높은 신뢰도 선택

    Args:
        yolo_crop_results: YOLO Crop OCR 결과 리스트
        edocr_results: eDOCr v2 결과 리스트
        yolo_weight: YOLO 결과 가중치 (기본 0.6 - 재현율 우수)
        edocr_weight: eDOCr 결과 가중치 (기본 0.4)
        similarity_threshold: 텍스트 유사도 임계값

    Returns:
        앙상블 병합된 치수 리스트
    """
    merged = []
    used_edocr = set()

    # YOLO 결과를 기준으로 병합
    for yolo_dim in yolo_crop_results:
        yolo_text = str(yolo_dim.get('value', '')).strip()
        yolo_conf = yolo_dim.get('confidence', 0) * yolo_weight

        # eDOCr 결과에서 유사한 항목 찾기
        best_match = None
        best_similarity = 0

        for idx, edocr_dim in enumerate(edocr_results):
            if idx in used_edocr:
                continue

            edocr_text = str(edocr_dim.get('value', '')).strip()
            similarity = difflib.SequenceMatcher(None, yolo_text, edocr_text).ratio()

            if similarity > best_similarity and similarity >= similarity_threshold:
                best_similarity = similarity
                best_match = (idx, edocr_dim, similarity)

        if best_match:
            # 두 결과가 유사함 - 더 높은 신뢰도 선택
            idx, edocr_dim, similarity = best_match
            edocr_conf = edocr_dim.get('confidence', 0.8) * edocr_weight

            if yolo_conf >= edocr_conf:
                merged_dim = yolo_dim.copy()
                merged_dim['confidence'] = min(1.0, yolo_conf + edocr_conf * similarity)
                merged_dim['source'] = 'yolo_crop_ocr'
                merged_dim['confirmed_by'] = 'edocr_v2'
            else:
                merged_dim = edocr_dim.copy()
                merged_dim['confidence'] = min(1.0, edocr_conf + yolo_conf * similarity)
                merged_dim['source'] = 'edocr_v2'
                merged_dim['confirmed_by'] = 'yolo_crop_ocr'

            merged.append(merged_dim)
            used_edocr.add(idx)
        else:
            # YOLO에만 있음
            if yolo_conf >= 0.3:
                merged_dim = yolo_dim.copy()
                merged_dim['source'] = 'yolo_crop_ocr'
                merged.append(merged_dim)

    # eDOCr에만 있는 항목 추가
    for idx, edocr_dim in enumerate(edocr_results):
        if idx not in used_edocr:
            edocr_conf = edocr_dim.get('confidence', 0.8) * edocr_weight
            if edocr_conf >= 0.4:
                merged_dim = edocr_dim.copy()
                merged_dim['source'] = 'edocr_v2'
                merged.append(merged_dim)

    # 신뢰도 순 정렬
    merged.sort(key=lambda x: x.get('confidence', 0), reverse=True)

    logger.info(
        f"Ensemble merged: {len(yolo_crop_results)} YOLO + "
        f"{len(edocr_results)} eDOCr → {len(merged)} total"
    )

    return merged
