"""BOM PDF Parser Service - BOM PDF 파싱 서비스

BOM PDF를 파싱하여 계층 구조를 추출합니다.
행 배경색으로 계층을 구분:
- PINK (R>200, G<150, B<200): Assembly (조립체)
- BLUE (R<150, G<150, B>200): Subassembly (하위 조립체)
- WHITE (모든 채널>230 또는 색상 없음): Part (단품) → 견적 대상
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class BOMPDFParser:
    """BOM PDF 파싱 서비스"""

    # 색상 기준 (RGB, 0-255 스케일)
    COLOR_THRESHOLDS = {
        "pink": {"r_min": 200, "g_max": 170, "b_max": 200},
        "blue": {"r_max": 150, "g_max": 170, "b_min": 200},
    }

    def parse_bom_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """BOM PDF → 구조화된 계층 데이터

        Args:
            pdf_path: BOM PDF 파일 경로

        Returns:
            {
                "source_file": str,
                "total_items": int,
                "assembly_count": int,
                "subassembly_count": int,
                "part_count": int,
                "items": List[Dict],  # flat 목록
                "hierarchy": List[Dict],  # 트리 구조
            }
        """
        import fitz  # PyMuPDF

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"BOM PDF를 찾을 수 없습니다: {pdf_path}")

        doc = fitz.open(str(pdf_path))
        all_items = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_items = self._extract_page_items(page, page_num)
            all_items.extend(page_items)

        doc.close()

        # 부모-자식 관계 설정
        self._assign_parents(all_items)

        # 견적 대상 표시 (WHITE만)
        for item in all_items:
            item["needs_quotation"] = item["level"] == "part"

        # 트리 구조 생성
        hierarchy = self._build_hierarchy(all_items)

        # 통계
        assembly_count = sum(1 for i in all_items if i["level"] == "assembly")
        subassembly_count = sum(1 for i in all_items if i["level"] == "subassembly")
        part_count = sum(1 for i in all_items if i["level"] == "part")

        result = {
            "source_file": pdf_path.name,
            "total_items": len(all_items),
            "assembly_count": assembly_count,
            "subassembly_count": subassembly_count,
            "part_count": part_count,
            "items": all_items,
            "hierarchy": hierarchy,
        }

        logger.info(
            f"BOM 파싱 완료: {pdf_path.name} → "
            f"{len(all_items)}개 항목 "
            f"(ASSY={assembly_count}, SUB={subassembly_count}, PART={part_count})"
        )

        return result

    def _extract_page_items(self, page, page_num: int) -> List[Dict]:
        """페이지에서 BOM 항목 추출

        테이블을 찾고, 각 행의 배경색을 감지하여 레벨을 분류합니다.
        """
        import fitz

        items = []

        # 테이블 추출 시도
        tables = page.find_tables()
        if not tables or len(tables.tables) == 0:
            logger.warning(f"페이지 {page_num + 1}: 테이블을 찾을 수 없습니다")
            return items

        for table in tables:
            rows = table.extract()
            if not rows or len(rows) < 2:
                continue

            # 헤더 행 분석 → 컬럼 매핑
            header_row = rows[0]
            col_map = self._detect_columns(header_row)
            if not col_map:
                logger.warning(f"페이지 {page_num + 1}: 컬럼 매핑 실패 (헤더: {header_row})")
                continue

            # 테이블의 행 bounding boxes
            row_bboxes = self._get_row_bboxes(table)

            # Level 컬럼 존재 여부 확인
            level_col_idx = col_map.get("level_depth")

            # 데이터 행 처리
            for row_idx in range(1, len(rows)):
                row = rows[row_idx]

                # 빈 행 건너뛰기
                if not any(cell and str(cell).strip() for cell in row):
                    continue

                # 행 배경색 감지
                row_bbox = row_bboxes[row_idx] if row_idx < len(row_bboxes) else None
                level = self._detect_row_color(page, row_bbox)

                # 색상이 part(기본값)이고 Level 컬럼이 있으면 컬럼 값으로 판단
                if level == "part" and level_col_idx is not None:
                    level = self._parse_level_column(row, level_col_idx)

                # 컬럼 값 추출
                item = self._extract_item_from_row(row, col_map, level, page_num)
                if item and item.get("drawing_number"):
                    items.append(item)

        return items

    def _detect_columns(self, header_row: list) -> Optional[Dict[str, int]]:
        """헤더 행에서 컬럼 인덱스 매핑

        BOM 테이블의 일반적인 컬럼:
        - No./번호/품번, 도면번호, 품명, 재질, 수량
        - Rev (BOM 항목 개정), Doc Rev (도면 개정), Part No, Size, 중량, 비고

        매칭 순서: 도면번호(구체적) → 품명 → 재질 → 수량 → 신규 컬럼 → 품번(범용적)
        """
        col_map = {}
        header_lower = [str(h).strip().lower() if h else "" for h in header_row]

        for idx, header in enumerate(header_lower):
            if not header:
                continue

            # 도면번호 (최우선 - "번호" 포함 컬럼보다 먼저 체크)
            if "drawing_number" not in col_map and any(
                k in header for k in ["도면", "drawing", "dwg"]
            ):
                col_map["drawing_number"] = idx
            # Doc Rev (도면 개정 — "doc rev" 형태, "rev" 단독보다 먼저)
            elif "doc_revision" not in col_map and (
                "doc" in header and "rev" in header
            ):
                col_map["doc_revision"] = idx
            # 품명
            elif "description" not in col_map and any(
                k in header for k in ["품명", "description", "명칭", "desc"]
            ):
                col_map["description"] = idx
            # Part No
            elif "part_no" not in col_map and (
                "part" in header and "no" in header
            ):
                col_map["part_no"] = idx
            # 재질
            elif "material" not in col_map and any(
                k in header for k in ["재질", "material", "mat"]
            ):
                col_map["material"] = idx
            # Size / 규격
            elif "size" not in col_map and any(
                k in header for k in ["size", "규격", "spec", "사양"]
            ):
                col_map["size"] = idx
            # 수량
            elif "quantity" not in col_map and any(
                k in header for k in ["수량", "qty", "quantity", "q'ty"]
            ):
                col_map["quantity"] = idx
            # 중량
            elif "weight" not in col_map and any(
                k in header for k in ["중량", "weight", "wt", "w.t"]
            ):
                col_map["weight"] = idx
            # BOM Rev (항목 개정 — "rev" 단독)
            elif "revision" not in col_map and (
                header in ("rev", "rev.", "rev.no", "개정", "revision")
                or re.match(r'^rev\b', header)
            ):
                col_map["revision"] = idx
            # 레벨/깊이 (계층 컬럼: "Level", "Lv" 등)
            elif "level_depth" not in col_map and any(
                k in header for k in ["level", "lv", "레벨", "계층"]
            ):
                col_map["level_depth"] = idx
            # 비고
            elif "remark" not in col_map and any(
                k in header for k in ["비고", "remark", "remarks", "note", "비 고"]
            ):
                col_map["remark"] = idx
            # 품번 (마지막 - "no", "번호" 등 범용 키워드)
            elif "item_no" not in col_map and any(
                k in header for k in ["품번", "품목", "item", "serial",
                                      "no", "번호", "#"]
            ):
                col_map["item_no"] = idx

        # 최소 drawing_number 또는 item_no가 있어야 유효
        if "drawing_number" not in col_map and "item_no" not in col_map:
            return None

        return col_map

    def _get_row_bboxes(self, table) -> List[Optional[Tuple[float, float, float, float]]]:
        """테이블의 각 행 bounding box 추출"""
        try:
            # PyMuPDF Table의 행 좌표 추출
            cells = table.cells
            if not cells:
                return []

            # 행별 y좌표 수집
            rows_y = {}
            for cell in cells:
                # cell: (x0, y0, x1, y1) 형태
                y0 = round(cell[1], 1)
                y1 = round(cell[3], 1)
                row_key = y0
                if row_key not in rows_y:
                    rows_y[row_key] = {
                        "x0": cell[0], "y0": y0,
                        "x1": cell[2], "y1": y1,
                    }
                else:
                    rows_y[row_key]["x0"] = min(rows_y[row_key]["x0"], cell[0])
                    rows_y[row_key]["x1"] = max(rows_y[row_key]["x1"], cell[2])
                    rows_y[row_key]["y1"] = max(rows_y[row_key]["y1"], y1)

            # y0 기준 정렬
            sorted_rows = sorted(rows_y.values(), key=lambda r: r["y0"])
            return [
                (r["x0"], r["y0"], r["x1"], r["y1"])
                for r in sorted_rows
            ]
        except Exception as e:
            logger.warning(f"행 bbox 추출 실패: {e}")
            return []

    def _detect_row_color(
        self, page, row_bbox: Optional[Tuple[float, float, float, float]]
    ) -> str:
        """행 배경색 → assembly/subassembly/part

        행 영역의 중앙 부근 픽셀 색상을 샘플링하여 판단합니다.
        """
        if not row_bbox:
            return "part"  # bbox 없으면 기본값 WHITE

        try:
            import fitz

            x0, y0, x1, y1 = row_bbox

            # 행 중앙의 작은 영역을 렌더링
            sample_x = x0 + (x1 - x0) * 0.1  # 왼쪽 10% 지점
            sample_y = (y0 + y1) / 2  # 수직 중앙

            # 작은 영역 클립 (5x5 픽셀)
            clip = fitz.Rect(sample_x - 2, sample_y - 2, sample_x + 3, sample_y + 3)
            mat = fitz.Matrix(2, 2)  # 2x scale
            pix = page.get_pixmap(matrix=mat, clip=clip)

            if pix.n < 3:
                return "part"

            # 중앙 픽셀 RGB
            w, h = pix.width, pix.height
            cx, cy = w // 2, h // 2
            pixel = pix.pixel(cx, cy)
            r, g, b = pixel[0], pixel[1], pixel[2]

            return self._classify_color(r, g, b)

        except Exception as e:
            logger.debug(f"색상 감지 실패: {e}")
            return "part"

    def _classify_color(self, r: int, g: int, b: int) -> str:
        """RGB → BOM 레벨 분류

        Args:
            r, g, b: 0-255 RGB 값

        Returns:
            "assembly" | "subassembly" | "part"
        """
        # PINK: 붉은 계열 (R이 높고, G/B가 상대적으로 낮음)
        if r > 200 and g < 170 and b < 200 and (r - g) > 50:
            return "assembly"

        # BLUE: 파란 계열 (B가 높고, R/G가 낮음)
        if b > 200 and r < 150 and g < 170:
            return "subassembly"

        # LIGHT BLUE: 연한 파란색 (B가 높지만 R/G도 어느 정도)
        if b > 180 and r < 180 and (b - r) > 40:
            return "subassembly"

        # WHITE 또는 기타 → part
        return "part"

    def _parse_level_column(self, row: list, level_col_idx: int) -> str:
        """Level 컬럼 값에서 계층 레벨 판단

        BOM Level 컬럼 형식: "..2", "...3", "....4", "…..5" 등
        숫자가 깊이를 나타냄 (1-2: assembly, 3: subassembly, 4+: part)
        """
        if level_col_idx >= len(row) or not row[level_col_idx]:
            return "part"

        val = str(row[level_col_idx]).strip()
        match = re.search(r'(\d+)', val)
        if not match:
            return "part"

        depth = int(match.group(1))
        if depth <= 2:
            return "assembly"
        elif depth == 3:
            return "subassembly"
        return "part"

    def _extract_item_from_row(
        self, row: list, col_map: Dict[str, int], level: str, page_num: int
    ) -> Optional[Dict[str, Any]]:
        """행 데이터 → BOM 항목 딕셔너리"""

        def get_cell(col_name: str) -> str:
            idx = col_map.get(col_name)
            if idx is None or idx >= len(row):
                return ""
            val = row[idx]
            return str(val).strip() if val else ""

        item_no = get_cell("item_no")
        drawing_number = get_cell("drawing_number")
        description = get_cell("description")
        material = get_cell("material")
        quantity_str = get_cell("quantity")

        # 신규 컬럼
        revision_str = get_cell("revision")
        doc_revision = get_cell("doc_revision")
        part_no = get_cell("part_no")
        size = get_cell("size")
        weight_str = get_cell("weight")
        remark = get_cell("remark")

        # 도면번호 정리 (공백, 특수문자 제거)
        drawing_number = re.sub(r'\s+', '', drawing_number)

        if not drawing_number and not item_no:
            return None

        # 수량 파싱
        quantity = 1
        if quantity_str:
            try:
                quantity = int(re.search(r'\d+', quantity_str).group())
            except (AttributeError, ValueError):
                quantity = 1

        # BOM Rev 파싱 (0 or 1)
        bom_revision = None
        if revision_str:
            try:
                bom_revision = int(re.search(r'\d+', revision_str).group())
            except (AttributeError, ValueError):
                pass

        # 중량 파싱
        weight_kg = None
        if weight_str:
            try:
                weight_kg = float(re.search(r'[\d.]+', weight_str).group())
            except (AttributeError, ValueError):
                pass

        return {
            "item_no": item_no or f"P{page_num + 1}-auto",
            "level": level,
            "drawing_number": drawing_number,
            "description": description,
            "material": material,
            "quantity": quantity,
            "parent_item_no": None,
            "needs_quotation": False,
            "matched_file": None,
            "session_id": None,
            # 신규 필드
            "assembly_drawing_number": None,
            "bom_revision": bom_revision,
            "doc_revision": doc_revision or None,
            "part_no": part_no or None,
            "size": size or None,
            "weight_kg": weight_kg,
            "remark": remark or None,
        }

    def _assign_parents(self, items: List[Dict]):
        """부모-자식 관계 + 어셈블리 귀속 설정

        순서대로 순회하면서:
        - ASSEMBLY가 나오면 현재 부모를 이 항목으로 설정
        - SUBASSEMBLY가 나오면 부모를 마지막 ASSEMBLY로, 현재 서브부모를 이것으로
        - PART가 나오면 부모를 마지막 SUBASSEMBLY (없으면 ASSEMBLY)로

        모든 항목에 assembly_drawing_number를 설정하여 소속 어셈블리를 추적.
        """
        current_assembly = None
        current_assembly_dwg = None
        current_subassembly = None

        for item in items:
            if item["level"] == "assembly":
                current_assembly = item["item_no"]
                current_assembly_dwg = item["drawing_number"]
                current_subassembly = None
                # assembly는 부모 없음 (최상위)
                item["parent_item_no"] = None
                item["assembly_drawing_number"] = current_assembly_dwg

            elif item["level"] == "subassembly":
                current_subassembly = item["item_no"]
                item["parent_item_no"] = current_assembly
                item["assembly_drawing_number"] = current_assembly_dwg

            elif item["level"] == "part":
                item["parent_item_no"] = current_subassembly or current_assembly
                item["assembly_drawing_number"] = current_assembly_dwg

    def _build_hierarchy(self, items: List[Dict]) -> List[Dict]:
        """flat 목록 → 트리 구조

        Returns:
            List of root nodes, each with optional 'children' key
        """
        # item_no → item 맵
        item_map = {item["item_no"]: {**item, "children": []} for item in items}

        roots = []
        for item in items:
            node = item_map[item["item_no"]]
            parent_no = item.get("parent_item_no")

            if parent_no and parent_no in item_map:
                item_map[parent_no]["children"].append(node)
            else:
                roots.append(node)

        # children이 비어있으면 키 제거 (클린)
        def clean_children(node):
            if not node.get("children"):
                node.pop("children", None)
            else:
                for child in node["children"]:
                    clean_children(child)

        for root in roots:
            clean_children(root)

        return roots

    def save_bom_items(self, project_dir: Path, bom_data: Dict[str, Any]):
        """파싱된 BOM 데이터를 프로젝트 디렉토리에 저장"""
        bom_file = project_dir / "bom_items.json"
        with open(bom_file, "w", encoding="utf-8") as f:
            json.dump(bom_data, f, ensure_ascii=False, indent=2)
        logger.info(f"BOM 데이터 저장: {bom_file}")

    def load_bom_items(self, project_dir: Path) -> Optional[Dict[str, Any]]:
        """프로젝트 디렉토리에서 BOM 데이터 로드"""
        bom_file = project_dir / "bom_items.json"
        if not bom_file.exists():
            return None
        with open(bom_file, "r", encoding="utf-8") as f:
            return json.load(f)
