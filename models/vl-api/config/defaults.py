"""
VL API 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

VL API: Vision-Language 모델 (도면 분류, 설명 생성)
"""

from typing import Dict, Any, Optional


# 프롬프트 템플릿
PROMPT_TEMPLATES: Dict[str, str] = {
    "classify": """Analyze this engineering drawing and classify it into one of these categories:
- mechanical: Mechanical parts, assemblies, machined components
- electrical: Electrical diagrams, wiring, circuits
- pid: P&ID (Piping and Instrumentation Diagrams)
- architectural: Building plans, floor plans
- structural: Structural engineering drawings
- other: Other types

Respond with only the category name.""",

    "describe": """Describe this engineering drawing in detail, including:
1. Type of drawing (mechanical, electrical, P&ID, etc.)
2. Main components visible
3. Key dimensions or specifications if visible
4. Purpose or function of the part/system
5. Any notable features or annotations""",

    "extract_info": """Extract the following information from this drawing:
- Title/Part name
- Part number
- Revision
- Material (if specified)
- Key dimensions
- Tolerances
- Notes or specifications

Return as structured JSON.""",

    "pid_analysis": """Analyze this P&ID (Piping and Instrumentation Diagram):
1. Identify main equipment (pumps, valves, tanks, etc.)
2. List instrument tags visible
3. Describe the process flow
4. Note any safety devices or interlocks
5. Identify control loops if visible""",
}


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반",
        "description": "기본 VLM 분석",
        "model": "gpt-4o-mini",
        "max_tokens": 1000,
        "temperature": 0.3,
        "prompt_template": "describe",
    },
    "classify": {
        "name": "분류",
        "description": "도면 유형 분류",
        "model": "gpt-4o-mini",
        "max_tokens": 50,
        "temperature": 0.1,
        "prompt_template": "classify",
    },
    "detailed": {
        "name": "상세 분석",
        "description": "상세 정보 추출",
        "model": "gpt-4o",
        "max_tokens": 2000,
        "temperature": 0.2,
        "prompt_template": "extract_info",
    },
    "pid": {
        "name": "P&ID 분석",
        "description": "P&ID 전용 분석",
        "model": "gpt-4o",
        "max_tokens": 2000,
        "temperature": 0.2,
        "prompt_template": "pid_analysis",
    },
    "fast": {
        "name": "빠른 분석",
        "description": "빠른 응답 (간단한 분류)",
        "model": "gpt-4o-mini",
        "max_tokens": 200,
        "temperature": 0.1,
        "prompt_template": "classify",
    },
    "debug": {
        "name": "디버그",
        "description": "디버그용 (상세 출력)",
        "model": "gpt-4o-mini",
        "max_tokens": 1500,
        "temperature": 0.5,
        "prompt_template": "describe",
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름
        overrides: 덮어쓸 파라미터

    Returns:
        설정 딕셔너리
    """
    base_config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE]).copy()

    if overrides:
        for key, value in overrides.items():
            if value is not None:
                base_config[key] = value

    return base_config


def get_prompt_template(template_name: str) -> str:
    """
    프롬프트 템플릿 반환

    Args:
        template_name: 템플릿 이름

    Returns:
        프롬프트 문자열
    """
    return PROMPT_TEMPLATES.get(template_name, PROMPT_TEMPLATES["describe"])


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }
