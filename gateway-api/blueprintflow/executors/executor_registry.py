"""
Executor Registry
노드 실행기 팩토리 및 레지스트리

YAML 스펙 기반 + Custom API 지원 하이브리드 시스템
"""
from typing import Dict, Any, Optional
from pathlib import Path
import logging
import yaml

logger = logging.getLogger(__name__)

# 스펙 디렉토리
SPEC_DIR = Path(__file__).parent.parent.parent / "api_specs"


class ExecutorRegistry:
    """노드 실행기 레지스트리"""

    _executors: Dict[str, type] = {}
    _spec_cache: Dict[str, Dict[str, Any]] = {}  # YAML 스펙 캐시

    @classmethod
    def register(cls, node_type: str, executor_class: type):
        """
        실행기 등록

        Args:
            node_type: 노드 타입 이름
            executor_class: 실행기 클래스
        """
        cls._executors[node_type] = executor_class
        logger.info(f"실행기 등록: {node_type} -> {executor_class.__name__}")

    @classmethod
    def get(cls, node_type: str) -> Optional[type]:
        """
        실행기 조회

        Args:
            node_type: 노드 타입 이름

        Returns:
            실행기 클래스 또는 None
        """
        return cls._executors.get(node_type)

    @classmethod
    def get_all_types(cls) -> list[str]:
        """등록된 모든 노드 타입 조회"""
        return list(cls._executors.keys())

    @classmethod
    def load_spec(cls, api_id: str) -> Optional[Dict[str, Any]]:
        """
        YAML 스펙 파일 로드

        Args:
            api_id: API ID

        Returns:
            스펙 딕셔너리 또는 None
        """
        # 캐시 확인
        if api_id in cls._spec_cache:
            return cls._spec_cache[api_id]

        spec_file = SPEC_DIR / f"{api_id}.yaml"

        if not spec_file.exists():
            return None

        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            if spec and spec.get("kind") == "APISpec":
                cls._spec_cache[api_id] = spec
                logger.info(f"스펙 로드: {api_id}")
                return spec
        except Exception as e:
            logger.error(f"스펙 로드 실패 {api_id}: {e}")

        return None

    @classmethod
    def spec_to_api_config(cls, spec: Dict[str, Any], host: str = "localhost") -> Dict[str, Any]:
        """
        YAML 스펙을 GenericAPIExecutor용 api_config로 변환

        Args:
            spec: YAML 스펙 딕셔너리
            host: API 서버 호스트

        Returns:
            api_config 딕셔너리
        """
        metadata = spec.get("metadata", {})
        server = spec.get("server", {})
        blueprintflow = spec.get("blueprintflow", {})
        mappings = spec.get("mappings", {})
        i18n = spec.get("i18n", {})

        port = metadata.get("port", 5000)

        return {
            "id": metadata.get("id"),
            "name": metadata.get("name"),
            "displayName": i18n.get("ko", {}).get("label", metadata.get("name")),
            "baseUrl": f"http://{host}:{port}",
            "endpoint": server.get("endpoint", "/api/v1/process"),
            "method": server.get("method", "POST"),
            "contentType": server.get("contentType", "multipart/form-data"),
            "timeout": server.get("timeout", 60),
            "requiresImage": blueprintflow.get("requiresImage", True),
            "inputs": spec.get("inputs", []),
            "outputs": spec.get("outputs", []),
            "parameters": spec.get("parameters", []),
            "inputMappings": mappings.get("input", {}),
            "outputMappings": mappings.get("output", {}),
            "blueprintflow": blueprintflow
        }

    @classmethod
    def get_all_available_types(cls) -> list[str]:
        """등록된 executor + 스펙 파일 모든 타입 조회"""
        types = set(cls._executors.keys())

        # 스펙 파일에서 추가
        if SPEC_DIR.exists():
            for spec_file in SPEC_DIR.glob("*.yaml"):
                types.add(spec_file.stem)

        return sorted(list(types))

    @classmethod
    def create(cls, node_id: str, node_type: str, parameters: Dict[str, Any], host: str = "localhost"):
        """
        실행기 인스턴스 생성

        우선순위:
        1. 등록된 전용 Executor
        2. YAML 스펙 기반 GenericAPIExecutor
        3. Custom API Config 기반 GenericAPIExecutor

        Args:
            node_id: 노드 ID
            node_type: 노드 타입
            parameters: 노드 파라미터
            host: API 서버 호스트 (기본: localhost)

        Returns:
            실행기 인스턴스

        Raises:
            ValueError: 등록되지 않은 노드 타입이고 스펙/Custom API도 없는 경우
        """
        executor_class = cls.get(node_type)

        # 1. 등록된 executor가 있으면 사용
        if executor_class is not None:
            return executor_class(node_id, node_type, parameters)

        logger.info(f"등록되지 않은 노드 타입: {node_type}, 스펙/Custom API 확인 중...")

        from .generic_api_executor import create_generic_executor

        # 2. YAML 스펙이 있는지 확인
        spec = cls.load_spec(node_type)
        if spec is not None:
            api_config = cls.spec_to_api_config(spec, host)
            logger.info(f"✅ 스펙 기반 Executor 생성: {node_type}")
            return create_generic_executor(node_id, node_type, parameters, api_config)

        # 3. Custom API Config 확인
        from ..api_config_manager import get_api_config_manager

        api_config_manager = get_api_config_manager()
        api_config = api_config_manager.get_config(node_type)

        if api_config is not None:
            logger.info(f"✅ Custom API 기반 Executor 생성: {node_type}")
            return create_generic_executor(node_id, node_type, parameters, api_config)

        # 모두 실패하면 에러
        available_types = cls.get_all_available_types()
        raise ValueError(
            f"알 수 없는 노드 타입: {node_type}. "
            f"사용 가능한 타입: {', '.join(available_types)}"
        )
