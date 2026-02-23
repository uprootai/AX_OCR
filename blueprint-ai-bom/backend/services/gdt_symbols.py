"""GD&T Symbols & Constants

GD&T 파싱에 사용되는 심볼 패턴, 상수, 데이터 클래스 정의
- GD&T 심볼 패턴 (14종)
- 표면 거칠기 패턴
- 치수 공차 패턴
- 재료 조건 수정자 패턴
- 데이텀 레이블 패턴
- DetectedGDTElement 데이터 클래스
"""

from typing import Dict, Any, Tuple, List
from dataclasses import dataclass, field

from schemas.gdt import (
    GeometricCharacteristic,
    MaterialCondition,
)


# GD&T 심볼 패턴 (OCR 텍스트에서 검출)
GDT_SYMBOL_PATTERNS: Dict[GeometricCharacteristic, List[str]] = {
    # Form (형상 공차)
    GeometricCharacteristic.STRAIGHTNESS: [r'[-─—]', r'직진도', r'straightness'],
    GeometricCharacteristic.FLATNESS: [r'[▱◇□]', r'평면도', r'flatness', r'flat'],
    GeometricCharacteristic.CIRCULARITY: [r'[○◯⚪]', r'진원도', r'circularity', r'roundness'],
    GeometricCharacteristic.CYLINDRICITY: [r'[⌭]', r'원통도', r'cylindricity'],

    # Profile (윤곽 공차)
    GeometricCharacteristic.PROFILE_LINE: [r'[⌒]', r'선.*윤곽', r'profile.*line'],
    GeometricCharacteristic.PROFILE_SURFACE: [r'[⌓]', r'면.*윤곽', r'profile.*surface', r'Ra\d', r'R[az]\s*\d'],

    # Orientation (방향 공차)
    GeometricCharacteristic.ANGULARITY: [r'[∠]', r'경사도', r'angularity', r'\d+°'],
    GeometricCharacteristic.PERPENDICULARITY: [r'[⊥]', r'직각도', r'perpendicularity', r'perp'],
    GeometricCharacteristic.PARALLELISM: [r'[∥‖//]', r'평행도', r'parallelism'],

    # Location (위치 공차)
    GeometricCharacteristic.POSITION: [r'[⌖⊕⊙\+]', r'위치도', r'position', r'true.*position', r'TP'],
    GeometricCharacteristic.CONCENTRICITY: [r'[◎⊚]', r'동심도', r'concentricity', r'coaxiality', r'conc'],
    GeometricCharacteristic.SYMMETRY: [r'[⌯≡]', r'대칭도', r'symmetry', r'sym'],

    # Runout (흔들림 공차)
    GeometricCharacteristic.CIRCULAR_RUNOUT: [r'[↗→]', r'원주.*흔들림', r'circular.*runout', r'TIR'],
    GeometricCharacteristic.TOTAL_RUNOUT: [r'[⇗⟹]', r'전체.*흔들림', r'total.*runout'],
}

# 표면 거칠기 패턴 (Ra, Rz, Rt 등)
SURFACE_ROUGHNESS_PATTERNS: List[str] = [
    r'R[aztp]\s*\d+\.?\d*',  # Ra3.2, Rz6.3
    r'√\s*\d+\.?\d*',        # √3.2
    r'∇\s*\d+\.?\d*',        # ∇표기
]

# 공차 표기 패턴 (치수 공차)
DIMENSION_TOLERANCE_PATTERNS: List[str] = [
    r'[±]\s*\d+\.?\d*',           # ±0.1
    r'\+\d+\.?\d*\s*[-/]\s*\d+\.?\d*',  # +0.2/-0.1
    r'\(\d+\.?\d*\)',              # (177) 참조 치수
]

# 재료 조건 수정자 패턴
MATERIAL_CONDITION_PATTERNS: Dict[MaterialCondition, List[str]] = {
    MaterialCondition.MMC: [r'[Ⓜ]', r'\(M\)', r'MMC', r'최대.*실체'],
    MaterialCondition.LMC: [r'[Ⓛ]', r'\(L\)', r'LMC', r'최소.*실체'],
    MaterialCondition.RFS: [r'[Ⓢ]', r'\(S\)', r'RFS'],
}

# 데이텀 레이블 패턴
DATUM_LABEL_PATTERN: str = r'[A-Z](?:\s*-\s*[A-Z])?'

# 공차 값 패턴 (예: 0.05, ⌀0.1, 0.02 A B)
TOLERANCE_PATTERN: str = r'(?:⌀|φ|Ø)?\s*(\d+(?:\.\d+)?)\s*(mm|in)?'


@dataclass
class DetectedGDTElement:
    """검출된 GD&T 요소"""
    element_type: str  # 'fcf', 'datum', 'symbol'
    bbox: Tuple[float, float, float, float]
    text: str
    confidence: float
    parsed_data: Dict[str, Any] = field(default_factory=dict)
