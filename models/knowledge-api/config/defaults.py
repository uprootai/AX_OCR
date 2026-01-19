"""
Knowledge API 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

Knowledge API: Neo4j GraphRAG 기반 지식 그래프
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반 쿼리",
        "description": "기본 그래프 쿼리",
        "max_results": 100,
        "include_relationships": True,
        "depth": 2,
        "timeout": 30,
    },
    "component_search": {
        "name": "부품 검색",
        "description": "부품 정보 검색 최적화",
        "max_results": 50,
        "include_relationships": True,
        "depth": 3,
        "timeout": 30,
    },
    "similarity": {
        "name": "유사 부품",
        "description": "유사 부품 검색 (벡터 유사도)",
        "max_results": 20,
        "include_relationships": False,
        "depth": 1,
        "timeout": 60,
    },
    "path_finding": {
        "name": "경로 탐색",
        "description": "노드 간 경로 탐색",
        "max_results": 10,
        "include_relationships": True,
        "depth": 5,
        "timeout": 60,
    },
    "export": {
        "name": "데이터 추출",
        "description": "대량 데이터 추출용",
        "max_results": 1000,
        "include_relationships": True,
        "depth": 2,
        "timeout": 120,
    },
    "debug": {
        "name": "디버그",
        "description": "디버그용 (상세 출력)",
        "max_results": 50,
        "include_relationships": True,
        "depth": 3,
        "timeout": 30,
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


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }
