"""
DSE Bearing Drawing Parser Service

실제 OCR 결과에서 Title Block과 Parts List를 파싱하는 서비스
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TitleBlockData:
    """Title Block 데이터"""
    drawing_number: str = ""
    revision: str = ""
    part_name: str = ""
    material: str = ""
    date: str = ""
    size: str = ""
    scale: str = ""
    sheet: str = ""
    unit: str = "mm"
    company: str = ""
    raw_texts: List[str] = None

    def __post_init__(self):
        if self.raw_texts is None:
            self.raw_texts = []

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items()}


@dataclass
class PartsListItem:
    """Parts List 항목"""
    no: str = ""
    description: str = ""
    material: str = ""
    size_dwg_no: str = ""
    qty: int = 1
    remark: str = ""
    weight: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v}


class DSEBearingParser:
    """DSE Bearing 도면 파서"""

    # 도면번호 패턴 (TD로 시작하는 7-8자리)
    DRAWING_NUMBER_PATTERNS = [
        r"TD\d{7}",          # TD0062016
        r"TD\d{6}",          # TD006201
        r"[A-Z]{2}\d{5,8}",  # 기타 패턴
    ]

    # Rev 패턴
    REVISION_PATTERNS = [
        r"REV[.\s]*([A-Z])",
        r"Rev[.\s]*([A-Z])",
        r"\bR([A-Z])\b",
        r"[Rr]evision[:\s]*([A-Z])",
    ]

    # 재질 패턴 (DSE Bearing 주요 재질)
    MATERIAL_PATTERNS = [
        r"SF\d{2,3}[A-Z]?",      # SF440A, SF45A
        r"SM\d{3}[A-Z]?",        # SM490A
        r"S45C[-N]?",            # S45C-N
        r"SS\d{3}",              # SS400
        r"STS\d{3}",             # STS304
        r"SCM\d{3}",             # SCM435
        r"ASTM\s*[AB]\d+",       # ASTM A193, ASTM B23
        r"ASTM\s*B23\s*GR[.\s]*\d", # ASTM B23 GR.2 (Babbitt)
    ]

    # 품명 키워드 (대문자)
    PART_NAME_KEYWORDS = [
        "BEARING", "RING", "CASING", "PAD", "ASSY", "ASSEMBLY",
        "UPPER", "LOWER", "THRUST", "SHIM", "PLATE", "BOLT",
        "PIN", "NUT", "WASHER", "WEDGE", "BUSHING", "LINER",
    ]

    # 날짜 패턴
    DATE_PATTERNS = [
        r"\d{4}[./]\d{2}[./]\d{2}",  # 2025.01.09, 2025/01/09
        r"\d{2}[./]\d{2}[./]\d{4}",  # 09.01.2025
        r"\d{4}-\d{2}-\d{2}",        # 2025-01-09
    ]

    def parse_title_block(self, ocr_texts: List[Dict[str, Any]]) -> TitleBlockData:
        """
        OCR 결과에서 Title Block 정보 추출

        Args:
            ocr_texts: eDOCr2 OCR 결과 리스트 [{"text": "...", "bbox": [...], ...}, ...]

        Returns:
            TitleBlockData: 파싱된 Title Block 정보
        """
        result = TitleBlockData()
        all_texts = []

        # 텍스트 추출
        for item in ocr_texts:
            if isinstance(item, dict):
                text = item.get("text", "")
            elif isinstance(item, str):
                text = item
            else:
                continue

            if text:
                all_texts.append(text.strip())

        result.raw_texts = all_texts
        combined_text = " ".join(all_texts)

        # 1. 도면번호 추출
        result.drawing_number = self._extract_drawing_number(all_texts, combined_text)

        # 2. Rev 추출
        result.revision = self._extract_revision(all_texts, combined_text)

        # 3. 품명 추출
        result.part_name = self._extract_part_name(all_texts, combined_text)

        # 4. 재질 추출
        result.material = self._extract_material(all_texts, combined_text)

        # 5. 날짜 추출
        result.date = self._extract_date(all_texts, combined_text)

        # 6. 기타 정보 추출
        self._extract_misc_info(result, all_texts, combined_text)

        logger.info(f"Title Block 파싱 완료: {result.drawing_number}, Rev.{result.revision}")
        return result

    def _extract_drawing_number(self, texts: List[str], combined: str) -> str:
        """도면번호 추출"""
        for pattern in self.DRAWING_NUMBER_PATTERNS:
            # 개별 텍스트에서 검색
            for text in texts:
                match = re.search(pattern, text.upper())
                if match:
                    return match.group(0)

            # 전체 텍스트에서 검색
            match = re.search(pattern, combined.upper())
            if match:
                return match.group(0)

        return ""

    def _extract_revision(self, texts: List[str], combined: str) -> str:
        """Rev 추출"""
        for pattern in self.REVISION_PATTERNS:
            for text in texts:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)

            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                return match.group(1)

        # 단독 A, B, C, D 등 (Rev 옆에 있는 경우)
        for i, text in enumerate(texts):
            if "REV" in text.upper() and i + 1 < len(texts):
                next_text = texts[i + 1].strip()
                if len(next_text) == 1 and next_text.isalpha():
                    return next_text.upper()

        return ""

    def _extract_part_name(self, texts: List[str], combined: str) -> str:
        """품명 추출"""
        # 키워드 조합으로 품명 찾기
        best_match = ""
        best_score = 0

        for text in texts:
            upper_text = text.upper()
            score = sum(1 for kw in self.PART_NAME_KEYWORDS if kw in upper_text)
            if score > best_score and len(text) > 5:
                best_score = score
                best_match = text

        # TD 도면번호와 같은 줄에 있는 텍스트 찾기
        if not best_match:
            for text in texts:
                if any(kw in text.upper() for kw in ["BEARING", "RING", "CASING", "ASSY"]):
                    best_match = text
                    break

        return best_match.strip()

    def _normalize_ocr_text(self, text: str) -> str:
        """OCR 오류 보정 (일반적인 문자 혼동 수정)"""
        # 재질 코드 컨텍스트에서 O→0 변환
        # SF4O0A → SF400A, SFA4OA → SF440A 등
        normalized = text
        # SF 다음에 오는 O를 0으로
        normalized = re.sub(r"(SF[A-Z]?)([O0]+)([O0A-Z]*)",
                          lambda m: m.group(1).replace('A', '') +
                                   m.group(2).replace('O', '0') +
                                   m.group(3).replace('O', '0'),
                          normalized)
        # SFA로 시작하면 SF로 보정 (SFA4OA → SF40A는 아님, SFA40A → SF440A)
        normalized = re.sub(r"SFA(\d)", r"SF4\1", normalized)
        return normalized

    def _extract_material(self, texts: List[str], combined: str) -> str:
        """재질 추출 (OCR 오류 보정 포함)"""
        materials = []

        # OCR 오류 보정된 텍스트도 검색
        normalized_texts = [self._normalize_ocr_text(t.upper()) for t in texts]
        normalized_combined = self._normalize_ocr_text(combined.upper())

        for pattern in self.MATERIAL_PATTERNS:
            # 원본 텍스트 검색
            for text in texts:
                matches = re.findall(pattern, text.upper())
                materials.extend(matches)

            matches = re.findall(pattern, combined.upper())
            materials.extend(matches)

            # 보정된 텍스트 검색
            for text in normalized_texts:
                matches = re.findall(pattern, text)
                materials.extend(matches)

            matches = re.findall(pattern, normalized_combined)
            materials.extend(matches)

        # 추가 패턴: OCR 오류 변형 (SFA40A, SFA4OA 등)
        ocr_error_patterns = [
            r"SFA\d{1,2}[O0]?[A-Z]?",  # SFA40A, SFA4OA
            r"SF[O0]\d{1,2}[A-Z]?",    # SF04A (잘못된 순서)
        ]
        for pattern in ocr_error_patterns:
            matches = re.findall(pattern, combined.upper())
            for match in matches:
                # 보정: SFA40A → SF440A, SFA4OA → SF440A
                corrected = match.replace('O', '0')
                if corrected.startswith('SFA'):
                    corrected = 'SF4' + corrected[3:]
                materials.append(corrected)

        # 중복 제거
        materials = list(set(materials))

        # 가장 관련성 높은 재질 반환
        if materials:
            # SF440A, SF45A 등 주요 베어링 재질 우선
            for mat in materials:
                if mat.startswith("SF") and any(c.isdigit() for c in mat):
                    return mat
            return materials[0]

        return ""

    def _extract_date(self, texts: List[str], combined: str) -> str:
        """날짜 추출"""
        for pattern in self.DATE_PATTERNS:
            for text in texts:
                match = re.search(pattern, text)
                if match:
                    return match.group(0)

            match = re.search(pattern, combined)
            if match:
                return match.group(0)

        return ""

    def _extract_misc_info(self, result: TitleBlockData, texts: List[str], combined: str):
        """기타 정보 추출 (크기, Scale, Sheet 등)"""
        # Size (A1, A2, A3, A4 등)
        size_match = re.search(r"\b(A[0-4])\b", combined)
        if size_match:
            result.size = size_match.group(1)

        # Scale
        scale_patterns = [
            r"SCALE[:\s]*([\d:]+|N/?S)",
            r"Scale[:\s]*([\d:]+|N/?S)",
            r"(\d+:\d+)",
        ]
        for pattern in scale_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                result.scale = match.group(1)
                break

        # Sheet
        sheet_match = re.search(r"(\d+)/(\d+)\s*(?:SHEET|sheet)?", combined)
        if sheet_match:
            result.sheet = f"{sheet_match.group(1)}/{sheet_match.group(2)}"

        # Company
        company_keywords = ["DOOSAN", "DSE", "ENERBILITY"]
        for kw in company_keywords:
            if kw in combined.upper():
                result.company = "DOOSAN Enerbility"
                break

    def parse_parts_list(self, ocr_texts: List[Dict[str, Any]],
                         table_data: Optional[List[List[str]]] = None) -> List[PartsListItem]:
        """
        OCR 결과에서 Parts List 파싱

        Args:
            ocr_texts: eDOCr2 OCR 결과
            table_data: Table Detector 결과 (있는 경우)

        Returns:
            List[PartsListItem]: 파싱된 부품 리스트
        """
        items = []

        # Table Detector 결과가 있으면 우선 사용
        if table_data:
            items = self._parse_from_table(table_data)

        # 테이블 결과가 없거나 부족하면 OCR 텍스트에서 파싱
        if not items:
            items = self._parse_from_ocr(ocr_texts)

        logger.info(f"Parts List 파싱 완료: {len(items)}개 항목")
        return items

    def _normalize_table_data(self, table_data: List) -> List[List[str]]:
        """다양한 테이블 포맷을 2D 배열로 정규화"""
        if not table_data:
            return []

        # 이미 2D 배열 형식인 경우
        if isinstance(table_data[0], list):
            return table_data

        # cells 키를 가진 딕셔너리 리스트인 경우
        if isinstance(table_data[0], dict):
            cells_data = []
            for table in table_data:
                if "cells" in table:
                    cells_data.extend(table["cells"])
                elif "data" in table:
                    # data가 2D 배열인 경우
                    if isinstance(table["data"], list) and table["data"] and isinstance(table["data"][0], list):
                        return table["data"]
                    cells_data.extend(table.get("data", []))

            if not cells_data:
                return []

            # cells를 2D 배열로 변환
            max_row = max(c.get("row", 0) for c in cells_data if isinstance(c, dict)) + 1
            max_col = max(c.get("col", 0) for c in cells_data if isinstance(c, dict)) + 1
            rows = [["" for _ in range(max_col)] for _ in range(max_row)]

            for cell in cells_data:
                if isinstance(cell, dict):
                    r = cell.get("row", 0)
                    c = cell.get("col", 0)
                    text = cell.get("text", "")
                    if r < max_row and c < max_col:
                        rows[r][c] = text

            return rows

        return []

    def _parse_from_table(self, table_data: List) -> List[PartsListItem]:
        """테이블 데이터에서 Parts List 파싱

        다양한 테이블 포맷 지원:
        - List[List[str]]: 2D 배열 (행 × 열)
        - List[Dict]: cells 키를 가진 딕셔너리 리스트
        """
        items = []
        header_found = False
        header_mapping = {}

        # 테이블 데이터 정규화
        normalized_rows = self._normalize_table_data(table_data)

        for row in normalized_rows:
            if not row:
                continue

            row_text = " ".join(str(cell) for cell in row).upper()

            # 헤더 행 감지
            if not header_found and any(h in row_text for h in ["NO", "DESCRIPTION", "MATERIAL", "QTY"]):
                header_found = True
                for i, cell in enumerate(row):
                    cell_upper = str(cell).upper().strip()
                    if "NO" in cell_upper and len(cell_upper) <= 4:
                        header_mapping["no"] = i
                    elif "DESC" in cell_upper:
                        header_mapping["description"] = i
                    elif "MATERIAL" in cell_upper or "MAT" in cell_upper:
                        header_mapping["material"] = i
                    elif "SIZE" in cell_upper or "DWG" in cell_upper:
                        header_mapping["size_dwg_no"] = i
                    elif "QTY" in cell_upper or "Q'TY" in cell_upper:
                        header_mapping["qty"] = i
                    elif "REMARK" in cell_upper:
                        header_mapping["remark"] = i
                continue

            # 데이터 행 파싱
            if header_found and row:
                item = PartsListItem()

                # NO 확인 (숫자로 시작해야 함)
                no_idx = header_mapping.get("no", 0)
                if no_idx < len(row):
                    no_val = str(row[no_idx]).strip()
                    if no_val.isdigit():
                        item.no = no_val
                    else:
                        continue  # NO가 없으면 건너뜀

                # 나머지 필드
                if "description" in header_mapping and header_mapping["description"] < len(row):
                    item.description = str(row[header_mapping["description"]]).strip()

                if "material" in header_mapping and header_mapping["material"] < len(row):
                    item.material = str(row[header_mapping["material"]]).strip()

                if "size_dwg_no" in header_mapping and header_mapping["size_dwg_no"] < len(row):
                    item.size_dwg_no = str(row[header_mapping["size_dwg_no"]]).strip()

                if "qty" in header_mapping and header_mapping["qty"] < len(row):
                    qty_str = str(row[header_mapping["qty"]]).strip()
                    try:
                        item.qty = int(re.search(r"\d+", qty_str).group(0))
                    except:
                        item.qty = 1

                if "remark" in header_mapping and header_mapping["remark"] < len(row):
                    item.remark = str(row[header_mapping["remark"]]).strip()

                if item.no and item.description:
                    items.append(item)

        return items

    def _parse_from_ocr(self, ocr_texts: List[Dict[str, Any]]) -> List[PartsListItem]:
        """OCR 텍스트에서 Parts List 패턴 파싱 (노이즈 대응 강화)"""
        items = []
        all_texts = []

        for item in ocr_texts:
            if isinstance(item, dict):
                text = item.get("text", "")
            elif isinstance(item, str):
                text = item
            else:
                continue
            if text:
                all_texts.append(text.strip())

        combined = " ".join(all_texts)

        # 부품 키워드 리스트
        part_keywords = [
            "RING UPPER", "RING LOWER", "CASING", "LINER", "PAD",
            "HEX SOCKET", "DOWEL PIN", "SHIM PLATE", "BOLT", "NUT",
            "WASHER", "SCREW", "PLATE", "BUSHING", "WEDGE", "PIN",
            "BEARING", "ASSY", "ASSEMBLY", "LOCKING", "BUTTON", "SET PIN"
        ]

        # 1단계: 키워드 기반 파싱 (OCR 노이즈 대응)
        found_parts = set()
        for idx, keyword in enumerate(part_keywords):
            # 키워드 주변에서 번호와 재질/도면번호 찾기
            keyword_pattern = re.compile(
                rf"(\d{{1,2}})\s*[^\w]*{re.escape(keyword)}[^\w]*"
                rf"([A-Z]{{2,}}[A-Z0-9]*|SEE\s*EXCEL[^\|]*)?[^\|]*"
                rf"(T[D0O]\d{{7}}[A-Z\d]*)?",
                re.IGNORECASE
            )
            for match in keyword_pattern.finditer(combined):
                no = match.group(1)
                if no not in found_parts:
                    found_parts.add(no)
                    material = match.group(2) or "SEE EXCEL BOM"
                    material = material.strip()
                    if "SEE" in material.upper() or "EXCEL" in material.upper():
                        material = "SEE EXCEL BOM"

                    dwg_no = match.group(3) or ""
                    # TD → TD로 정규화 (O→0)
                    dwg_no = dwg_no.replace("O", "0").replace("o", "0")

                    items.append(PartsListItem(
                        no=no,
                        description=keyword,
                        material=material,
                        size_dwg_no=dwg_no,
                        qty=1
                    ))

        # 2단계: 표준 패턴 매칭 (정확한 테이블 형식)
        if not items:
            part_pattern = re.compile(
                r"(\d+)\s+"  # NO
                r"([A-Z][A-Z\s]+(?:RING|BOLT|PIN|NUT|PLATE|ASSY|PAD|WASHER|SCREW))\s+"  # DESCRIPTION
                r"(SF\d+[A-Z]?|SM\d+[A-Z]?|S[A-Z0-9]+|SEE\s*EXCEL|ASTM[^\s]+)?\s*"  # MATERIAL
                r"(TD\d+[A-Z\d]*)\s+"  # DWG.NO
                r"(\d+)",  # QTY
                re.IGNORECASE
            )

            matches = part_pattern.findall(combined)
            for match in matches:
                items.append(PartsListItem(
                    no=match[0],
                    description=match[1].strip(),
                    material=match[2].strip() if match[2] else "SEE EXCEL BOM",
                    size_dwg_no=match[3].strip(),
                    qty=int(match[4]) if match[4] else 1
                ))

        # 3단계: 도면번호 패턴으로 역추적
        if not items:
            # TD도면번호 주변에서 부품 정보 찾기
            td_pattern = re.compile(r"(\d{1,2})[^\d]*([A-Z][A-Z\s]+)[^\d]*(T[D0O]\d{7}[A-Z\d]*)", re.IGNORECASE)
            for match in td_pattern.finditer(combined):
                no = match.group(1)
                desc = match.group(2).strip()
                dwg = match.group(3).replace("O", "0").replace("o", "0")
                if len(desc) > 3:
                    items.append(PartsListItem(
                        no=no,
                        description=desc,
                        size_dwg_no=dwg,
                    ))

        # 4단계: 단순 번호+설명 패턴
        if not items:
            simple_pattern = re.compile(r"(?:^|\s)(\d{1,2})\s+([A-Z][A-Z\s]{3,20})", re.MULTILINE)
            for text in all_texts:
                for match in simple_pattern.finditer(text):
                    items.append(PartsListItem(
                        no=match.group(1),
                        description=match.group(2).strip()
                    ))

        # 중복 제거 (NO 기준)
        seen = set()
        unique_items = []
        for item in items:
            if item.no not in seen:
                seen.add(item.no)
                unique_items.append(item)

        # NO 기준 정렬
        unique_items.sort(key=lambda x: int(x.no) if x.no.isdigit() else 99)

        return unique_items

    # ISO 공차 등급 테이블 (주요 등급만)
    ISO_TOLERANCE_GRADES = {
        # Hole basis (대문자) - 주요 등급
        "H6": {"upper": 0.016, "lower": 0},  # 정밀 끼워맞춤
        "H7": {"upper": 0.025, "lower": 0},  # 표준 끼워맞춤
        "H8": {"upper": 0.039, "lower": 0},  # 중급 끼워맞춤
        "H9": {"upper": 0.062, "lower": 0},  # 러프 끼워맞춤
        "H11": {"upper": 0.160, "lower": 0},
        "G7": {"upper": 0.020, "lower": 0.005},  # 슬라이딩 fit
        "F7": {"upper": 0.030, "lower": 0.010},  # 러닝 fit
        "E8": {"upper": 0.072, "lower": 0.040},
        "D9": {"upper": 0.117, "lower": 0.065},
        # Shaft basis (소문자) - 주요 등급
        "h6": {"upper": 0, "lower": -0.016},
        "h7": {"upper": 0, "lower": -0.025},
        "h9": {"upper": 0, "lower": -0.062},
        "g6": {"upper": -0.006, "lower": -0.022},  # 슬라이딩 fit
        "f7": {"upper": -0.010, "lower": -0.035},  # 러닝 fit
        "e8": {"upper": -0.040, "lower": -0.079},
        "d9": {"upper": -0.065, "lower": -0.127},
        "k6": {"upper": 0.015, "lower": -0.001},  # 트랜지션 fit
        "m6": {"upper": 0.019, "lower": 0.004},  # 인터페이스 fit
        "n6": {"upper": 0.024, "lower": 0.008},  # 인터페이스 fit
        "p6": {"upper": 0.030, "lower": 0.014},  # 압입 fit
        "r6": {"upper": 0.036, "lower": 0.020},  # 강압입 fit
        "s6": {"upper": 0.043, "lower": 0.027},  # 강압입 fit
    }

    # 표면 거칠기 값 (Ra 기준)
    SURFACE_ROUGHNESS = {
        "N1": 0.025,
        "N2": 0.05,
        "N3": 0.1,
        "N4": 0.2,
        "N5": 0.4,
        "N6": 0.8,
        "N7": 1.6,
        "N8": 3.2,
        "N9": 6.3,
        "N10": 12.5,
        "N11": 25.0,
    }

    def extract_dimensions(self, ocr_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        OCR 결과에서 주요 치수 추출 (복합 치수 지원)

        지원 패턴:
        - ISO 공차 (Ø450H7, 120h6, 50g6)
        - 대칭 공차 (120±0.05)
        - 비대칭 공차 (120+0.025/-0.000, 50 +0.1 -0.05)
        - 직경 (Ø450, φ120)
        - 나사 (M12x1.5, M16-2)
        - 각도 (45°, 30°15')
        - 표면 거칠기 (Ra 0.8, Rz 3.2, N6)
        - 베어링 OD×ID

        Args:
            ocr_texts: eDOCr2 OCR 결과

        Returns:
            치수 정보 리스트
        """
        dimensions = []
        all_texts = []

        for item in ocr_texts:
            if isinstance(item, dict):
                text = item.get("text", "")
                bbox = item.get("bbox", [])
                confidence = item.get("confidence", 1.0)
            elif isinstance(item, str):
                text = item
                bbox = []
                confidence = 1.0
            else:
                continue
            if text:
                all_texts.append({"text": text.strip(), "bbox": bbox, "confidence": confidence})

        # 확장된 치수 패턴 (우선순위 순)
        dimension_patterns = [
            # 1. 나사 (M12x1.5, M16-2, M20×2.5) - ISO 패턴보다 먼저 매칭
            (r"M(\d+\.?\d*)\s*[xX×-]\s*(\d+\.?\d*)", "thread"),

            # 2. 나사 단독 (M12, M16)
            (r"M(\d+)(?![xX×\d])", "thread_single"),

            # 3. ISO 공차 직경 (Ø450H7, φ120h6)
            (r"[ØφΦ⌀]\s*(\d+\.?\d*)\s*([A-Za-z])(\d{1,2})", "iso_diameter"),

            # 4. ISO 공차 선형 (120H7, 50g6) - x, X 제외 (나사와 구분)
            (r"(\d+\.?\d*)\s*([A-WYZa-wyz])(\d{1,2})(?![A-Za-z])", "iso_linear"),

            # 5. 베어링 OD×ID (OD 450 × ID 300)
            (r"OD\s*(\d+\.?\d*)\s*[×xX]\s*ID\s*(\d+\.?\d*)", "bearing_od_id"),

            # 6. 비대칭 공차 - 상하 분리 (120+0.025/-0.000, 50 +0.1 -0.05)
            (r"(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/?\s*-\s*(\d+\.?\d*)", "asymmetric_tolerance"),

            # 7. 비대칭 공차 - 분수 형태 (120 +0.025)
            #                              ( -0.000)
            (r"(\d+\.?\d*)\s*\(\s*\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)\s*\)", "asymmetric_bracket"),

            # 8. 대칭 공차 (120±0.05, 450 ± 0.1)
            (r"(\d+\.?\d*)\s*[±]\s*(\d+\.?\d*)", "symmetric_tolerance"),

            # 9. 직경 단독 (Ø450, φ120)
            (r"[ØφΦ⌀]\s*(\d+\.?\d*)", "diameter"),

            # 10. 각도 분초 (30°15'30")
            (r"(\d+)[°]\s*(\d+)[′']\s*(\d+)?[″\"]?", "angle_dms"),

            # 11. 각도 단순 (45°, 90°)
            (r"(\d+\.?\d*)[°]", "angle"),

            # 12. 표면 거칠기 Ra (Ra 0.8, Ra0.4)
            (r"Ra\s*(\d+\.?\d*)", "roughness_ra"),

            # 13. 표면 거칠기 Rz (Rz 3.2)
            (r"Rz\s*(\d+\.?\d*)", "roughness_rz"),

            # 14. 표면 거칠기 N등급 (N6, N7)
            (r"\b(N\d{1,2})\b", "roughness_n"),

            # 15. 반경 (R10, R5.5)
            (r"R(\d+\.?\d*)(?![aAzZ])", "radius"),

            # 16. 챔퍼 (C2, C1.5, 2×45°)
            (r"C(\d+\.?\d*)", "chamfer"),
            (r"(\d+\.?\d*)\s*[×xX]\s*45[°]", "chamfer_angle"),

            # 17. 일반 선형 치수 (120, 450.5) - 마지막에 배치
            (r"(\d{2,4}\.?\d*)\b", "linear"),
        ]

        seen_texts = set()  # 중복 방지

        for item in all_texts:
            text = item["text"]
            bbox = item.get("bbox", [])
            confidence = item.get("confidence", 1.0)

            if text in seen_texts:
                continue

            for pattern, dim_type in dimension_patterns:
                match = re.search(pattern, text)
                if match:
                    dim_data = self._parse_dimension_match(match, dim_type, text, bbox, confidence)
                    if dim_data:
                        dimensions.append(dim_data)
                        seen_texts.add(text)
                        break

        # 치수 중요도 정렬 (ISO 공차 > 베어링 > 기타)
        priority_order = {
            "iso_diameter": 1, "iso_linear": 2, "bearing_od_id": 3,
            "asymmetric_tolerance": 4, "asymmetric_bracket": 4,
            "symmetric_tolerance": 5, "diameter": 6, "thread": 7,
            "angle": 8, "roughness_ra": 9, "linear": 10
        }
        dimensions.sort(key=lambda x: priority_order.get(x.get("type", ""), 99))

        logger.info(f"Dimension 파싱 완료: {len(dimensions)}개 치수")
        return dimensions

    def _parse_dimension_match(self, match, dim_type: str, raw_text: str,
                                bbox: List, confidence: float) -> Optional[Dict[str, Any]]:
        """치수 매칭 결과를 구조화된 데이터로 변환"""
        dim_data = {
            "raw_text": raw_text,
            "type": dim_type,
            "bbox": bbox,
            "confidence": confidence,
            "unit": "mm",  # 기본 단위
        }

        try:
            if dim_type == "iso_diameter":
                value = float(match.group(1))
                grade_letter = match.group(2)
                grade_number = match.group(3)
                grade_key = f"{grade_letter}{grade_number}"

                dim_data["value"] = value
                dim_data["iso_grade"] = grade_key

                # ISO 공차 테이블에서 공차값 조회
                if grade_key in self.ISO_TOLERANCE_GRADES:
                    tol = self.ISO_TOLERANCE_GRADES[grade_key]
                    dim_data["upper_tolerance"] = tol["upper"]
                    dim_data["lower_tolerance"] = tol["lower"]
                    dim_data["fit_type"] = self._get_fit_type(grade_letter)

            elif dim_type == "iso_linear":
                value = float(match.group(1))
                grade_letter = match.group(2)
                grade_number = match.group(3)
                grade_key = f"{grade_letter}{grade_number}"

                dim_data["value"] = value
                dim_data["iso_grade"] = grade_key

                if grade_key in self.ISO_TOLERANCE_GRADES:
                    tol = self.ISO_TOLERANCE_GRADES[grade_key]
                    dim_data["upper_tolerance"] = tol["upper"]
                    dim_data["lower_tolerance"] = tol["lower"]

            elif dim_type == "bearing_od_id":
                dim_data["outer_diameter"] = float(match.group(1))
                dim_data["inner_diameter"] = float(match.group(2))
                dim_data["value"] = dim_data["outer_diameter"]

            elif dim_type in ["asymmetric_tolerance", "asymmetric_bracket"]:
                dim_data["value"] = float(match.group(1))
                dim_data["upper_tolerance"] = float(match.group(2))
                dim_data["lower_tolerance"] = -float(match.group(3))

            elif dim_type == "symmetric_tolerance":
                dim_data["value"] = float(match.group(1))
                tol_value = float(match.group(2))
                dim_data["upper_tolerance"] = tol_value
                dim_data["lower_tolerance"] = -tol_value
                dim_data["tolerance_value"] = tol_value

            elif dim_type == "diameter":
                dim_data["value"] = float(match.group(1))

            elif dim_type == "thread":
                dim_data["nominal_diameter"] = float(match.group(1))
                dim_data["pitch"] = float(match.group(2))
                dim_data["value"] = dim_data["nominal_diameter"]

            elif dim_type == "thread_single":
                dim_data["nominal_diameter"] = float(match.group(1))
                dim_data["value"] = dim_data["nominal_diameter"]

            elif dim_type == "angle_dms":
                degrees = float(match.group(1))
                minutes = float(match.group(2))
                seconds = float(match.group(3)) if match.group(3) else 0
                dim_data["value"] = degrees + minutes/60 + seconds/3600
                dim_data["degrees"] = degrees
                dim_data["minutes"] = minutes
                dim_data["seconds"] = seconds
                dim_data["unit"] = "deg"

            elif dim_type == "angle":
                dim_data["value"] = float(match.group(1))
                dim_data["unit"] = "deg"

            elif dim_type == "roughness_ra":
                dim_data["value"] = float(match.group(1))
                dim_data["roughness_type"] = "Ra"
                dim_data["unit"] = "um"

            elif dim_type == "roughness_rz":
                dim_data["value"] = float(match.group(1))
                dim_data["roughness_type"] = "Rz"
                dim_data["unit"] = "um"

            elif dim_type == "roughness_n":
                n_grade = match.group(1)
                dim_data["n_grade"] = n_grade
                if n_grade in self.SURFACE_ROUGHNESS:
                    dim_data["value"] = self.SURFACE_ROUGHNESS[n_grade]
                    dim_data["roughness_type"] = "Ra"
                    dim_data["unit"] = "um"

            elif dim_type == "radius":
                dim_data["value"] = float(match.group(1))

            elif dim_type == "chamfer":
                dim_data["value"] = float(match.group(1))

            elif dim_type == "chamfer_angle":
                dim_data["value"] = float(match.group(1))
                dim_data["angle"] = 45

            elif dim_type == "linear":
                value = float(match.group(1))
                # 너무 작거나 큰 값은 제외 (노이즈 필터링)
                if value < 1 or value > 10000:
                    return None
                dim_data["value"] = value

            return dim_data

        except (ValueError, AttributeError) as e:
            logger.warning(f"치수 파싱 오류: {raw_text} - {e}")
            return None

    def _get_fit_type(self, grade_letter: str) -> str:
        """ISO 공차 등급 문자로 끼워맞춤 유형 반환"""
        letter = grade_letter.upper()
        if letter in ["H", "G", "F"]:
            return "clearance"  # 헐거운 끼워맞춤
        elif letter in ["K", "M", "N"]:
            return "transition"  # 중간 끼워맞춤
        elif letter in ["P", "R", "S"]:
            return "interference"  # 억지 끼워맞춤
        else:
            return "unknown"


# 싱글톤 인스턴스
_parser_instance = None

def get_parser() -> DSEBearingParser:
    """파서 인스턴스 반환"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = DSEBearingParser()
    return _parser_instance
