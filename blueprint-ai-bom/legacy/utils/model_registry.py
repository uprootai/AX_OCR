"""
Model Registry Management
모델 레지스트리 관리 클래스
"""
import os
import json

class ModelRegistry:
    """모델 레지스트리 관리 클래스"""

    def __init__(self, registry_path="models/registry.json"):
        self.registry_path = registry_path
        self.registry = self.load_registry()

    def load_registry(self):
        """모델 레지스트리 로드"""
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"models": {}, "classes": {}, "metadata": {}}

    def get_available_models(self):
        """활성화된 모델 목록 반환"""
        available = {}
        for model_id, model_info in self.registry.get("models", {}).items():
            if model_info.get("active", True):
                # 실제 파일 존재 여부 확인
                model_path = model_info.get("path", "")
                if self._check_model_exists(model_path, model_info.get("type")):
                    available[model_id] = model_info
        return available

    def _check_model_exists(self, path, model_type):
        """모델 파일 존재 여부 확인"""
        if model_type == "YOLO":
            return os.path.exists(path) and path.endswith('.pt')
        elif model_type == "Detectron2":
            # Detectron2는 실제 구현 전까지 임시로 True 반환
            return True  # os.path.isdir(path) and DETECTRON2_AVAILABLE
        return False

    def get_model_info(self, model_id):
        """특정 모델 정보 반환"""
        return self.registry.get("models", {}).get(model_id, None)

    def get_class_info(self, class_name):
        """특정 클래스 정보 반환"""
        return self.registry.get("classes", {}).get(class_name, None)

    def save_registry(self):
        """레지스트리 저장"""
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)