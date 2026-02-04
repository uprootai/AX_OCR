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

            # 데이터 행 처리
            for row_idx in range(1, len(rows)):
                row = rows[row_idx]

                # 빈 행 건너뛰기
                if not any(cell and str(cell).strip() for cell in row):
                    continue

                # 행 배경색 감지
                row_bbox = row_bboxes[row_idx] if row_idx < len(row_bboxes) else None
                level = self._detect_row_color(page, row_bbox)

                # 컬럼 값 추출
                item = self._extract_item_from_row(row, col_map, level, page_num)
                if item and item.get("drawing_number"):
                    items.append(item)

        return items

    def _detect_columns(self, header_row: list) -> Optional[Dict[str, int]]:
        """헤더 행에서 컬럼 인덱스 매핑

        BOM 테이블의 일반적인 컬럼:
        - No./번호/품번
        - 도면번호/Drawing No.
        - 품명/Description
        - 재질/Material
        - 수량/Qty
        """
        col_map = {}
        header_lower = [str(h).strip().lower() if h else "" for h in header_row]

        for idx, header in enumerate(header_lower):
            if not header:
                continue

            # 품번
            if any(k in header for k in ["no", "번호", "품번", "item", "#"]):
                if "item_no" not in col_map:
                    col_map["item_no"] = idx
            # 도면번호
            elif any(k in header for k in ["도면", "drawing", "part no", "dwg"]):
                col_map["drawing_number"] = idx
            # 품명
            elif any(k in header for k in ["품명", "description", "name", "명칭", "desc"]):
                col_map["description"] = idx
            # 재질
            elif any(k in header for k in ["재질", "material", "mat", "spec"]):
                col_map["material"] = idx
            # 수량
            elif any(k in header for k in ["수량", "qty", "quantity", "q'ty", "ea"]):
                col_map["quantity"] = idx

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
        }

    def _assign_parents(self, items: List[Dict]):
        """부모-자식 관계 설정

        순서대로 순회하면서:
        - ASSEMBLY가 나오면 현재 부모를 이 항목으로 설정
        - SUBASSEMBLY가 나오면 부모를 마지막 ASSEMBLY로, 현재 서브부모를 이것으로
        - PART가 나오면 부모를 마지막 SUBASSEMBLY (없으면 ASSEMBLY)로
        """
        current_assembly = None
        current_subassembly = None

        for item in items:
            if item["level"] == "assembly":
                current_assembly = item["item_no"]
                current_subassembly = None
                # assembly는 부모 없음 (최상위)
                item["parent_item_no"] = None

            elif item["level"] == "subassembly":
                current_subassembly = item["item_no"]
                item["parent_item_no"] = current_assembly

            elif item["level"] == "part":
                item["parent_item_no"] = current_subassembly or current_assembly

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
