"""Drawing Matcher Service - 도면 파일 매칭 서비스

BOM 항목의 도면번호를 PJT 폴더의 도면 파일과 매칭합니다.
파일명 패턴: "TD0062017 Rev.A(BEARING RING(T1,T2,T3)).pdf"
→ 도면번호: TD0062017
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class DrawingMatcher:
    """도면 파일 매칭 서비스"""

    # 지원하는 도면 파일 확장자
    DRAWING_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}

    def match_drawings(
        self, bom_items: List[Dict], drawing_folder: str
    ) -> List[Dict]:
        """BOM 항목 ↔ 도면 파일 매칭

        Args:
            bom_items: BOM 항목 목록 (bom_pdf_parser 출력)
            drawing_folder: 도면 폴더 경로

        Returns:
            매칭 결과가 추가된 BOM 항목 목록
        """
        folder = Path(drawing_folder)
        if not folder.exists():
            logger.error(f"도면 폴더를 찾을 수 없습니다: {drawing_folder}")
            return bom_items

        # 1. 폴더 스캔 → 도면번호:파일경로 맵
        file_map = self._scan_folder(folder)
        logger.info(f"도면 폴더 스캔 완료: {len(file_map)}개 파일 발견")

        # 2. 각 BOM 항목에 대해 매칭
        matched = 0
        for item in bom_items:
            drawing_number = item.get("drawing_number", "")
            if not drawing_number:
                continue

            # 정확 매칭
            match = file_map.get(drawing_number.upper())
            if match:
                item["matched_file"] = match
                matched += 1
            else:
                # 유사 매칭 시도 (접두사, 부분 일치)
                fuzzy_match = self._fuzzy_match(drawing_number, file_map)
                if fuzzy_match:
                    item["matched_file"] = fuzzy_match
                    matched += 1

        total_with_dwg = sum(
            1 for i in bom_items if i.get("drawing_number")
        )
        logger.info(
            f"도면 매칭 완료: {matched}/{total_with_dwg} 매칭 "
            f"({total_with_dwg - matched}개 미매칭)"
        )

        return bom_items

    def _scan_folder(self, folder: Path) -> Dict[str, str]:
        """폴더 재귀 스캔 → {도면번호(대문자): 파일경로} 맵

        파일명에서 도면번호 추출 패턴:
        - "TD0062017 Rev.A(BEARING RING).pdf" → TD0062017
        - "PDM002.pdf" → PDM002
        - "BOM_Z24018_110104001_BRG_R1.pdf" → Z24018
        """
        file_map: Dict[str, str] = {}
        revision_map: Dict[str, List[Tuple[str, str]]] = {}

        for file_path in folder.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in self.DRAWING_EXTENSIONS:
                continue

            filename = file_path.stem  # 확장자 제외

            # 도면번호 추출
            drawing_number = self._extract_drawing_number(filename)
            if not drawing_number:
                continue

            dwg_upper = drawing_number.upper()

            # 리비전 추출
            revision = self._extract_revision(filename)

            if dwg_upper not in revision_map:
                revision_map[dwg_upper] = []
            revision_map[dwg_upper].append((revision, str(file_path)))

        # 각 도면번호에 대해 최신 리비전 선택
        for dwg_number, revisions in revision_map.items():
            # 리비전 정렬 (A < B < C < D...)
            revisions.sort(key=lambda x: x[0], reverse=True)
            file_map[dwg_number] = revisions[0][1]  # 최신 리비전

            if len(revisions) > 1:
                logger.debug(
                    f"다중 리비전: {dwg_number} → "
                    f"{[r[0] for r in revisions]} "
                    f"(최신: {revisions[0][0]})"
                )

        return file_map

    def _extract_drawing_number(self, filename: str) -> Optional[str]:
        """파일명에서 도면번호 추출

        패턴:
        - TD0062017 Rev.A(...) → TD0062017
        - STMPS00095 → STMPS00095
        - PDM002 → PDM002
        - BOM_Z24018_110104001_... → BOM_Z24018_110104001 (BOM 파일은 제외)
        """
        # BOM 파일은 제외
        if filename.upper().startswith("BOM_"):
            return None

        # 패턴 1: "TD0062017 Rev.A(...)" 또는 "TD0062017 Rev.A"
        match = re.match(r'^([A-Z]{1,10}\d{3,10})', filename.upper())
        if match:
            return match.group(1)

        # 패턴 2: 숫자로 시작하는 경우 (110104001 등)
        match = re.match(r'^(\d{6,})', filename)
        if match:
            return match.group(1)

        # 패턴 3: 일반 코드 (PDM002 등)
        match = re.match(r'^([A-Za-z]+\d+)', filename)
        if match:
            return match.group(1).upper()

        return None

    def _extract_revision(self, filename: str) -> str:
        """파일명에서 리비전 추출

        "TD0062017 Rev.A(...)" → "A"
        "TD0062017 Rev.B(...)" → "B"
        리비전 없으면 → ""
        """
        match = re.search(r'Rev\.?\s*([A-Z])', filename, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return ""

    def _fuzzy_match(
        self, drawing_number: str, file_map: Dict[str, str]
    ) -> Optional[str]:
        """유사 매칭 (접두사/부분 일치)

        정확 매칭 실패 시 시도:
        1. 접두사 매칭: TD006 → TD0062017
        2. 부분 매칭: 62017 → TD0062017
        """
        dwg_upper = drawing_number.upper()

        # 접두사 매칭
        candidates = [
            (k, v) for k, v in file_map.items()
            if k.startswith(dwg_upper) or dwg_upper.startswith(k)
        ]
        if len(candidates) == 1:
            return candidates[0][1]

        # 부분 매칭 (숫자 부분만)
        numbers = re.findall(r'\d+', dwg_upper)
        if numbers:
            main_number = numbers[0]
            if len(main_number) >= 5:  # 5자리 이상일 때만
                candidates = [
                    (k, v) for k, v in file_map.items()
                    if main_number in k
                ]
                if len(candidates) == 1:
                    return candidates[0][1]

        return None

    def get_match_summary(self, bom_items: List[Dict]) -> Dict[str, Any]:
        """매칭 결과 요약"""
        total = len(bom_items)
        with_dwg = sum(1 for i in bom_items if i.get("drawing_number"))
        matched = sum(1 for i in bom_items if i.get("matched_file"))
        unmatched_items = [
            {
                "item_no": i.get("item_no"),
                "drawing_number": i.get("drawing_number"),
                "description": i.get("description"),
            }
            for i in bom_items
            if i.get("drawing_number") and not i.get("matched_file")
        ]

        return {
            "total_items": total,
            "items_with_drawing": with_dwg,
            "matched_count": matched,
            "unmatched_count": with_dwg - matched,
            "match_rate": round(matched / with_dwg * 100, 1) if with_dwg > 0 else 0,
            "unmatched_items": unmatched_items,
        }
