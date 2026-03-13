"""
Parts List 파싱 로직
테이블 데이터 → 구조화된 Parts List 변환
DSE Bearing 전용 파서 통합
"""
import re
import logging
from typing import Dict, Any, List

from .normalizers import normalize_header, normalize_material, parse_quantity

logger = logging.getLogger(__name__)


def parse_parts_list(
    table: Dict,
    normalize_headers: bool,
    do_normalize_material: bool,
) -> Dict[str, Any]:
    """테이블 데이터를 Parts List로 파싱"""
    raw_headers = table.get("headers", [])
    raw_data = table.get("data", [])

    # 헤더 정규화
    if normalize_headers:
        headers = [normalize_header(str(h)) for h in raw_headers]
    else:
        headers = [str(h).lower().replace(" ", "_") for h in raw_headers]

    # 데이터 파싱
    parts = []
    for row in raw_data:
        if isinstance(row, list):
            # 리스트 형태의 행
            part = {}
            for i, value in enumerate(row):
                if i < len(headers):
                    header = headers[i]
                    value_str = str(value).strip() if value else ""

                    # 재질 정규화
                    if header == "material" and do_normalize_material:
                        value_str = normalize_material(value_str)

                    # 수량 파싱
                    if header == "quantity":
                        part[header] = parse_quantity(value_str)
                    elif header == "no":
                        try:
                            part[header] = int(re.sub(r"[^\d]", "", value_str) or "0")
                        except ValueError:
                            part[header] = 0
                    else:
                        part[header] = value_str

            # 유효한 부품인지 확인 (part_name이 있어야 함)
            if part.get("part_name") or part.get("material"):
                parts.append(part)

        elif isinstance(row, dict):
            # 딕셔너리 형태의 행
            part = {}
            for key, value in row.items():
                header = normalize_header(str(key)) if normalize_headers else str(key).lower()
                value_str = str(value).strip() if value else ""

                if header == "material" and do_normalize_material:
                    value_str = normalize_material(value_str)

                if header == "quantity":
                    part[header] = parse_quantity(value_str)
                elif header == "no":
                    try:
                        part[header] = int(re.sub(r"[^\d]", "", value_str) or "0")
                    except ValueError:
                        part[header] = 0
                else:
                    part[header] = value_str

            if part.get("part_name") or part.get("material"):
                parts.append(part)

    return {
        "headers": headers,
        "parts": parts,
        "parts_count": len(parts),
    }


def calculate_confidence(parsed: Dict[str, Any], expected_headers: List[str]) -> float:
    """파싱 신뢰도 계산"""
    if not parsed.get("parts"):
        return 0.0

    headers = parsed.get("headers", [])
    parts = parsed.get("parts", [])

    # 헤더 매칭 점수
    header_score = sum(1 for h in expected_headers if h in headers) / len(expected_headers)

    # 데이터 완성도 점수
    data_scores = []
    for part in parts:
        filled = sum(1 for h in expected_headers if part.get(h))
        data_scores.append(filled / len(expected_headers))

    data_score = sum(data_scores) / len(data_scores) if data_scores else 0

    return header_score * 0.4 + data_score * 0.6


def parse_with_dse_bearing_service(tables: List[Dict]) -> Dict[str, Any]:
    """
    DSE Bearing 파서 서비스로 Parts List 파싱

    Args:
        tables: Table Detector 결과 테이블 목록

    Returns:
        파싱된 Parts List 데이터
    """
    try:
        from services.dsebearing_parser import get_parser

        parser = get_parser()

        # 테이블 데이터 준비
        table_data = []
        for table in tables:
            data = table.get("data", [])
            headers = table.get("headers", [])

            # 헤더가 있으면 첫 행으로 추가
            if headers:
                table_data.append(headers)

            # 데이터 행 추가
            for row in data:
                if isinstance(row, list):
                    table_data.append(row)
                elif isinstance(row, dict):
                    # cells 형식 처리
                    cells = row.get("cells", [])
                    if cells:
                        row_data = [""] * 10  # 최대 10개 컬럼
                        for cell in cells:
                            if isinstance(cell, dict):
                                col = cell.get("col", 0)
                                text = cell.get("text", "")
                                if col < 10:
                                    row_data[col] = text
                        table_data.append([c for c in row_data if c])

        # DSE Bearing 파서로 파싱 (table_data와 ocr_texts 모두 전달)
        items = parser.parse_parts_list(ocr_texts=[], table_data=table_data)

        # 결과 변환 (parse_parts_list는 List[PartsListItem] 반환)
        parts = []
        for item in items:
            part = {
                "no": item.no,
                "part_name": item.description,
                "material": item.material,
                "quantity": item.qty,
            }
            if item.weight:
                part["weight"] = item.weight
            if item.size_dwg_no:
                part["drawing_no"] = item.size_dwg_no
            if item.remark:
                part["remarks"] = item.remark
            parts.append(part)

        headers = ["no", "part_name", "material", "quantity"]
        if any(p.get("weight") for p in parts):
            headers.append("weight")
        if any(p.get("drawing_no") for p in parts):
            headers.append("drawing_no")
        if any(p.get("remarks") for p in parts):
            headers.append("remarks")

        # 신뢰도 계산 (파싱된 항목 수 기반)
        confidence = min(0.95, 0.7 + len(parts) * 0.05) if parts else 0.0

        return {
            "parts_list": {
                "headers": headers,
                "parts": parts,
            },
            "parts": parts,
            "parts_count": len(parts),
            "headers": headers,
            "confidence": confidence,
            "parser": "dse_bearing",
        }

    except Exception as e:
        logger.error(f"DSE Bearing 파서 오류: {e}")
        return {}
