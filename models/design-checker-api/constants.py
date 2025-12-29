"""
Design Checker API - Constants
설계 검증 규칙 상수 및 Enum 정의
"""
from enum import Enum


class Severity(str, Enum):
    """규칙 심각도"""
    ERROR = "error"      # 반드시 수정 필요
    WARNING = "warning"  # 권고 사항
    INFO = "info"        # 참고 정보


class RuleCategory(str, Enum):
    """규칙 카테고리"""
    CONNECTIVITY = "connectivity"       # 연결 오류
    SYMBOL = "symbol"                   # 심볼 오류
    LABELING = "labeling"               # 라벨링 오류
    SPECIFICATION = "specification"     # 사양 오류
    STANDARD = "standard"               # 표준 위반
    SAFETY = "safety"                   # 안전 관련
    BWMS = "bwms"                       # BWMS 전용 규칙


# Design Rules Definition
DESIGN_RULES = {
    # 연결 관련 규칙
    "CONN-001": {
        "id": "CONN-001",
        "name": "끊어진 라인 검출",
        "name_en": "Broken Line Detection",
        "description": "라인이 심볼에 연결되지 않고 끊어진 경우",
        "category": RuleCategory.CONNECTIVITY,
        "severity": Severity.ERROR,
        "standard": "ISO 10628"
    },
    "CONN-002": {
        "id": "CONN-002",
        "name": "미연결 심볼",
        "name_en": "Unconnected Symbol",
        "description": "어떤 라인에도 연결되지 않은 심볼 검출",
        "category": RuleCategory.CONNECTIVITY,
        "severity": Severity.WARNING,
        "standard": "ISO 10628"
    },
    "CONN-003": {
        "id": "CONN-003",
        "name": "중복 연결",
        "name_en": "Duplicate Connection",
        "description": "동일한 두 심볼 간 중복 연결 검출",
        "category": RuleCategory.CONNECTIVITY,
        "severity": Severity.WARNING,
        "standard": "Internal"
    },
    "CONN-004": {
        "id": "CONN-004",
        "name": "데드엔드 라인",
        "name_en": "Dead-end Line",
        "description": "한쪽 끝만 연결된 라인 검출 (의도적 캡 제외)",
        "category": RuleCategory.CONNECTIVITY,
        "severity": Severity.WARNING,
        "standard": "ISO 10628"
    },

    # 심볼 관련 규칙
    "SYM-001": {
        "id": "SYM-001",
        "name": "미인식 심볼",
        "name_en": "Unrecognized Symbol",
        "description": "표준에 없는 심볼 사용",
        "category": RuleCategory.SYMBOL,
        "severity": Severity.WARNING,
        "standard": "ISA 5.1"
    },
    "SYM-002": {
        "id": "SYM-002",
        "name": "심볼 중첩",
        "name_en": "Symbol Overlap",
        "description": "두 개 이상의 심볼이 겹쳐있음",
        "category": RuleCategory.SYMBOL,
        "severity": Severity.ERROR,
        "standard": "Internal"
    },
    "SYM-003": {
        "id": "SYM-003",
        "name": "심볼 방향 오류",
        "name_en": "Symbol Orientation Error",
        "description": "밸브/펌프 등의 방향이 흐름과 불일치",
        "category": RuleCategory.SYMBOL,
        "severity": Severity.WARNING,
        "standard": "ISO 10628"
    },
    "SYM-004": {
        "id": "SYM-004",
        "name": "심볼 크기 비표준",
        "name_en": "Non-standard Symbol Size",
        "description": "심볼 크기가 도면 규정에 맞지 않음",
        "category": RuleCategory.SYMBOL,
        "severity": Severity.INFO,
        "standard": "Internal"
    },

    # 라벨링 관련 규칙
    "LBL-001": {
        "id": "LBL-001",
        "name": "태그번호 누락",
        "name_en": "Missing Tag Number",
        "description": "계기/밸브에 태그번호가 없음",
        "category": RuleCategory.LABELING,
        "severity": Severity.ERROR,
        "standard": "ISA 5.1"
    },
    "LBL-002": {
        "id": "LBL-002",
        "name": "중복 태그번호",
        "name_en": "Duplicate Tag Number",
        "description": "동일한 태그번호가 여러 곳에 사용됨",
        "category": RuleCategory.LABELING,
        "severity": Severity.ERROR,
        "standard": "ISA 5.1"
    },
    "LBL-003": {
        "id": "LBL-003",
        "name": "태그번호 형식 오류",
        "name_en": "Tag Number Format Error",
        "description": "태그번호 형식이 표준에 맞지 않음 (예: FV-001, PT-100)",
        "category": RuleCategory.LABELING,
        "severity": Severity.WARNING,
        "standard": "ISA 5.1"
    },
    "LBL-004": {
        "id": "LBL-004",
        "name": "라인번호 누락",
        "name_en": "Missing Line Number",
        "description": "배관 라인에 라인번호가 없음",
        "category": RuleCategory.LABELING,
        "severity": Severity.WARNING,
        "standard": "ISO 10628"
    },

    # 사양 관련 규칙
    "SPEC-001": {
        "id": "SPEC-001",
        "name": "배관 사이즈 불일치",
        "name_en": "Pipe Size Mismatch",
        "description": "연결된 배관 사이즈가 일치하지 않음 (리듀서 없음)",
        "category": RuleCategory.SPECIFICATION,
        "severity": Severity.ERROR,
        "standard": "Internal"
    },
    "SPEC-002": {
        "id": "SPEC-002",
        "name": "유체 등급 불일치",
        "name_en": "Fluid Class Mismatch",
        "description": "연결된 라인의 유체 등급이 다름",
        "category": RuleCategory.SPECIFICATION,
        "severity": Severity.ERROR,
        "standard": "Internal"
    },
    "SPEC-003": {
        "id": "SPEC-003",
        "name": "누락된 계기",
        "name_en": "Missing Instrument",
        "description": "필수 계기가 누락됨 (예: 펌프 후단 압력계)",
        "category": RuleCategory.SPECIFICATION,
        "severity": Severity.WARNING,
        "standard": "Engineering Best Practice"
    },

    # 표준 위반 규칙
    "STD-001": {
        "id": "STD-001",
        "name": "비표준 라인 타입",
        "name_en": "Non-standard Line Type",
        "description": "ISO 10628에 정의되지 않은 라인 타입 사용",
        "category": RuleCategory.STANDARD,
        "severity": Severity.INFO,
        "standard": "ISO 10628"
    },
    "STD-002": {
        "id": "STD-002",
        "name": "비표준 심볼 사용",
        "name_en": "Non-standard Symbol Usage",
        "description": "ISA 5.1에 정의되지 않은 계기 심볼 사용",
        "category": RuleCategory.STANDARD,
        "severity": Severity.INFO,
        "standard": "ISA 5.1"
    },

    # 안전 관련 규칙
    "SAF-001": {
        "id": "SAF-001",
        "name": "안전밸브 누락",
        "name_en": "Missing Safety Valve",
        "description": "압력용기에 안전밸브가 없음",
        "category": RuleCategory.SAFETY,
        "severity": Severity.ERROR,
        "standard": "ASME"
    },
    "SAF-002": {
        "id": "SAF-002",
        "name": "긴급차단밸브 누락",
        "name_en": "Missing Emergency Shutdown Valve",
        "description": "중요 계통에 긴급차단밸브가 없음",
        "category": RuleCategory.SAFETY,
        "severity": Severity.WARNING,
        "standard": "IEC 61511"
    },
    "SAF-003": {
        "id": "SAF-003",
        "name": "바이패스 없음",
        "name_en": "No Bypass Line",
        "description": "제어밸브에 바이패스 라인이 없음",
        "category": RuleCategory.SAFETY,
        "severity": Severity.INFO,
        "standard": "Engineering Best Practice"
    }
}
