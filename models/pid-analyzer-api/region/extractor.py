"""
Region Text Extractor
영역-텍스트 매칭 및 추출 엔진

저자: Claude AI (Opus 4.5)
생성일: 2025-12-29
리팩토링: 2025-12-31
"""
import logging
from typing import List, Dict, Any, Optional, Tuple

from .models import (
    ExtractionPattern,
    RegionTextPattern,
    RegionCriteria,
    ExtractionRule,
    MatchedRegion,
)
from .rule_manager import RuleManager

logger = logging.getLogger(__name__)


class RegionTextExtractor:
    """영역-텍스트 매칭 및 추출 엔진"""

    def __init__(self, rule_manager: RuleManager = None):
        self.rule_manager = rule_manager or RuleManager()

    def _bbox_contains_point(self, bbox: List[float], point: Tuple[float, float], margin: float = 10) -> bool:
        """bbox가 점을 포함하는지 확인 (마진 포함)"""
        if len(bbox) < 4:
            return False

        x1, y1, x2, y2 = bbox[:4]
        px, py = point

        return (x1 - margin) <= px <= (x2 + margin) and (y1 - margin) <= py <= (y2 + margin)

    def _get_text_center(self, text_item: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """OCR 텍스트 아이템의 중심점 계산"""
        # PaddleOCR 형식: bbox가 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        bbox = text_item.get("bbox", text_item.get("box", []))

        if not bbox:
            return None

        if isinstance(bbox[0], list):
            # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] 형식
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        elif len(bbox) >= 4:
            # [x1, y1, x2, y2] 형식
            return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

        return None

    def _calculate_region_area(self, region: Dict[str, Any]) -> float:
        """영역 면적 계산"""
        bbox = region.get("bbox", region.get("bounding_box", []))
        if len(bbox) < 4:
            return 0

        x1, y1, x2, y2 = bbox[:4]
        return abs(x2 - x1) * abs(y2 - y1)

    def _region_matches_criteria(self, region: Dict[str, Any], criteria: RegionCriteria) -> bool:
        """영역이 기준과 매칭되는지 확인"""
        # 가상 영역은 항상 통과 (이미 텍스트 패턴 매칭됨)
        if region.get("is_virtual"):
            return True

        # 라인 스타일 확인 - 여러 필드명 지원
        region_style = region.get("line_style") or region.get("enclosing_line_style") or region.get("style", "unknown")

        # "mixed" 스타일은 점선 영역으로 간주 (dashed, dash_dot 포함 시)
        if region_style == "mixed":
            # lines_inside에서 dashed/dash_dot 라인이 있는지 확인
            lines_inside = region.get("lines_inside", [])
            has_dashed = any(
                line.get("line_style") in criteria.line_styles
                for line in lines_inside
            )
            if has_dashed:
                region_style = "dashed"  # mixed이지만 dashed 라인 포함

        if region_style not in criteria.line_styles and region_style != "mixed":
            return False

        # 면적 확인
        area = self._calculate_region_area(region)
        if area < criteria.min_area:
            return False

        if criteria.max_area and area > criteria.max_area:
            return False

        # 종횡비 확인
        bbox = region.get("bbox", region.get("bounding_box", []))
        if len(bbox) >= 4:
            width = abs(bbox[2] - bbox[0])
            height = abs(bbox[3] - bbox[1])
            if height > 0:
                aspect_ratio = width / height

                if criteria.aspect_ratio_min and aspect_ratio < criteria.aspect_ratio_min:
                    return False
                if criteria.aspect_ratio_max and aspect_ratio > criteria.aspect_ratio_max:
                    return False

        return True

    def _find_texts_in_region(self, region_bbox: List[float], texts: List[Dict], margin: float = 20) -> List[Dict]:
        """영역 내에 있는 텍스트 찾기"""
        texts_in_region = []

        for text_item in texts:
            center = self._get_text_center(text_item)
            if center and self._bbox_contains_point(region_bbox, center, margin):
                texts_in_region.append(text_item)

        return texts_in_region

    def _region_matches_text_patterns(
        self,
        region_texts: List[Dict],
        patterns: List[RegionTextPattern]
    ) -> Tuple[bool, List[str]]:
        """영역 내 텍스트가 패턴과 매칭되는지 확인

        개선된 매칭 로직:
        1. 개별 텍스트가 패턴과 매칭되는지 확인
        2. 영역 내 모든 텍스트를 결합하여 패턴과 매칭 (OCR이 텍스트를 분리할 경우 대응)
        """
        if not patterns:
            return True, []  # 패턴이 없으면 모든 영역 매칭

        matched_texts = []

        # 1단계: 개별 텍스트 매칭 확인
        for text_item in region_texts:
            text = text_item.get("text", "")

            for pattern in patterns:
                if pattern.matches(text):
                    matched_texts.append(text)
                    break

        # 1단계에서 매칭되면 바로 반환
        if matched_texts:
            return True, matched_texts

        # 2단계: 영역 내 모든 텍스트를 결합하여 매칭 시도
        # OCR이 "SIGNAL"과 "FOR BWMS"를 분리해서 반환하는 경우 대응
        all_texts = [item.get("text", "") for item in region_texts]
        combined_text = " ".join(all_texts)
        combined_text_nospace = "".join(all_texts)  # 공백 없는 버전도 시도

        for pattern in patterns:
            if pattern.matches(combined_text) or pattern.matches(combined_text_nospace):
                # 매칭 성공 시, 패턴에 포함된 키워드를 가진 텍스트만 반환
                # 예: "SIGNAL FOR BWMS" 패턴 -> "SIGNAL"과 "FOR BWMS" 텍스트만 반환
                pattern_keywords = pattern.pattern.replace("_", " ").replace(".*", " ").split()
                relevant_texts = []
                for text in all_texts:
                    text_check = text.upper() if pattern.case_insensitive else text
                    for keyword in pattern_keywords:
                        keyword_check = keyword.upper() if pattern.case_insensitive else keyword
                        if keyword_check in text_check:
                            if text not in relevant_texts:
                                relevant_texts.append(text)
                            break
                if relevant_texts:
                    return True, relevant_texts
                # 키워드 매칭 실패 시 첫 번째 텍스트만 반환
                return True, [all_texts[0]] if all_texts else []

        # 3단계: 개별 패턴 키워드들이 각각 존재하는지 확인
        # 예: "SIGNAL FOR BWMS" -> "SIGNAL", "FOR", "BWMS" 각각 존재 확인
        # 단, 실제 매칭된 텍스트만 반환 (밸브 태그 등은 제외)
        for pattern in patterns:
            if not pattern.is_regex:
                # 단순 문자열 패턴의 경우, 키워드 분리
                keywords = pattern.pattern.replace("_", " ").split()
                found_all = True
                found_keywords = []  # 실제 키워드가 포함된 텍스트만 저장

                for keyword in keywords:
                    keyword_upper = keyword.upper() if pattern.case_insensitive else keyword
                    found = False
                    for text in all_texts:
                        text_check = text.upper() if pattern.case_insensitive else text
                        # 키워드가 텍스트에 포함되어 있는지 확인
                        if keyword_upper in text_check:
                            found = True
                            # 해당 텍스트가 키워드를 포함하면 추가
                            if text not in found_keywords:
                                found_keywords.append(text)
                            break
                    if not found:
                        found_all = False
                        break

                if found_all and found_keywords:
                    # 찾은 키워드 텍스트만 반환 (밸브 태그 등 다른 텍스트는 제외)
                    return True, found_keywords

        # 최소 1개의 패턴이 매칭되어야 함
        return len(matched_texts) > 0, matched_texts

    def _extract_from_texts(
        self,
        texts: List[Dict],
        patterns: List[ExtractionPattern],
        exclude_texts: List[str] = None
    ) -> List[Dict[str, Any]]:
        """텍스트에서 패턴에 매칭되는 항목 추출

        개선: 공백으로 분리된 여러 밸브도 처리 (예: "BAV29 BAV34")
        """
        if exclude_texts is None:
            exclude_texts = []

        extracted = []
        seen = set()  # 중복 방지

        # 우선순위 순으로 패턴 정렬
        sorted_patterns = sorted(patterns, key=lambda p: p.priority, reverse=True)

        for text_item in texts:
            text = text_item.get("text", "").strip()

            # 영역 식별 텍스트는 제외
            if any(exc.lower() in text.lower() for exc in exclude_texts):
                continue

            # 너무 긴 텍스트는 제외 (일반적으로 태그는 짧음)
            if len(text) > 30:  # 증가: 여러 밸브가 결합된 경우 대응
                continue

            # 공백으로 분리하여 각 부분을 개별 매칭 시도
            text_parts = text.split()

            for part in text_parts:
                part = part.strip()
                if not part:
                    continue

                for pattern in sorted_patterns:
                    match_result = pattern.match(part)
                    if match_result:
                        matched_text = match_result["matched_text"]

                        if matched_text not in seen:
                            seen.add(matched_text)

                            # 텍스트 위치 정보 추출
                            center = self._get_text_center(text_item)
                            bbox = text_item.get("bbox", text_item.get("box", []))

                            extracted.append({
                                "id": matched_text,
                                "type": pattern.type,
                                "matched_text": matched_text,
                                "original_text": text,
                                "confidence": text_item.get("confidence", 1.0),
                                "center": center,
                                "bbox": bbox,
                                "pattern_description": pattern.description,
                            })
                        break  # 한 부분당 하나의 패턴만 매칭

        return extracted

    def _find_text_based_regions(
        self,
        texts: List[Dict],
        patterns: List[RegionTextPattern],
        region_size: Tuple[int, int] = (500, 300)
    ) -> List[Dict]:
        """
        OCR 텍스트에서 패턴을 찾아 가상 영역 생성

        Line Detector가 영역을 검출하지 못한 경우의 폴백으로 사용
        개선: "SIGNAL"과 "FOR BWMS"가 분리된 경우도 처리

        Args:
            texts: OCR 텍스트 목록
            patterns: 영역 식별 패턴
            region_size: 가상 영역 크기 (width, height)
        """
        virtual_regions = []
        used_positions = set()  # 중복 방지 (y좌표 기반)

        # 1단계: 개별 텍스트가 패턴에 매칭되는 경우
        for text_item in texts:
            text = text_item.get("text", "")

            for pattern in patterns:
                if pattern.matches(text):
                    center = self._get_text_center(text_item)
                    if center:
                        cx, cy = center
                        # 비슷한 y 위치에 이미 영역이 있으면 건너뜀
                        y_key = int(cy / 50) * 50
                        if y_key in used_positions:
                            continue
                        used_positions.add(y_key)

                        w, h = region_size

                        virtual_region = {
                            "bbox": [cx - w/2, cy, cx + w/2, cy + h],
                            "line_style": "dashed",
                            "enclosing_line_style": "dashed",
                            "style": "dashed",
                            "area": w * h,
                            "is_virtual": True,
                            "source_text": text
                        }
                        virtual_regions.append(virtual_region)
                        logger.info(f"Created virtual region from text '{text}' at {center}")
                        break

        # 2단계: "SIGNAL"과 "FOR BWMS"가 분리된 경우 처리
        # SIGNAL 텍스트를 먼저 찾고, 근처에 FOR BWMS가 있는지 확인
        signal_texts = []
        for_bwms_texts = []

        for text_item in texts:
            text = text_item.get("text", "").upper()
            center = self._get_text_center(text_item)
            if not center:
                continue

            if "SIGNAL" in text and "FOR" not in text and "BWMS" not in text:
                signal_texts.append({"text": text_item.get("text", ""), "center": center})
            elif ("FOR" in text and "BWMS" in text) or "FORBWMS" in text.replace(" ", ""):
                for_bwms_texts.append({"text": text_item.get("text", ""), "center": center})

        # SIGNAL과 FOR BWMS가 y 좌표 기준 50픽셀 이내에 있으면 결합
        for signal in signal_texts:
            sx, sy = signal["center"]
            y_key = int(sy / 50) * 50

            # 이미 처리된 위치면 건너뜀
            if y_key in used_positions:
                continue

            for for_bwms in for_bwms_texts:
                fx, fy = for_bwms["center"]
                if abs(sy - fy) < 50:  # 같은 줄에 있음
                    used_positions.add(y_key)
                    w, h = region_size

                    # 두 텍스트의 중간점 사용
                    mid_x = (sx + fx) / 2
                    mid_y = min(sy, fy)

                    virtual_region = {
                        "bbox": [mid_x - w/2, mid_y, mid_x + w/2, mid_y + h],
                        "line_style": "dashed",
                        "enclosing_line_style": "dashed",
                        "style": "dashed",
                        "area": w * h,
                        "is_virtual": True,
                        "source_text": f"{signal['text']} {for_bwms['text']}"
                    }
                    virtual_regions.append(virtual_region)
                    logger.info(f"Created combined virtual region from '{signal['text']}' + '{for_bwms['text']}' at y={mid_y}")
                    break

        return virtual_regions

    def extract(
        self,
        regions: List[Dict],
        texts: List[Dict],
        rule_ids: List[str] = None,
        text_margin: float = 30,
        region_expand_margin: float = 150
    ) -> Dict[str, Any]:
        """
        영역에서 규칙에 따라 텍스트 추출

        Args:
            regions: Line Detector에서 검출된 영역 목록
            texts: PaddleOCR에서 검출된 텍스트 목록
            rule_ids: 적용할 규칙 ID 목록 (None이면 활성화된 모든 규칙)
            text_margin: 텍스트 매칭 시 마진 (픽셀)
            region_expand_margin: 매칭된 영역 확장 마진 (픽셀) - 영역 외 밸브 캡처용

        Returns:
            추출 결과 (규칙별 매칭 영역 및 추출 항목)
        """
        # 적용할 규칙 결정
        if rule_ids:
            rules = [self.rule_manager.get_rule(rid) for rid in rule_ids]
            rules = [r for r in rules if r is not None and r.enabled]
        else:
            rules = self.rule_manager.get_enabled_rules()

        if not rules:
            return {
                "success": True,
                "message": "No enabled rules found",
                "results": [],
                "statistics": {}
            }

        results_by_rule = {}

        # 가상 영역 생성을 위한 텍스트 기반 폴백 준비
        # Line Detector가 영역을 찾지 못한 경우만 폴백 사용
        all_virtual_regions = []
        if len(regions) == 0:
            logger.info("No regions from Line Detector, using text-based virtual regions")
            for rule in rules:
                if rule.region_text_patterns:
                    virtual_regions = self._find_text_based_regions(
                        texts,
                        rule.region_text_patterns,
                        region_size=(600, 400)  # 더 큰 영역으로 밸브 캡처
                    )
                    all_virtual_regions.extend(virtual_regions)
            logger.info(f"Created {len(all_virtual_regions)} virtual regions from OCR text")

        for rule in rules:
            matched_regions = []
            logger.info(f"Processing rule: {rule.id}")
            criteria_passed = 0
            texts_found = 0
            pattern_matched = 0

            # Line Detector 영역 + 가상 영역 결합
            combined_regions = list(regions) + all_virtual_regions
            logger.info(f"Processing {len(regions)} detector regions + {len(all_virtual_regions)} virtual regions")

            for region_idx, region in enumerate(combined_regions):
                # 1. 영역이 기준에 맞는지 확인
                if not self._region_matches_criteria(region, rule.region_criteria):
                    continue
                criteria_passed += 1

                # 2. 영역 내 텍스트 찾기 (영역 확장 마진 적용)
                region_bbox = region.get("bbox", region.get("bounding_box", []))
                if len(region_bbox) < 4:
                    continue

                # 영역 확장 (상하좌우 모두 마진 추가)
                # P&ID에서 밸브들이 영역 외곽에 배치될 수 있음
                expanded_bbox = [
                    region_bbox[0] - region_expand_margin * 2,  # 왼쪽 확장 (더 크게)
                    region_bbox[1] - region_expand_margin,       # 위쪽 확장
                    region_bbox[2] + region_expand_margin * 2,   # 오른쪽 확장 (더 크게)
                    region_bbox[3] + region_expand_margin        # 아래쪽 확장
                ]

                texts_in_region = self._find_texts_in_region(expanded_bbox, texts, text_margin)

                if not texts_in_region:
                    continue
                texts_found += 1
                text_contents = [t.get("text", "") for t in texts_in_region]
                logger.debug(f"Region {region_idx} texts: {text_contents[:5]}")

                # 3. 텍스트 패턴 매칭 확인
                # 가상 영역은 이미 텍스트 패턴 기반으로 생성됨
                if region.get("is_virtual"):
                    matches = True
                    matched_pattern_texts = [region.get("source_text", "")]
                else:
                    matches, matched_pattern_texts = self._region_matches_text_patterns(
                        texts_in_region,
                        rule.region_text_patterns
                    )

                if not matches:
                    continue
                pattern_matched += 1
                is_virtual_tag = " (virtual)" if region.get("is_virtual") else ""
                logger.info(f"Region {region_idx}{is_virtual_tag} matched patterns: {matched_pattern_texts}")

                # 4. 추출 패턴 적용
                extracted_items = self._extract_from_texts(
                    texts_in_region,
                    rule.extraction_patterns,
                    exclude_texts=matched_pattern_texts  # 영역 식별 텍스트 제외
                )

                if extracted_items:
                    matched_regions.append(MatchedRegion(
                        region_id=region_idx,
                        rule_id=rule.id,
                        bbox=region_bbox,
                        region_texts=matched_pattern_texts,
                        extracted_items=extracted_items,
                        confidence=sum(i["confidence"] for i in extracted_items) / len(extracted_items)
                    ))
                    logger.info(f"Region {region_idx} extracted: {[i['id'] for i in extracted_items]}")

            logger.info(f"Rule {rule.id}: criteria_passed={criteria_passed}, texts_found={texts_found}, pattern_matched={pattern_matched}")

            if matched_regions:
                results_by_rule[rule.id] = {
                    "rule": rule.to_dict(),
                    "matched_regions": [
                        {
                            "region_id": mr.region_id,
                            "bbox": mr.bbox,
                            "region_texts": mr.region_texts,
                            "extracted_items": mr.extracted_items,
                            "confidence": mr.confidence
                        }
                        for mr in matched_regions
                    ],
                    "total_extracted": sum(len(mr.extracted_items) for mr in matched_regions)
                }

        # 통계 생성
        all_extracted = []
        for rule_result in results_by_rule.values():
            for region in rule_result["matched_regions"]:
                all_extracted.extend(region["extracted_items"])

        # 중복 제거 후 통합 리스트
        unique_items = {}
        for item in all_extracted:
            key = item["id"]
            if key not in unique_items:
                unique_items[key] = item

        return {
            "success": True,
            "results_by_rule": results_by_rule,
            "all_extracted_items": list(unique_items.values()),
            "statistics": {
                "total_regions": len(regions),
                "virtual_regions": len(all_virtual_regions),
                "combined_regions": len(regions) + len(all_virtual_regions),
                "total_texts": len(texts),
                "rules_applied": len(rules),
                "rules_matched": len(results_by_rule),
                "total_matched_regions": sum(
                    len(r["matched_regions"]) for r in results_by_rule.values()
                ),
                "total_extracted_items": len(unique_items)
            }
        }
