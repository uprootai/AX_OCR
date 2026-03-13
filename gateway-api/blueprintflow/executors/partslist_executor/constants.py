"""
Parts List 상수 정의
헤더 별칭, 재질 정규화 매핑, 위치 프리셋
"""
from typing import Dict, List, Tuple

# 표준 헤더 매핑 (다양한 변형 → 표준 이름)
HEADER_ALIASES: Dict[str, List[str]] = {
    "no": ["NO", "NO.", "번호", "#", "SEQ", "ITEM", "ITEM NO", "ITEM NO."],
    "part_name": ["PART NAME", "NAME", "품명", "부품명", "DESCRIPTION", "DESC", "PART"],
    "material": ["MAT'L", "MATL", "MAT", "MATERIAL", "재질", "재료", "SPEC"],
    "quantity": ["Q'TY", "QTY", "QUANTITY", "수량", "EA", "PCS"],
    "remarks": ["REMARKS", "REMARK", "비고", "NOTE", "NOTES"],
    "drawing_no": ["DWG NO", "DWG NO.", "DRAWING NO", "도면번호", "DWG"],
    "weight": ["WEIGHT", "WT", "중량", "무게", "KG"],
    "specification": ["SPEC", "SPECIFICATION", "규격", "SIZE"],
}

# 재질 정규화 매핑
MATERIAL_NORMALIZATION: Dict[str, str] = {
    # SF 계열
    "SF440": "SF440A",
    "SF-440A": "SF440A",
    "SF 440A": "SF440A",
    "SF440-A": "SF440A",
    # SS 계열
    "SS-400": "SS400",
    "SS 400": "SS400",
    # SM 계열
    "SM-490A": "SM490A",
    "SM 490A": "SM490A",
    "SM490": "SM490A",
    # S45C 계열
    "S45C-N": "S45C-N",
    "S45CN": "S45C-N",
    "S-45C": "S45C",
    # ASTM 계열
    "B23": "ASTM B23 GR.2",
    "ASTM B23": "ASTM B23 GR.2",
    "ASTM B-23": "ASTM B23 GR.2",
    "BABBITT": "ASTM B23 GR.2",
    # SUS 계열
    "SUS-304": "SUS304",
    "SUS 304": "SUS304",
    # SCM 계열
    "SCM-440": "SCM440",
    "SCM 440": "SCM440",
}

# Parts List 위치 프리셋 (이미지 비율 기준)
POSITION_PRESETS: Dict[str, Tuple[float, float, float, float]] = {
    "top_left": (0.0, 0.0, 0.5, 0.4),
    "top_right": (0.5, 0.0, 1.0, 0.4),
    "bottom_left": (0.0, 0.6, 0.5, 1.0),
    "bottom_right": (0.5, 0.6, 1.0, 1.0),
    "full": (0.0, 0.0, 1.0, 1.0),
}

# Table Detector API URL
TABLE_DETECTOR_URL = "http://table-detector-api:5022"
