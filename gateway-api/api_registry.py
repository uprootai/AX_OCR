"""
API Registry Service
자동 검색, 등록, 헬스체크를 관리하는 중앙 레지스트리

YAML 스펙 기반 + 네트워크 자동 검색 하이브리드 시스템
"""
import asyncio
import logging
import os
from pathlib import Path
from threading import RLock
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel
import httpx
import yaml

logger = logging.getLogger(__name__)

# 스펙 파일 디렉토리
SPEC_DIR = Path(__file__).parent / "api_specs"
if os.getenv("API_SPECS_DIR"):
    SPEC_DIR = Path(os.getenv("API_SPECS_DIR"))


class APIMetadata(BaseModel):
    """API 메타데이터"""
    id: str
    name: str
    display_name: str
    version: str
    description: str
    base_url: str
    endpoint: str
    port: int
    method: str = "POST"
    requires_image: bool = True
    icon: str
    color: str
    category: str
    status: str = "unknown"  # healthy, unhealthy, unknown
    last_check: Optional[datetime] = None
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    parameters: List[Dict[str, Any]]
    output_mappings: Dict[str, str]


class APIRegistry:
    """
    API 자동 검색 및 레지스트리 관리
    """

    def __init__(self):
        self.apis: Dict[str, APIMetadata] = {}
        self._health_check_interval = 60  # 60초마다 헬스체크
        self._health_check_task: Optional[asyncio.Task] = None
        self._health_check_started = False  # 중복 시작 방지 플래그
        self._specs_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._specs_cache_signature: Optional[Tuple[Tuple[str, int, int], ...]] = None
        self._specs_cache_lock = RLock()

        # 기본 API 포트 목록 (자동 검색용)
        self.default_ports = [
            5001,  # eDOCr2 v1
            5002,  # eDOCr2 v2
            5003,  # SkinModel
            5004,  # VL API
            5005,  # YOLO
            5006,  # PaddleOCR
            5012,  # EDGNet
        ]

        # 추가 검색 포트 범위 (사용자 정의 API용)
        self.custom_port_range = range(5007, 5020)

        # Docker 컨테이너 호스트명 매핑 (API ID -> Docker hostname)
        # YAML 스펙 ID와 API의 /api/v1/info 반환 ID 모두 매핑
        self.docker_host_mapping = {
            # YOLO - YAML: yolo, API info: yolo-detector
            # YOLO handles P&ID detection via model_type parameter (no separate yolo-pid-api)
            "yolo": "yolo-api",
            "yolo-detector": "yolo-api",
            # eDOCr2 - YAML: edocr2, API info: edocr2-v2
            "edocr2": "edocr2-v2-api",
            "edocr2-v2": "edocr2-v2-api",
            # 기타 API (YAML ID와 API info ID 동일)
            "edgnet": "edgnet-api",
            "skinmodel": "skinmodel-api",
            "paddleocr": "paddleocr-api",
            "vl": "vl-api",
            "knowledge": "knowledge-api",
            "tesseract": "tesseract-api",
            "trocr": "trocr-api",
            "esrgan": "esrgan-api",
            "ocr-ensemble": "ocr-ensemble-api",
            "suryaocr": "surya-ocr-api",
            "doctr": "doctr-api",
            "easyocr": "easyocr-api",
            "line-detector": "line-detector-api",
            "linedetector": "line-detector-api",
            "pid-analyzer": "pid-analyzer-api",
            "pidanalyzer": "pid-analyzer-api",
            "design-checker": "design-checker-api",
            "designchecker": "design-checker-api",
            "blueprint-ai-bom": "blueprint-ai-bom-backend",
        }

        # 스펙별 healthEndpoint 저장 (load_from_specs에서 설정)
        self.health_endpoints: Dict[str, str] = {}

    def _build_spec_signature(self) -> Tuple[Tuple[str, int, int], ...]:
        """스펙 디렉토리의 파일 변경 시그니처 생성"""
        if not SPEC_DIR.exists():
            return ()

        signature = []
        for spec_file in sorted(SPEC_DIR.glob("*.yaml")):
            try:
                stat = spec_file.stat()
            except FileNotFoundError:
                continue
            signature.append((spec_file.name, stat.st_mtime_ns, stat.st_size))

        return tuple(signature)

    def _load_specs_from_disk(self) -> Dict[str, Dict[str, Any]]:
        """모든 스펙 파일을 디스크에서 로드"""
        specs: Dict[str, Dict[str, Any]] = {}

        if not SPEC_DIR.exists():
            return specs

        for spec_file in SPEC_DIR.glob("*.yaml"):
            try:
                with open(spec_file, "r", encoding="utf-8") as f:
                    spec = yaml.safe_load(f)
                    if spec and spec.get("kind") == "APISpec":
                        api_id = spec.get("metadata", {}).get("id", spec_file.stem)
                        specs[api_id] = spec
            except Exception as e:
                logger.error(f"스펙 로드 실패 {spec_file}: {e}")

        return specs

    def invalidate_spec_cache(self):
        """메모리 스펙 캐시 무효화"""
        with self._specs_cache_lock:
            self._specs_cache = None
            self._specs_cache_signature = None

    def refresh_spec_cache(self) -> Dict[str, Dict[str, Any]]:
        """디스크 기준으로 스펙 캐시 강제 갱신"""
        specs = self._load_specs_from_disk()
        with self._specs_cache_lock:
            self._specs_cache = specs
            self._specs_cache_signature = self._build_spec_signature()
        return specs

    def load_from_specs(self, host: str = "localhost", use_docker_hosts: bool = True) -> List[APIMetadata]:
        """
        YAML 스펙 파일에서 API 메타데이터 로드

        Args:
            host: API 서버 호스트 (기본: localhost)
            use_docker_hosts: Docker 컨테이너 이름 사용 여부 (기본: True)

        Returns:
            로드된 API 목록
        """
        loaded = []
        specs = self.get_all_specs()
        self.health_endpoints.clear()

        if not specs:
            if not SPEC_DIR.exists():
                logger.warning(f"Spec directory not found: {SPEC_DIR}")
            return loaded

        for api_id, spec in specs.items():
            try:
                metadata = spec.get("metadata", {})
                server = spec.get("server", {})
                blueprintflow = spec.get("blueprintflow", {})

                port = metadata.get("port", 5000)

                # Docker 환경에서는 컨테이너 이름 사용
                if use_docker_hosts and api_id in self.docker_host_mapping:
                    effective_host = self.docker_host_mapping[api_id]
                else:
                    effective_host = host

                # healthEndpoint 저장 (기본값: /api/v1/health)
                health_endpoint = server.get("healthEndpoint", "/api/v1/health")
                self.health_endpoints[api_id] = health_endpoint

                # 대체 ID에도 동일한 healthEndpoint 저장 (API info ID와 YAML ID 불일치 대응)
                # 예: edocr2 -> edocr2-v2, yolo -> yolo-detector
                alt_id_mapping = {
                    "edocr2": "edocr2-v2",
                    "yolo": "yolo-detector",
                }
                if api_id in alt_id_mapping:
                    self.health_endpoints[alt_id_mapping[api_id]] = health_endpoint

                api_metadata = APIMetadata(
                    id=api_id,
                    name=metadata.get("name", api_id),
                    display_name=spec.get("i18n", {}).get("ko", {}).get("label", metadata.get("name", api_id)),
                    version=metadata.get("version", "1.0.0"),
                    description=metadata.get("description", ""),
                    base_url=f"http://{effective_host}:{port}",
                    endpoint=server.get("endpoint", "/api/v1/process"),
                    port=port,
                    method=server.get("method", "POST"),
                    requires_image=blueprintflow.get("requiresImage", True),
                    icon=blueprintflow.get("icon", "Box"),
                    color=blueprintflow.get("color", "#6366f1"),
                    category=blueprintflow.get("category", "detection"),
                    status="unknown",
                    last_check=None,
                    inputs=spec.get("inputs", []),
                    outputs=spec.get("outputs", []),
                    parameters=spec.get("parameters", []),
                    output_mappings=spec.get("mappings", {}).get("output", {})
                )

                loaded.append(api_metadata)
                self.apis[api_id] = api_metadata
                logger.info(f"✅ 스펙에서 로드: {api_metadata.display_name} ({effective_host}:{port})")

            except Exception as e:
                logger.error(f"스펙 로드 실패 {api_id}: {e}")

        logger.info(f"📂 스펙 파일에서 {len(loaded)}개 API 로드됨")
        return loaded

    def get_spec(self, api_id: str) -> Optional[Dict[str, Any]]:
        """
        API 스펙 YAML 파일 원본 반환

        Args:
            api_id: API ID

        Returns:
            스펙 딕셔너리 또는 None
        """
        return self.get_all_specs().get(api_id)

    def get_all_specs(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """모든 스펙 파일 로드"""
        if force_refresh:
            return self.refresh_spec_cache()

        with self._specs_cache_lock:
            current_signature = self._build_spec_signature()
            if (
                self._specs_cache is None
                or self._specs_cache_signature is None
                or self._specs_cache_signature != current_signature
            ):
                specs = self._load_specs_from_disk()
                self._specs_cache = specs
                self._specs_cache_signature = self._build_spec_signature()
                return self._specs_cache

            return self._specs_cache

    async def discover_apis(self, host: str = "localhost") -> List[APIMetadata]:
        """
        네트워크에서 API 자동 검색

        Args:
            host: 검색할 호스트 (기본: localhost)

        Returns:
            발견된 API 목록
        """
        discovered = []
        all_ports = list(self.default_ports) + list(self.custom_port_range)

        logger.info(f"🔍 API 자동 검색 시작 (포트: {len(all_ports)}개)")

        async with httpx.AsyncClient(timeout=5.0) as client:
            tasks = []
            for port in all_ports:
                tasks.append(self._check_port(client, host, port))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for api_metadata in results:
                if isinstance(api_metadata, APIMetadata):
                    discovered.append(api_metadata)
                    self.apis[api_metadata.id] = api_metadata
                    logger.info(f"✅ API 발견: {api_metadata.display_name} ({api_metadata.base_url})")

        logger.info(f"🎉 API 검색 완료: {len(discovered)}개 발견")
        return discovered

    async def _check_port(self, client: httpx.AsyncClient, host: str, port: int) -> Optional[APIMetadata]:
        """
        특정 포트에서 API 확인

        Args:
            client: HTTP 클라이언트
            host: 호스트
            port: 포트

        Returns:
            APIMetadata 또는 None
        """
        base_url = f"http://{host}:{port}"
        info_url = f"{base_url}/api/v1/info"

        try:
            response = await client.get(info_url)
            if response.status_code == 200:
                data = response.json()

                # 헬스체크도 수행
                health_url = f"{base_url}/api/v1/health"
                health_status = "unknown"
                try:
                    health_response = await client.get(health_url, timeout=3.0)
                    if health_response.status_code == 200:
                        health_status = "healthy"
                    else:
                        health_status = "unhealthy"
                except:
                    health_status = "unhealthy"

                # APIMetadata 생성
                return APIMetadata(
                    id=data.get("id"),
                    name=data.get("name"),
                    display_name=data.get("display_name", data.get("displayName")),
                    version=data.get("version", "1.0.0"),
                    description=data.get("description", ""),
                    base_url=base_url,
                    endpoint=data.get("endpoint"),
                    port=port,
                    method=data.get("method", "POST"),
                    requires_image=data.get("requires_image", data.get("requiresImage", True)),
                    icon=data.get("blueprintflow", {}).get("icon", "🏷️"),
                    color=data.get("blueprintflow", {}).get("color", "#a855f7"),
                    category=data.get("blueprintflow", {}).get("category", "api"),
                    status=health_status,
                    last_check=datetime.now(),
                    inputs=data.get("inputs", []),
                    outputs=data.get("outputs", []),
                    parameters=data.get("parameters", []),
                    output_mappings=data.get("output_mappings", data.get("outputMappings", {}))
                )
        except httpx.ConnectError:
            # 포트에 서비스 없음 (정상)
            pass
        except Exception as e:
            # 기타 오류 (로깅만)
            logger.debug(f"포트 {port} 확인 실패: {e}")

        return None

    async def check_health(self, api_id: str) -> str:
        """
        특정 API의 헬스 상태 확인

        Args:
            api_id: API ID

        Returns:
            "healthy", "unhealthy", 또는 "unknown"
        """
        if api_id not in self.apis:
            return "unknown"

        api = self.apis[api_id]

        # base_url에서 localhost를 Docker 호스트명으로 변환
        base_url = api.base_url
        if "localhost" in base_url and api_id in self.docker_host_mapping:
            docker_host = self.docker_host_mapping[api_id]
            base_url = base_url.replace("localhost", docker_host)

        # 스펙에서 설정된 healthEndpoint 사용, 없으면 기본값 /api/v1/health
        health_endpoint = self.health_endpoints.get(api_id, "/api/v1/health")
        health_url = f"{base_url}{health_endpoint}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                if response.status_code == 200:
                    api.status = "healthy"
                    api.last_check = datetime.now()
                    return "healthy"
                else:
                    api.status = "unhealthy"
                    api.last_check = datetime.now()
                    return "unhealthy"
        except Exception as e:
            logger.warning(f"API {api_id} 헬스체크 실패 ({health_url}): {e}")
            api.status = "unhealthy"
            api.last_check = datetime.now()
            return "unhealthy"

    async def check_all_health(self):
        """모든 등록된 API의 헬스 상태 확인"""
        if not self.apis:
            return

        logger.info(f"🏥 모든 API 헬스체크 시작 ({len(self.apis)}개)")

        tasks = [self.check_health(api_id) for api_id in self.apis.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        healthy_count = sum(1 for r in results if r == "healthy")
        logger.info(f"✅ 헬스체크 완료: {healthy_count}/{len(self.apis)} healthy")

    async def start_health_check_loop(self):
        """백그라운드 헬스체크 루프 시작"""
        logger.info(f"🏥 헬스체크 루프 시작 (간격: {self._health_check_interval}초)")

        while True:
            try:
                await self.check_all_health()
            except Exception as e:
                logger.error(f"헬스체크 루프 오류: {e}")

            await asyncio.sleep(self._health_check_interval)

    def start_health_check_background(self):
        """백그라운드 헬스체크 태스크 시작 (중복 시작 방지)"""
        # 이미 시작된 경우 무시
        if self._health_check_started:
            logger.debug("⚠️ 헬스체크 태스크 이미 실행 중 (중복 시작 방지)")
            return

        if self._health_check_task is None or self._health_check_task.done():
            self._health_check_started = True
            self._health_check_task = asyncio.create_task(self.start_health_check_loop())
            logger.info("✅ 백그라운드 헬스체크 태스크 시작됨")

    def get_all_apis(self) -> List[APIMetadata]:
        """모든 등록된 API 반환"""
        return list(self.apis.values())

    def get_api(self, api_id: str) -> Optional[APIMetadata]:
        """특정 API 정보 반환"""
        return self.apis.get(api_id)

    def add_api(self, api_metadata: APIMetadata):
        """API 수동 추가"""
        self.apis[api_metadata.id] = api_metadata
        logger.info(f"✅ API 수동 추가: {api_metadata.display_name}")

    def remove_api(self, api_id: str) -> bool:
        """API 제거"""
        if api_id in self.apis:
            api = self.apis.pop(api_id)
            logger.info(f"🗑️ API 제거: {api.display_name}")
            return True
        return False

    def get_healthy_apis(self) -> List[APIMetadata]:
        """Healthy 상태인 API만 반환"""
        return [api for api in self.apis.values() if api.status == "healthy"]

    def get_apis_by_category(self, category: str) -> List[APIMetadata]:
        """카테고리별 API 반환"""
        return [api for api in self.apis.values() if api.category == category]


# 싱글톤 인스턴스
_api_registry: Optional[APIRegistry] = None


def get_api_registry() -> APIRegistry:
    """API 레지스트리 싱글톤 인스턴스 반환"""
    global _api_registry
    if _api_registry is None:
        _api_registry = APIRegistry()
    return _api_registry
