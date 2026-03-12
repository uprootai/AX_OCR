"""
DSE Bearing Parser — Constants

파싱에 사용되는 패턴 상수 및 ISO 공차/표면 거칠기 테이블
"""

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
