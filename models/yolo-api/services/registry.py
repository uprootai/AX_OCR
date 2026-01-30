"""
Model Registry Service

YAML 기반 모델 레지스트리 관리
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import yaml

from services.inference import YOLOInferenceService

logger = logging.getLogger(__name__)


class ModelRegistry:
    """YAML 기반 모델 레지스트리 관리"""

    def __init__(self, registry_path: Path, models_dir: Path):
        self.registry_path = registry_path
        self.models_dir = models_dir
        self._registry: Dict[str, Any] = {}
        self._model_cache: Dict[str, YOLOInferenceService] = {}
        self.load_registry()

    def load_registry(self):
        """레지스트리 파일 로드"""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self._registry = yaml.safe_load(f) or {}
            logger.info(f"모델 레지스트리 로드: {len(self._registry.get('models', {}))}개 모델")
        else:
            self._registry = {'models': {}, 'default_model': 'engineering'}
            self.save_registry()
            logger.info("새 모델 레지스트리 생성")

    def save_registry(self):
        """레지스트리 파일 저장"""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._registry, f, allow_unicode=True, default_flow_style=False)

    def get_models(self) -> Dict[str, Any]:
        """등록된 모델 목록"""
        models = {}
        for model_id, info in self._registry.get('models', {}).items():
            file_path = self.models_dir / info.get('file', '')
            models[model_id] = {
                **info,
                'id': model_id,
                'file_exists': file_path.exists(),
                'file_size_mb': round(file_path.stat().st_size / 1024 / 1024, 2) if file_path.exists() else 0
            }
        return models

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """특정 모델 정보"""
        return self._registry.get('models', {}).get(model_id)

    def get_default_model(self) -> str:
        """기본 모델 ID"""
        return self._registry.get('default_model', 'engineering')

    def add_model(self, model_id: str, info: Dict[str, Any]):
        """모델 등록"""
        if 'models' not in self._registry:
            self._registry['models'] = {}
        self._registry['models'][model_id] = info
        self.save_registry()
        logger.info(f"모델 등록: {model_id}")

    def update_model(self, model_id: str, info: Dict[str, Any]):
        """모델 정보 업데이트"""
        if model_id in self._registry.get('models', {}):
            self._registry['models'][model_id].update(info)
            self.save_registry()
            logger.info(f"모델 업데이트: {model_id}")

    def delete_model(self, model_id: str) -> bool:
        """모델 삭제 (파일은 유지, 레지스트리에서만 제거)"""
        if model_id in self._registry.get('models', {}):
            del self._registry['models'][model_id]
            if model_id in self._model_cache:
                del self._model_cache[model_id]
            self.save_registry()
            logger.info(f"모델 삭제: {model_id}")
            return True
        return False

    def get_inference_service(self, model_id: str) -> Optional[YOLOInferenceService]:
        """모델 로드 (캐시 사용)"""
        # 캐시에 있으면 반환
        if model_id in self._model_cache:
            return self._model_cache[model_id]

        # 레지스트리에서 모델 정보 조회
        model_info = self.get_model(model_id)
        if not model_info:
            logger.warning(f"모델을 찾을 수 없음: {model_id}")
            return None

        # 모델 파일 경로
        model_path = self.models_dir / model_info.get('file', '')
        if not model_path.exists():
            logger.warning(f"모델 파일이 없음: {model_path}")
            return None

        # 모델 로드
        logger.info(f"모델 로딩: {model_id} ({model_path})")
        service = YOLOInferenceService(str(model_path))
        service.load_model()

        # data.yaml로 클래스명 오버라이드 (drawing-bom-extractor 방식)
        data_yaml = model_info.get('data_yaml')
        if data_yaml:
            data_yaml_path = self.models_dir / data_yaml
            if data_yaml_path.exists():
                with open(data_yaml_path, 'r', encoding='utf-8') as f:
                    data_config = yaml.safe_load(f)
                names = data_config.get('names', [])
                override_names = {i: name for i, name in enumerate(names)}
                service.model.model.names = override_names
                service.class_names = override_names
                logger.info(f"data.yaml 클래스명 적용: {model_id} ({len(names)}개)")

        # 캐시에 저장
        self._model_cache[model_id] = service
        return service


# Global state
_model_registry: Optional[ModelRegistry] = None
_inference_service: Optional[YOLOInferenceService] = None


def get_model_registry() -> Optional[ModelRegistry]:
    """Get global model registry instance"""
    return _model_registry


def get_inference_service() -> Optional[YOLOInferenceService]:
    """Get global inference service instance"""
    return _inference_service


def set_model_state(
    model_registry: ModelRegistry,
    inference_service: YOLOInferenceService
):
    """Set global model state (called from lifespan)"""
    global _model_registry, _inference_service
    _model_registry = model_registry
    _inference_service = inference_service
