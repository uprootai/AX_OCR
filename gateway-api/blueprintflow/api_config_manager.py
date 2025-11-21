"""
API Config Manager
Custom API 설정을 관리하는 모듈
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# API Config 저장 경로
API_CONFIG_FILE = Path("/tmp/blueprintflow_api_configs.json")


class APIConfigManager:
    """API Configuration 관리자"""

    def __init__(self, config_file: Path = API_CONFIG_FILE):
        self.config_file = config_file
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.load_configs()

    def load_configs(self):
        """파일에서 API 설정 로드"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.configs = data.get("apis", {})
                    logger.info(f"API Config 로드 완료: {len(self.configs)}개")
            except Exception as e:
                logger.error(f"API Config 로드 실패: {e}")
                self.configs = {}
        else:
            logger.info("API Config 파일 없음, 빈 설정으로 시작")
            self.configs = {}

    def save_configs(self):
        """API 설정을 파일에 저장"""
        try:
            # 디렉토리 생성
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({"apis": self.configs}, f, indent=2, ensure_ascii=False)

            logger.info(f"API Config 저장 완료: {len(self.configs)}개")
        except Exception as e:
            logger.error(f"API Config 저장 실패: {e}")
            raise

    def get_config(self, api_id: str) -> Optional[Dict[str, Any]]:
        """특정 API 설정 조회"""
        return self.configs.get(api_id)

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """모든 API 설정 조회"""
        return self.configs

    def get_enabled_configs(self) -> Dict[str, Dict[str, Any]]:
        """활성화된 API 설정만 조회"""
        return {k: v for k, v in self.configs.items() if v.get("enabled", True)}

    def add_config(self, config: Dict[str, Any]) -> bool:
        """새 API 설정 추가"""
        api_id = config.get("id")

        if not api_id:
            logger.error("API Config에 id가 없습니다")
            return False

        if api_id in self.configs:
            logger.warning(f"API Config 이미 존재: {api_id}")
            return False

        self.configs[api_id] = config
        self.save_configs()
        logger.info(f"API Config 추가: {api_id}")
        return True

    def update_config(self, api_id: str, updates: Dict[str, Any]) -> bool:
        """기존 API 설정 업데이트"""
        if api_id not in self.configs:
            logger.error(f"API Config 없음: {api_id}")
            return False

        self.configs[api_id].update(updates)
        self.save_configs()
        logger.info(f"API Config 업데이트: {api_id}")
        return True

    def delete_config(self, api_id: str) -> bool:
        """API 설정 삭제"""
        if api_id not in self.configs:
            logger.error(f"API Config 없음: {api_id}")
            return False

        del self.configs[api_id]
        self.save_configs()
        logger.info(f"API Config 삭제: {api_id}")
        return True

    def toggle_enabled(self, api_id: str) -> bool:
        """API 활성화/비활성화 토글"""
        if api_id not in self.configs:
            logger.error(f"API Config 없음: {api_id}")
            return False

        current = self.configs[api_id].get("enabled", True)
        self.configs[api_id]["enabled"] = not current
        self.save_configs()
        logger.info(f"API Config 토글: {api_id} -> {not current}")
        return True


# 전역 인스턴스
_api_config_manager = None


def get_api_config_manager() -> APIConfigManager:
    """API Config Manager 싱글톤 인스턴스 반환"""
    global _api_config_manager
    if _api_config_manager is None:
        _api_config_manager = APIConfigManager()
    return _api_config_manager
