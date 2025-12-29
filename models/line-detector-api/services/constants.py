"""
Line Detector Constants
라인 검출/분류 관련 상수 정의
"""

# P&ID 라인 색상 분류 기준
LINE_COLOR_TYPES = {
    'black': {'name': 'process', 'korean': '공정 라인', 'description': '주요 공정 배관'},
    'blue': {'name': 'water', 'korean': '냉각수/급수', 'description': '냉각수 또는 급수 라인'},
    'red': {'name': 'steam', 'korean': '증기/가열', 'description': '증기 또는 가열 라인'},
    'green': {'name': 'signal', 'korean': '신호선', 'description': '계장 신호 라인'},
    'orange': {'name': 'electrical', 'korean': '전기', 'description': '전기 배선'},
    'purple': {'name': 'drain', 'korean': '배수', 'description': '배수 라인'},
    'cyan': {'name': 'air', 'korean': '공기/가스', 'description': '압축공기 또는 가스 라인'},
    'gray': {'name': 'unknown', 'korean': '미분류', 'description': '분류되지 않은 라인'},
}

# P&ID 라인 스타일 분류 기준 (확장)
LINE_STYLE_TYPES = {
    'solid': {'korean': '실선', 'description': '주요 공정 배관', 'signal_type': 'process', 'priority': 1},
    'dashed': {'korean': '점선', 'description': '계장 신호선', 'signal_type': 'instrument', 'priority': 2},
    'dotted': {'korean': '점점선', 'description': '보조/옵션 라인', 'signal_type': 'auxiliary', 'priority': 3},
    'dash_dot': {'korean': '일점쇄선', 'description': '경계선/중심선', 'signal_type': 'centerline', 'priority': 4},
    'double': {'korean': '이중선', 'description': '주요 배관/케이싱', 'signal_type': 'main_pipe', 'priority': 5},
    'wavy': {'korean': '물결선', 'description': '플렉시블 호스', 'signal_type': 'flexible', 'priority': 6},
    'unknown': {'korean': '미분류', 'description': '분류 불가', 'signal_type': 'unknown', 'priority': 99},
}

# P&ID 라인 용도별 분류 (ISO 10628 기반)
LINE_PURPOSE_TYPES = {
    'main_process': {'korean': '주공정 배관', 'style': 'solid', 'color': 'black', 'weight': 'thick'},
    'secondary_process': {'korean': '보조공정 배관', 'style': 'solid', 'color': 'black', 'weight': 'thin'},
    'instrument_signal': {'korean': '계장 신호선', 'style': 'dashed', 'color': 'black', 'weight': 'thin'},
    'electrical': {'korean': '전기 배선', 'style': 'dashed', 'color': 'red', 'weight': 'thin'},
    'pneumatic': {'korean': '공압 신호', 'style': 'dashed', 'color': 'blue', 'weight': 'thin'},
    'hydraulic': {'korean': '유압 라인', 'style': 'solid', 'color': 'green', 'weight': 'medium'},
    'software_link': {'korean': '소프트웨어 연결', 'style': 'dotted', 'color': 'black', 'weight': 'thin'},
    'future_equipment': {'korean': '미래 설비', 'style': 'dash_dot', 'color': 'gray', 'weight': 'thin'},
    'boundary': {'korean': '경계선', 'style': 'dash_dot', 'color': 'black', 'weight': 'medium'},
    'enclosure': {'korean': '영역 표시', 'style': 'dashed', 'color': 'black', 'weight': 'thin'},
}

# 점선 영역 타입 분류
REGION_TYPES = {
    'signal_group': {'korean': '신호 그룹', 'description': 'SIGNAL FOR BWMS 등 신호 관련 심볼 그룹', 'keywords': ['SIGNAL', 'BWMS', 'CONTROL']},
    'equipment_boundary': {'korean': '장비 경계', 'description': '패키지/스키드 경계', 'keywords': ['PACKAGE', 'SKID', 'UNIT']},
    'note_box': {'korean': '노트 박스', 'description': '주석/설명 영역', 'keywords': ['NOTE', 'REMARK', 'LEGEND']},
    'hazardous_area': {'korean': '위험 구역', 'description': '위험 구역 표시', 'keywords': ['HAZARD', 'DANGER', 'ZONE']},
    'scope_boundary': {'korean': '공급 범위', 'description': '공급자/구매자 범위 경계', 'keywords': ['SCOPE', 'SUPPLY', 'BY OWNER', 'BY VENDOR']},
    'detail_area': {'korean': '상세도 영역', 'description': '상세도 참조 영역', 'keywords': ['DETAIL', 'SEE', 'REFER']},
    'unknown': {'korean': '미분류 영역', 'description': '분류되지 않은 영역', 'keywords': []},
}
